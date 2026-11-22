"""graded.jsonl (scicode_runner.py score) -> results/<model-id>.json and results/<model-id>.jsonl.gz
(research/METHODOLOGY.md).

Usage: python3 summarize.py <out-dir> <results/model-id> [--limit N]
       python3 summarize.py --null <results/model-id> <reason>     (a model that is not run: score null)
A run with --limit is written to <out-dir>/<model-id>-limit<N>.* instead, so a smoke test never replaces a
published result.

Headline (PROTOCOL.md, "Metrics"): correct subproblems / 288 x 100 with background, as test_generated_code.py
prints it; the same without background in `other_metrics`. Each answered step is scored by the scorer; a prompt
over the context (`unsupported`) and an unfinished answer gave empty code and fail like any wrong answer, and are
counted. stderr is `sqrt(p(1-p)/n)`; `stderr_clustered` is the SE clustered by problem (65 clusters on the test
split), which the verdicts use:

    SE_cl = sqrt( G/(G-1) * sum_g ( sum_{i in g} (y_i - p) )^2 ) / n

with G problems, n steps and y_i 1 for a passed step. Main problems solved: a problem counts when all its scored
steps pass (the scorer's rule when every step has a file), out of 65. The scorer's printed counts must equal the
ones recomputed here. The same counts under extraction E1 (PROTOCOL.md Amendment 1) go to
`other_metrics.extraction_e1` and to `score_e1`/`output_e1` per line, never to the headline; the scorer's E1 counts
are checked the same way. Python 3.10+ standard library only (the scoring VM's python3).
"""

import gzip
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import provenance
from scicode_runner import (DATA_REPO, DATA_REVISION, H5_SHA256, SCICODE_COMMIT, SCORER_TIMEOUT_S, SEED, SETTINGS,
                            SPLIT_SIZES, TEMPERATURE, TOP_P, event_counts)

NO_EVENT_LOG = "no api-events.jsonl: this run sent no requests (ground truth) or was not run through the API"


def clustered_se(values: list[float], clusters: list[str]) -> float | None:
    """SE of the mean of `values`, clustered by `clusters` (CR1: G/(G-1) small-sample factor); None below 2
    clusters."""
    n = len(values)
    groups: dict[str, float] = defaultdict(float)
    mean = statistics.fmean(values) if n else 0.0
    for v, c in zip(values, clusters):
        groups[c] += v - mean
    g = len(groups)
    if g < 2:
        return None
    return math.sqrt(g / (g - 1) * sum(s * s for s in groups.values())) / n


def rate(passed: list[bool], clusters: list[str]) -> dict[str, Any]:
    """Pass rate in percent with the binomial and the clustered stderr; score null when nothing was scored."""
    n = len(passed)
    if not n:
        return {"score": None, "stderr": None, "stderr_clustered": None, "n": 0}
    p = sum(passed) / n
    se_cl = clustered_se([float(x) for x in passed], clusters)
    return {"score": round(100 * p, 2), "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2),
            "stderr_clustered": None if se_cl is None else round(100 * se_cl, 2), "n": n, "correct": sum(passed),
            "clusters": len(set(clusters))}


def problems_solved(records: list[dict[str, Any]], key: str = "pass") -> dict[str, Any]:
    by_problem: dict[str, list[bool]] = defaultdict(list)
    for r in records:
        by_problem[r["problem_id"]].append(bool(r[key]))
    solved = sorted((p for p, steps in by_problem.items() if all(steps)), key=int)
    return {"solved": len(solved), "of": len(by_problem), "solved_ids": solved}


def extraction_metrics(records: list[dict[str, Any]], extraction: str) -> dict[str, Any]:
    """Pass rate, clustered SE, main problems and verdicts of one extraction's scoring (`e1`: Amendment 1), with the
    number of steps whose E1 file was identical to the official one and took its verdict (`reused_identical`)."""
    p, v = f"pass_{extraction}", f"verdict_{extraction}"
    reused = sum(1 for r in records if r[f"{extraction}_reused"])
    return {**rate([bool(r[p]) for r in records], [r["problem_id"] for r in records]),
            "main_problems": problems_solved(records, p),
            "verdicts": {x: sum(1 for r in records if r[v] == x) for x in sorted({r[v] for r in records})},
            "reused_identical": reused, "scored": len(records) - reused}


def setting_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    answered = [r for r in records if r["status"] == "ok"]
    tokens = [r["output_tokens"] for r in answered if r["output_tokens"] is not None]
    return {
        **rate([bool(r["pass"]) for r in records], [r["problem_id"] for r in records]),
        "main_problems": problems_solved(records),
        "verdicts": {v: sum(1 for r in records if r["verdict"] == v) for v in sorted({r["verdict"] for r in records})},
        "timeouts": sum(1 for r in records if r["verdict"] == "time out"),
        "output_tokens": {"mean": round(statistics.mean(tokens), 1) if tokens else None,
                          "median": statistics.median(tokens) if tokens else None,
                          "max": max(tokens) if tokens else None},
        "unfinished": sum(1 for r in answered if r["unfinished"]),
        "length_stops": sum(1 for r in answered if r["finish_reason"] == "length"),
        "unsupported": sum(1 for r in records if r["status"] == "unsupported"),
        "answers_with_think_open": {"count": sum(1 for r in answered if r["think_open"]), "of": len(answered),
                                    "share": round(sum(1 for r in answered if r["think_open"]) / len(answered), 4)
                                    if answered else None},
        **api_prompt_check(answered),
    }


def api_prompt_check(answered: list[dict[str, Any]]) -> dict[str, Any]:
    """Hosted API only: the API's prompt count minus ours, and the largest prompt + output it billed."""
    pairs = [(r["api_prompt_tokens"], r) for r in answered if r.get("api_prompt_tokens") is not None]
    if not pairs:
        return {}
    diffs = [api - r["prompt_tokens"] for api, r in pairs]
    return {"api_prompt_minus_local": {"min": min(diffs), "max": max(diffs)},
            "api_prompt_plus_output_max": max(api + r["output_tokens"] for api, r in pairs)}


def check_against_scorer(setting: str, m: dict[str, Any], printed: dict[str, Any]) -> None:
    """The scorer's printed counts (its own reading of the same logs) must equal ours."""
    ours = (m["correct"], m["main_problems"]["solved"])
    theirs = (printed["correct_steps"], printed["correct_problems"])
    if ours != theirs:
        sys.exit(f"summarize.py: {setting}: correct steps and problems {ours} here, {theirs} printed by the scorer")


def check_e1_against_scorer(setting: str, m: dict[str, Any], run: dict[str, Any]) -> None:
    """E1: the scorer ran only on the steps whose E1 file differs from the official one, so its printed correct
    steps plus the reused official passes must equal ours, and the reused count must match (its printed problem
    count covers only the scored files and is not compared)."""
    printed = run["printed"]["correct_steps"] if run["printed"] else 0
    ours = (m["correct"], m["reused_identical"])
    theirs = (printed + run["reused_passes"], run["reused_identical"])
    if ours != theirs:
        sys.exit(f"summarize.py: {setting}: correct steps and reused steps {ours} here, {theirs} from the scorer "
                 "and the reused official verdicts")


def run_record(out_dir: Path) -> dict[str, Any]:
    path = out_dir / "run.json"
    if not path.is_file():
        sys.exit(f"summarize.py: {path} is missing; scicode_runner.py generate and score write it")
    run = json.loads(path.read_text(encoding="utf-8"))
    if not run.get("generation") or "scoring" not in run:
        sys.exit(f"summarize.py: {path} lacks the generation or scoring record")
    samplings = {json.dumps(g["sampling"], sort_keys=True) for g in run["generation"]}
    if len(samplings) != 1:
        sys.exit(f"summarize.py: the generation sessions in {path} used different sampling settings: {samplings}")
    return run


def api_events(out_dir: Path, model: str) -> dict[str, Any]:
    if "api-events.jsonl" not in provenance.read_manifest(out_dir)["files"]:
        return {"api_events": None, "api_events_reason": NO_EVENT_LOG}
    sha = provenance.verify(out_dir, ["api-events.jsonl"], "summarize.py")["api-events.jsonl"]
    lines = (out_dir / "api-events.jsonl").read_text(encoding="utf-8").splitlines()
    counts = event_counts([json.loads(line) for line in lines if line.strip()])
    return {"api_events": {"file": f"out/{model}/api-events.jsonl (not committed)", "sha256": sha, **counts}}


def write_result(target: str, result: dict[str, Any], lines: list[dict[str, Any]] | None) -> None:
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    names = [f"{Path(target).name}.json"]
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if lines is not None:
        with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
            for line in lines:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
        size = Path(f"{target}.jsonl.gz").stat().st_size
        if size > 10 * 1024 * 1024:
            sys.exit(f"summarize.py: {target}.jsonl.gz is {size} bytes, over the 10 MB limit of the repo")
        names.append(f"{Path(target).name}.jsonl.gz")
    provenance.record(Path(target).parent, names, "summarize.py")


def null_result(target: str, reason: str) -> None:
    model = Path(target).name
    result = {"benchmark": "SciCode", "model": model, "metric": "subproblem pass rate, with background",
              "score": None, "stderr": None, "n": 0, "date": None, "reason": reason,
              "harness": f"https://github.com/scicode-bench/SciCode @ {SCICODE_COMMIT}",
              "data": f"https://huggingface.co/datasets/{DATA_REPO} @ {DATA_REVISION}, test", "settings": None,
              "deviations": "see README.md, Deviations"}
    write_result(target, result, None)
    print(json.dumps(result, indent=2))


def main(out_dir: str, target: str, limit: int | None) -> None:
    out = Path(out_dir)
    hashes = provenance.verify(out, ["graded.jsonl"], "summarize.py")
    run = run_record(out)
    split = run["scoring"]["split"]
    raw_sha = provenance.read_manifest(out)["files"].get("generations.jsonl", {}).get("sha256")
    records = [json.loads(line) for line in (out / "graded.jsonl").read_text(encoding="utf-8").splitlines() if line]
    model = Path(target).name
    if limit:
        target = str(out / f"{model}-limit{limit}")
        print(f"summarize.py: --limit {limit}, writing to {target}.* (not results/)")
    if run["scoring"]["limit"] != limit:
        sys.exit(f"summarize.py: scored with --limit {run['scoring']['limit']}, summarizing with --limit {limit}")
    settings = [s for s in SETTINGS if any(r["setting"] == s for r in records)]
    per_setting, per_setting_e1 = {}, {}
    for s in settings:
        rs = [r for r in records if r["setting"] == s]
        if not limit and len(rs) != SPLIT_SIZES[split]["steps"]:
            sys.exit(f"summarize.py: {s} has {len(rs)} steps, expected {SPLIT_SIZES[split]['steps']} on {split}")
        m = setting_metrics(rs)
        check_against_scorer(s, m, run["scoring"]["runs"][s]["printed"])
        per_setting[s] = m
        e1 = extraction_metrics(rs, "e1")
        check_e1_against_scorer(f"e1/{s}", e1, run["scoring"]["runs"][f"e1/{s}"])
        per_setting_e1[s] = e1
    head = per_setting["with_background"]
    started = sorted(r["started"] for r in records if r["started"])
    contexts = sorted({r["context"] for r in records if r["context"]})
    margins = sorted({r["context"] - r["prompt_tokens"] - r["max_tokens"] for r in records
                      if r["status"] == "ok" and r.get("max_tokens") is not None})
    gen0 = run["generation"][0]
    scoring = run["scoring"]
    result = {
        "benchmark": "SciCode" + ("" if split == "test" else f" ({split} split)"),
        "model": model,
        "metric": "subproblem pass rate, with background (correct steps / 288 x 100, test_generated_code.py)",
        "score": head["score"],
        "stderr": head["stderr"],
        "stderr_clustered": head["stderr_clustered"],
        "n": head["n"],
        "date": started[0][:10] if started else None,
        "harness": f"https://github.com/scicode-bench/SciCode @ {SCICODE_COMMIT}",
        "data": f"https://huggingface.co/datasets/{DATA_REPO} @ {DATA_REVISION}, {split}; test_data.h5 sha256 "
                f"{H5_SHA256}",
        "settings": {
            "prompt": "SciCode Gencode (eval/scripts/gencode.py), one user message per subproblem, no system message",
            "settings_run": settings,
            "temperature": TEMPERATURE, "top_p": TOP_P, "seed": SEED,
            "thinking": gen0.get("thinking"),
            "max_tokens": ("context minus prompt tokens" if margins in ([], [0])
                           else f"context minus prompt tokens minus a margin of {', '.join(map(str, margins))}"),
            "context": contexts[0] if len(contexts) == 1 else contexts,
            "trials": 1,
            "scored_text": "extract_python_script of the text after the last </think> (empty when unfinished with "
                           "thinking on)",
            "scorer_timeout_s": SCORER_TIMEOUT_S,
            "blas_threads": 1,
            **gen0["sampling"],
        },
        "other_metrics": {
            "with_background": {k: v for k, v in head.items() if k not in ("score", "stderr", "n")},
            **{s: per_setting[s] for s in settings if s != "with_background"},
            "extraction_e1": {"note": "PROTOCOL.md Amendment 1, secondary: the same answers with extraction E1, "
                                      "scored by the same scorer; never the headline", **per_setting_e1},
        },
        "deviations": "see README.md, Deviations",
        "provenance": {
            "generation": [{k: v for k, v in g.items() if k != "sampling"} for g in run["generation"]],
            "scoring": scoring,
            "summary": provenance.step("summarize.py"),
            "inputs_sha256": hashes,
            **api_events(out, model),
        },
        "raw_outputs": {"file": f"out/{model}/generations.jsonl (with thinking; not committed)", "sha256": raw_sha,
                        "jsonl_gz_output": "the code extract_python_script took from the text after the last </think>"},
    }
    lines = [{
        "task_id": f"{r['setting']}/{r['problem_id']}.{r['step']}",
        "score": int(r["pass"]),
        **{k: r[k] for k in ("setting", "problem_id", "step", "step_id", "verdict", "pass", "status", "prompt_tokens",
                             "output_tokens", "finish_reason", "unfinished", "think_open", "api_prompt_tokens")},
        "output": r["code"],
        "score_e1": int(r["pass_e1"]),
        "verdict_e1": r["verdict_e1"],
        "output_e1": r["code_e1"],
        "e1_reused": r["e1_reused"],
    } for r in records]
    write_result(target, result, lines)
    print(json.dumps({k: result[k] for k in ("model", "score", "stderr", "stderr_clustered", "n")} |
                     {"other_metrics": {s: {k: v for k, v in m.items() if k in ("score", "correct", "n",
                                                                                 "main_problems", "timeouts")}
                                        for s, m in per_setting.items()},
                      "extraction_e1": {s: {k: v for k, v in m.items() if k in ("score", "correct", "n")}
                                        for s, m in per_setting_e1.items()}}, indent=2))


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "--null":
        null_result(argv[1], argv[2])
        sys.exit(0)
    limit_arg = None
    if "--limit" in argv:
        i = argv.index("--limit")
        limit_arg = int(argv[i + 1])
        del argv[i:i + 2]
    main(argv[0], argv[1], limit_arg)
