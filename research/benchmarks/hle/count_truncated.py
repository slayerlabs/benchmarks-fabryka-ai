"""Count HLE answers that hit the output-token limit, and optionally write a content-free verdicts file.

Input: the private per-question results file (gzipped JSONL, one record per question, git-ignored), with
fields `question_id`, `judge_correct` ("yes"/"no"), `judge_unresolved` (bool) and `usage.completion_tokens`.
Only IDs, verdicts and token counts are read; question text, answers and model responses are never printed.

Truncation rule: `completion_tokens >= limit`. `predict_api.py` did not store `finish_reason` for the
2026-11-23 run, so the token count is the only signal available; an answer that stops at exactly the
limit is counted as truncated.

Usage:
    python count_truncated.py results/bielik-11b-v3.1.jsonl.gz --limit 8192
    python count_truncated.py results/bielik-11b-v3.1.jsonl.gz --limit 8192 --verdicts results/bielik-11b-v3.1.verdicts.csv
"""
import argparse
import csv
import gzip
import json


def load(path):
    opener = gzip.open if path.endswith((".gz", ".gz.prywatne")) or _is_gzip(path) else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _is_gzip(path):
    with open(path, "rb") as f:
        return f.read(2) == b"\x1f\x8b"


def verdict(rec):
    if rec.get("judge_unresolved"):
        return "none"
    v = str(rec.get("judge_correct", "")).strip().lower()
    return v if v in ("yes", "no") else "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--limit", type=int, default=8192)
    ap.add_argument("--verdicts", help="write id,verdict,truncated CSV (no content)")
    args = ap.parse_args()

    recs = load(args.path)
    rows = []
    for r in recs:
        ct = (r.get("usage") or {}).get("completion_tokens")
        trunc = int(ct is not None and ct >= args.limit)
        rows.append((r["question_id"], verdict(r), trunc))
    rows.sort()
    n = len(rows)
    t = sum(x[2] for x in rows)
    correct = sum(1 for x in rows if x[1] == "yes")
    unjudged = sum(1 for x in rows if x[1] == "none")
    print(json.dumps({
        "n": n, "limit": args.limit, "rule": "completion_tokens >= limit",
        "truncated": t, "truncated_pct": round(100 * t / n, 2),
        "correct": correct, "unjudged": unjudged,
        "correct_among_truncated": sum(1 for x in rows if x[2] and x[1] == "yes"),
    }, indent=1))
    if args.verdicts:
        with open(args.verdicts, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["id", "verdict", "truncated"])
            w.writerows(rows)


if __name__ == "__main__":
    main()
