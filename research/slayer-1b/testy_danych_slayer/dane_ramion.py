"""Dane trzech ramion (C, E25, PLHQ) i wspólny heldout, tokenizacja Slayera.

Na instancji (PYTHONHASHSEED ustawia skrypt sam, ponownym execem):
  python testy_danych_slayer/dane_ramion.py --tokenizer /workspace/m106/tokenizer.json \
      --wyjscie /workspace/dane_ramion --tokeny_train 160e6

Próba lokalna (bez sieci, pliki parquet w układzie repo HF pod --lokalne, ewaluacje z cache HF):
  python testy_danych_slayer/dane_ramion.py --tokenizer tokenizer/tokenizer.json --wyjscie $TMPDIR/r \
      --lokalne $TMPDIR/fikstura --tokeny_train 2e4 --skala_heldout 0.002 --proba

Ramiona różnią się wyłącznie składem (RAMIONA). Pule dokumentów są wspólne i zagnieżdżone: każdy plik ma
własny generator (seed|plik), więc ramię bierze PREFIKS tej samej uporządkowanej puli. C i PLHQ mają
identyczne dokumenty core/legal/en, C i E25 mają te same dokumenty PL (E25 krótszy prefiks) i ten sam
początek puli EN. Heldout jest jeden dla wszystkich ramion i odjęty od pul przed podziałem.

Wyjście: {C,E25,PLHQ}/train.bin (uint16, równa długość we wszystkich ramionach, dokumenty z tokenem 0
z przodu), {ramię}/val.bin i heldout_meta.json (kopie wspólnego heldoutu), heldout/val.bin,
statystyki.json (tokeny per ramię × komponent, dekontaminacja, dedup FW2-HQ wobec HPLT, rewizje, sha256).
"""

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import random
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np

REPO = "SlayerLab/slayer-pl-8x3b"
HQ_REPO = "epfml/FineWeb2-HQ"
HQ_KATALOG = "pol_Latn"
N = 13
SLOWO = re.compile(r"\w+", re.UNICODE)
PROBKA_DEDUP = 16    # do szkicu HPLT wchodzi 13-gram, gdy hash % 16 == 0 (deterministyczne próbkowanie)
PROG_DUP = 0.5       # dokument FW2-HQ jest duplikatem HPLT, gdy >= 50% jego próbkowanych 13-gramów jest w szkicu
MIN_PROBEK = 4       # krótszy szkic: dokument zostaje, liczony jako „niesprawdzony”

_PL = 0.75 / 0.90    # E25: 15 pp z PL proporcjonalnie, proporcje web/core/legal jak u Arka
RAMIONA = {
    "C": {"web_hplt": 0.63, "core": 0.19, "legal": 0.08, "en": 0.10},
    "C2": {"web_hplt": 0.63, "core": 0.19, "legal": 0.08, "en": 0.10},  # C z inną kolejnością: szum kolejności
    "E25": {"web_hplt": 0.63 * _PL, "core": 0.19 * _PL, "legal": 0.08 * _PL, "en": 0.25},
    "PLHQ": {"web_hq": 0.63, "core": 0.19, "legal": 0.08, "en": 0.10},
}
# Klucz kolejności dokumentów: wspólny dla C/E25/PLHQ (wspólne dokumenty w tym samym porządku względnym),
# inny tylko dla C2.
KOLEJNOSC = {"C": "k1", "E25": "k1", "PLHQ": "k1", "C2": "k2"}
HELDOUT = {"web_hplt": 1.0e6, "web_hq": 1.0e6, "core": 1.0e6, "legal": 0.5e6, "en": 1.5e6}

EVAL_NGRAMY = set()
INDEKS_HPLT = None


# ---------------------------------------------------------------- czyste funkcje (testy: test_dane_ramion.py)

def procesy_domyslne():
    """Rdzenie dostępne procesowi (cgroup/affinity, jak `nproc`), nie rdzenie hosta z mp.cpu_count()."""
    try:
        n = len(os.sched_getaffinity(0))
    except AttributeError:  # macOS
        n = os.cpu_count() or 1
    return max(1, n - 1)


def slowa(tekst):
    return SLOWO.findall(tekst.lower())


def ngram_hashe(tekst):
    w = slowa(tekst)
    return [hash(tuple(w[i:i + N])) for i in range(len(w) - N + 1)]


def czy_czysty(tekst):
    return not any(h in EVAL_NGRAMY for h in ngram_hashe(tekst))


def szkic(tekst):
    """Próbkowane 13-gramy (hash % PROBKA_DEDUP == 0): ta sama reguła dla indeksu HPLT i dla kandydata."""
    return [h for h in ngram_hashe(tekst) if h % PROBKA_DEDUP == 0]


def udzial_duplikatu(probki, indeks):
    """Ułamek próbek obecnych w posortowanym indeksie; None, gdy próbek < MIN_PROBEK."""
    if len(probki) < MIN_PROBEK:
        return None
    a = np.asarray(probki, dtype=np.int64)
    pos = np.searchsorted(indeks, a)
    pos[pos >= len(indeks)] = 0
    return float(np.mean(indeks[pos] == a)) if len(indeks) else 0.0


def cele_plikow(sklad, rozmiary, tokeny):
    """{komponent: udział}, {komponent: {plik: bajty}} -> {plik: tokeny celu}; udział pliku w komponencie ∝ rozmiar."""
    out = {}
    for k, u in sklad.items():
        suma = sum(rozmiary[k].values())
        for f, r in rozmiary[k].items():
            out[f] = u * tokeny * r / suma
    return out


def prefiks(pula, cel):
    """Najkrótszy prefiks listy dokumentów (tablice tokenów) o sumie >= cel."""
    out, s = [], 0
    for d in pula:
        if s >= cel:
            break
        out.append(d)
        s += len(d)
    return out, s


def klucz_kolejnosci(seed, ids):
    return hashlib.blake2b(ids.tobytes(), digest_size=8, key=str(seed).encode()[:64]).digest()


def sklej_ramie(dokumenty, tokeny, seed):
    """Porządkuje dokumenty kluczem (seed, treść) i tnie konkatenację do dokładnie `tokeny` tokenów.

    Kolejność dokumentu zależy tylko od jego treści i seeda, więc dokumenty wspólne dla dwóch ramion
    z tym samym seedem stoją w tym samym porządku względnym, bez względu na resztę ramienia."""
    docs = sorted(dokumenty, key=lambda d: klucz_kolejnosci(seed, d))
    tr = np.concatenate(docs) if docs else np.zeros(0, dtype=np.uint16)
    if len(tr) < tokeny:
        raise SystemExit(f"STOP: ramię ma {len(tr)} tokenów, cel {tokeny}")
    return tr[:tokeny]


# ---------------------------------------------------------------- źródła

class Zrodla:
    """Pliki parquet z HF (HfFileSystem, odczyt tylko potrzebnych kolumn) albo z katalogu lokalnego tego samego układu."""

    def __init__(self, lokalne=None):
        self.lokalne = Path(lokalne) if lokalne else None
        self.rew = {}
        if not self.lokalne:
            from huggingface_hub import HfApi, HfFileSystem
            self.fs = HfFileSystem()
            api = HfApi()
            self.rew = {REPO: api.dataset_info(REPO).sha, HQ_REPO: api.dataset_info(HQ_REPO).sha}

    def sciezka(self, repo, wzgl):
        if self.lokalne:
            return str(self.lokalne / repo.split("/")[-1] / wzgl)
        return f"datasets/{repo}@{self.rew[repo]}/{wzgl}"

    def ls(self, repo, wzgl):
        if self.lokalne:
            return sorted(p.name for p in (self.lokalne / repo.split("/")[-1] / wzgl).iterdir())
        return sorted(p.split("/")[-1] for p in self.fs.ls(self.sciezka(repo, wzgl), detail=False))

    def rozmiar(self, sciezka):
        return Path(sciezka).stat().st_size if self.lokalne else self.fs.info(sciezka)["size"]

    def na_dysk(self, repo, wzgl, cache):
        """Ścieżka lokalna pliku (pobranie hf_hub_download). Workery puli czytają tylko pliki lokalne,
        bo HfFileSystem odziedziczony przez fork nie jest sprawdzony."""
        if self.lokalne:
            return self.sciezka(repo, wzgl)
        from huggingface_hub import hf_hub_download
        return hf_hub_download(repo, wzgl, repo_type="dataset", revision=self.rew[repo], local_dir=cache)

    def parquet(self, sciezka):
        import pyarrow.parquet as pq
        if self.lokalne:
            return pq.ParquetFile(sciezka)
        return pq.ParquetFile(self.fs.open(sciezka, "rb", block_size=64 * 2 ** 20))


ZR = None


def komponenty(zr, pack, hq_pliki, seed):
    shared = zr.ls(REPO, "shared")
    hq = [n for n in zr.ls(HQ_REPO, HQ_KATALOG) if n.endswith(".parquet")]
    rng = random.Random(f"{seed}|hq")
    hq_wybrane = sorted(rng.sample(hq, min(hq_pliki, len(hq))))
    return {"web_hplt": [zr.sciezka(REPO, f"pack-{pack:02d}/web.parquet")],
            "web_hq": [zr.sciezka(HQ_REPO, f"{HQ_KATALOG}/{n}") for n in hq_wybrane],
            "core": [zr.sciezka(REPO, f"shared/{n}") for n in shared if n.startswith("core")],
            "legal": [zr.sciezka(REPO, f"shared/{n}") for n in shared if n.startswith("legal")],
            "en": [zr.sciezka(REPO, f"shared/{n}") for n in shared if n.startswith("en")]}


# ---------------------------------------------------------------- ewaluacje do dekontaminacji

def teksty_ewaluacji(proba):
    """Teksty wszystkich testów: główne i szuflada (BETR). Brak zbioru = STOP, w --proba tylko odnotowany."""
    from datasets import load_dataset
    out, braki = {}, {}

    def dodaj(nazwa, fn):
        try:
            out[nazwa] = fn()
        except Exception as e:  # noqa: BLE001
            if not proba:
                raise
            braki[nazwa] = f"{type(e).__name__}: {str(e)[:120]}"

    def arc(cfg):
        d = load_dataset("allenai/ai2_arc", cfg, revision="210d026faf9955653af8916fad021475a3f00453")["test"]
        return [r["question"] + " " + " ".join(r["choices"]["text"]) for r in d]

    def mmlu():
        d = load_dataset("cais/mmlu", "all")
        return [r["question"] + " " + " ".join(r["choices"]) for s in ("test", "dev") for r in d[s]]

    def siqa():
        d = load_dataset("allenai/social_i_qa", revision="refs/convert/parquet")["validation"]
        return [f"{r['context']} {r['question']} {r['answerA']} {r['answerB']} {r['answerC']}" for r in d]

    def belebele():
        d = load_dataset("facebook/belebele", "pol_Latn")["test"]
        return list({r["flores_passage"] for r in d}) + \
            [r["question"] + " " + " ".join(r[f"mc_answer{j}"] for j in range(1, 5)) for r in d]

    def multiblimp():
        import csv
        from huggingface_hub import hf_hub_download
        p = hf_hub_download("jumelet/multiblimp", "pol/data.tsv", repo_type="dataset",
                            revision="de923efa8d2483d6b13364ee68e65308e990a991")
        csv.field_size_limit(10 ** 8)
        with open(p, encoding="utf-8") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        return [r["sen"] for r in rows] + [r["wrong_sen"] for r in rows]

    def hellaswag():
        d = load_dataset("Rowan/hellaswag", revision="refs/convert/parquet")["validation"]
        return [f"{r['ctx']} {' '.join(r['endings'])}" for r in d]

    def piqa():
        d = load_dataset("baber/piqa")["validation"]
        return [f"{r['goal']} {r['sol1']} {r['sol2']}" for r in d]

    def gmmlu_pl():
        d = load_dataset("CohereLabs/Global-MMLU", "pl")
        return [" ".join([r["question"], r["option_a"], r["option_b"], r["option_c"], r["option_d"]])
                for s in ("test", "dev") for r in d[s]]

    def llmzszl():
        d = load_dataset("amu-cai/llmzszl-dataset")["test"]
        return [r["question"] + " " + " ".join(r["answers"]) for r in d]

    for nazwa, fn in [("arc_c", lambda: arc("ARC-Challenge")), ("arc_e", lambda: arc("ARC-Easy")), ("mmlu", mmlu),
                      ("siqa", siqa), ("belebele_pl", belebele), ("multiblimp_pl", multiblimp),
                      ("hellaswag", hellaswag), ("piqa", piqa), ("gmmlu_pl", gmmlu_pl), ("llmzszl_cke", llmzszl)]:
        dodaj(nazwa, fn)
    return out, braki


# ---------------------------------------------------------------- indeks HPLT (dedup FW2-HQ)

def _szkic_grupy(arg):
    import pyarrow.parquet as pq
    sciezka, g = arg
    teksty = pq.ParquetFile(sciezka).read_row_group(g, columns=["text"]).column(0).to_pylist()
    h = [x for t in teksty if t for x in szkic(t)]
    return np.asarray(h, dtype=np.int64), len(teksty)


def zbuduj_indeks(zr, packi, pool, cache, limit_grup=None):
    import pyarrow.parquet as pq
    zadania = []
    for p in packi:
        s = zr.na_dysk(REPO, f"pack-{p:02d}/web.parquet", cache)
        n = pq.ParquetFile(s).num_row_groups
        zadania += [(s, g) for g in range(n if limit_grup is None else min(n, limit_grup))]
    czesci, docs = [], 0
    for i, (h, n) in enumerate(pool.imap_unordered(_szkic_grupy, zadania, chunksize=1)):
        czesci.append(h)
        docs += n
        if i % 50 == 0:
            print(f"indeks HPLT: grupa {i + 1}/{len(zadania)}, dokumentów {docs}", flush=True)
    return np.unique(np.concatenate(czesci)) if czesci else np.zeros(0, dtype=np.int64), docs


def _filtr_hq(tekst):
    if not czy_czysty(tekst):
        return "dekontaminacja"
    u = udzial_duplikatu(szkic(tekst), INDEKS_HPLT)
    if u is None:
        return "ok_niesprawdzony"
    return "duplikat_hplt" if u >= PROG_DUP else "ok"


def _filtr(tekst):
    return "ok" if czy_czysty(tekst) else "dekontaminacja"


# ---------------------------------------------------------------- pule

def zbuduj_pule(zr, plik, komp, cel_puli, cel_ho, tok, pool, seed):
    """Uporządkowana pula dokumentów pliku i jego część heldoutu; deterministyczna dla (seed, plik)."""
    rng = random.Random(f"{seed}|{plik.split('@')[-1]}")
    pf = zr.parquet(plik)
    nazwy = pf.schema_arrow.names
    kol = ["text"] + (["source_id"] if "source_id" in nazwy else [])
    grupy = list(range(pf.num_row_groups))
    rng.shuffle(grupy)
    s = {"plik": plik, "komponent": komp, "grup": pf.num_row_groups, "wierszy": pf.metadata.num_rows,
         "docs_pula": 0, "docs_heldout": 0, "tok_pula": 0, "tok_heldout": 0, "grupy_uzyte": 0, "filtr": {}}
    pula, ho = [], []
    filtr = _filtr_hq if komp == "web_hq" else _filtr
    przyklad = None
    for g in grupy:
        if s["tok_pula"] >= cel_puli and s["tok_heldout"] >= cel_ho:
            break
        t = pf.read_row_group(g, columns=kol)
        teksty = t.column("text").to_pylist()
        zrodla = t.column("source_id").to_pylist() if "source_id" in kol else [None] * len(teksty)
        para = [(x, z) for x, z in zip(teksty, zrodla) if x]
        rng.shuffle(para)
        werdykty = pool.map(filtr, [x for x, _ in para], chunksize=64)
        for w in werdykty:
            s["filtr"][w] = s["filtr"].get(w, 0) + 1
        para = [p for p, w in zip(para, werdykty) if w.startswith("ok")]
        s["grupy_uzyte"] += 1
        enc = tok.encode_batch([x for x, _ in para], add_special_tokens=False)
        if przyklad is None and enc:
            przyklad = {"komponent": komp, "tekst": para[0][0][:200], "tokeny": [tok.id_to_token(i) for i in enc[0].ids[:40]]}
        for (x, z), e in zip(para, enc):
            ids = np.asarray([0] + e.ids, dtype=np.uint16)
            if s["tok_heldout"] < cel_ho and rng.random() < 0.05:
                etyk = komp if komp != "en" else f"en:{z or 'brak'}"
                ho.append((etyk, ids)); s["tok_heldout"] += len(ids); s["docs_heldout"] += 1
            elif s["tok_pula"] < cel_puli:
                pula.append(ids); s["tok_pula"] += len(ids); s["docs_pula"] += 1
        print(f"{komp} {plik.split('/')[-1]} grupa {g}: pula {s['tok_pula'] / 1e6:.2f}M/{cel_puli / 1e6:.2f}M "
              f"heldout {s['tok_heldout'] / 1e6:.3f}M filtr {s['filtr']}", flush=True)
    if s["tok_pula"] < cel_puli:
        print(f"UWAGA: pula {plik} niepełna ({s['tok_pula']} < {cel_puli:.0f})", flush=True)
    return pula, ho, s, przyklad


# ---------------------------------------------------------------- main

def main():
    if os.environ.get("PYTHONHASHSEED") != "0":
        os.execve(sys.executable, [sys.executable] + sys.argv, {**os.environ, "PYTHONHASHSEED": "0"})
    global ZR, INDEKS_HPLT
    p = argparse.ArgumentParser()
    p.add_argument("--tokenizer", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--tokeny_train", type=float, default=160e6)
    p.add_argument("--skala_heldout", type=float, default=1.0)
    p.add_argument("--pack", type=int, default=7)
    p.add_argument("--dedup_packi", default="0,1,2,3,4,5,6,7")
    p.add_argument("--hq_pliki", type=int, default=8)
    p.add_argument("--seed", type=int, default=20261030)
    p.add_argument("--procesy", type=int, default=procesy_domyslne(),
                   help="domyślnie rdzenie dostępne procesowi (jak nproc), minus 1")
    p.add_argument("--ewal_teksty", help="JSON {zbiór: [teksty]} zamiast pobierania z HF (testy)")
    p.add_argument("--lokalne")
    p.add_argument("--cache", default="/workspace/hf_pliki", help="katalog na packi HPLT pobrane do indeksu dedupu")
    p.add_argument("--limit_grup_indeksu", type=int)
    p.add_argument("--proba", action="store_true", help="brak zbioru ewaluacji nie przerywa (tylko próba lokalna)")
    a = p.parse_args()
    wyj = Path(a.wyjscie)
    wyj.mkdir(parents=True, exist_ok=True)
    from tokenizers import Tokenizer

    t0 = time.time()
    if a.ewal_teksty:
        ev, braki = json.loads(Path(a.ewal_teksty).read_text()), {"wszystkie": "podane --ewal_teksty"}
    else:
        ev, braki = teksty_ewaluacji(a.proba)
    for k, teksty in ev.items():
        przed = len(EVAL_NGRAMY)
        for t in teksty:
            EVAL_NGRAMY.update(ngram_hashe(t))
        print(f"ewaluacja {k}: {len(teksty)} tekstów, +{len(EVAL_NGRAMY) - przed} 13-gramów", flush=True)
    if braki:
        print("BRAKI ewaluacji (tylko --proba):", braki, flush=True)

    ZR = Zrodla(a.lokalne)
    tok = Tokenizer.from_file(a.tokenizer)
    assert tok.token_to_id("<|endoftext|>") == 0
    assert tok.get_vocab_size() <= 65536, "uint16"
    packi = [int(x) for x in a.dedup_packi.split(",") if x != ""]

    # Indeks HPLT budowany przed pulą procesów filtra: workery dziedziczą go przez fork.
    pool = mp.get_context("fork").Pool(a.procesy)
    INDEKS_HPLT, docs_idx = zbuduj_indeks(ZR, packi, pool, a.cache, a.limit_grup_indeksu)
    pool.close()
    print(f"indeks HPLT: {len(INDEKS_HPLT)} próbek z {docs_idx} dokumentów, packi {packi}, {time.time() - t0:.0f}s",
          flush=True)
    pool = mp.get_context("fork").Pool(a.procesy)

    komp = komponenty(ZR, a.pack, a.hq_pliki, a.seed)
    rozm = {k: {f: ZR.rozmiar(f) for f in pliki} for k, pliki in komp.items()}
    T = int(a.tokeny_train)
    cele = {r: cele_plikow({k: u for k, u in s.items()}, rozm, T) for r, s in RAMIONA.items()}
    pule, held, stat, przyklady = {}, {}, {}, []
    for k, pliki in komp.items():
        suma = sum(rozm[k].values())
        for f in pliki:
            cel_puli = max(c.get(f, 0) for c in cele.values()) * 1.02  # zapas na nadmiar prefiksu
            cel_ho = HELDOUT[k] * a.skala_heldout * rozm[k][f] / suma
            pula, ho, s, prz = zbuduj_pule(ZR, f, k, cel_puli, cel_ho, tok, pool, a.seed)
            pule[f] = pula
            for etyk, ids in ho:
                held.setdefault(etyk, []).append(ids)
            stat[f] = s
            if prz and len(przyklady) < 3 and k in ("web_hplt", "web_hq", "core"):
                przyklady.append(prz)
    pool.close()

    # Heldout wspólny, posortowany po komponencie.
    (wyj / "heldout").mkdir(exist_ok=True)
    zakresy, czesci, pos = {}, [], 0
    for k in sorted(held):
        c = np.concatenate(held[k])
        zakresy[k] = [pos, pos + len(c)]
        pos += len(c)
        czesci.append(c)
    ho = np.concatenate(czesci)
    ho.tofile(wyj / "heldout" / "val.bin")
    (wyj / "heldout" / "heldout_meta.json").write_text(json.dumps({"zakresy": zakresy}, indent=1))

    ramiona = {}
    for r in RAMIONA:
        docs, sklad = [], {}
        for f, cel in cele[r].items():
            d, n = prefiks(pule[f], cel)
            docs += d
            k = stat[f]["komponent"]
            sklad[k] = sklad.get(k, 0) + n
        tr = sklej_ramie(docs, T, f"{a.seed}|{KOLEJNOSC[r]}")
        (wyj / r).mkdir(exist_ok=True)
        tr.tofile(wyj / r / "train.bin")
        for n in ("val.bin", "heldout_meta.json"):
            shutil.copyfile(wyj / "heldout" / n, wyj / r / n)
        suma = sum(sklad.values())
        ramiona[r] = {"tokeny_przed_cieciem": sklad, "udzial_zrealizowany": {k: v / suma for k, v in sklad.items()},
                      "tokeny_train": int(len(tr)),
                      "sha256_train": hashlib.sha256((wyj / r / "train.bin").read_bytes()).hexdigest()}
        print(r, json.dumps(ramiona[r]["udzial_zrealizowany"]), flush=True)

    out = {"repo": REPO, "hq_repo": HQ_REPO, "rewizje": ZR.rew, "lokalne": a.lokalne, "pack": a.pack,
           "ramiona_sklad": RAMIONA, "kolejnosc": KOLEJNOSC, "ramiona": ramiona,
           "en_komponenty": [k for k in zakresy if k.startswith("en")], "seed": a.seed, "tokeny_train": T,
           "heldout": {"zakresy": zakresy, "tokeny": int(len(ho)),
                       "sha256": hashlib.sha256((wyj / "heldout" / "val.bin").read_bytes()).hexdigest()},
           "dedup": {"packi": packi, "probka_co": PROBKA_DEDUP, "prog": PROG_DUP, "min_probek": MIN_PROBEK,
                     "probek_w_indeksie": int(len(INDEKS_HPLT)), "dokumentow_hplt": docs_idx,
                     "limit_grup_indeksu": a.limit_grup_indeksu},
           "ngramy_ewaluacji": len(EVAL_NGRAMY), "n": N, "braki_ewaluacji": braki,
           "zbiory_ewaluacji": sorted(ev), "pliki": stat, "przyklady_tokenizacji": przyklady,
           "czas_s": round(time.time() - t0)}
    (wyj / "statystyki.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k != "pliki"}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
