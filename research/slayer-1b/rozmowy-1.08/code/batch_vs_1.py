"""Greedy w batchu 4 (szablon A, jak w pomiarze) wobec greedy w batchu 1 na n pozycjach (runda poprawek 1, po pomiarze,
eksploracyjne). Pozycje: co 240/n-ta z pliku poleceń, limit nowych tokenów = limit typu (jak w pomiarze).

python -I code/batch_vs_1.py <model> <n>  -> wyniki/batch_vs_1_<model>.json
"""
import json
import sys
import time
from pathlib import Path

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import generuj  # noqa: E402
import modele  # noqa: E402
import szablony  # noqa: E402


def main():
    klucz, n = sys.argv[1], int(sys.argv[2])
    pozycje, shoty = generuj.wczytaj_zestaw()
    m = modele.wczytaj(klucz)
    krok = len(pozycje) / n
    wyn, t0 = [], time.time()
    for j in range(n):
        nr = int(j * krok)
        p = pozycje[nr]
        ctx = szablony.prompt("A", p, shoty[p["kat"]])
        st = szablony.stopy("A", p["kat"])
        mx = szablony.MAX_TOKENOW[p["typ"]]
        b4, _, _ = generuj.generuj_batch(m, ctx, generuj.DEKODOWANIA_A, nr, mx, st)
        b1, _, _ = generuj.generuj_batch(m, ctx, generuj.DEKODOWANIA_B, nr, mx, st)
        wyn.append(dict(id=p["id"], rowne=b4[3]["surowa"] == b1[0]["surowa"], tokeny_b4=b4[3]["tokeny"],
                        tokeny_b1=b1[0]["tokeny"]))
    out = dict(model=klucz, n=n, rozne=sum(not x["rowne"] for x in wyn), sekundy=round(time.time() - t0),
               eksploracyjne=True, pozycje=wyn)
    (generuj.BADANIE / "wyniki" / f"batch_vs_1_{klucz}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                                                       encoding="utf-8")
    print(klucz, "rozne:", out["rozne"], "/", n, "czas s:", out["sekundy"])


if __name__ == "__main__":
    main()
