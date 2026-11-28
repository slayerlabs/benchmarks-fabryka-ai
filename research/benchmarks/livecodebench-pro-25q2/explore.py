"""EXPLORATORY analyses added after the results were seen (not in PROTOCOL.md): results/exploratory.json.

Usage: python3 explore.py [results-dir]   (default: results/ next to this file)

From results/<model-id>.jsonl.gz of the three runs (sha256 checked against results/manifest.json):
- `budgets`: problems accepted within an output budget B, for B in BUDGETS: a problem counts only if it was
  accepted and its answer used at most B output tokens (thinking included). Descriptive: no hypothesis reads it.
- `compile_errors`: the compile errors of each run by cause, from the judge's message (`judge_error`, the first
  2000 characters of the compiler output):
  `compiler_says_missing_include` - g++ itself names a header (its note "did you forget to '#include ...'");
  `undeclared_std_name` - otherwise, the first error is "'X' was not declared in this scope" or "'X' is not a
  member of 'std'" with X in STD_NAMES, a standard-library name whose header the code did not include;
  `other` - any other first error (syntax, types, names the code never defined). Problem ids per cause.
"""

import gzip
import json
import re
import sys
from pathlib import Path
from typing import Any

import provenance

HERE = Path(__file__).resolve().parent
RUNS = ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1")
BUDGETS = (4096, 8192, 16384, 32768)
CAUSES = ("compiler_says_missing_include", "undeclared_std_name", "other")
# Standard-library names whose header is not pulled in by <iostream>/<vector> alone in g++ 11 (the judge image's
# compiler); listed by hand for this classification.
STD_NAMES = frozenset("""
gcd lcm reverse sort stable_sort min_element max_element accumulate iota partial_sum memset memcpy strlen
LLONG_MAX LLONG_MIN INT_MAX INT_MIN ULLONG_MAX LONG_MAX set multiset map multimap unordered_map unordered_set queue
priority_queue stack deque list string pair swap abs sqrt pow log2 fill lower_bound upper_bound unique
next_permutation tuple bitset numeric_limits greater less function setprecision count find
""".split())
UNDECLARED = re.compile(r"error: '([A-Za-z_][A-Za-z_0-9]*)' (?:was not declared in this scope|is not a member of 'std')")
FIRST_ERROR = re.compile(r"error: (.*)")


def rows(results: Path, run: str) -> list[dict[str, Any]]:
    provenance.verify(results, [f"{run}.jsonl.gz"], "explore.py")
    with gzip.open(results / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def cause(message: str) -> str:
    if "did you forget to '#include" in message:
        return "compiler_says_missing_include"
    first = FIRST_ERROR.search(message)
    if first:
        undeclared = UNDECLARED.match("error: " + first.group(1))
        if undeclared and undeclared.group(1) in STD_NAMES:
            return "undeclared_std_name"
    return "other"


def budgets(rs: list[dict[str, Any]]) -> dict[str, int]:
    return {str(b): sum(1 for r in rs if r["accepted"] and r["output_tokens"] is not None and r["output_tokens"] <= b)
            for b in BUDGETS}


def compile_errors(rs: list[dict[str, Any]]) -> dict[str, Any]:
    by_cause: dict[str, list[str]] = {c: [] for c in CAUSES}
    for r in rs:
        if r["category"] == "compile_error":
            by_cause[cause(r["judge_error"] or "")].append(r["task_id"])
    return {"total": sum(len(v) for v in by_cause.values()),
            "by_cause": {c: {"count": len(v), "problems": sorted(v)} for c, v in by_cause.items()}}


def analyse(results: Path) -> dict[str, Any]:
    data = {run: rows(results, run) for run in RUNS}
    return {"exploratory": True,
            "note": "added after the results were seen; descriptive, not part of PROTOCOL.md's verdicts",
            "budgets": {"tokens": list(BUDGETS), "accepted": {run: budgets(rs) for run, rs in data.items()},
                        "n": {run: len(rs) for run, rs in data.items()}},
            "compile_errors": {run: compile_errors(rs) for run, rs in data.items()}}


def main(results: Path) -> None:
    a = analyse(results)
    (results / "exploratory.json").write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")
    provenance.record(results, ["exploratory.json"], "explore.py")
    print(json.dumps({k: a[k] for k in ("budgets",)}, indent=1))
    print({run: {c: v["count"] for c, v in e["by_cause"].items()} for run, e in a["compile_errors"].items()})


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results")
