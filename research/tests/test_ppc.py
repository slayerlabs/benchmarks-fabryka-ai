"""PPC T26 (common/zadania.py, benchmarks/ppc/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `ppc_mc.yaml` (5 bank
demonstrations, then the sentence pair; continuations ` A`, ` B`, ` C`, gold = `label|int - 1`, so 1 -> A, 3 -> C),
and the decision metric `acc`. `acc_norm` equals `acc` (all options 1 character, card "Ocena"), so it cannot be told
apart on any model; the test checks the equality. Data: invented sentence pairs; demonstrations go in as the YAML's
train split (test_polemo2.ocen_5shot). Run: python tests/test_ppc.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_polemo2 as P  # noqa: E402  (ocen_5shot, prompt_5shot; sets HF_*_OFFLINE)

Z, ZK = P.Z, P.ZK
WYBORY = ["A", "B", "C"]
DANE = [{"sentence_A": "Kot śpi.", "sentence_B": "Kot drzemie.", "label": 1},
        {"sentence_A": "Pada deszcz.", "sentence_B": "Jutro egzamin.", "label": 3},
        {"sentence_A": "Idę do sklepu.", "sentence_B": "Wybieram się na zakupy.", "label": 2}]
DEMO = [{"sentence_A": f"Zdanie przykładowe {i}.", "sentence_B": f"Inne zdanie {i}.", "label": i % 3 + 1}
        for i in range(7)]


def szablon(d):
    return (f'Zdanie A: "{d["sentence_A"]}"\nZdanie B: "{d["sentence_B"]}"\nPytanie: jaka jest zależność między '
            f"zdaniami A i B? Możliwe odpowiedzi:\nA - znaczą dokładnie to samo\nB - mają podobne znaczenie\n"
            f"C - mają różne znaczenie\nPrawidłowa odpowiedź:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T26"], ZK.karta("T26").read_text(encoding="utf-8")
    oczekiwane = {"repo": "sdadas/ppc", "rewizja": "073012dc81efb47b0fd66b0ab48bf06ddb62f528",
                  "split": "test", "metric": "acc,none", "task": "polish_ppc_multiple_choice",
                  "yaml": "ppc/lm_eval_tasks/polish_ppc/ppc_mc.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 5
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `acc` |" in karta and "split: test" in karta and "5-shot" in karta
    assert '`doc_to_choice`: `["A","B","C"]`' in karta and '`doc_to_target`: `"{{label|int - 1}}"`' in karta
    assert '\\nPrawidłowa odpowiedź:"`' in karta and "`1`→A" in karta and "`3`→C" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T26"] == "ppc"


# the model answers A for every pair: gold A (label 1) hit, C (label 3) and B (label 2) missed -> acc 1/3 = acc_norm
def test_five_shot_prompt_and_decision_metric_acc(tmp_path, monkeypatch):
    roz, zadania, bank = P.ocen_5shot("T26", DANE, DEMO, lambda pytanie, kont: -1.0 if kont == " A" else -2.0,
                                      tmp_path, monkeypatch)
    for doc in DANE:
        kontekst = P.prompt_5shot(szablon, WYBORY, lambda d: d["label"] - 1, bank, doc)
        assert kontekst.count("Zdanie A: ") == 6
        assert [k for c, k in zadania if c == kontekst] == [" A", " B", " C"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 3) and space["acc_norm"]["value"] == pytest.approx(1 / 3)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 3) and roz["n_scored"] == 3


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
