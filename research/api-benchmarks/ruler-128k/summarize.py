"""Raw outputs -> RULER prediction files, and the scored run -> results/<model-id>.json and .jsonl.gz.

  python summarize.py preds <out>/<model-id>/<length>
      writes pred/<task>.jsonl (RULER's prediction format, the text after the last `</think>` as `pred`) for
      scripts/eval/evaluate.py. Samples whose last attempt is an error are left out: they are not scored at all.
  python summarize.py results <out>/<model-id> <results/model-id> --ruler-dir DIR
      scores every sample with RULER's own postprocess and metric (ruler.scorer), checks that the per-task means
      equal RULER's summary.csv, and writes the result files (format: research/METHODOLOGY.md).

A run with --limit (run.json "limit") is written to <out>/<model-id>/<model-id>.* instead of results/, so a
smoke test never replaces a published result.
"""

import argparse
import csv
import datetime
import gzip
import json
import random
import statistics
from pathlib import Path

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


def aggregate(rows, skipped, lengths, tasks=TASKS, resamples=BOOTSTRAP_RESAMPLES):
    """Per length: mean over tasks with bootstrap SE; per task and length; per category; error and unfinished counts.

    A length in `skipped` (length -> reason) is null with its reason. A length that ran but has a task without any
    scored sample is null too: the 13-task mean would silently become a mean over fewer tasks.
    """
    per_length, per_task, per_category, errors, unfinished = {}, {}, {}, {}, {}
    for length in lengths:
        key = str(length)
        if length in skipped:
            per_length[key] = {"score": None, "reason": skipped[length]}
            continue
        here = [r for r in rows if r["length"] == length]
        scores = {t: [r["score"] for r in here if r["task"] == t and r["score"] is not None] for t in tasks}
        errors[key] = {t: n for t in tasks if (n := sum(r["task"] == t and r["score"] is None for r in here))}
        unfinished[key] = sum(r.get("finished") is False for r in here)
        per_task[key] = {t: round(statistics.fmean(s), 2) if s else None for t, s in scores.items()}
        missing = [t for t, s in scores.items() if not s]
        if missing:
            per_length[key] = {"score": None, "reason": f"no scored sample in {', '.join(missing)}"}
            continue
        per_length[key] = {
            "score": round(statistics.fmean(statistics.fmean(s) for s in scores.values()), 2),
            "stderr": round(bootstrap_se(list(scores.values()), resamples), 2),
            "n": sum(len(s) for s in scores.values()),
        }
        per_category[key] = {c: round(statistics.fmean(statistics.fmean(scores[t]) for t in ts), 2)
                             for c, ts in CATEGORIES.items() if all(t in scores for t in ts)}
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


def result_json(run, metrics):
    headline = metrics["per_length"].get(str(HEADLINE_LENGTH), {"score": None, "reason": "length not run"})
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
        "settings": run["settings"],
        "other_metrics": metrics,
        "deviations": "see README.md, Deviations",
    }
    if headline["score"] is None:
        result["reason"] = headline["reason"]
    return result


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

    out_dir = Path(out_dir)
    run = json.loads((out_dir / "run.json").read_text(encoding="utf-8"))
    if run.get("limit"):
        target = out_dir / out_dir.name
        print(f"summarize.py: --limit {run['limit']}, writing to {target}.* (not results/)")
    postprocess, metric_fns = scorer(ruler_dir)
    rows, skipped = [], {}
    for length in run["lengths"]:
        length_dir = out_dir / str(length)
        if (length_dir / "skip.json").exists():
            skipped[length] = json.loads((length_dir / "skip.json").read_text(encoding="utf-8"))["reason"]
            continue
        here = []
        for task in run["tasks"]:
            samples = read_jsonl(length_dir / "data" / task / "validation.jsonl")
            records = latest_records(length_dir / "raw" / f"{task}.jsonl")
            here += sample_rows(task, length, samples, records, postprocess, metric_fns[task])
        check_against_ruler(here, ruler_summary(length_dir / "pred"), length)
        rows += here
    metrics = aggregate(rows, skipped, run["lengths"], run["tasks"])
    result = result_json(run, metrics)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
        for line in jsonl_rows(rows):
            f.write(json.dumps(line, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2))


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
