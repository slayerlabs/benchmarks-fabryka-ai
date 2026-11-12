"""Składa zestaw z plików roboczych i sprawdza go TYM SAMYM kodem oceny, którym będą oceniane modele.

python -I code/zloz_zestaw.py <katalog_roboczy>  -> dane/polecenia.jsonl, dane/shoty.jsonl (+ sha256 na stdout)

Sprawdza: 8 kategorii × 30, unikalne id, pola typu; wzorzec każdej pozycji weryfikowalnej dostaje 1 od oceny
(ze separatorem szablonu A, jak odpowiedź modelu); `liczba` == eval(obliczenie); kod: wzorzec przechodzi testy,
a atrapa zwracająca None ich nie przechodzi.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import ocena  # noqa: E402
import szablony  # noqa: E402

KATEGORIE = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski", "tekst_techniczny"]
POLA = {"krotka": {"akceptowane", "zakazane"}, "zdanie": {"akceptowane"}, "liczba": {"liczba", "obliczenie"},
        "kod": {"funkcja", "testy"}, "otwarte": {"kryteria"}}


def sprawdz(p, bledy):
    typ = p["typ"]
    for k in {"id", "kat", "typ", "trudnosc", "polecenie", "wzorzec"} | POLA[typ]:
        if k not in p:
            bledy.append(f"{p.get('id')}: brak pola {k}")
            return
    odp = szablony.ciag_wzorca("A", p)
    if typ in ("krotka", "zdanie", "liczba") and "\n" in p["wzorzec"]:
        bledy.append(f"{p['id']}: wzorzec wieloliniowy")
    if typ == "krotka" and ocena.ocen_krotka(odp, p["akceptowane"], p["zakazane"]) != 1:
        bledy.append(f"{p['id']}: wzorzec nie przechodzi oceny krotka")
    if typ == "zdanie" and ocena.ocen_zdanie(odp, p["akceptowane"]) != 1:
        bledy.append(f"{p['id']}: wzorzec nie przechodzi oceny zdanie")
    if typ == "liczba":
        if abs(eval(p["obliczenie"], {"__builtins__": {}}, {"round": round, "abs": abs}) - p["liczba"]) > 1e-6:
            bledy.append(f"{p['id']}: obliczenie != liczba")
        if ocena.ocen_liczba(odp, p["liczba"]) != 1:
            bledy.append(f"{p['id']}: wzorzec nie przechodzi oceny liczba")
    if typ == "kod":
        if ocena.ocen_kod(odp, p["testy"])[0] != 1:
            bledy.append(f"{p['id']}: wzorzec nie przechodzi testów")
        sygn = re.search(r"def\s+\w+\([^)]*\)[^:]*:", p["wzorzec"]).group()
        if ocena.uruchom_testy(f"{sygn}\n    return None", p["testy"])[0] != 0:
            bledy.append(f"{p['id']}: testy przechodzą dla atrapy None")


def main():
    rob = Path(sys.argv[1])
    pozycje, shoty, bledy = [], [], []
    for kat in KATEGORIE:
        rows = [json.loads(x) for x in (rob / f"{kat}.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        sh = [json.loads(x) for x in (rob / f"{kat}_shoty.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        if len(rows) != 30 or len(sh) != 3:
            bledy.append(f"{kat}: {len(rows)} pozycji, {len(sh)} przykładów")
        for p in rows + sh:
            if p.get("kat") != kat:
                bledy.append(f"{p.get('id')}: kat {p.get('kat')} != {kat}")
            sprawdz(p, bledy)
        pozycje += rows
        shoty += sh
    ids = [p["id"] for p in pozycje + shoty]
    if len(ids) != len(set(ids)):
        bledy.append("powtórzone id")
    if bledy:
        print("\n".join(bledy))
        sys.exit(1)
    dane = KOD.parent / "dane"
    dane.mkdir(exist_ok=True)
    for nazwa, rows in (("polecenia.jsonl", pozycje), ("shoty.jsonl", shoty)):
        tekst = "".join(json.dumps(p, ensure_ascii=False) + "\n" for p in rows)
        (dane / nazwa).write_text(tekst, encoding="utf-8")
        print(nazwa, len(rows), hashlib.sha256(tekst.encode("utf-8")).hexdigest())
    from collections import Counter
    print(Counter((p["kat"], p["typ"]) for p in pozycje))


if __name__ == "__main__":
    main()
