"""BFCL output -> results/<model-id>.json and results/<model-id>.jsonl.gz (format from research/METHODOLOGY.md).

Usage:
  python summarize.py <bfcl root> <results/model-id> [--bfcl-model bielik-FC] [--limit]
  python summarize.py --cannot-run "<reason>" <results/model-id>

<bfcl root> is the berkeley-function-call-leaderboard directory after `bfcl generate` and `bfcl evaluate`
(it holds result/ and score/). Pass/fail per task comes from the score files: their first line is the category
summary and the other lines list only the failed tasks. A task whose result starts with "Error during inference"
never reached a model answer. If the error is the server's context-length rejection (the conversation grew past
max_model_len), the task stays a failure in the full N, as the harness scores it, and is counted in
context_window_exceeded. Any other such error stops the script, because the harness would score a transport or server
failure as a model failure (rerun those IDs with `bfcl generate --run-ids --allow-overwrite`). Memory prerequisite
conversations (IDs with "prereq") are generated but not scored by the harness, so they are left out here too.
"""

import csv
import datetime
import gzip
import json
import math
import sys
from pathlib import Path

GORILLA_COMMIT = "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
# Scored tasks per category at GORILLA_COMMIT (rows of bfcl_eval/data/BFCL_v4_*.json; memory: the same 155 questions
# for each of the three backends). web_search (2 x 100) is not run, see README.
EXPECTED_N = {
    "simple_python": 400, "simple_java": 100, "simple_javascript": 50,
    "multiple": 200, "parallel": 200, "parallel_multiple": 200, "irrelevance": 240,
    "live_simple": 258, "live_multiple": 1053, "live_parallel": 16, "live_parallel_multiple": 24,
    "live_irrelevance": 884, "live_relevance": 16,
    "multi_turn_base": 200, "multi_turn_miss_func": 200, "multi_turn_miss_param": 200, "multi_turn_long_context": 200,
    "memory_kv": 155, "memory_vector": 155, "memory_rec_sum": 155,
}
LIVE_AST = ["live_simple", "live_multiple", "live_parallel", "live_parallel_multiple"]

# Each summary is a linear combination of category pass rates, with the weights of
# bfcl_eval/eval_checker/eval_runner_helper.py at GORILLA_COMMIT (unweighted means, except "live", which pools the
# four live AST categories by the number of scored tasks; main() fills those weights in, so that a --limit run is
# weighted like the harness). Standard error: sqrt(sum w^2 p (1 - p) / n) over the categories.
SUMMARIES = {
    "non_live_acc": {"simple_python": 1 / 12, "simple_java": 1 / 12, "simple_javascript": 1 / 12,
                     "multiple": 1 / 4, "parallel": 1 / 4, "parallel_multiple": 1 / 4},
    "live_acc": None,
    "irrelevance_acc": {"irrelevance": 1 / 2, "live_irrelevance": 1 / 2},
    "relevance_acc": {"live_relevance": 1.0},
    "multi_turn_acc": {c: 1 / 4 for c in ("multi_turn_base", "multi_turn_miss_func", "multi_turn_miss_param",
                                         "multi_turn_long_context")},
    "memory_acc": {c: 1 / 3 for c in ("memory_kv", "memory_vector", "memory_rec_sum")},
}
# Overall Acc = 10% non-live + 10% live + 10% irrelevance + 30% multi-turn + 40% agentic, agentic = mean(web search,
# memory); a missing category counts as 0. Without web search this is only a lower bound, never the score.
LOWER_BOUND = {"non_live_acc": 0.10, "live_acc": 0.10, "irrelevance_acc": 0.10, "multi_turn_acc": 0.30,
               "memory_acc": 0.20}
# Columns of score/data_overall.csv that the summaries must reproduce.
CSV_CHECK = {"non_live_acc": "Non-Live AST Acc", "live_acc": "Live Acc", "irrelevance_acc": "Irrelevance Detection",
             "relevance_acc": "Relevance Detection", "multi_turn_acc": "Multi Turn Acc", "memory_acc": "Memory Acc",
             "overall_acc_lower_bound": "Overall Acc"}


def jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def one_file(root, name):
    found = sorted(root.rglob(name))
    if len(found) != 1:
        sys.exit(f"summarize.py: expected one {name} under {root}, found {len(found)}")
    return found[0]


def combine(weights, cats):
    p = sum(w * cats[c]["p"] for c, w in weights.items())
    se = math.sqrt(sum(w * w * cats[c]["p"] * (1 - cats[c]["p"]) / cats[c]["n"] for c, w in weights.items()))
    return p, se


def pct(x):
    return round(100 * x, 2)


def write(target, result, rows):
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    if rows is not None:
        with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2))


def base_result(model):
    return {
        "benchmark": "BFCL V4",
        "model": model,
        "metric": "overall_acc",
        "date": datetime.date.today().isoformat(),
        "harness": f"https://github.com/ShishirPatil/gorilla @ {GORILLA_COMMIT} (berkeley-function-call-leaderboard)",
        "data": f"bundled with the harness: berkeley-function-call-leaderboard/bfcl_eval/data @ {GORILLA_COMMIT}",
    }


def cannot_run(reason, target):
    result = base_result(Path(target).name)
    result.update({"score": None, "stderr": None, "n": 0, "settings": {}, "score_null_reason": reason,
                   "deviations": "see README.md, Deviations"})
    write(target, result, None)


def main(root, target, bfcl_model, limit):
    root = Path(root)
    cats, rows, errors, prereq, window = {}, [], {}, 0, {}
    for cat, expected in EXPECTED_N.items():
        results = jsonl(one_file(root / "result" / bfcl_model, f"BFCL_v4_{cat}_result.json"))
        prereq += sum(1 for r in results if "prereq" in r["id"])
        results = [r for r in results if "prereq" not in r["id"]]
        score = jsonl(one_file(root / "score" / bfcl_model, f"BFCL_v4_{cat}_score.json"))
        head, failed = score[0], {e["id"]: e for e in score[1:]}
        no_answer = [r for r in results
                     if isinstance(r["result"], str) and r["result"].startswith("Error during inference")]
        over = [r["id"] for r in no_answer if "maximum context length" in r["result"]]
        bad = [r["id"] for r in no_answer if "maximum context length" not in r["result"]]
        if bad:
            errors[cat] = bad
        if over:
            window[cat] = len(over)
        n = len(results)
        if head["total_count"] != n or (not limit and n != expected):
            sys.exit(f"summarize.py: {cat}: {n} results, score total {head['total_count']}, expected {expected}")
        passed = n - len(failed)
        if (passed != head["correct_count"] or not set(failed) <= {r["id"] for r in results}
                or not set(over) <= set(failed)):
            sys.exit(f"summarize.py: {cat}: failed list does not match the score summary")
        cats[cat] = {"p": passed / n, "n": n, "passed": passed}
        for r in results:
            f = failed.get(r["id"])
            rows.append({"task_id": r["id"], "category": cat, "score": 0 if f else 1,
                         "error_type": f.get("error_type") if f else None, "output": r["result"]})
    if errors:
        sys.exit("summarize.py: tasks without a model answer (Error during inference), rerun them first: "
                 + json.dumps({c: len(v) for c, v in errors.items()}))

    live_n = sum(cats[c]["n"] for c in LIVE_AST)
    weights_of = {**SUMMARIES, "live_acc": {c: cats[c]["n"] / live_n for c in LIVE_AST}}
    raw = {name: combine(weights, cats) for name, weights in weights_of.items()}
    # the summaries share no category, so their errors add in quadrature
    raw["overall_acc_lower_bound"] = (sum(w * raw[k][0] for k, w in LOWER_BOUND.items()),
                                      math.sqrt(sum((w * raw[k][1]) ** 2 for k, w in LOWER_BOUND.items())))
    other = {k: pct(p) for k, (p, _) in raw.items()}
    other_se = {k: pct(se) for k, (_, se) in raw.items()}

    csv_path = root / "score" / "data_overall.csv"
    if csv_path.exists():  # the harness's own summary table must agree with ours
        table = {row["Model"]: row for row in csv.DictReader(csv_path.open(encoding="utf-8"))}
        row = table.get("Bielik-11B-v3.1-Instruct (FC)")
        if row is None:
            sys.exit("summarize.py: model row missing in score/data_overall.csv")
        for key, col in CSV_CHECK.items():
            theirs = float(str(row[col]).rstrip("%"))
            if abs(theirs - other[key]) > 0.011:
                sys.exit(f"summarize.py: {key} = {other[key]} but data_overall.csv {col} = {row[col]}")

    result = base_result(Path(target).name)
    result.update({
        "score": None,
        "stderr": None,
        "n": sum(c["n"] for c in cats.values()),
        "settings": {
            "mode": "FC (native function calling through the vLLM tool parser)",
            "temperature": 0.001,
            "effective_temperature": 0.01,  # vLLM raises temperatures below 0.01 to 0.01
            "max_tokens_per_turn": None,
            "max_model_len": 32768,
            "test_categories": list(EXPECTED_N),
            "trials": 1,
        },
        "score_null_reason": "Overall Acc needs the web_search categories (200 tasks, 40% x 1/2 of the weight), "
                             "which were not run: they need a search API key. See other_metrics.",
        "other_metrics": other,
        "other_metrics_stderr": other_se,
        "categories": {c: {"score": pct(v["p"]), "passed": v["passed"], "n": v["n"]} for c, v in cats.items()},
        "memory_prereq_generated_not_scored": prereq,
        "context_window_exceeded": window,
        "deviations": "see README.md, Deviations",
    })
    write(target, result, rows)


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--cannot-run":
        cannot_run(args[1], args[2])
    else:
        bfcl_model = args[args.index("--bfcl-model") + 1] if "--bfcl-model" in args else "bielik-FC"
        main(args[0], args[1], bfcl_model, "--limit" in args)
