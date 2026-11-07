"""8TAGS T23 (common/zadania.py, benchmarks/8tags/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `8tags_mc.yaml` (5 bank
demonstrations, then the title; continuations = space + category name, gold = `label|int`), and the decision metric
`acc` (not `acc_norm`) on a stand-in model. Data: invented titles; demonstrations go in as the YAML's train split
(test_polemo2.ocen_5shot). Run: python tests/test_8tags.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_polemo2 as P  # noqa: E402  (ocen_5shot, prompt_5shot; sets HF_*_OFFLINE)

Z, ZK = P.Z, P.ZK
WYBORY = ["Film", "Historia", "Jedzenie", "Medycyna", "Motoryzacja", "Praca", "Sport", "Technologie"]
DANE = [{"sentence": "Nowy silnik hybrydowy w kompakcie", "label": 4},
        {"sentence": "Finał ligi zakończony karnymi", "label": 6}]
DEMO = [{"sentence": f"Tytuł przykładowy {i}", "label": i} for i in range(8)]


def szablon(d):
    return (f'Tytuł: "{d["sentence"]}"\nDo podanego tytułu przyporządkuj jedną najlepiej pasującą kategorię z '
            f"podanych: Film, Historia, Jedzenie, Medycyna, Motoryzacja, Praca, Sport, Technologie.\nKategoria:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T23"], ZK.karta("T23").read_text(encoding="utf-8")
    oczekiwane = {"repo": "sdadas/8tags", "rewizja": "82ddf9c0d06ffc982aeccf2473b7ce31f2167adf",
                  "split": "test", "metric": "acc,none", "task": "polish_8tags_multiple_choice",
                  "yaml": "8tags/lm_eval_tasks/polish_8tags/8tags_mc.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 5
    for k in ("repo", "rewizja", "task"):
        assert oczekiwane[k] in karta, k
    assert "8tags_mc.yaml" in karta and "| Metryka decyzyjna | `acc` (trafność" in karta
    assert "split `test`" in karta and "5-shot" in karta
    assert "`" + str(WYBORY).replace("'", '"') + "`" in karta and "`{{label|int}}`" in karta
    assert "`Tytuł: \"{{sentence}}\"`" in karta and "`Kategoria:`" in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T23"] == "8tags"


# len: Film 4, Motoryzacja 11, Sport 5. q1 gold Motoryzacja (label 4): acc Film (-4 > -6), acc_norm Motoryzacja
# (-6/11 = -0.545 > -4/4 = -1); q2 gold Sport (label 6) wins both -> acc 1/2, acc_norm 1
LL = {"Nowy": {"Film": -4.0, "Motoryzacja": -6.0}, "Finał": {"Sport": -1.0}}


def test_five_shot_prompt_and_decision_metric_acc(tmp_path, monkeypatch):
    def ll(pytanie, kont):
        return LL[pytanie.split('"')[1].split()[0]].get(kont.strip(), -9.0)

    roz, zadania, bank = P.ocen_5shot("T23", DANE, DEMO, ll, tmp_path, monkeypatch)
    for doc in DANE:
        kontekst = P.prompt_5shot(szablon, WYBORY, lambda d: d["label"], bank, doc)
        assert kontekst.count("Tytuł: ") == 6
        assert [k for c, k in zadania if c == kontekst] == [" " + w for w in WYBORY]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(1 / 2) and space["acc_norm"]["value"] == pytest.approx(1.0)
    assert roz["metric"] == "acc,none" and roz["value"] == pytest.approx(1 / 2) and roz["n_scored"] == 2


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
