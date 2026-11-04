"""Liczby raportów (tools/liczby.py) i ich strażnik (tools/sprawdz_raporty.py).
Uruchom: python tests/test_liczby_raportow.py (albo pytest). Bez sieci; czyta surowe JSON-y z repo."""
import inspect
import math
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tools"))
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
    # a z that no comparison has (5,1 is a real held-out z of BLiMP checkpoints: avg5 vs the annealed arm, z = 5,15)
    assert S.niepasujace_liczby("SIQA 5,3 SE", zb, liczby["aliasy"]) == [("5,3", "z")]
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
    plik = "benchmarks/blimp/results/BLIMP.md"
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
    (meta,) = [m for m in liczby["raporty"] if m["plik"] == "benchmarks/blimp/results/BLIMP.md"]
    linie = (KORZEN / meta["plik"]).read_text(encoding="utf-8").splitlines()
    return liczby, copy.deepcopy(meta), linie


def test_bramki_przechodza_na_raporcie_blimp():
    liczby, meta, linie = _meta_blimp()
    assert S.bramki_raportu(meta, linie, liczby) == []
    # older reports have no metadata; CHECKPOINTS.md (BLiMP over checkpoints) has, when checkpoints.json exists
    assert [m["plik"] for m in liczby["raporty"]][0] == "benchmarks/blimp/results/BLIMP.md"
    assert set(m["plik"] for m in liczby["raporty"]) <= {"benchmarks/blimp/results/BLIMP.md",
                                                         "benchmarks/blimp/results/CHECKPOINTS.md",
                                                         "benchmarks/piqa/results/PIQA.md"}


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
    for rel in ("benchmarks/blimp/blimp_raport.py", "benchmarks/blimp/results/blimp.json", "benchmarks/blimp/results/BLIMP.md",
                "benchmarks/blimp/results/blimp_phenomena.svg", "benchmarks/blimp/results/blimp_paradigms.svg"):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(KORZEN / rel, tmp_path / rel)
    return tmp_path


def test_bramka_g_raport_bajt_w_bajt_z_generatora(tmp_path):
    liczby, meta, _ = _meta_blimp()
    assert S.bramka_generatora(meta, liczby) == []  # the committed report is the generator output
    k = _kopia_do_generatora(tmp_path)
    assert S.bramka_generatora(meta, liczby, k) == []
    md = k / "benchmarks/blimp/results/BLIMP.md"
    tekst = md.read_text(encoding="utf-8")
    # a verdict word, a number nobody else checks, a removed sentence, one trailing space
    for stare, nowe in (("t = -3.30, df = 66", "t = -3.30, df = 65"), (": certain;", ": probable;"),
                        ("This is a correlation over paradigm types, not a controlled experiment.", ""),
                        ("# BLiMP full set", "# BLiMP full set ")):
        assert stare in tekst, stare
        md.write_text(tekst.replace(stare, nowe, 1), encoding="utf-8")
        b = S.bramka_generatora(meta, liczby, k)
        assert len(b) == 1 and "(g)" in b[0][2] and b[0][0] == "benchmarks/blimp/results/BLIMP.md" and b[0][1] > 0, (stare, b)
    md.write_text(tekst, encoding="utf-8")
    svg = k / "benchmarks/blimp/results/blimp_paradigms.svg"
    svg.write_text(svg.read_text(encoding="utf-8").replace("#2a78d6", "#2a78d7", 1), encoding="utf-8")
    assert [b[0] for b in S.bramka_generatora(meta, liczby, k)] == ["benchmarks/blimp/results/blimp_paradigms.svg"]
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
    for rel, p in S.pliki_md(KORZEN):
        wszystkie += S.sprawdz_tekst(rel, p.read_text(encoding="utf-8").splitlines(), liczby, zb)
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
    assert not bledy("| Bielik-1.5B-v3 | 66,0 [63,4; 68,5] |", "benchmarks/ewok-pl/WYNIKI.md")
    assert [p for _, _, p in bledy("| Bielik-1.5B-v3 | 66,3 [63,4; 68,5] |", "benchmarks/ewok-pl/WYNIKI.md") if "66,3" in p]
    assert not bledy("Bielik ma na EWoK 66,0%.")
    assert [p for _, _, p in bledy("Bielik ma 63,4%.") if "63,4" in p]


def test_wlasne_z_benchmarku_sprawdzane_w_jego_plikach():
    # results/wsc273.json: Slayer 1.06 na panelu 200 wobec bazy losowej, z = 3,03
    assert not bledy("| panel 200 | losowa | z = 3,03 | pewne |", "benchmarks/wsc273/README.md")
    assert [p for _, _, p in bledy("| panel 200 | losowa | z = 3,77 | pewne |", "benchmarks/wsc273/README.md") if "3,77" in p]


def test_number_format_by_path_prefix():
    assert S.file_number_format("benchmarks/blimp/results/BLIMP.md") == (True, "blimp")  # generated English report
    assert S.file_number_format("benchmarks/blimp/README.md") == (False, "blimp")       # Polish docs, BLiMP numbers
    assert S.file_number_format("benchmarks/wikitext-2/RECIPE.md") == (False, None)
    assert S.file_number_format("benchmarks/ewok-pl/README.md") == (False, None)


def test_english_assessment_needs_se_or_verdict():
    assert S.ocena_bez_dowodu("Pythia-1B is better on BLiMP.")
    assert S.ocena_bez_dowodu("The gap is real for these pairs.")
    assert not S.ocena_bez_dowodu("Pythia-1B is ahead by 2.87 pts (SE 0.16 pts): certain.")
    assert not S.ocena_bez_dowodu("Slayer 1.06 is better on quantifiers, t = 0.27: noise.")
    assert S.zadeklarowany_werdykt("a certain gap") == "pewne"


def test_within_counts_only_as_a_bound():
    # regression: any "within" used to pass as evidence, so a count of paradigms hid a claim without SE
    assert S.ocena_bez_dowodu("X is better than Y within 7 paradigms.")
    assert not S.ocena_bez_dowodu("X is better than Y, within ±2 points.")
    assert not S.ocena_bez_dowodu("X is better than Y, within 2 SE.")


def test_within_paradigms_gives_exit_code_1(tmp_path):
    p = tmp_path / "raport.md"
    p.write_text("X is better than Y within 7 paradigms.\n", encoding="utf-8")
    assert S.main([str(p)]) == 1


def test_wikitext_files_use_pool_and_global_values():
    plik = "benchmarks/wikitext-2/README.md"
    assert not bledy("Byte perplexity Slayera 1.06: 1,846284.", plik)        # global (porownanie/wikitext)
    assert not bledy("Bajty oryginału: 1290527 (stosunek 1,0404).", plik)    # pool (mianownik.json)
    assert [p for _, _, p in bledy("Byte perplexity Slayera 1.06: 1,846290.", plik) if "1,846290" in p]
    assert not bledy("Model `x` ma 0,5.", plik)                               # code spans are skipped
    assert bledy("Model x ma 0,512345.", plik)


def test_porownanie_parowane_ma_obie_wersje_se():
    liczby, _ = dane()
    p = next(x for x in liczby["porownania"] if x["id"] == "wygaszanie/A-B/heldout/loss")
    assert p["se_parowane"] < p["se_niezalezne"] and p["werdykt"] == p["werdykt_parowane"] == "pewne"
    s = next(x for x in liczby["porownania"] if x["id"] == "slayer_vs_pythia/siqa_cloze/acc")
    assert "se_parowane" not in s and "niezależne" in s["adnotacja"] and s["werdykt"] == "szum"


class _WindowsLikeRel(type(KORZEN)):
    """A relative path whose str() gives backslashes, like WindowsPath; as_posix() gives slashes."""
    def __str__(self):
        return super().__str__().replace("/", "\\")

    def as_posix(self):
        return super().__str__().replace("\\", "/")


class _WindowsLikeRoot(type(KORZEN)):
    def relative_to(self, *other):
        return _WindowsLikeRel(super().relative_to(*other))


def test_path_keys_use_forward_slashes_when_str_gives_backslashes():
    # regression for PR #66: str(path) instead of .as_posix() breaks the gate on Windows only
    korzen = _WindowsLikeRoot(KORZEN)
    assert "\\" in str((korzen / "a/b").relative_to(korzen))
    rel = [r for r, _ in S.pliki_md(korzen)]
    zrodla = L.zbuduj(korzen)["zrodla"]
    assert rel and zrodla and all("\\" not in k for k in rel + zrodla), [k for k in rel + zrodla if "\\" in k][:3]


_WYJATEK_WERDYKTU = " <!-- liczba-spoza-wynikow: test werdyktu, liczba nie musi być w LICZBY.json -->"


def _problemy_werdyktu(tekst):
    return [p for _, _, p in bledy(tekst + _WYJATEK_WERDYKTU) if "(h)" in p]


def test_werdykt_pewne_przy_z_123_daje_kod_1():
    # |z| = 1,23 to szum; „pewne” obok poprawnej liczby ma paść
    b = _problemy_werdyktu("z = 1,23, pewne")
    assert b == ["(h) z 1,23 → szum, w tekście: pewne"], b
    assert not any("(a)" in p for _, _, p in bledy("z = 1,23, pewne" + _WYJATEK_WERDYKTU))


def test_werdykt_szum_przy_z_123_daje_kod_0():
    assert _problemy_werdyktu("z = 1,23, szum") == []
    assert bledy("z = 1,23, szum" + _WYJATEK_WERDYKTU) == []


def test_werdykt_prawdopodobne_przy_z_250_daje_kod_0():
    assert bledy("z = 2,50, prawdopodobne" + _WYJATEK_WERDYKTU) == []


def test_werdykt_pewne_przy_z_250_daje_kod_1():
    assert _problemy_werdyktu("z = 2,50, pewne") == ["(h) z 2,50 → prawdopodobne, w tekście: pewne"]


def test_werdykt_ujemne_z_minus_typograficzny_daje_kod_0():
    assert bledy("z = −3,20, pewne" + _WYJATEK_WERDYKTU) == []


def test_dwie_pary_w_linii_druga_bledna_daje_kod_1():
    tekst = "avg5 (z = 8,62, pewne), avg10 (z = 10,81, szum)"
    b = _problemy_werdyktu(tekst)
    assert b == ["(h) z 10,81 → pewne, w tekście: szum"], b


def test_progi_brzegowe_2_i_3_daja_kod_0():
    assert bledy("z = 2,00, prawdopodobne; z = 3,00, pewne" + _WYJATEK_WERDYKTU) == []


def test_przecinek_i_kropka_dziesietna_daja_kod_0():
    assert bledy("z = 1,23, szum oraz z = 1.23 (noise)" + _WYJATEK_WERDYKTU) == []
    assert bledy("z = 2.50 (probable) i z = 3.00: certain" + _WYJATEK_WERDYKTU) == []


def test_zly_werdykt_daje_kod_wyjscia_1(tmp_path):
    p = tmp_path / "raport.md"
    p.write_text("z = 1,23, pewne <!-- liczba-spoza-wynikow: test werdyktu -->\n", encoding="utf-8")
    assert S.main([str(p)]) == 1


def test_z_bez_werdyktu_zostaje_w_spokoju():
    assert bledy("SE 0,02 pkt, z = 12,55; po 67 paradygmatach t = 3,34." + _WYJATEK_WERDYKTU) == []
    assert bledy("z = 4,26." + _WYJATEK_WERDYKTU) == []


def test_iloraz_snr_i_przyimek_z_to_nie_statystyka():
    tekst = ("iloraz 1,11, szum. (|iloraz| ≥ 3 „pewne”, < 2 „szum”). "
             "Spada z 1,5757 do 1,4621.")
    assert bledy(tekst + _WYJATEK_WERDYKTU) == []


def test_werdykt_przed_nawiasem_nie_bierze_slowa_nastepnego_z():
    # blimp/README.md: „szum” po z = -2,68 należy do efektów wysp, nie do elipsy
    tekst = ("prawdopodobna w elipsie (z = -2,68) i szum w efektach wysp (z = -1,17) "
             "oraz kwantyfikatorach (z = 1,89).")
    assert bledy(tekst + _WYJATEK_WERDYKTU) == []


def test_werdykt_przed_nawiasem_bierze_slowo_najblizsze_z():
    # „pewne” dotyczy wyników wobec bazy, a werdyktem z = 0,40 jest „szum” tuż przed nawiasem
    tekst = "Oba wyniki są pewne wobec bazy, ale różnica między nimi to szum (z = 0,40)."
    assert bledy(tekst + _WYJATEK_WERDYKTU) == []
    zly = "Oba wyniki to szum wobec bazy, ale różnica między nimi jest pewna (z = 0,40)."
    assert _problemy_werdyktu(zly) == ["(h) z 0,40 → szum, w tekście: pewna"]


def test_werdykt_po_t_nie_jest_werdyktem_z():
    assert bledy("z = 10.81 | certain | t = 3.07 | probable" + _WYJATEK_WERDYKTU) == []
    assert bledy("z = -7,11 | t = -3,79 | pewne / prawdopodobne" + _WYJATEK_WERDYKTU) == []
    assert _problemy_werdyktu("z = -7,11 | t = -3,79 | szum / pewne") == [
        "(h) z -7,11 → pewne, w tekście: szum"]


def test_pewnosc_i_prawdopodobnie_nie_sa_werdyktem():
    # rzeczownik i przysłówek to nie przymiotnik werdyktu: kod 0, bez alarmu (h)
    assert bledy("z = 1,5, pewność niska" + _WYJATEK_WERDYKTU) == []
    assert bledy("z = 1,2, prawdopodobnie przez szum" + _WYJATEK_WERDYKTU) == []
    assert bledy("z = 1,2 (prawdopodobnie przypadek)" + _WYJATEK_WERDYKTU) == []


def test_z_bez_rownania_jak_w_piqa():
    assert bledy("(z 1,23, szum)" + _WYJATEK_WERDYKTU) == []
    assert _problemy_werdyktu("(z 1,23, pewne)") == ["(h) z 1,23 → szum, w tekście: pewne"]


def test_generator_gate_reports_forward_slashes_when_str_gives_backslashes(tmp_path):
    liczby, meta, _ = _meta_blimp()
    k = _kopia_do_generatora(tmp_path)
    (k / "benchmarks/blimp/results/blimp_paradigms.svg").unlink()
    b = S.bramka_generatora(meta, liczby, _WindowsLikeRoot(k))
    assert [x[0] for x in b] == ["benchmarks/blimp/results/blimp_paradigms.svg"], b


# ---- (i)-(k): werdykt przy t (p z rozkładu t przy df), dwa poziomy z jednym werdyktem, liczba Holma ----
# Zdania z main @ 09e597c, które przeszły bramkę (h), bo ona widzi tylko z (przegląd wsteczny, punkty 1 i 2).
_STARE_CHECKPOINTS_8 = (
    "**What the data show: step 13848 is closer to Pythia-1B than 10010, 2.14 pts (z = 15.00, t = 3.86), and than "
    "7150, 1.78 pts (z = 12.03, t = 3.18). Between 7150 and 10010 the gap does not shrink: -0.36 pts (z = -2.50, "
    "t = -0.77). The rise falls in the only interval that contains a restart of the run, and a trend cannot be told "
    "apart from the swings between checkpoints.** Step 10010 is a local dip: from 8600 the change is 1.55 pts "
    "(z = 10.81, t = 3.07).")
_STARE_CHECKPOINTS_110 = (
    "Per phenomenon (protocol question 2): average - Slayer 1.06 on the same pairs, paired SE, Holm over 12 phenomena "
    "x 3 averages at the 'probable' level. Holm-significant: 17 of 36, of them 2 decreases (quantifiers in avg5, "
    "quantifiers in avg10). Averaging does not move BLiMP evenly: some phenomena fall while the overall accuracy "
    "rises. Paradigms: t over the phenomenon's paradigm differences, df = k - 1; fewer than 3 paradigms: undetermined.")


def _reguly_ijk(tekst):
    return [p for _, _, p in bledy(tekst) if p[:3] in ("(i)", "(j)", "(k)")]


def test_regresja_wstecz_1_dolek_10010_daje_kod_1(tmp_path):
    # z = 10.81 pewne na parach, t = 3.07 (df = 66 z LICZBY.json) tylko prawdopodobne; zdanie niosło jeden werdykt
    assert any(p.startswith("(j) z 10.81") for p in _reguly_ijk(_STARE_CHECKPOINTS_8))
    assert any(p.startswith("(j) z -2.50") for p in _reguly_ijk(_STARE_CHECKPOINTS_8))
    p = tmp_path / "CHECKPOINTS_stary.md"
    p.write_text(_STARE_CHECKPOINTS_8 + "\n", encoding="utf-8")
    assert S.main([str(p)]) == 1


def test_regresja_wstecz_2_holm_bez_paradygmatow_daje_kod_1(tmp_path):
    assert any(p.startswith("(k)") for p in _reguly_ijk(_STARE_CHECKPOINTS_110))
    p = tmp_path / "CHECKPOINTS_stary.md"
    p.write_text(_STARE_CHECKPOINTS_110 + "\n", encoding="utf-8")
    assert S.main([str(p)]) == 1


def test_poprawione_zdania_wstecz_przechodza():
    nowe_8 = ("From 8600 to 10010 the change is -0.59 pts (z = -4.28, certain; t = -1.34, noise): a drop on these "
              "pairs that does not carry over to the paradigms.")
    nowe_110 = ("On the pairs, Holm-significant: 17 of 36, of them 2 decreases. Over the paradigms (phenomena with at "
                "least 3 paradigms, 27 tests): 4 not noise (probable), of them 0 decreases. Paradigms: t over the "
                "phenomenon's paradigm differences, df = k - 1.")
    assert _reguly_ijk(nowe_8) == [] and _reguly_ijk(nowe_110) == []


def test_werdykt_t_z_p_przy_df():
    # przy df = 2 t = 10 to p ≈ 0,0099: prawdopodobne, choć jako z byłoby pewne
    assert L.werdykt_t(10.0, 2) == "prawdopodobne"
    assert L.werdykt_t(-3.30, 66) == "pewne" and L.werdykt_t(3.07, 66) == "prawdopodobne"
    assert L.werdykt_t(-1.34, 66) == "szum" and L.werdykt_t(0.0, 5) == "szum"
    assert math.isclose(L.p_t(2.0, 10), 0.0734, abs_tol=1e-4)


def test_klastrowe_wazone_niezalezne_od_kolejnosci_grup():
    grupy = [(100, 0.2), (50, 0.1), (200, 0.3), (80, 0.25)]
    a, b = L.klastrowe_wazone(grupy), L.klastrowe_wazone(grupy[::-1])
    assert a == b
    assert math.isclose(a["roznica"], (20 + 5 + 60 + 20) / 430) and a["df"] == 3 and a["k"] == 4
    stala = L.klastrowe_wazone([(10, 0.1)] * 3)  # ta sama różnica w każdej grupie: brak rozrzutu, brak werdyktu
    assert stala["se"] == 0 and stala["t"] is None and stala["werdykt"] is None


def test_multiblimp_po_grupach_w_liczbach():
    liczby, _ = dane()
    p = next(x for x in liczby["porownania"] if x["id"] == "slayer_vs_pythia/multiblimp/acc_po_grupach")
    assert p["df"] == 13 and math.isclose(p["z"], 4.47, abs_tol=0.01) and p["werdykt"] == "pewne"


def test_zly_werdykt_przy_t_lapany_z_df_w_tekscie():
    assert _reguly_ijk("t = -1,34, df = 66, pewne") == ["(i) t -1,34 → szum, w tekście: pewne"]
    assert _reguly_ijk("t = -1,34, df = 66, szum") == []
    assert _reguly_ijk("t = 3,3, df = 2 (pewne)") == ["(i) t 3,3 → szum, w tekście: pewne"]


def test_werdykt_t_w_tabeli_z_df_z_kolumny_i_z_opisu():
    kolumna = "| zjawisko | t | df | werdykt |\n|---|---:|---:|---|\n| x | t = 2.40 | 7 | certain |"
    assert _reguly_ijk(kolumna) == ["(i) t 2.40 → szum, w tekście: certain"]
    opis = ("Paradigms: t over the 67 paradigm differences, df = 66.\n\n| a | t | p | verdict |\n|---|---|---|---|\n"
            "| x | t = 3.07 | 0.0031 | certain |")
    assert _reguly_ijk(opis) == ["(i) t 3.07 → prawdopodobne, w tekście: certain"]


def test_uklad_pary_ukosnik_paradygmaty_bierze_drugie_slowo_dla_t():
    assert _reguly_ijk("| z = -7,11 | t = -3,79, df = 7 | pewne / prawdopodobne |") == []
    assert _reguly_ijk("| z = -7,11 | t = -3,79, df = 7 | pewne / pewne |") == ["(i) t -3,79 → prawdopodobne, w tekście: pewne"]


def test_t_bez_df_i_bez_porownania_zostaje_w_spokoju():
    # nie wiadomo, przy jakim df czytać t: bramka nie zgaduje
    assert _reguly_ijk("t = 9,87 (pewne)") == []


if __name__ == "__main__":
    testy =[(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
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
