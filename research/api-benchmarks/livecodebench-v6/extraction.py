"""Exploratory, added after the results (not in PROTOCOL.md): how much the code extraction moves the scores.

LiveCodeBench's extraction for chat models (`extract_code`, OpenAIChat style) takes the lines between the last two
lines that contain three backticks; an answer with fewer than two such lines gives empty code, which its evaluator
grades as a fail. Rule F1 (fixed by the method refutation before it regraded anything) repairs a fence left out:

    exactly one fence line -> the lines before it (the lines after it when only whitespace precedes it);
    no fence line          -> the whole text;
    otherwise              -> LiveCodeBench's code, unchanged.

F1 is applied to the text after the last `</think>` of every answered problem of every run; only the answers whose
F1 code differs from LiveCodeBench's go through LiveCodeBench's evaluator again (same per-test timeout, on this
machine's CPU), the rest keep their official grade. The official results are not changed.

Usage (in the LiveCodeBench venv, with the pinned clone in .cache/LiveCodeBench, as `lcb.py score`):

    python extraction.py [out-dir] [results-dir] [--processes N]   (defaults: out/, results/, 8 processes)

Reads the raw generations out/<model-id>/<file> (sha256 checked against out/<model-id>/manifest.json) and
results/<model-id>.jsonl.gz (checked against results/manifest.json), stops unless LiveCodeBench's extraction of
each raw answer is the code in the result file, and writes results/extraction-f1.json with its sha256 in
results/manifest.json. compare.py reads it for its exploratory rows.
"""

import argparse
import collections
import gzip
import json
import sys
from pathlib import Path
from typing import Any

import lcb
import provenance

HERE = Path(__file__).resolve().parent
RUNS = ("lfm3-1.7b", "lfm3-1.7b-cardsampling", "bielik-11b-v3.1")
RAW = {"lfm3-1.7b": "lfm3-lcb-generations.jsonl.gz"}  # kept gzipped (README, Deviations); the others: generations.jsonl
OUTPUT = "extraction-f1.json"
FENCE = "```"
RULE = ("F1: with exactly one line containing three backticks, the lines before it (after it when only whitespace "
        "precedes it); with none, the whole text; otherwise LiveCodeBench's extraction (the last two such lines)")


def fence_lines(text: str) -> list[int]:
    """Indexes of the lines LiveCodeBench's extraction treats as fences."""
    return [i for i, line in enumerate(text.split("\n")) if FENCE in line]


def f1(text: str, official: str) -> str:
    """Rule F1 on the text after `</think>`; `official` is LiveCodeBench's code for the same text."""
    lines, idx = text.split("\n"), fence_lines(text)
    if not idx:
        return text
    if len(idx) == 1:
        before = "\n".join(lines[:idx[0]])
        return before if before.strip() else "\n".join(lines[idx[0] + 1:])
    return official


def read_raw(path: Path) -> dict[str, dict[str, Any]]:
    """The raw answers by question_id; the last record of a problem wins, as in `lcb.py score`."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return {r["question_id"]: r for r in map(json.loads, filter(str.strip, f))}


def read_result(results: Path, run: str) -> tuple[dict[str, dict[str, Any]], str]:
    """results/<run>.jsonl.gz by task_id, and its sha256 (checked against results/manifest.json)."""
    sha = provenance.verify(results, [f"{run}.jsonl.gz"], "extraction.py")[f"{run}.jsonl.gz"]
    with gzip.open(results / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}, sha


def main(out_root: Path, results: Path, processes: int, modules: Any = None) -> None:
    """`modules`: LiveCodeBench's (lcb.lcb_modules(), which changes the working directory) unless given."""
    out_root, results = out_root.resolve(), results.resolve()
    modules = modules or lcb.lcb_modules()
    jobs: list[tuple[str, str, str, bool]] = []  # run, task_id, F1 code, official pass
    runs: dict[str, dict[str, Any]] = {}
    for run in RUNS:
        raw_name = RAW.get(run, "generations.jsonl")
        raw_sha = provenance.verify(out_root / run, [raw_name], "extraction.py")[raw_name]
        answers = read_raw(out_root / run / raw_name)
        graded, result_sha = read_result(results, run)
        fences: collections.Counter[int] = collections.Counter()
        empty, changed = 0, 0
        for tid, g in sorted(graded.items()):
            if g["status"] != "ok":
                continue
            text = lcb.after_think(answers[tid]["output"])
            official = modules.extraction.extract_code(text, modules.style)
            if official != g["output"]:
                sys.exit(f"extraction.py: {run} {tid}: LiveCodeBench's extraction of out/{run}/{raw_name} is not the "
                         f"code in results/{run}.jsonl.gz; the raw file is not the one this result was scored from")
            fences[len(fence_lines(text))] += 1
            empty += official == ""
            code = f1(text, official)
            if code != official:
                changed += 1
                jobs.append((run, tid, code, bool(g["pass"])))
        runs[run] = {"raw": {"file": f"out/{run}/{raw_name}", "sha256": raw_sha},
                     "result": {"file": f"results/{run}.jsonl.gz", "sha256": result_sha},
                     "answered": sum(fences.values()), "fence_lines": {str(k): fences[k] for k in sorted(fences)},
                     "empty_code": empty, "changed": changed, "regraded": {}}
    if jobs:
        rows = {r["question_id"]: r for r in lcb.load_rows(None)}
        samples = [lcb.problem(modules, rows[tid]).get_evaluation_sample() for _, tid, _, _ in jobs]
        _, graded_now, metadata = modules.evaluation.codegen_metrics(
            samples, [[code] for _, _, code, _ in jobs], num_process_evaluate=processes, timeout=lcb.EVAL_TIMEOUT)
        grades = [g[0] for g in modules.evaluation.extract_instance_results(graded_now)]
        for (run, tid, code, official_pass), passed, meta in zip(jobs, grades, metadata):
            runs[run]["regraded"][tid] = {"pass": bool(passed), "official_pass": official_pass, "code": code,
                                          "eval_metadata": json.loads(meta[0])}
    for r in runs.values():
        r["passing_after_f1"] = sum(g["pass"] for g in r["regraded"].values())
        r["official_passes_lost"] = sum(g["official_pass"] and not g["pass"] for g in r["regraded"].values())
    out = {"exploratory": "added after the results; not a protocol test, the official results stand",
           "rule": RULE, "evaluator": {"timeout_s": lcb.EVAL_TIMEOUT, "processes": processes},
           "provenance": provenance.step("extraction.py"), "runs": runs}
    (results / OUTPUT).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance.record(results, [OUTPUT], "extraction.py")
    for run, r in runs.items():
        print(f"{run}: answered {r['answered']}, empty code {r['empty_code']}, changed by F1 {r['changed']}, "
              f"passing after F1 {r['passing_after_f1']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out_dir", nargs="?", default=str(HERE / "out"))
    parser.add_argument("results_dir", nargs="?", default=str(HERE / "results"))
    parser.add_argument("--processes", type=int, default=8)
    args = parser.parse_args()
    main(Path(args.out_dir), Path(args.results_dir), args.processes)
