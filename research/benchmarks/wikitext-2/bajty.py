"""Kąt „dane": bajty i słowa WikiText-2 test na oryginale (page) i po detokenizacji lm-eval.

Bez modelu. Przelicza nasz byte_ppl (NLL / bajty detok) na konwencję lm-eval (NLL / bajty page),
oraz word_ppl (słowa page wg re.split(r"\\s+") zamiast str.split() na detok).
Uruchom: <python z datasets> bajty.py  -> results/bajty.json.
"""
import json
import math
import re
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
REW = "647234772b9554e208af6c826f23b99e3cac88c8"
NASZ_BPPL = 1.8925413080292057  # LICZBY.json raport_formatu/slayer_wikitext_kontrola/przed_korekta/byte_perplexity
NASZ_WPPL = 48.03518812492844
SPACE_BPPL = 1.846283835597753  # results.json, SlayerLab/Slayer1B-1.06, T03 value


class pw:  # przepisane 1:1 z lm_eval/tasks/wikitext/preprocess_wikitext.py @ 6d2abda4 (kopia w lm_eval_src/)
    @staticmethod
    def wikitext_detokenizer(doc):
        string = doc["page"]
        string = string.replace("s '", "s'")
        string = re.sub(r"/' [0-9]/", r"/'[0-9]/", string)
        string = string.replace(" @-@ ", "-")
        string = string.replace(" @,@ ", ",")
        string = string.replace(" @.@ ", ".")
        string = string.replace(" : ", ": ")
        string = string.replace(" ; ", "; ")
        string = string.replace(" . ", ". ")
        string = string.replace(" ! ", "! ")
        string = string.replace(" ? ", "? ")
        string = string.replace(" , ", ", ")
        string = re.sub(r"\(\s*([^\)]*?)\s*\)", r"(\1)", string)
        string = re.sub(r"\[\s*([^\]]*?)\s*\]", r"[\1]", string)
        string = re.sub(r"{\s*([^}]*?)\s*}", r"{\1}", string)
        string = re.sub(r"\"\s*([^\"]*?)\s*\"", r'"\1"', string)
        string = re.sub(r"'\s*([^']*?)\s*'", r"'\1'", string)
        string = string.replace("= = = =", "====")
        string = string.replace("= = =", "===")
        string = string.replace("= =", "==")
        string = string.replace(" " + chr(176) + " ", chr(176))
        string = string.replace(" \n", "\n")
        string = string.replace("\n ", "\n")
        string = string.replace(" N ", " 1 ")
        string = string.replace(" 's", "'s")
        return string


from datasets import load_dataset  # noqa: E402

wyn = {"rewizja": REW}
for nazwa in ("wikitext-2-raw-v1", "wikitext-2-v1"):
    try:
        ds = load_dataset("EleutherAI/wikitext_document_level", nazwa, revision=REW)
    except Exception as e:  # noqa: BLE001
        wyn[nazwa] = {"blad": repr(e)[:300]}
        continue
    r = {"splity": {k: len(v) for k, v in ds.items()}}
    docs = ds["test"]
    b_page = b_det = w_page = w_det = 0
    per_doc = []
    for d in docs:
        det = pw.wikitext_detokenizer(d)
        bp, bd = len(d["page"].encode()), len(det.encode())
        b_page += bp; b_det += bd
        w_page += len(re.split(r"\s+", d["page"])); w_det += len(det.split())
        per_doc.append([bp, bd])
    r.update(n_docs=len(docs), bajty_page=b_page, bajty_detok=b_det, stosunek_page_do_detok=b_page / b_det,
             slowa_page_resplit=w_page, slowa_detok_split=w_det)
    if nazwa == "wikitext-2-raw-v1":
        nll = math.log(NASZ_BPPL) * b_det  # suma NLL odtworzona z naszego wyniku
        r["nll_suma_odtworzona"] = nll
        r["nasz_bppl_w_konwencji_lm_eval"] = math.exp(nll / b_page)
        r["nasz_wppl_w_konwencji_lm_eval"] = math.exp(math.log(NASZ_WPPL) * w_det / w_page)
        r["space_bppl"] = SPACE_BPPL
        r["roznica_po_przeliczeniu_proc"] = 100 * (r["nasz_bppl_w_konwencji_lm_eval"] / SPACE_BPPL - 1)
        r["roznica_przed_proc"] = 100 * (NASZ_BPPL / SPACE_BPPL - 1)
        r["per_doc_bajty_page_detok"] = per_doc
    wyn[nazwa] = r

(TU / "results" / "bajty.json").write_text(json.dumps(wyn, indent=1))
print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk != "per_doc_bajty_page_detok"} if isinstance(v, dict) else v)
                  for k, v in wyn.items()}, indent=1))
