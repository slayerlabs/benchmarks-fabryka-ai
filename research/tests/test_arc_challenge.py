"""ARC-Challenge T02 (common/zadania.py, benchmarks/arc-challenge/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt and continuations lm-eval builds from it, the pick of acc and acc_norm
and the decision metric on a stand-in model (`AtrapaLM`, log-likelihoods fixed here). Data: the first rows of
common/tests/data/arc_challenge.jsonl plus one question with digit labels (22 in the test split, card "Format zadania").
Run: python tests/test_arc_challenge.py (or pytest).
"""
import json
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

E, M, Z = C.E, C.M, C.Z
DANE = [json.loads(l) for l in (Z.DANE_TESTOWE / "arc_challenge.jsonl").read_text().splitlines()[:2]]
CYFRY = {"id": "syn-arc-cyfry", "question": "How many legs does an insect have?",
         "choices": {"text": ["four", "six", "eight"], "label": ["1", "2", "3"]}, "answerKey": "2"}


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T02"], ZK.karta("T02").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allenai/ai2_arc", "rewizja": "210d026faf9955653af8916fad021475a3f00453",
                  "nazwa_hf": "ARC-Challenge", "split": "test", "metric": "acc_norm,none"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja", "nazwa_hf"):
        assert oczekiwane[k] in karta, k
    assert "`acc_norm`, 0-shot" in karta and "split: `test`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}


# space (cloze): loglik per continuation; mc (letters): loglik per letter
LL = {" oxygen": -6.0, " carbon dioxide": -7.0, " nitrogen": -10.0, " helium": -10.0,  # acc: oxygen, norm: CO2
      " the rotation of Earth on its axis": -20.0, " the Moon": -1.0, " clouds": -20.0, " the orbit of Mars": -20.0,
      " four": -5.0, " six": -1.0, " eight": -5.0,
      " A": -1.0, " B": -2.0, " C": -3.0, " D": -4.0, " 1": -1.0, " 2": -2.0, " 3": -3.0}


def test_prompt_choices_picks_and_metric(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T02", {"arc_challenge": DANE + [CYFRY]},
                                 lambda ctx, kont: 0.0 if ctx == "" else LL[kont], tmp_path, monkeypatch)
    pytanie = "Question: Which gas do plants take in for photosynthesis?\nAnswer:"
    assert [k for c, k in zadania if c == pytanie] == [" oxygen", " carbon dioxide", " nitrogen", " helium"]
    litery = ("Question: Which gas do plants take in for photosynthesis?\nA. oxygen\nB. carbon dioxide\nC. nitrogen\n"
              "D. helium\nAnswer:")
    assert [k for c, k in zadania if c == litery] == [" A", " B", " C", " D"]
    assert [k for c, k in zadania if c == "Question: How many legs does an insect have?\nAnswer:"] == [
        " four", " six", " eight"]
    space = roz["dodatkowe"]["space"]
    # q1 gold B: acc picks oxygen (-6 > -7), acc_norm carbon dioxide (-7/14 > -6/6); q2 gold A: both pick
    # "the Moon"; q3 gold "2" (index 1): both pick "six" (-1/3 > -5/5 > -5/4)
    assert space["acc"]["value"] == pytest.approx(1 / 3) and space["acc_norm"]["value"] == pytest.approx(2 / 3)
    assert roz["metric"] == "acc_norm,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3
    # stałe klasy: golds 1, 0, 1 -> majority 2/3; random = mean 1/k = (1/4 + 1/4 + 1/3) / 3
    assert space["bazy"]["majority_value"] == pytest.approx(2 / 3)
    assert space["bazy"]["chance_value"] == pytest.approx((1 / 4 + 1 / 4 + 1 / 3) / 3)
    # letters: always the first letter -> hits q2 only; the variant is diagnostic, not the observation
    assert roz["dodatkowe"]["mc"]["acc"]["value"] == pytest.approx(1 / 3)
    assert roz["dodatkowe"]["mc"]["udzial_najczestszej_predykcji"] == 1.0


def test_target_is_the_label_index_also_for_digit_labels():
    assert Z.arc_target(DANE[0]) == 1 and Z.arc_target(CYFRY) == 1
    assert Z.arc_target({**CYFRY, "answerKey": "3"}) == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
