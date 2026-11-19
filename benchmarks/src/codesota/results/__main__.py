"""Validate run directories: python -m codesota.results <run dir> [<run dir> ...] [--json]

Exits 0 when every run is valid, 1 when any is not, 2 on a usage error. Reads files only.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from codesota.results.validate import validate_runs


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
            print(
                json.dumps(
                    {
                        "run_dir": str(r.run_dir),
                        "run_id": r.run_id,
                        "valid": r.ok,
                        "manifest_sha256": r.manifest_sha256,
                        "sample_states": r.counts,
                        "issues": [vars(i) for i in r.issues],
                    }
                )
            )
            continue
        states = ", ".join(f"{k} {v}" for k, v in sorted(r.counts.items())) or "no samples read"
        print(f"{'VALID' if r.ok else 'INVALID'} {r.run_dir} (run {r.run_id}; samples: {states})")
        if r.manifest_sha256:
            print(f"  manifest sha256 {r.manifest_sha256}")
        for issue in r.issues:
            print(f"  {issue}")
    return 0 if all(r.ok for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
