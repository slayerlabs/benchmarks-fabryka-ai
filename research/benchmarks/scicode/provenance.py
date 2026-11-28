"""What produced a file and on what: our code version, runner checksums, the machine, and sha256 of the files a step
writes, which the next step checks before it reads them.

Each step that writes a file a later step reads (scicode_runner.py generate -> generations.jsonl, scicode_runner.py
score -> graded.jsonl, summarize.py -> results/<model-id>.json and .jsonl.gz) records the file's sha256 in
`manifest.json` in the same directory. A step that reads such a file (scicode_runner.py score, summarize.py,
hypotheses.py) stops when the file is not in the manifest or its sha256 differs: the numbers would come from a file
nobody recorded writing.

The scoring step runs in a container without git; run.sh passes the commit and dirty flag it read on the host in
SCICODE_CODE_COMMIT and SCICODE_CODE_DIRTY, which `code_state` uses when git is not available (`code_commit_source`
says which).
"""

import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RUNNER_FILES = ("run.sh", "scicode_runner.py", "summarize.py", "hypotheses.py", "provenance.py", "Dockerfile.scoring",
                "requirements-scoring.lock", "requirements-generate.lock", "setup_scoring_vm.sh")
MANIFEST = "manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", "-C", str(HERE), *args], capture_output=True, text=True, check=True,
                              timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None


def code_state() -> dict[str, Any]:
    """Our repo's commit, whether a tracked file of this benchmark differs from it, and sha256 of the runner files
    as they are on disk (from the host's environment where git is not available, else null)."""
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=no", "--", ".")
    if head is None and os.environ.get("SCICODE_CODE_COMMIT"):
        commit, dirty, source = os.environ["SCICODE_CODE_COMMIT"], os.environ.get("SCICODE_CODE_DIRTY") == "1", "host"
    else:
        commit = head.strip() if head else None
        dirty, source = (None if status is None else bool(status.strip())), "git"
    return {"code_commit": commit, "code_commit_source": source, "dirty": dirty,
            "runner_sha256": {name: sha256_file(HERE / name) for name in RUNNER_FILES if (HERE / name).is_file()}}


def gpu_name() -> str | None:
    """`nvidia-smi --query-gpu=name`, one name per GPU joined by ", "; null without an NVIDIA GPU."""
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                             text=True, check=True, timeout=30).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    names = [line.strip() for line in out.splitlines() if line.strip()]
    return ", ".join(names) or None


def cpu_model() -> str:
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.is_file():
        for line in cpuinfo.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    if sys.platform == "darwin":
        try:
            return subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True,
                                  check=True, timeout=30).stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return platform.processor() or platform.machine()


def machine() -> dict[str, Any]:
    return {"gpu": gpu_name(), "platform": platform.platform(), "cpu": cpu_model(), "cpu_count": os.cpu_count(),
            "python": platform.python_version()}


def step(name: str) -> dict[str, Any]:
    """Code state and machine of one step, with its UTC start time."""
    return {"step": name, "at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
            **code_state(), **machine()}


def read_manifest(directory: Path) -> dict[str, Any]:
    path = Path(directory) / MANIFEST
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"files": {}}


def record(directory: Path, names: list[str], writer: str) -> None:
    """Writes the sha256 of `names` (files in `directory`) into its manifest, keeping the other entries."""
    directory = Path(directory)
    manifest = read_manifest(directory)
    at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    for name in names:
        manifest["files"][name] = {"sha256": sha256_file(directory / name), "written_by": writer, "at": at}
    (directory / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(directory: Path, names: list[str], reader: str) -> dict[str, str]:
    """Stops `reader` unless every file in `names` has the sha256 its manifest recorded; returns name -> sha256."""
    directory = Path(directory)
    files = read_manifest(directory)["files"]
    hashes = {}
    for name in names:
        entry = files.get(name)
        if entry is None:
            sys.exit(f"{reader}: {directory / name} has no sha256 in {directory / MANIFEST}; the step that writes it "
                     "records it there, so this file was not written by that step (or the manifest was lost)")
        actual = sha256_file(directory / name)
        if actual != entry["sha256"]:
            sys.exit(f"{reader}: {directory / name} has sha256 {actual}, but {directory / MANIFEST} recorded "
                     f"{entry['sha256']} ({entry.get('written_by')}, {entry.get('at')}); the file changed after it "
                     "was written, so nothing is computed from it")
        hashes[name] = actual
    return hashes
