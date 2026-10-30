"""Ewaluacja jednego modelu scorerem slayer_eval/hipoteza_formatu.py: testy główne albo szuflada (BETR).

python testy_danych_slayer/ewal_ramion.py --model <katalog> --wyjscie wyniki/<etykieta> [--szuflada] [--limit N]

Główne (PROGI.md): arc_e_cloze, arc_c_cloze, mmlu_cloze_5shot, siqa_cloze, belebele_cloze, belebele_mc, multiblimp.
Szuflada (otwierana dopiero po zapisaniu werdyktu głównego): hellaswag_cloze, piqa_cloze, gmmlu_pl_cloze_5shot,
llmzszl_cloze. Pliki <zadanie>.jsonl jak w hipoteza_formatu (wiersz na pytanie, logliki opcji, bajty, znaki),
zrodla.json z rewizjami zbiorów HF.
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "slayer_eval"))
import hipoteza_formatu as H  # noqa: E402

GLOWNE = "arc_e_cloze,arc_c_cloze,mmlu_cloze_5shot,siqa_cloze,belebele_cloze,belebele_mc,multiblimp"
SZUFLADA = "hellaswag_cloze,piqa_cloze,gmmlu_pl_cloze_5shot,llmzszl_cloze"
LIT = "ABCD"
ZRODLA = {}


def _ds(repo, cfg, split, rew=None):
    from datasets import load_dataset
    from huggingface_hub import HfApi
    if repo not in ZRODLA:
        try:
            ZRODLA[repo] = rew or HfApi().dataset_info(repo).sha
        except Exception as e:  # noqa: BLE001
            ZRODLA[repo] = f"nieznana ({type(e).__name__})"
    return load_dataset(repo, cfg, revision=rew)[split]


# ---------------------------------------------------------------- czyste budowy promptów (testy: test_dane_ramion.py)

def prefiks_5shot(przyklady, naglowek, q="Question", odp="Answer"):
    return naglowek + "".join(f"{q}: {p['pytanie'].strip()}\n{odp}: {p['opcje'][p['gold']]}\n\n" for p in przyklady)


def prompt_mmlu_5shot(doc):
    # OLMES/lm-eval cloze (RC): 5 przykładów z dev tego przedmiotu, odpowiedź treścią, nie literą
    return doc["prefiks"] + f"Question: {doc['pytanie'].strip()}\nAnswer:", [" " + o for o in doc["opcje"]]


def prompt_gmmlu_pl_5shot(doc):
    return doc["prefiks"] + f"Pytanie: {doc['pytanie'].strip()}\nOdpowiedź:", [" " + o for o in doc["opcje"]]


def prompt_llmzszl(doc):
    return f"Pytanie: {doc['pytanie'].strip()}\nOdpowiedź:", [" " + o for o in doc["opcje"]]


def hellaswag_tekst(t):
    # lm-eval hellaswag/utils.py preprocess
    t = t.strip().replace(" [title]", ". ")
    t = re.sub("\\[.*?\\]", "", t)
    return t.replace("  ", " ")


def prompt_hellaswag(doc):
    return doc["pytanie"], [" " + o for o in doc["opcje"]]


def prompt_piqa(doc):
    return f"Question: {doc['pytanie']}\nAnswer:", [" " + o for o in doc["opcje"]]


def z_5shot(test, dev, naglowek_fn, q, odp):
    """Dokleja do każdego pytania prefiks z pierwszych 5 przykładów dev jego przedmiotu."""
    po = {}
    for d in dev:
        po.setdefault(d["grupa"], []).append(d)
    return [{**d, "prefiks": prefiks_5shot(po.get(d["grupa"], [])[:5], naglowek_fn(d["grupa"]), q, odp)} for d in test]


# ---------------------------------------------------------------- dane

def mmlu_5shot():
    def rek(split):
        return [{"id": f"{r['subject']}|{split}|{i}", "grupa": r["subject"], "pytanie": r["question"],
                 "opcje": list(r["choices"]), "gold": int(r["answer"])} for i, r in enumerate(_ds("cais/mmlu", "all", split))]
    return z_5shot(rek("test"), rek("dev"),
                   lambda s: f"The following are questions (with answers) about {s.replace('_', ' ')}.\n\n",
                   "Question", "Answer")


def gmmlu_pl_5shot():
    def rek(split):
        return [{"id": f"gmmlu|{r['sample_id']}", "grupa": r["subject"], "pytanie": r["question"],
                 "opcje": [r["option_a"], r["option_b"], r["option_c"], r["option_d"]],
                 "gold": LIT.index(r["answer"].strip())} for r in _ds("CohereLabs/Global-MMLU", "pl", split)]
    return z_5shot(rek("test"), rek("dev"),
                   lambda s: f"Poniżej są pytania (z odpowiedziami) z dziedziny: {s.replace('_', ' ')}.\n\n",
                   "Pytanie", "Odpowiedź")


def llmzszl():
    return [{"id": f"llmzszl{i}", "grupa": r.get("type"), "pytanie": r["question"], "opcje": list(r["answers"]),
             "gold": int(r["correct_answer_index"])} for i, r in enumerate(_ds("amu-cai/llmzszl-dataset", None, "test"))]


def hellaswag():
    d = _ds("Rowan/hellaswag", None, "validation", rew="refs/convert/parquet")
    return [{"id": f"hs{r['ind']}", "pytanie": hellaswag_tekst(r["activity_label"] + ": " + r["ctx_a"] + " " +
                                                            r["ctx_b"].capitalize()),
             "opcje": [hellaswag_tekst(e) for e in r["endings"]], "gold": int(r["label"])} for r in d]


def piqa():
    return [{"id": f"piqa{i}", "pytanie": r["goal"], "opcje": [r["sol1"], r["sol2"]], "gold": int(r["label"])}
            for i, r in enumerate(_ds("baber/piqa", None, "validation"))]


H.ZADANIA.update({
    "mmlu_cloze_5shot": (mmlu_5shot, prompt_mmlu_5shot, None, False),
    "gmmlu_pl_cloze_5shot": (gmmlu_pl_5shot, prompt_gmmlu_pl_5shot, None, False),
    "llmzszl_cloze": (llmzszl, prompt_llmzszl, None, False),
    "hellaswag_cloze": (hellaswag, prompt_hellaswag, None, False),
    "piqa_cloze": (piqa, prompt_piqa, None, False),
})
H.BUDOWY_TRESC = H.BUDOWY_TRESC + (prompt_mmlu_5shot, prompt_gmmlu_pl_5shot, prompt_llmzszl, prompt_hellaswag,
                                   prompt_piqa)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--device", default="cuda")
    p.add_argument("--szuflada", action="store_true")
    p.add_argument("--zadania", help="nadpisuje listę (tylko próby)")
    p.add_argument("--limit", type=int)
    p.add_argument("--batch", type=int, default=16)
    a = p.parse_args()
    zad = a.zadania or (SZUFLADA if a.szuflada else GLOWNE)
    t0 = time.time()
    H.cmd_licz(argparse.Namespace(model=a.model, zadania=zad, wyjscie=a.wyjscie, device=a.device,
                                  limit=a.limit, batch=a.batch, etykieta=None))
    plik = Path(a.wyjscie) / "zrodla.json"
    stare = json.loads(plik.read_text()) if plik.exists() else {}
    krok = json.loads((Path(a.model) / "config.json").read_text()).get("step")
    plik.write_text(json.dumps({**stare, **ZRODLA, "model": a.model, "config_step": krok}, indent=1))
    print(f"EWAL KONIEC {a.wyjscie} {zad} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
