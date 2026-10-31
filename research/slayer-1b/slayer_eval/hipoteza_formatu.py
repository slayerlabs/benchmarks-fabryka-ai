"""Pomiar hipotezy formatu: czy Slayer 1B nie wie, czy nie radzi sobie z formatem litery.

Jeden scorer loglik dla modeli HF (Pythia, Qwen) i dla Slayera (slayer_model.py), kodowanie
par kontekst/kontynuacja jak lm-eval 0.4.9.1 (HFLM: bez BOS, pusty kontekst = token EOT;
Slayer: zawsze jeden BOS <|endoftext|>, jak w METHOD.md Space). Ten sam scorer przechodzi
test 0 (Pythia/Qwen vs opublikowane liczby), zanim mierzymy nim Slayera.

  python slayer_eval/hipoteza_formatu.py licz --model <katalog> --etykieta 1.06 \
      --zadania arc_c_cloze,arc_c_mc --wyjscie wyniki/1.06 [--device mps] [--limit N]
  python slayer_eval/hipoteza_formatu.py wikitext --model <katalog_slayera> --wyjscie wyniki/1.06
  python slayer_eval/hipoteza_formatu.py zgodnosc --model <katalog> --n 20   # MPS vs CPU
  python slayer_eval/hipoteza_formatu.py analiza --wyniki wyniki

Wyjście `licz`: <wyjscie>/<zadanie>.jsonl, wiersz na pytanie (logliki opcji, bezwarunkowe,
bajty/znaki/tokeny), dopisywane przyrostowo (wznowienie pomija gotowe id), oraz
trace/T02_space.jsonl i trace/T02_mc.jsonl w formacie trace_pytan.py dla porownaj_checkpointy.py.
"""

import argparse
import json
import math
import os
import sys
import time
from collections import Counter
from pathlib import Path

import torch

KATALOG = Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG))

LITERY = "ABCDEFGH"
LN2 = math.log(2)
ARC_REW = "210d026faf9955653af8916fad021475a3f00453"
MED_REW = "91c6572c454088bf71b679ad90aa8dffcd0d5868"
WIKI_REW = "647234772b9554e208af6c826f23b99e3cac88c8"


# ---------------------------------------------------------------- modele

class ModelHF:
    def __init__(self, katalog, device):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(katalog)
        self.m = AutoModelForCausalLM.from_pretrained(katalog, torch_dtype=torch.float32).to(device).eval()
        self.device = device
        eot = self.tok.eos_token_id
        # empty context = lm-eval HFLM prefix_token_id: BOS when the tokenizer has one, else EOS
        bos = self.tok.bos_token_id
        self.prefiks, self.prefiks_pusty = [], [bos if bos is not None else eot]
        self.pad = eot if eot is not None else 0
        self.max_len = min(getattr(self.m.config, "max_position_embeddings", 2048), 4096)

    def encode(self, s):
        return self.tok(s, add_special_tokens=False).input_ids

    @torch.no_grad()
    def logits(self, ids):
        return self.m(ids).logits.float()

    @torch.no_grad()
    def ukryte(self, ids):
        return self.m.base_model(ids).last_hidden_state

    @torch.no_grad()
    def glowa(self, h):
        return self.m.get_output_embeddings()(h).float()


class ModelSlayer:
    def __init__(self, katalog, device):
        from slayer_model import Slayer
        self.s = Slayer(katalog, device=device)
        self.device = device
        self.prefiks, self.prefiks_pusty = [self.s.bos], [self.s.bos]
        self.pad = 0
        self.max_len = self.s.blok

    def encode(self, s):
        return self.s.encode(s)

    def logits(self, ids):
        return self.s.logits(ids)

    def ukryte(self, ids):
        return self.s.ukryte(ids)

    def glowa(self, h):
        return self.s.glowa(h)


def zbuduj_model(katalog, device):
    cfg = json.loads((Path(katalog) / "config.json").read_text())
    return ModelSlayer(katalog, device) if "n_embd" in cfg and "model_type" not in cfg else ModelHF(katalog, device)


def para(model, ctx, cont):
    """(ids kontekstu, ids kontynuacji) jak lm-eval _encode_pair: końcowe spacje kontekstu idą do kontynuacji."""
    n_sp = len(ctx) - len(ctx.rstrip())
    if n_sp:
        cont, ctx = ctx[-n_sp:] + cont, ctx[:-n_sp]
    if ctx == "":
        ce = list(model.prefiks_pusty)
        return ce, model.encode(cont)
    whole = model.prefiks + model.encode(ctx + cont)
    ce = model.prefiks + model.encode(ctx)
    return ce, whole[len(ce):]


def licz_logliki(model, pary, batch=16):
    """pary: [(ctx_ids, cont_ids)] -> [(suma logprob, liczba tokenów)]; batchowanie po długości, prawy padding."""
    wynik = [None] * len(pary)
    kolej = sorted(range(len(pary)), key=lambda i: -(len(pary[i][0]) + len(pary[i][1])))
    for s in range(0, len(kolej), batch):
        idx = kolej[s:s + batch]
        seqs = []
        for i in idx:
            ce, co = pary[i]
            pelne = (ce + co)[-(model.max_len + 1):]
            seqs.append((pelne, len(co)))
        T = max(len(p) - 1 for p, _ in seqs)
        x = torch.full((len(seqs), T), model.pad, dtype=torch.long)
        for j, (p, _) in enumerate(seqs):
            x[j, :len(p) - 1] = torch.tensor(p[:-1])
        # Głowa (V do 151k) tylko na pozycjach kontynuacji: pełne logity batcha nie mieszczą się w pamięci.
        h = model.ukryte(x.to(model.device))
        for j, (i, (p, nc)) in enumerate(zip(idx, seqs)):
            L = len(p) - 1
            lp = torch.log_softmax(model.glowa(h[j, L - nc:L]), -1).cpu()
            cel = torch.tensor(p[-nc:])
            wynik[i] = (lp.gather(1, cel[:, None]).sum().item(), nc)
    return wynik


# ---------------------------------------------------------------- zadania

def _ds(repo, nazwa, rew, split):
    from datasets import load_dataset
    return load_dataset(repo, nazwa, revision=rew)[split]


def arc_doc(d):
    return {"id": d["id"], "pytanie": d["question"], "opcje": list(d["choices"]["text"]),
            "gold": list(d["choices"]["label"]).index(d["answerKey"])}


def med_doc(d):
    return {"id": d["id"], "pytanie": d["question"], "opcje": [d["opa"], d["opb"], d["opc"], d["opd"]], "gold": int(d["cop"])}


def prompt_cloze(doc):
    return "Question: " + doc["pytanie"] + "\nAnswer:", [" " + o for o in doc["opcje"]]


def prompt_arc_mc(doc):
    opcje = "\n".join(f"{LITERY[i]}. {t}" for i, t in enumerate(doc["opcje"]))
    return f"Question: {doc['pytanie']}\n{opcje}\nAnswer:", [" " + LITERY[i] for i in range(len(doc["opcje"]))]


def prompt_med_mc(doc):
    # lm-eval medmcqa/utils_medmcqa.py doc_to_text (format Space T45)
    p = "Question: " + doc["pytanie"] + "\nChoices:\n"
    for i, o in enumerate(doc["opcje"]):
        p += f"{LITERY[i]}. {o}\n"
    return p + "Answer:", [" " + LITERY[i] for i in range(len(doc["opcje"]))]


def przesun(doc):
    """Cykliczne przesunięcie treści odpowiedzi A->B->C->D->A; poprawna treść idzie z nią."""
    k = len(doc["opcje"])
    nowe = [None] * k
    for i, o in enumerate(doc["opcje"]):
        nowe[(i + 1) % k] = o
    return {**doc, "opcje": nowe, "gold": (doc["gold"] + 1) % k}


_ARC_TRAIN = None


def prompt_cloze_25shot(doc):
    """ARC-C 25-shot jak raport Qwen2.5 (Table 5): 25 losowych przykładów z train (seed 1234 + id), format lm-eval."""
    global _ARC_TRAIN
    import random
    if _ARC_TRAIN is None:
        _ARC_TRAIN = [arc_doc(d) for d in _ds("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "train")]
    rng = random.Random(f"1234|{doc['id']}")
    przyklady = rng.sample(_ARC_TRAIN, 25)
    prefiks = "".join(f"Question: {p['pytanie']}\nAnswer: {p['opcje'][p['gold']]}\n\n" for p in przyklady)
    ctx, konty = prompt_cloze(doc)
    return prefiks + ctx, konty


def _arc_train():
    global _ARC_TRAIN
    if _ARC_TRAIN is None:
        _ARC_TRAIN = [arc_doc(d) for d in _ds("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "train")]
    return _ARC_TRAIN


def prompt_arc_mc_bez_spacji(doc):
    """Kontrola tokenizacji litery: odpowiedź „A" bez spacji po „Answer:"."""
    ctx, konty = prompt_arc_mc(doc)
    return ctx, [k.strip() for k in konty]


def _arc_mc_kshot(doc, k):
    import random
    rng = random.Random(f"1234|{k}|{doc['id']}")
    przyklady = rng.sample(_arc_train(), k)
    prefiks = ""
    for p in przyklady:
        c, _ = prompt_arc_mc(p)
        prefiks += f"{c} {LITERY[p['gold']]}\n\n"
    ctx, konty = prompt_arc_mc(doc)
    return prefiks + ctx, konty


def prompt_arc_mc_5shot(doc):
    return _arc_mc_kshot(doc, 5)


def prompt_arc_mc_25shot(doc):
    return _arc_mc_kshot(doc, 25)


def siqa_dane():
    d = _ds("allenai/social_i_qa", None, "refs/convert/parquet", "validation")
    return [{"id": f"siqa{i}", "kontekst": f"{r['context']} {r['question']}", "pytanie": f"{r['context']} {r['question']}",
             "opcje": [r["answerA"], r["answerB"], r["answerC"]], "gold": int(r["label"]) - 1} for i, r in enumerate(d)]


def prompt_siqa_cloze(doc):
    # format Space T46 (lm-eval social_iqa): "Q: {context} {question}\nA:" + " odpowiedź"
    return "Q: " + doc["kontekst"] + "\nA:", [" " + o for o in doc["opcje"]]


def prompt_siqa_mc(doc):
    opcje = "\n".join(f"{LITERY[i]}. {t}" for i, t in enumerate(doc["opcje"]))
    return f"Question: {doc['kontekst']}\n{opcje}\nAnswer:", [" " + LITERY[i] for i in range(len(doc["opcje"]))]


def belebele_dane():
    d = _ds("facebook/belebele", "pol_Latn", None, "test")
    return [{"id": f"{r['link']}#{r['question_number']}", "pasaz": r["flores_passage"], "pytanie": r["question"],
             "opcje": [r[f"mc_answer{j}"] for j in range(1, 5)], "gold": int(r["correct_answer_num"]) - 1} for r in d]


def prompt_belebele_mc(doc):
    # lm-eval belebele_pol_Latn: "P: …\nQ: …\nA: …\nB: …\nC: …\nD: …\nAnswer:" + " A"
    opcje = "\n".join(f"{LITERY[i]}: {t}" for i, t in enumerate(doc["opcje"]))
    return f"P: {doc['pasaz']}\nQ: {doc['pytanie']}\n{opcje}\nAnswer:", [" " + LITERY[i] for i in range(4)]


def prompt_belebele_cloze(doc):
    return f"P: {doc['pasaz']}\nQ: {doc['pytanie']}\nAnswer:", [" " + o for o in doc["opcje"]]


MMLU_PRZEDMIOTY = None


def mmlu_dane():
    import glob
    przedmioty = sorted({Path(p).name for p in glob.glob(os.path.expanduser("~/.cache/huggingface/datasets/cais___mmlu/*"))})
    out = []
    for s in przedmioty:
        for i, r in enumerate(_ds("cais/mmlu", s, None, "test")):
            out.append({"id": f"{s}|{i}", "grupa": s, "pytanie": r["question"], "opcje": list(r["choices"]), "gold": int(r["answer"])})
    return out


def prompt_mmlu_mc(doc):
    # lm-eval mmlu (default): opis przedmiotu + "{q}\nA. …\nB. …\nC. …\nD. …\nAnswer:" + " A"
    opis = f"The following are multiple choice questions (with answers) about {doc['grupa'].replace('_', ' ')}.\n\n"
    opcje = "\n".join(f"{LITERY[i]}. {t}" for i, t in enumerate(doc["opcje"]))
    return f"{opis}{doc['pytanie'].strip()}\n{opcje}\nAnswer:", [" " + LITERY[i] for i in range(len(doc["opcje"]))]


def multiblimp_dane():
    import csv
    import glob
    plik = glob.glob(os.path.expanduser(
        "~/.cache/huggingface/hub/datasets--jumelet--multiblimp/snapshots/de923efa8d2483d6b13364ee68e65308e990a991/pol/data.tsv"))
    if not plik:
        raise FileNotFoundError("MultiBLiMP pol/data.tsv nie ma w cache HF (BLOCKED)")
    csv.field_size_limit(10 ** 8)
    with open(plik[0], encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    return [{"id": f"mb{i}", "grupa": f"{r['phenomenon']}:{r['grammatical_feature']}>{r['ungrammatical_feature']}",
             "pytanie": "", "opcje": [r["sen"], r["wrong_sen"]], "gold": 0} for i, r in enumerate(rows)]


def blimp_dane():
    # BLiMP EN (Space T01): pinned snapshot from BLIMP_DIR or the HF cache, see blimp.py
    from blimp import wczytaj
    return [{k: v for k, v in d.items() if k != "rekord"} for d in wczytaj()]


def prompt_para(doc):
    # Space T04: pusty kontekst, zdanie po spacji, suma logprob
    return "", [" " + o for o in doc["opcje"]]


ZADANIA = {
    "arc_c_mc_bezspacji": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_arc_mc_bez_spacji, None, False),
    "arc_c_mc_5shot": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_arc_mc_5shot, None, False),
    "arc_c_mc_25shot": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_arc_mc_25shot, None, False),
    "arc_e_mc": (("allenai/ai2_arc", "ARC-Easy", ARC_REW, "test", arc_doc), prompt_arc_mc, None, False),
    "siqa_cloze": (siqa_dane, prompt_siqa_cloze, None, True),
    "siqa_mc": (siqa_dane, prompt_siqa_mc, None, False),
    "belebele_mc": (belebele_dane, prompt_belebele_mc, None, False),
    "belebele_cloze": (belebele_dane, prompt_belebele_cloze, None, True),
    "mmlu_mc": (mmlu_dane, prompt_mmlu_mc, None, False),
    "mmlu_cloze": (mmlu_dane, prompt_cloze, None, False),
    "multiblimp": (multiblimp_dane, prompt_para, None, False),
    "blimp": (blimp_dane, prompt_para, None, False),  # lm-eval blimp: empty context, " " + sentence
    "arc_c_cloze_25shot": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_cloze_25shot, None, False),
    # nazwa: (źródło, budowa promptu, przekształcenie, czy liczyć bezwarunkowe)
    "arc_c_cloze": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_cloze, None, True),
    "arc_c_mc": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_arc_mc, None, False),
    "arc_c_mc_przes": (("allenai/ai2_arc", "ARC-Challenge", ARC_REW, "test", arc_doc), prompt_arc_mc, przesun, False),
    "arc_e_cloze": (("allenai/ai2_arc", "ARC-Easy", ARC_REW, "test", arc_doc), prompt_cloze, None, False),
    "med_mc": (("openlifescienceai/medmcqa", None, MED_REW, "validation", med_doc), prompt_med_mc, None, False),
    "med_cloze": (("openlifescienceai/medmcqa", None, MED_REW, "validation", med_doc), prompt_cloze, None, True),
}


BUDOWY_TRESC = (prompt_cloze, prompt_cloze_25shot, prompt_siqa_cloze, prompt_belebele_cloze, prompt_para)


def dokumenty(nazwa, limit=None):
    zrodlo, _, prz, _ = ZADANIA[nazwa]
    if callable(zrodlo):
        docs = zrodlo()
    else:
        repo, cfg, rew, split, fn = zrodlo
        docs = [fn(d) for d in _ds(repo, cfg, rew, split)]
    if limit:
        docs = docs[:limit]
    return [prz(d) for d in docs] if prz else docs


def licz_zadanie(model, nazwa, plik, limit=None, batch=16, porcja=64):
    _, budowa, _, z_bezw = ZADANIA[nazwa]
    docs = dokumenty(nazwa, limit)
    gotowe = set()
    if plik.exists():
        gotowe = {json.loads(l)["id"] for l in plik.read_text().splitlines() if l.strip()}
    docs = [d for d in docs if d["id"] not in gotowe]
    t0 = time.time()
    for s in range(0, len(docs), porcja):
        czesc = docs[s:s + porcja]
        pary, mapa = [], []
        for di, d in enumerate(czesc):
            ctx, konty = budowa(d)
            for oi, c in enumerate(konty):
                pary.append(para(model, ctx, c)); mapa.append((di, "w", oi))
                if z_bezw:
                    pary.append(para(model, "", c)); mapa.append((di, "b", oi))
        ll = licz_logliki(model, pary, batch)
        wiersze = [{"id": d["id"], "grupa": d.get("grupa"), "gold": d["gold"], "k": len(d["opcje"]), "ll": [None] * len(d["opcje"]),
                    "ntok": [None] * len(d["opcje"]), "bezw": [None] * len(d["opcje"]) if z_bezw else None,
                    "bajty": [len(c.encode()) for c in budowa(d)[1]],
                    "znaki": [len(o) for o in (d["opcje"] if budowa in BUDOWY_TRESC else [LITERY[i] for i in range(len(d["opcje"]))])]}
                   for d in czesc]
        for (di, typ, oi), (v, n) in zip(mapa, ll):
            if typ == "w":
                wiersze[di]["ll"][oi] = v; wiersze[di]["ntok"][oi] = n
            else:
                wiersze[di]["bezw"][oi] = v
        with open(plik, "a") as f:
            for w in wiersze:
                f.write(json.dumps(w) + "\n")
        print(f"[{nazwa}] {s + len(czesc)}/{len(docs)}  {time.time() - t0:.0f}s", flush=True)


def argmax(xs):
    return max(range(len(xs)), key=lambda i: (xs[i], -i))


def wybory(w):
    ll, b, z = w["ll"], w["bajty"], w["znaki"]
    r = {"acc": argmax(ll), "acc_norm": argmax([l / max(c, 1) for l, c in zip(ll, z)]),
         "bpb": argmax([l / max(x, 1) for l, x in zip(ll, b)])}
    if w.get("bezw"):
        r["pmi"] = argmax([l - u for l, u in zip(ll, w["bezw"])])
    return r


def zapisz_trace(plik_wej, plik_trace):
    """Wiersze w formacie trace_pytan.trace_pytania (klucze czytane przez porownaj_checkpointy.py)."""
    linie = []
    for l in plik_wej.read_text().splitlines():
        w = json.loads(l)
        wyb = wybory(w)
        b = w["bajty"]
        g = w["gold"]
        kr = min(range(len(b)), key=lambda i: (b[i], i))
        dl = max(range(len(b)), key=lambda i: (b[i], -i))
        opcje = [{"pozycja": LITERY[i], "tekst_bajty": b[i], "tokeny": w["ntok"][i], "logprob": w["ll"][i],
                  "logprob_na_bajt": w["ll"][i] / max(b[i], 1), "logprob_na_token": w["ll"][i] / max(w["ntok"][i], 1),
                  **({"logprob_bezwarunkowy": w["bezw"][i], "pmi": w["ll"][i] - w["bezw"][i]} if w.get("bezw") else {})}
                 for i in range(w["k"])]
        linie.append(json.dumps({
            "id": w["id"], "poprawna": g, "poprawna_litera": LITERY[g], "k": w["k"],
            "bpb_poprawnej": -w["ll"][g] / (LN2 * max(b[g], 1)), "opcje": opcje,
            "wybor": {m: LITERY[v] for m, v in wyb.items()},
            "trafione": {m: v == g for m, v in wyb.items()},
            "wybor_najkrotsza": {m: v == kr for m, v in wyb.items()},
            "wybor_najdluzsza": {m: v == dl for m, v in wyb.items()},
            "poprawna_najkrotsza": g == kr, "poprawna_najdluzsza": g == dl}, ensure_ascii=False))
    plik_trace.parent.mkdir(parents=True, exist_ok=True)
    plik_trace.write_text("\n".join(linie) + "\n")


# ---------------------------------------------------------------- komendy

def cmd_licz(a):
    model = zbuduj_model(a.model, a.device)
    wyj = Path(a.wyjscie)
    wyj.mkdir(parents=True, exist_ok=True)
    for z in a.zadania.split(","):
        licz_zadanie(model, z, wyj / f"{z}.jsonl", a.limit, a.batch)
        if z == "arc_c_cloze":
            zapisz_trace(wyj / f"{z}.jsonl", wyj / "trace" / "T02_space.jsonl")
        if z == "arc_c_mc":
            zapisz_trace(wyj / f"{z}.jsonl", wyj / "trace" / "T02_mc.jsonl")


def cmd_zgodnosc(a):
    """Te same 20 pytań ARC-C (cloze + litery) na CPU i MPS: max |Δ loglik| i zgodność wyborów."""
    wyniki = {}
    for dev in ("cpu", "mps"):
        model = zbuduj_model(a.model, dev)
        pary = []
        for nazwa in ("arc_c_cloze", "arc_c_mc"):
            budowa = ZADANIA[nazwa][1]
            for d in dokumenty(nazwa, a.n):
                ctx, konty = budowa(d)
                pary += [para(model, ctx, c) for c in konty]
        wyniki[dev] = [v for v, _ in licz_logliki(model, pary, a.batch)]
        del model
    roz = [abs(x - y) for x, y in zip(wyniki["cpu"], wyniki["mps"])]
    print(json.dumps({"n_par": len(roz), "max_abs_diff": max(roz), "sred_abs_diff": sum(roz) / len(roz)}))


def cmd_wikitext(a):
    """WikiText-2 test jak lm-eval wikitext (detokenizer, okna rolling, BOS jako prefiks): byte_ppl do porównania z Space."""
    from lm_eval.utils import get_rolling_token_windows, make_disjoint_window
    sys.path.insert(0, str(KATALOG))
    from zadania import _modul_lm_eval
    wt = _modul_lm_eval("wikitext/preprocess_wikitext.py")
    model = zbuduj_model(a.model, a.device)
    docs = _ds("EleutherAI/wikitext_document_level", "wikitext-2-raw-v1", WIKI_REW, "test")
    nll = bajty = slowa = 0.0
    for d in docs:
        tekst = wt.wikitext_detokenizer(d)
        ids = model.encode(tekst)
        okna = [make_disjoint_window(o) for o in get_rolling_token_windows(
            token_list=ids, prefix_token=model.prefiks_pusty[0], max_seq_len=model.max_len, context_len=1)]
        pary = [(list(c), list(t)) for c, t in okna]
        nll -= sum(v for v, _ in licz_logliki(model, pary, 1))
        bajty += len(tekst.encode()); slowa += len(tekst.split())
    out = {"n_docs": len(docs), "byte_perplexity": math.exp(nll / bajty), "bits_per_byte": nll / bajty / LN2,
           "word_perplexity": math.exp(nll / slowa)}
    Path(a.wyjscie).mkdir(parents=True, exist_ok=True)
    (Path(a.wyjscie) / "wikitext.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    l = sub.add_parser("licz")
    l.add_argument("--model", required=True); l.add_argument("--zadania", required=True)
    l.add_argument("--wyjscie", required=True); l.add_argument("--device", default="cpu")
    l.add_argument("--limit", type=int); l.add_argument("--batch", type=int, default=16)
    l.add_argument("--etykieta")
    z = sub.add_parser("zgodnosc")
    z.add_argument("--model", required=True); z.add_argument("--n", type=int, default=20)
    z.add_argument("--batch", type=int, default=8)
    w = sub.add_parser("wikitext")
    w.add_argument("--model", required=True); w.add_argument("--wyjscie", required=True)
    w.add_argument("--device", default="cpu")
    an = sub.add_parser("analiza")
    an.add_argument("--wyniki", required=True)
    a = p.parse_args()
    if a.cmd == "analiza":
        from analiza_formatu import analiza
        analiza(Path(a.wyniki))
    else:
        {"licz": cmd_licz, "zgodnosc": cmd_zgodnosc, "wikitext": cmd_wikitext}[a.cmd](a)


if __name__ == "__main__":
    main()
