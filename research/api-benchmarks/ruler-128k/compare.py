"""Hypotheses R1-R3 and the control of PROTOCOL.md (as amended), from the per-sample results of every model.

Usage: python3 compare.py   (reads results/<model-id>.json and .jsonl.gz, writes results/hypotheses.json)

Before reading, the sha256 of each model's result files is checked against results/results.sha256.json (written by
summarize.py); a mismatch stops. A result file not listed there is recorded now and named in `warnings`.
hypotheses.json carries the sha256 of every input and the commit, runner sha256 and machine of this run.

- Control (Amendment 1): LFM3-1.7B's mean at 131072 against its card value 65.56; PASS when |z| < 2, else FAIL with
  the gap unexplained (PROTOCOL.md, Control: no hypothesis is read until it is explained). Amendment 4 (decided after
  the result, when the control had failed) labels the card value `not comparable` and reads R1-R3 anyway; the
  status says that, it does not turn the FAIL into a pass.
- Amendment 4: every score twice, as pre-registered (whole text scored when there is no `</think>`) and strict (an
  output without `</think>` scores 0, from summarize.py's `other_metrics.strict` and the rows' `closed_think`).
  Verdicts come from the pre-registered scores; the strict verdict (its own Holm family, m = 3) is shown next to each.
- R1: LFM3-1.7B's mean at 131072 against 85.6. Confirmed: z <= -3 (after Holm); refuted: mean >= 85.6. Next to the
  pre-registered rule (sample-level SE), not replacing it: the same difference with the SE clustered by task, a sign
  test over the 13 tasks, the mean without the 2 lowest tasks, and the effective length with the z of each length.
- R2 (Amendment 1): slope of the per-length mean against log2(length), LFM3-1.7B minus Bielik 11B v3.1, over the
  lengths both models hold. Confirmed: negative, clear after Holm; refuted: not 2 SE below 0. Amendment 6: with
  fewer than 3 complete lengths shared it is `not decided` (still in Holm's m = 3) and the per-length means of both
  models over the lengths both measured (partial ones with their task count) are printed, descriptive only.
- R3: LFM3-1.7B's drop from 4096 to 131072 per category; tracing minus retrieval and aggregation minus retrieval,
  with the SE clustered by task that the protocol names (PROTOCOL.md, R3). A comparison whose categories have fewer
  than 3 tasks (tracing 1, aggregation 2) has no clustered verdict: R3 is then `undetermined` and enters Holm without
  a p (m stays 3). Its t uses the between-task SE of the categories that have one (one task: no spread, taken as 0)
  with df = tasks - 1 of the smallest of them, reported next to the verdict. The sample-level bootstrap comparison
  (tasks fixed) is reported as `descriptive_sample`, not as the verdict. Confirmed: both positive, clear after Holm;
  refuted: the retrieval drop is not smaller than both, read with the same clustered verdict.
- Slayer 1B 1.09 at update 70 000 (Amendment 2): per length, descriptive only.

z = value / SE, two-sided normal p, Holm over the three hypotheses with m = 3 whether or not they ran. Verdict from
the Holm-adjusted p at the p of |z| = 3 (clear) and |z| = 2 (likely), else noise. R3 combines two comparisons; the
weaker one (in the predicted direction) is the hypothesis's t. SEs come from one bootstrap per model (independent
per model, Amendment 1): samples resampled within each task and length, 10 000 resamples, seed fixed per model.
Errors (score null) are left out and counted, never scored as 0; a length that is null for a model is left out and
listed.
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
import provenance  # noqa: E402

LFM3, BIELIK, SLAYER = "lfm3-1.7b", "bielik-11b-v3.1", "slayer1b-1.09-k70000"
DESCRIPTIVE = [SLAYER]
CONTROL_CARD = 65.56  # LFM3-1.7B card, RULER 128K (PROTOCOL.md, Amendment 1)
CONTROL_FAIL = "FAIL, gap unexplained"
R2_NOT_DECIDED = "not decided (Amendment 6): fewer than 3 complete lengths shared"
R2_NOT_COMPARABLE = "not comparable: the RULER source files differ between the models"
R2_CAVEATS = [
    "a comparison of modes, not of models: LFM3-1.7B reasons before it answers (its generation prompt opens "
    "`<think>`, output up to the rest of its window, vLLM), Bielik 11B v3.1 answers without reasoning (its template "
    "closes `<think></think>`) through the Fabryka AI API with a hidden provider system prompt",
    "RULER counts each length with the model's own tokenizer, so one nominal length holds a different amount of text "
    "per model (diagnostics.json, input_text)",
]
CONTROL_READING = ("R1-R3 are read under Amendment 4, against the protocol's rule that no hypothesis is read until the "
                   "gap is explained (PROTOCOL.md, Control)")
CONTROL_LABEL = ("Amendment 4 labels the card value `not comparable` because the card states no RULER setup (harness, "
                 "thinking mode, samples, output cap; card @ 1da06bec line 536 gives only serving and sampling "
                 "defaults); the label was added after the control had failed")
THRESHOLD = 85.6  # Llama-2-7B at 4K, the paper's effective-length threshold
SHORT, LONG = LENGTHS[0], HEADLINE_LENGTH
M = 3  # hypotheses in the Holm family, fixed by the protocol
MIN_CLUSTERS = statystyka.MIN_KLASTROW
VERDICT = {"pewne": "clear", "prawdopodobne": "likely", "szum": "noise", statystyka.NIEROZSTRZYGALNE: "undetermined",
           None: "undetermined"}
DEVIATIONS = [
    "control, R1-R3: a length where RULER's generator could not produce some task (partial length, the task is null) "
    "is not comparable: the control and R1 at 131072 are `not run` there, and R2 and R3 use only lengths complete "
    "for the compared models.",
    "R3: the verdict uses the SE clustered by task, as the protocol says. Tracing has 1 task and aggregation 2, under "
    "the 3 clusters a clustered verdict needs, so R3 is `undetermined` and enters Holm without a p (m stays 3). Its "
    "t (the between-task SE of the categories that have one, df = tasks - 1) is reported next to it; the sample-level "
    "bootstrap comparison (tasks fixed) is descriptive only. Until the verification of 2026-11-22 the verdict used the "
    "sample-level SE (Amendment 7).",
    "R3: the hypothesis compares two categories against retrieval; its t is the weaker of the two comparisons "
    "(it holds only if both hold), so it enters Holm once and m stays 3.",
    "control (Amendment 4, decided after the result and after the control failed): the control failed and the gap is "
    "unexplained; Amendment 4 labels the card value `not comparable` and R1-R3 are read under it, against the "
    "protocol's rule that no hypothesis is read until the gap is explained. Every score is also given under strict "
    "scoring (an output without `</think>` scores 0); verdicts stay on the pre-registered scoring with the strict "
    "verdict next to each.",
]


def load(results_dir, model, strict=False):
    """Scored samples per usable length and task, the excluded lengths with reasons, the partial lengths and the
    error rows left out; None when the model has no result files, or with `strict` when the strict variant does not
    apply to it (Amendment 4: an output without `</think>` scores 0; summarize.py `other_metrics.strict`).

    A partial length (RULER could not generate some task there, summarize.py `partial`) is excluded: the protocol's
    measures are means over all 13 tasks, so its mean over fewer tasks is kept only as a descriptive number."""
    summary, samples = results_dir / f"{model}.json", results_dir / f"{model}.jsonl.gz"
    if not (summary.is_file() and samples.is_file()):
        return None
    result = json.loads(summary.read_text(encoding="utf-8"))
    metrics = result["other_metrics"]
    if strict:
        if not metrics.get("strict", {}).get("applies"):
            return None
        metrics = metrics["strict"]
    per_length = metrics["per_length"]
    excluded, partial = {}, {}
    for length in LENGTHS:
        entry = per_length.get(str(length))
        if entry is not None and entry.get("partial"):
            skipped = ", ".join(entry["skipped_tasks"])
            excluded[length] = f"partial: RULER could not generate {skipped}; not comparable (13-task mean undefined)"
            partial[length] = {"score": entry["score"], "skipped_tasks": sorted(entry["skipped_tasks"])}
        elif entry is None or entry["score"] is None:
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
                score = row["score"] if not strict or row["closed_think"] else 0.0
                scores[row["length"]][row["task"]].append(score)
    for length in usable:
        missing = [t for t, s in scores[length].items() if not s]
        if missing:
            excluded[length] = f"no scored sample in {', '.join(missing)}"
            del scores[length], errors[length]
            continue
        mean = length_mean({t: statistics.fmean(s) for t, s in scores[length].items()})
        if abs(mean - per_length[str(length)]["score"]) > 0.01:
            raise SystemExit(f"compare.py: {model} @ {length}{' (strict)' if strict else ''}: samples average "
                             f"{mean:.4f}, {summary.name} says {per_length[str(length)]['score']}")
    return {"scores": scores, "excluded": excluded, "errors": errors, "partial": partial,
            "data_sources": data_sources(result)}


def data_sources(result):
    """{file: sha256} of RULER's source files (essays, SQuAD, HotpotQA, word list), from the result's `data` field
    as summarize.py writes it ("...; source files sha256: name sha, name sha"); None when it has none."""
    head, sep, listed = result.get("data", "").partition("source files sha256: ")
    return dict(item.split(" ", 1) for item in listed.split(", ")) if sep and listed else None


def data_parity(runs, models):
    """Whether the compared models' RULER data came from the same source files (RULER fetches the essays live, so
    two runs can differ); `differs`: file -> model -> sha256 for every file that is not the same for all."""
    sources = {m: runs[m]["data_sources"] for m in models}
    if any(s is None for s in sources.values()):
        return {"same": None, "reason": "a result does not list the sha256 of its RULER source files"}
    files = sorted(set().union(*sources.values()))
    differs = {f: {m: sources[m].get(f) for m in models} for f in files if len({sources[m].get(f) for m in models}) > 1}
    return {"same": not differs, "differs": differs}


def parity_note(parity):
    if parity["same"] is None:
        return parity["reason"]
    return ("same RULER source files" if parity["same"] else "RULER source files differ: " + "; ".join(
        f"{f} " + ", ".join(f"{m} {sha[:8]}" for m, sha in by_model.items()) for f, by_model in parity["differs"].items())
        + " (the haystack text is not the same)")


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


def control(runs, strict_runs=None):
    """The control as measured: PASS within 2 SE of the card, else FAIL with the gap unexplained and the hypotheses
    read only under Amendment 4."""
    run = runs.get(LFM3)
    if run is None:
        return {"status": "not run", "missing": [LFM3]}
    if LONG not in run["point"]:
        return {"status": "not run", "missing": [f"{LFM3} @ {LONG}: {run['excluded'][LONG]}"]}
    mean, se = stat(lambda p: length_mean(p[LONG]), run)
    z = z_of(mean - CONTROL_CARD, se)
    passed = z is not None and abs(z) < 2
    out = {"status": "PASS" if passed else CONTROL_FAIL, "measured": "PASS" if passed else "FAIL",
           "mean": mean, "se": se, "card": CONTROL_CARD, "z": z, "n": n_scored(run, [LONG])}
    if not passed:
        out.update(reading=CONTROL_READING, amendment_4=CONTROL_LABEL)
    strict = (strict_runs or {}).get(LFM3)
    if strict is not None and LONG in strict["point"]:
        s_mean, s_se = stat(lambda p: length_mean(p[LONG]), strict)
        out["strict"] = {"mean": s_mean, "se": s_se, "z": z_of(s_mean - CONTROL_CARD, s_se)}
    return out


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
    return {"measure": f"LFM3 mean @ {LONG} vs {THRESHOLD}", "value": mean, "se": se, "z": c["z"], "p": c["p"],
            "n": c["n"], "comparisons": [c], "refuted": mean >= THRESHOLD, "confirmed_direction": mean < THRESHOLD,
            "sensitivity": r1_sensitivity(run), "effective_length": effective_length(run)}


def sign_test(k, n):
    """Two-sided binomial p of k of n under p = 1/2."""
    tail = sum(math.comb(n, i) for i in range(min(k, n - k) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def r1_sensitivity(run, drop=2):
    """Next to R1's pre-registered rule (sample-level SE): the mean at 131072 against 85.6 with the SE clustered by
    task (13 tasks, df 12), a sign test over the tasks, and the mean without the `drop` lowest tasks (bootstrap SE)."""
    tasks = run["point"][LONG]
    k = statystyka.klastrowe_wazone([(1, tasks[t] - THRESHOLD) for t in TASKS])
    below = sum(tasks[t] < THRESHOLD for t in TASKS)
    worst = sorted(TASKS, key=lambda t: (tasks[t], t))[:drop]
    rest = [t for t in TASKS if t not in worst]
    mean, se = stat(lambda p: statistics.fmean(p[LONG][t] for t in rest), run)
    return {"clustered": {"value": k["roznica"], "se": k["se"], "t": k["t"], "df": k["df"], "p": k["p_t"],
                          "verdict": VERDICT[k["werdykt"]]},
            "sign_test": {"below": below, "tasks": len(TASKS), "p": sign_test(below, len(TASKS)),
                          "verdict": VERDICT[statystyka.werdykt_p(sign_test(below, len(TASKS)))]},
            "without_lowest": {"tasks_dropped": worst, "mean": mean, "se": se, "z": z_of(mean - THRESHOLD, se),
                               "verdict": VERDICT[statystyka.werdykt(z_of(mean - THRESHOLD, se))]}}


def effective_length(run):
    """The paper's effective length (longest length whose mean is >= 85.6) with the z of every length against 85.6,
    and the longest length that is above 85.6 by at least 2 SE: the effective length is one of the two."""
    per = {}
    for length in sorted(run["point"]):
        mean, se = stat(lambda p: length_mean(p[length]), run)
        per[str(length)] = {"mean": mean, "se": se, "z": z_of(mean - THRESHOLD, se)}
    point = max((int(x) for x, v in per.items() if v["mean"] >= THRESHOLD), default=None)
    above = max((int(x) for x, v in per.items() if v["z"] is not None and v["z"] >= 2), default=None)
    return {"point": point, "z": per[str(point)]["z"] if point else None, "se": per[str(point)]["se"] if point else None,
            "above_2_se": above, "per_length": per}


def length_means(run):
    """length -> (13-task mean, None) for complete lengths, (mean of the generated tasks, skipped) for partial."""
    out = {length: (length_mean(run["point"][length]), None) for length in run["point"]}
    out.update({length: (p["score"], p["skipped_tasks"]) for length, p in run["partial"].items()})
    return out


def r2_descriptive(runs):
    """Amendment 6: per-length means of LFM3-1.7B and Bielik over every length both measured, partial ones marked
    with their task count; where one model has fewer tasks, the other's mean on the same tasks next to it.
    Descriptive only, no test statistic."""
    means = {m: length_means(runs[m]) for m in (LFM3, BIELIK)}
    out = {}
    for length in LENGTHS:
        if not all(length in means[m] for m in means):
            continue
        row = {}
        shared = [t for t in TASKS if not any(t in (means[m][length][1] or []) for m in means)]
        for m in means:
            mean, skipped = means[m][length]
            row[m] = {"mean": round(mean, 2), "tasks": len(TASKS) - len(skipped or []),
                      **({"skipped_tasks": skipped} if skipped else {})}
            if len(shared) < row[m]["tasks"] and length in runs[m]["point"]:
                row[m]["mean_on_shared_tasks"] = round(statistics.fmean(runs[m]["point"][length][t] for t in shared), 2)
                row[m]["shared_tasks"] = len(shared)
        out[str(length)] = row
    return out


def r2(runs):
    if gone := missing(runs, [LFM3, BIELIK], []):
        return {"missing": gone}
    parity = data_parity(runs, [LFM3, BIELIK])
    # The lengths both models hold (Amendment 1: 4096-32768); a length null for either model is left out.
    lengths = [length for length in LENGTHS if length in runs[LFM3]["point"] and length in runs[BIELIK]["point"]]
    context = {"lengths": lengths, "descriptive": r2_descriptive(runs), "data_parity": parity,
               "caveats": [*R2_CAVEATS, parity_note(parity)]}
    if len(lengths) < 3:  # Amendment 6: not tested on 2 lengths nor on a task subset; the means are descriptive
        return {"missing": [f"{LFM3} vs {BIELIK}: complete lengths shared: {lengths}"], "status": R2_NOT_DECIDED,
                **context}
    if parity["same"] is False:  # different haystack text: the slopes are not measured on the same data
        return {"missing": [f"{LFM3} vs {BIELIK}: {parity_note(parity)}"], "status": R2_NOT_COMPARABLE, **context}
    s_l, se_l = stat(lambda p: slope(p, lengths), runs[LFM3])
    s_b, se_b = stat(lambda p: slope(p, lengths), runs[BIELIK])
    comp = comparison(f"slope {LFM3} - {BIELIK}", s_l - s_b, math.hypot(se_l, se_b),
                      n_scored(runs[LFM3], lengths) + n_scored(runs[BIELIK], lengths))
    return combine("slope per doubling, LFM3 - Bielik", [comp], sign=-1,
                   slopes={LFM3: {"slope": s_l, "se": se_l}, BIELIK: {"slope": s_b, "se": se_b}},
                   lengths=lengths, lengths_excluded=[length for length in LENGTHS if length not in lengths],
                   data_parity=parity, caveats=context["caveats"])


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
    comps, n = [], n_scored(run, [SHORT, LONG])
    for other in ("tracing", "aggregation"):
        value, se = stat(lambda p: drop(p, other) - drop(p, "retrieval"), run)
        comps.append({"comparison": f"drop {other} - drop retrieval", "value": value, "n": n,
                      **clustered_difference(drops[other], drops["retrieval"]),
                      "sample": {"se": se, "z": z_of(value, se), "p": statystyka.p_z(z_of(value, se))}})
    # The weaker comparison in the predicted direction (both drops larger than retrieval's) is the hypothesis's t.
    weakest = min(comps, key=lambda c: math.inf if c["t"] is None else c["t"])
    determined = all(c["verdict_clustered"] != "undetermined" for c in comps)
    weakest_sample = min(comps, key=lambda c: math.inf if c["sample"]["z"] is None else c["sample"]["z"])
    return {"measure": "LFM3 drop 4096->131072: tracing, aggregation - retrieval (weaker), SE clustered by task",
            "value": weakest["value"], "se": weakest["se_clustered"], "z": None, "t": weakest["t"],
            "df": weakest["df"], "p_t": weakest["p_t"], "p": weakest["p_t"] if determined else None, "n": n,
            "comparisons": comps, "undetermined": not determined,
            "undetermined_reason": None if determined else (
                "fewer than 3 tasks in " + ", ".join(c for c in ("tracing", "aggregation")
                                                     if drops[c]["tasks"] < MIN_CLUSTERS)
                + f": no clustered verdict (PROTOCOL.md R3: SE clustered by task; {MIN_CLUSTERS} clusters needed)"),
            "refuted": not all(c["value"] > 0 for c in comps), "confirmed_direction": all(c["value"] > 0 for c in comps),
            "drops": drops,
            "descriptive_sample": {
                "note": "sample-level bootstrap SE (tasks fixed), not the protocol's SE; descriptive, not Holm-adjusted",
                "value": weakest_sample["value"], "se": weakest_sample["sample"]["se"],
                "z": weakest_sample["sample"]["z"], "p": weakest_sample["sample"]["p"],
                "verdict": VERDICT[statystyka.werdykt_p(weakest_sample["sample"]["p"])],
                "retrieval_drop_not_smaller": not all(c["value"] > 0 for c in comps)}}


def clustered_difference(a, b):
    """t of a difference of two category drops with the SE clustered by task: the between-task SEs of the categories
    that have one (a category of one task has no spread; its SE is taken as 0), df = tasks - 1 of the smallest of
    them. The verdict is undetermined when either category has fewer than 3 tasks (statystyka.MIN_KLASTROW)."""
    have = [c for c in (a, b) if c["se_clustered"] is not None]
    se = math.hypot(*(c["se_clustered"] for c in have)) if have else None
    df = min(c["tasks"] for c in have) - 1 if have else 0
    t = (a["drop"] - b["drop"]) / se if se and df > 0 else None
    p = statystyka.p_t(t, df) if t is not None else None
    small = min(a["tasks"], b["tasks"]) < MIN_CLUSTERS
    return {"se_clustered": se, "t": t, "df": df, "p_t": p, "tasks": [a["tasks"], b["tasks"]],
            "verdict_clustered": "undetermined" if small or p is None else VERDICT[statystyka.werdykt_p(p)]}


def combine(measure, comps, sign, **extra):
    """R2: the hypothesis's z is the weaker comparison in the predicted direction (sign)."""
    weakest = min(comps, key=lambda c: math.inf if c["z"] is None else sign * c["z"])
    refuted = all(c["z"] is None or c["z"] > -2 for c in comps)  # R2: refuted when no difference is 2 SE below 0
    return {"measure": measure, "value": weakest["value"], "se": weakest["se"], "z": weakest["z"],
            "p": weakest["p"], "n": weakest["n"], "comparisons": comps, "refuted": refuted,
            "confirmed_direction": all(c["value"] * sign > 0 for c in comps), **extra}


def prepared(run, model, resamples):
    """Point estimates for every model, the bootstrap for the models a hypothesis uses (not the descriptive ones)."""
    if run is not None:
        run["point"] = point(run["scores"])
        if model not in DESCRIPTIVE:
            run.update(resamples=resamples, boot=bootstrap(run["scores"], resamples, f"{BOOTSTRAP_SEED}:{model}"))
    return run


def read_hypotheses(runs):
    """R1-R3 with Holm over m = 3, verdict and outcome."""
    hyps = {"R1": r1(runs), "R2": r2(runs), "R3": r3(runs)}
    adjusted = statystyka.holm([h.get("p") for h in hyps.values()], m=M)
    for h, p_holm in zip(hyps.values(), adjusted):
        if "missing" in h:
            label = "not decided" if "status" in h else "not run"
            h.update(verdict=label, outcome=label)
            continue
        h["p_holm"] = p_holm
        if h.get("undetermined"):  # R3: no clustered verdict; the protocol's measure cannot decide it either way
            h.update(verdict="undetermined", outcome="undetermined")
            continue
        h["verdict"] = VERDICT[statystyka.werdykt_p(p_holm)] if p_holm is not None else "undetermined"
        h["outcome"] = ("refuted" if h["refuted"] else
                        "confirmed" if h["verdict"] == "clear" and h["confirmed_direction"] else "open")
    return hyps


def per_length(run):
    return {str(length): round(length_mean(run["point"][length]), 2) if length in run["point"] else None
            for length in LENGTHS}


def analyse(results_dir, resamples):
    runs, strict_runs, warnings, inputs = {}, {}, [], {}
    for model in [LFM3, BIELIK, *DESCRIPTIVE]:
        names = [f"{model}.json", f"{model}.jsonl.gz"]
        if all((results_dir / n).is_file() for n in names):
            if provenance.check(results_dir, names, provenance.RESULTS, "compare.py", add_unrecorded=True):
                warnings.append(f"{model}: result files not in {provenance.RESULTS}; their sha256 were recorded by "
                                "compare.py now, not by summarize.py when they were written")
            inputs.update(provenance.hashes(results_dir, names))
        runs[model] = prepared(load(results_dir, model), model, resamples)
        strict_runs[model] = prepared(load(results_dir, model, strict=True), model, resamples)
    hyps = read_hypotheses(runs)
    if hyps["R2"].get("data_parity", {}).get("same") is False:
        warnings.append(f"{LFM3} vs {BIELIK}: {parity_note(hyps['R2']['data_parity'])}")
    # Amendment 4: the verdicts are the pre-registered ones; the strict reading of each is shown next to it
    for name, s in read_hypotheses(strict_runs).items():
        hyps[name]["strict"] = ({k: s[k] for k in ("verdict", "outcome", "missing")} if "missing" in s
                                else {k: s[k] for k in ("value", "se", "z", "t", "df", "p_holm", "verdict", "outcome",
                                                        "n", "sensitivity", "effective_length") if k in s})
    descriptive = {m: None if run is None else {
        "per_length": per_length(run),
        "strict_per_length": None if strict_runs[m] is None else per_length(strict_runs[m]),
        "excluded_lengths": {str(k): v for k, v in sorted(run["excluded"].items())},
        "partial_lengths": {str(k): v for k, v in sorted(run["partial"].items())},
        "errors_excluded": {str(k): v for k, v in run["errors"].items() if v},
        "data_sources": run["data_sources"]} for m, run in runs.items()}
    return {"control": control(runs, strict_runs), "hypotheses": hyps, "holm_m": M, "models": descriptive,
            "deviations": DEVIATIONS, "bootstrap": {"resamples": resamples, "seed": f"{BOOTSTRAP_SEED}:<model-id>"},
            "warnings": warnings, "inputs_sha256": inputs, "provenance": provenance.machine()}


def fmt(x, digits=2):
    return "-" if x is None else f"{x:.{digits}f}"


def fmt_p(p):
    return "-" if p is None else f"{p:.2g}" if p < 1e-3 else f"{p:.4f}"


def z_or_t(h):
    """`z` of a sample-level comparison, or `t (df)` of a clustered one (R3)."""
    if h.get("z") is not None:
        return fmt(h["z"])
    return "-" if h.get("t") is None else f"t {h['t']:.2f} (df {h['df']})"


def report(result):
    lines = [f"deviation: {d}" for d in result["deviations"]] + [f"warning: {w}" for w in result["warnings"]]
    c = result["control"]
    if c["status"] == "not run":
        lines.append(f"control: not run (missing: {', '.join(c['missing'])})")
    else:
        lines.append(f"control: LFM3-1.7B @ {LONG} = {c['mean']:.2f} +- {c['se']:.2f} vs card {c['card']}, "
                     f"z = {fmt(c['z'])}: {c['measured']} (as measured)")
        if "strict" in c:
            s = c["strict"]
            lines.append(f"control, strict: LFM3-1.7B @ {LONG} = {s['mean']:.2f} +- {s['se']:.2f}, z = {fmt(s['z'])}")
        lines.append(f"control status: {c['status']}")
        if "reading" in c:
            lines += [f"control: {c['reading']}", f"control: {c['amendment_4']}"]
    for model, d in result["models"].items():
        if d is None:
            continue
        for length, reason in d["excluded_lengths"].items():
            lines.append(f"excluded: {model} @ {length}: {reason}")
        if d["errors_excluded"]:
            lines.append(f"errors left out: {model}: "
                         + ", ".join(f"{n} @ {length}" for length, n in d["errors_excluded"].items()))
    lines += ["", "| hypothesis | measure | value +- SE | z or t (df) | Holm p | verdict | outcome | n "
                  "| strict value +- SE | strict z or t | strict Holm p | strict verdict | strict outcome |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, h in result["hypotheses"].items():
        s = h["strict"]
        strict = (f"- | - | - | {s['verdict']} | {s['outcome']}" if "missing" in s else
                  f"{s['value']:.2f} +- {fmt(s['se'])} | {z_or_t(s)} | {fmt_p(s['p_holm'])} | {s['verdict']} | "
                  f"{s['outcome']}")
        if "status" in h:
            lines.append(f"| {name} | {h['status']} | - | - | - | {h['verdict']} | {h['outcome']} | - | {strict} |")
            continue
        if "missing" in h:
            lines.append(f"| {name} | missing: {', '.join(h['missing'])} | - | - | - | not run | not run | - | {strict} |")
            continue
        lines.append(f"| {name} | {h['measure']} | {h['value']:.2f} +- {fmt(h['se'])} | {z_or_t(h)} | "
                     f"{fmt_p(h['p_holm'])} | {h['verdict']} | {h['outcome']} | {h['n']} | {strict} |")
    r2_ = result["hypotheses"]["R2"]
    if "descriptive" in r2_:
        lines += ["", f"R2 descriptive only (Amendment 6, no test statistic): per-length means over the lengths both "
                      f"models measured; complete for both: {', '.join(map(str, r2_['lengths'])) or 'none'}",
                  f"| length | {LFM3} | {BIELIK} |", "|---|---|---|"]
        for length, d in r2_["descriptive"].items():
            cells = [f"{d[m]['mean']:.2f}" + (f" ({d[m]['tasks']} tasks, no {', '.join(d[m]['skipped_tasks'])})"
                                              if "skipped_tasks" in d[m] else "")
                     + (f"; {d[m]['mean_on_shared_tasks']:.2f} on the same {d[m]['shared_tasks']} tasks"
                        if "mean_on_shared_tasks" in d[m] else "") for m in (LFM3, BIELIK)]
            lines.append(f"| {length} | " + " | ".join(cells) + " |")
        lines += [f"R2 caveat: {c}" for c in r2_["caveats"]]
    comps = [(name, c) for name, h in result["hypotheses"].items() for c in h.get("comparisons", [])]
    if comps:
        lines += ["", "| hypothesis | comparison | value +- SE | z or t (df) | p (unadjusted) | n |",
                  "|---|---|---|---|---|---|"]
        for name, c in comps:
            if "se_clustered" in c:  # R3: SE clustered by task, the sample-level SE descriptive next to it
                lines.append(f"| {name} | {c['comparison']} (SE clustered by task, tasks {c['tasks']}) | "
                             f"{c['value']:.2f} +- {fmt(c['se_clustered'])} | {z_or_t(c)} | {fmt_p(c['p_t'])} | "
                             f"{c['n']} |")
                s = c["sample"]
                lines.append(f"| {name} | {c['comparison']} (sample-level SE, descriptive) | {c['value']:.2f} +- "
                             f"{fmt(s['se'])} | {fmt(s['z'])} | {fmt_p(s['p'])} | {c['n']} |")
            else:
                lines.append(f"| {name} | {c['comparison']} | {c['value']:.2f} +- {c['se']:.2f} | {fmt(c['z'])} | "
                             f"{fmt_p(c['p'])} | {c['n']} |")
    r1_ = result["hypotheses"]["R1"]
    if "effective_length" in r1_:
        e, s = r1_["effective_length"], r1_["sensitivity"]
        lines.append(f"\nLFM3-1.7B effective length (longest length with mean >= {THRESHOLD}): {e['point'] or 'none'}"
                     f" (z = {fmt(e['z'])} against {THRESHOLD}); longest length at least 2 SE above it: "
                     f"{e['above_2_se'] or 'none'}")
        lines.append("LFM3 mean vs 85.6 per length: " + ", ".join(f"{x}: {v['mean']:.2f} +- {v['se']:.2f}, z = "
                                                                    f"{fmt(v['z'])}" for x, v in e["per_length"].items()))
        c, g, w = s["clustered"], s["sign_test"], s["without_lowest"]
        lines.append(f"R1 next to the rule: clustered by task t = {fmt(c['t'])} (df {c['df']}, p {fmt_p(c['p'])}, "
                     f"{c['verdict']}); tasks below {THRESHOLD}: {g['below']} of {g['tasks']} (sign test p "
                     f"{fmt_p(g['p'])}); without {', '.join(w['tasks_dropped'])}: {w['mean']:.2f} +- {w['se']:.2f}, "
                     f"z = {fmt(w['z'])}")
    r3_ = result["hypotheses"]["R3"]
    if "drops" in r3_:
        if r3_.get("undetermined"):
            lines.append(f"\nR3 undetermined: {r3_['undetermined_reason']}")
        lines += ["", "| LFM3 category | drop 4096->131072 | SE sample | SE clustered (tasks) | clustered verdict |",
                  "|---|---|---|---|---|"]
        lines += [f"| {c} | {d['drop']:.2f} | {d['se_sample']:.2f} | {fmt(d['se_clustered'])} ({d['tasks']}) | "
                  f"{d['verdict_clustered']} |" for c, d in r3_["drops"].items()]
    lines += ["", "| model | scoring | " + " | ".join(map(str, LENGTHS)) + " |", "|---" * (len(LENGTHS) + 2) + "|"]
    for model, d in result["models"].items():
        cells = ["not run"] * len(LENGTHS) if d is None else [fmt(d["per_length"][str(x)]) for x in LENGTHS]
        lines.append(f"| {model} | pre-registered | " + " | ".join(cells) + " |")
        if d is not None and d["strict_per_length"] is not None:
            lines.append(f"| {model} | strict | " + " | ".join(fmt(d["strict_per_length"][str(x)]) for x in LENGTHS)
                         + " |")
    return "\n".join(lines)


def main(results_dir=HERE / "results", resamples=BOOTSTRAP_RESAMPLES):
    result = analyse(Path(results_dir), resamples)
    print(report(result))
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    (Path(results_dir) / "hypotheses.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    main()
