"""python -m codesota.runner: run a selection of benchmarks on one model; every benchmark gets its own run directory.

    python -m codesota.runner --list
    python -m codesota.runner --benchmarks arc-easy,piqa --model EleutherAI/pythia-1b-v0 \
        --revision f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0 --out runs/
    python -m codesota.runner --benchmarks @verified --model ./models/my-model --out runs/

Exit code 0 when every selected benchmark was scored, 1 when any was not (failed, unsupported, blocked, or not
implemented), 2 on a usage error.
"""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from codesota import catalog


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m codesota.runner", description=__doc__.split("\n")[0])
    p.add_argument("--list", action="store_true", help="print the catalog and the packs, and exit")
    p.add_argument("--benchmarks", help="IDs, aliases, legacy task IDs, @pack, or all; comma-separated")
    p.add_argument("--model", help="a Hub repository or a local directory")
    p.add_argument("--revision", help="commit SHA of the Hub repository (required for the Hub)")
    p.add_argument("--out", type=Path, help="directory under which each run directory is created")
    p.add_argument("--dtype", default="float32", help="default: float32, as the research central run")
    p.add_argument("--device", default="cuda")
    p.add_argument("--batch-size", type=int, default=1, help="default: 1, as the research central run")
    p.add_argument("--max-length", type=int, help="the model's context window (default: from its configuration)")
    p.add_argument("--bos", choices=("one", "none"), default="one", help="one leading BOS per request (default)")
    p.add_argument(
        "--trust-remote-code", action="store_true", help="run code shipped with the model (recorded in the run)"
    )
    return p


def print_catalog() -> None:
    rows = sorted(catalog.CATALOG.values(), key=lambda b: (catalog.STATUSES.index(b.status), b.id))
    for b in rows:
        names = ", ".join((*b.aliases, *((b.legacy_id,) if b.legacy_id else ())))
        print(f"{b.status:<22} {b.id:<18} {b.name:<26} {b.language}  {names}")
    print()
    for name, ids in catalog.packs().items():
        print(f"@{name:<22} {len(ids):>3} benchmarks")


def write_index(out: Path, index: list[dict[str, Any]]) -> None:
    """index.json: one row per selected benchmark, rewritten after each one, so a stopped run keeps its rows."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.list:
        print_catalog()
        return 0
    if not (args.benchmarks and args.model and args.out):
        parser().error("--benchmarks, --model and --out are required (or --list)")
    try:
        selected = catalog.select(args.benchmarks)
    except catalog.SelectionError as e:
        parser().error(str(e))
    from codesota.runner import models

    try:
        spec = models.ModelSpec.from_args(
            args.model,
            args.revision,
            dtype=args.dtype,
            device=args.device,
            batch_size=args.batch_size,
            max_length=args.max_length,
            trust_remote_code=args.trust_remote_code,
            bos=args.bos,
        )
    except ValueError as e:
        parser().error(str(e))
    runnable = [b for b in selected if b.status != "not-implemented"]
    index: list[dict[str, Any]] = [
        {"benchmark": b.id, "status": b.status, "state": "not_run", "reason": "not implemented in CodeSOTA"}
        for b in selected
        if b.status == "not-implemented"
    ]
    if runnable:
        from codesota.runner import execute  # needs the `eval` extra

        lm = models.load(spec)
        digests = models.weights_digests(spec)
        record = {
            "bos": models.bos_probe(lm),
            "weights_files": digests,
            "weights_sha256": next(iter(digests.values()))
            if len(digests) == 1
            else {"unknown": f"{len(digests)} weight files; per-file SHA-256 in execution.environment.weights_files"},
            "max_length": getattr(lm, "max_length", None),
        }
        for b in runnable:
            o = execute.run_benchmark(b, lm, spec, record, args.out)
            index.append(
                {
                    "benchmark": b.id,
                    "status": b.status,
                    "state": o.state,
                    "value": o.value,
                    "reason": o.reason,
                    "run_dir": str(o.run_dir),
                }
            )
            print(f"{b.id:<18} {b.status:<22} {o.state:<14} {o.value if o.value is not None else '-'}", flush=True)
            write_index(args.out, index)
    for row in index:
        if row["state"] == "not_run":
            print(f"{row['benchmark']:<18} {row['status']:<22} not_run        {row['reason']}")
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return 0 if all(r["state"] == "ok" for r in index) else 1


if __name__ == "__main__":
    sys.exit(main())
