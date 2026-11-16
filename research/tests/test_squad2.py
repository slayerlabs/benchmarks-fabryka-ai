"""SQuAD 2.0 T38 (common/zadania.py, benchmarks/squad2/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row (`ciagla +proc`, percent, b and control on the
HasAns subset); the prompt of the legacy class as the card writes it; the official normalisation and token F1 of
`metryki.squad_normalizuj` / `squad_f1` / `squad_em` on cases tests/test_przebieg_c.py does not cover: punctuation
dropped without a space, articles only as whole words, partial overlap with the best of several golds, repeated
tokens, golds empty after normalisation skipped (a HasAns question whose only gold is empty then scores like a
no-answer one). With lm-eval installed (.venv-eval) the prompt and the demonstration target are read from the
installed legacy `squadv2/task.py`. Run: python tests/test_squad2.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import metryki as M  # noqa: E402  (common/ is on the path after wpis_benchmarku)

Z = W.Z
DOC = {"id": "q0", "title": "Normans", "context": "The Normans gave their name to Normandy, a region in France.",
       "question": "In what country is Normandy located?", "answers": {"text": ["France"], "answer_start": [55]}}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "rajpurkar/squad_v2", "rewizja": "3ffb306f725f7d2ce8394bc1873b24868140c412",
                  "nazwa_hf": "squad_v2", "split": "validation", "metric": "f1,none", "task": "squadv2",
                  "lm_eval": None, "unit": "percent", "rodzaj": "proba", "klucz": "f1", "baza": "gen",
                  "podzbior": "HasAns", "klastry": None}
    meta, karta = W.sprawdz_wpis("T38", oczekiwane, shoty=0, typ="ciagla +proc")
    assert ("| Metryka decyzyjna | `f1` (średni F1 tokenów po wszystkich 11873 pytaniach `validation`, 0-shot, "
            "w procentach), zgodnie z wpisem `T38` (`metric=\"f1,none\"`, `klucz=\"f1\"`).") in karta
    assert "n: 11873 wierszy, w tym HasAns 5928 i NoAns 5945" in karta
    assert "wiersz T38: `ciagla +proc`, b i kontrola na podzbiorze HasAns" in karta
    assert ('`doc_to_text`: `"Title: " + title + "\\n\\nBackground: " + context + "\\n\\nQuestion: " + question'
            ' + "\\n\\nAnswer:"`; prompt kończy się na `Answer:` bez spacji') in karta
    assert ("`normalize_answer` (małe litery, usunięcie znaków `string.punctuation` bez wstawiania spacji, usunięcie "
            "przedimków `a`, `an`, `the` przez zamianę na spację, ujednolicenie spacji); złote odpowiedzi, które po "
            "normalizacji są puste, są pomijane, a pytanie bez złotych dostaje listę `[\"\"]`") in karta
    assert "Wynik w procentach (`unit=\"percent\"`)." in karta
    assert W.ZK.KATALOGI["T38"] == "squad2"


def prompt(doc):
    return ("Title: " + doc["title"] + "\n\nBackground: " + doc["context"] + "\n\nQuestion: " + doc["question"]
            + "\n\nAnswer:")


def test_prompt_of_the_legacy_class():
    assert prompt(DOC) == ("Title: Normans\n\nBackground: The Normans gave their name to Normandy, a region in "
                           "France.\n\nQuestion: In what country is Normandy located?\n\nAnswer:")


@pytest.mark.parametrize("tekst, znormalizowany", [
    ("U.S.-based", "usbased"),  # punctuation dropped, no space put in
    ("The theory of the anarchy", "theory of anarchy"),  # articles as whole words -> space, spaces squeezed
    ("Thea's  Anarchy ", "theas anarchy"),  # "Thea" is not an article; apostrophe dropped first
    ("an A-team", "ateam"),  # "an" goes; "A-team" -> "ateam" is one word, no article left in it
])
def test_official_normalisation(tekst, znormalizowany):
    assert M.squad_normalizuj(tekst) == znormalizowany


@pytest.mark.parametrize("pred, zlote, f1, em", [
    # pred tokens norman conquest of england (4), gold conquest of england (3): common 3, P 3/4, R 1 -> F1 6/7;
    # the other gold "France" gives 0, max over golds 6/7
    ("Norman conquest of England", ["France", "conquest of England"], 6 / 7, 0.0),
    ("the the cat cat", ["cat"], 2 / 3, 0.0),  # "cat cat" vs "cat": common 1 (multiset), P 1/2, R 1 -> 2/3
    ("France", ["!", "France"], 1.0, 1.0),  # gold "!" is empty after normalisation, skipped
    ("", ["the"], 1.0, 1.0),  # only gold empty after normalisation -> [""]: abstaining scores 1
    ("France", ["the"], 0.0, 0.0),  # ... and any answer 0, like a no-answer question
    ("", ["France"], 0.0, 0.0),  # abstaining on an answerable question
])
def test_token_f1_and_exact_against_the_best_gold(pred, zlote, f1, em):
    assert M.squad_f1(pred, zlote) == pytest.approx(f1) and M.squad_em(pred, zlote) == em


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): reads the installed squadv2/task.py")
def test_installed_legacy_class_has_the_card_prompt_and_target():
    klasa = Z._modul_lm_eval("squadv2/task.py").SQuAD2
    assert klasa.doc_to_text(None, DOC) == prompt(DOC)
    assert klasa.doc_to_target(None, DOC) == " France"
    assert klasa.doc_to_target(None, {**DOC, "answers": {"text": [], "answer_start": []}}) == " unanswerable"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
