"""Results files from a Harbor job: python3 summarize.py <job-dir> --model <model-id> [--out-dir results]
or the null result of a model that cannot run the benchmark: python3 summarize.py --null <model-id> --out <file>.

Score: the pass rate over all counted trials (a trial passes when the task's tests give reward 1). Every task has the
same number of counted trials, so this is also the mean of the per-task pass rates. stderr: the standard error of
that mean over tasks (sd of the per-task pass rates / sqrt(number of tasks)), because trials of one task are not
independent. The per-trial formula of research/METHODOLOGY.md (sqrt(p(1-p)/n) over all trials) is written as
other_metrics.stderr_per_trial, for comparison.

Harbor's exception label is not used to decide anything: it is a pattern match over the agent's output, and here it
mostly labels OpenCode's exit code 1 after a finished run (EPIPE on stdout, see README) as "rate limit" or
"network". What counts is the evidence in each trial:
- a trial with a test result is counted with that result, whatever the label, because the agent ran to its end
  (finished, timed out, or killed by the task's own memory limit) and the tests ran;
- a trial without a test result is missing: the agent never started (install failed), or the harness skipped or
  timed out the tests. Missing trials are re-run once (job given with --rerun) and the re-run trial is counted in
  their place, with its test result or, if it has none again, as a failure;
- a trial whose agent log holds an error event from the model server is an infrastructure failure, and the summary
  refuses to write a score.
Every trial, counted or replaced, goes to the .jsonl.gz with its status.
"""

import argparse
import gzip
import json
import math
import re
import statistics
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

BENCHMARK = "Terminal-Bench 2.1"
HARNESS = "https://github.com/harbor-framework/harbor v0.27.0, agent opencode (opencode-ai 1.19.6)"
DATA = "https://github.com/harbor-framework/terminal-bench-2-1 @ 12b7565679ce5006230b820666353673a133db93, 89 tasks"
METRIC = "pass rate (task tests pass, reward 1), mean over tasks and trials"
# What vllm.sh serves for each model (kept in step with vllm.sh): written to the result, because the Harbor job
# config does not record the model server.
SERVING = {
    "lfm3-1.7b": {"server": "vllm 0.34.0, bf16",
                  "weights": "LiquidAI/LFM3-1.7B @ 1da06bec6a819da10b54c67e5c90972b46d81871"},
    "bielik-11b-v3.1": {"server": "vllm 0.34.0, bf16",
                        "weights": "speakleash/Bielik-11B-v3.1-Instruct @ d6e755d356ad418d0f0e30b8c428db267415ddb9"},
}


# The full trajectories of one model are about 17 MB compressed, over the repo's 10 MB per file. In the committed
# rows every tool call and every message is kept whole; tool outputs and reasoning longer than these limits keep
# their start and end. Timestamps and per-step token metrics are dropped (totals stay in n_*_tokens).
OBSERVATION_CHARS = 2000
REASONING_CHARS = 3000
DROPPED_STEP_FIELDS = ("timestamp", "metrics", "model_name", "llm_call_count")


def cut(text, limit: int):
    if not isinstance(text, str) or len(text) <= limit:
        return text
    return f"{text[: limit // 2]}\n[... {len(text) - limit} characters cut ...]\n{text[-limit // 2 :]}"


def compact(trajectory: dict | None) -> dict | None:
    if not trajectory:
        return trajectory
    steps = []
    for step in trajectory.get("steps", []):
        step = {k: v for k, v in step.items() if k not in DROPPED_STEP_FIELDS}
        if "reasoning_content" in step:
            step["reasoning_content"] = cut(step["reasoning_content"], REASONING_CHARS)
        observation = step.get("observation") or {}
        for result in observation.get("results", []):
            result["content"] = cut(result.get("content"), OBSERVATION_CHARS)
        steps.append(step)
    return {"session_id": trajectory.get("session_id"), "agent": trajectory.get("agent"), "steps": steps,
            "final_metrics": trajectory.get("final_metrics")}


def agent_events(trial: Path) -> list[dict]:
    log = trial / "agent" / "opencode.txt"
    if not log.exists():
        return []
    events = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("{"):
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def load(job: Path) -> list[dict]:
    rows = []
    for path in sorted(job.glob("*/result.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        exc = r.get("exception_info") or {}
        agent = r.get("agent_result") or {}
        trial = path.parent
        events = agent_events(trial)
        last = events[-1] if events else {}
        value = ((r.get("verifier_result") or {}).get("rewards") or {}).get("reward")
        log_path = trial / "trial.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
        if value is not None:
            status = "scored"
        elif not events:
            status = "agent_not_started"
        elif "VerifierTimeoutError" in log:
            status = "verifier_timeout"
        else:
            status = "no_test_result"
        code = re.search(r"Command failed \(exit (\d+)\)", exc.get("exception_message") or "")
        end = "/".join(x for x in (last.get("type"), (last.get("part") or {}).get("reason")) if x) or None
        trajectory = trial / "agent" / "trajectory.json"
        rows.append(
            {
                "task": r["task_name"].removeprefix("terminal-bench/"),
                "trial": r["trial_name"],
                "job": job.name,
                "status": status,
                "counted": None,
                "score": float(value) if value is not None else None,
                "exception": exc.get("exception_type"),
                "agent_exit_code": int(code.group(1)) if code else None,
                "agent_end": end,
                "model_server_errors": sum(e.get("type") == "error" for e in events),
                "n_input_tokens": agent.get("n_input_tokens"),
                "n_output_tokens": agent.get("n_output_tokens"),
                "output": compact(json.loads(trajectory.read_text(encoding="utf-8"))) if trajectory.exists() else None,
            }
        )
    return rows


def count(main_rows: list[dict], rerun_rows: list[dict]) -> list[str]:
    """Marks which trials are counted and with what score. Returns the problems that block a score."""
    problems = []
    reruns: dict[str, list[dict]] = defaultdict(list)
    for r in rerun_rows:
        reruns[r["task"]].append(r)
    for r in main_rows:
        if r["status"] == "scored":
            r["counted"] = True
            continue
        r["counted"] = False
        if not reruns[r["task"]]:
            problems.append(f"{r['trial']} has no test result ({r['status']}) and no re-run")
            continue
        sub = reruns[r["task"]].pop(0)
        sub["counted"] = True
        sub["replaces"] = r["trial"]
        if sub["score"] is None:
            sub["score"] = 0.0
            sub["counted_as_failure"] = f"no test result after one re-run ({sub['status']})"
    for task, left in reruns.items():
        for r in left:
            r["counted"] = False
            problems.append(f"re-run {r['trial']} replaces nothing in the main job ({task})")
    for r in main_rows + rerun_rows:
        if r["model_server_errors"]:
            problems.append(f"{r['trial']}: {r['model_server_errors']} model-server error events")
    return problems


def tally(rows: list[dict], key: str) -> dict:
    out: dict[str, int] = defaultdict(int)
    for r in rows:
        out[str(r[key])] += 1
    return dict(sorted(out.items()))


def job_settings(job: Path) -> dict | None:
    """The job-level part of Harbor's config (concurrency and the agent), which the trial configs do not hold."""
    path = job / "config.json"
    if not path.exists():
        return None
    config = json.loads(path.read_text(encoding="utf-8"))
    agents = config.get("agents") or [{}]
    return {"job": job.name, "n_concurrent_trials": config.get("n_concurrent_trials"),
            "n_attempts": config.get("n_attempts"), "agent_import_path": agents[0].get("import_path")}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("job", nargs="?", type=Path)
    p.add_argument("--model")
    p.add_argument("--out-dir", type=Path, default=Path(__file__).parent / "results")
    p.add_argument("--null")
    p.add_argument("--out", type=Path)
    p.add_argument("--rerun", type=Path, action="append", default=[], help="a job that re-runs missing trials")
    a = p.parse_args(argv)

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

    main_rows = load(a.job)
    if not main_rows:
        print(f"no trials in {a.job}", file=sys.stderr)
        return 1
    rerun_rows = [r for job in a.rerun for r in load(job)]
    rows = main_rows + rerun_rows
    problems = count(main_rows, rerun_rows)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    counted = [r for r in rows if r["counted"]]

    by_task: dict[str, list[float]] = defaultdict(list)
    for r in counted:
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
    p_trial = sum(r["score"] for r in counted) / len(counted)

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
        "settings": {
            "trials_per_task": trials.pop(),
            "serving": SERVING.get(a.model),
            "jobs": [job_settings(j) for j in [a.job, *a.rerun]],
            "trial_config_example": config,
            "rerun_jobs": [j.name for j in a.rerun],
        },
        "deviations": "see README.md, Deviations",
        "output_field": f"Harbor trajectory; tool outputs over {OBSERVATION_CHARS} and reasoning over "
        f"{REASONING_CHARS} characters keep their start and end; timestamps and per-step metrics dropped",
        "other_metrics": {
            "trials": len(counted),
            "trials_passed": sum(r["score"] == 1.0 for r in counted),
            "stderr_per_trial": round(100 * math.sqrt(p_trial * (1 - p_trial) / len(counted)), 2),
            "trials_rerun": sum(1 for r in counted if r.get("replaces")),
            "rerun_counted_as_failure": sum(1 for r in counted if r.get("counted_as_failure")),
            "agent_end": tally(counted, "agent_end"),
            "agent_exit_code": tally(counted, "agent_exit_code"),
            "harbor_exception_label": tally(counted, "exception"),
            "replaced_trial_status": tally([r for r in rows if not r["counted"]], "status"),
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
