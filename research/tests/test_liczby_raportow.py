"""Liczby raportów (narzedzia/liczby.py) i ich strażnik (narzedzia/sprawdz_raporty.py).
Uruchom: python tests/test_liczby_raportow.py (albo pytest). Bez sieci; czyta surowe JSON-y z repo."""
import inspect
import math
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "narzedzia"))
import liczby as L  # noqa: E402
import sprawdz_raporty as S  # noqa: E402

_LICZBY = None


def dane():
    global _LICZBY
    if _LICZBY is None:
        _LICZBY = L.zbuduj(KORZEN)
    return _LICZBY, S.zbiory(_LICZBY)


def bledy(tekst, plik="lab/x.md"):
    liczby, zb = dane()
    return S.sprawdz_tekst(plik, tekst.splitlines(), liczby, zb)


def test_parsuje_polska_liczbe_z_minusem_typograficznym():
    assert S.parsuj_liczbe("−0,047") == (-0.047, 3)
    assert S.parsuj_liczbe("-0,047") == (-0.047, 3)
    assert S.parsuj_liczbe("2,2807") == (2.2807, 4)


def test_dopasowanie_po_zaokragleniu_do_cyfr_tekstu():
    assert S.pasuje(0.218, 3, 0.2175767918)
    assert not S.pasuje(0.217, 3, 0.2175767918)
    assert S.pasuje(-0.047, 3, -0.046953911)          # znak i moduł
    assert S.pasuje(0.047, 3, -0.046953911)           # „spadek o 0,047”


def test_werdykt_z_progow():
    assert L.werdykt(3.0) == "pewne" and L.werdykt(-4.2) == "pewne"
    assert L.werdykt(2.0) == "prawdopodobne" and L.werdykt(-2.99) == "prawdopodobne"
    assert L.werdykt(1.99) == "szum" and L.werdykt(None) is None


def test_se_niezalezne_to_hypot():
    assert math.isclose(L.se_niezalezne(0.03, 0.04), 0.05)


def test_ocena_bez_se_wykryta_a_z_se_przepuszczona():
    assert S.ocena_bez_dowodu("ARC-E −4,4 pkt gorszy od Pythii.")
    assert not S.ocena_bez_dowodu("ARC-E −4,4 pkt (3,0 SE) to prawdopodobna luka.")
    assert not S.ocena_bez_dowodu("SIQA −0,9 pkt, czyli szum.")
    assert not S.ocena_bez_dowodu("Odpowiedź poprawna to „A”.")   # „poprawna” to nie „poprawa”


def test_regresja_zdanie_wytkniete_przez_arka_odrzucone():
    stare = "- Po angielsku 1–4 pkt gorszy (ARC-E, MMLU, SIQA po treści). To są prawdziwe luki."
    b = bledy(stare)
    assert any("(b)" in p and "gorszy" in p for _, _, p in b), b
    assert any("(b)" in p and "prawdziwe luki" in p for _, _, p in b), b


def test_za_mocny_werdykt_przy_tescie_z_szumem():
    # SIQA i Belebele vs Pythia: w każdej metryce |z| < 3, więc „pewna” jest za mocne
    b = bledy("| 8 | SIQA vs Pythia-1B | −0,9 pkt | 0,6 SE | pewna luka |")
    assert any("(c)" in p and "siqa" in p for _, _, p in b), b
    assert not [p for _, _, p in bledy("| 7 | MultiBLiMP vs Pythia-1B | 28 SE | pewna różnica |") if "(c)" in p]


def test_liczba_z_se_i_pkt_sprawdzana_w_swojej_skali():
    liczby, zb = dane()
    assert S.niepasujace_liczby("SIQA −0,9 pkt (0,6 SE)", zb, liczby["aliasy"]) == []
    assert S.niepasujace_liczby("SIQA −4,9 pkt", zb, liczby["aliasy"]) == [("−4,9", "skalowana")]
    assert S.niepasujace_liczby("SIQA 5,1 SE", zb, liczby["aliasy"]) == [("5,1", "z")]
    assert S.niepasujace_liczby("koszt 0,85 $/h, `0,999`", zb, liczby["aliasy"]) == []


def test_wyjatek_w_linii_wylacza_regule():
    assert not bledy("Wynik 0,777 z innego źródła. <!-- liczba-spoza-wynikow: przykład -->")
    assert bledy("Wynik 0,777 z innego źródła.")


def _wartosc_tylko_blimp(liczby):
    """A BLiMP value (4 digits) that no non-BLiMP value of LICZBY.json rounds to."""
    inne = S.Zbior([v for k, v in liczby["wartosci"].items() if S.test_sciezki(k, liczby["aliasy"]) != "blimp"] +
                   [p[k] for p in liczby["porownania"] if p["test"] != "blimp"
                    for k in ("wartosc_a", "wartosc_b", "se_a", "se_b", "roznica", "se_niezalezne", "se_parowane")
                    if p.get(k) is not None])
    for p in liczby["porownania"]:
        if p["test"] == "blimp" and not inne.zawiera(p["wartosc_a"], 4):
            return f"{p['wartosc_a']:.4f}".replace(".", ",")
    raise AssertionError("no BLiMP-only value: BLiMP numbers are missing from LICZBY.json")


def test_liczby_blimp_tylko_w_linii_z_nazwa():
    liczby, zb = dane()
    tekst = _wartosc_tylko_blimp(liczby)
    assert not S.niepasujace_liczby(f"BLiMP: {tekst}", zb, liczby["aliasy"])
    assert S.niepasujace_liczby(f"Wynik {tekst}", zb, liczby["aliasy"])  # catch-all set has no BLiMP values


def test_multiblimp_nie_jest_blimp():
    liczby, zb = dane()
    assert S.testy_w_tekscie("MultiBLiMP-PL: 99,0", liczby["aliasy"]) == {"multiblimp"}
    assert S.testy_w_tekscie("BLiMP i MultiBLiMP", liczby["aliasy"]) == {"blimp", "multiblimp"}
    tekst = _wartosc_tylko_blimp(liczby)
    assert S.niepasujace_liczby(f"MultiBLiMP-PL {tekst}", zb, liczby["aliasy"])


def test_blimp_md_liczby_sprawdzane():
    liczby, zb = dane()
    plik = "benchmarki/blimp/wyniki/BLIMP.md"
    linie = (KORZEN / plik).read_text(encoding="utf-8").splitlines()
    assert S.sprawdz_tekst(plik, linie, liczby, zb) == []
    i = next(i for i, l in enumerate(linie) if l.startswith("**Slayer 1.06:"))
    zepsute = list(linie)
    zepsute[i] = S.LICZBA_EN.sub("0.7777", linie[i].replace("Slayer 1.06", "Slayer"), count=1)
    bl = S.sprawdz_tekst(plik, zepsute, liczby, zb)
    assert bl and "0.7777" in bl[0][2]


def _meta_blimp():
    import copy
    liczby, _ = dane()
    (meta,) = [m for m in liczby["raporty"] if m["plik"] == "benchmarki/blimp/wyniki/BLIMP.md"]
    linie = (KORZEN / meta["plik"]).read_text(encoding="utf-8").splitlines()
    return liczby, copy.deepcopy(meta), linie


def test_bramki_przechodza_na_raporcie_blimp():
    liczby, meta, linie = _meta_blimp()
    assert S.bramki_raportu(meta, linie, liczby) == []
    assert [m["plik"] for m in liczby["raporty"]] == ["benchmarki/blimp/wyniki/BLIMP.md"]  # older reports have no metadata


def test_bramka_d_werdykt_bez_se_klastrowego():
    # today's BLiMP case: z = -18 on pairs with no clustered field -> code 1
    liczby, meta, linie = _meta_blimp()
    meta["porownanie_klastrowe"] = None
    assert any("(d)" in b[2] and "klastrowan" in b[2] for b in S.bramki_raportu(meta, linie, liczby))
    liczby, meta, linie = _meta_blimp()
    del meta["holm"]
    assert any("Holma" in b[2] for b in S.bramki_raportu(meta, linie, liczby))
    liczby, meta, linie = _meta_blimp()
    meta["porownanie_klastrowe"] = None
    bez_werdyktow = [l for l in linie if not S.SLOWO_WERDYKTU.search(l)]
    assert not any("(d)" in b[2] for b in S.bramki_raportu(meta, bez_werdyktow, liczby))  # no verdict, no gate


def test_bramka_e_grupa_ponizej_3():
    liczby, meta, linie = _meta_blimp()
    g = next(g for g in meta["grupy"] if g["nazwa"] == "ellipsis")
    g["werdykt"] = "pewne"  # ellipsis has 2 paradigms
    assert any("(e)" in b[2] for b in S.bramki_raportu(meta, linie, liczby))
    liczby, meta, linie = _meta_blimp()
    zepsute = [l.replace("undetermined (k < 3)", "probable") if l.startswith("| ellipsis |") else l for l in linie]
    assert any("(e)" in b[2] and b[1] > 0 for b in S.bramki_raportu(meta, zepsute, liczby))
    liczby, meta, linie = _meta_blimp()
    zepsute = [l.replace("undetermined (k < 3)", "") if l.startswith("| ellipsis |") else l for l in linie]
    assert any("(e)" in b[2] and b[1] > 0 for b in S.bramki_raportu(meta, zepsute, liczby))  # empty cell


def test_bramka_e_tylko_kolumna_klastrowa():
    # the k < 3 rule binds the paradigm column only: the pair verdict of the same row is legitimate
    liczby, meta, linie = _meta_blimp()
    wiersze = {g["etykieta"]: l for g in meta["grupy"] if g["k"] < 3
               for l in linie if l.startswith(f"| {g['etykieta']} |")}
    assert set(wiersze) == {"anaphor agreement", "ellipsis", "irregular forms"}
    para = {e: S.komorka_kolumny(linie, linie.index(l), "verdict pairs") for e, l in wiersze.items()}
    assert para == {"anaphor agreement": "certain", "ellipsis": "probable", "irregular forms": "certain"}
    assert all(S.komorka_kolumny(linie, linie.index(l), "verdict paradigms") == "undetermined (k < 3)"
               for l in wiersze.values())
    assert S.bramki_raportu(meta, linie, liczby) == []
    # the old gate (any verdict word in the row) would flag these rows
    bez_kolumny = dict(meta, kolumna_werdyktu_klastrowego=None)
    assert any("(e)" in b[2] for b in S.bramki_raportu(bez_kolumny, linie, liczby))
    # a renamed header leaves the gate without its column: reported, not passed
    zly = [l.replace("| verdict paradigms |", "| verdict clusters |") for l in linie]
    assert any("(e)" in b[2] and "bez kolumny" in b[2] for b in S.bramki_raportu(meta, zly, liczby))


def _kopia_do_generatora(tmp_path):
    import shutil
    for rel in ("benchmarki/blimp/blimp_raport.py", "benchmarki/blimp/wyniki/blimp.json", "benchmarki/blimp/wyniki/BLIMP.md",
                "benchmarki/blimp/wyniki/blimp_phenomena.svg", "benchmarki/blimp/wyniki/blimp_paradigms.svg"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(KORZEN / rel, tmp_path / rel)
    return tmp_path


def test_bramka_g_raport_bajt_w_bajt_z_generatora(tmp_path):
    liczby, meta, _ = _meta_blimp()
    assert S.bramka_generatora(meta, liczby) == []  # the committed report is the generator output
    k = _kopia_do_generatora(tmp_path)
    assert S.bramka_generatora(meta, liczby, k) == []
    md = k / "benchmarki/blimp/wyniki/BLIMP.md"
    tekst = md.read_text(encoding="utf-8")
    # a verdict word, a number nobody else checks, a removed sentence, one trailing space
    for stare, nowe in (("t = -3.30, df = 66", "t = -3.30, df = 65"), (": certain;", ": probable;"),
                        ("This is a correlation over paradigm types, not a controlled experiment.", ""),
                        ("# BLiMP full set", "# BLiMP full set ")):
        assert stare in tekst, stare
        md.write_text(tekst.replace(stare, nowe, 1), encoding="utf-8")
        b = S.bramka_generatora(meta, liczby, k)
        assert len(b) == 1 and "(g)" in b[0][2] and b[0][0] == "benchmarki/blimp/wyniki/BLIMP.md" and b[0][1] > 0, (stare, b)
    md.write_text(tekst, encoding="utf-8")
    svg = k / "benchmarki/blimp/wyniki/blimp_paradigms.svg"
    svg.write_text(svg.read_text(encoding="utf-8").replace("#2a78d6", "#2a78d7", 1), encoding="utf-8")
    assert [b[0] for b in S.bramka_generatora(meta, liczby, k)] == ["benchmarki/blimp/wyniki/blimp_paradigms.svg"]
    svg.unlink()
    assert any("brak pliku" in b[2] for b in S.bramka_generatora(meta, liczby, k))


def test_bramka_f_rozne_tokenizery_bez_wyniku_na_token():
    liczby, meta, linie = _meta_blimp()
    meta["porownanie_na_token"] = None
    assert any("(f)" in b[2] for b in S.bramki_raportu(meta, linie, liczby))
    liczby, meta, linie = _meta_blimp()
    bez = [l for l in linie if "per token" not in l.lower() and "per-token" not in l.lower()]
    assert any("(f)" in b[2] for b in S.bramki_raportu(meta, bez, liczby))
    liczby, meta, linie = _meta_blimp()
    meta["tokenizery"] = {"a": "x", "b": "x"}  # same tokenizer: no per-token result needed
    meta["porownanie_na_token"] = None
    assert not any("(f)" in b[2] for b in S.bramki_raportu(meta, linie, liczby))


def test_dokumenty_repo_zgodne_z_liczbami():
    liczby, zb = dane()
    wszystkie = []
    for p in S.pliki_md(KORZEN):
        wszystkie += S.sprawdz_tekst(str(p.relative_to(KORZEN)), p.read_text(encoding="utf-8").splitlines(), liczby, zb)
    assert wszystkie == [], wszystkie


def test_zepsuta_liczba_w_kopii_dokumentu_zlapana():
    plik = "slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md"
    tekst = (KORZEN / plik).read_text(encoding="utf-8")
    assert "Belebele po treści 0,330 vs 0,297" in tekst
    zepsuty = tekst.replace("Belebele po treści 0,330 vs 0,297", "Belebele po treści 0,345 vs 0,297")
    b = bledy(zepsuty, plik)
    assert [p for _, _, p in b if "0,345" in p], b


def test_liczby_benchmarku_sprawdzane_w_jego_plikach_i_nie_wyciekaja():
    # Bielik PL EWoK = 66,0%; tabela EWoK pisze wartości w % bez znaku „%”
    assert not bledy("| Bielik-1.5B-v3 | 66,0 [63,4; 68,5] |", "benchmarki/ewok-pl/WYNIKI.md")
    assert [p for _, _, p in bledy("| Bielik-1.5B-v3 | 66,3 [63,4; 68,5] |", "benchmarki/ewok-pl/WYNIKI.md") if "66,3" in p]
    assert not bledy("Bielik ma na EWoK 66,0%.")
    assert [p for _, _, p in bledy("Bielik ma 63,4%.") if "63,4" in p]


def test_porownanie_parowane_ma_obie_wersje_se():
    liczby, _ = dane()
    p = next(x for x in liczby["porownania"] if x["id"] == "wygaszanie/A-B/heldout/loss")
    assert p["se_parowane"] < p["se_niezalezne"] and p["werdykt"] == p["werdykt_parowane"] == "pewne"
    s = next(x for x in liczby["porownania"] if x["id"] == "slayer_vs_pythia/siqa_cloze/acc")
    assert "se_parowane" not in s and "niezależne" in s["adnotacja"] and s["werdykt"] == "szum"


if __name__ == "__main__":
    testy = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    zle = 0
    for n, f in testy:
        try:
            if "tmp_path" in inspect.signature(f).parameters:  # pytest fixture, without pytest
                with tempfile.TemporaryDirectory() as d:
                    f(Path(d))
            else:
                f()
            print(f"PASS {n}")
        except AssertionError as e:
            zle += 1
            print(f"FAIL {n}: {e}")
    print(f"{len(testy) - zle}/{len(testy)}")
    sys.exit(1 if zle else 0)
