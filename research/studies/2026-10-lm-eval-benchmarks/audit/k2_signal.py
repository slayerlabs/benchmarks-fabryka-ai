"""Signal (K2) of the 15 benchmarks of the full run 2026-11, for the benchmark audit of 2026-11-26 (AUDIT.md).

Input (read only), relative to the research/ directory:
  studies/2026-10-lm-eval-benchmarks/results/full-run-2026-11/{przeglad.jsonl, sizes.json, <test>/<model>/results_rozszerzone.json}
  studies/2026-10-lm-eval-benchmarks/results/central-run/<test>/<model>/probki/*.jsonl.gz (bootstrap over questions,
  tools/snr_panelu.py).

Panels:
  M  = the panel of METODOLOGIA "Panel SNR": the first MODELE block of tools/przebieg_centralny.sh without SlayerLab,
       i.e. all non-Slayer models of the run except the comparison models Bielik-11B-Instruct and LFM3-1.7B (instruct).
       This is the panel the audit's verdicts use.
  C  = M without LFM2.5-1.2B-Base, whose full-run results differ from central-run on the same weights
       (full-run README, "Do sprawdzenia").
  A  = every non-Slayer model with a result; A2 = A without LFM2.5; B = A without results flagged `do_sprawdzenia`.
       Sensitivity only.
SNR = SD(n-1) of the panel scores / mean SE of one score (SE of the decision metric from przeglad.jsonl, clustered
where the test type says so). LOO = SNR without each single model; the verdict uses the smallest LOO.
Per-question samples of the full panel are not in the repository, so the 95% bootstrap interval cannot be computed.
Informative only: (i) a parametric approximation, each score ~ N(score, SE) independently, basic interval as in
snr_panelu.py; (ii) the real bootstrap of snr_panelu.policz on the central-run sub-panel (4 models) for 6 tests.

Run from research/: python3 studies/2026-10-lm-eval-benchmarks/audit/k2_signal.py . > studies/2026-10-lm-eval-benchmarks/audit/k2_signal.json
"""
import gzip
import json
import itertools
import math
import random
import statistics
import sys
from pathlib import Path

ZIARNO = 20261107
POWT = 2000
TESTY = ["arc-challenge", "arc-easy", "blimp", "ewok", "hellaswag", "lambada", "mathqa", "medmcqa",
         "multiblimp-pl", "piqa", "pubmedqa", "social-iqa", "wikitext-2", "winogrande", "wsc273"]
MALY = 2.0e9
# central-run: plik próbek, pole metryki decyzyjnej, klaster (typ testu z README.md tego studium, "Benchmarki i typy")
CENTRAL = {"arc-challenge": ("T02_space", "acc_norm", None), "blimp": ("T01_space", "acc", "UID"),
           "medmcqa": ("T45_space", "acc", None), "multiblimp-pl": ("T04_space", "acc", None),
           "pubmedqa": ("T44_space", "acc", None), "social-iqa": ("T46_space", "acc", None)}
CENTRAL_PANEL = ["eurollm-1.7b", "lfm2.5-1.2b-base", "lfm3-1.7b-base", "qwen3.5-0.8b-base"]


def snr(v, se):
    return statistics.stdev(v) / statistics.fmean(se)


def loo(modele, v, se):
    out = {}
    for i, m in enumerate(modele):
        vv = v[:i] + v[i + 1:]
        ss = se[:i] + se[i + 1:]
        out[m] = snr(vv, ss)
    return out


def param_basic(v, se, powt=POWT, ziarno=ZIARNO):
    """Basic interval [2θ − q97.5, 2θ − q2.5] z losowań wynik_i ~ N(v_i, se_i), niezależnie (rho = 0)."""
    rng = random.Random(ziarno)
    theta = snr(v, se)
    proby = sorted(snr([x + rng.gauss(0, s) for x, s in zip(v, se)], se) for _ in range(powt))
    lo, hi = proby[int(0.025 * powt)], proby[int(math.ceil(0.975 * powt)) - 1]
    return [2 * theta - hi, 2 * theta - lo]


def rangi(x):
    idx = sorted(range(len(x)), key=lambda i: x[i])
    r = [0.0] * len(x)
    i = 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and x[idx[j + 1]] == x[idx[i]]:
            j += 1
        for k in range(i, j + 1):
            r[idx[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def perm_p(a, b, rho):
    """Dokładne p jednostronne P(rho_perm >= rho) po wszystkich permutacjach b (n <= 8: 40 320)."""
    trafy = sum(spearman(a, list(p)) >= rho - 1e-12 for p in itertools.permutations(b))
    return trafy / math.factorial(len(b))


def spearman(a, b):
    ra, rb = rangi(a), rangi(b)
    ma, mb = statistics.fmean(ra), statistics.fmean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den


def wariant(rows, modele):
    modele = [m for m in modele if m in rows]
    v = [rows[m]["v"] for m in modele]
    se = [rows[m]["se"] for m in modele]
    l = loo(modele, v, se)
    mn = min(l, key=l.get)
    return {"modele": modele, "n": len(modele), "sd": statistics.stdev(v), "sr_se": statistics.fmean(se),
            "snr": snr(v, se), "loo": l, "loo_min": l[mn], "loo_min_bez": mn,
            "przedzial_param_rho0": param_basic(v, se)}


def main(research):
    R = Path(research)
    fr = R / "studies/2026-10-lm-eval-benchmarks/results/full-run-2026-11"
    sys.path.insert(0, str(R / "tools"))
    import snr_panelu  # noqa: E402  (repo tool, bootstrap po pytaniach)

    sizes = json.loads((fr / "sizes.json").read_text())
    dane = {t: {} for t in TESTY}
    for line in (fr / "przeglad.jsonl").read_text().splitlines():
        r = json.loads(line)
        if r.get("benchmark") not in dane or r["model"].startswith("slayer") or r.get("wartosc") is None:
            continue
        rr = json.loads((fr / r["benchmark"] / r["model"] / "results_rozszerzone.json").read_text())
        obs = rr["observations"][0]
        assert obs["value"] == r["wartosc"] and obs["metric"] == r["metryka"], (r["benchmark"], r["model"])
        sp = obs["dodatkowe"]["space"]
        wb = sp.get("wobec_b") or {}
        dane[r["benchmark"]][r["model"]] = {
            "v": r["wartosc"], "se": r["se"], "b": r["baza_b"], "flaga": r["flaga"], "lm_eval": r.get("lm_eval"),
            "dtype": r["dtype"], "metryka": r["metryka"], "params": sizes[r["model"]]["params"],
            "wobec_b_stat": wb.get("z") if wb.get("z") is not None else wb.get("t"), "wobec_b_metoda": wb.get("metoda"),
            "bpb": sp.get("bits_per_byte")}

    out = {"testy": {}, "spearman": {}, "central_bootstrap": {}}
    for t in TESTY:
        rows = dane[t]
        ppl = t == "wikitext-2"
        proc = not ppl and max(x["v"] for x in rows.values()) > 1.5  # MultiBLiMP-PL w procentach
        skala = 100.0 if proc else 1.0
        A = sorted(rows)
        B = [m for m in A if rows[m]["flaga"] == "ok"]
        A2 = [m for m in A if m != "lfm2.5-1.2b-base"]
        M = [m for m in A if m in snr_panelu.panel_z_modele()]
        C = [m for m in M if m != "lfm2.5-1.2b-base"]
        res = {"metryka": rows[A[0]]["metryka"], "skala_proc": proc,
               "M": wariant(rows, M), "C": wariant(rows, C),
               "A": wariant(rows, A), "B": wariant(rows, B), "A2": wariant(rows, A2),
               "wyniki": {m: {k: rows[m][k] for k in ("v", "se", "flaga", "lm_eval", "dtype", "params")} for m in A}}
        if ppl:
            bpb = {m: {"v": rows[m]["bpb"]["value"], "se": rows[m]["bpb"]["se"]} for m in A}
            res["bpb_A"] = wariant(bpb, A)
            res["bpb_B"] = wariant(bpb, B)
        # małe modele nad b
        male = [m for m in A if rows[m]["params"] <= MALY]
        if not ppl:
            b = rows[A[0]]["b"] * skala
            res["b"] = b
            res["male_nad_b_prosto"] = sorted(m for m in male if rows[m]["v"] > b + 2 * rows[m]["se"])
            res["male_nad_b_parowane"] = sorted(m for m in male if (rows[m]["wobec_b_stat"] or -1) > 2)
            res["male_wobec_b_metoda"] = sorted({str(rows[m]["wobec_b_metoda"]) for m in male})
            res["male_n"] = len(male)
        # Bielik-11B wobec najlepszego <= 2B
        if "bielik-11b-v3-instruct" in rows:
            best = (min if ppl else max)(male, key=lambda m: rows[m]["v"])
            b11 = rows["bielik-11b-v3-instruct"]
            d = (rows[best]["v"] - b11["v"]) if ppl else (b11["v"] - rows[best]["v"])
            res["bielik11_vs_best_male"] = {"bielik11": b11["v"], "best": best, "best_v": rows[best]["v"],
                                            "roznica_lepiej_11b": d,
                                            "z": d / math.hypot(b11["se"], rows[best]["se"])}
        else:
            res["bielik11_vs_best_male"] = None
        out["testy"][t] = res

    # Spearman po wspólnych modelach panelu (wikitext: niżej lepiej -> odwracamy)
    for wname in ("A", "B"):
        pary = []
        for i, t1 in enumerate(TESTY):
            for t2 in TESTY[i + 1:]:
                m1 = out["testy"][t1][wname]["modele"]
                m2 = out["testy"][t2][wname]["modele"]
                wsp = [m for m in m1 if m in m2]
                s = lambda t, m: -dane[t][m]["v"] if t == "wikitext-2" else dane[t][m]["v"]
                rho = spearman([s(t1, m) for m in wsp], [s(t2, m) for m in wsp])
                p = perm_p([s(t1, m) for m in wsp], [s(t2, m) for m in wsp], rho) if rho >= 0.9 else None
                pary.append({"t1": t1, "t2": t2, "n": len(wsp), "rho": rho, "p_perm": p})
        out["spearman"][wname] = sorted(pary, key=lambda p: -p["rho"])

    # Bootstrap po pytaniach (snr_panelu.policz) na podpanelu central-run z próbkami + kalibracja przybliżenia
    for t, (pl, met, kl) in CENTRAL.items():
        katalog = R / "studies/2026-10-lm-eval-benchmarks/results/central-run" / t
        d = {m: w for m in CENTRAL_PANEL if (w := snr_panelu.wczytaj(katalog, m, pl, met, kl)) is not None}
        wyn = snr_panelu.policz(d)
        modele = sorted(d)
        v = [wyn["wyniki"][m] for m in modele]
        se = []
        for m in modele:  # SE per model tą samą metodą co narzędzie (klastry przy BLiMP)
            sumy, licz = {}, {}
            for doc, (x, c) in d[m].items():
                sumy[c] = sumy.get(c, 0.0) + x
                licz[c] = licz.get(c, 0) + 1
            k = list(sumy)
            se.append(snr_panelu._wynik_i_se([sumy[c] for c in k], [licz[c] for c in k])[1])
        wyn["kalibracja_param_rho0"] = param_basic(v, se)
        out["central_bootstrap"][t] = wyn
    return out


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), ensure_ascii=False, indent=1))
