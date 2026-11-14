"""Pomiar 1.09 krok 40 000 (results/full-run-2026-11/slayer-1.09-k40000/): warunek startu (architektura), Holm z m z
protokołu, kontrola narzędzia, werdykt końcowy, porównanie parowane na atrapie z deterministycznymi logitami i
oznaczenie „w toku” w generatorze raportu. Bez sieci i bez prawdziwych wag."""
import json
import math
import sys
import tempfile
from pathlib import Path

import pytest

KORZEN = Path(__file__).resolve().parent.parent
KOD = KORZEN / "results" / "full-run-2026-11" / "slayer-1.09-k40000" / "code"
sys.path[:0] = [str(KOD), str(KORZEN / "tools" / "ewaluacja"), str(KORZEN / "tools"), str(KORZEN / "common")]
import liczby_109 as L  # noqa: E402
import raport as R  # noqa: E402
import sprawdz_architekture as SA  # noqa: E402
import statystyka as S  # noqa: E402

KSZ = {"tok.weight": (32768, 2048), "blocks.0.attn.qkv.weight": (6144, 2048), "norm.weight": (2048,)}
CFG = {"vocab": 32768, "n_layer": 20, "n_embd": 2048, "n_head": 16, "block": 4096, "qk_norm": True, "data_seed": 1}
TOK = "0640d3bd" + "0" * 56


def arch(ksz=None, cfg=None, wzorzec=None, cfg_wz=None, tok=TOK):
    ck = {"_orig_mod." + k: v for k, v in (ksz or KSZ).items()}
    ck["_orig_mod.head.weight"] = (32768, 2048)
    return SA.porownaj(ck, wzorzec or KSZ, CFG if cfg is None else cfg, cfg_wz or {**CFG, "data_seed": 2}, tok)


def test_architektura_rowna_mimo_innego_data_seed():
    assert arch()["zgodne"]


@pytest.mark.parametrize("zmiana", [
    {"ksz": {**KSZ, "norm.weight": (2049,)}},
    {"ksz": {k: v for k, v in KSZ.items() if k != "norm.weight"}},
    {"ksz": {**KSZ, "blocks.0.nowy": (4,)}},
    {"cfg": {**CFG, "n_layer": 21}},
    {"cfg": {**CFG, "n_layer": 21}, "cfg_wz": {**CFG, "n_layer": 21}},  # zgodne ze wzorcem, ale nie 20 warstw 1.08
    {"cfg": {}},
    {"tok": "1" * 64},
])
def test_kazda_roznica_architektury_zatrzymuje(zmiana):
    assert not arch(**zmiana)["zgodne"]


def test_holm_z_m_protokolu_liczy_wiersze_bez_p():
    ps = [0.001, None, 0.01]
    assert S.holm(ps) == [0.002, None, 0.01]
    h = S.holm(ps, m=15)
    assert h[0] == pytest.approx(0.015) and h[1] is None and h[2] == pytest.approx(0.14)
    with pytest.raises(ValueError):
        S.holm([0.1, 0.2], m=1)


def test_holm_odwrocona_kolejnosc_z_m():
    ps = [0.03, 0.0001, None, 0.2, 0.004]
    assert S.holm(ps[::-1], m=15) == S.holm(ps, m=15)[::-1]


def wiersz(wartosc, n=100, skala=1.0):
    return {"wartosc": wartosc, "n": n, "skala_w_pliku": skala}


@pytest.mark.parametrize("przeliczone,manifest,zgodna", [
    (wiersz(0.5049), {"wartosc": 0.5, "se": 0.01, "n": 100}, True),
    (wiersz(0.5051), {"wartosc": 0.5, "se": 0.01, "n": 100}, False),
    (wiersz(0.4949), {"wartosc": 0.5, "se": 0.01, "n": 100}, False),   # znak bez znaczenia
    (wiersz(0.5, n=99), {"wartosc": 0.5, "se": 0.01, "n": 100}, False),
    (wiersz(0.9875, skala=100.0), {"wartosc": 98.74, "se": 0.19, "n": 100}, True),  # MultiBLiMP w %
    (wiersz(0.5), {"wartosc": 0.5, "se": 0.0, "n": 100}, False),
])
def test_kontrola_narzedzia(przeliczone, manifest, zgodna):
    assert L.kontrola(przeliczone, manifest)["zgodna"] is zgodna


def test_kontrola_roznica_w_skali_ulamka():
    k = L.kontrola(wiersz(0.99, skala=100.0), {"wartosc": 98.0, "se": 0.5, "n": 100})
    assert k["roznica"] == pytest.approx(0.01) and k["w_se"] == pytest.approx(2.0)


@pytest.mark.parametrize("roznica,wyzej,werdykt,zgodna,oczekiwane", [
    (0.02, True, "pewne", True, ("lepszy (pewne)", "lepiej")),
    (-0.02, True, "prawdopodobne", True, ("gorszy (prawdopodobne)", "gorzej")),
    (-0.02, False, "pewne", True, ("lepszy (pewne)", "lepiej")),       # perpleksja: niżej = lepiej
    (0.02, False, "pewne", True, ("gorszy (pewne)", "gorzej")),
    (0.02, True, "szum", True, ("szum", None)),
    (0.02, True, "pewne", False, (L.NIEROZSTRZYGNIETE_KONTROLA, None)),
])
def test_wynik_koncowy(roznica, wyzej, werdykt, zgodna, oczekiwane):
    p = {"roznica": roznica, "werdykt_holm": werdykt, "p": 0.001}
    assert L.wynik_koncowy(p, wyzej, zgodna) == oczekiwane


def test_wiersz_bez_p_jest_nierozstrzygalny_a_nie_szumem():
    assert L.wynik_koncowy({"roznica": 0.0, "werdykt_holm": "nierozstrzygalne", "p": None}, True, True)[0] == S.NIEROZSTRZYGALNE


def test_ponad_trzy_niezgodne_kontrole_unieważniaja_calosc():
    t = lambda i, ok: {"nazwa": f"T{i}", "kierunek": None, "werdykt_koncowy": "szum", "kontrola": {"zgodna": ok}}
    assert not L.podsumuj([t(i, i >= 3) for i in range(15)])["caly_wynik_nierozstrzygniety"]
    s = L.podsumuj([t(i, i >= 4) for i in range(15)])
    assert s["caly_wynik_nierozstrzygniety"] and "Cały wynik nierozstrzygnięty" in s["twierdzenie"]


def probka(doc_id, lls, gold, ctx="Q:"):
    konty = [" a", " bb", " ccc", " dddd"][: len(lls)]
    return {"doc_id": doc_id, "doc": {}, "target": gold, "arguments": [[ctx, c] for c in konty],
            "filtered_resps": [[ll, False] for ll in lls], "metrics": ["acc", "acc_norm"]}


def zapisz(eksport, model, rek):
    d = eksport / "wyniki" / "arc-easy" / model / "probki"
    d.mkdir(parents=True)
    (d / "T51_space.jsonl").write_text("\n".join(json.dumps(r) for r in rek), encoding="utf-8")


def test_porownanie_parowane_na_atrapie():
    """6 pytań, A trafia 5, B 3, różnice d = [1,1,0,0,0,0]: Δ = 1/3, SE = s(d)/√n."""
    e = Path(tempfile.mkdtemp())
    gold = [0, 1, 2, 3, 0, 1]
    dobre = lambda g: [-1.0 if i == g else -5.0 for i in range(4)]
    zle = lambda g: [-1.0 if i == (g + 1) % 4 else -5.0 for i in range(4)]
    a = [probka(i, dobre(g) if i != 5 else zle(g), g) for i, g in enumerate(gold)]
    b = [probka(i, zle(g) if i in (0, 1, 5) else dobre(g), g) for i, g in enumerate(gold)]
    zapisz(e, L.A, a)
    zapisz(e, L.B, b)
    w = lambda m, v: {"benchmark": "arc-easy", "zadanie": "T51", "model": m, "metryka": "acc", "wartosc": v}
    r = R.porownaj(R.Oceny(), e, w(L.A, 5 / 6), w(L.B, 3 / 6))
    d = [1, 1, 0, 0, 0, 0]
    m = sum(d) / 6
    se = math.sqrt(sum((x - m) ** 2 for x in d) / 5 / 6)
    assert r["roznica_srednia"] == pytest.approx(1 / 3) and r["se"] == pytest.approx(se)
    assert r["z"] == pytest.approx(m / se) and r["metoda"] == "A parowane"


def wynik(model, bench="piqa"):
    return {"benchmark": bench, "zadanie": "T06", "model": model, "repo": "x", "rewizja": "y", "dtype": "float32",
            "env": "lock", "n": 10, "katalog": "k", "s": 1, "gpu": "g", "lm_eval": "0.4.9.1", "metryka": "acc_norm",
            "metryka_raw": "acc_norm,none", "wartosc": 0.6, "se": 0.01, "lo": 0.58, "hi": 0.62, "chance": 0.5,
            "majority": 0.5, "wyzej_lepiej": True, "skala_w_pliku": 1.0, "max_length": 4096, "contamination": None,
            "pmi": None, "wobec_b": None}


def test_checkpoint_w_toku_nie_jest_wersja_ani_wierszem_codesota():
    assert R.w_toku(L.A) and not R.w_toku("slayer1b-1.08")
    assert R.nazwa(L.A) == "Slayer 1B 1.09, krok 40 000 (w toku)"
    assert R.W_TOKU[L.A][1] == "1.09, krok 40 000 (~61 mld), trening w toku, wynik wstępny"
    cards = {"piqa": {"state": "control", "verdict": "spełniony"}}
    rows = [wynik(L.A), wynik("slayer1b-1.07")]
    w = R.flag_row({"uwagi": []}, rows[0], rows, {}, cards, {"piqa": "mc"})
    assert w["w_tabeli_codesota"] is False and w["uwagi"][0] == R.W_TOKU[L.A][1]
    assert R.flag_row({"uwagi": []}, rows[1], rows, {}, cards, {"piqa": "mc"})["w_tabeli_codesota"] is True
    # notatka „w toku” nie mnoży się przy ponownym przebiegu generatora
    assert R.flag_row(w, rows[0], rows, {}, cards, {"piqa": "mc"})["uwagi"].count(R.W_TOKU[L.A][1]) == 1


def test_progresja_wersji_pomija_checkpoint_w_toku(monkeypatch):
    pary = []
    monkeypatch.setattr(R, "porownaj", lambda o, p, a, b: pary.append((a["model"], b["model"])) or None)
    monkeypatch.setattr(R, "Oceny", lambda: None)
    R.progresja([wynik(m) for m in ("slayer1b-1.07", "slayer1b-1.08", L.A)], Path("."))
    assert pary and all(L.A not in p for p in pary)


def test_etykieta_porownania_w_toku():
    t = {"higher": True}
    x = {"kontrola": {"zgodna": True}, "porownanie": {"roznica": 0.01, "werdykt_holm": "pewne"}}
    assert R.toku_label(x, t) == "▲ pewna poprawa"
    assert R.toku_label({**x, "kontrola": {"zgodna": False}}, t) == "nierozstrzygnięte (kontrola narzędzia)"
    assert R.toku_label({**x, "porownanie": {"roznica": 0.01, "werdykt_holm": "szum"}}, t) == "≈ szum"
    assert R.toku_label(None, t) == "–"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
