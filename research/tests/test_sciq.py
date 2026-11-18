"""SciQ T09 (common/zadania.py, benchmarks/sciq/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the lm-eval `sciq` prompt `{{support.lstrip()}}\nQuestion: {{question}}\nAnswer:`
(the support paragraph comes first; an empty support leaves the context starting with "\n"), and the decision metric
`acc_norm` (not `acc`) on a stand-in model.

Option order: the code sends `[distractor1, distractor2, distractor3, correct_answer]` with `doc_to_target: 3`, so
the correct option is always last, as the card says; a tie (correct answer equal to a distractor, 2 test questions per
the card) is lost to the earlier distractor. benchmarks/sciq/README.md files T09 under type `poz` ("needs a second
run with shuffled options"); no shuffled-option variant exists in common/ (one variant, `space`), so only the dataset
order is scored, as the README states. Data: three invented questions. Run: python tests/test_sciq.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
DANE = [{"question": "Which animals are warm-blooded?", "distractor1": "fish", "distractor2": "reptiles",
         "distractor3": "insects", "correct_answer": "mammals", "support": "  Mammals are warm-blooded animals."},
        {"question": "What gas do plants absorb?", "distractor1": "oxygen", "distractor2": "helium",
         "distractor3": "neon", "correct_answer": "carbon dioxide", "support": ""},
        {"question": "What is frozen water?", "distractor1": "ice", "distractor2": "steam",
         "distractor3": "vapor", "correct_answer": "ice", "support": "Water freezes at 0 C."}]
KONTEKSTY = ["Mammals are warm-blooded animals.\nQuestion: Which animals are warm-blooded?\nAnswer:",
             "\nQuestion: What gas do plants absorb?\nAnswer:",
             "Water freezes at 0 C.\nQuestion: What is frozen water?\nAnswer:"]


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T09"], ZK.karta("T09").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allenai/sciq", "rewizja": "2c94ad3e1aafab77146f384e23536f97a4849815",
                  "split": "test", "metric": "acc_norm,none", "task": "sciq"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 0 and "nazwa_hf" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc_norm`" in karta and "split: `test`" in karta and "0-shot" in karta
    assert "`{{support.lstrip()}}\\nQuestion: {{question}}\\nAnswer:`" in karta
    assert "`[distractor1, distractor2, distractor3, correct_answer]`" in karta and "`doc_to_target: 3`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T09"] == "sciq"


def test_one_variant_correct_option_always_last():
    """No shuffled-option run in the code (README: type `poz`): one `space` variant, gold fixed at index 3."""
    (wariant, cfg), = Z.konfiguracje("T09")
    assert wariant == "space" and cfg["doc_to_target"] == 3
    assert cfg["doc_to_choice"] == "{{[distractor1, distractor2, distractor3, correct_answer]}}"


# q1 gold mammals: acc fish (-4 > -6), acc_norm mammals (-6/7 = -0.857 > -4/4 = -1);
# q2 gold carbon dioxide: wins both (-2 > -3, -2/14 > -3/6);
# q3 gold ice == distractor1 ice: equal logliks, the earlier option (index 0) wins -> wrong in both
# -> acc 1/3, acc_norm 2/3
LL = {" fish": -4.0, " reptiles": -99.0, " insects": -99.0, " mammals": -6.0,
      " oxygen": -3.0, " helium": -99.0, " neon": -99.0, " carbon dioxide": -2.0,
      " ice": -1.0, " steam": -99.0, " vapor": -99.0}


def test_prompt_choices_and_decision_metric_acc_norm(tmp_path, monkeypatch):
    roz, zadania = C.ocen_loglik("T09", {"sciq": DANE}, lambda ctx, kont: 0.0 if ctx == "" else LL[kont],
                                 tmp_path, monkeypatch)
    for kontekst, doc in zip(KONTEKSTY, DANE):
        assert [k for c, k in zadania if c == kontekst] == [
            " " + doc[p] for p in ("distractor1", "distractor2", "distractor3", "correct_answer")]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 3) and space["acc_norm"]["value"] == pytest.approx(2 / 3)
    assert roz["metric"] == "acc_norm,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
