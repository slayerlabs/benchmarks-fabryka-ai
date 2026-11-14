"""Skąd rozjazd przeliczenia niezależnego na HellaSwag (analiza po wyniku, eksploracyjna): acc_norm z pola próbki
lm_eval wobec acc_norm runnera (`metryki.oceny_mc`: loglik / długość kontynuacji BEZ wiodących spacji). Liczy oba
warianty własnym kodem z loglików i kontynuacji próbki, bez importu kodu repo.

    python diagnoza_acc_norm.py <eksport z próbkami> <wynik.json>

Dla każdego testu z acc_norm i każdej etykiety: liczba pytań, na których pole lm_eval różni się od wariantu runnera,
ile z nich ma kontynuację z więcej niż jedną wiodącą spacją, oraz Δ 1.09 − 1.08 w obu wariantach.
"""
import json
import sys
from pathlib import Path

A, B = "slayer1b-1.09-k40000", "slayer1b-1.08"
TESTY = {"arc-challenge": "T02", "hellaswag": "T05", "mathqa": "T19", "piqa": "T06"}


def argmax(x):
    return max(range(len(x)), key=lambda i: x[i])


def warianty(r):
    lls = [x[0] for x in r["filtered_resps"]]
    konty = [a[1] for a in r["arguments"]]
    gold = r["target"] if isinstance(r["target"], int) else int(r["target"])
    runner = float(argmax([ll / max(len(c.lstrip(" ")), 1) for ll, c in zip(lls, konty)]) == gold)
    pelna = float(argmax([ll / max(len(c), 1) for ll, c in zip(lls, konty)]) == gold)
    spacje = any(len(c) - len(c.lstrip(" ")) > 1 for c in konty)
    return float(r["acc_norm"]), runner, pelna, spacje


def main():
    eksport, wyj = Path(sys.argv[1]), Path(sys.argv[2])
    out = {}
    for bench, zad in TESTY.items():
        srednie = {}
        for model in (A, B):
            p = eksport / "wyniki" / bench / model / "probki" / f"{zad}_space.jsonl"
            w = [warianty(json.loads(l)) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
            n = len(w)
            rozne = [x for x in w if x[0] != x[1]]
            srednie[model] = {"n": n, "lm_eval": sum(x[0] for x in w) / n, "runner": sum(x[1] for x in w) / n,
                              "dlugosc_ze_spacja": sum(x[2] for x in w) / n,
                              "pytan_lm_eval_rozne_od_runnera": len(rozne),
                              "w_tym_z_wieloma_spacjami": sum(1 for x in rozne if x[3]),
                              "lm_eval_rowne_dlugosci_ze_spacja": sum(1 for x in w if x[0] == x[2])}
        out[bench] = {**srednie, "delta_lm_eval": srednie[A]["lm_eval"] - srednie[B]["lm_eval"],
                      "delta_runner": srednie[A]["runner"] - srednie[B]["runner"]}
    wyj.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for b, d in out.items():
        print(b, {m: (d[m]["pytan_lm_eval_rozne_od_runnera"], d[m]["w_tym_z_wieloma_spacjami"]) for m in (A, B)},
              f"Δ lm_eval {d['delta_lm_eval']:.6f}, Δ runner {d['delta_runner']:.6f}")


if __name__ == "__main__":
    main()
