"""Próba dymna jednego modelu przed pełną kolejką (nie wchodzi do wyników):
1) ścieżka generacji z KV cache daje te same logity co pełny forward (logprob_ciagu) na 5 pozycjach;
2) greedy w batchu 4 vs greedy w batchu 1 na 10 pozycjach (liczba różnych odpowiedzi);
3) wyrenderowany prompt i odpowiedź 3 pozycji z różnych kategorii (do ręcznego przeczytania, METODOLOGIA p. 8).

python -I code/dym.py <model>  -> wyniki/dym_<model>.json
"""
import json
import sys
from pathlib import Path

import torch

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import generuj  # noqa: E402
import modele  # noqa: E402
import szablony  # noqa: E402


def main():
    klucz = sys.argv[1]
    pozycje, shoty = generuj.wczytaj_zestaw()
    m = modele.wczytaj(klucz)
    wyn = dict(model=klucz, cache_vs_pelny=[], batch_vs_1=[], przyklady=[])
    wybor = [pozycje[i] for i in range(0, 240, 24)]
    for p in wybor[:5]:
        ctx = szablony.prompt("A", p, shoty[p["kat"]])
        ciag = szablony.ciag_wzorca("A", p)
        lp, n, _ = modele.logprob_ciagu(m, ctx, ciag)
        ids, n_ctx, _ = modele.czesc_ciagu(m, ctx, ciag)
        logity = m.start(ids[:n_ctx], 1)
        suma = 0.0
        for t in ids[n_ctx:]:
            suma += float(torch.log_softmax(logity[0].double(), -1)[t])
            logity = m.krok([t])
        wyn["cache_vs_pelny"].append(dict(id=p["id"], pelny=lp, cache=suma, roznica=abs(lp - suma)))
    for nr, p in enumerate(wybor):
        ctx = szablony.prompt("A", p, shoty[p["kat"]])
        st = szablony.stopy("A", p["kat"])
        mx = min(szablony.MAX_TOKENOW[p["typ"]], 64)
        b4, _, _ = generuj.generuj_batch(m, ctx, generuj.DEKODOWANIA_A, nr, mx, st)
        b1, _, _ = generuj.generuj_batch(m, ctx, generuj.DEKODOWANIA_B, nr, mx, st)
        wyn["batch_vs_1"].append(dict(id=p["id"], rowne=b4[3]["surowa"] == b1[0]["surowa"]))
        if nr < 3:
            wyn["przyklady"].append(dict(id=p["id"], prompt=ctx, odpowiedzi=b4))
    wyn["max_roznica_cache"] = max(x["roznica"] for x in wyn["cache_vs_pelny"])
    wyn["rozne_batch"] = sum(not x["rowne"] for x in wyn["batch_vs_1"])
    (generuj.BADANIE / "wyniki" / f"dym_{klucz}.json").write_text(json.dumps(wyn, ensure_ascii=False, indent=1), encoding="utf-8")
    print(klucz, "max |cache - pelny| =", wyn["max_roznica_cache"], "; rozne greedy batch4 vs batch1:", wyn["rozne_batch"], "/", len(wybor))


if __name__ == "__main__":
    main()
