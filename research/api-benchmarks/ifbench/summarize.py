"""IFBench output -> results/<model-id>.json and results/<model-id>.jsonl.gz (format from research/METHODOLOGY.md).

Usage: python summarize.py <input data jsonl> <eval dir> <eval prefix> <results/model-id> <settings json>

<eval dir>/<prefix>-eval_results_{strict,loose}.jsonl are written by IFBench's run_eval in input order. Only files
with the prefix are read: the IFBench repo also ships sample files named eval_results_*.jsonl in eval/.
"""

import datetime
import gzip
import json
import math
import sys
from pathlib import Path

IFBENCH_COMMIT = "488918665d53f867fa908a293769ec6e71e74aec"
DATA_REVISION = "ed7c12452594b7028b15807b86d3938150b663ae"


def jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def main(data, eval_dir, prefix, target, settings):
    docs = jsonl(data)
    strict = jsonl(Path(eval_dir) / f"{prefix}-eval_results_strict.jsonl")
    loose = jsonl(Path(eval_dir) / f"{prefix}-eval_results_loose.jsonl")
    n = len(docs)
    if not (n == len(strict) == len(loose)):
        sys.exit(f"summarize.py: {n} prompts, {len(strict)} strict and {len(loose)} loose results")
    for d, s, lo in zip(docs, strict, loose):
        if not (d["prompt"] == s["prompt"] == lo["prompt"]):
            sys.exit(f"summarize.py: results are not in input order at key {d['key']}")
    passed = [bool(s["follow_all_instructions"]) for s in strict]
    p = sum(passed) / n

    def rate(rows, inst=False):
        if inst:
            flags = [f for r in rows for f in r["follow_instruction_list"]]
            return round(100 * sum(flags) / len(flags), 2)
        return round(100 * sum(bool(r["follow_all_instructions"]) for r in rows) / len(rows), 2)

    result = {
        "benchmark": "IFBench",
        "model": Path(target).name,
        "metric": "prompt_level_strict_acc",
        "score": round(100 * p, 2),
        "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2),
        "n": n,
        "date": datetime.date.today().isoformat(),
        "harness": f"https://github.com/allenai/IFBench @ {IFBENCH_COMMIT} (generate_responses.py, run_eval)",
        "data": f"https://huggingface.co/datasets/allenai/IFBench_test @ {DATA_REVISION}",
        "settings": json.loads(settings),
        "other_metrics": {"inst_level_strict_acc": rate(strict, True), "prompt_level_loose_acc": rate(loose),
                          "inst_level_loose_acc": rate(loose, True)},
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
        for d, s, lo in zip(docs, strict, loose):
            f.write(json.dumps({
                "task_id": str(d["key"]),
                "score": int(bool(s["follow_all_instructions"])),
                "instruction_id_list": s["instruction_id_list"],
                "strict": s["follow_instruction_list"],
                "loose": lo["follow_instruction_list"],
                "prompt": d["prompt"],
                "output": s["response"],
            }, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:6])
