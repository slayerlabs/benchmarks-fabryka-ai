"""AutomationBench export -> results/<model-id>.json and results/<model-id>.jsonl.gz (format from research/METHODOLOGY.md).

Usage: python summarize.py <export json> <results/model-id> <settings json> [--limit]

The export is written by `auto-bench --export-json`. The official metric is the pass rate: a task passes only if
every non-excluded assertion passes (`passed`); the mean fraction of assertions met (`score`, partial credit) is in
other_metrics. Assertions marked `excluded` are the ones an idle agent would satisfy; the harness does not score them.
"""

import datetime
import gzip
import json
import math
import sys
from pathlib import Path

AB_COMMIT = "4a8e1061254004d9dac807054eed33fad7d1ff14"
PUBLIC_DOMAINS = ["sales", "marketing", "operations", "support", "finance", "hr"]
EXPECTED_N = 600


def main(export, target, settings, limit):
    d = json.loads(Path(export).read_text(encoding="utf-8"))
    meta, tasks = d["meta"], d["tasks"]
    n = len(tasks)
    if sorted(meta["domains"]) != sorted(PUBLIC_DOMAINS) or (not limit and n != EXPECTED_N):
        sys.exit(f"summarize.py: domains {meta['domains']}, {n} tasks; expected the public set of {EXPECTED_N}")
    if len({t["id"] for t in tasks}) != n:
        sys.exit("summarize.py: duplicate task ids in the export")
    passed = [bool(t["passed"]) for t in tasks]
    p = sum(passed) / n
    scored = [a for t in tasks for a in t["assertion_results"] if not a.get("excluded")]
    result = {
        "benchmark": "AutomationBench (public)",
        "model": Path(target).name,
        "metric": "pass_rate",
        "score": round(100 * p, 2),
        "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2),
        "n": n,
        "date": datetime.date.today().isoformat(),
        "harness": f"https://github.com/zapier/AutomationBench @ {AB_COMMIT} (auto-bench {meta.get('benchmark_version')})",
        "data": f"bundled with the harness, public domains {', '.join(PUBLIC_DOMAINS)} @ {AB_COMMIT}",
        "settings": {
            **json.loads(settings),
            "toolset": meta.get("toolset"),
            "max_steps": meta.get("max_steps"),
            "trials": 1,
        },
        "other_metrics": {
            "partial_credit": round(100 * sum(float(t["score"]) for t in tasks) / n, 2),
            "assertions_passed": sum(1 for a in scored if a["passed"]),
            "assertions_scored": len(scored),
            "tasks_without_tool_calls": sum(1 for t in tasks if not t["num_tool_calls"]),
            "tool_calls": d["summary"]["total_tool_calls"],
        },
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
        for t in tasks:
            f.write(
                json.dumps(
                    {
                        "task_id": str(t["id"]),
                        "name": t["name"],
                        "score": int(bool(t["passed"])),
                        "partial_credit": float(t["score"]),
                        "assertions": [
                            {"type": a["type"], "passed": a["passed"], "excluded": a.get("excluded", False)}
                            for a in t["assertion_results"]
                        ],
                        "steps": t["steps"],
                        "num_tool_calls": t["num_tool_calls"],
                        "output": [m for m in t["messages"] if m.get("role") != "system"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], "--limit" in sys.argv[4:])
