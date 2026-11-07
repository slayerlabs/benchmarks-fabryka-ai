"""BoolQ T10 (common/zadania.py, benchmarks/boolq/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the prompt `{passage}\nQuestion: {question}?\nAnswer:` with continuations ` no`
and ` yes` (index 0 = no = label False), and the decision metric `acc` (not `acc_norm`) on a stand-in model with
fixed log-likelihoods. Data: two invented passages. Run: python tests/test_boolq.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"idx": 0, "passage": "Cats are small domesticated mammals.", "question": "are cats mammals", "label": 1},
        {"idx": 1, "passage": "The Nile flows through Egypt.", "question": "does the nile flow through peru",
         "label": 0}]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T10"], ZK.karta("T10").read_text(encoding="utf-8")
    oczekiwane = {"repo": "aps/super_glue", "rewizja": "3de24cf8022e94f4ee4b9d55a6f539891524d646",
                  "nazwa_hf": "boolq", "split": "validation", "metric": "acc,none", "task": "boolq"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "konfiguracja `boolq`" in karta and "| Metryka decyzyjna | `acc` |" in karta
    assert "`validation`" in karta and "0-shot" in karta
    assert "`{passage}\\nQuestion: {question}?\\nAnswer:`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T10"] == "boolq"


# doc 1 gold yes: acc no (-4 > -5), acc_norm yes (-5/3 > -4/2); doc 2 gold no: no wins both (-1 > -2, -1/2 > -2/3)
# -> acc 1/2, acc_norm 1
LL = {"Cats": {" no": -4.0, " yes": -5.0}, "The ": {" no": -1.0, " yes": -2.0}}


def test_prompt_choices_and_decision_metric_acc(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T10", {"boolq": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[ctx[:4]][kont],
                                 tmp_path, monkeypatch)
    assert [k for c, k in zadania if c == "Cats are small domesticated mammals.\nQuestion: are cats mammals?\nAnswer:"
            ] == [" no", " yes"]
    assert [k for c, k in zadania if c == "The Nile flows through Egypt.\nQuestion: does the nile flow through peru?"
            "\nAnswer:"] == [" no", " yes"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
