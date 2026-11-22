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
    provenance.record(results, [f"{model}.jsonl.gz", f"{model}.json"], "test")  # as summarize.py does


def run_of(passes_per_level, tokens, n_per_level=30, prefix="p"):
    """passes_per_level: how many of the first problems of each level pass; every 5th problem is v6-only."""
    return [row(f"{prefix}{lvl}{i:02d}", i < passes_per_level[lvl], lvl, tokens=tokens, v6_only=i % 5 == 0)
            for lvl in LEVELS for i in range(n_per_level)]


def by_id(rows):
    return {r["id"]: r for r in rows}


CLEAR_LFM = run_of({"easy": 30, "medium": 30, "hard": 30}, tokens=10000)
CLEAR_BIELIK = run_of({"easy": 10, "medium": 10, "hard": 10}, tokens=2000)


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
    """Answers chat completions; the first `fail` requests get 503, and a request with max_tokens 1 gets 400."""

    def __init__(self, fail=0, reasoning=False):
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
                    return self.reply(503, {"error": "busy"})
                message = {"role": "assistant", "content": "```python\nprint(1)\n```"}
                if reasoning:
                    message["reasoning_content"] = "hmm"
                self.reply(200, {"choices": [{"message": message, "finish_reason": "stop"}],
                                 "usage": {"prompt_tokens": 1071, "completion_tokens": 9}})

            def do_GET(self):  # vLLM's /version and /v1/models, recorded for a reused server
                if self.path == "/version":
                    return self.reply(200, {"version": "0.34.0"})
                self.reply(200, {"object": "list", "data": [{"id": "lfm3-1.7b", "root": "LiquidAI/LFM3-1.7B"}]})

            def reply(self, code, payload):
                data = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
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
    api = FakeAPI()
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

        lcb.score(argparse.Namespace(out_dir=str(out), limit=None))
        assert [(c["timeout"], c["num_process_evaluate"]) for c in calls] == [(6, 12)]
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
