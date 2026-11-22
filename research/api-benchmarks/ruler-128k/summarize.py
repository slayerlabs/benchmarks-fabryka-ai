"""Raw outputs -> RULER prediction files, and the scored run -> results/<model-id>.json and .jsonl.gz.

  python summarize.py preds <out>/<model-id>/<length>
      writes pred/<task>.jsonl (RULER's prediction format, the text after the last `</think>` as `pred`) for
      scripts/eval/evaluate.py. Samples whose last attempt is an error are left out: they are not scored at all.
  python summarize.py results <out>/<model-id> <results/model-id> --ruler-dir DIR
      checks the sha256 of every input against <out>/<model-id>/inputs.sha256.json (run.sh writes it after scoring),
      scores every sample with RULER's own postprocess and metric (ruler.scorer), checks that the per-task means
      equal RULER's summary.csv, and writes the result files (format: research/METHODOLOGY.md) with the effective
      sampling in `settings.sampling` and the code commit, runner sha256 and hardware of generation (generation.jsonl)
      and of this summary in `provenance`; their sha256 go to results.sha256.json next to them, which compare.py checks.

A run with --limit (run.json "limit") is written to <out>/<model-id>/<model-id>.* instead of results/, so a
smoke test never replaces a published result. An out dir from a run.sh before generation.jsonl and
inputs.sha256.json existed is still summarized: what was not recorded is null with the reason, the sampling is read
from the pinned generation_config.json now, the input manifest is written now, and each is a line in `warnings`.
"""

import argparse
import csv
import datetime
import gzip
import json
import random
import statistics
from pathlib import Path

import provenance
from ruler import answer_text, latest_records, read_jsonl

TASKS = ["niah_single_1", "niah_single_2", "niah_single_3", "niah_multikey_1", "niah_multikey_2", "niah_multikey_3",
         "niah_multivalue", "niah_multiquery", "vt", "cwe", "fwe", "qa_1", "qa_2"]
LENGTHS = [4096, 8192, 16384, 32768, 65536, 131072]
HEADLINE_LENGTH = 131072
CATEGORIES = {  # PROTOCOL.md, Metrics (R3)
    "retrieval": TASKS[:8],
    "tracing": ["vt"],
    "aggregation": ["cwe", "fwe"],
    "qa": ["qa_1", "qa_2"],
}
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261122
ANSWER_CHARS = 2000  # stored answer text per sample in the .jsonl.gz; scoring always uses the full text


def pred_records(samples, records):
    """RULER prediction lines for the samples whose last attempt has an output (errors are not scored)."""
    out = []
    for s in samples:
        r = records.get(s["index"])
        if r is None or "output" not in r:
            continue
        out.append({"index": s["index"], "pred": answer_text(r["output"]), "input": "", "outputs": s["outputs"],
                    "others": {}, "truncation": -1, "length": s["length"]})
    return out


def write_preds(length_dir):
    length_dir = Path(length_dir)
    pred_dir = length_dir / "pred"
    pred_dir.mkdir(exist_ok=True)
    for old in pred_dir.glob("summary*.csv"):  # evaluate.py rewrites it; a stale one would be read instead
        old.unlink()
    for data_file in sorted((length_dir / "data").glob("*/validation.jsonl")):
        task = data_file.parent.name
        lines = pred_records(read_jsonl(data_file), latest_records(length_dir / "raw" / f"{task}.jsonl"))
        target = pred_dir / f"{task}.jsonl"
        if lines:  # evaluate.py divides by the number of lines; a task with no output gets no file
            target.write_text("".join(json.dumps(x) + "\n" for x in lines), encoding="utf-8")
        elif target.exists():
            target.unlink()


def sample_rows(task, length, samples, records, postprocess, metric_fn):
    """One row per sample: score in percent (RULER's metric on this sample alone), or score None with the error."""
    rows = []
    for s in samples:
        r = records.get(s["index"])
        row = {"task": task, "length": length, "index": s["index"]}
        if r is None:
            row.update(score=None, error="not run")
        elif "output" not in r:
            row.update(score=None, error=r["error"])
        else:
            answer = answer_text(r["output"])
            row.update(score=metric_fn([postprocess(answer, None)], [s["outputs"]]), answer=answer,
                       output_tokens=r["output_tokens"], finished=r["finish_reason"] == "stop")
        rows.append(row)
    return rows


def bootstrap_se(scores_by_task, resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED):
    """SE of the unweighted task mean, resampling samples within each task (PROTOCOL.md, Metrics)."""
    rng = random.Random(seed)
    means = []
    for _ in range(resamples):
        task_means = [statistics.fmean(rng.choices(s, k=len(s))) for s in scores_by_task]
        means.append(statistics.fmean(task_means))
    return statistics.stdev(means)


def aggregate(rows, skipped, lengths, tasks=TASKS, resamples=BOOTSTRAP_RESAMPLES, task_skips=None):
    """Per length: mean over tasks with bootstrap SE; per task and length; per category; error and unfinished counts.

    A length in `skipped` (length -> reason) is null with its reason. A task in `task_skips` (length -> task ->
    reason: RULER could not generate it) is null for that length, never 0: the length mean is over the remaining
    tasks and flagged `partial` with the skipped tasks. A task that was generated but has no scored sample (only
    errors) makes the length null: that is a failed run, not a property of the data.
    """
    task_skips = task_skips or {}
    per_length, per_task, per_category, errors, unfinished = {}, {}, {}, {}, {}
    for length in lengths:
        key = str(length)
        if length in skipped:
            per_length[key] = {"score": None, "reason": skipped[length]}
            continue
        gone = task_skips.get(length, {})
        here = [r for r in rows if r["length"] == length]
        scores = {t: [r["score"] for r in here if r["task"] == t and r["score"] is not None]
                  for t in tasks if t not in gone}
        errors[key] = {t: n for t in tasks if (n := sum(r["task"] == t and r["score"] is None for r in here))}
        unfinished[key] = sum(r.get("finished") is False for r in here)
        per_task[key] = {t: round(statistics.fmean(scores[t]), 2) if scores.get(t) else None for t in tasks}
        missing = [t for t, s in scores.items() if not s]
        if missing:
            per_length[key] = {"score": None, "reason": f"no scored sample in {', '.join(missing)}"}
            continue
        if not scores:
            per_length[key] = {"score": None, "reason": "every task skipped", "partial": True, "skipped_tasks": gone}
            continue
        per_length[key] = {
            "score": round(statistics.fmean(statistics.fmean(s) for s in scores.values()), 2),
            "stderr": round(bootstrap_se(list(scores.values()), resamples), 2),
            "n": sum(len(s) for s in scores.values()),
        }
        if gone:
            per_length[key].update(partial=True, skipped_tasks=dict(gone))
        per_category[key] = {c: round(statistics.fmean(statistics.fmean(scores[t]) for t in ts if t in scores), 2)
                             for c, ts in CATEGORIES.items() if any(t in scores for t in ts)}
    return {"per_length": per_length, "per_task": per_task, "per_category": per_category, "errors": errors,
            "unfinished": unfinished}


def ruler_summary(pred_dir):
    """task -> score from RULER's evaluate.py output: rows Tasks / Score / Nulls, in summary.csv, or in
    summary-<task>.csv when only one task had a prediction file."""
    (summary,) = Path(pred_dir).glob("summary*.csv")  # write_preds removes old ones before evaluate.py runs
    rows = {r[0]: r[1:] for r in csv.reader(summary.read_text(encoding="utf-8").splitlines()) if r}
    return {t: float(s) for t, s in zip(rows["Tasks"], rows["Score"])}


def check_against_ruler(rows, ruler_scores, length):
    """The per-sample scores must average to RULER's own task score (each is rounded to 0.01 by RULER)."""
    for task, official in ruler_scores.items():
        mine = [r["score"] for r in rows if r["task"] == task and r["length"] == length and r["score"] is not None]
        if abs(statistics.fmean(mine) - official) > 0.01:
            raise SystemExit(f"summarize.py: {task} @ {length}: per-sample mean {statistics.fmean(mine):.4f} "
                             f"!= RULER evaluate.py {official}")


def result_json(run, metrics, sampling=None, prov=None, warnings=()):
    headline = metrics["per_length"].get(str(HEADLINE_LENGTH), {"score": None, "reason": "length not run"})
    if headline.get("partial"):  # the headline is the 13-task mean; a partial mean is only in other_metrics
        headline = {"score": None, "reason": f"partial at {HEADLINE_LENGTH}: RULER could not generate "
                                             + ", ".join(headline["skipped_tasks"])}
    result = {
        "benchmark": "RULER",
        "model": run["model"],
        "metric": f"mean of the 13 RULER task scores at {HEADLINE_LENGTH} tokens (percent)",
        "score": headline["score"],
        "stderr": headline.get("stderr"),
        "n": headline.get("n"),
        "date": run["date"],
        "harness": f"https://github.com/NVIDIA/RULER @ {run['ruler_commit']} (data: scripts/data/prepare.py, "
                   "scoring: scripts/eval/evaluate.py)",
        "data": (f"RULER synthetic tasks generated with the model's tokenizer, seed {run['seed']}, "
                 f"{run['num_samples']} samples per task and length; source files sha256: "
                 + ", ".join(f"{k} {v}" for k, v in sorted(run["data_sources"].items()))),
        "settings": {**run["settings"], "sampling": sampling},
        "other_metrics": metrics,
        "deviations": "see README.md, Deviations",
        "provenance": prov,
        "warnings": list(warnings),
    }
    if headline["score"] is None:
        result["reason"] = headline["reason"]
    return result


def run_provenance(out_dir, run, read_config=None):
    """(effective sampling, provenance, warnings) of a run. generation.jsonl (run.sh, one line per generating call)
    gives the sampling and each call's commit, runner sha256 and hardware; an out dir without it (a run.sh before it
    existed) gets null with the reason and the sampling read now from the pinned generation_config.json."""
    warnings = []
    generation = read_jsonl(Path(out_dir) / "generation.jsonl")
    prov = {"generation": None, "summarize": provenance.machine()}
    if generation:
        variants = sorted({json.dumps(e["sampling"], sort_keys=True) for e in generation})
        if len(variants) > 1:
            raise SystemExit("summarize.py: STOP: generation.jsonl records different sampling across run.sh calls: "
                             + " | ".join(variants))
        prov["generation"] = [{k: e[k] for k in ("time", "code", "runner_sha256", "hardware")} for e in generation]
        return generation[-1]["sampling"], prov, warnings
    prov["generation_reason"] = ("no generation.jsonl: generated by a run.sh before it was recorded, so the code "
                                 "commit, runner sha256 and hardware of generation are unknown")
    warnings.append(prov["generation_reason"])
    try:
        sampling = provenance.sampling(run["settings"], read_config)
        sampling["recorded"] = "by summarize.py from the pinned revision, not at generation (no generation.jsonl)"
    except Exception as e:  # noqa: BLE001  an old out dir is still summarized; the gap is stated
        sampling = {"effective": None, "reason": f"not derivable from run.json and the pinned generation_config.json: "
                                                 f"{type(e).__name__}: {e}"}
        warnings.append(f"effective sampling unknown: {sampling['reason']}")
    return sampling, prov, warnings


def jsonl_rows(rows):
    for r in rows:
        line = {k: r[k] for k in ("task", "length", "index", "score")}
        if r["score"] is None:
            line["error"] = r["error"]
        else:
            line.update(answer=r["answer"][:ANSWER_CHARS], answer_truncated=len(r["answer"]) > ANSWER_CHARS,
                        output_tokens=r["output_tokens"], finished=r["finished"])
        yield line


def results(out_dir, target, ruler_dir):
    from ruler import scorer  # needs the RULER checkout and its dependencies (pyyaml, nltk, pandas)

    postprocess, metric_fns = scorer(ruler_dir)
    print(json.dumps(summarize_run(out_dir, target, postprocess, metric_fns), indent=2))


def summarize_run(out_dir, target, postprocess, metric_fns, read_config=None):
    out_dir = Path(out_dir)
    input_warning = provenance.verify_inputs(out_dir)  # before anything is read
    run = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    if run.get("limit"):
        target = out_dir / out_dir.name
        print(f"summarize.py: --limit {run['limit']}, writing to {target}.* (not results/)")
    rows, skipped, task_skips = [], {}, {}
    for length in run["lengths"]:
        length_dir = out_dir / str(length)
        if (length_dir / "skip.json").exists():
            skipped[length] = json.loads((length_dir / "skip.json").read_text(encoding="utf-8"))["reason"]
            continue
        here = []
        for task in run["tasks"]:
            task_skip = length_dir / "data" / task / "skip.json"
            if task_skip.exists():  # run.sh: RULER's generator could not produce this task at this length
                task_skips.setdefault(length, {})[task] = json.loads(task_skip.read_text(encoding="utf-8"))["reason"]
                continue
            samples = read_jsonl(length_dir / "data" / task / "validation.jsonl")
            records = latest_records(length_dir / "raw" / f"{task}.jsonl")
            here += sample_rows(task, length, samples, records, postprocess, metric_fns[task])
        if any((length_dir / "pred").glob("*.jsonl")):  # evaluate.py ran only where some task has an output
            check_against_ruler(here, ruler_summary(length_dir / "pred"), length)
        rows += here
    metrics = aggregate(rows, skipped, run["lengths"], run["tasks"], task_skips=task_skips)
    sampling, prov, warnings = run_provenance(out_dir, run, read_config)
    if input_warning:
        warnings.append(input_warning)
    result = result_json(run, metrics, sampling, prov, warnings)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
        for line in jsonl_rows(rows):
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    provenance.write_manifest(target.parent, [f"{target.name}.json", f"{target.name}.jsonl.gz"], provenance.RESULTS)
    return result


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preds")
    p.add_argument("length_dir")
    r = sub.add_parser("results")
    r.add_argument("out_dir")
    r.add_argument("target")
    r.add_argument("--ruler-dir", required=True)
    args = ap.parse_args()
    if args.command == "preds":
        write_preds(args.length_dir)
    else:
        results(args.out_dir, args.target, args.ruler_dir)


if __name__ == "__main__":
    main()
