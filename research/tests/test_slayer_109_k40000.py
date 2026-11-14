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


# --------------------------------------------------------------------------- dolacz_wyniki.py na atrapie

import gzip  # noqa: E402
import hashlib  # noqa: E402

import dolacz_wyniki as DW  # noqa: E402

PLIKI_PARY = {"results.json": b'{"r": 1}\n', "results_rozszerzone.json": b'{"r": 2}\n', "scores-history-wiersz.csv": b"a,b\n",
              "podsumowanie.md": "# wynik 0,5\n".encode(), "probki/T06_space.jsonl": b'{"doc_id": 0}\n{"doc_id": 1}\n',
              "trace/T06_space.jsonl": b'{"t": 0}\n'}


def atrapa_eksportu(tmp, bench="piqa"):
    """Eksport z dwiema parami (1.09 k40000 i 1.08) i katalog przebiegu z jednym starym wierszem; sumy jak zrob_sha.py."""
    eksport, cel = tmp / "eksport", tmp / "przebieg"
    manifest, sumy = [], {}
    for model in (DW.A, DW.B):
        kat = f"wyniki/{bench}/{model}"
        pliki = {}
        for wzgl, dane in PLIKI_PARY.items():
            dane = dane + model.encode()  # różne bajty obu etykiet
            p = eksport / kat / wzgl
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(dane)
            pliki[wzgl] = sumy[f"{kat}/{wzgl}"] = hashlib.sha256(dane).hexdigest()
        manifest.append({"benchmark": bench, "model": model, "katalog": kat, "pliki": pliki})
    (eksport / "manifest.jsonl").write_text("".join(json.dumps(w) + "\n" for w in manifest), encoding="utf-8")
    (eksport / "srodowisko.json").write_text('{"gpu": "x"}', encoding="utf-8")
    (eksport / "czasy.jsonl").write_text("".join(json.dumps({"etap": "ewaluacja", "model": m}) + "\n"
                                                 for m in (DW.A, DW.B)), encoding="utf-8")
    (eksport / "logi").mkdir()
    (eksport / "logi" / "para.log").write_bytes(b"log\n")
    (cel / DW.KATALOG).mkdir(parents=True)
    (cel / "manifest.jsonl").write_text(json.dumps({"benchmark": bench, "model": DW.B}) + "\n", encoding="utf-8")
    (cel / "czasy.jsonl").write_text(json.dumps({"etap": "pobieranie", "model": DW.B}) + "\n", encoding="utf-8")
    (cel / DW.KATALOG / "probki_sha256.json").write_text(json.dumps({"paczka": {"sha256": "p"}, "pliki": sumy}),
                                                         encoding="utf-8")
    return eksport, cel


def test_dolacz_i_odtworz_daja_te_same_bajty(tmp_path):
    eksport, cel = atrapa_eksportu(tmp_path)
    DW.dolacz(eksport, cel)
    a = cel / "piqa" / DW.A
    assert (a / "results.json").read_bytes() == (eksport / "wyniki/piqa" / DW.A / "results.json").read_bytes()
    assert not (a / "probki" / "T06_space.jsonl").exists() and (a / "probki" / "T06_space.jsonl.gz").exists()
    assert (cel / DW.KATALOG / "wyniki" / "piqa" / DW.B / "probki" / "T06_space.jsonl.gz").exists()
    assert not (cel / "piqa" / DW.B).exists()  # 1.08 przebiegu nietknięte, przeliczone tylko w katalogu pomiaru
    # manifest i czasy przebiegu: stare wiersze bez zmian, dopisane tylko wiersze 1.09
    m = [json.loads(x) for x in (cel / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [w["model"] for w in m] == [DW.B, DW.A]
    c = [json.loads(x) for x in (cel / "czasy.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [w["model"] for w in c] == [DW.B, DW.A] and c[0]["etap"] == "pobieranie"
    sumy = json.loads((cel / DW.KATALOG / "probki_sha256.json").read_text(encoding="utf-8"))
    assert sumy["paczka"] == {"sha256": "p"} and "logi/para.log.gz" in "".join(sumy["pliki_gz"])
    for p, s in sumy["pliki_gz"].items():
        assert hashlib.sha256((cel / p).read_bytes()).hexdigest() == s
    assert DW.odtworz(cel, tmp_path / "odtw") == []
    for p in sumy["pliki"]:
        assert (tmp_path / "odtw" / p).read_bytes() == (eksport / p).read_bytes()
    assert (tmp_path / "odtw" / "manifest.jsonl").read_bytes() == (eksport / "manifest.jsonl").read_bytes()


def test_gzip_deterministyczny():
    assert DW.gz(b"x" * 1000) == DW.gz(b"x" * 1000)
    assert DW.gz(b"abc")[4:8] == b"\0\0\0\0"  # mtime 0 w nagłówku, jak gzip -n
    assert gzip.decompress(DW.gz(b"abc")) == b"abc"


def test_drugie_dolaczenie_odmawia(tmp_path):
    eksport, cel = atrapa_eksportu(tmp_path)
    DW.dolacz(eksport, cel)
    przed = (cel / "manifest.jsonl").read_bytes()
    with pytest.raises(SystemExit):
        DW.dolacz(eksport, cel)
    assert (cel / "manifest.jsonl").read_bytes() == przed
    # same wiersze 1.09 w manifeście (katalog usunięty) też zatrzymują: inaczej wiersze by się zdublowały
    import shutil
    shutil.rmtree(cel / "piqa" / DW.A)
    with pytest.raises(SystemExit):
        DW.dolacz(eksport, cel)
    assert (cel / "manifest.jsonl").read_bytes() == przed


@pytest.mark.parametrize("psuj", ["plik", "nadmiar", "manifest"])
def test_zla_suma_wejscia_zatrzymuje_przed_zapisem(tmp_path, psuj):
    eksport, cel = atrapa_eksportu(tmp_path)
    if psuj == "plik":
        (eksport / "wyniki/piqa" / DW.A / "probki/T06_space.jsonl").write_bytes(b"zmienione\n")
    elif psuj == "nadmiar":
        (eksport / "wyniki/piqa" / DW.A / "probki/T06_inny.jsonl").write_bytes(b"x\n")
    else:
        m = [json.loads(x) for x in (eksport / "manifest.jsonl").read_text(encoding="utf-8").splitlines()]
        m[0]["pliki"]["results.json"] = "0" * 64
        (eksport / "manifest.jsonl").write_text("".join(json.dumps(w) + "\n" for w in m), encoding="utf-8")
    przed = (cel / "manifest.jsonl").read_bytes()
    with pytest.raises(SystemExit):
        DW.dolacz(eksport, cel)
    assert (cel / "manifest.jsonl").read_bytes() == przed and not (cel / "piqa").exists()


def test_odtworz_lapie_zmieniony_plik_w_repo(tmp_path):
    eksport, cel = atrapa_eksportu(tmp_path)
    DW.dolacz(eksport, cel)
    (cel / "piqa" / DW.A / "probki" / "T06_space.jsonl.gz").write_bytes(DW.gz(b'{"doc_id": 9}\n'))
    (cel / DW.KATALOG / "wyniki" / "piqa" / DW.B / "results.json").unlink()
    r = DW.odtworz(cel, tmp_path / "odtw")
    assert len(r) == 2 and any("T06_space" in x for x in r) and any("brak" in x for x in r)


# --------------------------------------------------------------------------- strażnik liczb na RAPORT.md

def liczby_atrapa():
    """Najmniejszy LICZBY.json w kształcie liczby_109.zbuduj: dwa testy, jeden lepszy pewnie, jeden w szumie."""
    def test(bench, nazwa, v108, v109, roznica, z, werdykt, holm):
        p = {"n": 1000, "roznica": roznica, "roznica_srednia": roznica, "roznica_bpb": None, "se": 0.0052, "z": z,
             "t": None, "df": None, "k": None, "p": 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2)))),
             "werdykt": werdykt}
        t = {"benchmark": bench, "nazwa": nazwa, "metryka": "acc", "wyzej_lepiej": True, "chance": 0.25,
             "majority": None, "v108_manifest": {"wartosc": v108, "se": 0.0123, "n": 1000},
             "v108_przeliczone": {"wartosc": v108 + 0.0004, "se": 0.0123, "n": 1000},
             "v109": {"wartosc": v109, "se": 0.0119, "n": 1000},
             "kontrola": L.kontrola({"wartosc": v108 + 0.0004, "n": 1000, "skala_w_pliku": 1.0},
                                    {"wartosc": v108, "se": 0.0123, "n": 1000}),
             "porownanie": p, "kontrola_sensu": {L.A: [], L.B: []}}
        return t
    testy = [test("arc-easy", "ARC-Easy", 0.5838, 0.6131, 0.0293, 5.63, "pewne", "pewne"),
             test("piqa", "PIQA", 0.6812, 0.6845, 0.0033, 0.64, "szum", "szum")]
    for t, h in zip(testy, S.po_holmie([t["porownanie"]["p"] for t in testy], m=2)):
        t["porownanie"].update(h)
        t["werdykt_koncowy"], t["kierunek"] = L.wynik_koncowy(t["porownanie"], True, t["kontrola"]["zgodna"])
    return {"etykieta": R.W_TOKU[L.A][1], "model": L.A, "odniesienie": L.B, "m_holm": 2, "srodowisko": {},
            "wejscia": {"paczka": {"nazwa": "e.tgz", "sha256": "0" * 64}, "probki_sha256": "1" * 64,
                        "manifest_przebiegu": "2" * 64}, "testy": testy, "podsumowanie": L.podsumuj(testy)}


def test_raport_z_liczb_przechodzi_straznik_a_zamieniona_liczba_nie():
    import raport_md
    import sprawdz_raport
    straznik = sprawdz_raport.zaladuj(sprawdz_raport.DOMYSLNY)
    liczby = liczby_atrapa()
    tekst = raport_md.raport(liczby)
    assert sprawdz_raport.sprawdz(straznik, liczby, tekst) == []
    assert "0,6131 ± 0,0119" in tekst
    zle = sprawdz_raport.sprawdz(straznik, liczby, tekst.replace("0,6131 ± 0,0119", "0,6231 ± 0,0119"))
    assert len(zle) == 1 and "0,6231" in zle[0][2]
    # słowo „pewne” przy teście, którego dane mają tylko szum, łapie reguła (c)
    zle = sprawdz_raport.sprawdz(straznik, liczby, tekst + "\nPIQA: różnica pewna.\n")
    assert any("(c)" in b[2] for b in zle)


# --------------------------------------------------------------------------- dane rzeczywiste z repo

POMIAR = KOD.parent
PRZEBIEG = POMIAR.parent


@pytest.mark.skipif(not (POMIAR / "LICZBY.json").exists(), reason="pomiar jeszcze bez LICZBY.json")
@pytest.mark.parametrize("bench", ["pubmedqa", "wsc273", "multiblimp-pl"])
def test_dane_rzeczywiste_z_repo_daja_liczby_z_LICZBY(tmp_path, bench):
    """Pliki gzip z repo → układ eksportu (sha256 zgodne), porównanie parowane i kontrola narzędzia jak w LICZBY.json."""
    assert DW.odtworz(PRZEBIEG, tmp_path, testy={bench}) == []
    LZ = {t["benchmark"]: t for t in json.loads((POMIAR / "LICZBY.json").read_text(encoding="utf-8"))["testy"]}[bench]
    wyniki = {(w["benchmark"], w["model"]): w for w in R.wczytaj_wyniki(tmp_path) if w["benchmark"] == bench}
    a, b = wyniki[(bench, L.A)], wyniki[(bench, L.B)]
    p = R.porownaj(R.Oceny(), tmp_path, a, b)
    assert p["roznica"] == pytest.approx(LZ["porownanie"]["roznica"], abs=1e-12)
    assert p["se"] == pytest.approx(LZ["porownanie"]["se"], rel=1e-12)
    assert b["wartosc"] == pytest.approx(LZ["v108_przeliczone"]["wartosc"], abs=1e-12)
    man = {"wartosc": LZ["v108_manifest"]["wartosc"] * b["skala_w_pliku"], "se": LZ["v108_manifest"]["se"] * b["skala_w_pliku"],
           "n": LZ["v108_manifest"]["n"]}
    assert L.kontrola(b, man)["zgodna"] is LZ["kontrola"]["zgodna"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
