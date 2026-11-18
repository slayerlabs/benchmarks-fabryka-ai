"""WikiText-2 T03 (common/zadania.py, benchmarks/wikitext-2/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, and the central-run path (`common/ewaluuj.ocen_zadanie`) on a stand-in model:
the rolling request is the detokenized page, the denominators come from the ORIGINAL page (card "Ocena"), and
the perplexities are weighted over the corpus (NLL and denominators summed before dividing, card "Agregacja").
`test_wikitext_mianownik.py` checks the same denominators in `hipoteza_formatu.cmd_wikitext` (Space hypothesis
code), not in the central run. Data: two invented pages, not from the dataset. Run: python tests/test_wikitext_2.py
(or pytest).
"""
import math
import re
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
STRONY = [{"page": " = Tytuł = \n Rok 1 @-@ 2 , potem @,@ koniec . \n"},
          {"page": " = Drugi = \n Krótko ( tak ) . \n"}]
# lm-eval wikitext_detokenizer on the two pages (" @-@ " -> "-", " @,@ " -> ",", " , " -> ", ", " . " -> ". ",
# "( " -> "(", " )" -> ")", " \n" -> "\n", "\n " -> "\n")
DETOK = {" = Tytuł =\nRok 1-2, potem,koniec.\n", " = Drugi =\nKrótko (tak).\n"}
NLL = [30.0, 12.0]


class Atrapa(C.AtrapaLM):
    def __init__(self):
        super().__init__()
        self.teksty = []

    def loglikelihood_rolling(self, requests):
        wynik = []
        for r in requests:
            self.teksty.append(r.args[0])
            wynik.append(-NLL[len(self.teksty) - 1])
        return wynik


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T03"], ZK.karta("T03").read_text(encoding="utf-8")
    oczekiwane = {"repo": "EleutherAI/wikitext_document_level", "rewizja": "647234772b9554e208af6c826f23b99e3cac88c8",
                  "nazwa_hf": "wikitext-2-raw-v1", "split": "test", "metric": "byte_perplexity,none",
                  "task": "wikitext", "rodzaj": "rolling"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "nazwa_hf"):
        assert oczekiwane[k] in karta, k
    assert "Split do wyników: `test`" in karta and "`byte_perplexity`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T03"] == "wikitext-2"


def test_rolling_text_is_detokenized_and_denominators_come_from_the_original(tmp_path, monkeypatch):
    lm = Atrapa()
    _, d = C.ocen("T03", {"wikitext": STRONY}, lm, tmp_path, monkeypatch)
    assert set(lm.teksty) == DETOK
    bajty = sum(len(s["page"].encode("utf-8")) for s in STRONY)
    slowa = sum(len(re.split(r"\s+", s["page"])) for s in STRONY)
    # detokenized text is shorter than the original: a denominator taken from it would give a different value
    assert bajty > sum(len(t.encode("utf-8")) for t in DETOK)
    assert d["byte_perplexity"]["value"] == pytest.approx(math.exp(sum(NLL) / bajty))
    assert d["word_perplexity"]["value"] == pytest.approx(math.exp(sum(NLL) / slowa))
    assert d["bits_per_byte"]["value"] == pytest.approx(sum(NLL) / bajty / math.log(2))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
