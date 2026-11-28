"""Convert HLE prediction/judge outputs to research/benchmarks format.

Outputs:
  <target>.json      summary (benchmarks/docs/methodology.md)
  <target>.jsonl.gz  per-question records WITHOUT question text or correct answer
                     (HLE contamination/canary policy; see README).

Smoke tests (--limit > 0) write to out/ and do not replace published results.
"""

import argparse
import datetime
import gzip
import json
import math
from pathlib import Path


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--judged", required=True)
    parser.add_argument("--target", required=True, help="results/<model-id> path without extension")
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--harness", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--max_completion_tokens", type=int, default=None)
    parser.add_argument("--judge", default="o3-mini-2025-01-31")
    args = parser.parse_args()

    predictions = load_json(args.predictions)
    judged = load_json(args.judged)

    # Only include questions that have judge responses.
    rows = []
    for qid, pred in judged.items():
        jr = pred.get("judge_response")
        if not jr:
            continue
        rows.append((qid, pred, jr))

    n = len(rows)
    if n == 0:
        raise SystemExit("no judged responses found")

    correct = sum(1 for _, _, jr in rows if "yes" in jr.get("correct", ""))
    p = correct / n
    score = round(100 * p, 2)
    stderr = round(100 * math.sqrt(p * (1 - p) / n), 2)

    target = Path(args.target)
    if args.limit and args.limit > 0:
        target = Path(args.predictions).parent / f"{args.model}-limit{args.limit}"
        print(f"summarize.py: --limit {args.limit}, writing to {target}.* (not results/)")

    result = {
        "benchmark": "Humanity's Last Exam (no tools)",
        "model": args.model,
        "metric": "accuracy",
        "score": score,
        "stderr": stderr,
        "n": n,
        "date": datetime.date.today().isoformat(),
        "harness": args.harness,
        "data": args.data,
        "settings": {
            "temperature": args.temperature,
            "top_p": args.top_p,
            "max_completion_tokens": args.max_completion_tokens,
            "max_turns": 1,
            "trials": 1,
            "judge_model": args.judge,
            "judge_max_completion_tokens": 4096,
        },
        "deviations": "see README.md, Deviations",
    }

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(f"{target}.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    # Contamination policy: do NOT write question text, correct answer, rationale, or images.
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8") as f:
        for qid, pred, jr in rows:
            rec = {
                "question_id": qid,
                "model": args.model,
                "response": pred.get("response"),
                "extracted_final_answer": jr.get("model_answer"),
                "judge_correct": jr.get("correct"),
                "judge_confidence": jr.get("confidence"),
                "judge_reasoning": jr.get("reasoning"),
            }
            usage = pred.get("usage")
            if usage is not None:
                rec["usage"] = usage
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
