"""GSM8K T33 (common/zadania.py, studies/2026-10-lm-eval-benchmarks/benchmarks/gsm8k/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row; the decision filter `strict-match` (number
right after the first `#### `) and the `exact_match` normalisation as the card writes them, applied to invented
generations: the card's examples `#### 1,000` hits gold 1000, `#### 1000.00` and `#### $1000.` miss, a bare number
without `#### ` misses. With lm-eval installed (.venv-eval) the same pattern and ignore list are read from the
installed `gsm8k` YAML. Run: python tests/test_gsm8k.py (or pytest).
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402

Z = W.Z
REGEX = r"#### (\-?[0-9\.\,]+)"  # strict-match
DO_POMINIECIA = [",", r"\$", r"(?s).*#### ", r"\.$"]  # exact_match regexes_to_ignore, ignore_case, punctuation kept
ZLOTE = "Ann has 400 + 600 = <<400+600=1000>>1000 apples.\n#### 1000"


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "openai/gsm8k", "rewizja": "740312add88f781978c0658806c59bc2815b9866", "nazwa_hf": "main",
                  "split": "test", "metric": "exact_match,strict-match", "lm_eval": "gsm8k", "rodzaj": "proba",
                  "klucz": "exact_match", "filtr": "strict-match", "baza": "gen"}
    meta, karta = W.sprawdz_wpis("T33", oczekiwane, shoty=5, typ="gen")
    assert "| Metryka decyzyjna | `exact_match` z filtrem `strict-match`, 5-shot" in karta
    assert "n: 1319 (parquet `main/test` @ `740312ad`)" in karta and "pełny split" in karta
    assert "`doc_to_text: \"Question: {{question}}\\nAnswer:\"`" in karta
    assert 'regex_pattern: "#### (\\\\-?[0-9\\\\.\\\\,]+)"' in karta
    assert '`","`, `"\\\\$"`, `"(?s).*#### "`, `"\\\\.$"`' in karta
    assert W.ZK.KATALOGI["T33"] == "gsm8k"


def strict_match(generacja):
    m = re.search(REGEX, generacja)
    return m.group(1) if m else "[invalid]"


def normalizuj(tekst):
    for r in DO_POMINIECIA:
        tekst = re.sub(r, "", tekst)
    return tekst.lower()


def exact_match(generacja, zlote=ZLOTE):
    return float(normalizuj(strict_match(generacja)) == normalizuj(zlote))


@pytest.mark.parametrize("generacja, wynik", [
    (" 400 + 600 = 1000.\n#### 1,000", 1.0),  # separator dropped on both sides
    (" #### 1000\n\nQuestion: next", 1.0),  # the first `#### ` counts, the rest of the text does not
    (" so 1000.\n#### 1000.00", 0.0),  # trailing .00 stays
    (" #### $1000.", 0.0),  # `$` right after `#### ` is not matched -> [invalid]
    (" The answer is 1000.", 0.0),  # no `#### `: strict-match gives [invalid]
    (" #### -1000", 0.0),
])
def test_strict_match_and_exact_match(generacja, wynik):
    assert exact_match(generacja) == wynik


def test_strict_match_takes_the_first_marker():
    assert strict_match(" #### 12\n#### 13") == "12" and strict_match("#### $5") == "[invalid]"


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed gsm8k YAML")
def test_installed_yaml_has_the_card_filter_and_metric():
    cfg = Z._yaml("gsm8k")
    strict = next(f for f in cfg["filter_list"] if f["name"] == "strict-match")["filter"]
    assert strict == [{"function": "regex", "regex_pattern": REGEX}, {"function": "take_first"}]
    em, = cfg["metric_list"]
    assert em["metric"] == "exact_match" and em["regexes_to_ignore"] == DO_POMINIECIA
    assert em["ignore_case"] is True and em["ignore_punctuation"] is False
    assert cfg["doc_to_text"] == "Question: {{question}}\nAnswer:" and cfg["fewshot_split"] == "train"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
