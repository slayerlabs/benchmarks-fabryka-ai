"""Sanity check of ewaluuj.py outputs (end of a full run in przebieg_centralny.sh).

An error is: a task that did not finish, a main score of exactly 1.000, a score below the random
baseline minus 5 points, a random baseline of 1.000 (only one choice read per question), or a
perplexity that is not finite and above 1.
  python tools/kontrola_sensu.py [--tylko-stan] DIR...   (each DIR holds results_rozszerzone.json; exit 1 on any error)
--tylko-stan: only "the task finished" (stage proba_cpu: a few questions say nothing about the score).
"""
import json
import math
import sys
from pathlib import Path

MARGINES = 0.05


def bledy_obserwacji(obs, tylko_stan=False):
    """Error messages for one observation of results_rozszerzone.json (fractions, not percent)."""
    zadanie = obs.get("task_id")
    if obs.get("state") != "ok":
        return [f"{zadanie}: {obs.get('state')} {obs.get('reason', '')[:120]}"]
    if tylko_stan:
        return []
    space = (obs.get("dodatkowe") or {}).get("space") or {}
    if "byte_perplexity" in space:
        v = space["byte_perplexity"]["value"]
        return [] if v is not None and math.isfinite(v) and v > 1 else [f"{zadanie}: byte perplexity {v}"]
    klucz = "acc_norm" if obs.get("metric", "").startswith("acc_norm") else "acc"
    v = space[klucz]["value"]
    losowa = (space.get("bazy") or {}).get("chance_value")
    wynik = []
    if losowa is not None and losowa >= 1:
        wynik.append(f"{zadanie}: random baseline {losowa:.3f}, one choice per question")
    if v >= 1:
        wynik.append(f"{zadanie}: {klucz} {v:.3f}")
    if losowa is not None and v < losowa - MARGINES:
        wynik.append(f"{zadanie}: {klucz} {v:.3f} below random {losowa:.3f} - {MARGINES}")
    return wynik


def main(argv=None):
    katalogi = list(argv if argv is not None else sys.argv[1:])
    tylko_stan = "--tylko-stan" in katalogi
    katalogi = [k for k in katalogi if k != "--tylko-stan"]
    wszystkie = []
    for k in katalogi:
        plik = Path(k) / "results_rozszerzone.json"
        if not plik.exists():
            wszystkie.append(f"{k}: no results_rozszerzone.json")
            continue
        for obs in json.loads(plik.read_text())["observations"]:
            wszystkie += [f"{k} {b}" for b in bledy_obserwacji(obs, tylko_stan)]
    print("\n".join(wszystkie) if wszystkie else f"sanity OK: {len(katalogi)} outputs")
    return 1 if wszystkie else 0


if __name__ == "__main__":
    sys.exit(main())
