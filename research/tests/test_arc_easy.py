"""ARC-Easy T51 (common/zadania.py, benchmarks/arc-easy/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the cloze prompt and continuations of lm-eval `arc_easy`, and the decision metric
`acc` (not `acc_norm` as in ARC-Challenge) on a stand-in model with fixed log-likelihoods. Data: two invented questions,
one with digit labels (97 in the test split, card "Dane"). Run: python tests/test_arc_easy.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"id": "syn-arc-e-1", "question": "Which part of a plant takes in water?",
         "choices": {"text": ["roots", "flowers", "seeds", "fruit"], "label": ["A", "B", "C", "D"]}, "answerKey": "A"},
        {"id": "syn-arc-e-2", "question": "What do bees make?",
         "choices": {"text": ["milk", "honey", "silk"], "label": ["1", "2", "3"]}, "answerKey": "2"}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T51"], ZK.karta("T51").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allenai/ai2_arc", "rewizja": "210d026faf9955653af8916fad021475a3f00453",
                  "nazwa_hf": "ARC-Easy", "split": "test", "metric": "acc,none", "task": "arc_easy"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "nazwa_hf"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc`." in karta and "split: test" in karta
    assert "`Question: {{question}}\\nAnswer:`" in karta and "0-shot" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T51"] == "arc-easy"


LL ={" roots": -4.0, " flowers": -5.0, " seeds": -9.0, " fruit": -9.0,
      " milk": -1.0, " honey": -2.0, " silk": -9.0}


def test_prompt_choices_and_decision_metric_acc(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T51", {"arc_easy": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                                 tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == "Question: Which part of a plant takes in water?\nAnswer:"] == [
        " roots", " flowers", " seeds", " fruit"]
    assert [k for c, k in zadania if c == "Question: What do bees make?\nAnswer:"] == [" milk", " honey", " silk"]
    space = roz["dodatkowe"]["space"]
    # q1 gold roots: acc roots (-4 > -5), acc_norm flowers (-5/7 > -4/5); q2 gold honey: acc and acc_norm milk
    # (-1 > -2, -1/4 > -2/5) -> acc 1/2, acc_norm 0
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(0.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2
    assert list(roz["dodatkowe"]) == ["space"]  # one variant, no letter format


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
