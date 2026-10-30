"""Kąt tokenizacja: mianownik byte_ppl WikiText-2 (nasz cmd_wikitext vs lm-eval process_results).

Bez modelu: NLL jest stała, zmienia się tylko liczba bajtów/słów w mianowniku.
Nasz hipoteza_formatu.cmd_wikitext: bajty = len(detokenizer(doc).encode()), słowa = len(detok.split()).
lm-eval 6d2abda (Space): bajty = len(doc["page"].encode("utf-8")), słowa = len(re.split(r"\\s+", doc["page"])).

python mianownik.py <preprocess_wikitext.py> <katalog_wyjscia>
"""
import importlib.util
import json
import math
import re
import sys
from pathlib import Path

from datasets import load_dataset

WIKI_REW = "647234772b9554e208af6c826f23b99e3cac88c8"
NASZ_BPPL = 1.892541306655693   # wyniki/LICZBY.json porownanie/wikitext/1.06/przed_korekta/byte_perplexity
NASZ_WPPL = 48.035187913332166  # porownanie/wikitext/1.06/przed_korekta/word_perplexity
SPACE_BPPL = 1.846

spec = importlib.util.spec_from_file_location("pw", sys.argv[1])
pw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pw)
docs = load_dataset("EleutherAI/wikitext_document_level", "wikitext-2-raw-v1", revision=WIKI_REW)["test"]

b_det = b_org = w_det = w_org = 0
for d in docs:
    det = pw.wikitext_detokenizer(d)
    b_det += len(det.encode("utf-8")); b_org += len(d["page"].encode("utf-8"))
    w_det += len(det.split()); w_org += len(re.split(r"\s+", d["page"]))

nll = math.log(NASZ_BPPL) * b_det          # nats, odtworzone z naszego wyniku
bppl_lmeval = math.exp(nll / b_org)
wppl_lmeval = math.exp(math.log(NASZ_WPPL) * w_det / w_org)
out = {
    "n_docs": len(docs), "bajty_detok": b_det, "bajty_oryginal": b_org, "stosunek_bajtow": b_org / b_det,
    "slowa_detok": w_det, "slowa_oryginal_resplit": w_org,
    "nll_nats_odtworzone": nll,
    "nasz_byte_ppl_mianownik_detok": NASZ_BPPL,
    "byte_ppl_mianownik_lmeval": bppl_lmeval, "bits_per_byte_lmeval": nll / b_org / math.log(2),
    "word_ppl_mianownik_lmeval": wppl_lmeval,
    "space_byte_ppl": SPACE_BPPL,
    "roznica_przed_proc": 100 * (NASZ_BPPL / SPACE_BPPL - 1),
    "roznica_po_proc": 100 * (bppl_lmeval / SPACE_BPPL - 1),
}
Path(sys.argv[2]).mkdir(parents=True, exist_ok=True)
(Path(sys.argv[2]) / "mianownik.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
