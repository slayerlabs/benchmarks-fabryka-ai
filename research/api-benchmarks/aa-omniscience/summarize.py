"""AA-Omniscience grades -> results/<model-id>.json and results/<model-id>.jsonl.gz (format from research/METHODOLOGY.md).

Usage: python summarize.py <prepare dir> <grades.json> <answers.json> <results/model-id> <settings json> <judge label>

Metrics as in the AA-Omniscience paper, N = 600: Omniscience Index OI = 100 (correct - incorrect) / N (the score);
accuracy = correct / N; hallucination rate = incorrect / (partial + incorrect + not attempted). The OI stderr is
s / sqrt(N) of the per-question values +1 / 0 / -1. The question set is closed: the .jsonl.gz holds only the
question id, domain and grade, no question text and no model output.
"""

import datetime
import gzip
import json
import math
import sys
from pathlib import Path

VALUE = {"A": 1, "B": -1, "C": 0, "D": 0}
CLASS = {"A": "correct", "B": "incorrect", "C": "partial", "D": "not_attempted"}


def main(prep, grades_path, answers_path, target, settings, judge, limit=False):
    questions = [
        json.loads(l) for l in Path(prep, "questions.jsonl").read_text(encoding="utf-8").split("\n") if l.strip()
    ]
    grades = json.loads(Path(grades_path).read_text(encoding="utf-8"))["grades"]
    if limit:  # run.sh --limit N: only the questions that were asked
        questions = [q for q in questions if q["id"] in grades]
    meta = json.loads(Path(answers_path).read_text(encoding="utf-8"))["meta"]
    missing = [q["id"] for q in questions if grades.get(q["id"]) is None]
    if (not limit and len(questions) != 600) or missing or not questions:
        sys.exit(f"summarize.py: {len(questions)} questions, {len(missing)} without a grade; the score needs all 600")
    letters = [grades[q["id"]] for q in questions]
    n = len(letters)
    c, i, p, a = (sum(1 for x in letters if x == k) for k in "ABCD")
    values = [VALUE[x] for x in letters]
    mean = sum(values) / n
    se = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1) / n)
    acc = c / n
    result = {
        "benchmark": "AA-Omniscience (public)",
        "model": Path(target).name,
        "metric": "omniscience_index",
        "score": round(100 * mean, 2),
        "stderr": round(100 * se, 2),
        "n": n,
        "date": datetime.date.today().isoformat(),
        "harness": "AA-Omniscience README prompts (answer and grader templates) with generate.py and judge.py",
        "data": "https://huggingface.co/datasets/ArtificialAnalysis/AA-Omniscience-Public @ e4883edbb9f5ccf2b2a8fdc6fb65e01a58e99849",
        "settings": {**json.loads(settings), "judge": {"model": judge}},
        "other_metrics": {
            "accuracy": round(100 * acc, 2),
            "accuracy_stderr": round(100 * math.sqrt(acc * (1 - acc) / n), 2),
            "hallucination_rate": round(100 * i / (p + i + a), 2) if p + i + a else None,
            "non_hallucination_rate": round(100 * (1 - i / (p + i + a)), 2) if p + i + a else None,
            "correct": c,
            "incorrect": i,
            "partial": p,
            "not_attempted": a,
            "answers_cut_at_length": meta.get("cut_at_length"),
        },
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
        for q, x in zip(questions, letters):
            f.write(
                json.dumps(
                    {"task_id": q["id"], "domain": q["domain"], "grade": CLASS[x], "score": VALUE[x], "output": None}
                )
                + "\n"
            )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:7], limit="--limit" in sys.argv[7:])
