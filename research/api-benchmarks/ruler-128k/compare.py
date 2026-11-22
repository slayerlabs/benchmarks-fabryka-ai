"""Hypotheses R1-R3 and the control of PROTOCOL.md, from the per-sample results of every model.

Usage: python3 compare.py   (reads results/<model-id>.json and .jsonl.gz, writes results/hypotheses.json)

- Control: Qwen3.5-9B's mean at 131072 against its card value 87.11; PASS when |z| < 2. Without a PASS the
  hypotheses are printed but not read.
- R1: LFM3-1.7B's mean at 131072 against 85.6. Confirmed: z <= -3 (after Holm); refuted: mean >= 85.6.
- R2: slope of the per-length mean against log2(length), LFM3-1.7B minus Qwen3.5-4B and minus Qwen3.5-9B.
  Confirmed: both differences negative, clear after Holm; refuted: neither is 2 SE below 0.
- R3: LFM3-1.7B's drop from 4096 to 131072 per category; tracing minus retrieval and aggregation minus retrieval.
  Confirmed: both positive, clear after Holm; refuted: the retrieval drop is not smaller than both.

z = value / SE, two-sided normal p, Holm over the three hypotheses with m = 3 whether or not they ran. Verdict from
the Holm-adjusted p at the p of |z| = 3 (clear) and |z| = 2 (likely), else noise. R2 and R3 combine two comparisons;
the weaker one (in the predicted direction) is the hypothesis's z. SEs come from one bootstrap per model: samples
resampled within each task and length, 10 000 resamples, seed fixed per model. Errors (score null) are left out
and counted, never scored as 0; a length that is null for a model is left out and listed.
"""

import gzip
import json
import math
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import statystyka  # noqa: E402  (Holm, p from z and t, clustered SE; shared with the other research reports)
from summarize import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, CATEGORIES, HEADLINE_LENGTH, LENGTHS, TASKS  # noqa: E402

LFM3, QWEN_4B, QWEN_9B = "lfm3-1.7b", "qwen3.5-4b", "qwen3.5-9b"
DESCRIPTIVE = ["bielik-11b-v3.1-vllm", "slayer1b-1.08"]
CONTROL_CARD = 87.11  # Qwen3.5-9B, LFM3-1.7B card
THRESHOLD = 85.6  # Llama-2-7B at 4K, the paper's effective-length threshold
SHORT, LONG = LENGTHS[0], HEADLINE_LENGTH
M = 3  # hypotheses in the Holm family, fixed by the protocol
MIN_CLUSTERS = statystyka.MIN_KLASTROW
VERDICT = {"pewne": "clear", "prawdopodobne": "likely", "szum": "noise", statystyka.NIEROZSTRZYGALNE: "undetermined",
           None: "undetermined"}
DEVIATIONS = [
    "R2: the protocol asks for a paired bootstrap over samples, but RULER generates its data with each model's own "
    "tokenizer, so sample i of two models is a different text; the slopes get independent bootstraps per model and "
    "the SE of the difference is sqrt(SE_a^2 + SE_b^2).",
    "R3: the protocol asks for an SE clustered by task, but tracing has 1 task and aggregation 2, under the 3 "
    "clusters a clustered verdict needs; the verdict uses the sample-level bootstrap SE (tasks fixed), and the "
    "clustered SE is reported next to it, undetermined for every category with fewer than 3 tasks.",
    "R2, R3: each hypothesis compares against two references; its z is the weaker of the two comparisons "
    "(it holds only if both hold), so each hypothesis enters Holm once and m stays 3.",
]


def load(results_dir, model):
    """Scored samples per usable length and task, the excluded lengths with reasons and the error rows left out;
    None when the model has no result files."""
    summary, samples = results_dir / f"{model}.json", results_dir / f"{model}.jsonl.gz"
    if not (summary.is_file() and samples.is_file()):
        return None
    per_length = json.loads(summary.read_text(encoding="utf-8"))["other_metrics"]["per_length"]
    excluded = {}
    for length in LENGTHS:
        entry = per_length.get(str(length))
        if entry is None or entry["score"] is None:
            excluded[length] = entry["reason"] if entry else "length not in the result"
    usable = [length for length in LENGTHS if length not in excluded]
    scores = {length: {t: [] for t in TASKS} for length in usable}
    errors = {length: 0 for length in usable}
    with gzip.open(samples, "rt", encoding="utf-8") as f:
        for row in map(json.loads, f):
            if row["length"] not in scores:
                continue
            if row["score"] is None:
                errors[row["length"]] += 1
            else:
                scores[row["length"]][row["task"]].append(row["score"])
    for length in usable:
        missing = [t for t, s in scores[length].items() if not s]
        if missing:
            excluded[length] = f"no scored sample in {', '.join(missing)}"
            del scores[length], errors[length]
            continue
        mean = length_mean({t: statistics.fmean(s) for t, s in scores[length].items()})
        if abs(mean - per_length[str(length)]["score"]) > 0.01:
            raise SystemExit(f"compare.py: {model} @ {length}: samples average {mean:.4f}, "
                             f"{summary.name} says {per_length[str(length)]['score']}")
    return {"scores": scores, "excluded": excluded, "errors": errors}


def length_mean(task_means):
    return statistics.fmean(task_means[t] for t in TASKS)


def category_mean(task_means, category):
    return statistics.fmean(task_means[t] for t in CATEGORIES[category])


def bootstrap(scores, resamples, seed):
    """length -> task -> resampled task means (samples drawn with replacement within the task)."""
    rng = random.Random(seed)
    return {length: {t: [statistics.fmean(rng.choices(s, k=len(s))) for _ in range(resamples)]
                     for t, s in by_task.items()} for length, by_task in scores.items()}


def point(scores):
    return {length: {t: statistics.fmean(s) for t, s in by_task.items()} for length, by_task in scores.items()}


def resample(boot, r):
    return {length: {t: means[r] for t, means in by_task.items()} for length, by_task in boot.items()}


def slope(task_means, lengths):
    xs = [math.log2(length) for length in lengths]
    ys = [length_mean(task_means[length]) for length in lengths]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def stat(fn, run):
    """fn over the point estimates and its SE over the bootstrap resamples."""
    value = fn(run["point"])
    draws = [fn(resample(run["boot"], r)) for r in range(run["resamples"])]
    return value, statistics.stdev(draws)


def z_of(value, se):
    return value / se if se > 0 else None


def n_scored(run, lengths):
    return sum(len(s) for length in lengths for s in run["scores"][length].values())


def comparison(label, value, se, n):
    z = z_of(value, se)
    return {"comparison": label, "value": value, "se": se, "z": z, "p": statystyka.p_z(z), "n": n}


def control(runs):
    run = runs.get(QWEN_9B)
    if run is None:
        return {"status": "not run", "missing": [QWEN_9B]}
    if LONG not in run["point"]:
        return {"status": "not run", "missing": [f"{QWEN_9B} @ {LONG}: {run['excluded'][LONG]}"]}
    mean, se = stat(lambda p: length_mean(p[LONG]), run)
    z = z_of(mean - CONTROL_CARD, se)
    return {"status": "PASS" if z is not None and abs(z) < 2 else "FAIL", "mean": mean, "se": se, "card": CONTROL_CARD,
            "z": z, "n": n_scored(run, [LONG])}


def missing(runs, models, lengths):
    out = [m for m in models if runs.get(m) is None]
    for m in models:
        if runs.get(m) is not None:
            out += [f"{m} @ {length}: {runs[m]['excluded'][length]}" for length in lengths if length in runs[m]["excluded"]]
    return out


def r1(runs):
    if gone := missing(runs, [LFM3], [LONG]):
        return {"missing": gone}
    run = runs[LFM3]
    mean, se = stat(lambda p: length_mean(p[LONG]), run)
    c = comparison(f"LFM3 mean @ {LONG} - {THRESHOLD}", mean - THRESHOLD, se, n_scored(run, [LONG]))
    effective = [length for length in run["point"] if length_mean(run["point"][length]) >= THRESHOLD]
    return {"measure": f"LFM3 mean @ {LONG} vs {THRESHOLD}", "value": mean, "se": se, "z": c["z"], "p": c["p"],
            "n": c["n"], "comparisons": [c], "refuted": mean >= THRESHOLD, "confirmed_direction": mean < THRESHOLD,
            "effective_length": max(effective, default=None)}


def r2(runs):
    if gone := missing(runs, [LFM3, QWEN_4B, QWEN_9B], []):
        return {"missing": gone}
    comps, slopes, excluded = [], {}, {}
    for ref in (QWEN_4B, QWEN_9B):
        lengths = [length for length in LENGTHS if length in runs[LFM3]["point"] and length in runs[ref]["point"]]
        excluded[ref] = [length for length in LENGTHS if length not in lengths]
        if len(lengths) < 3:
            return {"missing": [f"{LFM3} vs {ref}: fewer than 3 lengths measured by both"]}
        s_l, se_l = stat(lambda p: slope(p, lengths), runs[LFM3])
        s_r, se_r = stat(lambda p: slope(p, lengths), runs[ref])
        slopes[f"{LFM3} (lengths shared with {ref})"] = {"slope": s_l, "se": se_l}
        slopes[ref] = {"slope": s_r, "se": se_r}
        comps.append(comparison(f"slope {LFM3} - {ref}", s_l - s_r, math.hypot(se_l, se_r),
                                n_scored(runs[LFM3], lengths) + n_scored(runs[ref], lengths)))
    return combine("slope per doubling, LFM3 - Qwen3.5 (weaker of 4B, 9B)", comps, sign=-1,
                   slopes=slopes, lengths_excluded=excluded)


def r3(runs):
    if gone := missing(runs, [LFM3], [SHORT, LONG]):
        return {"missing": gone}
    run = runs[LFM3]

    def drop(p, category):
        return category_mean(p[SHORT], category) - category_mean(p[LONG], category)

    drops = {}
    for c, tasks in CATEGORIES.items():
        value, se = stat(lambda p: drop(p, c), run)
        task_drops = [run["point"][SHORT][t] - run["point"][LONG][t] for t in tasks]
        k = statystyka.klastrowe_wazone([(1, d) for d in task_drops])  # equal weights: the unweighted task mean
        drops[c] = {"drop": value, "se_sample": se, "z_sample": z_of(value, se), "tasks": len(tasks),
                    "se_clustered": k["se"], "t_clustered": k["t"], "df": k["df"],
                    "verdict_clustered": VERDICT[k["werdykt"]] if len(tasks) >= MIN_CLUSTERS else "undetermined"}
    comps = []
    for other in ("tracing", "aggregation"):
        value, se = stat(lambda p: drop(p, other) - drop(p, "retrieval"), run)
        comp = comparison(f"drop {other} - drop retrieval", value, se, n_scored(run, [SHORT, LONG]))
        comp["verdict_clustered"] = clustered_difference(drops[other], drops["retrieval"])
        comps.append(comp)
    return combine("LFM3 drop 4096->131072: tracing, aggregation - retrieval (weaker)", comps, sign=1, drops=drops)


def clustered_difference(a, b):
    """Clustered verdict of a difference of two category drops; undetermined when one has fewer than 3 tasks."""
    if min(a["tasks"], b["tasks"]) < MIN_CLUSTERS or not (a["se_clustered"] or b["se_clustered"]):
        return "undetermined"
    t = (a["drop"] - b["drop"]) / math.hypot(a["se_clustered"], b["se_clustered"])
    return VERDICT[statystyka.werdykt_t(t, min(a["tasks"], b["tasks"]) - 1)]


def combine(measure, comps, sign, **extra):
    """Both comparisons must go in the predicted direction (sign): the hypothesis's z is the weaker one."""
    weakest = min(comps, key=lambda c: math.inf if c["z"] is None else sign * c["z"])
    if sign < 0:  # R2: refuted when neither difference is 2 SE below 0
        refuted = all(c["z"] is None or c["z"] > -2 for c in comps)
    else:  # R3: refuted when the retrieval drop is not smaller than both other drops
        refuted = not all(c["value"] > 0 for c in comps)
    return {"measure": measure, "value": weakest["value"], "se": weakest["se"], "z": weakest["z"],
            "p": weakest["p"], "n": weakest["n"], "comparisons": comps, "refuted": refuted,
            "confirmed_direction": all(c["value"] * sign > 0 for c in comps), **extra}


def analyse(results_dir, resamples):
    runs = {}
    for model in [LFM3, QWEN_4B, QWEN_9B, *DESCRIPTIVE]:
        run = load(results_dir, model)
        if run is not None and model not in DESCRIPTIVE:
            run.update(point=point(run["scores"]), resamples=resamples,
                       boot=bootstrap(run["scores"], resamples, f"{BOOTSTRAP_SEED}:{model}"))
        elif run is not None:
            run["point"] = point(run["scores"])
        runs[model] = run
    hyps = {"R1": r1(runs), "R2": r2(runs), "R3": r3(runs)}
    adjusted = statystyka.holm([h.get("p") for h in hyps.values()], m=M)
    for h, p_holm in zip(hyps.values(), adjusted):
        if "missing" in h:
            h.update(verdict="not run", outcome="not run")
            continue
        h["p_holm"] = p_holm
        h["verdict"] = VERDICT[statystyka.werdykt_p(p_holm)] if p_holm is not None else "undetermined"
        h["outcome"] = ("refuted" if h["refuted"] else
                        "confirmed" if h["verdict"] == "clear" and h["confirmed_direction"] else "open")
    descriptive = {m: None if run is None else {
        "per_length": {str(length): round(length_mean(run["point"][length]), 2) if length in run["point"] else None
                       for length in LENGTHS},
        "excluded_lengths": {str(k): v for k, v in sorted(run["excluded"].items())},
        "errors_excluded": {str(k): v for k, v in run["errors"].items() if v}} for m, run in runs.items()}
    return {"control": control(runs), "hypotheses": hyps, "holm_m": M, "models": descriptive,
            "deviations": DEVIATIONS, "bootstrap": {"resamples": resamples, "seed": f"{BOOTSTRAP_SEED}:<model-id>"}}


def fmt(x, digits=2):
    return "-" if x is None else f"{x:.{digits}f}"


def fmt_p(p):
    return "-" if p is None else f"{p:.2g}" if p < 1e-3 else f"{p:.4f}"


def report(result):
    lines = [f"deviation: {d}" for d in result["deviations"]]
    c = result["control"]
    if c["status"] == "not run":
        lines.append(f"control: not run (missing: {', '.join(c['missing'])}); hypotheses not read until it passes")
    else:
        lines.append(f"control: Qwen3.5-9B @ {LONG} = {c['mean']:.2f} +- {c['se']:.2f} vs card {c['card']}, "
                     f"z = {fmt(c['z'])}: {c['status']}")
        if c["status"] == "FAIL":
            lines.append("control FAIL: hypotheses not read until explained")
    for model, d in result["models"].items():
        if d is None:
            continue
        for length, reason in d["excluded_lengths"].items():
            lines.append(f"excluded: {model} @ {length}: {reason}")
        if d["errors_excluded"]:
            lines.append(f"errors left out: {model}: "
                         + ", ".join(f"{n} @ {length}" for length, n in d["errors_excluded"].items()))
    lines += ["", "| hypothesis | measure | value +- SE | z | Holm p | verdict | outcome | n |",
              "|---|---|---|---|---|---|---|---|"]
    for name, h in result["hypotheses"].items():
        if "missing" in h:
            lines.append(f"| {name} | missing: {', '.join(h['missing'])} | - | - | - | not run | not run | - |")
            continue
        lines.append(f"| {name} | {h['measure']} | {h['value']:.2f} +- {h['se']:.2f} | {fmt(h['z'])} | "
                     f"{fmt_p(h['p_holm'])} | {h['verdict']} | {h['outcome']} | {h['n']} |")
    comps = [(name, c) for name, h in result["hypotheses"].items() for c in h.get("comparisons", [])]
    if comps:
        lines += ["", "| hypothesis | comparison | value +- SE | z | p (unadjusted) | n |", "|---|---|---|---|---|---|"]
        lines += [f"| {name} | {c['comparison']} | {c['value']:.2f} +- {c['se']:.2f} | {fmt(c['z'])} | "
                  f"{fmt_p(c['p'])} | {c['n']} |" for name, c in comps]
    r1_ = result["hypotheses"]["R1"]
    if "effective_length" in r1_:
        lines.append(f"\nLFM3-1.7B effective length (longest length with mean >= {THRESHOLD}): "
                     f"{r1_['effective_length'] or 'none'}")
    r3_ = result["hypotheses"]["R3"]
    if "drops" in r3_:
        lines += ["", "| LFM3 category | drop 4096->131072 | SE sample | SE clustered (tasks) | clustered verdict |",
                  "|---|---|---|---|---|"]
        lines += [f"| {c} | {d['drop']:.2f} | {d['se_sample']:.2f} | {fmt(d['se_clustered'])} ({d['tasks']}) | "
                  f"{d['verdict_clustered']} |" for c, d in r3_["drops"].items()]
    lines += ["", "| model | " + " | ".join(map(str, LENGTHS)) + " |", "|---" * (len(LENGTHS) + 1) + "|"]
    for model, d in result["models"].items():
        cells = ["not run"] * len(LENGTHS) if d is None else [fmt(d["per_length"][str(x)]) for x in LENGTHS]
        lines.append(f"| {model} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main(results_dir=HERE / "results", resamples=BOOTSTRAP_RESAMPLES):
    result = analyse(Path(results_dir), resamples)
    print(report(result))
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    (Path(results_dir) / "hypotheses.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
