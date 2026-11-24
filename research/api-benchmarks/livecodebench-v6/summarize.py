"""graded.jsonl (lcb.py score) -> results/<model-id>.json and results/<model-id>.jsonl.gz (research/METHODOLOGY.md).

Usage: python summarize.py <out-dir> <results/model-id> [--limit N]
A run with --limit is written to <out-dir>/<model-id>-limit<N>.* instead, so a smoke test never replaces a
published result.

Only answered problems (`status: ok`) are scored. A request that failed in our infrastructure (`error`) or a
prompt that does not fit the context (`unsupported`) is left out of n and counted on its own, never as a wrong
answer (PROTOCOL.md, "Settings").

graded.jsonl must still have the sha256 `lcb.py score` recorded in `<out-dir>/manifest.json`, and
`<out-dir>/run.json` must hold the generation and scoring records (code commit, runner checksums, machine,
sampling in effect); both go into the result file. The retries, pauses and HTTP errors of the requests come from
`<out-dir>/api-events.jsonl` (sha256 checked; counts in `provenance.api_events`), or are `null` with the reason for
a run that has no such log. The sha256 of the two files written here goes into `manifest.json` next to them, which
compare.py checks.
"""

import gzip
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

import provenance
from lcb import (DATA_REPO, DATA_REVISION, EVAL_PROCESSES, EVAL_TIMEOUT, LCB_COMMIT, PROMPT_STYLE, SEED, TEMPERATURE,
                 TOP_P, event_counts)

BUDGETS = (4096, 16384)  # PROTOCOL.md, "Metrics"; "no limit" is the main score
DIFFICULTIES = ("easy", "medium", "hard")
RUNNER_ERROR = -5  # LiveCodeBench's evaluator: an exception in its test runner, which it grades as a fail
NO_EVENT_LOG = ("no api-events.jsonl was recorded for this run (generated before lcb.py logged retries), so its "
                "retries, pauses and HTTP errors are unknown")


def pass_rate(passed: list[bool]) -> dict[str, Any]:
    """pass@1 in percent with stderr sqrt(p(1-p)/n); score null when nothing was scored."""
    n = len(passed)
    if not n:
        return {"score": None, "stderr": None, "n": 0}
    p = sum(passed) / n
    return {"score": round(100 * p, 2), "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2), "n": n}


def passes_within(record: dict[str, Any], budget: int) -> bool:
    """Counts at budget B only if the answer finished within B output tokens (PROTOCOL.md, "Metrics")."""
    return bool(record["pass"]) and bool(record["finished"]) and record["output_tokens"] <= budget


def metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    scored = [r for r in records if r["status"] == "ok"]
    main = pass_rate([bool(r["pass"]) for r in scored])
    tokens = [r["output_tokens"] for r in scored]
    return {
        **main,
        "v6_only": pass_rate([bool(r["pass"]) for r in scored if r["in_v6_only"]]),
        "per_difficulty": {d: pass_rate([bool(r["pass"]) for r in scored if r["difficulty"] == d])
                           for d in DIFFICULTIES},
        "pass_at_budget": {str(b): pass_rate([passes_within(r, b) for r in scored]) for b in BUDGETS},
        "output_tokens": {"mean": round(statistics.mean(tokens), 1) if tokens else None,
                          "median": statistics.median(tokens) if tokens else None,
                          "max": max(tokens) if tokens else None},
        "problems": len(records),
        "unfinished": sum(1 for r in scored if not r["finished"]),
        "errors": sum(1 for r in records if r["status"] == "error"),
        "unsupported": sum(1 for r in records if r["status"] == "unsupported"),
        "evaluator_runner_errors": sum(1 for r in scored if (r["eval_metadata"] or {}).get("error_code") == RUNNER_ERROR),
        **api_prompt_check(scored),
    }


def api_prompt_check(scored: list[dict[str, Any]]) -> dict[str, Any]:
    """Hosted API only: the API's prompt count minus ours, and the largest prompt + output it billed, to check that
    the margin covered what the API's own rendering adds (README, Deviations)."""
    pairs = [(r["api_prompt_tokens"], r) for r in scored if r.get("api_prompt_tokens") is not None]
    if not pairs:
        return {}
    diffs = [api - r["prompt_tokens"] for api, r in pairs]
    return {"api_prompt_minus_local": {"min": min(diffs), "max": max(diffs)},
            "api_prompt_plus_output_max": max(api + r["output_tokens"] for api, r in pairs)}


def margin_of(records: list[dict[str, Any]]) -> list[int]:
    """Tokens kept free beyond the counted prompt: 0 on our vLLM, the --margin on a hosted API."""
    return sorted({r["context"] - r["prompt_tokens"] - r["max_tokens"]
                   for r in records if r["status"] == "ok" and r.get("max_tokens") is not None})


def run_record(out_dir: Path) -> dict[str, Any]:
    """run.json of the run: the generation sessions (all with the same sampling) and the scoring step."""
    path = out_dir / "run.json"
    if not path.is_file():
        sys.exit(f"summarize.py: {path} is missing; lcb.py generate and score write it (code commit, machine, "
                 "sampling in effect), and a result without it cannot say what produced it")
    run = json.loads(path.read_text(encoding="utf-8"))
    if not run.get("generation") or "scoring" not in run:
        sys.exit(f"summarize.py: {path} lacks the generation or scoring record; run lcb.py generate and score")
    samplings = {json.dumps(g["sampling"], sort_keys=True) for g in run["generation"]}
    if len(samplings) != 1:
        sys.exit(f"summarize.py: the generation sessions in {path} used different sampling settings: {samplings}")
    return run


def api_events(out_dir: Path, run: dict[str, Any], model: str) -> dict[str, Any]:
    """Counts of the run's api-events.jsonl (checked against the manifest), or null with the reason."""
    if "api-events.jsonl" not in provenance.read_manifest(out_dir)["files"]:
        reasons = sorted({g["api_events_reason"] for g in run["generation"] if g.get("api_events_reason")})
        return {"api_events": None, "api_events_reason": "; ".join(reasons) or NO_EVENT_LOG}
    sha = provenance.verify(out_dir, ["api-events.jsonl"], "summarize.py")["api-events.jsonl"]
    lines = (out_dir / "api-events.jsonl").read_text(encoding="utf-8").splitlines()
    counts = event_counts([json.loads(line) for line in lines if line.strip()])
    return {"api_events": {"file": f"out/{model}/api-events.jsonl (not committed)", "sha256": sha, **counts}}


def main(out_dir: str, target: str, limit: int | None) -> None:
    path = Path(out_dir) / "graded.jsonl"
    hashes = provenance.verify(Path(out_dir), ["graded.jsonl"], "summarize.py")
    run = run_record(Path(out_dir))
    raw_sha = provenance.read_manifest(Path(out_dir))["files"].get("generations.jsonl", {}).get("sha256")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    model = Path(target).name
    if limit:
        if len(records) != limit:
            sys.exit(f"summarize.py: {path} has {len(records)} problems, not --limit {limit}; run lcb.py score")
        target = str(Path(out_dir) / f"{model}-limit{limit}")
        print(f"summarize.py: --limit {limit}, writing to {target}.* (not results/)")
    m = metrics(records)
    started = sorted(r["started"] for r in records if r["started"])
    contexts = sorted({r["context"] for r in records if r["context"]})
    margins = margin_of(records)
    reason = None
    if m["score"] is None:
        reason = "no problem was answered: " + "; ".join(sorted({r["error"] for r in records if r["error"]}))
    result = {
        "benchmark": "LiveCodeBench v6 (code generation, release_v6)",
        "model": model,
        "metric": "pass@1",
        "score": m["score"],
        "stderr": m["stderr"],
        "n": m["n"],
        "date": started[0][:10] if started else None,  # UTC day of the first request
        "harness": f"https://github.com/LiveCodeBench/LiveCodeBench @ {LCB_COMMIT}",
        "data": f"https://huggingface.co/datasets/{DATA_REPO} @ {DATA_REVISION}, release_v6",
        "settings": {
            "prompt_style": PROMPT_STYLE,
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "seed": SEED,
            "max_tokens": ("context minus prompt tokens" if margins in ([], [0])
                           else f"context minus prompt tokens minus a margin of {', '.join(map(str, margins))}"),
            "context": contexts[0] if len(contexts) == 1 else contexts,
            "trials": 1,
            "scored_text": "after the last </think>",
            "eval_timeout_s": EVAL_TIMEOUT,
            "eval_processes": EVAL_PROCESSES,
            **run["generation"][0]["sampling"],
        },
        "other_metrics": {k: v for k, v in m.items() if k not in ("score", "stderr", "n")},
        "deviations": "see README.md, Deviations",
        "provenance": {
            "generation": [{k: v for k, v in g.items() if k != "sampling"} for g in run["generation"]],
            "scoring": run["scoring"],
            "summary": provenance.step("summarize.py"),
            "inputs_sha256": hashes,
            **api_events(Path(out_dir), run, model),
        },
        "raw_outputs": {"file": f"out/{model}/generations.jsonl (with thinking; not committed)", "sha256": raw_sha,
                        "jsonl_gz_output": "the code LiveCodeBench extracted from the text after the last </think>"},
    }
    if reason:
        result["reason"] = reason
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps({
                "task_id": r["question_id"],
                "score": None if r["pass"] is None else int(r["pass"]),
                **{k: r[k] for k in ("difficulty", "contest_date", "platform", "in_v6_only", "status", "pass",
                                     "prompt_tokens", "output_tokens", "finished", "finish_reason", "error",
                                     "eval_metadata")},
                "api_prompt_tokens": r.get("api_prompt_tokens"),
                "output": r["code"],  # the code LiveCodeBench extracted and ran; no thinking
            }, ensure_ascii=False) + "\n")
    size = Path(f"{target}.jsonl.gz").stat().st_size
    if size > 10 * 1024 * 1024:
        sys.exit(f"summarize.py: {target}.jsonl.gz is {size} bytes, over the 10 MB limit of the repo")
    provenance.record(Path(target).parent, [f"{Path(target).name}.json", f"{Path(target).name}.jsonl.gz"],
                      "summarize.py")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    argv = sys.argv[1:]
    limit_arg = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit_arg = int(argv[i + 1])
        del argv[i:i + 2]
    main(argv[0], argv[1], limit_arg)
