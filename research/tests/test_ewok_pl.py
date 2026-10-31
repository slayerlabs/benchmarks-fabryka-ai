"""Czyste funkcje EWoK-PL (benchmarks/ewok-pl/ewok.py), bez wag i bez danych. Uruchom: python tests/test_ewok_pl.py (albo pytest)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "benchmarks" / "ewok-pl"))
import ewok as E  # noqa: E402


def rek(ll, bezw=(-10.0, -10.0)):
    return {"ll": ll, "bezw": list(bezw)}


def test_obie_pary_trafione_daja_punkt():
    # T1 lepiej po C1, T2 lepiej po C2
    o = E.ocen(rek([[-1.0, -5.0], [-3.0, -2.0]]))
    assert o["ewok"] == 1.0 and o["oba"] == 1.0


def test_jedna_para_daje_pol_punktu():
    o = E.ocen(rek([[-1.0, -5.0], [-3.0, -6.0]]))
    assert o["ewok"] == 0.5 and o["oba"] == 0.0


def test_remis_to_pudlo():
    o = E.ocen(rek([[-1.0, -1.0], [-1.0, -1.0]]))
    assert o["ewok"] == 0.0


def test_prior_zdania_nie_psuje_reguly_glownej():
    # T2 ma dużo niższy prior: przy stałym kontekście model zawsze wybiera T1 (stały target),
    # a reguła z paperu (target stały) i tak widzi, że kontekst przesuwa oba zdania we właściwą stronę
    o = E.ocen(rek([[-1.0, -9.0], [-2.0, -8.0]], bezw=(-1.0, -8.5)))
    assert o["ewok"] == 1.0 and o["kontekst_staly"] == 0.5 and o["staly_target"] == 1.0
    assert o["kontekst_staly_pmi"] == 1.0


def test_id_na_source_id():
    assert E.w_id_src("ewok-pl-0001") == 0 and E.w_id_src("ewok-en-0624") == 624


def test_holm_monotoniczny_i_obciety():
    assert E.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert E.holm([0.9, 0.8]) == [1.0, 1.0]


def test_permutacja_bez_roznicy_daje_duze_p():
    assert E.test_permutacyjny([0.5, -0.5] * 50) > 0.9
    assert E.test_permutacyjny([0.5] * 60) < 0.001


if __name__ == "__main__":
    for nazwa, f in list(globals().items()):
        if nazwa.startswith("test_"):
            f()
    print("OK")
