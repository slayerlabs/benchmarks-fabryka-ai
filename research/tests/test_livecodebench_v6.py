"""LiveCodeBench v6 (api-benchmarks/livecodebench-v6): golden checks of the summary and of the scored text.

No network, no weights, no torch or lm-eval. Fixed fake graded records pin pass@1 and its stderr, pass@1 per
difficulty and on the v6-only problems, the budget rule (an answer counts at budget B only if it passed, finished
and used at most B output tokens), and that infrastructure errors and prompts over the context are left out of n
instead of counted as wrong. `after_think` pins which text goes to code extraction; with the pinned LiveCodeBench
clone in the benchmark's `.cache/` (run.sh makes it), its `extract_code` is checked on the same outputs.
Run: python3 tests/test_livecodebench_v6.py (or pytest).
"""
import gzip
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
