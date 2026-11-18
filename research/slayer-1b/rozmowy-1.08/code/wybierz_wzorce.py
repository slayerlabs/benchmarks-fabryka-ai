"""Próba 10% poleceń weryfikowalnych do niezależnej kontroli wzorców (PROTOKOL_ANEKS.md, A4).

python -I code/wybierz_wzorce.py  -> dane/kontrola_wzorcow.jsonl (bez wyników modeli)
Warstwy = kategorie, przydział proporcjonalny metodą największych reszt (remis: kolejność kategorii w pliku),
losowanie random.Random(20261112) w obrębie kategorii.
"""
import json
import math
import random
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
SEED, N = 20261112, 20
POLA = ["id", "kat", "typ", "polecenie", "wzorzec", "akceptowane", "zakazane", "liczba", "obliczenie", "funkcja", "testy"]


def przydzial(liczby, n):
    razem = sum(liczby.values())
    udz = {k: n * v / razem for k, v in liczby.items()}
    wynik = {k: math.floor(u) for k, u in udz.items()}
    reszta = n - sum(wynik.values())
    for k in sorted(udz, key=lambda k: -(udz[k] - wynik[k]))[:reszta]:
        wynik[k] += 1
    return wynik


def main():
    poz = [json.loads(x) for x in (BADANIE / "dane/polecenia.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    wer = [p for p in poz if p["typ"] != "otwarte"]
    kat = {}
    for p in wer:
        kat.setdefault(p["kat"], []).append(p)
    ile = przydzial({k: len(v) for k, v in kat.items()}, N)
    rng = random.Random(SEED)
    wybrane = []
    for k, v in kat.items():
        wybrane += rng.sample(v, ile[k])
    with open(BADANIE / "dane/kontrola_wzorcow.jsonl", "w", encoding="utf-8") as f:
        for p in wybrane:
            f.write(json.dumps({k: p[k] for k in POLA if k in p}, ensure_ascii=False) + "\n")
    print(len(wer), "weryfikowalnych;", ile, [p["id"] for p in wybrane])


if __name__ == "__main__":
    main()
