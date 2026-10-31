"""Czyste funkcje i ścieżka danych testów danych Slayera.

Uruchom: python tests/test_testy_danych_slayer.py  (kod wyjścia 0 = wszystko przeszło; albo pytest)
Test fikstury odpala dane_ramion.py w podprocesie na plikach parquet z katalogu tymczasowego, bez sieci.
"""
import json
import math
import multiprocessing as mp
import os
import random
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np

KAT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KAT / "slayer-1b" / "testy_danych_slayer"))
sys.path.insert(0, str(KAT / "wspolne"))
import dane_ramion as D  # noqa: E402
import heldout_bpb as HB  # noqa: E402
import porownaj_ramion as P  # noqa: E402

TOKENIZER = KAT / "slayer-1b" / "tokenizer" / "tokenizer.json"
SL = ("dom kot pies rzeka góra miasto szkoła nauka prawo sąd ustawa artykuł rozdział wiedza fizyka chemia "
      "historia król wojna pokój zdrowie lekarz szpital droga samochód").split()
EN = "the of energy cell water plant force mass number equation proof theorem river".split()
PYTANIE = ("which factor will most likely cause a person to develop a fever when the bacterial population "
           "in the bloodstream grows quickly")


# ---------------------------------------------------------------- skład i sklejanie

def test_sklady_ramion_sumuja_sie_do_jedynki_i_E25_zachowuje_proporcje_PL():
    for r, s in D.RAMIONA.items():
        assert math.isclose(sum(s.values()), 1.0), r
    c, e = D.RAMIONA["C"], D.RAMIONA["E25"]
    assert math.isclose(e["en"], 0.25)
    assert math.isclose(e["web_hplt"] / e["core"], c["web_hplt"] / c["core"])
    assert set(D.RAMIONA["PLHQ"]) - set(c) == {"web_hq"} and D.RAMIONA["PLHQ"]["web_hq"] == c["web_hplt"]
    assert D.RAMIONA["C2"] == c and D.KOLEJNOSC["C2"] != D.KOLEJNOSC["C"] == D.KOLEJNOSC["E25"] == D.KOLEJNOSC["PLHQ"]


def test_cele_plikow_dziela_komponent_wg_rozmiaru():
    assert D.cele_plikow({"core": 0.5}, {"core": {"a": 1, "b": 3}}, 1000) == {"a": 125.0, "b": 375.0}


def test_prefiks_najkrotszy_o_sumie_co_najmniej_cel_i_zagniezdzony():
    pula = [np.ones(n, dtype=np.uint16) for n in (5, 5, 5, 5)]
    d1, s1 = D.prefiks(pula, 7)
    d2, s2 = D.prefiks(pula, 12)
    assert (len(d1), s1) == (2, 10) and (len(d2), s2) == (3, 15)
    assert all(a is b for a, b in zip(d1, d2))


def test_sklej_ramie_kolejnosc_zalezy_tylko_od_tresci_i_seeda():
    docs = [np.array([0, i, i + 1], dtype=np.uint16) for i in range(1, 30)]
    a = D.sklej_ramie(docs, 60, "s|k1")
    b = D.sklej_ramie(list(reversed(docs)), 60, "s|k1")  # odwrócone wejście: ta sama kolejność
    assert len(a) == 60 and np.array_equal(a, b)
    assert not np.array_equal(a, D.sklej_ramie(docs, 60, "s|k2"))
    # Dokumenty wspólne dwóch ramion stoją w tym samym porządku względnym.
    pod = docs[::2]
    pelne = D.sklej_ramie(docs, 3 * len(docs), "s|k1")
    czesc = D.sklej_ramie(pod, 3 * len(pod), "s|k1")
    kol = [tuple(pelne[i:i + 3]) for i in range(0, len(pelne), 3)]
    assert [x for x in kol if x in {tuple(d) for d in pod}] == [tuple(czesc[i:i + 3]) for i in range(0, len(czesc), 3)]


def test_sklej_ramie_za_malo_tokenow_to_stop():
    try:
        D.sklej_ramie([np.ones(3, dtype=np.uint16)], 10, "x")
    except SystemExit as e:
        assert "STOP" in str(e)
    else:
        raise AssertionError("brak STOP")


def test_procesy_domyslne_dodatnie():
    assert D.procesy_domyslne() >= 1


# ---------------------------------------------------------------- dekontaminacja i dedup

def test_dekontaminacja_lapie_13_gram_niezaleznie_od_wielkosci_liter():
    D.EVAL_NGRAMY.clear()
    D.EVAL_NGRAMY.update(D.ngram_hashe(PYTANIE))
    try:
        assert not D.czy_czysty("Wstęp. " + PYTANIE.upper() + " koniec")
        assert D.czy_czysty(" ".join(PYTANIE.split()[:12]))
    finally:
        D.EVAL_NGRAMY.clear()


def test_udzial_duplikatu_i_krotki_szkic():
    idx = np.array(sorted([3, 7, 11, 20]), dtype=np.int64)
    assert D.udzial_duplikatu([3, 7, 99, 100], idx) == 0.5
    assert D.udzial_duplikatu([3, 7], idx) is None
    assert D.udzial_duplikatu([1, 2, 30, 40], np.zeros(0, dtype=np.int64)) == 0.0
    assert D.udzial_duplikatu([100, 200, 300, 400], idx) == 0.0


def test_szkic_tego_samego_tekstu_jest_ten_sam_i_podzbiorem_ngramow():
    t = " ".join(f"słowo{i}" for i in range(400))
    s = D.szkic(t)
    assert s == D.szkic(t) and set(s) <= set(D.ngram_hashe(t)) and all(h % D.PROBKA_DEDUP == 0 for h in s)


def _doc(rng, slownik, n):
    return " ".join(rng.choice(slownik) for _ in range(n)) + "."


def test_filtr_hq_rozroznia_duplikat_dekontaminacje_krotki_i_nowy():
    rng = random.Random(3)
    hplt = _doc(rng, SL, 600)
    D.INDEKS_HPLT = np.unique(np.asarray(D.szkic(hplt), dtype=np.int64))
    D.EVAL_NGRAMY.clear()
    D.EVAL_NGRAMY.update(D.ngram_hashe(PYTANIE))
    try:
        assert D._filtr_hq(hplt + " dopisek") == "duplikat_hplt"
        assert D._filtr_hq(_doc(rng, SL, 300) + " " + PYTANIE) == "dekontaminacja"
        assert D._filtr_hq("krótki tekst") == "ok_niesprawdzony"
        assert D._filtr_hq(_doc(rng, SL, 600)) == "ok"
        assert D._filtr("x " + PYTANIE) == "dekontaminacja"
    finally:
        D.EVAL_NGRAMY.clear()
        D.INDEKS_HPLT = None


# ---------------------------------------------------------------- fikstura parquet (zbuduj_pule i main)

def fikstura(baza, rng):
    import pyarrow as pa
    import pyarrow.parquet as pq

    def zapisz(p, teksty, zrodla=None):
        p.parent.mkdir(parents=True, exist_ok=True)
        kol = {"document_id": [f"d{i}" for i in range(len(teksty))], "text": teksty}
        if zrodla:
            kol["source_id"] = zrodla
        pq.write_table(pa.table(kol), p, row_group_size=20)

    S = baza / "slayer-pl-8x3b"
    hplt = {pk: [_doc(rng, SL, rng.randint(150, 400)) for _ in range(200)] for pk in (6, 7)}
    for pk, t in hplt.items():
        zapisz(S / f"pack-{pk:02d}" / "web.parquet", t)
    zapisz(S / "shared" / "core.parquet", [_doc(rng, SL, 200) for _ in range(80)])
    zapisz(S / "shared" / "core_sa.parquet", [_doc(rng, SL, 200) for _ in range(160)])
    zapisz(S / "shared" / "legal.parquet", [_doc(rng, SL, 150) for _ in range(80)])
    zapisz(S / "shared" / "legal_sa.parquet", [_doc(rng, SL, 150) for _ in range(20)])
    zapisz(S / "shared" / "en.parquet", [_doc(rng, EN, 200) for _ in range(300)],
           zrodla=[rng.choice(["fineweb-edu", "finemath"]) for _ in range(300)])
    kopie = [t + " dopisek" for t in hplt[7][:20]] + hplt[6][:20]
    skazone = [_doc(rng, SL, 100) + " " + PYTANIE + " " + _doc(rng, SL, 100) for _ in range(5)]
    hq = kopie + skazone + [_doc(rng, SL, rng.randint(150, 400)) for _ in range(300)]
    rng.shuffle(hq)
    H = baza / "FineWeb2-HQ" / "pol_Latn"
    zapisz(H / "000_00000.parquet", hq[:170])
    zapisz(H / "000_00001.parquet", hq[170:])
    return set(kopie), set(skazone)


def test_zbuduj_pule_deterministyczna_heldout_rozlaczny_i_odfiltrowana():
    from tokenizers import Tokenizer
    with tempfile.TemporaryDirectory() as t:
        baza = Path(t)
        kopie, skazone = fikstura(baza, random.Random(5))
        zr = D.Zrodla(str(baza))
        D.ZR = zr
        tok = Tokenizer.from_file(str(TOKENIZER))
        D.EVAL_NGRAMY.clear()
        D.EVAL_NGRAMY.update(D.ngram_hashe(PYTANIE))
        D.INDEKS_HPLT = np.zeros(0, dtype=np.int64)
        try:
            with mp.get_context("fork").Pool(1) as pool:
                D.INDEKS_HPLT, n = D.zbuduj_indeks(zr, [6, 7], pool, cache=None)
            assert n == 400 and len(D.INDEKS_HPLT) > 0
            with mp.get_context("fork").Pool(1) as pool:
                f = zr.sciezka(D.HQ_REPO, "pol_Latn/000_00000.parquet")
                p1, h1, s1, _ = D.zbuduj_pule(zr, f, "web_hq", 1e9, 3000, tok, pool, 7)
                p2, h2, s2, _ = D.zbuduj_pule(zr, f, "web_hq", 1e9, 3000, tok, pool, 7)
        finally:
            D.EVAL_NGRAMY.clear()
        assert [x.tobytes() for x in p1] == [x.tobytes() for x in p2]  # deterministyczna dla (seed, plik)
        pula = {x.tobytes() for x in p1}
        held = {x.tobytes() for _, x in h1}
        assert held and not (pula & held)  # heldout rozłączny z pulą
        assert s1["filtr"].get("duplikat_hplt", 0) > 0
        teksty = {tok.decode(list(np.frombuffer(b, dtype=np.uint16)[1:])) for b in pula | held}
        assert not (teksty & skazone), "dokument z pytaniem testu przeszedł dekontaminację"
        assert len(teksty & kopie) <= s1["filtr"].get("ok_niesprawdzony", 0)


def _docs(p, odetnij_ostatni):
    a = np.fromfile(p, dtype=np.uint16)
    cut = np.flatnonzero(a == 0)
    out = [a[s:e].tobytes() for s, e in zip(cut, list(cut[1:]) + [len(a)])]
    return set(out[:-1] if odetnij_ostatni else out)


def test_main_na_fiksturze_ramiona_rowne_heldout_rozlaczny_wspolne_dokumenty():
    with tempfile.TemporaryDirectory() as t:
        baza = Path(t)
        fikstura(baza / "zr", random.Random(9))
        (baza / "ewal.json").write_text(json.dumps({"test": [PYTANIE]}))
        wyj = baza / "wyj"
        r = subprocess.run([sys.executable, str(KAT / "slayer-1b" / "testy_danych_slayer" / "dane_ramion.py"),
                            "--tokenizer", str(TOKENIZER), "--wyjscie", str(wyj), "--lokalne", str(baza / "zr"),
                            "--tokeny_train", "6e4", "--skala_heldout", "0.003", "--dedup_packi", "6,7",
                            "--hq_pliki", "2", "--procesy", "2", "--ewal_teksty", str(baza / "ewal.json")],
                           capture_output=True, text=True, env={**os.environ, "HF_HUB_OFFLINE": "1"})
        assert r.returncode == 0, r.stderr[-2000:]
        s = json.loads((wyj / "statystyki.json").read_text())
        assert {v["tokeny_train"] for v in s["ramiona"].values()} == {60000}
        tr = {x: _docs(wyj / x / "train.bin", True) for x in ("C", "C2", "E25", "PLHQ")}
        H = _docs(wyj / "heldout" / "val.bin", False)
        assert all(not (H & v) for v in tr.values()), "heldout przecina train"
        assert tr["C"] & tr["PLHQ"] and tr["C"] & tr["E25"]
        a, b = (np.fromfile(wyj / x / "train.bin", dtype=np.uint16) for x in ("C", "C2"))
        assert not np.array_equal(a, b)  # C2: te same dokumenty, inna kolejność
        assert sum(x["filtr"].get("duplikat_hplt", 0) for x in s["pliki"].values()) > 0
        assert set(s["en_komponenty"]) <= {"en:fineweb-edu", "en:finemath"} and s["en_komponenty"]


# ---------------------------------------------------------------- heldout BPB

def test_tablica_bajtow_zgodna_z_utf8_dla_tokenizera_bytelevel():
    from tokenizers import Tokenizer
    tok = Tokenizer.from_file(str(TOKENIZER))
    tab = HB.bajty_tokenow(tok)
    assert tab[0] == 0
    assert HB.sprawdz_bajty(tok, tab, ["Zażółć gęślą jaźń.", "x € ąę\n\n  y", "Mathematics 2+2=4"]) == []


def test_okna_nie_przechodza_przez_koniec_komponentu():
    assert HB.okna_komponentu(0, 10, 4) == [0, 4] and HB.okna_komponentu(100, 104, 4) == []


# ---------------------------------------------------------------- porównanie i werdykty

def test_bpb_agregatu_punkt_i_bootstrap():
    okna = {"a": (np.array([math.log(2) * 10, math.log(2) * 10]), np.array([10.0, 10.0])),
            "b": (np.array([math.log(2) * 30]), np.array([10.0]))}
    assert math.isclose(P.bpb_agregatu(okna, {"a": 1.0}), 1.0)
    assert math.isclose(P.bpb_agregatu(okna, {"a": 1, "b": 1}), 2.0)
    idx = {"a": np.array([[0, 0], [1, 1]]), "b": np.array([[0], [0]])}
    assert np.allclose(P.bpb_agregatu(okna, {"a": 1, "b": 1}, idx), [2.0, 2.0])


def test_wagi_en_nie_zaleza_od_kolejnosci_wejscia():
    w1 = P.wagi_en({"core": 5, "en:finemath": 1, "en:fineweb-edu": 3})
    w2 = P.wagi_en({"en:fineweb-edu": 3, "en:finemath": 1, "core": 5})
    assert w1 == w2 and math.isclose(w1["en:fineweb-edu"], 0.75)
    assert P.wagi_en({"en:brak": 4}) == {"en:brak": 1.0}  # en.parquet bez source_id: jeden komponent


def test_werdykt_loss_wymaga_2SE_i_progu_szumu_lub_1_procent():
    assert P.werdykt_loss(-0.02, 0.005, 0.001, 1.0) == "spadek"
    assert P.werdykt_loss(-0.02, 0.011, 0.001, 1.0) == "nierozstrzygnięte"
    assert P.werdykt_loss(-0.02, 0.001, 0.01, 1.0) == "nierozstrzygnięte"
    assert P.werdykt_loss(-0.005, 0.001, 0.0, 1.0) == "nierozstrzygnięte"
    assert P.werdykt_loss(0.03, 0.005, 0.001, 1.0) == "wzrost"


def test_ruch_bpb_nizej_lepiej_i_szum_kolejnosci():
    assert P.ruch(-0.05, 0.01, lepiej_nizej=True) == 1
    assert P.ruch(-0.05, 0.01, szum=0.03, lepiej_nizej=True) == 0  # w 2·Zk
    assert P.ruch(0.05, 0.01, lepiej_nizej=True) == -1 and P.ruch(0.02, 0.01) == 0


def test_koszt_pl_wymaga_gornej_granicy_CI_ponizej_tolerancji():
    assert P.koszt_pl(0.005, 1.0, "nierozstrzygnięte", {"b": 0}) == "brak"
    assert P.koszt_pl(0.02, 1.0, "nierozstrzygnięte", {"b": 0}) == "nierozstrzygnięty"  # brak wykrycia to nie brak kosztu
    assert P.koszt_pl(0.005, 1.0, "wzrost", {"b": 0}) == "jest"
    assert P.koszt_pl(0.005, 1.0, "nierozstrzygnięte", {"b": -1}) == "jest"


def test_werdykty_testow():
    assert P.werdykt_test1("spadek", {"a": 1, "b": 1, "c": 0}, "brak") == "EN pomaga bez kosztu PL"
    assert P.werdykt_test1("spadek", {"a": 1, "b": 0, "c": 0}, "brak") == "nierozstrzygnięte"  # 1 z 3 to za mało
    assert P.werdykt_test1("nierozstrzygnięte", {"a": 1, "b": 1}, "brak") == "nierozstrzygnięte"
    assert P.werdykt_test1("spadek", {"a": 1, "b": 1}, "nierozstrzygnięty") == "EN pomaga, koszt PL nierozstrzygnięty"
    assert P.werdykt_test1("spadek", {"a": 1, "b": 1}, "jest") == "EN pomaga kosztem PL"
    assert P.werdykt_test1("spadek", {"a": 1, "b": -1}, "brak") == "EN szkodzi EN"
    assert P.werdykt_test1("nierozstrzygnięte", {"a": 0}, "jest") == "szkodzi PL bez zysku EN"
    assert P.werdykt_test2("spadek", {"p": 1}) == "PL-HQ pomaga (loss i testy)"
    assert P.werdykt_test2("spadek", {"p": 0}) == "PL-HQ obniża loss PL"
    assert P.werdykt_test2("spadek", {"p": -1}) == "nierozstrzygnięte"
    assert P.werdykt_test2("nierozstrzygnięte", {"p": -1}) == "PL-HQ szkodzi"


def test_szuflada_potwierdza_tylko_ruchem_w_kierunku_werdyktu():
    k = P.kierunki("EN pomaga bez kosztu PL", "PL-HQ szkodzi")
    assert k[("test1", "EN")] == 1 and k[("test1", "PL")] == 0 and k[("test2", "PL")] == -1
    assert P.status_szuflady(1, {"a": 0, "b": 0}, 2) == "niepotwierdzony (szuflada w szumie)"
    assert P.status_szuflady(1, {"a": 1, "b": 0}, 2) == "potwierdzony"
    assert P.status_szuflady(1, {"a": 1, "b": -1}, 2) == "sprzeczny"
    assert P.status_szuflady(-1, {"a": -1, "b": 0}, 2) == "potwierdzony"  # „szkodzi” też sprawdzane
    assert P.status_szuflady(-1, {"a": 1, "b": 0}, 2) == "sprzeczny"
    assert P.status_szuflady(0, {"a": -1}, 1) == "sprzeczny"
    assert P.status_szuflady(None, {}, 2) == "nie dotyczy"
    assert P.status_szuflady(1, {"a": 1}, 2).startswith("brak danych")


def test_prompty_szuflady_i_5shot():
    import ewal_ramion as E
    dev = [{"grupa": "x", "pytanie": f"q{i}", "opcje": ["a", "b"], "gold": i % 2} for i in range(7)]
    test = [{"grupa": "x", "pytanie": "Q?", "opcje": ["tak", "nie"], "gold": 0}]
    d = E.z_5shot(test, dev, lambda s: f"H {s}\n\n", "Pytanie", "Odpowiedź")[0]
    ctx, konty = E.prompt_gmmlu_pl_5shot(d)
    assert ctx.count("Pytanie:") == 6 and ctx.endswith("Pytanie: Q?\nOdpowiedź:") and konty == [" tak", " nie"]
    assert "q5" not in ctx and "Odpowiedź: b" in ctx
    assert E.hellaswag_tekst("A man [title] runs [header]  fast ") == "A man. runs  fast"  # jak lm-eval


if __name__ == "__main__":
    bledy = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try:
                f()
                print("ok", n)
            except Exception:  # noqa: BLE001
                bledy += 1
                print("FAIL", n)
                traceback.print_exc()
    print(f"{'FAIL' if bledy else 'PASS'}: {bledy} błędów")
    sys.exit(1 if bledy else 0)
