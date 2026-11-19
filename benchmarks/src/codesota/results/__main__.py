"""Validate run directories: python -m codesota.results <run dir> [<run dir> ...] [--json]

Exits 0 when every run is structurally valid, 1 when any is not, 2 on a usage error. Reads files only.
A valid run is not a scientifically verified result: see benchmarks/docs/result-artifacts.md.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from codesota.results.validate import Report, validate_runs

SCIENTIFIC = "not checked by this tool (needs review of the benchmark integration)"


def as_json(r: Report) -> str:
    return json.dumps(
        {
            "run_dir": str(r.run_dir),
            "run_id": r.run_id,
            "structurally_valid": r.ok,
            "provenance_complete": r.provenance_complete,
            "scientific_verification": SCIENTIFIC,
            "manifest_sha256": r.manifest_sha256,
            "samples_sha256": r.samples_sha256,
            "sample_states": r.counts,
            "not_recomputed": r.not_recomputed,
            "issues": [vars(i) for i in r.issues],
            "warnings": [vars(i) for i in r.warnings],
        }
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m codesota.results",
        description="Validate CodeSOTA run directories (manifest.json plus the artifacts it lists).",
    )
    parser.add_argument("runs", nargs="+", type=Path, help="run directories")
    parser.add_argument("--json", action="store_true", help="print one JSON report per run")
    args = parser.parse_args(argv)
    reports = validate_runs(args.runs)
    for r in reports:
        if args.json:
            print(as_json(r))
            continue
        states = ", ".join(f"{k} {v}" for k, v in sorted(r.counts.items())) or "no samples read"
        print(f"{'VALID' if r.ok else 'INVALID'} {r.run_dir} (run {r.run_id}; samples: {states})")
        print(f"  structure: {'valid' if r.ok else 'invalid'}")
        print(f"  provenance: {'complete' if r.provenance_complete else 'partial (some fields unknown or missing)'}")
        print(f"  scientific verification: {SCIENTIFIC}")
        if r.not_recomputed:
            print(f"  not recomputed (aggregation external): {', '.join(r.not_recomputed)}")
        if r.manifest_sha256:
            print(f"  manifest sha256 {r.manifest_sha256}")
        for issue in r.issues:
            print(f"  {issue}")
        for warning in r.warnings:
            print(f"  warning: {warning}")
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
