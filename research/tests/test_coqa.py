"""CoQA T41 (common/zadania.py, benchmarks/coqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, RECIPE.md and the README type row; the lm-eval `coqa` helpers as the card writes
them, re-implemented here on invented conversations: the prompt (story, answered turns as history, the last question
ending in `A:`), the gold list of the last turn (main answer plus additional ones, duplicates by lower case dropped),
the prediction (`strip().split("\n")[0]`) and the SQuAD-style token F1 averaged leave-one-out over the gold list.
The constant-answer baseline b goes through `ewaluuj.bazy_proby` with a stand-in task: the card's rule takes the most
frequent gold answer after the metric's normalisation (`Yes` and `yes` are one answer), the repo code counts raw
strings (#245), so that test is a strict xfail until #245 is fixed. With lm-eval installed (.venv-eval) the
installed `coqa` helpers are run on the same conversations. Run: python tests/test_coqa.py (or pytest).
"""
import sys
from itertools import zip_longest
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wpis_benchmarku as W  # noqa: E402
import ewaluuj as E  # noqa: E402  (common/ is on the path after wpis_benchmarku)
import metryki as M  # noqa: E402

Z = W.Z


def rozmowa(story, tury, dodatkowe=()):
    """A CoQA document: `tury` = [(question, answer)], `dodatkowe` = answer lists of the 3 additional annotators."""
    return {"story": story, "questions": {"input_text": [q for q, _ in tury]},
            "answers": {"input_text": [a for _, a in tury]},
            "additional_answers": {str(i): {"input_text": odp} for i, odp in enumerate(dodatkowe)}}


KOT = rozmowa("Cotton was a white cat. She lived in a barn.",
              [("What color was Cotton?", "white"), ("Where did she live?", "in a barn"),
               ("Did she want to change her fur?", "No")],
              [["white", "in a barn", "no"], ["White", "a barn", "NO"], ["white", "barn", "no"]])


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA, the card, RECIPE.md and the README row."""
    oczekiwane = {"repo": "EleutherAI/coqa", "rewizja": "82e11af842af6c1396f5e9a5c7de260107c50cf1", "nazwa_hf": None,
                  "split": "validation", "metric": "f1,none", "lm_eval": "coqa", "unit": "score", "rodzaj": "proba",
                  "klucz": "f1", "baza": "gen", "filtr": None, "klastry": None}
    meta, karta = W.sprawdz_wpis("T41", oczekiwane, shoty=0, typ="ciagla")
    assert ("| Metryka decyzyjna | `f1` (lm-eval `f1,none`), 0-shot, średnia po 500 dokumentach pełnego splitu "
            "`validation`.") in karta
    assert "n: **500** dokumentów, po jednym na tekst" in karta
    assert ('`doc_to_text` = `story + "\\n\\n"`, potem dla każdej tury `Q: {pytanie}\\n\\n` i '
            '`A: {złota odpowiedź}\\n\\n`, a dla ostatniej tury `Q: {pytanie}\\n\\nA:`') in karta
    assert "lista złotych odpowiedzi ostatniej tury (odpowiedź główna plus 3 dodatkowe, bez powtórzeń po małych " \
           "literach)" in karta
    assert "`process_results`: predykcja = `generacja.strip().split(\"\\n\")[0]`" in karta
    assert ("Przy liście > 1 wynik to średnia po i z maksimum F1 wobec listy bez i-tej odpowiedzi (leave-one-out), "
            "przy jednej odpowiedzi F1 wobec niej.") in karta
    assert "b = max(0; 0,1413333) = 0,1413333 = stała odpowiedź `yes`" in karta
    assert W.ZK.KATALOGI["T41"] == "coqa"


def doc_to_text(doc):
    tekst = doc["story"] + "\n\n"
    for q, a in zip_longest(doc["questions"]["input_text"], doc["answers"]["input_text"][:-1]):
        tekst += f"Q: {q}\n\n" + (f"A: {a}\n\n" if a is not None else "A:")
    return tekst


def doc_to_target(doc):
    ostatnia = len(doc["questions"]["input_text"]) - 1
    zlote = [doc["answers"]["input_text"][ostatnia]]
    for odp in doc.get("additional_answers", {}).values():
        if odp["input_text"][ostatnia].lower() not in map(str.lower, zlote):
            zlote.append(odp["input_text"][ostatnia])
    return zlote


def f1(zlote, pred):
    """Leave-one-out mean of the best token F1 (metryki.squad_f1 against one gold = squad_metrics.compute_f1)."""
    if len(zlote) == 1:
        return M.squad_f1(pred, zlote)
    return sum(max(M.squad_f1(pred, [z]) for z in zlote[:i] + zlote[i + 1:]) for i in range(len(zlote))) / len(zlote)


def process_results(doc, results):
    return {"f1": f1(doc_to_target(doc), results[0].strip().split("\n")[0])}


def test_prompt_and_gold_list_of_the_last_turn():
    assert doc_to_text(KOT) == ("Cotton was a white cat. She lived in a barn.\n\nQ: What color was Cotton?\n\n"
                                "A: white\n\nQ: Where did she live?\n\nA: in a barn\n\n"
                                "Q: Did she want to change her fur?\n\nA:")
    assert doc_to_target(KOT) == ["No"]  # "no", "NO", "no" are duplicates by lower case
    druga = rozmowa("S", [("Q1", "Yes")], [["yes"], ["Yes indeed"], ["YES"]])
    assert doc_to_target(druga) == ["Yes", "Yes indeed"]


@pytest.mark.parametrize("zlote, generacja, wynik", [
    (["No"], " No.\nQ: Why not?", 1.0),  # first line after strip, punctuation and case normalised
    (["No"], "", 0.0),  # card: the empty answer gives 0
    # card doc 120: i=0 -> vs "n its mouth": common its, mouth (2 of 3 each) -> 2/3; i=1 -> vs "in its mouth" 1
    (["in its mouth", "n its mouth"], " in its mouth", (2 / 3 + 1) / 2),
    # i=0 -> best of "red" / "ball" vs "red ball": P 1/2, R 1 -> 2/3; i=1, i=2 -> "the red ball" 1 -> 8/9
    (["the red ball", "red", "a ball"], " red ball\n", (2 / 3 + 1 + 1) / 3),
])
def test_leave_one_out_f1(zlote, generacja, wynik):
    doc = rozmowa("S", [("Q", zlote[0])], [[z] for z in zlote[1:]])
    assert doc_to_target(doc) == zlote
    assert process_results(doc, [generacja])["f1"] == pytest.approx(wynik)


class AtrapaCoQA:
    """Stand-in task object: the helpers above plus lm-eval's default filter "none" (take_first)."""
    doc_to_target = staticmethod(doc_to_target)
    process_results = staticmethod(process_results)
    _filters = [SimpleNamespace(name="none", filters=[
        lambda: SimpleNamespace(apply=lambda resps, docs: [r[0] for r in resps])])]


@pytest.mark.xfail(strict=True, reason="#245: ewaluuj.bazy_proby picks the most frequent RAW gold string ('no'), "
                                       "the card's rule the most frequent one after the metric's normalisation")
def test_constant_answer_baseline_after_normalisation():
    # last-turn golds: no, no, yes, Yes, YES -> raw counts no 2, yes 1, Yes 1, YES 1; normalised yes 3, no 2.
    # The constant "yes" scores 1 on the three yes-documents and 0 on the two no-documents: b = 3/5 (empty answer 0).
    # The raw count picks "no" and gives 2/5.
    docs = [rozmowa("S", [("Q", a)]) for a in ("no", "no", "yes", "Yes", "YES")]
    bazy, szczegoly = E.bazy_proby(AtrapaCoQA, Z.ZADANIA["T41"], docs)
    assert szczegoly["pusta"] == 0.0
    assert szczegoly["najczestsza_zlota"]["value"] == pytest.approx(3 / 5)
    assert bazy["majority_value"] == pytest.approx(3 / 5)


@pytest.mark.skipif(not W.MA_LM_EVAL, reason="needs lm-eval (.venv-eval): runs the installed coqa helpers")
def test_installed_helpers_agree_with_the_card():
    cfg = Z._yaml("coqa")
    assert cfg["output_type"] == "generate_until" and cfg["generation_kwargs"]["until"] == ["\nQ:"]
    assert [m["metric"] for m in cfg["metric_list"]] == ["em", "f1"]
    przypadki = [(KOT, " No.\nQ: Why not?"), (KOT, ""),
                 (rozmowa("S", [("Q", "in its mouth")], [["n its mouth"]]), " in its mouth"),
                 (rozmowa("S", [("Q", "the red ball")], [["red"], ["a ball"]]), " red ball\n")]
    for doc, generacja in przypadki:
        assert cfg["doc_to_text"](doc) == doc_to_text(doc)
        assert cfg["doc_to_target"](doc) == doc_to_target(doc)
        assert cfg["process_results"](doc, [generacja])["f1"] == pytest.approx(process_results(doc, [generacja])["f1"])


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
