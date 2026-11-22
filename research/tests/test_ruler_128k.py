"""RULER 128K (api-benchmarks/ruler-128k): golden checks of summarize.py and compare.py on fixed fake data.

No network, RULER checkout, torch or lm-eval: the RULER metric is replaced by a stand-in with the same call shape
(`metric([pred], [refs])` -> percent), so these tests pin the aggregation, not RULER's scorer. Checked: the text
after the last `</think>` is what gets scored; an error is left out of the score, never counted as 0; the
13-task mean, the category means and the nulls for lengths that did not run or have a task without any score.
compare.py (hypotheses R1-R3 and the control) on fake per-sample results: a clear and a noise case, Holm with m = 3,
errors left out, null lengths listed, `not run` for a missing model and a control FAIL above the table.
Run: python3 tests/test_ruler_128k.py (or pytest).
"""
import contextlib
import gzip
import io
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api-benchmarks" / "ruler-128k"))
import compare as C  # noqa: E402
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
    run = {"model": "slayer1b-1.09-k70000", "date": "2026-11-22", "ruler_commit": "db43f92", "seed": 20261122,
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


def by_category(retrieval, tracing, aggregation, qa):
    """task -> percent, one value per R3 category."""
    pct = {"retrieval": retrieval, "tracing": tracing, "aggregation": aggregation, "qa": qa}
    return {t: pct[c] for c, ts in S.CATEGORIES.items() for t in ts}


def write_model(results_dir, model, means, skipped=None, errors=None):
    """Fake results/<model>.json and .jsonl.gz: means is length -> percent or length -> task -> percent; each task
    gets 50 samples of 100 or 0 with that mean; errors is (length, task) -> error rows on top."""
    rows = []
    for length, pct in means.items():
        pct = pct if isinstance(pct, dict) else dict.fromkeys(S.TASKS, pct)
        for t in S.TASKS:
            k = round(pct[t] / 2)
            rows += [{"task": t, "length": length, "index": i, "score": 100.0 if i < k else 0.0, "finished": True}
                     for i in range(50)]
    for (length, task), n in (errors or {}).items():
        rows += [{"task": task, "length": length, "index": 100 + j, "score": None, "error": "timeout"}
                 for j in range(n)]
    metrics = S.aggregate(rows, skipped or {}, S.LENGTHS, resamples=2)
    (results_dir / f"{model}.json").write_text(json.dumps({"model": model, "other_metrics": metrics}))
    with gzip.open(results_dir / f"{model}.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({k: v for k, v in r.items() if k != "finished"}) + "\n")


WINDOW = "the context window does not hold this length"
FIT = "templated prompts do not fit"
# At 131072 the mean is 882 / 13 = 67.85, within 2 SE of the card's 65.56: the control passes.
LFM3_STEEP = {4096: by_category(98, 100, 90, 70), 8192: by_category(98, 90, 85, 68),
              16384: by_category(96, 80, 75, 66), 32768: by_category(94, 60, 65, 60),
              65536: by_category(92, 45, 50, 55), 131072: by_category(84, 30, 40, 50)}


def clear_case(results_dir, lfm3_errors=None):
    write_model(results_dir, C.LFM3, LFM3_STEEP, errors=lfm3_errors)
    # Bielik through the API: 32768 does not fit with its system prompt, 65536 and 131072 exceed the window.
    write_model(results_dir, C.BIELIK, {4096: 70, 8192: 80, 16384: 90},
                skipped={32768: FIT, 65536: WINDOW, 131072: WINDOW})
    write_model(results_dir, C.SLAYER, {4096: 20}, skipped=dict.fromkeys(S.LENGTHS[1:], WINDOW))


def run_compare(results_dir):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        result = C.main(results_dir, resamples=200)
    return result, out.getvalue()


def test_compare_clear_case():
    with tempfile.TemporaryDirectory() as d:
        clear_case(Path(d))
        result, text = run_compare(Path(d))
        assert json.loads((Path(d) / "hypotheses.json").read_text()) == json.loads(json.dumps(result))
    assert result["control"]["status"] == "PASS" and result["control"]["mean"] == 882 / 13
    assert result["control"]["card"] == 65.56
    h = result["hypotheses"]
    assert h["R1"]["value"] == 882 / 13 and h["R1"]["n"] == 650
    assert h["R1"]["effective_length"] == 16384  # 92.6, 90.8, 86.9, then 81.7 at 32768
    for name in ("R1", "R2", "R3"):
        assert (h[name]["verdict"], h[name]["outcome"]) == ("clear", "confirmed"), (name, h[name])
    # R2 over the lengths both models hold: Bielik's 32768 is null, so 4096-16384.
    assert h["R2"]["lengths"] == [4096, 8192, 16384] and h["R2"]["lengths_excluded"] == [32768, 65536, 131072]
    assert len(h["R2"]["comparisons"]) == 1 and h["R2"]["value"] < 0
    assert abs(h["R2"]["slopes"][C.BIELIK]["slope"] - 10) < 1e-9  # 70, 80, 90 per doubling
    drops = h["R3"]["drops"]
    assert {c: d["drop"] for c, d in drops.items()} == {"retrieval": 14, "tracing": 70, "aggregation": 50, "qa": 20}
    assert drops["retrieval"]["se_clustered"] == 0  # every niah task drops by 14
    assert [drops[c]["verdict_clustered"] for c in ("tracing", "aggregation", "qa")] == ["undetermined"] * 3
    assert [c["verdict_clustered"] for c in h["R3"]["comparisons"]] == ["undetermined", "undetermined"]
    assert result["models"][C.BIELIK]["excluded_lengths"] == {"32768": FIT, "65536": WINDOW, "131072": WINDOW}
    assert result["models"][C.BIELIK]["per_length"]["131072"] is None
    assert result["models"][C.SLAYER]["per_length"]["4096"] == 20
    assert f"excluded: {C.BIELIK} @ 32768: {FIT}" in text
    assert sum(line.startswith("deviation: ") for line in text.splitlines()) == len(C.DEVIATIONS) == 2


def test_compare_noise_case_holm_and_control_fail():
    with tempfile.TemporaryDirectory() as d:
        write_model(Path(d), C.LFM3, {**dict.fromkeys(S.LENGTHS[:-1], 86), 131072: 84})
        write_model(Path(d), C.BIELIK, dict.fromkeys(S.LENGTHS[:4], 86), skipped={65536: WINDOW, 131072: WINDOW})
        result, text = run_compare(Path(d))
    assert result["control"]["status"] == "FAIL"
    assert text.index("hypotheses not read until explained") < text.index("| hypothesis |")
    h = result["hypotheses"]
    assert (h["R1"]["verdict"], h["R1"]["outcome"]) == ("noise", "open") and h["R1"]["value"] == 84
    # LFM3 and Bielik are both flat over 4096-32768: equal slopes, z = 0, under 2 SE, so R2 is refuted.
    assert (h["R2"]["verdict"], h["R2"]["outcome"]) == ("noise", "refuted") and abs(h["R2"]["z"]) < 1e-9
    assert h["R2"]["lengths"] == [4096, 8192, 16384, 32768]
    assert h["R3"]["outcome"] == "refuted" and h["R3"]["value"] == 0  # every category drops by 2
    # Holm, m = 3: in raw-p order the adjusted p are 3p, then max(previous, 2p), then max(previous, p), capped at 1.
    rows = sorted(h.values(), key=lambda x: x["p"])
    expected, previous = [], 0.0
    for rank, row in enumerate(rows):
        previous = max(previous, min(1.0, (3 - rank) * row["p"]))
        expected.append(previous)
    assert [row["p_holm"] for row in rows] == expected
    assert rows[0]["p_holm"] == min(1.0, 3 * rows[0]["p"]) > rows[0]["p"]


def test_compare_errors_are_left_out_not_zero():
    with tempfile.TemporaryDirectory() as clean, tempfile.TemporaryDirectory() as noisy:
        clear_case(Path(clean))
        clear_case(Path(noisy), lfm3_errors={(131072, "niah_single_1"): 3, (4096, "vt"): 2})
        base, _ = run_compare(Path(clean))
        result, text = run_compare(Path(noisy))
    assert result["models"][C.LFM3]["errors_excluded"] == {"4096": 2, "131072": 3}
    assert "errors left out: lfm3-1.7b: 2 @ 4096, 3 @ 131072" in text
    for name in ("R1", "R3"):
        assert result["hypotheses"][name]["value"] == base["hypotheses"][name]["value"]
        assert result["hypotheses"][name]["n"] == base["hypotheses"][name]["n"]


def test_compare_missing_model_is_not_run_and_holm_keeps_m_3():
    with tempfile.TemporaryDirectory() as d:
        clear_case(Path(d))
        for suffix in (".json", ".jsonl.gz"):
            (Path(d) / f"{C.BIELIK}{suffix}").unlink()
        result, text = run_compare(Path(d))
        for suffix in (".json", ".jsonl.gz"):
            (Path(d) / f"{C.LFM3}{suffix}").unlink()
        no_lfm3, _ = run_compare(Path(d))
    h = result["hypotheses"]
    assert result["control"]["status"] == "PASS"  # the control needs LFM3 only
    assert (h["R2"]["verdict"], h["R2"]["outcome"], h["R2"]["missing"]) == ("not run", "not run", [C.BIELIK])
    assert f"| R2 | missing: {C.BIELIK} |" in text
    assert result["models"][C.BIELIK] is None and result["holm_m"] == 3
    low, high = sorted((h["R1"], h["R3"]), key=lambda x: x["p"])
    assert low["p_holm"] == min(1.0, 3 * low["p"])  # m stays 3 with R2 not run
    assert high["p_holm"] == max(low["p_holm"], min(1.0, 2 * high["p"]))
    assert no_lfm3["control"] == {"status": "not run", "missing": [C.LFM3]}
    assert all(x["verdict"] == "not run" for x in no_lfm3["hypotheses"].values())


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} passed")
