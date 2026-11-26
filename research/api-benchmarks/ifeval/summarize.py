"""lm-eval output -> results/<model-id>.json and results/<model-id>.jsonl.gz
(format from research/api-benchmarks/README.md).

Usage: python summarize.py <lm-eval output dir> <results/model-id>
A run with --limit is written to <lm-eval output dir>/<model-id>-limit<N>.* instead, so a smoke test never
replaces a published result.
"""

import datetime
import gzip
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "task"))
from utils import strip_thinking  # noqa: E402

TASK = "ifeval_pinned"
MAIN_METRIC = "prompt_level_strict_acc"  # see README, "Deviations"
OTHER_METRICS = ["inst_level_strict_acc", "prompt_level_loose_acc", "inst_level_loose_acc"]


def latest(directory, pattern):
    files = sorted(Path(directory).rglob(pattern), key=lambda p: p.stat().st_mtime)
    if not files:
        sys.exit(f"summarize.py: no {pattern} in {directory}")
    return files[-1]


def main(out_dir, target):
    summary = json.loads(latest(out_dir, "results_*.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in latest(out_dir, f"samples_{TASK}_*.jsonl").read_text(encoding="utf-8").splitlines()]
    model = Path(target).name
    limit = summary.get("config", {}).get("limit")
    if limit:
        target = Path(out_dir) / f"{model}-limit{int(limit)}"
        print(f"summarize.py: --limit {limit}, writing to {target}.* (not results/)")
    passed = [bool(r[MAIN_METRIC]) for r in rows]
    n = len(passed)
    p = sum(passed) / n
    config = summary["configs"][TASK]
    gen = config.get("generation_kwargs", {})  # the task config after --gen_kwargs overrides
    result = {
        "benchmark": "IFEval",
        "model": model,
        "metric": MAIN_METRIC,
        "score": round(100 * p, 2),
        "stderr": round(100 * math.sqrt(p * (1 - p) / n), 2),
        "n": n,
        "date": datetime.date.fromtimestamp(summary["date"]).isoformat(),  # day the run started (local time)
        "harness": f"https://github.com/EleutherAI/lm-evaluation-harness v{summary.get('lm_eval_version', '?')}",  # git_hash is this repo's commit, not lm-eval's
        "data": f"https://huggingface.co/datasets/google/IFEval @ {config.get('dataset_kwargs', {}).get('revision', 'unrecorded')}",
        "settings": {
            "temperature": gen.get("temperature"),
            "top_p": gen.get("top_p"),
            "max_tokens_per_turn": gen.get("max_gen_toks"),
            "max_turns": 1,
            "trials": 1,
        },
        "other_metrics": {m: round(100 * summary["results"][TASK][f"{m},none"], 2) for m in OTHER_METRICS},
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({
                "task_id": r["doc"]["key"],
                "score": int(bool(r[MAIN_METRIC])),
                **{m: r[m] for m in ["prompt_level_strict_acc", "inst_level_strict_acc",
                                     "prompt_level_loose_acc", "inst_level_loose_acc"]},
                "prompt": r["doc"]["prompt"],
                "output": r["resps"][0][0],  # raw, with any thinking
                "scored_output": strip_thinking(r["resps"][0][0]),  # what the IFEval rules checked
            }, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:3])
