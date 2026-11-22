"""EXPLORATORY re-judging (added after the results were seen, PROTOCOL.md Amendment 1): results/rejudge.json.

Usage, on the scoring machine after `run.sh <model-id> --score` for the three runs (the pinned test zips in
.cache/hf and the judge image are already there):
    HF_HOME=.cache/hf HF_HUB_OFFLINE=1 .venv/bin/python rejudge.py [out-root] [results-dir]

Two variants, each judged with the harness's own judge and `WORKERS` workers; a problem whose code does not change
keeps its official verdict, so only the changed problems are submitted:
- `whole_answer`: the harness's `extract_longest_cpp_code` on the whole answer, as `benchmark.py` does, instead of
  on the text after the last `</think>` (README, Deviations). Answers the official run did not judge for reasons
  other than the extraction (no test zip, unfinished, request errors) keep their official outcome.
- `bits_prefix`: every Bielik answer that did not compile, with `#include <bits/stdc++.h>` and
  `using namespace std;` put before its code: do missing headers explain Bielik's compile errors?
Inputs: out/<model-id>/{generations.jsonl,graded.jsonl} (sha256 checked against their manifests).
"""

import datetime
import json
import sys
from pathlib import Path
from typing import Any

import lcbpro
import provenance

HERE = Path(__file__).resolve().parent
RUNS = ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1")
WORKERS = 4  # the scoring VM was shared with another job when this ran; official judging used JUDGE_WORKERS = 8
PREFIX = "#include <bits/stdc++.h>\nusing namespace std;\n"
KEEP = ("no_tests", "unfinished", "request_error", "unsupported")  # outcomes not decided by the extraction


def answers_and_grades(out: Path, run: str) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    d = out / run
    provenance.verify(d, ["generations.jsonl", "graded.jsonl"], "rejudge.py")
    answers = {r["problem_id"]: r for r in lcbpro.read_jsonl(d / "generations.jsonl")}  # the last record wins
    grades = {r["problem_id"]: r for r in lcbpro.read_jsonl(d / "graded.jsonl")}
    return answers, grades


def whole_answer_todo(answers: dict[str, dict[str, Any]], grades: dict[str, dict[str, Any]],
                      extract: Any) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """Problems whose whole-answer code differs from the official code: to judge (code) or now without code."""
    todo, no_code = {}, {}
    for pid, g in grades.items():
        if g["category"] in KEEP:
            continue
        code = extract(answers[pid]["output"])
        if code == g["code"]:
            continue
        if code is None:
            no_code[pid] = {"category": "no_code", "accepted": False}
        else:
            todo[pid] = code
    return todo, no_code


def summary(grades: dict[str, dict[str, Any]], changed: dict[str, dict[str, Any]]) -> dict[str, Any]:
    official = sum(1 for g in grades.values() if g["accepted"])
    variant = sum(1 for pid, g in grades.items() if (changed[pid]["accepted"] if pid in changed else g["accepted"]))
    return {"accepted_official": official, "accepted_variant": variant, "changed_code": len(changed),
            "lost": sorted(pid for pid in changed if grades[pid]["accepted"] and not changed[pid]["accepted"]),
            "gained": sorted(pid for pid in changed if changed[pid]["accepted"] and not grades[pid]["accepted"]),
            "results": {pid: {"official": grades[pid]["category"], "variant": r["category"]}
                        for pid, r in sorted(changed.items())}}


def main(out: Path, results: Path) -> None:
    from huggingface_hub import constants
    if not constants.HF_HUB_OFFLINE:
        sys.exit("rejudge.py: set HF_HUB_OFFLINE=1 (the judge must read the pinned test zips; lcbpro.py score)")
    extract = lcbpro.harness_extract()
    from judge import LightCPVerifierJudge, ProblemNotFoundError, SupportedLanguage
    import requests

    data = {run: answers_and_grades(out, run) for run in RUNS}
    started = datetime.datetime.now(datetime.timezone.utc)
    lcbpro.fresh_problems_dir(Path(LightCPVerifierJudge.PROBLEMS_DIR))
    variants: dict[str, Any] = {"whole_answer": {}, "bits_prefix": {}}
    with LightCPVerifierJudge(worker=WORKERS) as judge:
        environment = lcbpro.judge_environment(judge)
        environment["workers"] = WORKERS

        def fetch(sid: int) -> dict[str, Any] | None:
            response = requests.get(f"{judge.base_url}/result/{sid}", timeout=60)
            return response.json() if response.status_code == 200 else None

        def run_judge(todo: dict[str, str]) -> dict[str, dict[str, Any]]:
            return lcbpro.judge_all(judge, SupportedLanguage.CPP, ProblemNotFoundError, todo, fetch) if todo else {}

        for run, (answers, grades) in data.items():
            todo, no_code = whole_answer_todo(answers, grades, extract)
            variants["whole_answer"][run] = summary(grades, {**run_judge(todo), **no_code})
        answers, grades = data["bielik-11b-v3.1"]
        failed = {pid: PREFIX + g["code"] for pid, g in grades.items() if g["category"] == "compile_error"}
        judged = run_judge(failed)
        counts: dict[str, int] = {}
        for r in judged.values():
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        variants["bits_prefix"]["bielik-11b-v3.1"] = {
            "problems": len(failed), "categories": dict(sorted(counts.items())),
            "results": {pid: r["category"] for pid, r in sorted(judged.items())}}
    record = {"exploratory": True, "amendment": "PROTOCOL.md, Amendment 1", "variants": variants,
              "judge": environment, "machine": provenance.step("rejudge.py"),
              "seconds": round((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds(), 1),
              "note": f"judged with {WORKERS} workers while another job shared the machine; official verdicts used "
                      f"{lcbpro.JUDGE_WORKERS} workers on an otherwise idle machine, so a borderline time limit can "
                      "differ"}
    results.mkdir(parents=True, exist_ok=True)
    (results / "rejudge.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    provenance.record(results, ["rejudge.json"], "rejudge.py")
    print(json.dumps({k: {r: {x: y for x, y in v.items() if x != "results"} for r, v in d.items()}
                      for k, d in variants.items()}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out",
         Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "results")
