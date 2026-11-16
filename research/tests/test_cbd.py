"""CBD T28 (common/zadania.py, benchmarks/cbd/ORIGINAL.md), no network and no weights.

The ZADANIA entry against the card, the 5-shot prompt of the copied OpenPL YAML `cbd_mc.yaml` (5 bank demonstrations,
then the question; 6 continuations = space + category, gold = the YAML's map of `CATEGORIES`, an empty or unknown
category = 0 = nieszkodliwa), and the decision metric: corpus macro F1 (`utils.agg_f1_macro`), not `acc`.
Data: invented entries; demonstrations go in as the YAML's train split (test_polemo2.ocen_5shot).
Run: python tests/test_cbd.py (or pytest).
"""
import sys
from pathlib import Path

import pytest

TESTY = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTY))
import test_polemo2 as P  # noqa: E402  (ocen_5shot, prompt_5shot; sets HF_*_OFFLINE)

Z, ZK = P.Z, P.ZK
WYBORY = ["nieszkodliwa", "szyderstwo", "obelga", "insynuacja", "groźba", "molestowanie"]
MAPA = {"szyderstwo": 1, "obelga": 2, "insynuacja": 3, "grozba": 4, "molestowanie": 5}  # cbd_mc.yaml doc_to_target
DANE = [{"TEXT": "Miłego dnia wszystkim", "CATEGORIES": ""},
        {"TEXT": "Dzięki za pomoc", "CATEGORIES": "nieszkodliwa"},
        {"TEXT": "Ale z ciebie geniusz haha", "CATEGORIES": "szyderstwo"},
        {"TEXT": "Ty głupku", "CATEGORIES": "obelga"}]
DEMO = [{"TEXT": f"Wypowiedź przykładowa {i}", "CATEGORIES": ["", "szyderstwo", "obelga"][i % 3]} for i in range(7)]


def szablon(d):
    return (f'Wypowiedź: "{d["TEXT"]}"\nDo podanej wypowiedzi przyporządkuj jedną, najlepiej pasującą kategorię z '
            f"podanych: nieszkodliwa, szyderstwo, obelga, insynuacja, groźba, molestowanie.\nKategoria:")


def test_entry_matches_the_card():
    """Values copied from the card; each must be in ZADANIA and in the card text (catches a change on one side)."""
    meta, karta = Z.ZADANIA["T28"], ZK.karta("T28").read_text(encoding="utf-8")
    oczekiwane = {"repo": "ptaszynski/PolishCyberbullyingDataset", "rewizja": "be3b1236598a02eff6db05ea7ac386afaabc33e8",
                  "split": "test", "metric": "f1,none", "klucz": "f1", "task": "polish_cbd_multiple_choice",
                  "yaml": "cbd/lm_eval_tasks/polish_cbd/cbd_mc.yaml"}
    assert {k: meta[k] for k in oczekiwane} == oczekiwane and ZK.shoty(meta) == 5
    assert meta["klasy_stale"] and "klastry" not in meta
    for k in ("repo", "rewizja"):
        assert oczekiwane[k] in karta, k
    assert "| Metryka decyzyjna | `f1` (makro, korpusowe)" in karta
    assert "split: test; n: 1" in karta and "5-shot" in karta
    assert '`["nieszkodliwa", "szyderstwo", "obelga", "insynuacja", "groźba", "molestowanie"]`' in karta
    assert "`{{{'szyderstwo': 1, 'obelga': 2, 'insynuacja': 3, 'grozba': 4, 'molestowanie': 5}.get(CATEGORIES, 0)}}`" in karta
    assert '`Wypowiedź: "{{TEXT}}"\\nDo podanej wypowiedzi przyporządkuj' in karta
    assert ZK.rozbieznosci(meta, karta) == {}
    assert ZK.KATALOGI["T28"] == "cbd"


# gold (YAML map): 0, 0, 1, 2; predictions nieszkodliwa, szyderstwo, szyderstwo, nieszkodliwa -> acc 2/4.
# Macro F1 over the classes present (0, 1, 2): class 0 TP 1, FP 1, FN 1 -> 1/2; class 1 TP 1, FP 1 -> 2/3;
# class 2 FN 1 -> 0; mean (1/2 + 2/3 + 0) / 3 = 7/18. The winning option is far ahead (-1 against -20), so
# acc_norm picks the same options -> 2/4.
PRED = {"Miłego": "nieszkodliwa", "Dzięki": "szyderstwo", "Ale": "szyderstwo", "Ty": "nieszkodliwa"}


def test_five_shot_prompt_and_decision_metric_macro_f1(tmp_path, monkeypatch):
    def ll(pytanie, kont):
        return -1.0 if kont.strip() == PRED[pytanie.split('"')[1].split()[0]] else -20.0

    roz, zadania, bank = P.ocen_5shot("T28", DANE, DEMO, ll, tmp_path, monkeypatch)
    for doc in DANE:
        kontekst = P.prompt_5shot(szablon, WYBORY, lambda d: MAPA.get(d["CATEGORIES"], 0), bank, doc)
        assert kontekst.count("Wypowiedź: ") == 6
        assert [k for c, k in zadania if c == kontekst] == [" " + w for w in WYBORY]
    space = roz["dodatkowe"]["space"]
    assert space["acc"]["value"] == pytest.approx(2 / 4) and space["acc_norm"]["value"] == pytest.approx(2 / 4)
    assert space["glowna"]["metryka"] == "f1" and space["glowna"]["value"] == pytest.approx(7 / 18)
    assert roz["metric"] == "f1,none" and roz["value"] == pytest.approx(7 / 18) and roz["n_scored"] == 4


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
