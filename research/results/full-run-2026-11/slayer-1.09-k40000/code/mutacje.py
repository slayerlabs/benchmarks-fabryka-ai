"""Mutacje na prawdziwych danych pomiaru: każda psuje jedną rzecz w kodzie liczącym albo w jego wyniku i musi zapalić
strażnika. Reguła strażnika-tautologii (notatka zasad raportowania): mutacja kodu liczby_109.py regeneruje cały
LICZBY.json przy przypiętych sumach wejść, a łapie ją przeliczenie niezależne, nie ten sam kod.

    python mutacje.py <eksport z próbkami> <manifest.jsonl przebiegu> <probki_sha256.json> <LICZBY.json> <RAPORT.md>
                      <katalog roboczy> <wynik.json>

Strażnicy: przelicz_niezaleznie.py (LICZBY wobec próbek), sprawdz_sumy w liczby_109.py (próbki wobec spisu sum),
sprawdz_raport.py (RAPORT wobec LICZBY: strażnik liczb repo i zgodność bajt w bajt z generatorem). Przeliczenie
niezależne musi dać kod 0 na danych bez zmian (inaczej mutacje nic nie mierzą i skrypt kończy się kodem 1); mutacja
jest złapana, gdy daje rozjazd. Mutacje kodu robione na modułach w pamięci, pliki się nie zmieniają.
Kod 0 tylko wtedy, gdy każda mutacja została złapana.
"""
import copy
import json
import subprocess
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
sys.path.insert(0, str(TU))
import liczby_109 as L  # noqa: E402
import sprawdz_raport as SR  # noqa: E402

R, S = L.R, L.S


SUMY = None  # probki_sha256.json, ustawiane w main


def przelicz(eksport, liczby, manifest, roboczy, nazwa):
    """Zbiór linii rozjazdu przeliczenia niezależnego (pusty = zgodne) i kod wyjścia."""
    p = roboczy / f"LICZBY_{nazwa}.json"
    p.write_text(json.dumps(liczby, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(TU / "przelicz_niezaleznie.py"), str(eksport), str(p), str(manifest),
                        str(SUMY)], capture_output=True, text=True)
    linie = set(r.stdout.strip().splitlines()) if r.returncode else set()
    if r.returncode not in (0, 1):
        linie = {f"przelicz_niezaleznie.py padł: {r.stderr.strip().splitlines()[-1:]}"}
    return r.returncode, linie


def main():
    global SUMY
    eksport, manifest, sumy, liczby_p, raport_p, roboczy, wyj = map(Path, sys.argv[1:8])
    SUMY = sumy
    roboczy.mkdir(parents=True, exist_ok=True)
    LZ = json.loads(liczby_p.read_text(encoding="utf-8"))
    wyniki = []
    kod0, baza = przelicz(eksport, LZ, manifest, roboczy, "bez_zmian")
    wyniki.append({"mutacja": "bez zmian (strażnik musi dać 0)", "zlapana": None, "kod": kod0, "rozjazdy": sorted(baza)})
    print(f"bez zmian: kod {kod0}, rozjazdów {len(baza)}")
    if kod0 != 0:
        wyj.write_text(json.dumps(wyniki, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("przeliczenie niezależne nie daje 0 na danych bez zmian: mutacje nic by nie mierzyły")
        return 1

    def zapisz(nazwa, zlapana, opis):
        wyniki.append({"mutacja": nazwa, "zlapana": zlapana, "komunikat": opis})
        print(f"{'ZŁAPANA ' if zlapana else 'PRZESZŁA'} {nazwa}: {opis[:140]}")

    def oceń(nazwa, m):
        kod, linie = przelicz(eksport, m, manifest, roboczy, str(len(wyniki)))
        nowe = sorted(linie - baza)
        zapisz(nazwa, bool(nowe), "; ".join(nowe) or "brak nowego rozjazdu")

    # 1. wynik kodu liczącego podmieniony w LICZBY.json
    def zmien(nazwa, f):
        m = copy.deepcopy(LZ)
        f(m)
        oceń(nazwa, m)

    idx = {t["benchmark"]: i for i, t in enumerate(LZ["testy"])}
    t0 = "arc-easy"
    zmien(f"LICZBY: Δ {t0} + 0,01", lambda m: m["testy"][idx[t0]]["porownanie"].__setitem__(
        "roznica", m["testy"][idx[t0]]["porownanie"]["roznica"] + 0.01))
    zmien(f"LICZBY: SE Δ {t0} × 1,1", lambda m: m["testy"][idx[t0]]["porownanie"].__setitem__(
        "se", m["testy"][idx[t0]]["porownanie"]["se"] * 1.1))
    zmien(f"LICZBY: kontrola narzędzia {t0} odwrócona", lambda m: m["testy"][idx[t0]]["kontrola"].__setitem__(
        "zgodna", not m["testy"][idx[t0]]["kontrola"]["zgodna"]))
    zmien("LICZBY: werdykt po Holmie winogrande prawdopodobne → pewne", lambda m: m["testy"][idx["winogrande"]][
        "porownanie"].__setitem__("werdykt_holm", "pewne"))
    zmien("LICZBY: 1.08 przeliczone piqa + 0,001", lambda m: m["testy"][idx["piqa"]]["v108_przeliczone"].__setitem__(
        "wartosc", m["testy"][idx["piqa"]]["v108_przeliczone"]["wartosc"] + 0.001))

    # 2. mutacje kodu liczby_109 / raport / statystyka w pamięci, pełna regeneracja LICZBY.json przy przypiętych sumach
    def kod_mut(nazwa, ustaw, przywroc):
        ustaw()
        try:
            m = L.zbuduj(eksport, manifest, sumy)
        except BaseException as e:  # noqa: BLE001 — wyjątek przy regeneracji też jest złapaniem
            przywroc()
            zapisz(nazwa, True, f"zbuduj przerwał: {type(e).__name__}: {str(e)[:100]}")
            return
        przywroc()
        m["eksploracyjne"] = LZ.get("eksploracyjne")  # zbuduj liczy tylko protokół; eksploracja bez zmian
        oceń(nazwa, m)

    stare = {"M_HOLM": L.M_HOLM, "A": L.A, "B": L.B, "wynik_koncowy": L.wynik_koncowy, "kontrola": L.kontrola,
             "porownaj": R.porownaj, "po_holmie": S.po_holmie}
    przywroc = lambda: [setattr(L, k, stare[k]) for k in ("M_HOLM", "A", "B", "wynik_koncowy", "kontrola")] + [
        setattr(R, "porownaj", stare["porownaj"]), setattr(S, "po_holmie", stare["po_holmie"])]
    kod_mut("kod: m w Holmie 15 → 14", lambda: setattr(L, "M_HOLM", 14), przywroc)
    kod_mut("kod: m w Holmie 15 → 16", lambda: setattr(L, "M_HOLM", 16), przywroc)
    kod_mut("kod: porównanie liczone B − A (znak Δ i statystyki)",
            lambda: setattr(R, "porownaj", lambda o, p, a, b: stare["porownaj"](o, p, b, a)), przywroc)
    kod_mut("kod: Holm z m = liczbie wierszy z p mniejszej o jeden (filtr wiersza)",
            lambda: setattr(S, "po_holmie", lambda ps, m: stare["po_holmie"](ps, m=m - 1)), przywroc)
    kod_mut("kod: A i B zamienione (znak Δ)", lambda: (setattr(L, "A", stare["B"]), setattr(L, "B", stare["A"])), przywroc)
    kod_mut("kod: kierunek wyzej_lepiej odwrócony", lambda: setattr(
        L, "wynik_koncowy", lambda p, w, z: stare["wynik_koncowy"](p, not w, z)), przywroc)
    kod_mut("kod: kontrola narzędzia bez skali pliku (MultiBLiMP w %)", lambda: setattr(
        L, "kontrola", lambda prz, man: stare["kontrola"]({**prz, "skala_w_pliku": 1.0}, man)), przywroc)

    def se_x(o, p, a, b):
        r = stare["porownaj"](o, p, a, b)
        return r and {**r, "se": r["se"] * 1.1}
    kod_mut("kod: SE porównania × 1,1", lambda: setattr(R, "porownaj", se_x), przywroc)

    # 3. próbki wobec spisu sum zapisanego przed raportem
    sm = json.loads(sumy.read_text(encoding="utf-8"))
    plik = sorted(sm["pliki"])[0]
    sm["pliki"][plik] = "0" * 64
    try:
        L.sprawdz_sumy(eksport, sm)
        zapisz(f"próbki: suma {plik} zmieniona", False, "sprawdz_sumy przepuścił")
    except SystemExit as e:
        zapisz(f"próbki: suma {plik} zmieniona", True, str(e)[:120])

    # 4. RAPORT wobec LICZBY: liczba i werdykt podmienione w tekście
    straznik = SR.zaladuj(SR.DOMYSLNY)
    tekst = raport_p.read_text(encoding="utf-8")
    sprawdz = lambda x: SR.sprawdz(straznik, LZ, x) + SR.bajt_w_bajt(LZ, x)
    zdrowy = sprawdz(tekst)
    wyniki.append({"mutacja": "RAPORT bez zmian", "zlapana": None, "kod": 1 if zdrowy else 0,
                   "komunikat": f"{len(zdrowy)} problemów"})
    t = LZ["testy"][idx[t0]]
    stara = f"{t['v109']['wartosc']:.4f}".replace(".", ",")
    nowa = f"{t['v109']['wartosc'] + 0.0123:.4f}".replace(".", ",")
    assert stara in tekst, stara
    n_med = str(LZ["testy"][idx["medmcqa"]]["v109"]["n"])
    for nazwa, zmieniony in ((f"RAPORT: {stara} → {nowa}", tekst.replace(stara, nowa, 1)),
                             ("RAPORT: WinoGrande „tak (prawdopodobne)” → „tak (pewne)”",
                              tekst.replace("| tak (prawdopodobne) | lepszy (prawdopodobne) |",
                                            "| tak (pewne) | lepszy (pewne) |", 1)),
                             (f"RAPORT: n MedMCQA {n_med} → 4138", tekst.replace(f"| MedMCQA | {n_med} |", "| MedMCQA | 4138 |", 1)),
                             ("RAPORT: „na 9 z 15” → „na 10 z 15”", tekst.replace("na 9 z 15", "na 10 z 15", 1))):
        assert zmieniony != tekst, nazwa
        bledy = sprawdz(zmieniony)
        zapisz(nazwa, bool(bledy), bledy[0][2] if bledy else "strażnik przepuścił")

    wyj.write_text(json.dumps(wyniki, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    niezlapane = [w["mutacja"] for w in wyniki if w["zlapana"] is False]
    zdrowe_ok = not zdrowy
    print(f"{sum(1 for w in wyniki if w['zlapana'])} złapanych, niezłapane: {niezlapane or 'brak'}; "
          f"raport bez zmian: {'0 problemów' if zdrowe_ok else 'PROBLEMY'}")
    return 1 if niezlapane or not zdrowe_ok else 0


if __name__ == "__main__":
    raise SystemExit(main())
