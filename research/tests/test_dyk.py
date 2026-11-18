"""DYK T25 (common/zadania.py, benchmarks/dyk/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `dyk_mc.yaml` (5 bank
demonstrations, then the question; continuations ` Nie`, ` Tak`, gold = `target|int`, 1 = Tak), and the decision
metric: corpus binary F1 with positive class Tak, not `acc`. `acc_norm` equals `acc` here (both options 3 characters).
In lm-eval `multiple_choice` the fork's `utils.f1` is never called: the item is (gold, pred) and only `utils.agg_f1`
runs, which is symmetric in its two arguments for binary F1. Data: invented questions; demonstrations go in as the
YAML's train split (test_polemo2.ocen_5shot). Run: python tests/test_dyk.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_polemo2 as P  # noqa: E402  (ocen_5shot, prompt_5shot; sets HF_*_OFFLINE)

Z, ZK = P.Z, P.ZK
WYBORY = ["Nie", "Tak"]
DANE = [{"question": "stolica Francji", "answer": "Paryż", "target": 1},
        {"question": "najdłuższa rzeka Polski", "answer": "Wisła", "target": 1},
        {"question": "autor Lalki", "answer": "Sienkiewicz", "target": 0},
        {"question": "największa planeta", "answer": "Mars", "target": 0}]
DEMO = [{"question": f"pytanie przykładowe {i}", "answer": f"odpowiedź {i}", "target": i % 2} for i in range(7)]


def szablon(d):
    return (f'Pytanie: "{d["question"]}"\nSugerowana odpowiedź: "{d["answer"]}"\nPytanie: Czy sugerowana odpowiedź '
            f'na zadane pytanie jest poprawna?\nOdpowiedz krótko "Tak" lub "Nie". Prawidłowa odpowiedź:')


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T25"], ZK.karta("T25").read_text(encoding="utf-8")
    oczekiwane = {"repo": "allegro/klej-dyk", "rewizja": "dd7c3c3bb336738c853ea17c64b85d876e6714a9",
                  "split": "test", "metric": "f1,none", "klucz": "f1", "task": "polish_dyk_multiple_choice",
                  "yaml": "dyk/lm_eval_tasks/polish_dyk/dyk_mc.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 5
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "dyk_mc.yaml" in karta and "| Metryka decyzyjna | `f1` (korpusowe)" in karta
    assert "split: test" in karta and "5-shot" in karta and "klasa pozytywna = „Tak”/1" in karta
    assert '`doc_to_choice: ["Nie", "Tak"]`' in karta and '`doc_to_target: "{{target|int}}"`' in karta
    assert "`Pytanie: \"{{question}}\"\\nSugerowana odpowiedź: \"{{answer}}\"\\n" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T25"] == "dyk"


# predictions Tak, Nie, Nie, Nie against gold 1, 1, 0, 0: acc 3/4 (= acc_norm, equal lengths);
# F1 for Tak: TP 1, FP 0, FN 1 -> 2*1 / (2*1 + 0 + 1) = 2/3
PRED = {"stolica": "Tak", "najdłuższa": "Nie", "autor": "Nie", "największa": "Nie"}


def test_five_shot_prompt_and_decision_metric_f1(tmp_path, monkeypatch):
    def ll(pytanie, kont):
        return -1.0 if kont.strip() == PRED[pytanie.split('"')[1].split()[0]] else -2.0

    roz, zadania, bank = P.ocen_5shot("T25", DANE, DEMO, ll, tmp_path, monkeypatch)
    for doc in DANE:
        kontekst = P.prompt_5shot(szablon, WYBORY, lambda d: d["target"], bank, doc)
        assert kontekst.count("Sugerowana odpowiedź: ") == 6
        assert [k for c, k in zadania if c == kontekst] == [" Nie", " Tak"]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(3 / 4) and space["acc_norm"]["value"] == pytest.approx(3 / 4)
    assert space["glowna"]["metryka"] == "f1" and space["glowna"]["value"] == pytest.approx(2 / 3)
    assert roz["metric"] == "f1,none" and roz["value"] == pytest.approx(2 / 3) and roz["n_scored"] == 4


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
