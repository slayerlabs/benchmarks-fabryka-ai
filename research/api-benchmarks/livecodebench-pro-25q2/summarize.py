"""graded.jsonl (lcbpro.py score) -> results/<model-id>.json and results/<model-id>.jsonl.gz
(research/api-benchmarks/README.md).

Usage: python summarize.py <out-dir> <results/model-id> [--limit N]
       python summarize.py --not-run <results/model-id> <reason>
A run with --limit is written to <out-dir>/<model-id>-limit<N>.* instead, so a smoke test never replaces a
published result. `--not-run` writes the `score: null` file of a model the protocol does not run, with the reason.

Metrics (PROTOCOL.md, "Metrics"):
- headline `score`: accepted / all problems x 100 (167 for the full split), every problem that is not accepted
  counting as a fail, including a missing test zip and judge or request errors that persisted after their retry;
  `stderr` sqrt(p(1-p)/n) on the same n;
- `other_metrics.secondary`: the same with the problems left out whose zip is missing or whose judging or request
  failed in the infrastructure (or whose prompt did not fit the context), with their count by reason;
- accepted / n per difficulty (headline basis), the count of each judge category, output tokens per answer,
  unfinished answers (thinking on), length stops, and the share of answers containing `<think>`.

graded.jsonl must still have the sha256 `lcbpro.py score` recorded in `<out-dir>/manifest.json`, and
`<out-dir>/run.json` must hold the generation and scoring records (code commit, runner checksums, machine,
sampling in effect, judge image); they go into the result file. The retries, pauses and HTTP errors of the
requests come from `<out-dir>/api-events.jsonl` (sha256 checked). The sha256 of the two files written here goes into
`manifest.json` next to them, which compare.py checks.
"""

import gzip
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

import provenance
from lcbpro import (CATEGORIES, DATA_REPO, DATA_REVISION, HARNESS_COMMIT, HARNESS_REPO, JUDGE_WORKERS, N_PROBLEMS,
                    SEED, SPLIT, TEMPERATURE, TESTS_REPO, TESTS_REVISION, TOP_P, VERIFIER_COMMIT, event_counts)

BENCHMARK = "LiveCodeBench Pro 25Q2 (quater_2025_4_6)"
# PROTOCOL.md, "Metrics": left out of the secondary score (not the model's fault, or not judgeable)
EXCLUDED_IN_SECONDARY = ("no_tests", "judge_error", "request_error", "unsupported")


def pass_rate(accepted: list[bool]) -> dict[str, Any]:
    """accepted share in percent with stderr sqrt(p(1-p)/n); score null when n is 0."""
    n = len(accepted)
    if not n:
        return {"score": None, "stderr": None, "n": 0, "accepted": 0}
    p = sum(accepted) / n
    return {"score": round(100 * p, 2), "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2), "n": n,
            "accepted": sum(accepted)}


def metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    accepted = [bool(r["accepted"]) for r in records]
    kept = [r for r in records if r["category"] not in EXCLUDED_IN_SECONDARY]
    answered = [r for r in records if r["status"] == "ok"]
    tokens = [r["output_tokens"] for r in answered]
    difficulties = sorted({r["difficulty"] for r in records})
    unknown = sorted({r["category"] for r in records} - set(CATEGORIES))
    if unknown:
        raise ValueError(f"unknown categories in graded.jsonl: {unknown}")
    return {
        **pass_rate(accepted),
        "secondary": {**pass_rate([bool(r["accepted"]) for r in kept]),
                      "left_out": {c: sum(1 for r in records if r["category"] == c) for c in EXCLUDED_IN_SECONDARY}},
        "per_difficulty": {d: pass_rate([bool(r["accepted"]) for r in records if r["difficulty"] == d])
                           for d in difficulties},
        "categories": {c: sum(1 for r in records if r["category"] == c) for c in CATEGORIES},
        "output_tokens": {"mean": round(statistics.mean(tokens), 1) if tokens else None,
                          "median": statistics.median(tokens) if tokens else None,
                          "max": max(tokens) if tokens else None},
        "problems": len(records),
        "unfinished": sum(1 for r in records if r["unfinished"]),
        "length_stops": sum(1 for r in answered if r["finish_reason"] == "length"),
        "think_in_output": {"answers": sum(1 for r in answered if r["think_in_output"]), "of": len(answered),
                            "share": round(sum(1 for r in answered if r["think_in_output"]) / len(answered), 4)
                            if answered else None},
        "no_tests": sorted(r["problem_id"] for r in records if not r["has_tests"]),
        **api_prompt_check(answered),
    }


def api_prompt_check(answered: list[dict[str, Any]]) -> dict[str, Any]:
    """Hosted API only: the API's prompt count minus ours, and the largest prompt + output it billed, to check that
    the margin covered what the API's own rendering adds (README, Deviations)."""
    pairs = [(r["api_prompt_tokens"], r) for r in answered if r.get("api_prompt_tokens") is not None]
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
        sys.exit(f"summarize.py: {path} is missing; lcbpro.py generate and score write it (code commit, machine, "
                 "sampling in effect, judge), and a result without it cannot say what produced it")
    run = json.loads(path.read_text(encoding="utf-8"))
    if not run.get("generation") or "scoring" not in run:
        sys.exit(f"summarize.py: {path} lacks the generation or scoring record; run lcbpro.py generate and score")
    samplings = {json.dumps(g["sampling"], sort_keys=True) for g in run["generation"]}
    if len(samplings) != 1:
        sys.exit(f"summarize.py: the generation sessions in {path} used different sampling settings: {samplings}")
    return run


NO_EVENT_LOG = "no api-events.jsonl: this run sent no requests (Slayer local generation) or was not run through the API"


def api_events(out_dir: Path, model: str) -> dict[str, Any]:
    """Counts of the run's api-events.jsonl, checked against the manifest."""
    if "api-events.jsonl" not in provenance.read_manifest(out_dir)["files"]:
        return {"api_events": None, "api_events_reason": NO_EVENT_LOG}
    sha = provenance.verify(out_dir, ["api-events.jsonl"], "summarize.py")["api-events.jsonl"]
    lines = (out_dir / "api-events.jsonl").read_text(encoding="utf-8").splitlines()
    counts = event_counts([json.loads(line) for line in lines if line.strip()])
    return {"api_events": {"file": f"out/{model}/api-events.jsonl (not committed)", "sha256": sha, **counts}}


def test_zips(out_dir: Path, model: str, run: dict[str, Any]) -> dict[str, Any]:
    """The test zips the run was judged on: tests.json (checked against the manifest) with its revision and the
    sha256 of every zip, and the `lcbpro.py tests` step record when run.json has one (runs before it recorded the
    step have only the file)."""
    sha = provenance.verify(out_dir, ["tests.json"], "summarize.py")["tests.json"]
    record = json.loads((out_dir / "tests.json").read_text(encoding="utf-8"))
    return {"file": f"out/{model}/tests.json (not committed)", "sha256": sha, "repo": record["repo"],
            "revision": record["revision"], "missing": record["missing"],
            "zip_sha256": {pid: f["sha256"] for pid, f in sorted(record["files"].items()) if f is not None},
            "step": run.get("tests")}


def write_result(target: str, result: dict[str, Any], rows: list[dict[str, Any]] | None) -> None:
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    names = [f"{Path(target).name}.json"]
    if rows is not None:
        with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        size = Path(f"{target}.jsonl.gz").stat().st_size
        if size > 10 * 1024 * 1024:
            sys.exit(f"summarize.py: {target}.jsonl.gz is {size} bytes, over the 10 MB limit of the repo")
        names.append(f"{Path(target).name}.jsonl.gz")
    provenance.record(Path(target).parent, names, "summarize.py")


def base(model: str) -> dict[str, Any]:
    return {"benchmark": BENCHMARK, "model": model, "metric": "pass@1 (accepted / all problems, percent)",
            "harness": f"{HARNESS_REPO} @ {HARNESS_COMMIT} (LightCPVerifier @ {VERIFIER_COMMIT})",
            "data": f"https://huggingface.co/datasets/{DATA_REPO} @ {DATA_REVISION}, split {SPLIT}; tests "
                    f"https://huggingface.co/datasets/{TESTS_REPO} @ {TESTS_REVISION}"}


def not_run(target: str, reason: str) -> None:
    model = Path(target).name
    write_result(target, {**base(model), "score": None, "stderr": None, "n": 0, "date": None, "settings": None,
                          "deviations": "see README.md, Deviations", "reason": reason}, None)
    print(Path(f"{target}.json").read_text(encoding="utf-8"))


def main(out_dir: str, target: str, limit: int | None) -> None:
    out = Path(out_dir)
    path = out / "graded.jsonl"
    hashes = provenance.verify(out, ["graded.jsonl"], "summarize.py")
    run = run_record(out)
    raw_sha = provenance.read_manifest(out)["files"].get("generations.jsonl", {}).get("sha256")
    records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    model = Path(target).name
    expected = limit or N_PROBLEMS
    if len(records) != expected:
        sys.exit(f"summarize.py: {path} has {len(records)} problems, expected {expected}; run lcbpro.py score")
    if limit:
        target = str(out / f"{model}-limit{limit}")
        print(f"summarize.py: --limit {limit}, writing to {target}.* (not results/)")
    m = metrics(records)
    started = sorted(r["started"] for r in records if r["started"])
    contexts = sorted({r["context"] for r in records if r["context"]})
    margins = margin_of(records)
    scoring = run["scoring"]
    result = {
        **base(model),
        "score": m["score"],
        "stderr": m["stderr"],
        "n": m["n"],
        "date": started[0][:10] if started else None,  # UTC day of the first request
        "settings": {
            "prompt": "api_interface.LLMInterface().prompt + problem_statement, the only user message",
            "temperature": TEMPERATURE,
            "top_p": TOP_P,
            "seed": SEED,
            "max_tokens": ("context minus prompt tokens" if margins in ([], [0])
                           else f"context minus prompt tokens minus a margin of {', '.join(map(str, margins))}"),
            "context": contexts[0] if len(contexts) == 1 else contexts,
            "trials": 1,
            "scored_text": "after the last </think>, code by util.extract_longest_cpp_code",
            "unfinished": "thinking on: no </think> or finish_reason other than stop; counted as not accepted",
            "judge": scoring["judge"],
            "judge_workers": JUDGE_WORKERS,
            "judge_machine": {k: scoring.get(k) for k in ("cpu", "cpu_count", "platform")},
            **run["generation"][0]["sampling"],
        },
        "other_metrics": {k: v for k, v in m.items() if k not in ("score", "stderr", "n")},
        "deviations": "see README.md, Deviations",
        "provenance": {
            "generation": [{k: v for k, v in g.items() if k != "sampling"} for g in run["generation"]],
            "tests": test_zips(out, model, run),
            "scoring": scoring,
            "summary": provenance.step("summarize.py"),
            "inputs_sha256": hashes,
            **api_events(out, model),
        },
        "raw_outputs": {"file": f"out/{model}/generations.jsonl (with thinking; not committed)", "sha256": raw_sha,
                        "jsonl_gz_output": "the code extracted from the text after the last </think>"},
    }
    rows = [{"task_id": r["problem_id"], "score": int(bool(r["accepted"])),
             **{k: r[k] for k in ("problem_title", "difficulty", "platform", "category", "verdict", "accepted",
                                  "has_tests", "status", "finish_reason", "unfinished", "think_in_output",
                                  "prompt_tokens", "output_tokens", "api_prompt_tokens", "error", "judge_error",
                                  "judge_message", "cases_run", "judge_attempts")},
             "output": r["code"]} for r in records]
    write_result(target, result, rows)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "--not-run":
        not_run(argv[1], argv[2])
        sys.exit(0)
    limit_arg = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit_arg = int(argv[i + 1])
        del argv[i:i + 2]
    main(argv[0], argv[1], limit_arg)
