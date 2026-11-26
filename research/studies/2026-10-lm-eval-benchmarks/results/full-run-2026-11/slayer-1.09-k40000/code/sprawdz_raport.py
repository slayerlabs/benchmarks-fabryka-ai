"""RAPORT.md wobec LICZBY.json tego pomiaru strażnikiem liczb: `research/tools/sprawdz_raporty.py` tego repo
(domyślnie) albo `narzedzia/sprawdz_raporty.py` repo slayer-lab (te same czyste funkcje `zbiory`, `sprawdz_tekst`).

    python sprawdz_raport.py <LICZBY.json> <RAPORT.md> [<sprawdz_raporty.py>]

Globalny przebieg strażnika czyta `results/LICZBY.json` repo i skanuje wszystkie .md, więc ten raport ma tam
wyłączenie, a tutaj wołamy jego czyste funkcje na NASZYM pliku: LICZBY.json spłaszczone do formatu strażnika
(`wartosci` ze ścieżką z kluczem testu, `aliasy` z pełnych nazw testów, `porownania` z werdyktem i z albo t).
Reguły (a) liczba bez pokrycia, (b) ocena bez SE, (c) za mocny werdykt, (h)-(l) werdykt wobec z/t i Holm w tabeli.
Kod wyjścia 1 przy którymkolwiek problemie, 0 bez problemów.
"""
import importlib.util
import json
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
DOMYSLNY = TU.parents[5] / "tools" / "sprawdz_raporty.py"
SILA = ("szum", "prawdopodobne", "pewne")


def splaszcz(obj, sciezka=""):
    """{ścieżka: liczba}; element listy `testy` dostaje w ścieżce klucz testu, żeby strażnik przypisał go testowi."""
    if isinstance(obj, bool) or obj is None:
        return {}
    if isinstance(obj, (int, float)):
        return {sciezka: obj}
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(splaszcz(v, f"{sciezka}/{k}" if sciezka else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            seg = v.get("benchmark", str(i)) if isinstance(v, dict) else str(i)
            out.update(splaszcz(v, f"{sciezka}/{seg}"))
    return out


def format_straznika(L: dict) -> dict:
    aliasy = {t["benchmark"]: [t["nazwa"]] for t in L["testy"]}
    porownania = []
    for t in L["testy"]:
        p = t["porownanie"]
        porownania.append({"test": t["benchmark"], "rodzina": "wersje",
                           # najmocniejszy werdykt testu: przed Holmem (Holm go tylko osłabia); tabela pisze oba
                           "werdykt": p["werdykt"] if p["werdykt"] in SILA else None,
                           "z_parowane": p.get("z") if p.get("z") is not None else p.get("t"),
                           # próg kontroli narzędzia pisany jako „0,5 SE”: strażnik czyta liczbę przed SE jako z
                           "z_niezalezne": t["kontrola"]["prog_se"]})
    # porównania eksploracyjne (po wyniku): każdy słownik z z albo t pod kluczem testu, z jego werdyktem
    def zbierz(obj, test):
        if isinstance(obj, dict):
            stat = obj.get("z") if obj.get("z") is not None else obj.get("t")
            if stat is not None and isinstance(stat, (int, float)):
                for w in {obj.get("werdykt"), obj.get("werdykt_holm")} & set(SILA):
                    porownania.append({"test": test, "rodzina": "wersje", "werdykt": w, "z_parowane": stat})
                if not {obj.get("werdykt"), obj.get("werdykt_holm")} & set(SILA):
                    porownania.append({"test": test, "rodzina": "wersje", "werdykt": None, "z_parowane": stat})
            for k, v in obj.items():
                zbierz(v, k if k in aliasy else test)
        elif isinstance(obj, list):
            for v in obj:
                zbierz(v, test)
    zbierz(L.get("eksploracyjne") or {}, None)
    return {"wartosci": splaszcz(L), "aliasy": aliasy, "porownania": porownania}


def zaladuj(sciezka: Path):
    sys.path.insert(0, str(sciezka.parent))  # strażnik repo importuje liczby.py ze swojego katalogu
    spec = importlib.util.spec_from_file_location(f"straznik_{abs(hash(str(sciezka)))}", sciezka)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sprawdz(straznik, L: dict, tekst: str, nazwa: str = "RAPORT.md") -> list:
    liczby = format_straznika(L)
    return straznik.sprawdz_tekst(nazwa, tekst.splitlines(), liczby, straznik.zbiory(liczby))


def bajt_w_bajt(L: dict, tekst: str, nazwa: str = "RAPORT.md") -> list:
    """(g) raport równy wyjściu generatora raport_md.py z tego LICZBY.json; łapie każdą ręczną zmianę tekstu (także
    liczby całkowite, których strażnik liczb nie czyta: n, „9 z 15”). Błąd obliczeń łapie tylko przeliczenie niezależne."""
    sys.path.insert(0, str(TU))
    import raport_md
    wzor = raport_md.raport(L)
    if tekst == wzor:
        return []
    a, b = tekst.splitlines(), wzor.splitlines()
    nr = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    return [(nazwa, nr + 1, f"(g) plik różni się od wyjścia raport_md.py z LICZBY.json (pierwsza różnica w linii {nr + 1})")]


def sekcja_readme(tekst: str) -> str:
    """Sekcja 1.08 → 1.09 README przebiegu (raport.py, toku_section): od jej <details> do </details>."""
    start = tekst.find("<summary><b>1.08 → Slayer 1B 1.09")
    if start < 0:
        return ""
    koniec = tekst.find("</details>", start)
    return tekst[tekst.rfind("<details>", 0, start):koniec + len("</details>")]


def sekcja_zbiorcza(tekst: str) -> str:
    """Tabela zbiorcza na górze README przebiegu (raport.py, toku_summary): od jej nagłówka do następnego „## ”."""
    start = tekst.find("## Wyniki Slayer 1B 1.09")
    if start < 0:
        return ""
    koniec = tekst.find("\n## ", start + 3)
    return tekst[start:koniec if koniec > 0 else len(tekst)]


def main():
    args = sys.argv[1:]
    readme = None
    if "--readme" in args:
        i = args.index("--readme")
        readme = Path(args[i + 1])
        del args[i:i + 2]
    L = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    raport = Path(args[1])
    straznik = zaladuj(Path(args[2]) if len(args) > 2 else DOMYSLNY)
    tekst = raport.read_text(encoding="utf-8")
    bledy = sprawdz(straznik, L, tekst, raport.name) + bajt_w_bajt(L, tekst, raport.name)
    pliki = 1
    if readme is not None:
        tekst_r = readme.read_text(encoding="utf-8")
        pliki += 1
        for nazwa, sek in (("sekcja 1.08 → 1.09", sekcja_readme(tekst_r)), ("tabela zbiorcza 1.09", sekcja_zbiorcza(tekst_r))):
            if not sek:
                bledy.append((readme.name, 0, f"brak: {nazwa} w README"))
                continue
            bledy += sprawdz(straznik, L, sek, f"{readme.name} ({nazwa})")
            wiersze = [w for w in sek.splitlines() if w.startswith("| ") and not w.startswith("| test")]
            if len(wiersze) != len(L["testy"]):
                bledy.append((readme.name, 0, f"{nazwa}: {len(wiersze)} wierszy testów, LICZBY.json {len(L['testy'])}"))
    for plik, nr, powod in bledy:
        print(f"{plik}:{nr}: {powod}")
    print(f"{pliki} plików, {len(bledy)} problemów")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
