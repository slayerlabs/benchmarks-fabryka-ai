"""Wynik kontroli narzędzia (PROTOKOL.md, sekcja 6) z wyniki/surowe/kontrola_slayer.jsonl -> wyniki/kontrola.json.

Wartości referencyjne czytane z EVALUATION.json karty 1.08 (models/1.08/tasks), warunek |różnica| <= 0,02.
python -I code/podsumuj_kontrole.py <EVALUATION.json>
"""
import json
import math
import sys
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
PROG = 0.02


def main():
    ev = json.loads(Path(sys.argv[1]).read_text())["models"]["1.08"]["tasks"]
    rows = [json.loads(x) for x in (BADANIE / "wyniki/surowe/kontrola_slayer.jsonl").read_text().splitlines()][1:]
    wynik = {}
    for zad in ("arc_challenge", "openbookqa"):
        r = [x for x in rows if x["zadanie"] == zad]
        wynik[zad] = {"n": len(r), "n_referencji": ev[zad]["n"]}
        for met in ("acc", "acc_norm"):
            p = sum(x[met] for x in r) / len(r)
            se = math.sqrt(p * (1 - p) / len(r))
            ref = ev[zad][met]
            wynik[zad][met] = dict(nasz=p, se=se, referencja=ref, roznica=p - ref,
                                   odtworzone=abs(p - ref) <= PROG)
    wynik["warunek"] = f"|roznica| <= {PROG} dla kazdej wartosci"
    wynik["wszystkie_odtworzone"] = all(wynik[z][m]["odtworzone"] for z in ("arc_challenge", "openbookqa") for m in ("acc", "acc_norm"))
    (BADANIE / "wyniki" / "kontrola.json").write_text(json.dumps(wynik, indent=1))
    print(json.dumps(wynik, indent=1))


if __name__ == "__main__":
    main()
