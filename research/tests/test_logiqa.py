"""LogiQA T18 (common/zadania.py, benchmarks/logiqa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt of lm-eval `utils_logiqa.doc_to_text` with the option TEXT (not the
letter) as continuation, the target from the lower-case `label` letter (parquet format), and the decision metric
`acc_norm` (not `acc`) on a stand-in model with fixed log-likelihoods. Data: two invented questions.
Run: python tests/test_logiqa.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"label": "b", "context": "Every cat is an animal. Tom is a cat.",
         "question": "Which of the following can be derived?",
         "options": ["Yes", "Tom is an animal", "No", "Maybe so"]},
        {"label": "d", "context": "Ann is taller than Bob. Bob is taller than Cid.",
         "question": "Which of the following must be true?",
         "options": ["Red", "Blue", "Green", "Ann is taller than Cid"]}]
PROMPTY = ["Passage: Every cat is an animal. Tom is a cat.\nQuestion: Which of the following can be derived?\n"
           "Choices:\nA. Yes\nB. Tom is an animal\nC. No\nD. Maybe so\nAnswer:",
           "Passage: Ann is taller than Bob. Bob is taller than Cid.\nQuestion: Which of the following must be true?\n"
           "Choices:\nA. Red\nB. Blue\nC. Green\nD. Ann is taller than Cid\nAnswer:"]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T18"], ZK.karta("T18").read_text(encoding="utf-8")
    oczekiwane = {"repo": "EleutherAI/logiqa", "rewizja": "c1eee1b2fd0ddc87777e36490f7ad54d0b97d141",
                  "nazwa_hf": "logiqa", "split": "test", "metric": "acc_norm,none", "task": "logiqa"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "nazwa_hf"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc_norm`" in karta and "split: test, n: 651" in karta
    assert "`Passage: <context>\\nQuestion: <question>\\nChoices:\\nA. <opcja 1>" in karta and "0-shot" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T18"] == "logiqa"


# q1 gold b (index 1), q2 gold d (index 3); lengths are of the option text without the leading space
LL = {" Yes": -3.0, " Tom is an animal": -5.0, " No": -4.0, " Maybe so": -9.0,
      " Red": -3.0, " Blue": -4.0, " Green": -5.0, " Ann is taller than Cid": -1.0}


def test_prompt_choices_target_and_decision_metric_acc_norm(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T18", {"logiqa": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                                 tmp_path, monkeypatch)
    for prompt, d in zip(PROMPTY, DANE):
        assert [k for c, k in zadania if c == prompt] == [" " + o for o in d["options"]]
    space = roz["dodatkowe"]["space"]
    # q1: acc picks Yes (-3 > -4 > -5 > -9), wrong; acc_norm picks "Tom is an animal" (-5/16 = -0.31 beats
    # Yes -3/3 = -1, No -4/2 = -2, Maybe so -9/8 = -1.13), right. q2: both pick "Ann is taller than Cid" (-1 raw,
    # -1/22 per char), right. -> acc 1/2, acc_norm 1
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc_norm,none" and roz["value"] == pytest.approx(1.0) and roz["n_scored"] == 2
    assert list(roz["dodatkowe"]) == ["space"]  # one variant, no letter format


def test_target_comes_from_label_letter(tmp_path, monkeypatch):
    """Same log-likelihoods, gold of q1 moved from b to a: acc_norm drops to 1/2 and acc rises to 1."""
    dane = [{**DANE[0], "label": "a"}, DANE[1]]
    roz, _ = C.ocen_loglik("T18", {"logiqa": dane}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                           tmp_path, monkeypatch)
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1.0) and space["acc_norm"]["value"] == pytest.approx(1 / 2)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
