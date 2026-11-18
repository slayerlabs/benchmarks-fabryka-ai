"""COPA T11 (common/zadania.py, benchmarks/copa/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the lm-eval `copa` prompt (premise without its final full stop + " because" or
" therefore") with continuations of two spaces + the option with a lower-case first letter, and the decision metric
`acc` (not `acc_norm`, which divides by the option length counting its leading space) on a stand-in model.
Data: two invented questions, one `cause`, one `effect`. Run: python tests/test_copa.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"idx": 0, "premise": "The man lost his keys.", "question": "cause",
         "choice1": "He dropped them in the park.", "choice2": "He bought a new car.", "label": 0},
        {"idx": 1, "premise": "It started to rain.", "question": "effect",
         "choice1": "The sun came out.", "choice2": "The streets got wet.", "label": 1}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T11"], ZK.karta("T11").read_text(encoding="utf-8")
    oczekiwane = {"repo": "aps/super_glue", "rewizja": "3de24cf8022e94f4ee4b9d55a6f539891524d646",
                  "nazwa_hf": "copa", "split": "validation", "metric": "acc,none", "task": "copa"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "konfiguracja `copa`" in karta and "| Metryka decyzyjna | `acc`" in karta
    assert "split: `validation`" in karta and "0-shot" in karta
    assert '`" because"`' in karta and '`" therefore"`' in karta and "dwóch spacji" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T11"] == "copa"


# len with the leading space: " he dropped them in the park." 29, " he bought a new car." 21.
# q1 gold dropped: acc bought (-10 > -12), acc_norm dropped (-12/29 = -0.414 > -10/21 = -0.476);
# q2 gold wet: wet wins both (-2 > -3) -> acc 1/2, acc_norm 1
LL = {"  he dropped them in the park.": -12.0, "  he bought a new car.": -10.0,
      "  the sun came out.": -3.0, "  the streets got wet.": -2.0}


def test_prompt_choices_and_decision_metric_acc(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T11", {"copa": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                                 tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == "The man lost his keys because"] == [
        "  he dropped them in the park.", "  he bought a new car."]
    assert [k for c, k in zadania if c == "It started to rain therefore"] == [
        "  the sun came out.", "  the streets got wet."]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
