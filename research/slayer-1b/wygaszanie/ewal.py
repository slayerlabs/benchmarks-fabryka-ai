"""Ewaluacja jednego modelu scorerem wspolne/hipoteza_formatu.py, plus PubMedQA.

python wygaszanie/ewal.py --model <katalog> --wyjscie wyniki/<etykieta> [--device cuda] [--limit N]

Zadania: arc_c_cloze (+PMI), arc_c_mc (litery), med_mc, med_cloze (+PMI), siqa_cloze (+PMI), siqa_mc,
pubmedqa (yes/no/maybe, prompt lm-eval, +PMI), multiblimp (pol, para minimalna), potem WikiText-2.
Pliki <zadanie>.jsonl jak w hipoteza_formatu (wiersz na pytanie), wikitext.json.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "wspolne"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hipoteza_formatu as H  # noqa: E402
from dane import pubmedqa_docs  # noqa: E402

ZADANIA = "arc_c_cloze,arc_c_mc,med_mc,med_cloze,siqa_cloze,siqa_mc,pubmedqa,multiblimp"
ODP = ["yes", "no", "maybe"]


def pubmed_dane():
    return [{"id": f"pmqa{d.get('PUBMED_ID', i)}", "konteksty": d["CONTEXTS"], "pytanie": d["QUESTION"],
             "opcje": ODP, "gold": ODP.index(d["final_decision"])} for i, d in enumerate(pubmedqa_docs())]


def prompt_pubmed(doc):
    # lm-eval pubmedqa/preprocess_pubmedqa.py doc_to_text, kontynuacja " yes"/" no"/" maybe"
    return "Abstract: {}\nQuestion: {}\nAnswer:".format("\n".join(doc["konteksty"]), doc["pytanie"]), \
        [" " + o for o in ODP]


H.ZADANIA["pubmedqa"] = (pubmed_dane, prompt_pubmed, None, True)
H.BUDOWY_TRESC = H.BUDOWY_TRESC + (prompt_pubmed,)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--device", default="cuda")
    p.add_argument("--zadania", default=ZADANIA)
    p.add_argument("--limit", type=int)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--bez_wikitext", action="store_true")
    a = p.parse_args()
    t0 = time.time()
    H.cmd_licz(argparse.Namespace(model=a.model, zadania=a.zadania, wyjscie=a.wyjscie, device=a.device,
                                  limit=a.limit, batch=a.batch, etykieta=None))
    if not a.bez_wikitext:
        H.cmd_wikitext(argparse.Namespace(model=a.model, wyjscie=a.wyjscie, device=a.device))
    print(f"EWAL KONIEC {a.wyjscie} {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
