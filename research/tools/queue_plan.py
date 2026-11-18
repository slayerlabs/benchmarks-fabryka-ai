"""Split the (model, task) pairs of a central run into one queue per GPU by estimated time, not by list order.

Input on stdin, one item per line: `ITEM<TAB>T01 T02 ...`, ITEM = LABEL or LABEL:T01,T02 as `licz` got it, then the
tasks this run gives it. Output on stdout, one
line per queue: `<gpu> ITEM ...`, ITEM = LABEL (every task of the line) or LABEL:T01,T02 (a part of them); estimates
on stderr. Called by `kolejki` in tools/przebieg_centralny.sh when the instance has more than one GPU.

Time of a pair, in this order:
1. median `s` of finished `ewaluacja` entries (kod 0) of that model and task in the timing files;
2. median over all models of that task, times the model's speed ratio (its median over tasks it shares with others);
3. DEFAULT_S: an assumption, not a measurement, for tasks never timed (logged on stderr).
The timing files were measured with 1-4 jobs per card, so the numbers order the pairs; they do not promise hours.

Plan: a model longer than PART of the ideal share (total / N) is cut into the fewest parts of at most that length (its
tasks longest first, each to the shortest part); then every part, longest first, goes to the queue with the least work
(LPT). Whole models of ~10 h on 4-8 GPUs are too coarse for LPT (8 GPUs, 15 models: longest queue 28 h against an
ideal 18,5 h); parts of at most a third of a share give 19,4 h, for ~20 extra weight downloads. The longest queue is
at most the ideal share plus the longest part. Same input, same plan.
"""
import argparse
import glob
import json
import math
import os
import statistics
import sys

PART = 1 / 3
"""Longest part of one model, as a fraction of the ideal share of one GPU."""

DEFAULT_S = 1200.0
"""Seconds for a task no timing file has: ~20 min, the order of the issue estimate 17.11 (10-26 h for 53 tasks)."""


def read_times(paths):
    pairs = {}
    for p in paths:
        try:
            lines = open(p, encoding="utf-8").read().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("etap") == "ewaluacja" and r.get("kod") == 0 and r.get("model") and r.get("zadanie"):
                pairs.setdefault((r["model"], r["zadanie"]), []).append(float(r["s"]))
    return {k: statistics.median(v) for k, v in pairs.items()}


def estimator(measured):
    by_task = {}
    for (m, t), s in measured.items():
        by_task.setdefault(t, {})[m] = s
    task_median = {t: statistics.median(v.values()) for t, v in by_task.items()}
    ratio = {}
    for m in {m for m, _ in measured}:
        r = [measured[(m, t)] / task_median[t] for t in by_task if (m, t) in measured and task_median[t] > 0]
        ratio[m] = statistics.median(r) if r else 1.0
    unknown = set()

    def cost(m, t):
        if (m, t) in measured:
            return measured[(m, t)]
        if t in task_median:
            return task_median[t] * ratio.get(m, 1.0)
        unknown.add(t)
        return DEFAULT_S

    return cost, unknown


def lpt(items, n):
    """items: [(cost, key, payload)]; returns n bins [(load, [payload...])], longest item first, ties by key."""
    bins = [[0.0, i, []] for i in range(n)]
    for c, _, payload in sorted(items, key=lambda x: (-x[0], x[1])):
        b = min(bins, key=lambda x: (x[0], x[1]))
        b[0] += c
        b[2].append(payload)
    return [(b[0], b[2]) for b in bins]


def plan(models, n, cost):
    """models: [(item, [tasks])], item = LABEL or LABEL:T01,... as given -> [(load, [item...])] for n queues.
    An item that stays whole is printed as given; a cut one as LABEL:<its part of the tasks>."""
    total = sum(cost(i.split(":")[0], t) for i, ts in models for t in ts)
    target = (total / n if n else total) * PART
    parts = []
    for i, ts in models:
        m = i.split(":")[0]
        c = {t: cost(m, t) for t in ts}
        k = max(1, math.ceil(sum(c.values()) / target - 1e-9)) if target > 0 else 1
        k = min(k, len(ts)) if ts else 1
        for load, chunk in lpt([(c[t], t, t) for t in ts], k):
            if chunk:
                order = [t for t in ts if t in chunk]
                item = i if k == 1 else f"{m}:{','.join(order)}"
                parts.append((load, item, (m, order, item)))
    queues = []
    for load, payload in lpt(parts, n):  # parts of one model that land in one queue: one item, one download
        merged = {}
        for m, order, item in payload:
            merged.setdefault(m, []).append((order, item))
        items = []
        for m, chunks in merged.items():
            if len(chunks) == 1:
                items.append(chunks[0][1])
            else:
                tasks = [t for order, _ in chunks for t in order]
                items.append(f"{m}:{','.join(tasks)}")
        queues.append((load, items))
    return queues, total


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gpus", type=int, required=True)
    ap.add_argument("--repo", required=True, help="research/ directory: timing files are results/**/czasy.jsonl and "
                                                  "results/central-run/times_*.jsonl")
    ap.add_argument("--czasy", default="", help="czasy.jsonl of this instance (finished pairs of this run)")
    a = ap.parse_args()
    paths = sorted(glob.glob(os.path.join(a.repo, "results", "**", "czasy.jsonl"), recursive=True))
    paths += sorted(glob.glob(os.path.join(a.repo, "results", "central-run", "times_*.jsonl")))
    if a.czasy:
        paths.append(a.czasy)
    cost, unknown = estimator(read_times(paths))
    models = []
    for line in sys.stdin.read().splitlines():
        if line.strip():
            label, _, tasks = line.partition("\t")
            models.append((label.strip(), tasks.split()))
    queues, total = plan(models, a.gpus, cost)
    for i, (load, items) in enumerate(queues):
        print(f"{i} {' '.join(items)}".rstrip())
        print(f"# estimate GPU {i}: ~{load / 3600:.1f} h", file=sys.stderr)
    print(f"# estimate: {total / 3600:.1f} h of card work in all, ideal per GPU {total / max(a.gpus, 1) / 3600:.1f} h",
          file=sys.stderr)
    if unknown:
        print(f"# never timed, assumed {DEFAULT_S:.0f} s per pair: {' '.join(sorted(unknown))}", file=sys.stderr)


if __name__ == "__main__":
    main()
