"""RULER 128K (api-benchmarks/ruler-128k): golden checks of summarize.py and compare.py on fixed fake data.

No network, RULER checkout, torch or lm-eval: the RULER metric is replaced by a stand-in with the same call shape
(`metric([pred], [refs])` -> percent), so these tests pin the aggregation, not RULER's scorer. Checked: the text
after the last `</think>` is what gets scored; an error is left out of the score, never counted as 0; the
13-task mean, the category means and the nulls for lengths that did not run or have a task without any score.
compare.py (hypotheses R1-R3 and the control) on fake per-sample results: a clear and a noise case, Holm with m = 3,
errors left out, null lengths listed, `not run` for a missing model, the control's 2-SE bound as measured and its
status `not comparable (Amendment 4)` with the hypotheses read; strict scoring (Amendment 4: no `</think>` -> 0) next
to the unchanged pre-registered scores. Generation path: the request body (protocol sampling, seed, output limit),
run.sh's protocol constants, the last attempt of a sample wins. Provenance: effective sampling (vLLM fills from
generation_config.json, PROTOCOL.md Amendment 3), commit/runner/hardware in the result, and the sha256 manifests that
summarize.py and compare.py check (an out dir from before them is summarized with warnings, never a crash).
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
import predict as P  # noqa: E402
import provenance as V  # noqa: E402
from ruler import answer_text, latest_records  # noqa: E402

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "ruler-128k"


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
             "output_tokens": 3, "finished": True, "closed_think": True},
            {"task": "qa_1", "length": 4096, "index": 1, "score": None, "error": "timeout"}]
    first, second = S.jsonl_rows(rows)
    assert len(first["answer"]) == S.ANSWER_CHARS and first["answer_truncated"] is True
    assert second == {"task": "qa_1", "length": 4096, "index": 1, "score": None, "error": "timeout"}


def by_category(retrieval, tracing, aggregation, qa):
    """task -> percent, one value per R3 category."""
    pct = {"retrieval": retrieval, "tracing": tracing, "aggregation": aggregation, "qa": qa}
    return {t: pct[c] for c, ts in S.CATEGORIES.items() for t in ts}


def write_model(results_dir, model, means, skipped=None, errors=None, task_skips=None, unclosed=None):
    """Fake results/<model>.json and .jsonl.gz: means is length -> percent or length -> task -> percent; each task
    gets 50 samples of 100 or 0 with that mean; errors is (length, task) -> error rows on top; task_skips is
    length -> task -> reason for tasks RULER could not generate (no rows). With `unclosed` ((length, task) -> k: the
    first k passing samples have no `</think>`) the result also has summarize.py's strict variant (Amendment 4)."""
    task_skips = task_skips or {}
    rows = []
    for length, pct in means.items():
        pct = pct if isinstance(pct, dict) else dict.fromkeys(S.TASKS, pct)
        for t in S.TASKS:
            if t in task_skips.get(length, {}):
                continue
            k, open_ = round(pct[t] / 2), (unclosed or {}).get((length, t), 0)
            rows += [{"task": t, "length": length, "index": i, "score": 100.0 if i < k else 0.0, "finished": True,
                      "closed_think": i >= open_} for i in range(50)]
    for (length, task), n in (errors or {}).items():
        rows += [{"task": task, "length": length, "index": 100 + j, "score": None, "error": "timeout"}
                 for j in range(n)]
    metrics = S.aggregate(rows, skipped or {}, S.LENGTHS, resamples=2, task_skips=task_skips)
    if unclosed is not None:
        run = {"settings": {"scored": S.CHAT_SCORED}, "lengths": S.LENGTHS, "tasks": S.TASKS}
        metrics["strict"] = S.strict_metrics(run, rows, skipped or {}, task_skips, resamples=2)
    (results_dir / f"{model}.json").write_text(json.dumps({"model": model, "other_metrics": metrics}))
    with gzip.open(results_dir / f"{model}.jsonl.gz", "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({k: v for k, v in r.items() if k != "finished"}) + "\n")
    V.write_manifest(results_dir, [f"{model}.json", f"{model}.jsonl.gz"], V.RESULTS)  # as summarize.py does


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
    assert result["control"]["measured"] == "PASS" and result["control"]["mean"] == 882 / 13
    assert result["control"]["status"] == C.CONTROL_STATUS
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
    assert sum(line.startswith("deviation: ") for line in text.splitlines()) == len(C.DEVIATIONS) == 4


def test_compare_noise_case_holm_and_control_fail():
    with tempfile.TemporaryDirectory() as d:
        write_model(Path(d), C.LFM3, {**dict.fromkeys(S.LENGTHS[:-1], 86), 131072: 84})
        write_model(Path(d), C.BIELIK, dict.fromkeys(S.LENGTHS[:4], 86), skipped={65536: WINDOW, 131072: WINDOW})
        result, text = run_compare(Path(d))
    assert result["control"]["measured"] == "FAIL" and result["control"]["status"] == C.CONTROL_STATUS
    assert text.index(": FAIL (as measured)") < text.index("| hypothesis |")
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
    assert result["control"]["measured"] == "PASS"  # the control needs LFM3 only
    assert (h["R2"]["verdict"], h["R2"]["outcome"], h["R2"]["missing"]) == ("not run", "not run", [C.BIELIK])
    assert f"| R2 | missing: {C.BIELIK} |" in text
    assert result["models"][C.BIELIK] is None and result["holm_m"] == 3
    low, high = sorted((h["R1"], h["R3"]), key=lambda x: x["p"])
    assert low["p_holm"] == min(1.0, 3 * low["p"])  # m stays 3 with R2 not run
    assert high["p_holm"] == max(low["p_holm"], min(1.0, 2 * high["p"]))
    assert no_lfm3["control"] == {"status": "not run", "missing": [C.LFM3]}
    assert all(x["verdict"] == "not run" for x in no_lfm3["hypotheses"].values())


QA2_SKIP = "RULER's qa_2 generator cannot fit a sample into 4096 tokens with this tokenizer"


def test_task_skip_is_null_not_zero_and_length_is_partial():
    tasks = S.TASKS
    rows = rows_for(4096, {t: [100.0, 100.0] for t in tasks if t != "qa_2"})
    rows += rows_for(8192, {t: [100.0] for t in tasks})
    m = S.aggregate(rows, {}, [4096, 8192], tasks, resamples=50, task_skips={4096: {"qa_2": QA2_SKIP}})
    l4 = m["per_length"]["4096"]
    assert l4["score"] == 100.0 and l4["n"] == 24  # mean over the 12 generated tasks, not 12 x 100 / 13 = 92.31
    assert l4["partial"] is True and l4["skipped_tasks"] == {"qa_2": QA2_SKIP}
    assert m["per_task"]["4096"]["qa_2"] is None and m["errors"]["4096"] == {}
    assert m["per_category"]["4096"]["qa"] == 100.0  # qa_1 only
    assert "partial" not in m["per_length"]["8192"]
    # a partial headline length is not the 13-task headline: null with the reason
    run = {"model": "slayer1b-1.09-k70000", "date": "2026-11-22", "ruler_commit": "db43f92", "seed": 20261122,
           "num_samples": 50, "data_sources": {}, "settings": {}}
    metrics = {"per_length": {"131072": {**l4}}}
    result = S.result_json(run, metrics)
    assert result["score"] is None and result["reason"] == "partial at 131072: RULER could not generate qa_2"
    assert result["other_metrics"]["per_length"]["131072"]["score"] == 100.0  # kept as a descriptive number


def test_compare_partial_length_is_not_comparable():
    with tempfile.TemporaryDirectory() as d:
        write_model(Path(d), C.LFM3, LFM3_STEEP, task_skips={131072: {"qa_2": QA2_SKIP}, 8192: {"qa_2": QA2_SKIP}})
        write_model(Path(d), C.BIELIK, {4096: 70, 8192: 80, 16384: 90, 32768: 95},
                    skipped={65536: WINDOW, 131072: WINDOW})
        result, text = run_compare(Path(d))
    reason = "partial: RULER could not generate qa_2; not comparable (13-task mean undefined)"
    assert result["control"] == {"status": "not run", "missing": [f"{C.LFM3} @ 131072: {reason}"]}
    h = result["hypotheses"]
    assert h["R1"]["verdict"] == "not run" and h["R1"]["missing"] == [f"{C.LFM3} @ 131072: {reason}"]
    assert h["R3"]["verdict"] == "not run"  # needs 4096 and 131072 complete
    assert h["R2"]["lengths"] == [4096, 16384, 32768]  # 8192 is partial for LFM3
    assert result["models"][C.LFM3]["partial_lengths"]["131072"]["skipped_tasks"] == ["qa_2"]
    assert result["models"][C.LFM3]["per_length"]["131072"] is None
    assert f"excluded: {C.LFM3} @ 131072: {reason}" in text and "control: not run" in text


def control_run(mean, se):
    """A fake LFM3 run for compare.control: the mean at 131072 is `mean`, its bootstrap SE exactly `se`."""
    d = se / 2 ** 0.5  # stdev of [mean - d, mean + d] is d * sqrt(2)
    return {"point": {C.LONG: dict.fromkeys(S.TASKS, mean)}, "resamples": 2,
            "boot": {C.LONG: {t: [mean - d, mean + d] for t in S.TASKS}},
            "scores": {C.LONG: {t: [mean] for t in S.TASKS}}}


def test_control_passes_within_2_se_only():
    for z, status in ((0.0, "PASS"), (1.9, "PASS"), (-1.9, "PASS"), (2.1, "FAIL"), (-2.1, "FAIL"), (2.5, "FAIL"),
                      (-2.9, "FAIL")):
        c = C.control({C.LFM3: control_run(C.CONTROL_CARD + z * 1.5, 1.5)})
        assert abs(c["z"] - z) < 1e-9 and abs(c["se"] - 1.5) < 1e-9, (z, c)
        assert c["measured"] == status and c["status"] == C.CONTROL_STATUS, (z, c)
    assert C.CONTROL_CARD == 65.56


def test_request_body_sends_protocol_sampling_seed_and_output_limit():
    import argparse
    args = argparse.Namespace(model="lfm3-1.7b", margin=256, temperature=0.6, top_p=0.95, seed=20261122)
    sample = {"index": 3, "input": "Find the number.", "answer_prefix": " Answer:"}
    assert P.request_body(args, sample, 1000, 32768, {}) == {
        "model": "lfm3-1.7b", "messages": [{"role": "user", "content": "Find the number. Answer:"}],
        "max_tokens": 32768 - 1000 - 256, "temperature": 0.6, "top_p": 0.95, "seed": 20261122}
    body = P.request_body(args, sample, 5000, 262144, {"chat_template_kwargs": {"enable_thinking": True}})
    assert body["max_tokens"] == 262144 - 5000 - 256 and body["chat_template_kwargs"] == {"enable_thinking": True}


def test_run_sh_carries_the_protocol_sampling():
    text = (BENCH / "run.sh").read_text(encoding="utf-8")
    values = {k: v for k, v in (line.split("=", 1) for line in text.splitlines()
                                if line.split("=", 1)[0] in ("SEED", "TEMPERATURE", "TOP_P", "NUM_SAMPLES"))}
    assert values == {"SEED": "20261122", "NUM_SAMPLES": "50", "TEMPERATURE": "0.6", "TOP_P": "0.95"}
    assert '--seed "$SEED" --temperature "$TEMPERATURE"' in text and '--top-p "$TOP_P"' in text
    protocol = (BENCH / "PROTOCOL.md").read_text(encoding="utf-8")
    assert "temperature 0.6, top_p 0.95" in protocol and "one sampling seed (20261122) per request" in protocol


def test_last_attempt_of_a_sample_wins():
    with tempfile.TemporaryDirectory() as d:
        raw = Path(d) / "niah_single_1.jsonl"
        raw.write_text("".join(json.dumps(r) + "\n" for r in [
            {"index": 0, "error": "HTTP 500"}, {"index": 0, "output": "a"},
            {"index": 1, "output": "b"}, {"index": 1, "error": "HTTP 503"}]))
        latest = latest_records(raw)
    assert latest == {0: {"index": 0, "output": "a"}, 1: {"index": 1, "error": "HTTP 503"}}


# LiquidAI/LFM3-1.7B @ 1da06bec generation_config.json, the fields vLLM reads
LFM3_CONFIG = {"bos_token_id": 124894, "do_sample": True, "eos_token_id": [124900], "pad_token_id": 124893,
               "repetition_penalty": 1.1, "temperature": 0.1, "top_k": 50, "transformers_version": "5.12.1"}
LFM3_SETTINGS = {"weights": "LiquidAI/LFM3-1.7B @ 1da06bec6a819da10b54c67e5c90972b46d81871",
                 "context_window": 262144, "seed": 20261122, "serving": "vLLM 0.34.0, bfloat16",
                 "max_tokens": "context window minus templated input", "temperature": 0.6, "top_p": 0.95,
                 "scored": "text after the last </think>"}


def lfm3_config(repo, revision):
    assert (repo, revision) == ("LiquidAI/LFM3-1.7B", "1da06bec6a819da10b54c67e5c90972b46d81871")
    return LFM3_CONFIG


def test_effective_sampling_per_serving_path():
    vllm = V.sampling(LFM3_SETTINGS, lfm3_config)
    # vLLM 0.34.0 fills what the request does not set from generation_config.json (PROTOCOL.md, Amendment 3)
    assert vllm["from_generation_config"] == {"repetition_penalty": 1.1, "top_k": 50}
    assert vllm["effective"] == {"repetition_penalty": 1.1, "presence_penalty": 0.0, "frequency_penalty": 0.0,
                                 "temperature": 0.6, "top_p": 0.95, "top_k": 50, "min_p": 0.0, "seed": 20261122,
                                 "max_tokens": "per request: context window minus templated input"}
    api = V.sampling({**LFM3_SETTINGS, "serving": "Fabryka AI API, https://fabryka.ai/v1/chat/completions",
                      "weights": "speakleash/Bielik-11B-v3.1-Instruct @ d6e755d3"}, read_config=None)
    assert api == {"sent": {"temperature": 0.6, "top_p": 0.95, "seed": 20261122,
                            "max_tokens": "per request: context window minus templated input"},
                   "server_defaults": "unknown (Fabryka API)"}
    slayer = V.sampling({"serving": "research/common/slayer_lm.py, bfloat16", "temperature": 0.0, "seed": 20261122,
                         "max_tokens": "RULER per-task answer budget", "weights": "SlayerLab/x @ y"})
    assert slayer["effective"]["decoding"].startswith("greedy") and slayer["sent"] == {
        "max_tokens": "RULER per-task answer budget"}


WINDOW_8192 = "the 4096-token context window does not hold a 8192-token RULER sample"


def fake_out_dir(root):
    """An out dir as run.sh leaves it: 4096 with niah_single_1 (two attempts per sample) and qa_2 skipped by RULER's
    generator, 8192 outside the window. Last attempt wins: sample 0 -> 100, sample 1 -> error (first wins: 0, 100)."""
    out = root / "out" / "lfm3-1.7b"
    (out / "8192").mkdir(parents=True)
    (out / "8192" / "skip.json").write_text(json.dumps({"reason": WINDOW_8192}))
    (out / "run.json").write_text(json.dumps({
        "model": "lfm3-1.7b", "date": "2026-11-22", "ruler_commit": "db43f92", "seed": 20261122, "num_samples": 2,
        "limit": None, "tasks": ["niah_single_1", "qa_2"], "lengths": [4096, 8192],
        "data_sources": {"squad.json": "abc"}, "settings": LFM3_SETTINGS}))
    data = out / "4096" / "data"
    (data / "niah_single_1").mkdir(parents=True)
    (data / "niah_single_1" / "validation.jsonl").write_text("".join(
        json.dumps({"index": i, "input": "...", "answer_prefix": "", "outputs": ["1234567"], "length": 4000}) + "\n"
        for i in range(2)))
    (data / "qa_2").mkdir()
    (data / "qa_2" / "skip.json").write_text(json.dumps({"reason": QA2_SKIP}))
    (out / "4096" / "raw").mkdir()
    (out / "4096" / "raw" / "niah_single_1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [
        {"index": 0, "output": "<think>1234567</think>no idea", "finish_reason": "stop", "output_tokens": 5},
        {"index": 1, "output": "<think>x</think>1234567", "finish_reason": "stop", "output_tokens": 3},
        {"index": 0, "output": "<think>x</think>It is 1234567.", "finish_reason": "stop", "output_tokens": 6},
        {"index": 1, "error": "HTTP 500: overloaded"}]))
    return out


def summarize_fake(out, root):
    return S.summarize_run(out, root / "results" / "lfm3-1.7b", keep, dict.fromkeys(S.TASKS, match_all),
                           read_config=lfm3_config)


def stops(fn, text):
    try:
        fn()
    except SystemExit as e:
        assert text in str(e), str(e)
        return
    raise AssertionError(f"did not stop ({text})")


def test_summarize_scores_last_attempt_and_task_skip_as_null():
    with tempfile.TemporaryDirectory() as d:
        out = fake_out_dir(Path(d))
        result = summarize_fake(out, Path(d))
        with gzip.open(Path(d) / "results" / "lfm3-1.7b.jsonl.gz", "rt") as f:
            lines = [json.loads(x) for x in f]
    m = result["other_metrics"]
    assert [(r["index"], r["score"]) for r in lines] == [(0, 100.0), (1, None)]
    assert m["per_task"]["4096"] == {"niah_single_1": 100.0, "qa_2": None}
    assert m["errors"]["4096"] == {"niah_single_1": 1}
    assert m["per_length"]["4096"]["score"] == 100.0 and m["per_length"]["4096"]["n"] == 1
    assert m["per_length"]["4096"]["partial"] is True and m["per_length"]["4096"]["skipped_tasks"] == {"qa_2": QA2_SKIP}
    assert m["per_length"]["8192"] == {"score": None, "reason": WINDOW_8192}
    assert result["score"] is None and result["reason"] == "length not run"


def test_summarize_old_out_dir_records_gaps_and_writes_manifests():
    """An out dir from a run.sh before generation.jsonl and inputs.sha256.json: summarized, gaps null with reasons."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        out = fake_out_dir(root)
        result = summarize_fake(out, root)
        again = summarize_fake(out, root)
        manifest = json.loads((root / "results" / V.RESULTS).read_text())
        files = {n: V.sha256(root / "results" / n) for n in ("lfm3-1.7b.json", "lfm3-1.7b.jsonl.gz")}
        with open(out / "4096" / "raw" / "niah_single_1.jsonl", "a") as f:
            f.write(json.dumps({"index": 1, "output": "1234567", "finish_reason": "stop", "output_tokens": 1}) + "\n")
        stops(lambda: summarize_fake(out, root), "sha256 differs")
    prov = result["provenance"]
    assert prov["generation"] is None and "no generation.jsonl" in prov["generation_reason"]
    assert prov["summarize"]["code"] == V.code_version()
    assert prov["summarize"]["runner_sha256"]["summarize.py"] == V.sha256(BENCH / "summarize.py")
    assert set(prov["summarize"]["runner_sha256"]) == set(V.RUNNER_FILES)
    assert {"gpu", "platform", "machine", "processor", "cpu_count"} <= set(prov["summarize"]["hardware"])
    sampling = result["settings"]["sampling"]
    assert sampling["from_generation_config"] == {"repetition_penalty": 1.1, "top_k": 50} and "recorded" in sampling
    assert len(result["warnings"]) == 2 and "no generation.jsonl" in result["warnings"][0]
    assert V.INPUTS in result["warnings"][1]
    assert again["warnings"] == result["warnings"]  # the manifest written by summarize.py keeps saying so
    assert manifest == files


def test_summarize_new_out_dir_carries_generation_provenance_and_checks_inputs():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        out = fake_out_dir(root)
        entry = V.record_generation(out, lfm3_config)
        V.record_inputs(out)
        result = summarize_fake(out, root)
        (out / "4096" / "raw" / "qa_2.jsonl").write_text("{}\n")
        stops(lambda: summarize_fake(out, root), "not in")
        (out / "4096" / "raw" / "qa_2.jsonl").unlink()
        (out / "8192" / "skip.json").unlink()
        stops(lambda: summarize_fake(out, root), "missing: 8192/skip.json")
        (out / "8192" / "skip.json").write_text(json.dumps({"reason": WINDOW_8192}))
        with open(out / "generation.jsonl", "a") as f:
            f.write(json.dumps({**entry, "sampling": V.sampling(LFM3_SETTINGS, lambda r, v: {})}) + "\n")
        V.record_inputs(out)
        stops(lambda: summarize_fake(out, root), "different sampling")
    assert result["warnings"] == []
    assert result["provenance"]["generation"] == [{k: entry[k] for k in ("time", "code", "runner_sha256", "hardware")}]
    assert entry["code"] == V.code_version() and entry["runner_sha256"]["predict.py"] == V.sha256(BENCH / "predict.py")
    assert result["settings"]["sampling"] == entry["sampling"]
    assert result["settings"]["sampling"]["effective"]["repetition_penalty"] == 1.1
    assert result["settings"]["temperature"] == 0.6


def test_compare_checks_result_sha256():
    with tempfile.TemporaryDirectory() as d:
        clear_case(Path(d))
        result, text = run_compare(Path(d))
        assert result["warnings"] == [] and len(result["inputs_sha256"]) == 6
        assert result["provenance"]["code"] == V.code_version()
        (Path(d) / V.RESULTS).unlink()  # results summarized before results.sha256.json existed
        unrecorded, text = run_compare(Path(d))
        summary = Path(d) / f"{C.LFM3}.json"
        summary.write_text(summary.read_text() + "\n")
        stops(lambda: run_compare(Path(d)), "sha256 differs")
    assert len(unrecorded["warnings"]) == 3 and f"warning: {C.LFM3}: result files not in" in text


def strict_out_dir(root, settings):
    """One task at 131072, five samples: closed + right (stop), UNclosed + needle in the reasoning (stop), closed +
    wrong, an error, closed + right but cut at the limit (length). Pre-registered 100, 100, 0, -, 100 = 75;
    strict (no `</think>` -> 0): 100, 0, 0, -, 100 = 50. The flag is `</think>`, not finish_reason."""
    out = root / "out" / "lfm3-1.7b"
    (out / "131072" / "data" / "niah_single_1").mkdir(parents=True)
    (out / "run.json").write_text(json.dumps({
        "model": "lfm3-1.7b", "date": "2026-11-22", "ruler_commit": "db43f92", "seed": 20261122, "num_samples": 5,
        "limit": None, "tasks": ["niah_single_1"], "lengths": [131072], "data_sources": {}, "settings": settings}))
    (out / "131072" / "data" / "niah_single_1" / "validation.jsonl").write_text("".join(
        json.dumps({"index": i, "input": "...", "answer_prefix": "", "outputs": ["1234567"], "length": 131000}) + "\n"
        for i in range(5)))
    (out / "131072" / "raw").mkdir()
    (out / "131072" / "raw" / "niah_single_1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [
        {"index": 0, "output": "<think>x</think>It is 1234567.", "finish_reason": "stop", "output_tokens": 6},
        {"index": 1, "output": "<think>maybe 1234567 ... 1234567", "finish_reason": "stop", "output_tokens": 9},
        {"index": 2, "output": "<think>x</think>I do not know.", "finish_reason": "stop", "output_tokens": 6},
        {"index": 3, "error": "HTTP 500: overloaded"},
        {"index": 4, "output": "<think>x</think>1234567 1234567", "finish_reason": "length", "output_tokens": 9}]))
    return out


def test_strict_scoring_zeroes_outputs_without_think_end_and_keeps_pre_registered():
    with tempfile.TemporaryDirectory() as d:
        result = summarize_fake(strict_out_dir(Path(d), LFM3_SETTINGS), Path(d))
        with gzip.open(Path(d) / "results" / "lfm3-1.7b.jsonl.gz", "rt") as f:
            lines = [json.loads(x) for x in f]
    with tempfile.TemporaryDirectory() as d:
        slayer = summarize_fake(strict_out_dir(Path(d), {"serving": "research/common/slayer_lm.py, bfloat16",
                                                         "max_tokens": "RULER per-task answer budget"}), Path(d))
    m = result["other_metrics"]
    assert (result["score"], result["n"]) == (75.0, 4) and m["per_task"]["131072"]["niah_single_1"] == 75.0
    assert m["errors"]["131072"] == {"niah_single_1": 1}
    strict = m["strict"]
    assert strict["applies"] is True and strict["per_task"]["131072"]["niah_single_1"] == 50.0
    assert strict["per_length"]["131072"]["score"] == 50.0 and strict["per_length"]["131072"]["n"] == 4
    assert strict["no_think_end"] == {"131072": {"niah_single_1": 1}}
    assert (result["strict"]["score"], result["strict"]["n"], result["strict"]["rule"]) == (50.0, 4, S.STRICT_RULE)
    assert [(r["index"], r["score"], r.get("closed_think")) for r in lines] == [
        (0, 100.0, True), (1, 100.0, False), (2, 0.0, True), (3, None, None), (4, 100.0, True)]
    # Slayer: raw prompt, no reasoning block, so the strict variant does not apply (null with the reason)
    assert slayer["score"] == 75.0 and slayer["other_metrics"]["strict"]["applies"] is False
    assert slayer["strict"]["score"] is None and "raw prompt" in slayer["strict"]["reason"]


def test_compare_control_not_comparable_and_strict_next_to_pre_registered():
    with tempfile.TemporaryDirectory() as d:
        # LFM3 at 131072: 5 passing fwe samples never closed their reasoning -> strict 10 points lower on fwe
        write_model(Path(d), C.LFM3, {**LFM3_STEEP, 131072: {**LFM3_STEEP[131072], "fwe": 90}},
                    unclosed={(131072, "fwe"): 5})
        write_model(Path(d), C.BIELIK, {4096: 70, 8192: 80, 16384: 90},
                    skipped={32768: FIT, 65536: WINDOW, 131072: WINDOW})
        result, text = run_compare(Path(d))
    pre, strict = (882 + 50) / 13, (882 + 50 - 10) / 13
    c = result["control"]
    assert c["status"] == C.CONTROL_STATUS and c["measured"] == "FAIL" and c["mean"] == pre and c["z"] > 2
    assert abs(c["strict"]["mean"] - strict) < 1e-9
    assert f"z = {c['z']:.2f}: FAIL (as measured)" in text and f"control status: {C.CONTROL_STATUS}" in text
    h = result["hypotheses"]
    assert h["R1"]["verdict"] != "not run" and h["R3"]["verdict"] != "not run"  # read despite the FAIL
    assert h["R1"]["value"] == pre and abs(h["R1"]["strict"]["value"] - strict) < 1e-9
    assert h["R1"]["strict"]["verdict"] == "clear" and h["R2"]["strict"]["verdict"] == "not run"  # Bielik: no strict
    assert abs(h["R3"]["strict"]["value"] - h["R3"]["value"]) > 1  # aggregation drops more under strict
    m = result["models"][C.LFM3]
    assert m["per_length"]["131072"] == round(pre, 2) and m["strict_per_length"]["131072"] == round(strict, 2)
    assert m["strict_per_length"]["4096"] == m["per_length"]["4096"]  # every output there closed its reasoning
    assert result["models"][C.BIELIK]["strict_per_length"] is None
    assert f"| {C.LFM3} | strict | " in text and f"| {C.LFM3} | pre-registered | " in text


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} passed")
