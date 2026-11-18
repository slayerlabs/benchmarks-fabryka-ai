"""OpenBookQA T08 (common/zadania.py, benchmarks/openbookqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the lm-eval `openbookqa` prompt (context = the bare `question_stem`, no
"Question:"/"Answer:", continuation = space + option text, gold = index of `answerKey.lstrip()` in `choices.label`),
and the decision metric `acc_norm` (not `acc`) on a stand-in model. Data: two invented questions, the second with
a leading space in `answerKey`. Run: python tests/test_openbookqa.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
LITERY = ["A", "B", "C", "D"]
DANE = [{"id": "syn-obqa-1", "question_stem": "Plants grow best with plenty of",
         "choices": {"text": ["moon", "sunshine", "noise", "plastic"], "label": LITERY}, "answerKey": "B"},
        {"id": "syn-obqa-2", "question_stem": "A magnet will pick up",
         "choices": {"text": ["iron", "wood", "glass", "paper"], "label": LITERY}, "answerKey": " A"}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T08"], ZK.karta("T08").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allenai/openbookqa", "rewizja": "388097ea7776314e93a529163e0fea805b8a6454",
                  "nazwa_hf": "main", "split": "test", "metric": "acc_norm,none", "task": "openbookqa"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "konfiguracji `main`" in karta and "| Metryka decyzyjna | `acc_norm`" in karta
    assert "split: `test`" in karta and "0-shot" in karta
    assert "kontekst to sam `question_stem`" in karta and "`choices.label.index(answerKey.lstrip())`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T08"] == "openbookqa"


# q1 gold sunshine: acc moon (-4 > -6), acc_norm sunshine (-6/8 = -0.75 > -4/4 = -1);
# q2 gold iron (" A" -> index 0): iron wins both (-1 > -2, -1/4 > -2/4) -> acc 1/2, acc_norm 1
LL = {" moon": -4.0, " sunshine": -6.0, " noise": -99.0, " plastic": -99.0,
      " iron": -1.0, " wood": -2.0, " glass": -99.0, " paper": -99.0}


def test_prompt_choices_and_decision_metric_acc_norm(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T08", {"openbookqa": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                                 tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == "Plants grow best with plenty of"] == [
        " moon", " sunshine", " noise", " plastic"]
    assert [k for c, k in zadania if c == "A magnet will pick up"] == [" iron", " wood", " glass", " paper"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc_norm,none" and roz["value"] == pytest.approx(1.0) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
