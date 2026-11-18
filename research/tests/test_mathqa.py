"""MathQA T19 (common/zadania.py, benchmarks/mathqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt `Question: {{Problem}}\\nAnswer:` with five continuations cut out of the
one-string `options` field by lm-eval `mathqa/utils.doc_to_choice` (also the list-shaped field, whose options keep a
trailing quote, card "Znane rozbieżności: opcje"), the target from the `correct` letter, and the decision metric
`acc_norm` (not `acc`) on a stand-in model with fixed log-likelihoods. Data: three invented problems, not from the
dataset. Run: python tests/test_mathqa.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z


def doc(problem, options, correct):
    return {"Problem": problem, "Rationale": "syn", "options": options, "correct": correct,
            "annotated_formula": "add(n0,n1)", "linear_formula": "add(n0,n1)|", "category": "general"}


DANE = [doc("a box has 3 red and 4 blue balls . how many balls are in the box ?",
            "a ) 7 , b ) 12 , c ) 1 , d ) none of these , e ) 34", "a"),
        doc("a car drives 50 km per hour for 10 hours . how far does it go ?",
            "a ) 5 km , b ) 50 km , c ) 500 km , d ) 2 km , e ) data inadequate", "c"),
        doc("what is 25 * 2 ?", "['a ) 10', 'b ) 20', 'c ) 30', 'd ) 40', 'e ) 50']", "e")]
KONT = {"a box has 3 red and 4 blue balls . how many balls are in the box ?":
        [" 7", " 12", " 1", " none of these", " 34"],
        "a car drives 50 km per hour for 10 hours . how far does it go ?":
        [" 5 km", " 50 km", " 500 km", " 2 km", " data inadequate"],
        # list-shaped `options`: doc_to_choice keeps the quote and, on the last option, the bracket
        "what is 25 * 2 ?": [" 10'", " 20'", " 30'", " 40'", " 50']"]}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T19"], ZK.karta("T19").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allenai/math_qa", "rewizja": "c4f1cc784c04c4957b50c97858f23893b633eea6",
                  "nazwa_hf": "default", "split": "test", "metric": "acc_norm,none", "task": "mathqa"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "nazwa_hf"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc_norm`" in karta and "split: `test`, n: 2985" in karta
    assert "`Question: {{Problem}}\\nAnswer:`" in karta and "0-shot" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T19"] == "mathqa"


LL = {" 7": -3.0, " 12": -4.0, " 1": -5.0, " none of these": -7.0, " 34": -9.0,
      " 5 km": -2.0, " 50 km": -3.0, " 500 km": -2.5, " 2 km": -6.0, " data inadequate": -20.0,
      " 10'": -4.2, " 20'": -9.0, " 30'": -9.0, " 40'": -9.0, " 50']": -4.5}


def test_prompt_choices_target_and_decision_metric_acc_norm(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T19", {"mathqa": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                                 tmp_path, monkeypatch)
    for problem, kont in KONT.items():
        assert [k for c, k in zadania if c == f"Question: {problem}\nAnswer:"] == kont
    space = roz["dodatkowe"]["space"]
    # q1 gold a " 7": acc " 7" (-3 > -4), acc_norm " none of these" (-7/14 = -0.5 > -3/2 = -1.5) -> acc 1, norm 0
    # q2 gold c " 500 km": acc " 5 km" (-2 > -2.5), acc_norm " 500 km" (-2.5/7 = -0.357 > -2/5 = -0.4) -> acc 0, norm 1
    # q3 gold e " 50']": acc " 10'" (-4.2 > -4.5), acc_norm " 50']" (-4.5/5 = -0.9 > -4.2/4 = -1.05) -> acc 0, norm 1
    # -> acc 1/3, acc_norm 2/3
    assert space["acc"]["value"] == pytest.approx(1 / 3) and space["acc_norm"]["value"] == pytest.approx(2 / 3)
    assert roz["metric"] == "acc_norm,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3
    assert list(roz["dodatkowe"]) == ["space"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
