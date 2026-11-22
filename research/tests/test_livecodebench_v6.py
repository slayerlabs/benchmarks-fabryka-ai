"""LiveCodeBench v6 (api-benchmarks/livecodebench-v6): golden checks of the summary and of the scored text.

No network, no weights, no torch or lm-eval. Fixed fake graded records pin pass@1 and its stderr, pass@1 per
difficulty and on the v6-only problems, the budget rule (an answer counts at budget B only if it passed, finished
and used at most B output tokens), and that infrastructure errors and prompts over the context are left out of n
instead of counted as wrong. `after_think` pins which text goes to code extraction; with the pinned LiveCodeBench
clone in the benchmark's `.cache/` (run.sh makes it), its `extract_code` is checked on the same outputs.
compare.py (PROTOCOL.md hypotheses L1-L3) is checked on fixed fake per-problem results: a clear lead, a noise
difference, Holm ordering with m = 3, errors left out of both sides of a pair, and `not run` without a model file.
Run: python3 tests/test_livecodebench_v6.py (or pytest).
"""
import gzip
import importlib.util
import json
import math
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "livecodebench-v6"
sys.path.insert(0, str(BENCH))
import lcb  # noqa: E402
import summarize  # noqa: E402


class Skipped(Exception):
    pass


def skip(reason):
    try:
        import pytest
    except ImportError:
        raise Skipped(reason)
    pytest.skip(reason)


def rec(qid, passed, difficulty="easy", tokens=100, finished=True, v6_only=False, status="ok", error_code=None):
    ok = status == "ok"
    return {"question_id": qid, "platform": "atcoder", "difficulty": difficulty, "contest_date": "2025-03-01T00:00:00",
            "in_v6_only": v6_only, "status": status, "pass": passed if ok else None,
            "prompt_tokens": 300, "output_tokens": tokens if ok else None, "context": 262144,
            "finished": finished if ok else None, "finish_reason": ("stop" if finished else "length") if ok else None,
            "error": None if ok else "URLError('refused')",
            "eval_metadata": ({"error_code": error_code} if error_code else {}) if ok else None,
            "code": "print(1)" if ok else None, "started": "2026-11-23T10:00:00+00:00"}


RECORDS = [
    rec("a", True, "easy", tokens=3000, v6_only=True),       # passes at 4096, 16384 and no limit
    rec("b", True, "medium", tokens=10000),                  # passes at 16384 and no limit
    rec("c", True, "hard", tokens=2000, finished=False),     # passed, but cut at the context: no budget
    rec("d", False, "hard", tokens=100, v6_only=True, error_code=-5),  # LCB runner error, graded as a fail by LCB
    rec("e", False, "easy", status="error"),                 # our request failed: not in n
    rec("f", False, "medium", status="unsupported"),         # prompt over the context: not in n
]


def test_pass_at_1_and_stderr():
    m = summarize.metrics(RECORDS)
    assert m["n"] == 4
    assert m["score"] == 75.0
    assert m["stderr"] == round(100 * math.sqrt(0.75 * 0.25 / 4), 2) == 21.65


def test_errors_are_not_wrong_answers():
    m = summarize.metrics(RECORDS)
    assert (m["errors"], m["unsupported"], m["problems"]) == (1, 1, 6)
    # the same four answered problems without the two unscored ones give the same score
    assert summarize.metrics(RECORDS[:4])["score"] == m["score"]
    assert m["evaluator_runner_errors"] == 1 and m["unfinished"] == 1


def test_per_difficulty_and_v6_only():
    m = summarize.metrics(RECORDS)
    assert m["per_difficulty"]["easy"] == {"score": 100.0, "stderr": 0.0, "n": 1}
    assert m["per_difficulty"]["medium"] == {"score": 100.0, "stderr": 0.0, "n": 1}
    assert m["per_difficulty"]["hard"] == {"score": 50.0, "stderr": 35.36, "n": 2}
    assert m["v6_only"] == {"score": 50.0, "stderr": 35.36, "n": 2}


def test_budgets_from_tokens_and_finished_flag():
    m = summarize.metrics(RECORDS)
    assert m["pass_at_budget"]["4096"]["score"] == 25.0      # only a
    assert m["pass_at_budget"]["16384"]["score"] == 50.0     # a and b; c passed but did not finish
    assert m["pass_at_budget"]["4096"]["n"] == m["n"]
    assert summarize.passes_within(rec("x", True, tokens=4096), 4096)
    assert not summarize.passes_within(rec("x", True, tokens=4097), 4096)
    assert m["output_tokens"] == {"mean": 3775.0, "median": 2500.0, "max": 10000}


def test_nothing_scored_is_null_not_zero():
    m = summarize.metrics([rec("e", False, status="error")])
    assert (m["score"], m["stderr"], m["n"]) == (None, None, 0)


OUTPUT = ("Let me try.\n```python\nprint('draft')\n```\nHmm, wrong.</think>\n\nFinal:\n"
          "```python\nprint(int(input()) * 2)\n```\n")


def test_after_think():
    assert lcb.after_think(OUTPUT) == "\n\nFinal:\n```python\nprint(int(input()) * 2)\n```\n"
    assert lcb.after_think("a</think>b</think>c") == "c"
    assert lcb.after_think("```python\nprint(1)\n```") == "```python\nprint(1)\n```"


def test_lcb_extract_code_on_the_text_after_think():
    if not (lcb.LCB_DIR / "lcb_runner").is_dir():
        skip("no LiveCodeBench clone in .cache/ (run.sh makes it)")
    sys.path.insert(0, str(lcb.LCB_DIR))
    from lcb_runner.lm_styles import LMStyle
    from lcb_runner.utils.extraction_utils import extract_code
    style = LMStyle(lcb.PROMPT_STYLE)
    assert extract_code(lcb.after_think(OUTPUT), style) == "print(int(input()) * 2)"
    # unfinished thinking with no </think>: the whole output, so the last block written so far
    assert extract_code(lcb.after_think("```python\nprint('draft')\n```\nstill thinking"), style) == "print('draft')"
    assert extract_code(lcb.after_think("<think>no code</think>no code either"), style) == ""


def test_summary_files():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        out.mkdir()
        (out / "graded.jsonl").write_text("".join(json.dumps(r) + "\n" for r in RECORDS), encoding="utf-8")
        summarize.main(str(out), str(Path(tmp) / "results" / "m"), None)
        result = json.loads((Path(tmp) / "results" / "m.json").read_text(encoding="utf-8"))
        assert (result["model"], result["score"], result["n"], result["date"]) == ("m", 75.0, 4, "2026-11-23")
        assert result["other_metrics"]["pass_at_budget"]["16384"]["score"] == 50.0
        with gzip.open(Path(tmp) / "results" / "m.jsonl.gz", "rt", encoding="utf-8") as f:
            lines = [json.loads(line) for line in f]
        assert [line["score"] for line in lines] == [1, 1, 1, 0, None, None]
        assert lines[0]["output"] == "print(1)" and "</think>" not in json.dumps(lines)
        summarize.main(str(out), str(Path(tmp) / "results" / "m"), 6)
        assert (out / "m-limit6.json").is_file()


# compare.py: hypotheses L1-L3 on fixed fake per-problem results (the .jsonl.gz rows summarize.py writes)
_spec = importlib.util.spec_from_file_location("lcb_compare", BENCH / "compare.py")
compare = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compare)
LEVELS = ("easy", "medium", "hard")


def row(tid, passed, difficulty, tokens=2000, finished=True, v6_only=False, status="ok"):
    ok = status == "ok"
    return {"task_id": tid, "score": int(passed) if ok else None, "difficulty": difficulty, "in_v6_only": v6_only,
            "status": status, "pass": passed if ok else None, "output_tokens": tokens if ok else None,
            "finished": finished if ok else None}


def write_run(results, model, rows, score=None, stderr=None):
    results.mkdir(parents=True, exist_ok=True)
    with gzip.open(results / f"{model}.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write("".join(json.dumps(r) + "\n" for r in rows))
    (results / f"{model}.json").write_text(json.dumps({"model": model, "score": score, "stderr": stderr}),
                                           encoding="utf-8")


def run_of(passes_per_level, tokens, n_per_level=30, prefix="p"):
    """passes_per_level: how many of the first problems of each level pass; every 5th problem is v6-only."""
    return [row(f"{prefix}{lvl}{i:02d}", i < passes_per_level[lvl], lvl, tokens=tokens, v6_only=i % 5 == 0)
            for lvl in LEVELS for i in range(n_per_level)]


def by_id(rows):
    return {r["id"]: r for r in rows}


CLEAR_LFM = run_of({"easy": 30, "medium": 30, "hard": 30}, tokens=10000)
CLEAR_QWEN = run_of({"easy": 10, "medium": 10, "hard": 10}, tokens=2000)


def test_compare_clear_lead_refutes_l1_l2_l3():
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM)
        write_run(res, compare.QWEN9, CLEAR_QWEN, score=70.0, stderr=1.4)
        a = compare.analyse(res)
    h = by_id(a["hypotheses"])
    # d = 1 on 60 problems, 0 on 30: mean 2/3, SE = sd(d)/sqrt(90)
    se = math.sqrt((60 * (1 / 3) ** 2 + 30 * (2 / 3) ** 2) / 89) / math.sqrt(90)
    assert h["L1"]["n"] == 90 and math.isclose(h["L1"]["value"], 100 * 2 / 3)
    assert math.isclose(h["L1"]["se"], 100 * se) and math.isclose(h["L1"]["z"], (2 / 3) / se)
    assert (h["L1"]["verdict"], h["L1"]["outcome"]) == ("clear", "refuted")
    assert (h["L2"]["signs"], h["L2"]["outcome"], h["L2"]["sign_not_established"]) == ("+++", "refuted", [])
    # equal cost: LFM3 at 16384 (10000 tokens, the first of the tied LFM3 budgets) against Qwen3.5-9B at 4096
    # (2000 tokens): 2 x 1.73e9 x 10000 vs 2 x 8.95e9 x 2000, ratio 0.97, the nearest to 1 of the nine pairs
    assert (h["L3"]["budget_a"], h["L3"]["budget_b"]) == (16384, 4096)
    assert h["L3"]["mean_cost_a"] == 2 * compare.PARAMETERS["lfm3-1.7b"] * 10000
    assert h["L3"]["mean_cost_b"] == 2 * compare.PARAMETERS["qwen3.5-9b"] * 2000
    assert (h["L3"]["verdict"], h["L3"]["outcome"]) == ("clear", "refuted")
    assert a["control"]["status"] == "passed"  # 70.0 vs 69.86, within 2 x 1.4
    v6 = a["descriptive"][0]["v6_only"]  # every 5th problem: 6 per level, LFM3 passes all, Qwen3.5-9B the first 2
    assert v6["n"] == 18 and math.isclose(v6["value"], 100 * 12 / 18)


def test_compare_noise_confirms_l1():
    lfm = run_of({"easy": 12, "medium": 12, "hard": 11}, tokens=3000)
    qwen = run_of({"easy": 11, "medium": 11, "hard": 12}, tokens=3000)
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, lfm)
        write_run(res, compare.QWEN9, qwen, score=60.0, stderr=1.5)
        a = compare.analyse(res)
    h = by_id(a["hypotheses"])
    assert math.isclose(h["L1"]["value"], 100 / 90)  # +1, +1, -1 over 90 problems
    assert abs(h["L1"]["z"]) < 2 and (h["L1"]["verdict"], h["L1"]["outcome"]) == ("noise", "confirmed")
    # signs + + -, but each level rests on one problem: not established, so neither confirmed nor refuted
    assert h["L2"]["signs"] == "++-" and h["L2"]["sign_not_established"] == list(LEVELS)
    assert h["L2"]["outcome"] == "not established"
    assert a["control"]["status"] == "failed"  # 60.0 is 6.6 SE from the card's 69.86


def test_compare_l2_predicted_pattern():
    lfm = run_of({"easy": 30, "medium": 30, "hard": 10}, tokens=3000)
    qwen = run_of({"easy": 10, "medium": 10, "hard": 30}, tokens=3000)
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, lfm)
        write_run(res, compare.QWEN9, qwen)
        h = by_id(compare.analyse(res)["hypotheses"])
    assert (h["L2"]["signs"], h["L2"]["sign_not_established"], h["L2"]["outcome"]) == ("++-", [], "confirmed")
    levels = h["L2"]["per_difficulty"]
    assert h["L2"]["p"] == max(levels[lvl]["p"] for lvl in LEVELS)


def test_compare_holm_ordering():
    assert compare.holm([0.01, 0.04, 0.03], m=3) == [0.03, 0.06, 0.06]  # 3 x 0.01, then max(2 x 0.03, ...), 1 x 0.04
    assert compare.holm([0.04, 0.001, 0.5], m=3) == [0.08, 0.003, 0.5]
    # a hypothesis not run keeps m = 3 and ranks last: the others get multipliers 3 and 2, never fewer
    assert compare.holm([0.01, None, 0.04], m=3) == [0.03, None, 0.08]
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM)
        write_run(res, compare.QWEN9, CLEAR_QWEN)
        hs = compare.analyse(res)["hypotheses"]
    assert [h["p_holm"] for h in hs] == compare.holm([h["p"] for h in hs], m=3)
    assert all(h["p_holm"] >= h["p"] for h in hs)


def test_compare_excludes_errors_from_both_sides():
    lfm = CLEAR_LFM + [row("x1", False, "easy", status="error"), row("x2", True, "hard")]
    qwen = CLEAR_QWEN + [row("x1", True, "easy"), row("x2", False, "hard", status="unsupported"),
                         row("x3", False, "medium")]  # x3: no LFM3 row at all
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM)
        write_run(res, compare.QWEN9, CLEAR_QWEN)
        clean = compare.analyse(res)
        write_run(res, compare.LFM, lfm)
        write_run(res, compare.QWEN9, qwen)
        dirty = compare.analyse(res)
    for c, d in zip(clean["hypotheses"], dirty["hypotheses"]):
        assert (c["value"], c["se"], c["z"], c["n"]) == (d["value"], d["se"], d["z"], d["n"])
    assert dirty["hypotheses"][0]["excluded"] == {"not_scored_a": 1, "not_scored_b": 1, "missing_a": 1,
                                                  "missing_b": 0, "total": 3}
    assert compare.cost("lfm3-1.7b", row("y", False, "easy", tokens=20000, finished=False), 4096) == \
        2 * compare.PARAMETERS["lfm3-1.7b"] * 4096  # an answer cut at the budget used the budget
    assert not compare.passes_within(row("y", True, "easy", tokens=20000, finished=False), None)


def test_compare_not_run_when_a_model_file_is_absent():
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM)
        write_run(res, "qwen3.5-4b", CLEAR_QWEN)
        compare.main(res)
        a = json.loads((res / "hypotheses.json").read_text(encoding="utf-8"))
        text = compare.report(a)
    assert [h["outcome"] for h in a["hypotheses"]] == ["not run"] * 3
    assert all(h["missing"] == ["qwen3.5-9b"] and h["p_holm"] is None for h in a["hypotheses"])
    assert a["holm_m"] == 3 and a["control"]["status"] == "not run"
    desc = {d["b"]: d for d in a["descriptive"]}
    assert desc["qwen3.5-4b"]["status"] == "ok" and desc["qwen3.5-4b"]["overall"]["verdict"] == "clear"
    assert desc["bielik-11b-v3.1-vllm"] == {"a": "lfm3-1.7b", "b": "bielik-11b-v3.1-vllm", "status": "not run",
                                            "missing": ["bielik-11b-v3.1-vllm"]}
    assert "| L1 | | | | | not run | not run | not run (missing: qwen3.5-9b) | |" in text
    assert any(line.startswith("deviation: a hypothesis that is not run") for line in text.splitlines())


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok      {name}")
            except Skipped as e:
                print(f"skipped {name}: {e}")
            except AssertionError as e:
                failed += 1
                print(f"FAILED  {name}: {e!r}")
    raise SystemExit(1 if failed else 0)
