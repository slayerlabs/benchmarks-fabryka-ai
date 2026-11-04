"""tools/statystyka.py: SE K przy klastrach nierównych, porównanie ze stałym predyktorem, Holm z flagą."""
import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import statystyka as S  # noqa: E402

# 3 klastry nierówne: 4, 2 i 1 pozycja
X = [1, 1, 0, 1, 0, 0, 1]
C = ["a", "a", "a", "a", "b", "b", "c"]


def test_se_k_wzor_przy_klastrach_nierownych():
    r = S.se_k(X, C)
    xbar = sum(X) / len(X)
    sumy = {}
    for x, c in zip(X, C):
        sumy[c] = sumy.get(c, 0.0) + (x - xbar)
    k = len(sumy)
    oczek = math.sqrt(k / (k - 1) * sum(v * v for v in sumy.values())) / len(X)
    assert math.isclose(r["se"], oczek, rel_tol=1e-12)
    assert r["k"] == 3 and r["df"] == 2 and r["n"] == 7 and math.isclose(r["srednia"], xbar)
    assert math.isclose(r["p_t"], S.p_t(r["t"], 2)) and r["werdykt"] == S.werdykt_p(r["p_t"])


def test_se_k_rowne_klastry_to_sd_srednich_przez_pierwiastek_k():
    xs = [0.9, 0.7, 0.8, 0.4, 0.6, 0.5, 0.2, 0.3, 0.1]
    cs = [i // 3 for i in range(9)]
    srednie = [statistics.fmean(xs[i:i + 3]) for i in (0, 3, 6)]
    assert math.isclose(S.se_k(xs, cs)["se"], statistics.stdev(srednie) / math.sqrt(3), rel_tol=1e-12)


def test_se_k_odwrocona_kolejnosc_pozycji_daje_to_samo():
    a, b = S.se_k(X, C, b=0.5), S.se_k(X[::-1], C[::-1], b=0.5)
    for klucz in ("srednia", "roznica", "se", "t", "p_t", "werdykt", "k"):
        assert a[klucz] == b[klucz] or math.isclose(a[klucz], b[klucz], rel_tol=1e-12)


def test_se_k_wobec_b_przesuwa_srednia_nie_se():
    a, b = S.se_k(X, C), S.se_k(X, C, b=0.5)
    assert math.isclose(a["se"], b["se"]) and math.isclose(b["roznica"], a["roznica"] - 0.5)


def test_se_k_mniej_niz_3_klastry_nierozstrzygalne():
    r = S.se_k([1, 1, 1, 0, 0, 1], [0, 0, 0, 1, 1, 1])
    assert r["k"] == 2 and r["werdykt"] == S.NIEROZSTRZYGALNE and r["se"] > 0  # t policzone, werdyktu nie ma
    assert S.se_k([1, 0, 1], [0, 0, 0])["werdykt"] == S.NIEROZSTRZYGALNE  # k = 1: bez SE


def test_wobec_stalej_parowane():
    gold = [0, 0, 0, 1, 1, 0, 1, 0]  # najczęstsza: 0 (5 z 8), b = 0,625
    wyn = [1, 1, 0, 1, 1, 1, 1, 0]
    r = S.wobec_stalej(wyn, gold)
    d = [w - (g == 0) for w, g in zip(wyn, gold)]
    assert r["stala"] == 0 and math.isclose(r["b"], 5 / 8)
    assert math.isclose(r["roznica"], statistics.fmean(d))
    assert math.isclose(r["se"], statistics.stdev(d) / math.sqrt(8))
    assert r["werdykt"] == S.werdykt(r["roznica"] / r["se"]) and r["metoda"] == "A parowane"


def test_wobec_stalej_odwrocona_kolejnosc_i_remis_klas():
    gold = [1, 0, 1, 0, 1, 0]  # remis 3:3 -> najmniejsza etykieta, niezależnie od kolejności
    wyn = [1, 1, 0, 1, 1, 0]
    a, b = S.wobec_stalej(wyn, gold), S.wobec_stalej(wyn[::-1], gold[::-1])
    assert a["stala"] == b["stala"] == 0
    assert math.isclose(a["se"], b["se"]) and math.isclose(a["z"], b["z"])


def test_wobec_stalej_bez_rozrzutu_nierozstrzygalne():
    r = S.wobec_stalej([1, 1, 1, 1], [0, 0, 0, 0])  # model = stała na każdej pozycji
    assert r["se"] == 0 and r["z"] is None and r["werdykt"] == S.NIEROZSTRZYGALNE


def test_wobec_stalej_z_klastrami_to_se_k_roznic():
    gold = [0, 0, 1, 1, 0, 1, 0, 0]
    wyn = [1, 0, 1, 1, 1, 0, 1, 1]
    kl = [0, 0, 1, 1, 2, 2, 3, 3]
    r = S.wobec_stalej(wyn, gold, klastry=kl)
    ref = S.se_k([w - (g == 0) for w, g in zip(wyn, gold)], kl)
    assert r["metoda"] == "K" and r["df"] == 3 and math.isclose(r["se"], ref["se"]) and r["werdykt"] == ref["werdykt"]


def test_holm_skumulowany_max_i_obciecie():
    assert S.holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]
    assert S.holm([0.9, 0.8]) == [1.0, 1.0]


def test_holm_odwrocona_kolejnosc_wierszy():
    ps = [0.001, 0.02, 0.0004, 0.3, 0.01]
    assert S.holm(ps[::-1]) == S.holm(ps)[::-1]
    assert [r["po_holmie"] for r in S.po_holmie(ps[::-1])] == [r["po_holmie"] for r in S.po_holmie(ps)][::-1]


def test_po_holmie_flaga_i_werdykt():
    # p surowe 0,002 (pewne) w rodzinie 3: 3 · 0,002 = 0,006 > p(|z| = 3) -> prawdopodobne po Holmie
    w = S.po_holmie([0.002, 0.02, 0.5])
    assert [r["po_holmie"] for r in w] == ["tak", "tak", "nie"]
    assert [r["werdykt_holm"] for r in w] == ["prawdopodobne", "prawdopodobne", "szum"]


def test_po_holmie_wiersz_bez_p_poza_rodzina():
    w = S.po_holmie([None, 0.02, 0.01])  # rodzina m = 2, nie 3
    assert w[0] == {"p_holm": None, "werdykt_holm": S.NIEROZSTRZYGALNE, "po_holmie": "nie"}
    assert math.isclose(w[2]["p_holm"], 0.02) and math.isclose(w[1]["p_holm"], 0.02)


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
