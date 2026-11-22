"""LiveCodeBench v6 (api-benchmarks/livecodebench-v6): golden checks of the summary and of the scored text.

No network, no weights, no torch or lm-eval. Fixed fake graded records pin pass@1 and its stderr, pass@1 per
difficulty and on the v6-only problems, the budget rule (an answer counts at budget B only if it passed, finished
and used at most B output tokens), and that infrastructure errors and prompts over the context are left out of n
instead of counted as wrong. `after_think` pins which text goes to code extraction; with the pinned LiveCodeBench
clone in the benchmark's `.cache/` (run.sh makes it), its `extract_code` is checked on the same outputs.
compare.py (PROTOCOL.md hypotheses L1-L3, Amendment 1: LFM3-1.7B against Bielik 11B v3.1, control LFM3-1.7B against
its card's 73.46) is checked on fixed fake per-problem results: a clear lead, a noise difference, Holm ordering with
m = 3, errors left out of both sides of a pair, and `not run` without a model file. lcb.py's request layer for the
Fabryka API is checked against a fake server on 127.0.0.1: the request fields, max_tokens = context - local prompt
count - margin, retries with the shared pause, a 400 not retried, a prompt over the context never sent. The vLLM
request (its exact body and max_tokens = context - prompt from /tokenize), the evaluator settings, the alignment of
LiveCodeBench's grades with the problems in `score`, the v6-only flag and order of `load_rows`, the control's 2 SE
threshold, the recorded sampling settings (sent, and vLLM's defaults from generation_config.json), the provenance in
run.json and the result, and the sha256 checks of each step's input are checked with fakes of LiveCodeBench's
modules and of the Hugging Face download, so without the clone, GPU or network.
Run: python3 tests/test_livecodebench_v6.py (or pytest).
"""
import argparse
import contextlib
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import tempfile
import types
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "livecodebench-v6"
sys.path.insert(0, str(BENCH))
import ablation  # noqa: E402
import lcb  # noqa: E402
import provenance  # noqa: E402
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


def write_out(out, records, sampling=None):
    """An out dir as lcb.py score leaves it: graded.jsonl with its sha256 in manifest.json, and run.json."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "graded.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    provenance.record(out, ["graded.jsonl"], "test")
    sampling = sampling or {"request_sampling": {"temperature": 0.6}, "server_defaults": {"top_k": 50}}
    run = {"generation": [{"step": "lcb.py generate", "code_commit": "abc", "gpu": "GPU X", "sampling": sampling}],
           "scoring": {"step": "lcb.py score", "code_commit": "abc", "cpu": "CPU Y"}}
    (out / "run.json").write_text(json.dumps(run), encoding="utf-8")


def test_summary_files():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out"
        write_out(out, RECORDS)
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


def row(tid, passed, difficulty, tokens=2000, finished=True, v6_only=False, status="ok", platform="atcoder",
        contest_date="2025-03-01T00:00:00", output="print(1)", prompt_tokens=300):
    ok = status == "ok"
    return {"task_id": tid, "score": int(passed) if ok else None, "difficulty": difficulty, "in_v6_only": v6_only,
            "status": status, "pass": passed if ok else None, "output_tokens": tokens if ok else None,
            "finished": finished if ok else None, "platform": platform, "contest_date": contest_date,
            "output": output if ok else None, "prompt_tokens": prompt_tokens}


def write_run(results, model, rows, score=None, stderr=None):
    results.mkdir(parents=True, exist_ok=True)
    with gzip.open(results / f"{model}.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write("".join(json.dumps(r) + "\n" for r in rows))
    (results / f"{model}.json").write_text(json.dumps({"model": model, "score": score, "stderr": stderr}),
                                           encoding="utf-8")
    provenance.record(results, [f"{model}.jsonl.gz", f"{model}.json"], "test")  # as summarize.py does


def run_of(passes_per_level, tokens, n_per_level=30, prefix="p"):
    """passes_per_level: how many of the first problems of each level pass; every 5th problem is v6-only."""
    return [row(f"{prefix}{lvl}{i:02d}", i < passes_per_level[lvl], lvl, tokens=tokens, v6_only=i % 5 == 0)
            for lvl in LEVELS for i in range(n_per_level)]


def by_id(rows):
    return {r["id"]: r for r in rows}


CLEAR_LFM = run_of({"easy": 30, "medium": 30, "hard": 30}, tokens=10000)
CLEAR_BIELIK = run_of({"easy": 10, "medium": 10, "hard": 10}, tokens=2000)


def test_compare_clustered_se_by_contest_and_platform():
    # 4 contests of 10 problems: LFM3 passes all; Bielik passes none of contest 1 and 4, 5 of contest 2, all of 3,
    # so d per contest sums to 10, 5, 0, 10. Platforms: contests 1 and 4 atcoder, 2 leetcode, 3 codeforces.
    contests = [("atcoder", "2025-01-04", 10), ("leetcode", "2025-01-05", 5), ("codeforces", "2025-01-06", 0),
                ("atcoder", "2025-01-11", 10)]
    lfm, bielik = [], []
    for c, (platform, date, lead) in enumerate(contests):
        for i in range(10):
            kw = {"platform": platform, "contest_date": f"{date}T00:00:00"}
            lfm.append(row(f"c{c}p{i}", True, "easy", **kw))
            bielik.append(row(f"c{c}p{i}", i >= lead, "easy", **kw))
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, lfm)
        write_run(res, compare.BIELIK, bielik)
        a = compare.analyse(res)
    l1 = by_id(a["hypotheses"])["L1"]
    n, mean = 40, 25 / 40

    def cluster_se(sums_sizes):  # sqrt(G/(G-1) * sum_g (sum_{i in g} (d_i - mean))^2) / n, by hand
        g = len(sums_sizes)
        return math.sqrt(g / (g - 1) * sum((s - k * mean) ** 2 for s, k in sums_sizes)) / n

    by_contest, by_platform = l1["clustered"]["contest"], l1["clustered"]["platform"]
    se_c = cluster_se([(10, 10), (5, 10), (0, 10), (10, 10)])
    se_p = cluster_se([(20, 20), (5, 10), (0, 10)])
    assert (by_contest["k"], by_contest["df"], by_platform["k"], by_platform["df"]) == (4, 3, 3, 2)
    assert math.isclose(by_contest["value"], 100 * mean) and math.isclose(by_contest["se"], 100 * se_c)
    assert math.isclose(by_platform["se"], 100 * se_p) and math.isclose(by_platform["t"], mean / se_p)
    # two-sided p of Student's t in closed form: df = 3 and df = 2
    x = (mean / se_c) / math.sqrt(3)
    assert math.isclose(by_contest["p"], 1 - 2 / math.pi * (x / (1 + x * x) + math.atan(x)), rel_tol=1e-9)
    t = mean / se_p
    assert math.isclose(by_platform["p"], 1 - t / math.sqrt(2 + t * t), rel_tol=1e-9)
    assert by_contest["verdict"] == by_platform["verdict"] == "noise"  # t 2.61 (df 3), 2.07 (df 2)
    assert l1["verdict"] == "clear"  # over problems z = 0.625 / 0.0775 = 8.06: clustering changes the verdict
    assert set(by_id(a["hypotheses"])["L3"]["clustered"]) == {"contest", "platform"}
    assert "| L1 | platform | 3 | +62.50 ± 30.14 | t = +2.07 | 2 | 0.174 | noise |" in compare.report(a)


def test_compare_clear_lead_refutes_l1_l2_l3():
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM, score=74.0, stderr=1.4)
        write_run(res, compare.BIELIK, CLEAR_BIELIK)
        a = compare.analyse(res)
    h = by_id(a["hypotheses"])
    # d = 1 on 60 problems, 0 on 30: mean 2/3, SE = sd(d)/sqrt(90)
    se = math.sqrt((60 * (1 / 3) ** 2 + 30 * (2 / 3) ** 2) / 89) / math.sqrt(90)
    assert h["L1"]["n"] == 90 and math.isclose(h["L1"]["value"], 100 * 2 / 3)
    assert math.isclose(h["L1"]["se"], 100 * se) and math.isclose(h["L1"]["z"], (2 / 3) / se)
    assert (h["L1"]["verdict"], h["L1"]["outcome"]) == ("clear", "refuted")
    assert (h["L2"]["signs"], h["L2"]["outcome"], h["L2"]["sign_not_established"]) == ("+++", "refuted", [])
    # equal cost: LFM3 at 16384 (10000 tokens, the first of the tied LFM3 budgets) against Bielik at 4096
    # (2000 tokens): 2 x 1.73e9 x 10000 vs 2 x 11.17e9 x 2000, ratio 0.77, the nearest to 1 of the nine pairs
    assert (h["L3"]["budget_a"], h["L3"]["budget_b"]) == (16384, 4096)
    assert h["L3"]["mean_cost_a"] == 2 * compare.PARAMETERS["lfm3-1.7b"] * 10000
    assert h["L3"]["mean_cost_b"] == 2 * compare.PARAMETERS["bielik-11b-v3.1"] * 2000
    # descriptive: the prompt (300 tokens each here) counted on top, 2 x parameters x (prompt + output tokens)
    assert (h["L3"]["mean_prompt_tokens_a"], h["L3"]["mean_prompt_tokens_b"]) == (300, 300)
    assert h["L3"]["mean_cost_with_prompt_b"] == 2 * compare.PARAMETERS["bielik-11b-v3.1"] * 2300
    assert (h["L3"]["verdict"], h["L3"]["outcome"]) == ("clear", "refuted")
    assert a["control"]["status"] == "passed"  # LFM3-1.7B 74.0 vs its card's 73.46, within 2 x 1.4
    v6 = a["descriptive"][0]["v6_only"]  # every 5th problem: 6 per level, LFM3 passes all, Bielik the first 2
    assert v6["n"] == 18 and math.isclose(v6["value"], 100 * 12 / 18)


def test_compare_noise_confirms_l1():
    lfm = run_of({"easy": 12, "medium": 12, "hard": 11}, tokens=3000)
    bielik = run_of({"easy": 11, "medium": 11, "hard": 12}, tokens=3000)
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, lfm, score=60.0, stderr=1.5)
        write_run(res, compare.BIELIK, bielik)
        a = compare.analyse(res)
    h = by_id(a["hypotheses"])
    assert math.isclose(h["L1"]["value"], 100 / 90)  # +1, +1, -1 over 90 problems
    assert abs(h["L1"]["z"]) < 2 and (h["L1"]["verdict"], h["L1"]["outcome"]) == ("noise", "confirmed")
    # signs + + -, but each level rests on one problem: not established, so neither confirmed nor refuted
    assert h["L2"]["signs"] == "++-" and h["L2"]["sign_not_established"] == list(LEVELS)
    assert h["L2"]["outcome"] == "not established"
    assert a["control"]["status"] == "failed"  # 60.0 is 9.0 SE from the card's 73.46
    assert compare.CONTROL_CARD == 73.46


def test_compare_l2_predicted_pattern():
    lfm = run_of({"easy": 30, "medium": 30, "hard": 10}, tokens=3000)
    bielik = run_of({"easy": 10, "medium": 10, "hard": 30}, tokens=3000)
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, lfm)
        write_run(res, compare.BIELIK, bielik)
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
        write_run(res, compare.BIELIK, CLEAR_BIELIK)
        hs = compare.analyse(res)["hypotheses"]
    assert [h["p_holm"] for h in hs] == compare.holm([h["p"] for h in hs], m=3)
    assert all(h["p_holm"] >= h["p"] for h in hs)


def test_compare_excludes_errors_from_both_sides():
    lfm = CLEAR_LFM + [row("x1", False, "easy", status="error"), row("x2", True, "hard")]
    bielik = CLEAR_BIELIK + [row("x1", True, "easy"), row("x2", False, "hard", status="unsupported"),
                             row("x3", False, "medium")]  # x3: no LFM3 row at all
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM)
        write_run(res, compare.BIELIK, CLEAR_BIELIK)
        clean = compare.analyse(res)
        write_run(res, compare.LFM, lfm)
        write_run(res, compare.BIELIK, bielik)
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
        write_run(res, compare.BIELIK, CLEAR_BIELIK)
        compare.main(res)
        files = provenance.read_manifest(res)["files"]
        assert (files["hypotheses.json"]["sha256"], files["hypotheses.json"]["written_by"]) == \
            (sha256(res / "hypotheses.json"), "compare.py")
        a = json.loads((res / "hypotheses.json").read_text(encoding="utf-8"))
        text = compare.report(a)
    assert [h["outcome"] for h in a["hypotheses"]] == ["not run"] * 3
    assert all(h["missing"] == ["lfm3-1.7b"] and h["p_holm"] is None for h in a["hypotheses"])
    assert a["holm_m"] == 3 and a["control"]["status"] == "not run"
    assert a["descriptive"] == [{"a": "lfm3-1.7b", "b": "bielik-11b-v3.1", "status": "not run",
                                 "missing": ["lfm3-1.7b"]}]
    assert sorted(compare.PARAMETERS) == ["bielik-11b-v3.1", "lfm3-1.7b"]
    assert "| L1 | | | | | not run | not run | not run (missing: lfm3-1.7b) | |" in text
    assert any(line.startswith("deviation: a hypothesis that is not run") for line in text.splitlines())


# lcb.py request layer against a local fake OpenAI-compatible server (127.0.0.1, no outside network)
class FakeAPI:
    """Answers chat completions; the first `fail` requests get `fail_code` (503 by default), the next `truncate` a body
    cut short of its Content-Length (IncompleteRead), and a request with max_tokens 1 gets 400. The answer is
    `content` with `finish_reason`."""

    def __init__(self, fail=0, reasoning=False, fail_code=503, truncate=0, content="```python\nprint(1)\n```",
                 finish_reason="stop"):
        import http.server
        import threading
        self.fail, self.requests, self.headers, self.tokenize_requests = fail, [], [], []
        api = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path.endswith("/tokenize"):  # vLLM's prompt count
                    api.tokenize_requests.append(body)
                    return self.reply(200, {"count": 1000, "max_model_len": 262144})
                api.requests.append(body)
                api.headers.append(dict(self.headers))
                if body["max_tokens"] == 1:
                    return self.reply(400, {"error": {"message": "This request field is not supported"}})
                if body["max_tokens"] == 2:
                    return self.reply(401, {"error": {"code": "invalid_api_key"}})
                if len(api.requests) <= api.fail:
                    return self.reply(fail_code, {"error": "busy"})
                message = {"role": "assistant", "content": content}
                if reasoning:
                    message["reasoning_content"] = "hmm"
                self.reply(200, {"choices": [{"message": message, "finish_reason": finish_reason}],
                                 "usage": {"prompt_tokens": 1071, "completion_tokens": 9}},
                           cut=len(api.requests) <= api.fail + truncate)

            def do_GET(self):  # vLLM's /version and /v1/models, recorded for a reused server
                if self.path == "/version":
                    return self.reply(200, {"version": "0.34.0"})
                self.reply(200, {"object": "list", "data": [{"id": "lfm3-1.7b", "root": "LiquidAI/LFM3-1.7B"}]})

            def reply(self, code, payload, cut=False):
                data = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data) + (100 if cut else 0)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1/chat/completions"

    def close(self):
        self.server.shutdown()


MESSAGES = [{"role": "system", "content": "s"}, {"role": "user", "content": "q"}]


def api_server(url, count=1000, context=32768, margin=64, retries=30):
    return lcb.Server(model="bielik-11b-v3.1", chat_url=url, retries=retries, timeout=10,
                      headers={"Authorization": "Bearer test"}, count=lambda m: count, context=context,
                      margin=margin, gate=lcb.Gate(0.01, 0.04))


def test_api_request_body_and_limit():
    api = FakeAPI()
    try:
        record = lcb.answer(api_server(api.url), MESSAGES)
    finally:
        api.close()
    body = api.requests[0]
    # only the fields the Fabryka API accepted in IFEval: no n, penalties, stop, chat_template_kwargs; plain messages
    assert sorted(body) == ["max_tokens", "messages", "model", "seed", "temperature", "top_p"]
    assert body["messages"] == MESSAGES and body["model"] == "bielik-11b-v3.1"
    assert (body["temperature"], body["top_p"], body["seed"]) == (0.6, 0.95, 20261122)
    assert body["max_tokens"] == 32768 - 1000 - 64  # context - local prompt count - margin
    assert api.headers[0]["Authorization"] == "Bearer test"
    assert (record["status"], record["prompt_tokens"], record["context"], record["max_tokens"]) == \
        ("ok", 1000, 32768, 32768 - 1000 - 64)
    assert (record["output_tokens"], record["finished"], record["api_prompt_tokens"]) == (9, True, 1071)


def test_api_retries_with_shared_pause():
    api = FakeAPI(fail=3)
    server = api_server(api.url)
    try:
        record = lcb.answer(server, MESSAGES)
    finally:
        api.close()
    assert record["status"] == "ok" and len(api.requests) == 4  # 3 x 503, then the answer
    assert server.gate.pause == server.gate.pause_min  # a success resets the pause
    gate = lcb.Gate(10, 300)
    for _ in range(7):
        gate.failed()
    assert gate.pause == 300  # 10, 20, 40, 80, 160, 300 (capped)


def test_api_errors_are_errors_not_fails():
    api = FakeAPI(fail=100)
    try:
        with_retries = api_server(api.url, retries=3)
        try:
            lcb.answer(with_retries, MESSAGES)
            raise AssertionError("expected an HTTPError after 3 attempts")
        except lcb.urllib.error.HTTPError as e:
            assert e.code == 503 and len(api.requests) == 3
        api.requests.clear()
        try:  # a 400 is not retried
            lcb.answer(api_server(api.url, count=32768 - 64 - 1), MESSAGES)
            raise AssertionError("expected Rejected")
        except lcb.Rejected as e:
            assert "HTTP 400" in str(e) and len(api.requests) == 1
        too_long = lcb.answer(api_server(api.url, count=32768 - 64), MESSAGES)
        assert too_long["status"] == "unsupported" and len(api.requests) == 1  # never sent
        try:  # a wrong key stops the whole run instead of turning every problem into an error
            lcb.answer(api_server(api.url, count=32768 - 64 - 2), MESSAGES)
            raise AssertionError("expected SetupError")
        except lcb.SetupError as e:
            assert "HTTP 401" in str(e) and len(api.requests) == 2
    finally:
        api.close()


def test_api_reasoning_field_stops_the_run():
    api = FakeAPI(reasoning=True)
    try:
        lcb.answer(api_server(api.url), MESSAGES)
        raise AssertionError("expected SetupError")
    except lcb.SetupError:
        pass
    finally:
        api.close()


# vLLM request, evaluator settings, grade alignment, problem set, sampling record, provenance and input checks

LFM3_REPO = "LiquidAI/LFM3-1.7B@1da06bec6a819da10b54c67e5c90972b46d81871"
# generation_config.json of LFM3_REPO, sampling fields as in the file
LFM3_GENERATION_CONFIG = {"_from_model_config": True, "bos_token_id": 124894, "do_sample": True,
                          "eos_token_id": [124900], "pad_token_id": 124893, "repetition_penalty": 1.1,
                          "temperature": 0.1, "top_k": 50, "transformers_version": "5.12.1", "use_cache": True}
VLLM_SAMPLING = {"n": 1, "temperature": 0.6, "top_p": 0.95, "seed": 20261122, "frequency_penalty": 0,
                 "presence_penalty": 0}
# a draft inside the thinking, the answer after </think>: only the answer may reach the evaluator
THINKING_OUTPUT = "Plan.\n```python\nprint(0)\n```\n</think>\n```python\nprint(1)\n```"


@contextlib.contextmanager
def patched(obj, **attrs):
    old = {k: getattr(obj, k) for k in attrs}
    for k, v in attrs.items():
        setattr(obj, k, v)
    try:
        yield
    finally:
        for k, v in old.items():
            setattr(obj, k, v)


def exit_message(fn, *args):
    """The message of the sys.exit that `fn(*args)` must raise."""
    try:
        fn(*args)
    except SystemExit as e:
        return str(e.code)
    raise AssertionError(f"{fn.__name__} did not stop")


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_evaluator_and_prompt_style_pinned():
    # PROTOCOL.md / README "Settings": LiveCodeBench's OpenAIChat prompt; evaluator 6 s per test case, 12 processes
    assert (lcb.EVAL_TIMEOUT, lcb.EVAL_PROCESSES, lcb.PROMPT_STYLE) == (6, 12, "OpenAIChat")
    parser = lcb.LCB_DIR / "lcb_runner" / "runner" / "parser.py"
    if not parser.is_file():
        skip("no LiveCodeBench clone in .cache/ (run.sh makes it)")
    text = " ".join(parser.read_text(encoding="utf-8").split())
    assert '"--timeout", type=int, default=6,' in text  # the runner defaults the constants claim to copy
    assert '"--num_process_evaluate", type=int, default=12,' in text


class FakeProblem:
    """Stands for LiveCodeBench's CodeGenerationProblem; `passes` says what the fake evaluator grades it."""

    def __init__(self, **row):
        self.row = row

    def get_evaluation_sample(self):
        return {"question_id": self.row["question_id"], "passes": self.row["passes"]}


def fake_lcb(calls):
    """LiveCodeBench's modules as lcb.py uses them: the evaluator grades each sample by its `passes` and returns
    results keyed by sample index, which extract_instance_results orders (pass_k_utils.py @ LCB_COMMIT)."""
    def codegen_metrics(samples, generations, num_process_evaluate, timeout):
        calls.append({"num_process_evaluate": num_process_evaluate, "timeout": timeout, "generations": generations})
        results = {i: [[1, 1] if s["passes"] else [1, -2]] for i, s in enumerate(samples)}
        return {}, results, [[json.dumps({"question_id": s["question_id"]})] for s in samples]

    def extract_instance_results(results):
        grades = {k: [all(g > 0 for g in gen) for gen in res] for k, res in results.items()}
        return [v for _, v in sorted(grades.items(), key=lambda item: item[0])]

    def prompt(problem, style):
        return [{"role": "system", "content": "s"}, {"role": "user", "content": problem.row["question_id"]}]

    return argparse.Namespace(
        benchmark=types.SimpleNamespace(CodeGenerationProblem=FakeProblem),
        evaluation=types.SimpleNamespace(codegen_metrics=codegen_metrics,
                                         extract_instance_results=extract_instance_results),
        prompts=types.SimpleNamespace(format_prompt_generation=prompt),
        extraction=types.SimpleNamespace(extract_code=lambda text, style: text.strip()), style=lcb.PROMPT_STYLE)


ROWS = [{"question_id": q, "platform": "atcoder", "difficulty": d, "contest_date": "2025-01-01T00:00:00",
         "in_v6_only": v6, "passes": p}
        for q, d, v6, p in (("q1", "easy", False, True), ("q2", "medium", True, False), ("q3", "hard", False, False))]


def vllm_args(api, out):
    return argparse.Namespace(
        out_dir=str(out), base_url=api.url.removesuffix("/v1/chat/completions"), chat_url="", model="lfm3-1.7b",
        model_repo=LFM3_REPO, limit=None, chat_template_kwargs="", api_key_env="", tokenizer="", context=0, margin=0,
        card_sampling=False, retries=3, concurrency=2, request_timeout=10)


def test_vllm_pipeline_body_alignment_provenance_and_input_checks():
    api = FakeAPI(content=THINKING_OUTPUT)
    calls = []
    with tempfile.TemporaryDirectory() as tmp, \
            patched(lcb, lcb_modules=lambda: fake_lcb(calls), load_rows=lambda limit: [dict(r) for r in ROWS],
                    generation_config=lambda repo: LFM3_GENERATION_CONFIG if repo == LFM3_REPO else {}):
        out, results = Path(tmp) / "out", Path(tmp) / "results"
        try:
            lcb.generate(vllm_args(api, out))
        finally:
            api.close()

        # the vLLM request: exactly the PROTOCOL.md sampling and seed, max_tokens = context - prompt from /tokenize
        assert len(api.requests) == 3 and len(api.tokenize_requests) == 3
        for body in api.requests:
            assert {k: v for k, v in body.items() if k != "messages"} == \
                {"model": "lfm3-1.7b", **VLLM_SAMPLING, "max_tokens": 262144 - 1000}
        gen = [json.loads(line) for line in (out / "generations.jsonl").read_text(encoding="utf-8").splitlines()]
        assert {(g["context"], g["prompt_tokens"], g["max_tokens"]) for g in gen} == {(262144, 1000, 261144)}

        # generation-time record: our commit, runner checksums, machine, and the sampling in effect
        run = json.loads((out / "run.json").read_text(encoding="utf-8"))
        g = run["generation"][0]
        state = provenance.code_state()
        assert g["code_commit"] == state["code_commit"] and g["dirty"] == state["dirty"]
        assert g["runner_sha256"]["lcb.py"] == sha256(BENCH / "lcb.py")
        assert set(g["runner_sha256"]) == set(provenance.RUNNER_FILES)
        assert "gpu" in g and g["platform"] and g["cpu"]
        assert g["sampling"] == {
            "request_sampling": VLLM_SAMPLING, "server_defaults": {"repetition_penalty": 1.1, "top_k": 50},
            "server_defaults_source": f"vLLM generation_config=auto: {LFM3_REPO} generation_config.json",
            "effective": {"repetition_penalty": 1.1, "top_k": 50, **VLLM_SAMPLING}}
        assert g["server"]["version"] == {"version": "0.34.0"} and g["server"]["models"]["data"][0]["id"] == "lfm3-1.7b"
        assert provenance.read_manifest(out)["files"]["generations.jsonl"]["sha256"] == \
            sha256(out / "generations.jsonl")
        # no failed request: an empty event log, recorded, and zero counts in run.json
        assert (out / "api-events.jsonl").read_text(encoding="utf-8") == ""
        assert provenance.read_manifest(out)["files"]["api-events.jsonl"]["sha256"] == sha256(out / "api-events.jsonl")
        assert g["api_events"] == {"events": 0, "by_action": {}, "by_status": {}, "problems": 0}

        lcb.score(argparse.Namespace(out_dir=str(out), limit=None))
        assert [(c["timeout"], c["num_process_evaluate"]) for c in calls] == [(6, 12)]
        # the evaluator gets the code from the text after the last </think>, not the draft inside the thinking
        assert calls[0]["generations"] == [["```python\nprint(1)\n```"]] * 3
        graded = [json.loads(line) for line in (out / "graded.jsonl").read_text(encoding="utf-8").splitlines()]
        # each grade on its own problem: q1 passes, q2 and q3 fail, the evaluator's metadata names the same problem
        assert [(r["question_id"], r["pass"], r["eval_metadata"]["question_id"], r["in_v6_only"]) for r in graded] == \
            [("q1", True, "q1", False), ("q2", False, "q2", True), ("q3", False, "q3", False)]
        assert json.loads((out / "run.json").read_text(encoding="utf-8"))["scoring"]["step"] == "lcb.py score"

        summarize.main(str(out), str(results / "lfm3-1.7b"), None)
        result = json.loads((results / "lfm3-1.7b.json").read_text(encoding="utf-8"))
        assert result["score"] == round(100 / 3, 2) and result["other_metrics"]["v6_only"]["score"] == 0.0
        assert result["settings"]["server_defaults"] == {"repetition_penalty": 1.1, "top_k": 50}
        assert result["settings"]["request_sampling"] == VLLM_SAMPLING
        assert result["settings"]["eval_timeout_s"] == 6 and result["settings"]["prompt_style"] == "OpenAIChat"
        p = result["provenance"]
        assert p["generation"][0]["code_commit"] == state["code_commit"] and "sampling" not in p["generation"][0]
        assert p["scoring"]["step"] == "lcb.py score" and p["summary"]["step"] == "summarize.py"
        assert p["inputs_sha256"] == {"graded.jsonl": sha256(out / "graded.jsonl")}
        assert result["raw_outputs"]["sha256"] == sha256(out / "generations.jsonl")
        assert p["api_events"] == {"file": "out/lfm3-1.7b/api-events.jsonl (not committed)",
                                   "sha256": sha256(out / "api-events.jsonl"), "events": 0, "by_action": {},
                                   "by_status": {}, "problems": 0}
        files = provenance.read_manifest(results)["files"]
        assert {n: f["sha256"] for n, f in files.items()} == \
            {n: sha256(results / n) for n in ("lfm3-1.7b.json", "lfm3-1.7b.jsonl.gz")}

        # every step refuses an input changed after it was written
        with gzip.open(results / "lfm3-1.7b.jsonl.gz", "rt", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f]
        compare.analyse(results)  # untouched: runs
        rows[1]["pass"], rows[1]["score"] = True, 1
        with gzip.open(results / "lfm3-1.7b.jsonl.gz", "wt", encoding="utf-8") as f:
            f.write("".join(json.dumps(r) + "\n" for r in rows))
        assert "sha256" in exit_message(compare.analyse, results)
        graded_text = (out / "graded.jsonl").read_text(encoding="utf-8")
        (out / "graded.jsonl").write_text(graded_text.replace('"pass": false', '"pass": true', 1), encoding="utf-8")
        assert "sha256" in exit_message(summarize.main, str(out), str(results / "lfm3-1.7b"), None)
        with (out / "generations.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({**gen[1], "output": "print(2)"}) + "\n")
        assert "sha256" in exit_message(lcb.score, argparse.Namespace(out_dir=str(out), limit=None))
        assert "sha256" in exit_message(lcb.generate, vllm_args(api, out))  # a resume checks what it keeps


def test_compare_and_summarize_refuse_unrecorded_or_changed_inputs():
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp) / "results"
        write_run(res, compare.LFM, CLEAR_LFM, score=74.0, stderr=1.4)
        write_run(res, compare.BIELIK, CLEAR_BIELIK)
        compare.analyse(res)
        (res / f"{compare.LFM}.json").write_text(json.dumps({"model": compare.LFM, "score": 73.5, "stderr": 1.4}),
                                                 encoding="utf-8")
        message = exit_message(compare.analyse, res)
        assert "lfm3-1.7b.json" in message and "sha256" in message
        (res / provenance.MANIFEST).unlink()
        assert "no sha256" in exit_message(compare.analyse, res)
        out = Path(tmp) / "out"
        write_out(out, RECORDS)
        (out / provenance.MANIFEST).unlink()
        assert "no sha256" in exit_message(summarize.main, str(out), str(res / "m"), None)
        write_out(out, RECORDS)
        (out / "run.json").unlink()
        assert "run.json" in exit_message(summarize.main, str(out), str(res / "m"), None)


def test_load_rows_order_and_v6_only():
    files = {"test.jsonl": ["b", "a"], "test2.jsonl": ["c"], "test3.jsonl": [], "test4.jsonl": ["d"],
             "test5.jsonl": ["e"], "test6.jsonl": ["z", "f"]}  # test6.jsonl: the problems added in v6
    seen = []
    with tempfile.TemporaryDirectory() as tmp:
        for name, ids in files.items():
            (Path(tmp) / name).write_text("".join(json.dumps({"question_id": i}) + "\n" for i in ids), encoding="utf-8")

        def download(repo, name, repo_type, revision):
            seen.append((repo, name, repo_type, revision))
            return str(Path(tmp) / name)

        fake = types.ModuleType("huggingface_hub")
        fake.hf_hub_download = download
        old = sys.modules.get("huggingface_hub")
        sys.modules["huggingface_hub"] = fake
        try:
            rows, first3 = lcb.load_rows(None), lcb.load_rows(3)
        finally:
            if old is None:
                del sys.modules["huggingface_hub"]
            else:
                sys.modules["huggingface_hub"] = old
    assert [r["question_id"] for r in rows] == ["a", "b", "c", "d", "e", "f", "z"]  # sorted by question_id
    assert [r["question_id"] for r in rows if r["in_v6_only"]] == ["f", "z"]
    assert [r["question_id"] for r in first3] == ["a", "b", "c"]
    assert seen[:6] == [(lcb.DATA_REPO, n, "dataset", lcb.DATA_REVISION) for n in lcb.RELEASE_FILES["release_v6"]]


def test_control_within_two_se():
    # PROTOCOL.md, Amendment 1: passed within 2 SE of the card's 73.46, failed beyond (also between 2 and 3 SE)
    for z, status in ((1.9, "passed"), (-1.9, "passed"), (2.5, "failed"), (-2.5, "failed"), (-2.9, "failed")):
        with tempfile.TemporaryDirectory() as tmp:
            res = Path(tmp)
            write_run(res, compare.LFM, CLEAR_LFM, score=compare.CONTROL_CARD + z * 1.0, stderr=1.0)
            c = compare.control(res)
        assert c["status"] == status and math.isclose(c["z"], z), (z, c)


def test_sampling_record():
    body = lcb.request_body(lcb.Server(model="m", chat_url="u", retries=1, timeout=1, tokenize_url="t"), [], 0)
    # vLLM fills what the request leaves unset; temperature and top_p come from the request
    assert lcb.vllm_defaults(LFM3_GENERATION_CONFIG, body) == {"repetition_penalty": 1.1, "top_k": 50}
    assert lcb.vllm_defaults({**LFM3_GENERATION_CONFIG, "max_new_tokens": 100, "min_p": None}, body) == \
        {"repetition_penalty": 1.1, "top_k": 50}
    assert lcb.vllm_defaults({"min_p": 0.05}, body) == {"min_p": 0.05}
    assert lcb.sampling(api_server("http://127.0.0.1:9/v1/chat/completions")) == {
        "request_sampling": {"temperature": 0.6, "top_p": 0.95, "seed": 20261122},
        "server_defaults": "unknown (Fabryka API)"}
    try:
        lcb.sampling(lcb.Server(model="m", chat_url="u", retries=1, timeout=1, tokenize_url="t"))
        raise AssertionError("expected SetupError without --model-repo")
    except lcb.SetupError:
        pass


# PROTOCOL.md, Amendment 4: lfm3-1.7b-cardsampling request, context rule, and the A1 equivalence analysis
CARD = {"repetition_penalty": 1.0, "top_k": 0}


def vllm_server(api, context=0, card=False):
    base = api.url.removesuffix("/v1/chat/completions")
    return lcb.Server(model="lfm3-1.7b", chat_url=api.url, retries=3, timeout=10, tokenize_url=f"{base}/tokenize",
                      model_repo=LFM3_REPO, context=context, sampling_extra=dict(CARD) if card else {})


def test_card_sampling_request_and_protocol_context():
    api = FakeAPI()  # its /tokenize: 1000 prompt tokens, max_model_len 262144
    try:
        record = lcb.answer(vllm_server(api, context=262144, card=True), MESSAGES)
        body = {k: v for k, v in api.requests[-1].items() if k != "messages"}
        assert body == {"model": "lfm3-1.7b", **VLLM_SAMPLING, **CARD, "max_tokens": 262144 - 1000}
        assert (record["context"], record["max_tokens"]) == (262144, 261144)
        # a server allowing more than the protocol's context: max_tokens still from the protocol's 262144 ...
        smaller = lcb.answer(vllm_server(api, context=200000, card=True), MESSAGES)
        assert (smaller["context"], smaller["max_tokens"], api.requests[-1]["max_tokens"]) == (200000, 199000, 199000)
        # ... and one allowing less stops the run instead of sending a shorter limit
        try:
            lcb.answer(vllm_server(api, context=300000, card=True), MESSAGES)
            raise AssertionError("expected SetupError")
        except lcb.SetupError as e:
            assert "262144" in str(e)
        lcb.answer(vllm_server(api), MESSAGES)  # lfm3-1.7b: unchanged body, the server's context
        assert {k: v for k, v in api.requests[-1].items() if k != "messages"} == \
            {"model": "lfm3-1.7b", **VLLM_SAMPLING, "max_tokens": 261144}
    finally:
        api.close()
    assert lcb.CARD_SAMPLING == CARD
    with patched(lcb, generation_config=lambda repo: LFM3_GENERATION_CONFIG):
        s = lcb.sampling(vllm_server(api, card=True))
    # the request's values override generation_config.json: nothing left for the server to fill
    assert s["request_sampling"] == {**VLLM_SAMPLING, **CARD} and s["server_defaults"] == {}
    assert s["effective"]["repetition_penalty"] == 1.0 and s["effective"]["top_k"] == 0


def test_paired_equivalence_hand_example():
    # n = 120, one problem passed only by the original, one only by the ablation: d = +1, -1, 118 x 0
    # mean 0; sd = sqrt(2 / 119) = 0.129641; SE = 0.129641 / sqrt(120) = 0.0118346 -> 1.18346 pp
    # 90% CI = 0 ± 1.644854 x 1.18346 = ± 1.94664 pp, inside ±2: equivalent; p_upper = Phi(-2 / 1.18346) = 0.0455
    e = ablation.paired_equivalence([1, -1] + [0] * 118)
    assert e["n"] == 120 and e["delta"] == 0.0
    assert math.isclose(e["se"], 1.18346, abs_tol=1e-4)
    assert math.isclose(e["ci90"][0], -1.94664, abs_tol=1e-3) and math.isclose(e["ci90"][1], 1.94664, abs_tol=1e-3)
    assert math.isclose(e["p_upper"], 0.0455, abs_tol=5e-4) and math.isclose(e["p_tost"], e["p_upper"])
    assert e["verdict"] == "equivalent"  # a 95% CI (± 2.3196) would not be
    # n = 400, d = +1, +1, -1: Δ = 0.25 pp; var = (3 - 400 x 0.0025^2) / 399 = 0.00751253; SE = 0.433375 pp;
    # CI = 0.25 ± 0.71284 = [-0.46284, 0.96284]
    e = ablation.paired_equivalence([1, 1, -1] + [0] * 397)
    assert math.isclose(e["delta"], 0.25) and math.isclose(e["se"], 0.433375, abs_tol=1e-5)
    assert math.isclose(e["ci90"][0], -0.46284, abs_tol=1e-4) and math.isclose(e["ci90"][1], 0.96284, abs_tol=1e-4)
    # n = 10, d = +1, -1: SE = sqrt(2 / 9) / sqrt(10) = 14.907 pp; CI ± 24.52: not shown equivalent
    e = ablation.paired_equivalence([1, -1] + [0] * 8)
    assert math.isclose(e["se"], 14.9071, abs_tol=1e-3) and e["verdict"] == "not shown equivalent"
    # a shift: Δ = 3 pp outside the margin however small the SE
    e = ablation.paired_equivalence([1] * 3 + [0] * 97)
    assert math.isclose(e["delta"], 3.0) and e["verdict"] == "not shown equivalent"
    assert ablation.paired_equivalence([1])["verdict"] == "undecidable"


def test_mcnemar_exact():
    assert ablation.mcnemar(0, 0) == 1.0
    assert ablation.mcnemar(2, 1) == 1.0  # 2 x P(X <= 1 | 3) = 2 x 4/8, capped
    assert ablation.mcnemar(6, 0) == 2 / 64
    assert ablation.mcnemar(5, 1) == ablation.mcnemar(1, 5) == 14 / 64  # 2 x (1 + 6) / 64


SETTINGS = {"prompt_style": "OpenAIChat", "temperature": 0.6, "top_p": 0.95, "seed": 20261122,
            "max_tokens": "context minus prompt tokens", "context": 262144, "trials": 1,
            "scored_text": "after the last </think>", "eval_timeout_s": 6, "eval_processes": 12}
ORIGINAL_SETTINGS = {**SETTINGS, "request_sampling": VLLM_SAMPLING,
                     "server_defaults": {"repetition_penalty": 1.1, "top_k": 50}}
CARD_SETTINGS = {**SETTINGS, "request_sampling": {**VLLM_SAMPLING, **CARD}, "server_defaults": {}}


def write_ablation_run(results, model, passes, settings, extra_rows=()):
    rows = [{"task_id": f"t{i:03d}", "status": "ok", "pass": p, "score": int(p)} for i, p in enumerate(passes)]
    rows += list(extra_rows)
    results.mkdir(parents=True, exist_ok=True)
    with gzip.open(results / f"{model}.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write("".join(json.dumps(r) + "\n" for r in rows))
    score = round(100 * sum(passes) / len(passes), 2)
    (results / f"{model}.json").write_text(json.dumps({"model": model, "score": score, "settings": settings}),
                                           encoding="utf-8")
    provenance.record(results, [f"{model}.json", f"{model}.jsonl.gz"], "test")


def test_ablation_analysis_files_and_checks():
    original = [False if i == 1 else True for i in range(120)]  # t001 passes only with the card's sampling
    card = [False if i == 0 else True for i in range(120)]  # t000 passes only with the defaults
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_ablation_run(res, ablation.ORIGINAL, original + [True], ORIGINAL_SETTINGS)
        write_ablation_run(res, ablation.ABLATION, card, CARD_SETTINGS,
                           [{"task_id": "t120", "status": "error", "pass": None, "score": None}])
        ablation.main(res)
        a = json.loads((res / "ablation-a1.json").read_text(encoding="utf-8"))
        table = (res / "ablation-a1.md").read_text(encoding="utf-8")
        assert (a["n"], a["delta"], a["verdict"]) == (120, 0.0, "equivalent")
        assert a["excluded"] == {"not_scored_original": 0, "not_scored_ablation": 1, "missing_original": 0,
                                 "missing_ablation": 0, "total": 1}
        assert a["mcnemar"] == {"only_original": 1, "only_ablation": 1, "p_exact": 1.0, "descriptive": True}
        assert a["consequence"].startswith("A1 holds") and "| equivalent (margin ±2 pt) | 120 | 1 |" in table
        assert set(a["inputs_sha256"]) == {"lfm3-1.7b.json", "lfm3-1.7b.jsonl.gz", "lfm3-1.7b-cardsampling.json",
                                           "lfm3-1.7b-cardsampling.jsonl.gz"}
        files = provenance.read_manifest(res)["files"]  # each output's sha256, recorded by the step that wrote it
        assert {n: (files[n]["sha256"], files[n]["written_by"]) for n in ("ablation-a1.json", "ablation-a1.md")} == \
            {n: (sha256(res / n), "ablation.py") for n in ("ablation-a1.json", "ablation-a1.md")}
        # 5 problems passed only with the defaults: Δ = 5/120 = +4.17 pp, not shown equivalent; card score is headline
        write_ablation_run(res, ablation.ABLATION, [i >= 6 for i in range(120)], CARD_SETTINGS)
        a = ablation.analyse(res)
        assert a["verdict"] == "not shown equivalent" and "headline" in a["consequence"]
        assert a["mcnemar"]["only_original"] == 5 and a["mcnemar"]["only_ablation"] == 0
        # runs that differ in anything but the two settings, or ran with other values, are refused
        write_ablation_run(res, ablation.ABLATION, card, {**CARD_SETTINGS, "temperature": 0.7})
        assert "temperature" in exit_message(ablation.analyse, res)
        write_ablation_run(res, ablation.ABLATION, card, {**CARD_SETTINGS, "request_sampling": VLLM_SAMPLING,
                                                          "server_defaults": {"repetition_penalty": 1.1, "top_k": 50}})
        assert "Amendment 4 says" in exit_message(ablation.analyse, res)
        write_ablation_run(res, ablation.ABLATION, card, CARD_SETTINGS)
        with gzip.open(res / f"{ablation.ABLATION}.jsonl.gz", "wt", encoding="utf-8") as f:
            f.write(json.dumps({"task_id": "t000", "status": "ok", "pass": True, "score": 1}) + "\n")
        assert "sha256" in exit_message(ablation.analyse, res)


# API robustness and the event log (out/<model>/api-events.jsonl), finished flag, compare pins
def logged_server(url, path, retries=30, **kwargs):
    server = api_server(url, retries=retries, **kwargs)
    server.events = lcb.EventLog(path)
    return server


def read_events(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


def test_api_429_is_retried_and_logged():
    api = FakeAPI(fail=2, fail_code=429)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "api-events.jsonl"
        try:
            record = lcb.answer(logged_server(api.url, path), MESSAGES, "q7")
        finally:
            api.close()
        events = read_events(path)
    assert record["status"] == "ok" and len(api.requests) == 3  # 2 x 429, then the answer
    assert [(e["problem"], e["endpoint"], e["attempt"], e["status"], e["action"], e["pause_s"]) for e in events] == [
        ("q7", "/v1/chat/completions", 1, 429, "retry", 0.01), ("q7", "/v1/chat/completions", 2, 429, "retry", 0.02),
        ("q7", "/v1/chat/completions", 3, None, "recovered", None)]
    assert events[0]["error"] == '{"error": "busy"}' and events[0]["time"].endswith("+00:00")


def test_api_incomplete_read_is_retried_like_a_5xx():
    api = FakeAPI(truncate=2)  # the first two answers end before their Content-Length
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "api-events.jsonl"
        try:
            record = lcb.answer(logged_server(api.url, path), MESSAGES, "q1")
        finally:
            api.close()
        events = read_events(path)
    assert record["status"] == "ok" and len(api.requests) == 3
    assert [e["action"] for e in events] == ["retry", "retry", "recovered"]
    assert all("IncompleteRead" in e["error"] and e["status"] is None for e in events[:2])


def test_api_failures_logged_with_counts():
    api = FakeAPI(fail=100)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "api-events.jsonl"
        try:
            server = logged_server(api.url, path, retries=3)
            try:
                lcb.answer(server, MESSAGES, "a")
                raise AssertionError("expected an HTTPError after 3 attempts")
            except lcb.urllib.error.HTTPError:
                pass
            try:
                lcb.answer(logged_server(api.url, path, count=32768 - 64 - 1), MESSAGES, "b")  # 400
                raise AssertionError("expected Rejected")
            except lcb.Rejected:
                pass
            try:
                lcb.answer(logged_server(api.url, path, count=32768 - 64 - 2), MESSAGES, "c")  # 401
                raise AssertionError("expected SetupError")
            except lcb.SetupError:
                pass
        finally:
            api.close()
        events = read_events(path)
    assert [(e["problem"], e["status"], e["action"]) for e in events] == [
        ("a", 503, "retry"), ("a", 503, "retry"), ("a", 503, "gave_up"), ("b", 400, "rejected"), ("c", 401, "stop")]
    assert [e["pause_s"] for e in events[:3]] == [0.01, 0.02, 0.04]
    assert "not supported" in events[3]["error"]
    assert lcb.event_counts(events) == {"events": 5, "by_action": {"gave_up": 1, "rejected": 1, "retry": 2, "stop": 1},
                                        "by_status": {"400": 1, "401": 1, "503": 3}, "problems": 3}
    assert server.events.counts()["by_action"] == {"gave_up": 1, "retry": 2}  # this server's own events


def test_finished_follows_finish_reason():
    for reason, finished in (("stop", True), ("length", False)):
        api = FakeAPI(finish_reason=reason)
        try:
            record = lcb.answer(api_server(api.url), MESSAGES)
        finally:
            api.close()
        assert (record["finish_reason"], record["finished"]) == (reason, finished)


def test_summary_carries_api_events_or_null_with_reason():
    events = [{"problem": "a", "status": 503, "action": "retry"},
              {"problem": "a", "status": None, "action": "recovered"}]
    with tempfile.TemporaryDirectory() as tmp:
        out, res = Path(tmp) / "out", Path(tmp) / "results"
        write_out(out, RECORDS)
        summarize.main(str(out), str(res / "m"), None)
        p = json.loads((res / "m.json").read_text(encoding="utf-8"))["provenance"]
        assert p["api_events"] is None and p["api_events_reason"] == summarize.NO_EVENT_LOG
        run = json.loads((out / "run.json").read_text(encoding="utf-8"))
        run["generation"][0].update(api_events=None, api_events_reason="no retry log in this run")
        (out / "run.json").write_text(json.dumps(run), encoding="utf-8")
        summarize.main(str(out), str(res / "m"), None)
        p = json.loads((res / "m.json").read_text(encoding="utf-8"))["provenance"]
        assert p["api_events"] is None and p["api_events_reason"] == "no retry log in this run"
        (out / "api-events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events), encoding="utf-8")
        provenance.record(out, ["api-events.jsonl"], "test")
        summarize.main(str(out), str(res / "m"), None)
        p = json.loads((res / "m.json").read_text(encoding="utf-8"))["provenance"]
        assert p["api_events"] == {"file": "out/m/api-events.jsonl (not committed)",
                                   "sha256": sha256(out / "api-events.jsonl"), "events": 2,
                                   "by_action": {"recovered": 1, "retry": 1}, "by_status": {"503": 1, "none": 1},
                                   "problems": 1}
        with (out / "api-events.jsonl").open("a", encoding="utf-8") as f:
            f.write("{}\n")
        assert "sha256" in exit_message(summarize.main, str(out), str(res / "m"), None)


def test_compare_parameter_counts_pinned():
    # exact weight counts (compare.py, PARAMETERS): sums of the safetensors tensor shapes at the pinned revisions;
    # Bielik's equals its config arithmetic and the safetensors index `total_parameters`, not the card's "11B"
    assert compare.PARAMETERS == {"lfm3-1.7b": 1_728_801_536, "bielik-11b-v3.1": 11_168_796_672}
    assert compare.cost("bielik-11b-v3.1", row("y", True, "easy", tokens=2000), None) == 44_675_186_688_000


def test_l1_refuted_only_at_z_3():
    def outcome(z):
        return compare.l1({"overall": {"value": 1.0, "se": 1.0, "z": z, "p": None, "verdict": "", "n": 10}})["outcome"]
    assert [outcome(z) for z in (2.0, 2.99, 3.0, 36.3, -5.0, None)] == \
        ["confirmed", "confirmed", "refuted", "refuted", "confirmed", "undecidable"]


def test_control_uses_card_sampling_run_with_original_descriptive():
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM, score=72.23, stderr=1.38)
        assert compare.control(res)["run"] == "lfm3-1.7b"  # before the ablation: the original run
        write_run(res, compare.CONTROL_RUN, CLEAR_LFM, score=72.89, stderr=1.37)
        a = compare.analyse(res)
        text = compare.report(a)
        # a card-sampling run far from the card fails the control even when the original passes
        write_run(res, compare.CONTROL_RUN, CLEAR_LFM, score=60.0, stderr=1.37)
        failed = compare.control(res)
    c = a["control"]
    assert (c["run"], c["status"]) == ("lfm3-1.7b-cardsampling", "passed")
    assert math.isclose(c["z"], (72.89 - 73.46) / 1.37)
    assert c["descriptive"]["run"] == "lfm3-1.7b" and math.isclose(c["descriptive"]["z"], (72.23 - 73.46) / 1.38)
    assert "status" not in c["descriptive"]
    assert "control: LFM3-1.7B (lfm3-1.7b-cardsampling) 72.89 ± 1.37 vs card 73.46, z = -0.42: passed" in text
    assert "descriptive, not tested: LFM3-1.7B (lfm3-1.7b, the run L1-L3 use) 72.23 ± 1.38 vs card 73.46, z = -0.89" \
        in text
    assert (failed["run"], failed["status"]) == ("lfm3-1.7b-cardsampling", "failed")
    assert compare.CONTROL_RUN == "lfm3-1.7b-cardsampling"


def test_hypotheses_on_both_lfm3_runs_and_reading():
    near_bielik = run_of({"easy": 11, "medium": 10, "hard": 10}, tokens=10000)  # +1 problem over Bielik: noise
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp)
        write_run(res, compare.LFM, CLEAR_LFM)
        write_run(res, compare.BIELIK, CLEAR_BIELIK)
        alone = compare.analyse(res)  # without the card-sampling run: the verdict run only
        write_run(res, compare.CONTROL_RUN, near_bielik)
        a = compare.analyse(res)
        text = compare.report(a)
        write_run(res, compare.CONTROL_RUN, CLEAR_LFM)
        same = compare.analyse(res)
    assert alone["other_run"] is None and [r["depends_on_sampling"] for r in alone["reading"]] == [None] * 3
    assert a["verdict_run"] == "lfm3-1.7b" and [h["outcome"] for h in a["hypotheses"]] == ["refuted"] * 3
    other = a["other_run"]
    assert other["run"] == "lfm3-1.7b-cardsampling"
    assert [h["outcome"] for h in other["hypotheses"]] == ["confirmed", "not established", "confirmed"]
    assert [h["p_holm"] for h in other["hypotheses"]] == compare.holm([h["p"] for h in other["hypotheses"]], m=3)
    l3 = by_id(a["reading"])["L3"]
    assert l3["depends_on_sampling"] and (l3["outcome"], l3["outcome_other_run"]) == ("refuted", "confirmed")
    # the verdict run's outcome never stands alone: both outcomes and "unresolved" in the same sentence
    assert "`refuted` on lfm3-1.7b, the verdict run" in l3["text"] and \
        "`confirmed` on lfm3-1.7b-cardsampling" in l3["text"] and "unresolved" in l3["text"]
    assert f"- {l3['text']}" in text and "L1-L3 on lfm3-1.7b-cardsampling, reported next to the verdict run" in text
    assert [(d["a"], d["b"]) for d in a["descriptive"]] == [("lfm3-1.7b", "bielik-11b-v3.1"),
                                                           ("lfm3-1.7b-cardsampling", "bielik-11b-v3.1")]
    assert [r["depends_on_sampling"] for r in same["reading"]] == [False] * 3
    assert by_id(same["reading"])["L3"]["text"].startswith("L3: refuted on both runs (lfm3-1.7b z = +")


def lcb_extract_code(text, style):
    """LiveCodeBench's extract_code for chat styles (extraction_utils.py @ LCB_COMMIT): the last two fence lines."""
    lines = text.split("\n")
    idx = [i for i, line in enumerate(lines) if "```" in line]
    return "" if len(idx) < 2 else "\n".join(lines[idx[-2] + 1: idx[-1]])


def test_extraction_rule_f1():
    import extraction
    assert extraction.f1("solve()\n```", "") == "solve()"  # closing fence only: the code before it
    assert extraction.f1("  \n```python\nsolve()", "") == "solve()"  # opening fence only: the code after it
    assert extraction.f1("solve()", "") == "solve()"  # no fence: the whole text
    assert extraction.f1("a\n```\nb\n```", "b") == "b"  # two or more fence lines: LiveCodeBench's code
    assert extraction.f1("```\na\n```\nb\n```", "b") == "b"
    assert [extraction.fence_lines(t) for t in ("x", "```py\nx\n```", "x\n```")] == [[], [0, 2], [1]]


# raw answers (after </think>), whether each official extraction passed, and the result rows built from them
F1_RAW = {
    "lfm3-1.7b": {"q1": "t</think>```python\nsolve()\n```", "q2": "t</think>no fence: nothing",
                  "q3": "```\nsolve()\n```"},
    "lfm3-1.7b-cardsampling": {"q1": "```\nsolve()\n```", "q2": "```\nsolve()\n```", "q3": "```\nsolve()\n```"},
    "bielik-11b-v3.1": {"q1": "solve()\n```", "q2": "```\nbroken", "q3": "x\n```python\nsolve()\n```"},
}


def write_f1_fixture(root):
    out, res = root / "out", root / "results"
    for run, answers in F1_RAW.items():
        raw = extraction_raw_name(run)
        (out / run).mkdir(parents=True)
        lines = "".join(json.dumps({"question_id": q, "status": "ok", "output": o}) + "\n" for q, o in answers.items())
        if raw.endswith(".gz"):
            with gzip.open(out / run / raw, "wt", encoding="utf-8") as f:
                f.write(lines)
        else:
            (out / run / raw).write_text(lines, encoding="utf-8")
        provenance.record(out / run, [raw], "test")
        codes = {q: lcb_extract_code(lcb.after_think(o), None) for q, o in answers.items()}
        write_run(res, run, [row(q, "solve" in c, "easy", output=c) for q, c in codes.items()])
    return out, res


def extraction_raw_name(run):
    import extraction
    return extraction.RAW.get(run, "generations.jsonl")


def f1_modules(calls):
    """fake_lcb with LiveCodeBench's extraction and an evaluator that passes code containing `solve`."""
    mods = fake_lcb(calls)

    def codegen_metrics(samples, generations, num_process_evaluate, timeout):
        calls.append({"num_process_evaluate": num_process_evaluate, "timeout": timeout, "generations": generations})
        results = {i: [[1, 1] if "solve" in g[0] else [1, -2]] for i, g in enumerate(generations)}
        return {}, results, [[json.dumps({"n": i})] for i in range(len(generations))]

    mods.evaluation.codegen_metrics = codegen_metrics
    mods.extraction.extract_code = lcb_extract_code
    return mods


def test_extraction_regrade_file_and_compare_exploratory_rows():
    import extraction
    rows = [{"question_id": q, "passes": None} for q in ("q1", "q2", "q3")]
    calls = []
    with tempfile.TemporaryDirectory() as tmp, patched(lcb, load_rows=lambda limit: [dict(r) for r in rows]):
        out, res = write_f1_fixture(Path(tmp))
        extraction.main(out, res, 3, modules=f1_modules(calls))
        x = json.loads((res / "extraction-f1.json").read_text(encoding="utf-8"))
        files = provenance.read_manifest(res)["files"]
        assert (files["extraction-f1.json"]["sha256"], files["extraction-f1.json"]["written_by"]) == \
            (sha256(res / "extraction-f1.json"), "extraction.py")
        a = compare.analyse(res)
        text = compare.report(a)
        # a result file whose code is not LiveCodeBench's extraction of the raw answer stops the run
        write_run(res, "bielik-11b-v3.1", [row("q1", False, "easy", output="other"), row("q2", False, "easy"),
                                           row("q3", True, "easy", output="solve()")])
        stopped = exit_message(extraction.main, out, res, 3, f1_modules([]))
        assert "is not the code in results/bielik-11b-v3.1.jsonl.gz" in stopped
        assert "another bielik-11b-v3.1.jsonl.gz" in exit_message(compare.analyse, res)  # stale exploratory file
    assert [(c["num_process_evaluate"], c["timeout"]) for c in calls] == [(3, lcb.EVAL_TIMEOUT)]
    assert calls[0]["generations"] == [["no fence: nothing"], ["solve()"], ["broken"]]  # only the changed answers
    b, lfm = x["runs"]["bielik-11b-v3.1"], x["runs"]["lfm3-1.7b"]
    assert (b["fence_lines"], b["empty_code"], b["changed"], b["passing_after_f1"]) == ({"1": 2, "2": 1}, 2, 2, 1)
    assert b["regraded"]["q1"]["pass"] and not b["regraded"]["q2"]["pass"]
    assert not b["regraded"]["q1"]["official_pass"]
    assert (lfm["fence_lines"], lfm["empty_code"], lfm["changed"], lfm["passing_after_f1"]) == \
        ({"0": 1, "2": 2}, 1, 1, 0)
    assert x["runs"]["lfm3-1.7b-cardsampling"]["changed"] == 0
    assert x["exploratory"].startswith("added after the results")
    assert x["runs"]["bielik-11b-v3.1"]["result"]["sha256"] == files["bielik-11b-v3.1.jsonl.gz"]["sha256"]
    assert {m: v["empty_code"] for m, v in a["extraction"].items()} == \
        {"lfm3-1.7b": 1, "lfm3-1.7b-cardsampling": 0, "bielik-11b-v3.1": 2}
    # official L1 on lfm3-1.7b: d = (1, 0, 0) over q1-q3; after F1 Bielik's q1 passes: d = (0, 0, 0)
    h = a["hypotheses"][0]
    assert math.isclose(h["value"], 100 / 3)
    ex = {r["run"]: r for r in a["exploratory_extraction"]["hypotheses"]}
    assert ex["lfm3-1.7b"]["L1"]["value"] == 0 and ex["lfm3-1.7b"]["L1"]["n"] == 3
    assert a["exploratory_extraction"]["sha256"] == files["extraction-f1.json"]["sha256"]
    assert "| bielik-11b-v3.1 | 3 | 2 | 2 | 1 | 0 |" in text and "| bielik-11b-v3.1 | 3 | 2 |" in text
    assert "Exploratory, added after the results" in text


# The committed results, checked without this benchmark's code: an independent count from results/*.jsonl.gz
# against results/*.json, results/hypotheses.json, compare.py on the same files, and the numbers in README.md.
RESULTS = BENCH / "results"
REAL_RUNS = ("lfm3-1.7b", "lfm3-1.7b-cardsampling", "bielik-11b-v3.1")
REAL_WEIGHTS = {"lfm3-1.7b": 1_728_801_536, "lfm3-1.7b-cardsampling": 1_728_801_536,
                "bielik-11b-v3.1": 11_168_796_672}  # safetensors tensor-shape sums (PROTOCOL.md revisions)


def real_rows(run):
    with gzip.open(RESULTS / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in (json.loads(line) for line in f)}


def mean_se(d):
    n = len(d)
    m = sum(d) / n
    return 100 * m, 100 * math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n)


def independent_counts():
    """pass@1 per run, and per LFM3-1.7B run the L1 and L3 differences against Bielik, paired by task_id."""
    rows = {run: real_rows(run) for run in REAL_RUNS}
    out = {"pass@1": {}, "L1": {}, "L3": {}, "L3_f1": {}, "L1_platform_se": {}}
    for run, rs in rows.items():
        ok = [r for r in rs.values() if r["status"] == "ok"]
        p = sum(bool(r["pass"]) for r in ok) / len(ok)
        out["pass@1"][run] = (round(100 * p, 2), round(100 * math.sqrt(p * (1 - p) / len(ok)), 2), len(ok))
    f1 = json.loads((RESULTS / "extraction-f1.json").read_text(encoding="utf-8"))["runs"]
    bielik = rows["bielik-11b-v3.1"]
    for run in ("lfm3-1.7b", "lfm3-1.7b-cardsampling"):
        lfm = rows[run]
        ids = sorted(t for t in lfm if t in bielik and lfm[t]["status"] == bielik[t]["status"] == "ok")
        d = [int(bool(lfm[t]["pass"])) - int(bool(bielik[t]["pass"])) for t in ids]
        out["L1"][run] = (*mean_se(d), len(ids))
        by_platform = {}
        for t, x in zip(ids, d):
            by_platform.setdefault(lfm[t]["platform"], []).append(x)
        mean, g = sum(d) / len(d), len(by_platform)
        out["L1_platform_se"][run] = 100 * math.sqrt(
            g / (g - 1) * sum(sum(x - mean for x in xs) ** 2 for xs in by_platform.values())) / len(d)

        def l3(pass_a, pass_b):
            """pass_a, pass_b: task_id -> passed, for LFM3-1.7B and Bielik."""
            def within(rs, passed, t, b):
                return passed[t] and rs[t]["finished"] and (b is None or rs[t]["output_tokens"] <= b)

            def mean_cost(m, rs, b):
                return sum(2 * REAL_WEIGHTS[m] * (r["output_tokens"] if b is None else min(r["output_tokens"], b))
                           for r in (rs[t] for t in ids)) / len(ids)
            budgets = (4096, 16384, None)
            pairs = [(abs(math.log(mean_cost(run, lfm, ba) / mean_cost("bielik-11b-v3.1", bielik, bb))), ba, bb)
                     for ba in budgets for bb in budgets]
            _, ba, bb = min(pairs, key=lambda x: x[0])  # min keeps the first of equal ratios
            d3 = [int(within(lfm, pass_a, t, ba)) - int(within(bielik, pass_b, t, bb)) for t in ids]
            return (*mean_se(d3), ba, bb)

        def passes(rs, m=None):  # official grades, or with extraction-f1.json's regrade of run m over them
            regraded = {t: g["pass"] for t, g in f1[m]["regraded"].items()} if m else {}
            return {t: regraded.get(t, bool(r["pass"])) for t, r in rs.items()}

        out["L3"][run] = l3(passes(lfm), passes(bielik))
        out["L3_f1"][run] = l3(passes(lfm, run), passes(bielik, "bielik-11b-v3.1"))
    return out


def test_results_and_hypotheses_match_an_independent_count():
    c = independent_counts()
    for run, (score, stderr, n) in c["pass@1"].items():
        r = json.loads((RESULTS / f"{run}.json").read_text(encoding="utf-8"))
        assert (r["score"], r["stderr"], r["n"]) == (score, stderr, n), run
    h = json.loads((RESULTS / "hypotheses.json").read_text(encoding="utf-8"))
    families = {h["verdict_run"]: h["hypotheses"], h["other_run"]["run"]: h["other_run"]["hypotheses"]}
    assert h["verdict_run"] == "lfm3-1.7b"
    for run, rows in families.items():
        l1, l3 = by_id(rows)["L1"], by_id(rows)["L3"]
        value, se, n = c["L1"][run]
        assert math.isclose(l1["value"], value) and math.isclose(l1["se"], se) and l1["n"] == n, run
        value, se, ba, bb = c["L3"][run]
        assert math.isclose(l3["value"], value) and math.isclose(l3["se"], se), run
        assert (l3["budget_a"], l3["budget_b"]) == (ba, bb), run
        assert math.isclose(l1["clustered"]["platform"]["se"], c["L1_platform_se"][run]), run
    ex = {r["run"]: r for r in h["exploratory_extraction"]["hypotheses"]}
    for run, (value, se, ba, bb) in c["L3_f1"].items():
        assert math.isclose(ex[run]["L3"]["value"], value) and math.isclose(ex[run]["L3"]["se"], se), run


def test_compare_on_the_committed_results_matches_the_independent_count():
    # catches a pairing error in compare.py (e.g. Bielik's answers shifted by one problem) without regenerating
    c = independent_counts()
    a = compare.analyse(RESULTS)
    for run, rows in ((a["verdict_run"], a["hypotheses"]), (a["other_run"]["run"], a["other_run"]["hypotheses"])):
        value, se, _ = c["L1"][run]
        assert math.isclose(by_id(rows)["L1"]["value"], value) and math.isclose(by_id(rows)["L1"]["se"], se), run
        value, se, _, _ = c["L3"][run]
        assert math.isclose(by_id(rows)["L3"]["value"], value) and math.isclose(by_id(rows)["L3"]["se"], se), run


def readme_cells(text, starts):
    """Cells of the first README table line that starts with `starts`."""
    line = next(line for line in text.splitlines() if line.startswith(starts))
    return [c.strip() for c in line.strip().strip("|").split("|")]


def test_readme_numbers_match_the_independent_count():
    text = (BENCH / "README.md").read_text(encoding="utf-8")
    c = independent_counts()
    names = {"lfm3-1.7b": "| LFM3-1.7B (`lfm3-1.7b`", "lfm3-1.7b-cardsampling": "| LFM3-1.7B with the card's sampling",
             "bielik-11b-v3.1": "| Bielik 11B v3.1 (`bielik-11b-v3.1`)"}
    for run, (score, stderr, n) in c["pass@1"].items():
        assert readme_cells(text, names[run])[4:7] == [f"{score:.2f}", f"{stderr:.2f}", str(n)], run
    for run in ("lfm3-1.7b", "lfm3-1.7b-cardsampling"):
        section = text[text.index(f"L1-L3 on {run}, "):]
        for hid, (value, se) in (("L1", c["L1"][run][:2]), ("L3", c["L3"][run][:2])):
            assert readme_cells(section, f"| {hid} |")[2] == f"{value:+.2f} ± {se:.2f}", (run, hid)
        value, se, _, _ = c["L3_f1"][run]
        assert readme_cells(text, f"| L3 | {run} |")[5] == f"{value:+.2f} ± {se:.2f}", run


def test_readme_blocks_are_the_generator_output():
    import readme
    text = (BENCH / "README.md").read_text(encoding="utf-8")
    bodies = readme.blocks(RESULTS)
    assert readme.render(text, bodies) == text  # byte for byte: no number edited by hand, none stale
    row_line = next(line for line in text.splitlines() if line.startswith("| Bielik 11B v3.1 (`bielik-11b-v3.1`)"))
    score = readme_cells(text, "| Bielik 11B v3.1 (`bielik-11b-v3.1`)")[4]
    swapped = text.replace(row_line, row_line.replace(f"| {score} |", f"| {score[::-1]} |", 1))
    assert swapped != text and readme.render(swapped, bodies) != swapped  # one swapped number is caught
    broken = text.replace("<!-- readme.py: end hypotheses -->", "")
    assert "needs exactly one" in exit_message(readme.render, broken, bodies)


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
