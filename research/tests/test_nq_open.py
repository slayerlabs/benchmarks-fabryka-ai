"""NQ-Open T42 (common/zadania.py, benchmarks/nq-open/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row; the prompt and the decision scoring as the
card writes them: filter `remove_whitespace` (only `lstrip()`, then take_first), then `exact_match` with the article
regex (article plus the space after it, before lower-casing), `ignore_case`, `ignore_punctuation` (dropped, no space
put in) and no whitespace squeezing, a hit on any of the reference answers. The card's own examples (rows 0 and 1577)
plus invented edge cases. With lm-eval installed (.venv-eval) the same settings are read from the installed `nq_open`
YAML and the rows are rescored by lm-eval's filter and metric. Run: python tests/test_nq_open.py (or pytest).
"""
import re
import string
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402

Z = W.Z
DESCRIPTION = "Answer these questions:\n\n"
DOC_TO_TEXT = "Q: {{question}}?\nA:"
PRZEDIMKI = r"\b(?:The |the |An |A |The |a |an )"  # exact_match regexes_to_ignore
WIERSZ_0 = ["14 December 1972 UTC", "December 1972"]  # card: validation row 0
WIERSZ_1577 = ["February 19, 2017"]  # card: validation row 1577


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "google-research-datasets/nq_open", "rewizja": "5dd9790a83002ad084ddeb7c420dc716852c6f28",
                  "nazwa_hf": "nq_open", "split": "validation", "metric": "exact_match,remove_whitespace",
                  "lm_eval": "nq_open", "rodzaj": "proba", "klucz": "exact_match", "filtr": "remove_whitespace",
                  "baza": "gen", "klastry": None}
    meta, karta = W.sprawdz_wpis("T42", oczekiwane, shoty=0, typ="gen")
    assert ("| Metryka decyzyjna | `exact_match` z filtrem `remove_whitespace`, 0-shot, średnia po pytaniach "
            "pełnego splitu `validation`.") in karta
    assert "n: 3610 wierszy (parquet `nq_open/validation` @ `5dd9790a`)" in karta
    assert '`description: "Answer these questions:\\n\\n"`, `doc_to_text: "Q: {{question}}?\\nA:"`' in karta
    assert "`Answer these questions:\\n\\nQ: when was the last time anyone was on the moon?\\nA:`" in karta
    assert "`WhitespaceFilter` (`filters/extraction.py` @ `v0.4.9.1`) robi tylko `lstrip()`, potem `take_first`" in karta
    assert r'`regexes_to_ignore` `"\\b(?:The \|the \|An \|A \|The \|a \|an )"`' in karta
    assert "`ignore_case: true` (małe litery) i `ignore_punctuation: true`" in karta
    assert W.ZK.KATALOGI["T42"] == "nq-open"


def prompt(pytanie):
    return DESCRIPTION + DOC_TO_TEXT.replace("{{question}}", pytanie)


def normalizuj(tekst):
    tekst = re.sub(PRZEDIMKI, "", tekst)  # before lower-casing, so "THE " stays
    return tekst.lower().translate(str.maketrans("", "", string.punctuation))


def exact_match(generacja, zlote):
    pred = normalizuj(generacja.lstrip())  # remove_whitespace + take_first
    return float(any(pred == normalizuj(z) for z in zlote))


def test_prompt_of_the_card_row_0():
    # questions are lower-case without "?", the template adds it; no space after "A:"
    assert prompt("when was the last time anyone was on the moon") == (
        "Answer these questions:\n\nQ: when was the last time anyone was on the moon?\nA:")


@pytest.mark.parametrize("generacja, zlote, wynik", [
    (" a December 1972", WIERSZ_0, 1.0),  # card: "a " removed, matches the second answer
    (" December 1972 UTC", WIERSZ_0, 0.0),  # card
    (" 14 december 1972 utc", WIERSZ_0, 1.0),  # card: case ignored
    (" February 19", WIERSZ_1577, 0.0),  # card: generation cut at "," loses the year
    (" February 19 2017", WIERSZ_1577, 1.0),  # card: the comma is dropped from the answer, no space put in
    (" December 1972 ", WIERSZ_0, 0.0),  # trailing space: lstrip only (authors' script gives 1)
    (" December  1972", WIERSZ_0, 0.0),  # double space is not squeezed (authors' script gives 1)
    (" the Beatles", ["The Beatles"], 1.0),  # article with its space dropped on both sides
    (" THE Beatles", ["Beatles"], 0.0),  # regex runs before lower-casing: "THE " is not in it -> "the beatles"
    (" Theodore", ["Theodore"], 1.0),  # "The" without a space after it stays
    ("", ["---"], 1.0),  # card: the empty answer hits answers made of punctuation only (row 290)
])
def test_remove_whitespace_and_exact_match(generacja, zlote, wynik):
    assert exact_match(generacja, zlote) == wynik


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed nq_open YAML")
def test_installed_yaml_has_the_card_prompt_filter_and_metric():
    from lm_eval.api.metrics import exact_match_hf_evaluate
    from lm_eval.filters.extraction import WhitespaceFilter

    cfg = Z._yaml("nq_open")
    assert cfg["description"] == DESCRIPTION and cfg["doc_to_text"] == DOC_TO_TEXT
    assert cfg["generation_kwargs"]["until"] == ["\n", ".", ","]
    filtr = next(f for f in cfg["filter_list"] if f["name"] == "remove_whitespace")["filter"]
    assert filtr == [{"function": "remove_whitespace"}, {"function": "take_first"}]
    em, = cfg["metric_list"]
    assert em["metric"] == "exact_match" and em["regexes_to_ignore"] == [PRZEDIMKI]
    assert em["ignore_case"] is True and em["ignore_punctuation"] is True
    kw = {k: em[k] for k in ("regexes_to_ignore", "ignore_case", "ignore_punctuation")}
    for generacja, zlote, wynik in [(" a December 1972", WIERSZ_0, 1.0), (" December 1972 ", WIERSZ_0, 0.0),
                                    (" February 19 2017", WIERSZ_1577, 1.0), (" THE Beatles", ["Beatles"], 0.0),
                                    ("", ["---"], 1.0), (" December  1972", WIERSZ_0, 0.0)]:
        pred, = WhitespaceFilter().apply([[generacja]], [{}])[0]
        lm = max(exact_match_hf_evaluate([pred], [z], **kw)["exact_match"] for z in zlote)
        assert lm == exact_match(generacja, zlote) == wynik, generacja


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
