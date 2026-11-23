"""Where the raw outputs (with thinking) are, checked against the results, and what they show: results/raw-outputs.json.

Usage: python3 raw_outputs.py <archive.tgz> [results-dir]

The raw generations are not committed (they hold the thinking). The LFM3-1.7B runs were copied off the GPU box in one
archive (`ARCHIVE_NAME`, with `out/<model-id>/generations.jsonl` under `ARCHIVE_PREFIX`); Bielik's stayed in this
benchmark's `out/bielik-11b-v3.1/` on the generating Mac. For each run this records the sha256 of its
generations.jsonl, whether it equals `raw_outputs.sha256` in results/<model-id>.json, and the archive's own sha256.

Per run and prompt setting, from the last answer of each step (descriptive, added after the results; PROTOCOL.md
Amendment 2):
- `reasoning`: answers; answers that close a reasoning block with `</think>`; the median share of an answer's
  characters before its last `</think>` (over those answers); steps passed (official extraction) and how many of them
  close a `</think>`. With `enable_thinking: false` LFM3-1.7B's template ends the prompt with an empty
  `<think></think>`, and Bielik's API template with `<think></think>` too, so a `</think>` in their output is
  reasoning (or a stray tag) the model wrote itself.
- `extraction`: steps whose official extracted code is empty, by cause read from the text the extraction saw (after
  the last `</think>`): `lone_fence` (exactly one fence line and no ```python, so the official rule takes what follows
  it), `unfinished` (thinking on, no `</think>` or a length stop), `other`; and, over all answers, how many are such a
  lone fence (the case where E1 differs from the official extraction) and how many have no fence line at all.
"""

import gzip
import hashlib
import json
import re
import statistics
import sys
import tarfile
from pathlib import Path
from typing import Any

import provenance

HERE = Path(__file__).resolve().parent
ARCHIVE_NAME = "labaj-agency/out/coding-group/box/export.tgz"  # on the measuring Mac, copied from the H100 box
ARCHIVE_PREFIX = "scicode/research/api-benchmarks/scicode/out"
ARCHIVED = ("lfm3-1.7b", "lfm3-1.7b-nothink")
LOCAL = ("bielik-11b-v3.1",)
SETTINGS = ("with_background", "without_background")
THINK_END = "</think>"
FENCE_LINE = re.compile(r"^[ \t]*```", re.MULTILINE)  # as scicode_runner.FENCE_LINE (Amendment 1)


def last_records(data: bytes) -> dict[tuple[str, str, int], dict[str, Any]]:
    """The last record per (setting, problem, step), as the scorer saw it (a retried step replaces its error)."""
    out = {}
    for line in data.decode("utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[(r["setting"], r["problem_id"], int(r["step"]))] = r
    return out


def seen_text(record: dict[str, Any]) -> str:
    """The text the extraction read: after the last `</think>` (the whole output without one)."""
    return record["output"].rsplit(THINK_END, 1)[-1]


def empty_cause(record: dict[str, Any]) -> str:
    if record.get("unfinished"):
        return "unfinished"
    text = seen_text(record)
    if len(FENCE_LINE.findall(text)) == 1 and "```python" not in text:
        return "lone_fence"
    return "other"


def per_setting(last: dict[tuple, dict[str, Any]], graded: dict[tuple, dict[str, Any]], setting: str) -> dict[str, Any]:
    keys = sorted(k for k in graded if k[0] == setting)
    answered = [last[k] for k in keys if last[k]["status"] == "ok"]
    closed = [r for r in answered if THINK_END in r["output"]]
    shares = [len(r["output"].rsplit(THINK_END, 1)[0]) / len(r["output"]) for r in closed]
    passed = [k for k in keys if graded[k]["pass"]]
    empty = [k for k in keys if not (graded[k]["output"] or "").strip()]
    causes: dict[str, list[str]] = {}
    for k in empty:
        causes.setdefault(empty_cause(last[k]), []).append(f"{k[1]}.{k[2]}")
    texts = [seen_text(r) for r in answered]
    fences = [(len(FENCE_LINE.findall(t)), "```python" in t) for t in texts]
    return {
        "reasoning": {"answers": len(answered), "closing_think": len(closed),
                      "median_share_before_last_think_end": round(statistics.median(shares), 4) if shares else None,
                      "passed": len(passed), "passed_closing_think": sum(1 for k in passed if THINK_END in last[k]["output"])},
        "extraction": {"empty_official": len(empty), "empty_by_cause": causes,
                       "answers_lone_fence": sum(1 for n, py in fences if n == 1 and not py),
                       "answers_without_fence_line": sum(1 for n, _ in fences if n == 0)},
    }


def entry(results: Path, run: str, data: bytes, where: str) -> dict[str, Any]:
    provenance.verify(results, [f"{run}.json", f"{run}.jsonl.gz"], "raw_outputs.py")
    recorded = json.loads((results / f"{run}.json").read_text(encoding="utf-8"))["raw_outputs"]["sha256"]
    sha = hashlib.sha256(data).hexdigest()
    with gzip.open(results / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        graded = {(r["setting"], r["problem_id"], int(r["step"])): r for r in map(json.loads, f)}
    last = last_records(data)
    missing = sorted(set(graded) - set(last))
    if missing:
        sys.exit(f"raw_outputs.py: {run}: {len(missing)} scored steps have no raw answer (first: {missing[0]})")
    return {"file": where, "sha256": sha, "matches_result": sha == recorded,
            "settings": {s: per_setting(last, graded, s) for s in SETTINGS}}


def main(archive: Path, results: Path) -> None:
    runs = {}
    with tarfile.open(archive) as t:
        for run in ARCHIVED:
            name = f"{ARCHIVE_PREFIX}/{run}/generations.jsonl"
            runs[run] = entry(results, run, t.extractfile(name).read(), f"{ARCHIVE_NAME} : {name}")
    for run in LOCAL:
        runs[run] = entry(results, run, (HERE / "out" / run / "generations.jsonl").read_bytes(),
                          f"out/{run}/generations.jsonl on the generating Mac")
    bad = [run for run, e in runs.items() if not e["matches_result"]]
    if bad:
        sys.exit(f"raw_outputs.py: generations.jsonl of {bad} differ from the sha256 in their result files")
    record = {"archive": {"file": ARCHIVE_NAME, "committed": False, "sha256": provenance.sha256_file(archive)},
              "runs": runs}
    (results / "raw-outputs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    provenance.record(results, ["raw-outputs.json"], "raw_outputs.py")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else HERE / "results")
