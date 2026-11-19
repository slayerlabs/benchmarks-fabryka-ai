"""IFStruct results file -> results/<model-id>.json and results/<model-id>.jsonl.gz (format from research/METHODOLOGY.md).

Usage: python summarize.py <ifstruct-eval --results-file> <input data jsonl> <results/model-id> <settings json> [--limit]

A sample passes only if the harness's validator finds no error (`passed`). A sample whose request failed after the
harness's retries carries `details.api_error`; the script stops if it finds any, because such a sample has no model
answer (rerun it first).
"""

import datetime
import gzip
import json
import math
import sys
from pathlib import Path

IFSTRUCT_COMMIT = "73e03a6d3a8508357ba430675a106d4887abedf3"
DATA_REVISION = "2e342ca5f2673fb1287411fdbadcdfde82b35682"
EXPECTED_N = 2000


def main(results_file, data, target, settings, limit):
    d = json.loads(Path(results_file).read_text(encoding="utf-8"))
    samples = {str(s["seed"]): s for s in d["samples"]}
    seeds = [str(json.loads(line)["seed"]) for line in Path(data).read_text(encoding="utf-8").splitlines() if line.strip()]
    if limit:
        seeds = seeds[:len(samples)]
    n = len(seeds)
    if set(seeds) != set(samples) or (not limit and n != EXPECTED_N):
        sys.exit(f"summarize.py: {len(samples)} results for {n} input samples (expected {EXPECTED_N})")
    api_errors = [s for s in seeds if samples[s]["details"].get("api_error")]
    if api_errors:
        sys.exit(f"summarize.py: {len(api_errors)} samples without a model answer (api_error), rerun them first")
    passed = [bool(samples[s]["passed"]) for s in seeds]
    p = sum(passed) / n
    if not limit and abs(p - d["summary"]["pass_rate"]) > 1e-12:
        sys.exit(f"summarize.py: pass rate {p} != harness summary {d['summary']['pass_rate']}")
    by_format = {}
    for s in seeds:
        f = samples[s]["output_format"]
        by_format.setdefault(f, []).append(bool(samples[s]["passed"]))
    result = {
        "benchmark": "IFStruct",
        "model": Path(target).name,
        "metric": "pass_rate",
        "score": round(100 * p, 2),
        "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2),
        "n": n,
        "date": datetime.date.today().isoformat(),
        "harness": f"https://github.com/Liquid4All/ifstruct @ {IFSTRUCT_COMMIT} (ifstruct-eval)",
        "data": f"https://huggingface.co/datasets/LiquidAI/ifstruct-v1.0 @ {DATA_REVISION}",
        "settings": json.loads(settings),
        "other_metrics": {f"pass_rate_{f}": round(100 * sum(v) / len(v), 2) for f, v in sorted(by_format.items())},
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
        for s in seeds:
            x = samples[s]
            f.write(json.dumps({"task_id": s, "score": int(bool(x["passed"])), "output_format": x["output_format"],
                                "entity_type": x["entity_type"], "errors": x["errors"], "prompt": x["prompt"],
                                "output": x["response"]}, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], "--limit" in sys.argv[5:])
