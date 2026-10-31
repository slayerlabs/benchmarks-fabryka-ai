"""Dane: mieszanka SlayerLab/slayer-pl-8x3b, dekontaminacja 13-gramami, tokenizacja Slayera.

python wygaszanie/dane.py --tokenizer M/tokenizer.json --wyjscie /workspace/dane \
    --tokeny_train 200000000 --tokeny_heldout 4200000 --pack 7

Wyjście: train.bin (uint16, dokumenty przemieszane, przed każdym token 0 <|endoftext|>),
val.bin = heldout.bin (uint16, posortowane po komponencie), heldout_meta.json (zakresy komponentów),
statystyki.json (tokeny, dokumenty, usunięte przez dekontaminację, rewizja zbioru, sha256 plików).
"""

import argparse
import hashlib
import json
import multiprocessing as mp
import random
import re
import sys
import time
from pathlib import Path

import numpy as np

REPO = "SlayerLab/slayer-pl-8x3b"
UDZIALY = {"web": 0.63, "core": 0.19, "legal": 0.08, "en": 0.10}  # karta zbioru, scenariusz B
N = 13
SLOWO = re.compile(r"\w+", re.UNICODE)
EVAL_NGRAMY = set()


def ngramy(tekst):
    w = SLOWO.findall(tekst.lower())
    return {hash(tuple(w[i:i + N])) for i in range(len(w) - N + 1)}


def teksty_ewaluacji():
    from datasets import load_dataset
    out = {}
    arc = load_dataset("allenai/ai2_arc", "ARC-Challenge", revision="210d026faf9955653af8916fad021475a3f00453")["test"]
    out["arc_c"] = [r["question"] + " " + " ".join(r["choices"]["text"]) for r in arc] + [r["question"] for r in arc]
    med = load_dataset("openlifescienceai/medmcqa", revision="91c6572c454088bf71b679ad90aa8dffcd0d5868")["validation"]
    out["medmcqa"] = [r["question"] + " " + " ".join([r["opa"], r["opb"], r["opc"], r["opd"]]) for r in med] + \
                     [r["question"] for r in med] + [r["exp"] or "" for r in med]
    siqa = load_dataset("allenai/social_i_qa", revision="refs/convert/parquet")["validation"]
    out["siqa"] = [f"{r['context']} {r['question']} {r['answerA']} {r['answerB']} {r['answerC']}" for r in siqa]
    out["pubmedqa"] = [" ".join(d["CONTEXTS"]) + " " + d["QUESTION"] for d in pubmedqa_docs()]
    wt = load_dataset("EleutherAI/wikitext_document_level", "wikitext-2-raw-v1",
                      revision="647234772b9554e208af6c826f23b99e3cac88c8")["test"]
    out["wikitext"] = [r["page"] for r in wt]
    import csv
    from huggingface_hub import hf_hub_download
    p = hf_hub_download("jumelet/multiblimp", "pol/data.tsv", repo_type="dataset",
                        revision="de923efa8d2483d6b13364ee68e65308e990a991")
    csv.field_size_limit(10 ** 8)
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    out["multiblimp"] = [r["sen"] for r in rows] + [r["wrong_sen"] for r in rows]
    return out


def pubmedqa_docs():
    """bigbio/pubmed_qa, config jak lm-eval, plik parquet wprost z refs/convert/parquet.

    load_dataset na tej gałęzi pada (DatasetGenerationError: configi mają różne schematy kolumn).
    """
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download
    cfg = "pubmed_qa_labeled_fold0_source"
    p = hf_hub_download("bigbio/pubmed_qa", f"{cfg}/test/0000.parquet", repo_type="dataset",
                        revision="refs/convert/parquet")
    return [dict(r, _config=cfg) for r in pq.read_table(p).to_pylist()]


def czy_czysty(tekst):
    w = SLOWO.findall(tekst.lower())
    for i in range(len(w) - N + 1):
        if hash(tuple(w[i:i + N])) in EVAL_NGRAMY:
            return False
    return True


def pliki_komponentow(fs, rew, pack):
    baza = f"datasets/{REPO}@{rew}"
    shared = [p.split("/")[-1] for p in fs.ls(f"{baza}/shared", detail=False)]
    print("shared:", shared, flush=True)
    komp = {"web": [f"{baza}/pack-{pack:02d}/web.parquet"],
            "core": [f"{baza}/shared/{n}" for n in shared if n.startswith("core")],
            "legal": [f"{baza}/shared/{n}" for n in shared if n.startswith("legal")],
            "en": [f"{baza}/shared/{n}" for n in shared if n.startswith("en")]}
    return komp


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tokenizer", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--tokeny_train", type=float, default=2e8)
    p.add_argument("--tokeny_heldout", type=float, default=4.2e6)
    p.add_argument("--pack", type=int, default=7)
    p.add_argument("--seed", type=int, default=20261030)
    p.add_argument("--procesy", type=int, default=max(1, mp.cpu_count() - 2))
    a = p.parse_args()
    wyj = Path(a.wyjscie)
    wyj.mkdir(parents=True, exist_ok=True)

    import pyarrow.parquet as pq
    from huggingface_hub import HfApi, HfFileSystem
    from tokenizers import Tokenizer

    t0 = time.time()
    ev = teksty_ewaluacji()
    for k, teksty in ev.items():
        przed = len(EVAL_NGRAMY)
        for t in teksty:
            EVAL_NGRAMY.update(ngramy(t))
        print(f"ewaluacja {k}: {len(teksty)} tekstów, +{len(EVAL_NGRAMY) - przed} 13-gramów", flush=True)

    rew = HfApi().dataset_info(REPO).sha
    fs = HfFileSystem()
    komp = pliki_komponentow(fs, rew, a.pack)
    tok = Tokenizer.from_file(a.tokenizer)
    assert tok.token_to_id("<|endoftext|>") == 0

    # Udział w obrębie komponentu (core vs core_sa, legal vs legal_sa) proporcjonalnie do rozmiaru pliku.
    cele = {}
    for k, pliki in komp.items():
        rozm = {f: fs.info(f)["size"] for f in pliki}
        suma = sum(rozm.values())
        for f in pliki:
            cele[f] = (k, UDZIALY[k] * rozm[f] / suma)
    rng = random.Random(a.seed)
    pool = mp.get_context("fork").Pool(a.procesy)
    train_docs, held, stat = [], {}, {}
    przyklady = []
    for f, (k, udzial) in cele.items():
        cel_tr, cel_ho = udzial * a.tokeny_train, udzial * a.tokeny_heldout
        pf = pq.ParquetFile(fs.open(f, "rb", block_size=64 * 2 ** 20))
        kol = "text" if "text" in pf.schema_arrow.names else pf.schema_arrow.names[0]
        grupy = list(range(pf.num_row_groups))
        rng.shuffle(grupy)
        s = {"plik": f, "komponent": k, "kolumna": kol, "grup": pf.num_row_groups, "wierszy": pf.metadata.num_rows,
             "docs_train": 0, "docs_heldout": 0, "tok_train": 0, "tok_heldout": 0, "usuniete_dekontaminacja": 0,
             "grupy_uzyte": 0}
        ho = []
        for g in grupy:
            if s["tok_train"] >= cel_tr and s["tok_heldout"] >= cel_ho:
                break
            teksty = [t for t in pf.read_row_group(g, columns=[kol]).column(0).to_pylist() if t]
            s["grupy_uzyte"] += 1
            rng.shuffle(teksty)
            maska = pool.map(czy_czysty, teksty, chunksize=64)
            s["usuniete_dekontaminacja"] += maska.count(False)
            teksty = [t for t, m in zip(teksty, maska) if m]
            enc = tok.encode_batch(teksty, add_special_tokens=False)
            if len(przyklady) < 2 and enc:
                przyklady.append({"komponent": k, "tekst": teksty[0][:200],
                                  "tokeny": [tok.id_to_token(i) for i in enc[0].ids[:40]]})
            for e in enc:
                ids = np.asarray([0] + e.ids, dtype=np.uint16)
                if s["tok_heldout"] < cel_ho and rng.random() < 0.05:
                    ho.append(ids); s["tok_heldout"] += len(ids); s["docs_heldout"] += 1
                elif s["tok_train"] < cel_tr:
                    train_docs.append(ids); s["tok_train"] += len(ids); s["docs_train"] += 1
            print(f"{k} {f.split('/')[-1]} grupa {g}: train {s['tok_train']/1e6:.1f}M/{cel_tr/1e6:.1f}M "
                  f"heldout {s['tok_heldout']/1e6:.2f}M usunięte {s['usuniete_dekontaminacja']} "
                  f"{time.time()-t0:.0f}s", flush=True)
        held.setdefault(k, []).extend(ho)
        stat[f] = s
    pool.close()

    rng.shuffle(train_docs)
    tr = np.concatenate(train_docs)
    tr.tofile(wyj / "train.bin")
    zakresy, czesci, pos = {}, [], 0
    for k in UDZIALY:
        if held.get(k):
            c = np.concatenate(held[k])
            zakresy[k] = [pos, pos + len(c)]
            pos += len(c)
            czesci.append(c)
    ho = np.concatenate(czesci)
    ho.tofile(wyj / "val.bin")
    (wyj / "heldout_meta.json").write_text(json.dumps({"zakresy": zakresy}, indent=1))
    sha = {n: hashlib.sha256((wyj / n).read_bytes()).hexdigest() for n in ("train.bin", "val.bin")}
    out = {"repo": REPO, "rewizja": rew, "pack": a.pack, "udzialy": UDZIALY, "seed": a.seed,
           "tokeny_train": int(len(tr)), "tokeny_heldout": int(len(ho)), "pliki": stat, "sha256": sha,
           "ngramy_ewaluacji": len(EVAL_NGRAMY), "n": N, "przyklady_tokenizacji": przyklady,
           "pubmedqa_config": pubmedqa_docs()[0]["_config"], "czas_s": round(time.time() - t0)}
    (wyj / "statystyki.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k != "pliki"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
