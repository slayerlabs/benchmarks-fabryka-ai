"""Where the raw outputs (with thinking) are, checked against the results: results/raw-outputs.json.

Usage: python3 raw_outputs.py <archive.tgz> [results-dir]

The raw generations are not committed (too large, and they hold the thinking). The LFM3-1.7B runs were copied off
the GPU box in one archive (`ARCHIVE_NAME`, with `out/<model-id>/generations.jsonl` under `ARCHIVE_PREFIX`); Bielik's
stayed in this benchmark's `out/bielik-11b-v3.1/` on the generating Mac. For each run this records the sha256 of its
generations.jsonl and whether it equals `raw_outputs.sha256` in results/<model-id>.json (the sha256 lcbpro.py
generate recorded), and the archive's own sha256. It also gives the cause of every `no_code` answer (nothing
extracted), read from the raw text after the last `</think>`: `python_fence` (a ```python block instead of C++),
`tool_call` (a `<tool_call>` instead of an answer), `length_stop` (cut by the output limit), `other`; and, per
run, how many answers close a reasoning block with `</think>`, the median share of an answer's characters before
its last `</think>`, and how many accepted answers close one (PROTOCOL.md Amendment 1: with `enable_thinking:
false` the template opens and closes an empty `<think></think>`, so a `</think>` in the output is reasoning the
model wrote anyway).
"""

import gzip
import hashlib
import json
import statistics
import sys
import tarfile
from pathlib import Path
from typing import Any

import provenance

HERE = Path(__file__).resolve().parent
ARCHIVE_NAME = "labaj-agency/out/coding-group/box/export.tgz"  # on the measuring Mac, copied from the H100 box
ARCHIVE_PREFIX = "lcbpro/research/api-benchmarks/livecodebench-pro-25q2/out"
ARCHIVED = ("lfm3-1.7b", "lfm3-1.7b-nothink")
LOCAL = ("bielik-11b-v3.1",)


def no_code_cause(record: dict[str, Any]) -> str:
    text = record["output"].rsplit("</think>", 1)[-1]
    if record["finish_reason"] == "length":
        return "length_stop"
    if "<tool_call>" in text:
        return "tool_call"
    if "```python" in text:
        return "python_fence"
    return "other"


def last_records(data: bytes) -> dict[str, dict[str, Any]]:
    out = {}
    for line in data.decode("utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out[r["problem_id"]] = r
    return out


def reasoning(last: dict[str, dict[str, Any]], accepted: dict[str, bool]) -> dict[str, Any]:
    answered = [r for r in last.values() if r["status"] == "ok"]
    closed = [r for r in answered if "</think>" in r["output"]]
    shares = [len(r["output"].rsplit("</think>", 1)[0]) / len(r["output"]) for r in closed]
    return {"answers": len(answered), "closing_think": len(closed),
            "median_share_before_last_think_end": round(statistics.median(shares), 4) if shares else None,
            "accepted": sum(accepted.values()),
            "accepted_closing_think": sum(1 for r in closed if accepted.get(r["problem_id"]))}


def entry(results: Path, run: str, data: bytes, where: str) -> dict[str, Any]:
    provenance.verify(results, [f"{run}.json", f"{run}.jsonl.gz"], "raw_outputs.py")
    recorded = json.loads((results / f"{run}.json").read_text(encoding="utf-8"))["raw_outputs"]["sha256"]
    sha = hashlib.sha256(data).hexdigest()
    with gzip.open(results / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    no_code = sorted(r["task_id"] for r in rows if r["category"] == "no_code")
    last = last_records(data)
    causes: dict[str, list[str]] = {}
    for pid in no_code:
        causes.setdefault(no_code_cause(last[pid]), []).append(pid)
    return {"file": where, "sha256": sha, "matches_result": sha == recorded, "no_code": causes,
            "reasoning": reasoning(last, {r["task_id"]: bool(r["accepted"]) for r in rows})}


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
