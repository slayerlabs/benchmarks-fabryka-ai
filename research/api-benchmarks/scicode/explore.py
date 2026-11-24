"""Exploratory analyses added after the results were seen (PROTOCOL.md Amendment 2): results/exploratory.json.

Usage: python3 explore.py [results-dir]

- `k3_without_reasoning_passes`: K3's D (with background) recomputed with every step that `lfm3-1.7b-nothink`
  passed from an answer that still closes a reasoning block with `</think>` counted as failed (the steps listed in
  results/raw-outputs.json, raw_outputs.py): how much of the lead that survives the switch sits in answers that
  reason anyway. Same formula and SE clustered by problem as hypotheses.py. No verdict reads it.
Every file read must have the sha256 its writer recorded in results/manifest.json.
"""

import json
import sys
from pathlib import Path
from typing import Any

import hypotheses
import provenance

HERE = Path(__file__).resolve().parent


def k3_without_reasoning_passes(results: Path) -> dict[str, Any]:
    runs = {m: hypotheses.load(results, m) for m in (hypotheses.LFM, hypotheses.NOTHINK, hypotheses.BIELIK)}
    ids, clusters = hypotheses.items(runs, hypotheses.PRIMARY)
    provenance.verify(results, ["raw-outputs.json"], "explore.py")
    raw = json.loads((results / "raw-outputs.json").read_text(encoding="utf-8"))
    reasoning = raw["runs"][hypotheses.NOTHINK]["settings"][hypotheses.PRIMARY]["reasoning"]
    removed = {f"{hypotheses.PRIMARY}/{s}" for s in reasoning["passed_closing_think_steps"]}
    if not removed <= {t for t in ids if runs[hypotheses.NOTHINK][t]["score"]}:
        sys.exit("explore.py: raw-outputs.json lists steps that lfm3-1.7b-nothink did not pass")
    on, b = hypotheses.y(runs[hypotheses.LFM], ids), hypotheses.y(runs[hypotheses.BIELIK], ids)
    off = [0.0 if t in removed else v for t, v in zip(ids, hypotheses.y(runs[hypotheses.NOTHINK], ids))]
    s = hypotheses.mean_z([o - a / 2 - c / 2 for o, a, c in zip(off, on, b)], clusters)
    return {"note": "exploratory: nothink's passes from answers closing `</think>` counted as failed",
            "passes_removed": len(removed), "value": 100 * s["value"], "se": 100 * s["se"], "z": s["z"],
            "n": s["n"], "clusters": s["clusters"]}


def main(results: Path) -> None:
    record = {"k3_without_reasoning_passes": k3_without_reasoning_passes(results)}
    (results / "exploratory.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    provenance.record(results, ["exploratory.json"], "explore.py")
    print(json.dumps(record, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results")
