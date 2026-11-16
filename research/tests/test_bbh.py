"""BIG-Bench Hard T47 (common/zadania.py, benchmarks/bbh/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card (group `bbh_fewshot`, 27 subtasks, 3 fixed source demonstrations, not the bank),
the prompt of one subtask (description, 3 source demonstrations `Q: ...\nA: <target>`, then `Q: {input}\nA:`), and
the decision metric `exact_match` after stripping whitespace from the answer, averaged over subtasks with population
weights (`+warstwy`), so a subtask with more questions weighs more. Data: invented inputs.
Run: python tests/test_bbh.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_przebieg_c as C  # noqa: E402  (sets HF_*_OFFLINE, imports common/)
import test_zgodnosc_karty as ZK  # noqa: E402

Z = C.Z
BOOL = "bbh_fewshot_boolean_expressions"
DEMO_BOOL = ("Evaluate the result of a random Boolean expression.\n\n"
             "Q: not ( ( not not True ) ) is\nA: False\n\n"
             "Q: True and False and not True and True is\nA: False\n\n"
             "Q: not not ( not ( False ) ) is\nA: True\n\n")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T47"], ZK.karta("T47").read_text(encoding="utf-8")
    oczekiwane = {"repo": "lukaemon/bbh", "rewizja": "982bb89fd79532a8ac676a61fc42eb1aeec63f99", "split": "test",
                  "metric": "exact_match,none", "klucz": "exact_match", "task": "bbh_fewshot", "grupa": "bbh_fewshot",
                  "rodzaj": "proba", "baza": "gen", "shots": 3, "strip": True}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 3 and "klastry" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "grupa lm-eval `bbh_fewshot` z 27 podtestami, 3 stałe demonstracje źródłowe, metryka `exact_match`" in karta
    assert "| Metryka decyzyjna | `exact_match` po obcięciu białych znaków, 3-shot, średnia podtestów z wagami" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T47"] == "bbh"


def test_group_has_27_subtasks_with_three_shots_and_the_card_revision():
    czlonkowie = Z.czlonkowie_grupy("bbh_fewshot")
    assert len(czlonkowie) == 27 and BOOL in czlonkowie
    warianty = Z.konfiguracje("T47")
    assert [cfg["task"] for _, cfg in warianty] == [f"slayer_{m}" for m in czlonkowie]
    for _, cfg in warianty:
        assert cfg["num_fewshot"] == 3 and cfg["output_type"] == "generate_until"
        assert cfg["dataset_kwargs"]["revision"] == "982bb89fd79532a8ac676a61fc42eb1aeec63f99"


# boolean_expressions: 3 questions, gold True, True, False, the model answers " True" -> 2 of 3 after stripping;
# the other 26 subtasks: 1 question each, gold "X" -> 0. Population weights: 2 / (3 + 26) = 2/29;
# an unweighted mean of subtasks would give (2/3) / 27 = 2/81.
def test_source_shots_strip_and_population_weights(tmp_path, monkeypatch):
    czlonkowie = Z.czlonkowie_grupy("bbh_fewshot")
    dane = {m: [{"input": f"{m} x", "target": "X"}] for m in czlonkowie}
    dane[BOOL] = [{"input": f"b{i}", "target": t} for i, t in enumerate(["True", "True", "False"])]
    lm = C.AtrapaLM(gen=lambda ctx: " True")
    obs, d = C.ocen("T47", dane, lm, tmp_path, monkeypatch)
    assert [c for c in lm.konteksty if c.endswith("Q: b0\nA:")] == [DEMO_BOOL + "Q: b0\nA:"]
    assert all(c.count("Q: ") == 4 for c in lm.konteksty)  # 3 source demonstrations + the question
    assert "demonstracje" not in d  # source shots, no bank
    assert d["glowna"]["value"] == pytest.approx(2 / 29)
    assert obs["metric"] == "exact_match,none" and obs["value"] == pytest.approx(2 / 29) and obs["n_scored"] == 29


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
