"""Decide whether a pull request needs the `codesota` package test job (.github/workflows/codesota.yml).

Input on stdin: one changed file per line as `<filename>\t<previous_filename or empty>`, from
`gh api --paginate repos/{repo}/pulls/{n}/files --jq '.[] | [.filename, (.previous_filename // "")] | @tsv'`.
Environment: CHANGED_FILES, the PR's `changed_files` count from the event payload.
Output: `v2=true` or `v2=false`, to append to $GITHUB_OUTPUT.

The decision fails closed: when the listing cannot be trusted to be complete (the API lists at most MAX_LISTED files,
or the listing is shorter than the PR's file count), the tests run.
"""

import os
import sys

MAX_LISTED = 3000
"""GitHub's "list pull request files" endpoint returns at most 3000 files."""

# benchmarks/, plus the research code the runner's tests compare against (tests/test_runner.py), the benchmark
# directories its catalog must list (tests/test_catalog.py), and the result files the results page is generated from
# (tests/test_leaderboard.py): a change there can break the package's tests.
TRIGGER_PREFIXES = (
    "benchmarks/",
    "research/common/",
    "research/benchmarks/",
    "research/tools/statystyka.py",
    "research/results/full-run-2026-11/",
    "research/api-benchmarks/ifeval/results/",
)
TRIGGER_FILES = frozenset({".github/workflows/codesota.yml", ".github/scripts/codesota_changes.py"})


def touches_v2(path: str) -> bool:
    return path.startswith(TRIGGER_PREFIXES) or path in TRIGGER_FILES


def needs_tests(lines: list[str], changed_files: int) -> bool:
    if changed_files >= MAX_LISTED or len(lines) < changed_files:
        return True  # incomplete listing: cannot prove benchmarks/ is untouched
    for line in lines:
        filename, _, previous = line.partition("\t")
        if touches_v2(filename) or (previous and touches_v2(previous)):
            return True
    return False


def verdict(changes: str, v2: str, test: str) -> bool:
    """The `CodeSOTA CI` aggregator: job results are GitHub's `needs.<job>.result` values (success, failure,
    cancelled, skipped; a timeout is a failure). Pass only when detection succeeded with a definite decision and the
    test job did what that decision requires."""
    if changes != "success" or v2 not in ("true", "false"):
        return False
    return test == ("success" if v2 == "true" else "skipped")


def main() -> int:
    if sys.argv[1:] == ["--verdict"]:
        env = os.environ
        ok = verdict(env.get("CHANGES", ""), env.get("V2", ""), env.get("TEST", ""))
        print(f"changes={env.get('CHANGES')!r} v2={env.get('V2')!r} test={env.get('TEST')!r}: {'pass' if ok else 'fail'}")
        return 0 if ok else 1
    raw = os.environ.get("CHANGED_FILES", "")
    if not raw.isdigit():
        print(f"CHANGED_FILES must be a non-negative integer, got {raw!r}", file=sys.stderr)
        return 2
    lines = [line for line in sys.stdin.read().splitlines() if line]
    print(f"v2={'true' if needs_tests(lines, int(raw)) else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
