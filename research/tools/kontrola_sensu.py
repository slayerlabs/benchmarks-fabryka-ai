"""Sanity check of ewaluuj.py outputs (end of a full run in przebieg_centralny.sh).

An error is: a task that did not finish, a main score of exactly 1.000, a score below the random
baseline minus 5 points (not for MCC, which may be negative), a random baseline of 1.000 (only one
choice read per question), or a perplexity that is not finite and above 1. The main score is
acc/acc_norm, or `dodatkowe.space.glowna` for the other metrics (exact_match, f1, mcc, levenshtein, ...).
  python tools/kontrola_sensu.py [--tylko-stan] DIR...   (each DIR holds results_rozszerzone.json; exit 1 on any error)
--tylko-stan: only "the task finished" (stage proba_cpu: a few questions say nothing about the score).

Separately each score gets the control of the METODOLOGIA type table, score > b + 2 SE (`na_poziomie_bazy`). A score
that fails it is listed as "at baseline level", not an error: the run is fine, the card then says the test does not
tell this model from b, and the exit code does not change.
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
    if "glowna" in space:  # generation, mass, corpus metrics (exact_match, f1, mcc, levenshtein, ...)
        klucz, v = space["glowna"].get("metryka", "glowna"), space["glowna"].get("value")
    else:
        klucz = "acc_norm" if obs.get("metric", "").startswith("acc_norm") else "acc"
        v = space[klucz]["value"]
    if v is None or not math.isfinite(v):
        return [f"{zadanie}: {klucz} {v}"]
    # MCC may be negative: its random level 0 is not a floor
    losowa = None if klucz == "mcc" else (space.get("bazy") or {}).get("chance_value")
    wynik = []
    if losowa is not None and losowa >= 1:
        wynik.append(f"{zadanie}: random baseline {losowa:.3f}, one choice per question")
    if v >= 1:
        wynik.append(f"{zadanie}: {klucz} {v:.3f}")
    if losowa is not None and v < losowa - MARGINES:
        wynik.append(f"{zadanie}: {klucz} {v:.3f} below random {losowa:.3f} - {MARGINES}")
    return wynik


DALEJ_NIZ_SZUM = ("pewne", "prawdopodobne")


def na_poziomie_bazy(obs):
    """Control column of the METODOLOGIA type table: score > b + 2 SE, b = the higher of the random baseline and the
    constant answer. MC outputs carry `wobec_b` (common/ewaluuj.wobec_b: paired with the constant answer, SE K with
    `+klastry`), and the control passes when that difference is positive and pewne or prawdopodobne. Other outputs:
    b from `bazy` and the SE of the main metric. With a `podzbior` (SQuAD2: HasAns) b and the control use the subset,
    as the `ciagla` row says. A failing score gives a message, a passing one, perplexity or a missing SE gives None."""
    if obs.get("state") != "ok":
        return None
    space = (obs.get("dodatkowe") or {}).get("space") or {}
    if "byte_perplexity" in space:
        return None
    wb = space.get("wobec_b")
    if wb:
        if "roznica" not in wb:  # fewer than 2 questions: nothing to check
            return None
        if wb["roznica"] > 0 and wb.get("werdykt") in DALEJ_NIZ_SZUM:
            return None
        stat = (f"t {wb['t']:.2f} df {wb['df']}" if wb.get("t") is not None
                else f"z {wb['z']:.2f}" if wb.get("z") is not None else "no z")
        return (f"{obs.get('task_id')}: {wb['roznica']:+.4f} vs b {wb['b']:.4f} ({wb['baza']}), {stat}, "
                f"{wb.get('werdykt')}, at baseline level")
    zrodlo = space.get("podzbior") or space
    if "glowna" in zrodlo:
        klucz, glowna = zrodlo["glowna"].get("metryka", "glowna"), zrodlo["glowna"]
    else:
        klucz = "acc_norm" if obs.get("metric", "").startswith("acc_norm") else "acc"
        glowna = zrodlo.get(klucz) or {}
    bazy = [v for v in ((zrodlo.get("bazy") or {}).get(k) for k in ("chance_value", "majority_value")) if v is not None]
    v, se = glowna.get("value"), glowna.get("se")
    if v is None or se is None or not bazy:
        return None
    b = max(bazy)
    if v > b + 2 * se:
        return None
    return f"{obs.get('task_id')}: {klucz} {v:.4f} <= b {b:.4f} + 2 SE ({se:.4f}), at baseline level"


def main(argv=None):
    katalogi = list(argv if argv is not None else sys.argv[1:])
    tylko_stan = "--tylko-stan" in katalogi
    katalogi = [k for k in katalogi if k != "--tylko-stan"]
    wszystkie, flagi = [], []
    for k in katalogi:
        plik = Path(k) / "results_rozszerzone.json"
        if not plik.exists():
            wszystkie.append(f"{k}: no results_rozszerzone.json")
            continue
        for obs in json.loads(plik.read_text())["observations"]:
            wszystkie += [f"{k} {b}" for b in bledy_obserwacji(obs, tylko_stan)]
            flaga = None if tylko_stan else na_poziomie_bazy(obs)
            if flaga:
                flagi.append(f"{k} {flaga}")
    print("\n".join(wszystkie) if wszystkie else f"sanity OK: {len(katalogi)} outputs")
    if flagi:
        print(f"at baseline level (score <= b + 2 SE, not an error): {len(flagi)}\n" + "\n".join(flagi))
    return 1 if wszystkie else 0


if __name__ == "__main__":
    sys.exit(main())
