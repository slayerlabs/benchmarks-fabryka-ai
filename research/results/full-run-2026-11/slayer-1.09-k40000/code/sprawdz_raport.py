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
DOMYSLNY = TU.parents[3] / "tools" / "sprawdz_raporty.py"
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


def main():
    L = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    raport = Path(sys.argv[2])
    straznik = zaladuj(Path(sys.argv[3]) if len(sys.argv) > 3 else DOMYSLNY)
    bledy = sprawdz(straznik, L, raport.read_text(encoding="utf-8"), raport.name)
    for plik, nr, powod in bledy:
        print(f"{plik}:{nr}: {powod}")
    print(f"1 plik, {len(bledy)} problemów")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
