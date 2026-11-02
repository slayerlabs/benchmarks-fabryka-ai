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


def test_poziom_losowy_symulacja():
    # losowe logliki: ewok i stały target 0,5, „oba” 0,25 (przy niezależnych porównaniach)
    import random
    rng = random.Random(0)
    o = [E.ocen(rek([[rng.gauss(0, 1) for _ in range(2)] for _ in range(2)], bezw=(rng.gauss(0, 1), rng.gauss(0, 1))))
         for _ in range(20000)]
    sr = lambda k: sum(x[k] for x in o) / len(o)
    assert abs(sr("ewok") - 0.5) < 0.01 and abs(sr("oba") - 0.25) < 0.01 and abs(sr("staly_target") - 0.5) < 0.01


def test_zamiana_kontekstow_odwraca_wynik():
    # symetria: C1↔C2 przy tych samych T daje wynik 1 − wynik (bez remisów)
    ll = [[-1.0, -4.0], [-3.0, -2.5]]
    a = E.ocen(rek(ll))["ewok"]
    b = E.ocen(rek([ll[1], ll[0]]))["ewok"]
    assert a + b == 1.0


def test_remis_zdan_to_nie_staly_target():
    # przy C1 remis T1 = T2 (k1 fałsz), przy C2 wygrywa T2: wybory różne, więc nie „stały target”
    o = E.ocen(rek([[-2.0, -2.0], [-3.0, -1.0]]))
    assert o["staly_target"] == 0.0


def test_szablony_grupuja_wypelnienia():
    pola = lambda imie, rzecz: {"Context1": f"{imie} sees the {rzecz} inside.", "Context2": f"{imie} sees the {rzecz} outside.",
                                "Target1": f"{imie} believes the {rzecz} is in.", "Target2": f"{imie} doubts the {rzecz} is in."}
    pola2 = lambda imie, rzecz: {"Context1": f"{imie} moved the {rzecz} into the shop.", "Context2": f"{imie} moved the {rzecz} out of the shop.",
                                 "Target1": f"{imie} believes the {rzecz} is in.", "Target2": f"{imie} doubts the {rzecz} is in."}
    wyp = [(f"Imie{i}", f"rzecz{i}") for i in range(10)]
    meta = {"ConceptA": "believe", "ConceptB": "doubt", "Domain": "agent-properties"}
    recs = [{"source_id": i, **meta, **(pola if i < 5 else pola2)(*w)} for i, w in enumerate(wyp)]
    s = E.szablony(recs)
    assert len({s[i] for i in range(5)}) == 1 and len({s[i] for i in range(5, 10)}) == 1 and s[5] != s[0]


def test_srednia_klastrowa_szersza_przy_skorelowanych_rekordach():
    # 20 szablonów po 5 identycznych rekordów: CI po szablonach szerszy niż po rekordach
    wart = [float(k % 2) for k in range(20) for _ in range(5)]
    kl = [k for k in range(20) for _ in range(5)]
    sk = E.srednia_klastrowa(wart, kl)
    zw = E.srednia_z_niepewnoscia(wart)
    assert sk["value"] == zw["value"] == 0.5 and sk["n_szablonow"] == 20
    assert (sk["ci95"][1] - sk["ci95"][0]) > 1.5 * (zw["ci95"][1] - zw["ci95"][0])


def test_roznica_roznic():
    o = lambda v: {"ewok": v}
    a, b, a2, b2 = {0: o(1.0), 1: o(0.5)}, {0: o(0.5), 1: o(0.5)}, {0: o(1.0), 1: o(1.0)}, {0: o(0.0), 1: o(0.5)}
    k = E.kontrast(a, b, "a", "b", szabl={0: 0, 1: 1}, a2=a2, b2=b2)
    # (0,5 − 1,0) i (0 − 0,5) → średnia −0,5
    assert k["roznica"]["value"] == -0.5 and k["n"] == 2 and "p_po_szablonach" in k


def test_zaokraglenie_polowek_w_gore():
    assert E.zaokr(0.575 * 100, 0) == "58" and E.zaokr(0.5225 * 100) == "52.3" and E.zaokr(0.05, znak=True) == "+0.1"


if __name__ == "__main__":
    for nazwa, f in list(globals().items()):
        if nazwa.startswith("test_"):
            f()
    print("OK")
