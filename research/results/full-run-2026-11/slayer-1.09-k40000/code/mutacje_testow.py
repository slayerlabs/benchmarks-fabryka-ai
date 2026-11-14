"""Mutacje kodu kontrolnego wobec testów: każda psuje jedną rzecz w dolacz_wyniki.py albo przelicz_niezaleznie.py i musi
zapalić tests/test_slayer_109_k40000.py. Plik źródłowy wraca do stanu wyjściowego po każdej mutacji (także po błędzie).

    python mutacje_testow.py <python z pytest> <wynik.json>

Kod 0: baza zielona i każda mutacja zapalona.
"""
import json
import subprocess
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
TEST = TU.parents[3] / "tests" / "test_slayer_109_k40000.py"
DW, PN, EK = TU / "dolacz_wyniki.py", TU / "przelicz_niezaleznie.py", TU / "eksploracja_109.py"
MUT = [
    (DW, "dolacz: bez sprawdzania sha plików", "    if zle:\n        raise SystemExit(f\"sha256 różne od probki_sha256.json: {zle[:5]}\")", "    pass"),
    (DW, "dolacz: bez sprawdzania spisu plików", "    if pliki != set(sumy[\"pliki\"]):", "    if False:"),
    (DW, "dolacz: bez sprawdzania manifestu eksportu", "            if sumy[\"pliki\"].get(p) != s:", "            if False:"),
    (DW, "dolacz: gzip z czasem w nagłówku", "compresslevel=9, mtime=0)", "compresslevel=9)"),
    (DW, "dolacz: 1.08 do manifestu przebiegu", "nowe = [w for w in manifest if w[\"model\"] == A]", "nowe = manifest"),
    (DW, "odtworz: bez porównania sha", "        if sha256_bajtow(dane) != s:", "        if False:"),
    (DW, "dolacz: drugie dołączenie bez odmowy", "        raise SystemExit(f\"{manifest_przebiegu} ma już wiersze {A}\")", "        pass"),
    (PN, "przelicz: próg „prawdopodobne” |z| 2 → 1,5", "P3, P2 = 2 * stats.norm.sf(3), 2 * stats.norm.sf(2)",
     "P3, P2 = 2 * stats.norm.sf(3), 2 * stats.norm.sf(1.5)"),
    (PN, "przelicz: próg „pewne” |z| 3 → 2,5", "P3, P2 = 2 * stats.norm.sf(3), 2 * stats.norm.sf(2)",
     "P3, P2 = 2 * stats.norm.sf(2.5), 2 * stats.norm.sf(2)"),
    (PN, "przelicz: m Holma 15 → liczba p", "out, mx = [None] * len(ps), 0.0", "out, mx = [None] * len(ps), 0.0\n    m = len(idx)"),
    (PN, "przelicz: acc_norm ze spacjami (definicja lm_eval)",
     "    return float(pierwszy_max([ll / max(len(c.lstrip(\" \")), 1) for ll, c in zip(lls, konty)]) == gold)",
     "    return float(pierwszy_max([ll / max(len(c), 1) for ll, c in zip(lls, konty)]) == gold)"),
    (PN, "przelicz: remis → ostatni indeks", "        if v > x[best]:", "        if v >= x[best]:"),
    (PN, "przelicz: PMI bez dzielenia listy", "k = len(lls) // 2 if \"acc_mutual_info\" in r[\"metrics\"] else len(lls)",
     "k = len(lls)"),
    (PN, "przelicz: SE klastrowe bez G/(G−1)", "sum(s * s for s in sumy.values()) * G / (G - 1)", "sum(s * s for s in sumy.values())"),
    (PN, "przelicz: kontrola 0,5 → 5 SE", "<= 0.5 * m[\"se\"]", "<= 5 * m[\"se\"]"),
    (PN, "przelicz: kontrola bez skali MultiBLiMP", "skala = 100.0 if m[\"benchmark\"] == \"multiblimp-pl\" else 1.0", "skala = 1.0"),
    (PN, "przelicz: bez sprawdzania sha plików eksportu",
     "    bledy += [f\"{p}: sha256 różne od spisu\" for p in sorted(pliki & set(spis)) if sha256_pliku(eksport / p) != spis[p]]",
     "    pass"),
    (PN, "przelicz: bez sprawdzania sha manifestu", "    if sha256_pliku(manifest_p) != w.get(\"manifest_przebiegu\"):", "    if False:"),
    (PN, "przelicz main: zła suma wejścia nie zatrzymuje (M7)", "    if bledy:\n        print(", "    if False:\n        print("),
    (PN, "przelicz rozbicie: CI 1,645 zamiast 1,96", "Z95 = 1.96", "Z95 = 1.645"),
    (PN, "przelicz rozbicie: Holm z m = 15 zamiast liczby grup", "holm([out[g][\"p\"] for g in nazwy], m=len(nazwy))",
     "holm([out[g][\"p\"] for g in nazwy], m=M)"),
    (PN, "przelicz rozbicie: CI bez przycięcia", "[max(0.0, m - Z95 * se), min(1.0, m + Z95 * se)])",
     "[m - Z95 * se, m + Z95 * se])"),
    (EK, "eksploracja: CI 1,645 zamiast 1,96", "Z95 = 1.96", "Z95 = 1.645"),
    (EK, "eksploracja: CI bez przycięcia", "[max(0.0, m - Z95 * se), min(1.0, m + Z95 * se)]", "[m - Z95 * se, m + Z95 * se]"),
    (EK, "eksploracja: Holm w rodzinie jako p × (m − ranga)", "    return S.holm(zm, m=m)[i]",
     "    return min(1.0, p_nowe * (m - sorted(x for x in zm if x is not None).index(p_nowe)))"),
    (EK, "eksploracja: Holm w rozbiciu z m = 15", "S.po_holmie([w[\"porownanie\"][\"p\"] for w in wiersze], m=len(wiersze))",
     "S.po_holmie([w[\"porownanie\"][\"p\"] for w in wiersze], m=15)"),
]


def pytest(py):
    r = subprocess.run([py, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", str(TEST)], capture_output=True, text=True)
    return r.returncode, (r.stdout.strip().splitlines() or [""])[-1][:120]


def main():
    py, wyj = sys.argv[1], Path(sys.argv[2])
    kod, ost = pytest(py)
    wyniki = [{"mutacja": "baza", "kod": kod, "komunikat": ost}]
    print(f"BAZA kod {kod}: {ost}")
    zle = kod != 0
    for plik, nazwa, old, new in MUT:
        oryg = plik.read_text(encoding="utf-8")
        if old not in oryg:
            wyniki.append({"mutacja": nazwa, "zapalona": None, "komunikat": "nie zastosowano"})
            print(f"NIE ZASTOSOWANO {nazwa}")
            zle = True
            continue
        try:
            plik.write_text(oryg.replace(old, new, 1), encoding="utf-8")
            kod, ost = pytest(py)
        finally:
            plik.write_text(oryg, encoding="utf-8")
        wyniki.append({"mutacja": nazwa, "zapalona": kod != 0, "kod": kod, "komunikat": ost})
        print(f"{'ZAPALONA' if kod else 'PRZESZŁA'} {nazwa}: {ost}")
        zle |= kod == 0
    wyj.write_text(json.dumps(wyniki, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("KOD", 1 if zle else 0)
    return 1 if zle else 0


if __name__ == "__main__":
    raise SystemExit(main())
