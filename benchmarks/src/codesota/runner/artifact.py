"""Writing a run directory in the `codesota.results` format, and validating it before it is reported."""

import datetime
import hashlib
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

from codesota.results import schema, sha256_file, validate_run

PACKAGE_DIR = Path(__file__).resolve().parent.parent
PACKAGES = ("lm_eval", "torch", "transformers", "datasets", "tokenizers", "huggingface_hub", "numpy", "accelerate")


def now() -> str:
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def runner_sha256() -> str:
    """Digest of the code that defines a result: the runner modules and the catalog, in name order."""
    files = [*sorted((PACKAGE_DIR / "runner").glob("*.py")), PACKAGE_DIR / "catalog.py"]
    return hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()


def source_state() -> tuple[str | dict[str, str], bool]:
    """(commit of the checkout, whether `benchmarks/` has uncommitted changes). Unknown when git is unavailable."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=PACKAGE_DIR, capture_output=True, text=True, check=True
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "--", str(PACKAGE_DIR.parent.parent)],
            cwd=PACKAGE_DIR,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as e:
        return {"unknown": f"git is unavailable: {e}"}, False
    return commit, bool(status)


def environment(device: str) -> dict[str, Any]:
    versions: dict[str, str | None] = {}
    for name in PACKAGES:
        try:
            versions[name] = metadata.version(name.replace("_", "-"))
        except metadata.PackageNotFoundError:
            versions[name] = None
    env: dict[str, Any] = {"python": sys.version.split()[0], "platform": platform.platform(), "packages": versions}
    import torch

    env["cuda"] = torch.version.cuda
    if device.startswith("cuda") and torch.cuda.is_available():
        env["gpu"] = torch.cuda.get_device_name(0)
    env["device"] = device
    return env


def write_json(path: Path, value: Any) -> None:
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"))


def write_run(
    run_dir: Path,
    manifest: dict[str, Any],
    records: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    extra: dict[str, tuple[str, bytes]],
) -> Path:
    """Write samples.jsonl, the extra artifacts ({path: (role, bytes)}), and manifest.json, with checksums.

    `observations` get `results_sha256` (the samples checksum) filled in when they are scored. Raises when the
    written run is not structurally valid: that is a bug in the runner, and the files stay for inspection.
    """
    run_dir.mkdir(parents=True, exist_ok=False)
    samples = run_dir / "samples.jsonl"
    samples.write_bytes(
        b"".join(json.dumps(r, sort_keys=True, ensure_ascii=False).encode("utf-8") + b"\n" for r in records)
    )
    artifacts = [
        {"path": "samples.jsonl", "role": "samples", "sha256": sha256_file(samples), "bytes": samples.stat().st_size}
    ]
    for rel, (role, data) in sorted(extra.items()):
        if role not in schema.ARTIFACT_ROLES:
            raise ValueError(f"artifact role {role!r}")
        path = run_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        artifacts.append({"path": rel, "role": role, "sha256": sha256_file(path), "bytes": len(data)})
    for obs in observations:
        if obs["state"] == "ok":
            obs["results_sha256"] = artifacts[0]["sha256"]
    write_json(run_dir / "manifest.json", {**manifest, "artifacts": artifacts, "observations": observations})
    report = validate_run(run_dir)
    if not report.ok:
        problems = "; ".join(f"{i.code} at {i.path}: {i.message}" for i in report.issues)
        raise RuntimeError(f"the runner wrote an invalid run in {run_dir}: {problems}")
    return run_dir
