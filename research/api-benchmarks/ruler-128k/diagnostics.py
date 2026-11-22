"""Exploratory checks of the published runs, from the raw outputs and RULER data in the out dirs -> diagnostics.json.

Usage: python diagnostics.py --ruler-dir DIR --lfm3 OUT --bielik OUT [--target results/diagnostics.json]

Nothing here is a verdict or a pre-registered number: each block was asked for by the verification of 2026-11-22
(PROTOCOL.md, Amendment 7) after the results were seen, and README labels it exploratory.

- control_variants: LFM3-1.7B at 131072 rescored in the 7 ways the refuter tried after the control had failed (strict;
  the answer cut to RULER's answer budget at about 0.75 words per token; outputs longer than 8192, 16384, 32768 or
  65536 tokens scored 0; strict with the cut answer), each with its bootstrap SE and z against the card's 65.56.
- duplicates: LFM3-1.7B samples with more than one record in raw/ (the last one is scored, ruler.latest_records),
  with the means and the R3 comparisons if the first record were scored instead.
- input_text: the median characters of a RULER input per model and length (RULER counts length with each model's
  tokenizer, so the same nominal length holds different text).
- think_end: outputs without `</think>` per length and finish reason; those that stopped on their own (`stop`)
  are listed, since strict scoring gives them 0 although Amendment 4's reason was outputs looping to the limit.

Every out dir is checked against its inputs.sha256.json before it is read (provenance.verify_inputs). Scoring is
RULER's own postprocess_pred and metric (ruler.scorer), as in summarize.py; the last record of a sample wins.
"""
import argparse
import json
import statistics
from pathlib import Path

import provenance
from ruler import THINK_END, answer_budgets, answer_text, read_jsonl, scorer
from summarize import BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, CATEGORIES, HEADLINE_LENGTH, LENGTHS, TASKS, bootstrap_se

HERE = Path(__file__).resolve().parent
CARD = 65.56  # compare.CONTROL_CARD (not imported: compare.py pulls in the hypothesis machinery)
WORDS_PER_TOKEN = 0.75  # the refuter's approximation of RULER's answer budget in words
OUTPUT_CAPS = [8192, 16384, 32768, 65536]


def records(length_dir, task):
    """index -> every record with an output, in the order written (a rerun appends)."""
    out = {}
    for r in read_jsonl(length_dir / "raw" / f"{task}.jsonl"):
        if "output" in r:
            out.setdefault(r["index"], []).append(r)
    return out


def samples(out_dir, length, which=-1):
    """task -> list of (sample, record) for one length; `which` picks the record of a sample (-1: the last, as
    summarize.py scores; 0: the first)."""
    length_dir = Path(out_dir) / str(length)
    found = {}
    for task in TASKS:
        data = length_dir / "data" / task / "validation.jsonl"
        if not data.is_file():
            continue
        recs = records(length_dir, task)
        found[task] = [(s, recs[s["index"]][which]) for s in read_jsonl(data) if s["index"] in recs]
    return found


def mean_se(by_task):
    """Unweighted task mean and its bootstrap SE (summarize.bootstrap_se: samples within tasks)."""
    lists = [v for v in by_task.values() if v]
    return statistics.fmean(statistics.fmean(v) for v in lists), bootstrap_se(lists, BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED)


def control_variants(out_dir, postprocess, metrics, budgets):
    rows = samples(out_dir, HEADLINE_LENGTH)

    def score(task, text, sample):
        return metrics[task]([postprocess(text, None)], [sample["outputs"]])

    def cut(task, record, sample):
        words = postprocess(answer_text(record["output"]), None).split()
        return score(task, " ".join(words[:int(budgets[task] * WORDS_PER_TOKEN)]), sample)

    def closed(record):
        return THINK_END in record["output"]

    def full(task, record, sample):
        return score(task, answer_text(record["output"]), sample)

    variants = {
        "pre-registered": full,
        "strict": lambda t, r, s: full(t, r, s) if closed(r) else 0.0,
        f"answer cut to RULER's answer budget (about {WORDS_PER_TOKEN} words per token)": cut,
        **{f"output limit {cap} tokens (a longer output scores 0)":
           (lambda c: lambda t, r, s: 0.0 if r["output_tokens"] > c else full(t, r, s))(cap) for cap in OUTPUT_CAPS},
        "strict and answer cut": lambda t, r, s: cut(t, r, s) if closed(r) else 0.0,
    }
    out = {}
    for name, fn in variants.items():
        mean, se = mean_se({t: [fn(t, r, s) for s, r in pairs] for t, pairs in rows.items()})
        z = (mean - CARD) / se if se > 0 else None
        out[name] = {"mean": mean, "se": se, "z_vs_card": z, "within_2_se": z is not None and abs(z) < 2}
    return {"length": HEADLINE_LENGTH, "card": CARD, "variants_tried": len(variants) - 1,
            "note": "exploratory: tried after the control had failed; not a fix of the control", "variants": out}


def task_means(rows, score_fn):
    return {t: statistics.fmean(score_fn(t, r, s) for s, r in pairs) for t, pairs in rows.items()}


def category_drops(short, long):
    """category -> mean drop from `short` to `long` (task -> mean), over the category's tasks present in both."""
    present = {c: [t for t in ts if t in short and t in long] for c, ts in CATEGORIES.items()}
    return {c: statistics.fmean(short[t] for t in ts) - statistics.fmean(long[t] for t in ts)
            for c, ts in present.items() if ts}


def duplicates(out_dir, postprocess, metrics):
    def pre(task, record, sample):
        return metrics[task]([postprocess(answer_text(record["output"]), None)], [sample["outputs"]])

    def strict(task, record, sample):
        return pre(task, record, sample) if THINK_END in record["output"] else 0.0

    per_length, first_vs_last = {}, None
    for length in LENGTHS:
        length_dir = Path(out_dir) / str(length)
        dups = {t: {i: rs for i, rs in records(length_dir, t).items() if len(rs) > 1} for t in TASKS}
        dups = {t: d for t, d in dups.items() if d}
        if not dups:
            continue
        pairs = [rs for d in dups.values() for rs in d.values()]
        replaced = [r for rs in pairs for r in rs[:-1]]
        last, first = samples(out_dir, length, -1), samples(out_dir, length, 0)
        entry = {
            "samples_with_more_than_one_record": {t: len(d) for t, d in dups.items()},
            "records_per_sample": sorted({len(rs) for rs in pairs}),
            "finish_reason_of_replaced": {k: sum(r["finish_reason"] == k for r in replaced)
                                          for k in sorted({r["finish_reason"] for r in replaced})},
            "identical_outputs": sum(all(r["output"] == rs[-1]["output"] for r in rs[:-1]) for rs in pairs),
            "output_tokens_median": {"first": statistics.median(rs[0]["output_tokens"] for rs in pairs),
                                     "last": statistics.median(rs[-1]["output_tokens"] for rs in pairs)},
            "last_longer_than_first": sum(rs[-1]["output_tokens"] > rs[0]["output_tokens"] for rs in pairs),
            "mean": {"last (scored)": statistics.fmean(task_means(last, pre).values()),
                     "first": statistics.fmean(task_means(first, pre).values())},
            "strict_mean": {"last (scored)": statistics.fmean(task_means(last, strict).values()),
                            "first": statistics.fmean(task_means(first, strict).values())},
        }
        per_length[str(length)] = entry
        if length == LENGTHS[0]:
            long = task_means(samples(out_dir, HEADLINE_LENGTH), pre)
            first_vs_last = {}
            for which, rows in (("last (scored)", last), ("first", first)):
                drops = category_drops(task_means(rows, pre), long)
                first_vs_last[which] = {f"drop {c} - drop retrieval": drops[c] - drops["retrieval"]
                                        for c in ("tracing", "aggregation") if c in drops}
    return {"rule": "the last record of a sample is scored (ruler.latest_records); a rerun appends",
            "per_length": per_length, "r3_comparisons_at_4096": first_vs_last}


def input_text(out_dirs):
    """model -> length -> median characters of a RULER input (all tasks), and Bielik / LFM3 per shared length."""
    out = {}
    for model, out_dir in out_dirs.items():
        out[model] = {}
        for length in LENGTHS:
            chars = [len(s["input"]) for t in TASKS
                     for s in read_jsonl(Path(out_dir) / str(length) / "data" / t / "validation.jsonl")]
            if chars:
                out[model][str(length)] = statistics.median(chars)
    a, b = "lfm3-1.7b", "bielik-11b-v3.1"
    ratio = {x: out[b][x] / out[a][x] for x in out.get(a, {}) if x in out.get(b, {})}
    return {"median_chars": out, "bielik_over_lfm3": ratio}


def think_end(out_dir, postprocess, metrics):
    per_length, stopped = {}, []
    for length in LENGTHS:
        rows = samples(out_dir, length)
        if not rows:
            continue
        no_end = [(t, s, r) for t, pairs in rows.items() for s, r in pairs if THINK_END not in r["output"]]
        per_length[str(length)] = {k: sum(r["finish_reason"] == k for _, _, r in no_end)
                                   for k in sorted({r["finish_reason"] for _, _, r in no_end})}
        stopped += [{"length": length, "task": t, "index": s["index"], "output_tokens": r["output_tokens"],
                     "pre_registered_score": metrics[t]([postprocess(answer_text(r["output"]), None)], [s["outputs"]]),
                     "strict_score": 0.0}
                    for t, s, r in no_end if r["finish_reason"] == "stop"]
    return {"without_think_end_by_finish_reason": per_length, "stopped_without_think_end": stopped}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ruler-dir", required=True)
    ap.add_argument("--lfm3", type=Path, required=True, help="LFM3-1.7B out dir (out/_box/lfm3-1.7b)")
    ap.add_argument("--bielik", type=Path, required=True, help="Bielik out dir (out/bielik-11b-v3.1)")
    ap.add_argument("--target", type=Path, default=HERE / "results" / "diagnostics.json")
    args = ap.parse_args()
    if args.target.parent.resolve() == (HERE / "results").resolve():
        provenance.require_committed("diagnostics.py")
    dirs = {"lfm3-1.7b": args.lfm3, "bielik-11b-v3.1": args.bielik}
    inputs = {}
    for model, out_dir in dirs.items():
        provenance.verify_inputs(out_dir, "diagnostics.py")
        inputs[model] = {"out_dir": out_dir.as_posix(), provenance.INPUTS: provenance.sha256(out_dir / provenance.INPUTS)}
    postprocess, metrics = scorer(args.ruler_dir)
    budgets = answer_budgets(args.ruler_dir)
    result = {"exploratory": True, "lfm3-1.7b": {
        "control_variants": control_variants(args.lfm3, postprocess, metrics, budgets),
        "duplicates": duplicates(args.lfm3, postprocess, metrics),
        "think_end": think_end(args.lfm3, postprocess, metrics)},
        "input_text": input_text(dirs), "inputs": inputs, "provenance": provenance.machine()}
    args.target.parent.mkdir(parents=True, exist_ok=True)
    args.target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    provenance.write_manifest(args.target.parent, [args.target.name], provenance.RESULTS)
    print(json.dumps({k: v for k, v in result["lfm3-1.7b"]["control_variants"]["variants"].items()}, indent=1))


if __name__ == "__main__":
    main()
