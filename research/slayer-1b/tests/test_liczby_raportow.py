"""Liczby raportów (narzedzia/liczby.py) i ich strażnik (narzedzia/sprawdz_raporty.py).
Uruchom: python tests/test_liczby_raportow.py (albo pytest). Bez sieci; czyta surowe JSON-y z repo."""
import math
import sys
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


def test_liczby_blimp_tylko_w_linii_z_nazwa():
    liczby, _ = dane()
    p = next(p for p in liczby["porownania"] if p["test"] == "blimp")
    tekst = f"{p['wartosc_a']:.4f}".replace(".", ",")
    zb = S.zbiory(liczby)
    assert not S.niepasujace_liczby(f"BLiMP: {tekst}", zb, liczby["aliasy"])
    assert S.niepasujace_liczby(f"Wynik {tekst}", zb, liczby["aliasy"]) or \
        zb["*"]["surowa"].zawiera(p["wartosc_a"], 4)  # unless a non-BLiMP value happens to match


def test_dokumenty_repo_zgodne_z_liczbami():
    liczby, zb = dane()
    wszystkie = []
    for p in S.pliki_md(KORZEN):
        wszystkie += S.sprawdz_tekst(str(p.relative_to(KORZEN)), p.read_text(encoding="utf-8").splitlines(), liczby, zb)
    assert wszystkie == [], wszystkie


def test_zepsuta_liczba_w_kopii_dokumentu_zlapana():
    plik = "lab/DLA_ARKA_I_CHETNYCH.md"
    tekst = (KORZEN / plik).read_text(encoding="utf-8")
    assert "Belebele po treści 0,330 vs 0,297" in tekst
    zepsuty = tekst.replace("Belebele po treści 0,330 vs 0,297", "Belebele po treści 0,345 vs 0,297")
    b = bledy(zepsuty, plik)
    assert [p for _, _, p in b if "0,345" in p], b


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
            f()
            print(f"PASS {n}")
        except AssertionError as e:
            zle += 1
            print(f"FAIL {n}: {e}")
    print(f"{len(testy) - zle}/{len(testy)}")
    sys.exit(1 if zle else 0)
