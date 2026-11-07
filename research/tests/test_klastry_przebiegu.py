"""Testy `+klastry` w przebiegu centralnym: SE wyniku po klastrach (METODOLOGIA, „SE K”), nie po pytaniach.

common/ewaluuj.podsumuj_wariant na próbkach-atrapach z polem klastra w dokumencie, reguły klastrów WinoGrande
i WSC273 w dowolnej kolejności próbek, bootstrap klastrów metryki korpusowej (DYK) oraz zapisane wyniki BLiMP
przebiegu z 03.11 przeliczone z próbek per para. SE K liczy niezależnie tools/statystyka.se_k.
Uruchom: python tests/test_klastry_przebiegu.py (albo pytest).
"""
import gzip
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "common"))
sys.path.insert(0, str(KORZEN / "tools"))
import ewaluuj as E  # noqa: E402
import metryki as M  # noqa: E402
import zadania as Z  # noqa: E402
from statystyka import se_k  # noqa: E402

CFG_ACC = {"metric_list": [{"metric": "acc"}]}  # BLiMP: acc only, no PMI half


def para(trafiona, uid, doc_id=0):
    """Próbka pary BLiMP: poprawne zdanie (indeks 0) wygrywa, gdy `trafiona`."""
    ll = [0.0, -1.0] if trafiona else [-1.0, 0.0]
    return {"doc_id": doc_id, "doc": {"UID": uid}, "target": 0, "arguments": [("", " a"), ("", " b")],
            "filtered_resps": [(x, False) for x in ll]}


def test_blimp_se_is_se_k_over_paradigms_not_over_pairs():
    # three paradigms of 4 pairs: 4/4, 0/4, 2/4 hit -> pairs look independent, paradigms do not
    trafienia = {"p1": [1, 1, 1, 1], "p2": [0, 0, 0, 0], "p3": [1, 0, 1, 0]}
    probki = [para(t, uid) for uid, ts in trafienia.items() for t in ts]
    d = E.podsumuj_wariant(Z.ZADANIA["T01"], [("blimp", CFG_ACC, SimpleNamespace(eval_docs=probki), probki)])
    x = [float(t) for ts in trafienia.values() for t in ts]
    oczekiwane = se_k(x, [u for u, ts in trafienia.items() for _ in ts])
    assert d["acc"]["value"] == pytest.approx(0.5)
    assert d["acc"]["se"] == pytest.approx(oczekiwane["se"]) and d["acc"]["metoda_se"] == "K"
    assert (d["acc"]["k"], d["acc"]["df"]) == (3, 2)
    assert d["acc"]["se_a"] == pytest.approx((0.25 / 12 * 12 / 11) ** 0.5)  # s / sqrt(n), informational
    assert d["acc"]["se"] > 1.5 * d["acc"]["se_a"]
    # b = 1/2 (para: no constant answer); the control reads t at df = k - 1 from the clustered SE
    wb = d["wobec_b"]
    assert (wb["b"], wb["baza"], wb["metoda"], wb["df"]) == (0.5, "losowa", "K", 2) and wb["se"] == d["acc"]["se"]


def test_score_against_b_is_paired_with_the_constant_answer():
    wyniki, zlote = [1, 1, 0, 1, 0, 1], [0, 0, 0, 1, 2, 0]  # constant answer "0" hits 4 of 6, above random 1/3
    glowna = M.srednia_z_niepewnoscia(wyniki)
    wb = E.wobec_b(wyniki, zlote, glowna, {"chance_value": 1 / 3, "majority_value": 4 / 6})
    r = se_k([w - (z == 0) for w, z in zip(wyniki, zlote)], list(range(6)))  # one question per cluster
    assert wb["baza"] == "stala odpowiedz" and wb["b"] == pytest.approx(4 / 6) and wb["metoda"] == "A parowane"
    assert wb["roznica"] == pytest.approx(0.0) and wb["se"] == pytest.approx(r["se"])
    # random baseline above the constant answer: unpaired z with the SE of the score
    wb = E.wobec_b(wyniki, zlote, glowna, {"chance_value": 0.7, "majority_value": 4 / 6})
    assert wb["baza"] == "losowa" and wb["z"] == pytest.approx((4 / 6 - 0.7) / glowna["se"])


def test_task_without_clusters_keeps_the_per_question_se():
    probki = [para(t, "p1") for t in (1, 0, 1, 1)]
    d = E.podsumuj_wariant({**Z.ZADANIA["T01"], "klastry": None},
                           [("blimp", CFG_ACC, SimpleNamespace(eval_docs=probki), probki)])
    assert "metoda_se" not in d["acc"] and d["acc"]["se"] == pytest.approx((0.75 * 0.25 / 3) ** 0.5)


def wino(doc_id, opcje):
    return {"doc_id": doc_id, "doc": {"option1": opcje[0], "option2": opcje[1]}}


@pytest.mark.parametrize("odwroc", [False, True])
def test_winogrande_twin_pairs_in_split_order_whatever_the_sample_order(odwroc):
    probki = [wino(0, ("Ann", "Bob")), wino(1, ("Bob", "Ann")), wino(2, ("cat", "dog")), wino(3, ("x", "y")),
              wino(4, ("y", "x"))]
    if odwroc:
        probki = probki[::-1]
    ids = dict(zip((p["doc_id"] for p in probki), E.klastry_probek(Z.ZADANIA["T07"], probki)))
    assert ids[0] == ids[1] and ids[3] == ids[4] and len({ids[0], ids[2], ids[3]}) == 3


@pytest.mark.parametrize("odwroc", [False, True])
def test_wsc273_schemas_in_split_order_whatever_the_sample_order(odwroc):
    teksty = ["The trophy does not fit in the suitcase because it is too big.",
              "The trophy does not fit in the suitcase because it is too small.",
              "Joan thanked Susan for the help she had given.",
              "Joan thanked Susan for the help she had received."]
    probki = [{"doc_id": i, "doc": {"text": t}} for i, t in enumerate(teksty)]
    if odwroc:
        probki = probki[::-1]
    ids = dict(zip((p["doc_id"] for p in probki), E.klastry_probek(Z.ZADANIA["T14"], probki)))
    assert ids[0] == ids[1] != ids[2] == ids[3]


def test_corpus_metric_bootstrap_draws_whole_clusters():
    zlote, pred = [1, 0, 1, 1, 0, 0, 1, 0], [1, 0, 0, 1, 1, 0, 1, 1]
    f = M.f1_korpus
    po_pytaniach = M.korpusowa_z_niepewnoscia(zlote, pred, f, powtorzenia=2000)
    # one question per cluster: the same draws as the per-question bootstrap
    pojedyncze = M.korpusowa_z_niepewnoscia(zlote, pred, f, powtorzenia=2000, klastry=list(range(8)))
    assert pojedyncze["se"] == pytest.approx(po_pytaniach["se"]) and pojedyncze["metoda_se"] == "B po klastrach"
    # every question twice, both copies in one cluster: drawing whole clusters is drawing the 8 originals, while
    # drawing the 16 rows one by one treats the copies as independent and gives an SE about sqrt(2) smaller
    dwa = M.korpusowa_z_niepewnoscia(zlote * 2, pred * 2, f, powtorzenia=2000, klastry=list(range(8)) * 2)
    assert dwa["k"] == 8 and dwa["se"] == pytest.approx(po_pytaniach["se"])
    assert M.korpusowa_z_niepewnoscia(zlote * 2, pred * 2, f, powtorzenia=2000)["se"] < 0.8 * dwa["se"]


def test_dyk_corpus_f1_uses_the_question_clusters():
    def probka(p, g, pytanie):
        return {"arguments": [("q", " Nie"), ("q", " Tak")], "target": g, "doc": {"question": pytanie},
                "filtered_resps": [(0.0 if i == p else -1.0, False) for i in range(2)]}

    probki = [probka(p, g, q) for p, g, q in zip([1, 0, 0, 1, 1, 1], [1, 1, 0, 0, 1, 0], "aabbcc")]
    cfg = {"metric_list": [{"metric": "acc"}]}
    d = E.podsumuj_wariant({**Z.ZADANIA["T25"], "klucz": "f1"},
                           [("dyk", cfg, SimpleNamespace(eval_docs=probki), probki)])
    assert d["glowna"]["metoda_se"] == "B po klastrach" and d["glowna"]["k"] == 3


def test_resummary_keeps_old_numbers_that_differ_only_by_rounding():
    import podsumuj_ponownie as PP

    stare = {"b": 0.2501564277588168, "se": 0.0016, "lista": [1.0, 2.0]}
    nowe = {"b": 0.25015642775881686, "se": 0.0197, "lista": [1.0, 2.0], "k": 67}
    assert PP.scal(stare, nowe) == {"b": 0.2501564277588168, "se": 0.0197, "lista": [1.0, 2.0], "k": 67}
    assert not PP.rozne(stare["b"], nowe["b"]) and PP.rozne(stare["se"], nowe["se"])


def test_committed_central_run_blimp_se_is_se_k_of_its_samples():
    katalog = KORZEN / "results/central-run/blimp/slayer1b-1.06"
    with gzip.open(katalog / "probki/T01_space.jsonl.gz", "rt") as f:
        probki = [json.loads(w) for w in f]
    r = se_k([float(p["acc"]) for p in probki], [p["doc"]["UID"] for p in probki])
    acc = json.loads((katalog / "results_rozszerzone.json").read_text())["observations"][0]["dodatkowe"]["space"]["acc"]
    assert r["k"] == 67 and acc["se"] == pytest.approx(r["se"], rel=1e-9)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
