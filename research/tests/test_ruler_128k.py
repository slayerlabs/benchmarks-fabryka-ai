"""RULER 128K (api-benchmarks/ruler-128k): golden checks of summarize.py on fixed fake predictions.

No network, RULER checkout, torch or lm-eval: the RULER metric is replaced by a stand-in with the same call shape
(`metric([pred], [refs])` -> percent), so these tests pin the aggregation, not RULER's scorer. Checked: the text
after the last `</think>` is what gets scored; an error is left out of the score, never counted as 0; the
13-task mean, the category means and the nulls for lengths that did not run or have a task without any score.
Run: python3 tests/test_ruler_128k.py (or pytest).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-benchmarks" / "ruler-128k"))
import summarize as S  # noqa: E402
from ruler import answer_text  # noqa: E402


def match_all(preds, refs):
    """Stand-in for RULER's string_match_all on one sample: share of references found, in percent."""
    return round(100 * sum(r.lower() in preds[0].lower() for r in refs[0]) / len(refs[0]), 2)


def keep(text, task_config):
    return text.strip()


def test_answer_is_text_after_last_think():
    assert answer_text("<think>a</think>b</think> 42") == " 42"
    assert answer_text("no reasoning 42") == "no reasoning 42"
    assert answer_text("<think>the answer is 42</think>") == ""


def test_needle_only_in_thinking_scores_zero_and_error_is_not_scored():
    samples = [{"index": i, "outputs": ["1234567"], "length": 4090} for i in range(3)]
    records = {
        0: {"index": 0, "output": "<think>maybe 1234567</think>I do not know.", "finish_reason": "stop",
            "output_tokens": 9},
        1: {"index": 1, "output": "<think>x</think>It is 1234567.", "finish_reason": "length", "output_tokens": 7},
        2: {"index": 2, "error": "HTTP 500: overloaded"},
    }
    rows = S.sample_rows("niah_single_1", 4096, samples, records, keep, match_all)
    assert [r["score"] for r in rows] == [0.0, 100.0, None]
    assert rows[2]["error"] == "HTTP 500: overloaded"
    assert [r.get("finished") for r in rows] == [True, False, None]
    preds = S.pred_records(samples, records)
    assert [p["index"] for p in preds] == [0, 1] and preds[1]["pred"] == "It is 1234567."
    # A sample that never got a record is an error too, not a zero.
    assert S.sample_rows("vt", 4096, samples[:1], {}, keep, match_all)[0] == {
        "task": "vt", "length": 4096, "index": 0, "score": None, "error": "not run"}


def rows_for(length, scores_by_task, errors_by_task=None):
    errors_by_task = errors_by_task or {}
    rows = []
    for task in dict.fromkeys([*scores_by_task, *errors_by_task]):
        rows += [{"task": task, "length": length, "index": i, "score": s, "finished": True}
                 for i, s in enumerate(scores_by_task.get(task, []))]
        rows += [{"task": task, "length": length, "index": 100 + j, "score": None, "error": "timeout"}
                 for j in range(errors_by_task.get(task, 0))]
    return rows


def test_aggregate_means_categories_and_nulls():
    tasks = S.TASKS
    # 4096: every task 100 except vt (50) and qa_2 (0); niah_single_1 has an error on top of its two 100s.
    at_4096 = {t: [100.0, 100.0] for t in tasks}
    at_4096["vt"] = [100.0, 0.0]
    at_4096["qa_2"] = [0.0, 0.0]
    rows = rows_for(4096, at_4096, {"niah_single_1": 1})
    # 8192: cwe has only errors, so the 13-task mean is not defined.
    at_8192 = {t: [100.0] for t in tasks if t != "cwe"}
    rows += rows_for(8192, at_8192, {"cwe": 2})
    skipped = {16384: "the 4096-token context window does not hold a 16384-token RULER sample"}
    m = S.aggregate(rows, skipped, [4096, 8192, 16384], tasks, resamples=200)

    l4 = m["per_length"]["4096"]
    assert l4["score"] == round((11 * 100 + 50 + 0) / 13, 2) == 88.46
    assert l4["n"] == 26  # the error is not a sample
    assert 0 < l4["stderr"] < 10
    assert m["errors"]["4096"] == {"niah_single_1": 1}
    assert m["per_task"]["4096"]["niah_single_1"] == 100.0  # not 66.67: the error is not a zero
    assert m["per_task"]["4096"]["vt"] == 50.0
    assert m["per_category"]["4096"] == {"retrieval": 100.0, "tracing": 50.0, "aggregation": 100.0, "qa": 50.0}

    assert m["per_length"]["8192"] == {"score": None, "reason": "no scored sample in cwe"}
    assert m["per_task"]["8192"]["cwe"] is None and m["errors"]["8192"] == {"cwe": 2}
    assert "8192" not in m["per_category"]
    assert m["per_length"]["16384"] == {"score": None, "reason": skipped[16384]}


def test_bootstrap_se_is_zero_for_constant_scores_and_reproducible():
    assert S.bootstrap_se([[100.0] * 5, [0.0] * 5], resamples=50) == 0
    data = [[100.0, 0.0, 100.0, 0.0], [50.0, 100.0]]
    assert S.bootstrap_se(data, resamples=300) == S.bootstrap_se(data, resamples=300)


def test_result_headline_is_131072_or_null_with_reason():
    run = {"model": "slayer1b-1.08", "date": "2026-11-22", "ruler_commit": "db43f92", "seed": 20261122,
           "num_samples": 50, "data_sources": {"squad.json": "abc"}, "settings": {}}
    metrics = {"per_length": {"4096": {"score": 10.0, "stderr": 1.0, "n": 650},
                              "131072": {"score": None, "reason": "too long"}}}
    result = S.result_json(run, metrics)
    assert result["score"] is None and result["stderr"] is None and result["reason"] == "too long"
    metrics["per_length"]["131072"] = {"score": 65.0, "stderr": 1.2, "n": 650}
    result = S.result_json(run, metrics)
    assert (result["score"], result["stderr"], result["n"]) == (65.0, 1.2, 650) and "reason" not in result
    for field in ("benchmark", "model", "metric", "score", "stderr", "n", "date", "harness", "data", "settings",
                  "deviations", "other_metrics"):
        assert field in result


def test_jsonl_rows_keep_errors_and_cap_answers():
    rows = [{"task": "qa_1", "length": 4096, "index": 0, "score": 100.0, "answer": "x" * (S.ANSWER_CHARS + 5),
             "output_tokens": 3, "finished": True},
            {"task": "qa_1", "length": 4096, "index": 1, "score": None, "error": "timeout"}]
    first, second = S.jsonl_rows(rows)
    assert len(first["answer"]) == S.ANSWER_CHARS and first["answer_truncated"] is True
    assert second == {"task": "qa_1", "length": 4096, "index": 1, "score": None, "error": "timeout"}


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} passed")
