"""Results files from a Harbor job: python3 summarize.py <job-dir> --model <model-id> [--out-dir results]
or the null result of a model that cannot run the benchmark: python3 summarize.py --null <model-id> --out <file>.

Score: the pass rate over all trials (a trial passes when the task's tests give reward 1). Every task has the same
number of trials, so this is also the mean of the per-task pass rates. stderr: the standard error of that mean over
tasks (sd of the per-task pass rates / sqrt(number of tasks)), because trials of one task are not independent.

A trial that fails for an infrastructure reason (container build, Docker, model server unreachable) is not a model
failure. Such trials are listed and the summary refuses to write a score until they are rerun (--allow-infra
overrides, and then counts them as failures, which the README must say).
"""

import argparse
import gzip
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

BENCHMARK = "Terminal-Bench 2.1"
HARNESS = "https://github.com/harbor-framework/harbor v0.27.0, agent opencode (opencode-ai 1.19.6)"
DATA = "https://github.com/harbor-framework/terminal-bench-2-1 @ 12b7565679ce5006230b820666353673a133db93, 89 tasks"
METRIC = "pass rate (task tests pass, reward 1), mean over tasks and trials"
# Exceptions that end a trial because of the model or the agent, not the machine: they count as failures.
MODEL_SIDE = {"AgentTimeoutError", "NonZeroAgentExitCodeError", "VerifierTimeoutError"}


def reward(result: dict) -> float:
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    value = rewards.get("reward")
    return float(value) if value is not None else 0.0


def load(job: Path) -> list[dict]:
    rows = []
    for path in sorted(job.glob("*/result.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        exc = r.get("exception_info") or {}
        agent = r.get("agent_result") or {}
        trajectory = path.parent / "agent" / "trajectory.json"
        rows.append(
            {
                "task": r["task_name"].removeprefix("terminal-bench/"),
                "trial": r["trial_name"],
                "score": reward(r),
                "exception": exc.get("exception_type"),
                "n_input_tokens": agent.get("n_input_tokens"),
                "n_output_tokens": agent.get("n_output_tokens"),
                "output": json.loads(trajectory.read_text(encoding="utf-8")) if trajectory.exists() else None,
            }
        )
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("job", nargs="?", type=Path)
    p.add_argument("--model")
    p.add_argument("--out-dir", type=Path, default=Path(__file__).parent / "results")
    p.add_argument("--null")
    p.add_argument("--out", type=Path)
    p.add_argument("--allow-infra", action="store_true")
    a = p.parse_args()

    if a.null:
        result = {
            "benchmark": BENCHMARK,
            "model": a.null,
            "metric": METRIC,
            "score": None,
            "stderr": None,
            "n": 0,
            "date": date.today().isoformat(),
            "harness": HARNESS,
            "data": DATA,
            "settings": None,
            "deviations": "not run: a base model without a chat template or a tool-call format, so OpenCode cannot "
            "drive it (see README)",
        }
        a.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {a.out}")
        return 0

    rows = load(a.job)
    if not rows:
        print(f"no trials in {a.job}", file=sys.stderr)
        return 1
    infra = [r for r in rows if r["exception"] and r["exception"] not in MODEL_SIDE]
    for r in infra:
        print(f"infrastructure failure: {r['trial']} ({r['exception']})", file=sys.stderr)
    if infra and not a.allow_infra:
        print(f"{len(infra)} trials failed for infrastructure reasons; rerun them first", file=sys.stderr)
        return 1

    by_task: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        by_task[r["task"]].append(r["score"])
    trials = {len(v) for v in by_task.values()}
    if len(trials) != 1:
        print(f"tasks have different trial counts: {sorted(trials)}", file=sys.stderr)
        return 1
    per_task = [statistics.fmean(v) for v in by_task.values()]
    score = 100 * statistics.fmean(per_task)
    stderr = 100 * statistics.stdev(per_task) / math.sqrt(len(per_task)) if len(per_task) > 1 else None
    config = json.loads(next(a.job.glob("*/config.json")).read_text(encoding="utf-8")) if any(
        a.job.glob("*/config.json")
    ) else None

    result = {
        "benchmark": BENCHMARK,
        "model": a.model,
        "metric": METRIC,
        "score": round(score, 2),
        "stderr": None if stderr is None else round(stderr, 2),
        "n": len(per_task),
        "date": date.today().isoformat(),
        "harness": HARNESS,
        "data": DATA,
        "settings": {"trials_per_task": trials.pop(), "job_config": config},
        "deviations": "see README.md, Deviations",
        "other_metrics": {
            "trials": len(rows),
            "trials_passed": sum(r["score"] == 1.0 for r in rows),
            "trial_exceptions": dict(sorted(
                {e: sum(r["exception"] == e for r in rows) for e in {r["exception"] for r in rows} if e}.items()
            )),
            "infrastructure_failures_counted_as_fail": len(infra),
        },
    }
    a.out_dir.mkdir(parents=True, exist_ok=True)
    (a.out_dir / f"{a.model}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with gzip.open(a.out_dir / f"{a.model}.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{a.model}: {score:.2f} ± {stderr if stderr is None else round(stderr, 2)} over {len(per_task)} tasks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
