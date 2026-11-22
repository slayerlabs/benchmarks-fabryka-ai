"""LiveCodeBench Pro 25Q2 (api-benchmarks/livecodebench-pro-25q2): prompt, extraction, requests, judging, summary
and the K1-K3 analysis, without GPU, Docker, network or the gated data.

- Prompt and extraction run the pinned harness clone in the benchmark's `.cache/` (run.sh makes it; skipped
  without it): the message is the harness's `LLMInterface.prompt` (read from api_interface.py here with `ast`,
  independently of lcbpro.py) plus the statement, and code is extracted from the text after the last `</think>`.
- Requests go to a fake OpenAI-compatible server on 127.0.0.1: the Fabryka API body and max_tokens = context - local
  count - margin, retries and the event log; the vLLM body with the card sampling, the no-thinking switch and
  max_tokens = context - /tokenize count; resume and the one retry of failed requests.
- Judging uses a fake of the harness's judge: verdict categories, compile errors apart from judge errors, one retry
  of judge errors, missing tests, and the pinned-tests guard.
- summarize.py and compare.py on hand-made records: headline and secondary score, per difficulty, categories,
  K1, K2 (SE floor), K3 (paired, precondition), Holm over the group of four with another benchmark's file.
Run (from the repo root; the prompt test imports the harness, which needs openai):
    uv run --no-project --python 3.12 --with pytest --with huggingface_hub==0.35.0 --with openai==1.108.1 \
        --with certifi python -m pytest research/tests/test_livecodebench_pro_25q2.py
"""
import argparse
import ast
import contextlib
import gzip
import http.server
import json
import math
import os
import statistics
import sys
import tempfile
import threading
import types
from pathlib import Path

import pytest

BENCH = Path(os.environ.get("LCBPRO_BENCH", Path(__file__).resolve().parents[1] / "api-benchmarks" /
                            "livecodebench-pro-25q2"))
HARNESS = Path(__file__).resolve().parents[1] / "api-benchmarks" / "livecodebench-pro-25q2" / ".cache" / \
    "LiveCodeBench-Pro"
os.environ.setdefault("LCBPRO_DIR", str(HARNESS))
for name in ("provenance", "lcbpro", "summarize", "compare"):  # other benchmarks have modules with these names
    sys.modules.pop(name, None)
sys.path.insert(0, str(BENCH))
import compare  # noqa: E402
import lcbpro  # noqa: E402
import provenance  # noqa: E402
import summarize  # noqa: E402

sys.path.remove(str(BENCH))


def need_harness():
    if not (HARNESS / ".git").exists():
        pytest.skip(f"no harness clone in {HARNESS} (bash run.sh creates it)")


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


@contextlib.contextmanager
def kept_cwd():
    cwd = os.getcwd()
    try:
        yield
    finally:
        os.chdir(cwd)


@contextlib.contextmanager
def injected_modules(**modules):
    """Puts fake modules in sys.modules for the imports inside a call, then restores what was there."""
    old = {k: sys.modules.get(k) for k in modules}
    sys.modules.update(modules)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


def fast_server_from(args, original=lcbpro.server_from):
    server = original(args)
    server.gate = lcbpro.Gate(0.01, 0.02)
    return server


def exit_message(fn, *args):
    with pytest.raises(SystemExit) as e:
        fn(*args)
    return str(e.value.code)


# --- prompt and extraction with the pinned harness -------------------------------------------------------------

def harness_prompt_literal():
    """LLMInterface.__init__'s `self.prompt` string, parsed from the pinned api_interface.py."""
    tree = ast.parse((HARNESS / "api_interface.py").read_text(encoding="utf-8"))
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "LLMInterface")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    assign = next(n for n in init.body if isinstance(n, ast.Assign))
    assert ast.unparse(assign.targets[0]) == "self.prompt"
    return assign.value.value


def test_prompt_is_the_harness_string_plus_statement():
    need_harness()
    with kept_cwd():
        prompt = lcbpro.harness_prompt()
    literal = harness_prompt_literal()
    statement = "Given n, print n.\n\nInput\n1 <= n <= 10\n"
    assert prompt(statement) == literal + statement
    assert literal.startswith("\n        You are a competitive programmer.") and literal.endswith("\n        ")
    assert "```cpp" in literal


THINKING = ("Let me draft.\n```cpp\n#include <cstdio>\nint main(){puts(\"draft\");}\n```\nNo.</think>\n"
            "Final answer:\n```cpp\n#include <cstdio>\nint main(){puts(\"final\");}\n```\n")


def answer_record(output, finish_reason="stop", status="ok"):
    return {"status": status, "output": output, "finish_reason": finish_reason}


def test_extraction_reads_the_text_after_the_last_think():
    need_harness()
    with kept_cwd():
        extract = lcbpro.harness_extract()
    category, code = lcbpro.prejudge(answer_record(THINKING), "on", extract)
    assert category is None and code == "#include <cstdio>\nint main(){puts(\"final\");}"
    assert lcbpro.after_think("a</think>b</think>c") == "c"
    assert lcbpro.after_think("no think") == "no think"
    # no fenced block after </think>: the harness falls back to the last int main( with its #include lines
    fallback = "```cpp\n#include <a>\nint main(){1;}\n```</think>\n#include <b>\nint main(){ return 0; }\n"
    assert lcbpro.prejudge(answer_record(fallback), "on", extract) == \
        (None, "#include <b>\nint main(){ return 0; }")
    assert lcbpro.prejudge(answer_record("</think>Sorry, no code."), "on", extract) == ("no_code", None)


def test_unfinished_and_unscored_answers_never_reach_the_judge():
    def extract(text):
        return "CODE:" + text

    assert lcbpro.prejudge(answer_record(None, status="error"), "on", extract) == ("request_error", None)
    assert lcbpro.prejudge(answer_record(None, status="unsupported"), "none", extract) == ("unsupported", None)
    # thinking on: no </think>, or not stopped by `stop`
    assert lcbpro.prejudge(answer_record("```cpp\nx\n```"), "on", extract) == ("unfinished", None)
    assert lcbpro.prejudge(answer_record("a</think>b", "length"), "on", extract) == ("unfinished", None)
    assert lcbpro.prejudge(answer_record("a</think>b", "stop"), "on", extract) == (None, "CODE:b")
    # thinking off or no switch: no </think> needed, the whole output is extracted
    assert lcbpro.prejudge(answer_record("b"), "off", extract) == (None, "CODE:b")
    assert lcbpro.prejudge(answer_record("b", "length"), "none", extract) == (None, "CODE:b")


# --- judge categories, retries and pinned tests ----------------------------------------------------------------

def test_judge_verdict_categories():
    assert lcbpro.judged("Accepted", {"cases": [{"time": 5}, {"time": 9}]}) == \
        {"verdict": "Accepted", "accepted": True, "category": "accepted", "cases_run": 2, "max_time_ns": 9}
    wa = lcbpro.judged("Wrong Answer", {"cases": [{"time": 1, "msg": "wrong answer 1st"}]})
    assert (wa["category"], wa["accepted"], wa["judge_message"]) == ("wrong_answer", False, "wrong answer 1st")
    for verdict, category in (("Time Limit Exceeded", "time_limit"), ("Memory Limit Exceeded", "memory_limit"),
                              ("Nonzero Exit Status", "runtime_error"), ("Signalled", "runtime_error"),
                              ("Output Limit Exceeded", "output_limit"), ("Internal Error", "judge_error"),
                              ("File Error", "judge_error")):
        assert lcbpro.judged(verdict, {"cases": [{}]})["category"] == category
    ce = lcbpro.judged("Judge Failed", {"status": "error", "error": "Error: compile failed: main.cpp:1: error"})
    assert (ce["category"], ce["accepted"]) == ("compile_error", False)
    for error in ("Error: checker compile failed: x", "Error: interactor compile failed: x",
                  "TypeError: Cannot read properties of undefined (reading 'ok')"):
        assert lcbpro.judged("Judge Failed", {"status": "error", "error": error})["category"] == "judge_error"
    assert lcbpro.judged("Judge Failed", None)["category"] == "judge_error"


class NotFound(Exception):
    pass


class FakeJudge:
    """The harness judge's submit/get_result: `script[pid]` is the list of verdicts of successive submissions;
    a verdict "missing" raises the not-found error, "crash" any other exception at submit."""

    def __init__(self, script):
        self.script = {k: list(v) for k, v in script.items()}
        self.submitted, self.verdicts, self.full = [], {}, {}

    def submit(self, pid, lang, code):
        verdict = self.script[pid].pop(0)
        if verdict == "missing":
            raise NotFound(pid)
        if verdict == "crash":
            raise RuntimeError("container gone")
        sid = len(self.submitted) + 1
        self.submitted.append((pid, lang, code))
        error = verdict.partition(":")[2] if verdict.startswith("Judge Failed:") else None
        self.verdicts[sid] = ["Judging", "Judge Failed" if error is not None else verdict]
        self.full[sid] = {"status": "error", "error": error} if error is not None else {"status": "done", "cases": [{}]}
        return sid

    def get_result(self, sid):
        return self.verdicts[sid].pop(0) if len(self.verdicts[sid]) > 1 else self.verdicts[sid][0]


def test_judge_errors_are_retried_once_compile_errors_not():
    judge = FakeJudge({
        "A": ["Accepted"],
        "B": ["Judge Failed:Error: compile failed: x"],
        "C": ["Judge Failed:Error: checker compile failed", "Accepted"],
        "D": ["Internal Error", "Internal Error"],
        "E": ["missing"],
        "F": ["crash", "Wrong Answer"],
    })
    todo = {p: f"code {p}" for p in "ABCDEF"}
    r = lcbpro.judge_all(judge, "CPP", NotFound, todo, lambda sid: judge.full[sid], poll=0)
    assert {p: (r[p]["category"], r[p]["judge_attempts"]) for p in r} == {
        "A": ("accepted", 1), "B": ("compile_error", 1), "C": ("accepted", 2), "D": ("judge_error", 2),
        "E": ("no_tests", 1), "F": ("wrong_answer", 2)}
    assert r["A"]["accepted"] and not r["D"]["accepted"]
    assert all(lang == "CPP" and code == f"code {pid}" for pid, lang, code in judge.submitted)


def test_scoring_refuses_unpinned_tests():
    from huggingface_hub import constants
    with tempfile.TemporaryDirectory() as tmp, patched(constants, HF_HUB_CACHE=tmp, HF_HUB_OFFLINE=False):
        record = {"revision": lcbpro.TESTS_REVISION}
        assert "HF_HUB_OFFLINE" in exit_message(lcbpro.check_pinned_tests, record)
        constants.HF_HUB_OFFLINE = True
        assert "does not point" in exit_message(lcbpro.check_pinned_tests, record)
        ref = lcbpro.tests_cache_dir() / "refs" / "main"
        ref.parent.mkdir(parents=True)
        ref.write_text("0" * 40, encoding="utf-8")
        assert "does not point" in exit_message(lcbpro.check_pinned_tests, record)
        ref.write_text(lcbpro.TESTS_REVISION, encoding="utf-8")
        lcbpro.check_pinned_tests(record)
        assert "tests.json" in exit_message(lcbpro.check_pinned_tests, {"revision": "main"})


def test_tests_step_downloads_at_the_pin_and_points_main_there():
    import huggingface_hub
    calls = []

    class Api:
        def list_repo_files(self, repo, repo_type, revision):
            calls.append(("list", repo, repo_type, revision))
            return ["A.zip", "README.md"]

    with tempfile.TemporaryDirectory() as tmp:
        zip_path = Path(tmp) / "A.zip"
        zip_path.write_bytes(b"zip")

        def download(repo, name, repo_type, revision):
            calls.append(("get", repo, name, repo_type, revision))
            return str(zip_path)

        out = Path(tmp) / "out"
        out.mkdir()
        (out / "problems.json").write_text(json.dumps({"problems": [{"problem_id": "A"}, {"problem_id": "B"}]}))
        provenance.record(out, ["problems.json"], "test")
        with patched(huggingface_hub, HfApi=Api, hf_hub_download=download), \
                patched(huggingface_hub.constants, HF_HUB_CACHE=tmp):
            lcbpro.tests(argparse.Namespace(out_dir=str(out), limit=None))
            ref = lcbpro.tests_cache_dir() / "refs" / "main"
        assert ref.read_text() == lcbpro.TESTS_REVISION
        rev = lcbpro.TESTS_REVISION
        assert calls == [("list", lcbpro.TESTS_REPO, "dataset", rev), ("get", lcbpro.TESTS_REPO, "A.zip", "dataset", rev)]
        record = json.loads((out / "tests.json").read_text())
        assert record["missing"] == ["B"] and record["files"]["B"] is None
        assert record["files"]["A"]["sha256"] == provenance.sha256_file(zip_path)


# --- requests against a fake server ----------------------------------------------------------------------------

class FakeAPI:
    """Chat completions on 127.0.0.1; the first `fail` requests get 503; max_tokens 1 -> 400, 2 -> 401;
    `fail_ids` lists user messages answered with 503 every time. /tokenize answers count 1000."""

    def __init__(self, fail=0, content="</think>```cpp\n#include <x>\nint main(){}\n```", fail_ids=()):
        self.requests, self.headers, self.tokenize_requests = [], [], []
        api = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path.endswith("/tokenize"):
                    api.tokenize_requests.append(body)
                    return self.reply(200, {"count": 1000, "max_model_len": 262144})
                api.requests.append(body)
                api.headers.append(dict(self.headers))
                if body["max_tokens"] == 1:
                    return self.reply(400, {"error": "unsupported field"})
                if body["max_tokens"] == 2:
                    return self.reply(401, {"error": {"code": "invalid_api_key"}})
                if len(api.requests) <= fail or body["messages"][-1]["content"] in fail_ids:
                    return self.reply(503, {"error": "busy"})
                self.reply(200, {"choices": [{"message": {"role": "assistant", "content": content},
                                              "finish_reason": "stop"}],
                                 "usage": {"prompt_tokens": 1071, "completion_tokens": 9}})

            def do_GET(self):
                if self.path == "/version":
                    return self.reply(200, {"version": "0.34.0"})
                self.reply(200, {"object": "list", "data": [{"id": "lfm3-1.7b"}]})

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
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.url = f"{self.base}/v1/chat/completions"

    def close(self):
        self.server.shutdown()


MESSAGES = [{"role": "user", "content": "q"}]


def api_server(url, count=1000, retries=30, events=None):
    return lcbpro.Server(model="bielik-11b-v3.1", chat_url=url, retries=retries, timeout=10,
                         headers={"Authorization": "Bearer test"}, count=lambda m: count, context=32768, margin=64,
                         gate=lcbpro.Gate(0.01, 0.04), **({"events": events} if events else {}))


def test_api_body_margin_and_local_count():
    api = FakeAPI()
    try:
        record = lcbpro.answer(api_server(api.url), MESSAGES)
    finally:
        api.close()
    body = api.requests[0]
    assert sorted(body) == ["max_tokens", "messages", "model", "seed", "temperature", "top_p"]
    assert (body["temperature"], body["top_p"], body["seed"]) == (0.6, 0.95, 20261122)
    assert body["max_tokens"] == 32768 - 1000 - 64
    assert api.headers[0]["Authorization"] == "Bearer test"
    assert (record["status"], record["prompt_tokens"], record["max_tokens"], record["output_tokens"],
            record["api_prompt_tokens"], record["finish_reason"]) == ("ok", 1000, 32768 - 1064, 9, 1071, "stop")


def test_api_retries_rejections_and_event_log():
    with tempfile.TemporaryDirectory() as tmp:
        events = lcbpro.EventLog(Path(tmp) / "api-events.jsonl")
        api = FakeAPI(fail=2)
        try:
            server = api_server(api.url, events=events)
            assert lcbpro.answer(server, MESSAGES, "P1")["status"] == "ok" and len(api.requests) == 3
            assert server.gate.pause == server.gate.pause_min
            api.requests.clear()
            with pytest.raises(lcbpro.Rejected):  # a 400 is not retried
                lcbpro.answer(api_server(api.url, count=32768 - 64 - 1, events=events), MESSAGES, "P2")
            assert len(api.requests) == 1
            too_long = lcbpro.answer(api_server(api.url, count=32768 - 64, events=events), MESSAGES, "P3")
            assert too_long["status"] == "unsupported" and len(api.requests) == 1  # never sent
            with pytest.raises(lcbpro.SetupError):  # a wrong key stops the run
                lcbpro.answer(api_server(api.url, count=32768 - 64 - 2, events=events), MESSAGES, "P4")
        finally:
            api.close()
        lines = [json.loads(x) for x in (Path(tmp) / "api-events.jsonl").read_text().splitlines()]
        assert [(e["problem"], e["status"], e["action"]) for e in lines] == [
            ("P1", 503, "retry"), ("P1", 503, "retry"), ("P1", None, "recovered"), ("P2", 400, "rejected"),
            ("P4", 401, "stop")]
        assert lcbpro.event_counts(lines)["by_action"] == {"recovered": 1, "rejected": 1, "retry": 2, "stop": 1}


def vllm_server(api, kwargs=None):
    return lcbpro.Server(model="lfm3-1.7b", chat_url=api.url, retries=3, timeout=10,
                         tokenize_url=f"{api.base}/tokenize", template_kwargs=kwargs, context=262144,
                         model_repo="LiquidAI/LFM3-1.7B@1da06bec6a819da10b54c67e5c90972b46d81871")


VLLM_FIELDS = {"model": "lfm3-1.7b", "n": 1, "temperature": 0.6, "top_p": 0.95, "seed": 20261122, "top_k": 0,
               "repetition_penalty": 1.0, "frequency_penalty": 0, "presence_penalty": 0, "max_tokens": 262144 - 1000}


def test_vllm_body_card_sampling_and_thinking_switch():
    api = FakeAPI()
    try:
        on = vllm_server(api)
        off = vllm_server(api, {"enable_thinking": False})
        lcbpro.answer(on, MESSAGES)
        lcbpro.answer(off, MESSAGES)
    finally:
        api.close()
    assert {k: v for k, v in api.requests[0].items() if k != "messages"} == VLLM_FIELDS
    assert {k: v for k, v in api.requests[1].items() if k != "messages"} == \
        {**VLLM_FIELDS, "chat_template_kwargs": {"enable_thinking": False}}
    assert "chat_template_kwargs" not in api.tokenize_requests[0]
    assert api.tokenize_requests[1]["chat_template_kwargs"] == {"enable_thinking": False}
    assert (lcbpro.thinking(on), lcbpro.thinking(off), lcbpro.thinking(api_server("x"))) == ("on", "off", "none")
    config = {"repetition_penalty": 1.1, "top_k": 50, "temperature": 0.1}
    with patched(lcbpro, generation_config=lambda repo: config):
        s = lcbpro.sampling(on)
    # every field vLLM would take from generation_config.json is sent, so nothing is filled from it
    assert s["server_defaults"] == {} and s["effective"]["top_k"] == 0 and s["effective"]["repetition_penalty"] == 1.0
    assert s["thinking"] == "on"


ROWS = [{"problem_id": p, "problem_title": p, "difficulty": d, "platform": "codeforces", "link": "",
         "time_limit": 1000, "memory_limit": 256, "problem_statement": f"S{p}"}
        for p, d in (("A", "easy"), ("B", "medium"), ("C", "hard"))]


def vllm_args(api, out, limit=None):
    return argparse.Namespace(out_dir=str(out), base_url=api.base, chat_url="", model="lfm3-1.7b",
                              model_repo="LiquidAI/LFM3-1.7B@x", limit=limit, chat_template_kwargs="",
                              api_key_env="", tokenizer="", context=262144, margin=0, retries=1, concurrency=2,
                              request_timeout=10)


def test_generate_resumes_and_retries_failed_requests_once():
    api = FakeAPI(fail_ids=("PROMPT SB",))
    with tempfile.TemporaryDirectory() as tmp, \
            patched(lcbpro, harness_prompt=lambda: (lambda s: "PROMPT " + s), load_rows=lambda: [dict(r) for r in ROWS],
                    generation_config=lambda repo: {}, server_from=fast_server_from):
        out = Path(tmp) / "out"
        try:
            lcbpro.generate(vllm_args(api, out, limit=2))
            first = [b["messages"][0]["content"] for b in api.requests]
            # A once; B fails (1 attempt each) and is tried once more at the end of the session
            assert sorted(first) == ["PROMPT SA", "PROMPT SB", "PROMPT SB"]
            assert api.requests[0]["messages"] == [{"role": "user", "content": first[0]}]
            gen = lcbpro.read_jsonl(out / "generations.jsonl")
            assert [(g["problem_id"], g["status"]) for g in gen if g["problem_id"] == "B"] == \
                [("B", "error"), ("B", "error")]
            api.requests.clear()
            lcbpro.generate(vllm_args(api, out))  # resume: A kept, B (error) and C asked again
            assert sorted(b["messages"][0]["content"] for b in api.requests) == ["PROMPT SB", "PROMPT SB", "PROMPT SC"]
        finally:
            api.close()
        problems = json.loads((out / "problems.json").read_text())
        assert [p["problem_id"] for p in problems["problems"]] == ["A", "B", "C"]
        assert "problem_statement" not in problems["problems"][0]
        run = json.loads((out / "run.json").read_text())
        assert [g["limit"] for g in run["generation"]] == [2, None]
        assert run["generation"][0]["sampling"]["thinking"] == "on"


# --- score end to end with a fake judge, then summarize -----------------------------------------------------------

def write_generation(out, answers, thinking="on"):
    out.mkdir(parents=True)
    (out / "problems.json").write_text(json.dumps({"problems": [{k: r[k] for k in lcbpro.PROBLEM_FIELDS}
                                                                for r in ROWS]}))
    with (out / "generations.jsonl").open("w") as f:
        for pid, a in answers.items():
            f.write(json.dumps({"problem_id": pid, "prompt_tokens": 10, "context": 100, "max_tokens": 90,
                                "output_tokens": 50, "started": "2026-11-23T10:00:00+00:00", **a}) + "\n")
    (out / "api-events.jsonl").write_text("")
    (out / "tests.json").write_text(json.dumps({"repo": lcbpro.TESTS_REPO, "revision": lcbpro.TESTS_REVISION,
                                                "files": {"A": {"sha256": "aa", "bytes": 1},
                                                          "B": {"sha256": "bb", "bytes": 1}, "C": None},
                                                "missing": ["C"]}))
    (out / "run.json").write_text(json.dumps({"generation": [{"sampling": {"thinking": thinking}}]}))
    provenance.record(out, ["problems.json", "generations.jsonl", "api-events.jsonl", "tests.json"], "test")


def test_score_and_summary_end_to_end():
    judge = FakeJudge({"A": ["Accepted"], "B": ["Judge Failed:Error: compile failed: x"]})

    class Judge:
        PROBLEMS_DIR = "/nonexistent"
        IMAGE_NAME = "lightcpverifier"

        def __init__(self, worker):
            assert worker == lcbpro.JUDGE_WORKERS == 8
            self.base_url = "http://judge"

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        submit, get_result = judge.submit, judge.get_result

    fake_judge = types.SimpleNamespace(LightCPVerifierJudge=Judge, ProblemNotFoundError=NotFound,
                                       SupportedLanguage=types.SimpleNamespace(CPP="cpp"))
    fake_requests = types.SimpleNamespace(get=lambda url, timeout: types.SimpleNamespace(
        status_code=200, json=lambda: judge.full[int(url.rsplit("/", 1)[1])]))
    ok = "</think>```cpp\n#include <x>\nint main(){}\n```"
    with tempfile.TemporaryDirectory() as tmp, \
            patched(lcbpro, harness_extract=lambda: (lambda t: t.split("```cpp\n")[1].split("\n```")[0]
                                                      if "```cpp" in t else None),
                    check_pinned_tests=lambda r: None, fresh_problems_dir=lambda p: None,
                    judge_environment=lambda j: {"image_id": "sha256:abc", "workers": 8}), \
            injected_modules(judge=fake_judge, requests=fake_requests):
        out = Path(tmp) / "out"
        write_generation(out, {"A": {"status": "ok", "output": ok, "finish_reason": "stop"},
                               "B": {"status": "ok", "output": "<think>x" + ok, "finish_reason": "stop"},
                               "C": {"status": "ok", "output": ok, "finish_reason": "stop"}})
        lcbpro.score(argparse.Namespace(out_dir=str(out), limit=None))
        graded = lcbpro.read_jsonl(out / "graded.jsonl")
        assert [(g["problem_id"], g["category"], g["accepted"], g["has_tests"], g["think_in_output"])
                for g in graded] == [("A", "accepted", True, True, False), ("B", "compile_error", False, True, True),
                                     ("C", "no_tests", False, False, False)]
        assert [s[0] for s in judge.submitted] == ["A", "B"]  # C has no test zip: never submitted
        run = json.loads((out / "run.json").read_text())
        assert run["scoring"]["judge"]["image_id"] == "sha256:abc"
        with patched(lcbpro, N_PROBLEMS=3), patched(summarize, N_PROBLEMS=3):
            summarize.main(str(out), str(Path(tmp) / "results" / "lfm3-1.7b"), None)
        result = json.loads((Path(tmp) / "results" / "lfm3-1.7b.json").read_text())
        assert (result["score"], result["n"]) == (round(100 / 3, 2), 3)
        assert result["other_metrics"]["secondary"]["score"] == 50.0
        assert result["settings"]["judge"]["image_id"] == "sha256:abc" and result["settings"]["judge_workers"] == 8
        with gzip.open(Path(tmp) / "results" / "lfm3-1.7b.jsonl.gz", "rt") as f:
            rows = [json.loads(x) for x in f]
        assert [(r["task_id"], r["score"]) for r in rows] == [("A", 1), ("B", 0), ("C", 0)]
        # every step refuses an input changed after it was written
        (out / "graded.jsonl").write_text((out / "graded.jsonl").read_text().replace('"accepted": false', '"accepted": true', 1))
        assert "sha256" in exit_message(summarize.main, str(out), str(Path(tmp) / "results" / "x"), None)
        with (out / "generations.jsonl").open("a") as f:
            f.write(json.dumps({"problem_id": "B", "status": "ok", "output": ok, "finish_reason": "stop"}) + "\n")
        assert "sha256" in exit_message(lcbpro.score, argparse.Namespace(out_dir=str(out), limit=None))


# --- summarize.py on hand-made records ------------------------------------------------------------------------

def rec(pid, category, difficulty="easy", status="ok", tokens=100, finish="stop", think=False, has_tests=True):
    return {"problem_id": pid, "category": category, "accepted": category == "accepted", "difficulty": difficulty,
            "status": status, "output_tokens": tokens if status == "ok" else None, "finish_reason": finish,
            "unfinished": category == "unfinished", "think_in_output": think, "has_tests": has_tests,
            "prompt_tokens": 10, "context": 100, "max_tokens": 90}


RECORDS = [
    rec("a", "accepted", "easy", tokens=10),
    rec("b", "accepted", "medium", tokens=30),
    rec("c", "wrong_answer", "easy", tokens=20, think=True),
    rec("d", "compile_error", "hard", tokens=40),
    rec("e", "no_tests", "medium", tokens=50, has_tests=False),
    rec("f", "judge_error", "easy", tokens=60),
    rec("g", "request_error", "hard", status="error"),
    rec("h", "unfinished", "easy", tokens=90, finish="length"),
]


def test_headline_secondary_and_breakdowns():
    m = summarize.metrics(RECORDS)
    assert (m["score"], m["n"], m["accepted"]) == (25.0, 8, 2)  # 2 of all 8: errors and missing tests count as 0
    assert m["stderr"] == round(100 * math.sqrt(0.25 * 0.75 / 8), 2) == 15.31
    sec = m["secondary"]
    assert (sec["score"], sec["n"]) == (40.0, 5)  # without e, f, g
    assert sec["left_out"] == {"no_tests": 1, "judge_error": 1, "request_error": 1, "unsupported": 0}
    assert m["per_difficulty"] == {"easy": {"score": 25.0, "stderr": 21.65, "n": 4, "accepted": 1},
                                   "hard": {"score": 0.0, "stderr": 0.0, "n": 2, "accepted": 0},
                                   "medium": {"score": 50.0, "stderr": 35.36, "n": 2, "accepted": 1}}
    assert m["categories"]["accepted"] == 2 and m["categories"]["compile_error"] == 1
    assert sum(m["categories"].values()) == 8
    assert (m["unfinished"], m["length_stops"]) == (1, 1)
    assert m["think_in_output"] == {"answers": 1, "of": 7, "share": round(1 / 7, 4)}
    assert m["output_tokens"] == {"mean": round(300 / 7, 1), "median": 40, "max": 90}  # the 7 answered
    assert m["no_tests"] == ["e"]
    with pytest.raises(ValueError):
        summarize.metrics([rec("z", "Accepted")])


def test_not_run_is_null_with_reason():
    with tempfile.TemporaryDirectory() as tmp:
        summarize.not_run(str(Path(tmp) / "slayer1b-1.09-k70000"), "base model")
        r = json.loads((Path(tmp) / "slayer1b-1.09-k70000.json").read_text())
        assert (r["score"], r["stderr"], r["n"], r["reason"]) == (None, None, 0, "base model")


# --- compare.py: K1, K2, K3 and Holm ---------------------------------------------------------------------------

def write_results(res, runs):
    res.mkdir(parents=True, exist_ok=True)
    for model, accepted in runs.items():
        with gzip.open(res / f"{model}.jsonl.gz", "wt") as f:
            for i, a in enumerate(accepted):
                f.write(json.dumps({"task_id": f"{2000 + i // 7}{'ABCDEFG'[i % 7]}", "accepted": bool(a),
                                    "difficulty": ("easy", "medium", "hard")[i % 3]}) + "\n")
        provenance.record(res, [f"{model}.jsonl.gz"], "test")


def phi(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def test_k1_control_window():
    n = 167
    on = [1] * 53 + [0] * (n - 53)  # 31.74 exactly
    assert compare.control({str(i): x for i, x in enumerate(on)})["status"] == "passed"
    p = 30 / n
    z = (p - 0.3174) / math.sqrt(p * (1 - p) / n)
    c = compare.control({str(i): int(i < 30) for i in range(n)})
    assert math.isclose(c["z"], z) and c["status"] == ("passed" if abs(z) <= 2 else "failed")
    between = compare.control({str(i): int(i < 40) for i in range(n)})  # 23.95: about -2.4 SE, outside 2 SE
    assert -3 < between["z"] < -2 and between["status"] == "failed"
    low = compare.control({str(i): int(i < 35) for i in range(n)})  # 20.96: about -3.6 SE
    assert low["status"] == "failed" and low["z"] < -2


def test_k2_formula_with_se_floor():
    n = 167
    bielik = {str(i): int(i < 10) for i in range(n)}
    k = compare.k2(bielik)
    p = 10 / n
    se = max(math.sqrt(p * (1 - p) / n), math.sqrt(0.1916 * 0.8084 / n))
    assert se == math.sqrt(0.1916 * 0.8084 / n)  # the floor binds below 19.16
    assert math.isclose(k["z"], (p - 0.1916) / se) and math.isclose(k["se"], 100 * se)
    high = compare.k2({str(i): int(i < 60) for i in range(n)})
    p = 60 / n
    assert math.isclose(high["z"], (p - 0.1916) / math.sqrt(p * (1 - p) / n))
    assert compare.raw_outcome(k["z"]) == "supported" and compare.raw_outcome(high["z"]) == "refuted"
    assert compare.raw_outcome(-1.99) == "undetermined" and compare.raw_outcome(-2.0) == "supported"


def k3_runs():
    """Hand-made: 40 problems; on accepts 0-29, Bielik 0-4, off 0-9 and 30-31."""
    n = 40
    on = {f"p{i:03d}": int(i < 30) for i in range(n)}
    bielik = {f"p{i:03d}": int(i < 5) for i in range(n)}
    off = {f"p{i:03d}": int(i < 10 or i in (30, 31)) for i in range(n)}
    return on, off, bielik


def test_k3_paired_formula_and_precondition():
    on, off, bielik = k3_runs()
    d = [off[t] - on[t] / 2 - bielik[t] / 2 for t in sorted(on)]
    mean, se = statistics.fmean(d), statistics.stdev(d) / math.sqrt(len(d))
    k = compare.k3(on, off, bielik)
    assert k["status"] == "ok" and math.isclose(k["z"], mean / se) and math.isclose(k["value"], 100 * mean)
    lead = [on[t] - bielik[t] for t in sorted(on)]
    assert math.isclose(k["lead"]["z"], statistics.fmean(lead) / (statistics.stdev(lead) / math.sqrt(40)))
    # a lead below z = 3 leaves K3 unread
    weak_on = {t: int(int(t[1:]) < 9) for t in on}
    weak = compare.k3(weak_on, off, bielik)
    assert weak["status"] == "precondition not met" and weak["z"] is None and weak["z_descriptive"] is not None
    assert compare.k3(on, off, None)["status"] == "not run"
    with pytest.raises(SystemExit):
        compare.k3(on, {**off, "extra": 1}, bielik)


def test_holm_over_the_group_of_four():
    assert compare.holm([0.01, 0.04, None, 0.03], 4) == [0.04, 0.09, None, 0.09]
    assert compare.holm([0.001], 4) == [0.004]  # m stays 4 with three tests missing
    assert compare.holm_verdict(phi(-3.5), None) == "supported (clear)"
    assert compare.holm_verdict(0.02, 0.98) == "supported (likely)"
    assert compare.holm_verdict(0.98, 0.02) == "refuted (likely)"
    assert compare.holm_verdict(0.03, 0.97) == "undetermined"


def test_analyse_with_and_without_the_other_benchmark():
    n = 167
    on = [1] * 53 + [0] * (n - 53)
    bielik = [1] * 10 + [0] * (n - 10)
    off = [1] * 12 + [0] * (n - 12)
    with tempfile.TemporaryDirectory() as tmp:
        res = Path(tmp) / "results"
        write_results(res, {compare.ON: on, compare.OFF: off, compare.BIELIK: bielik})
        alone = compare.analyse(res)
        assert alone["control"]["status"] == "passed"
        assert len(alone["holm"]["family"]) == 4 and alone["holm"]["m"] == 4
        k2 = alone["hypotheses"][0]
        z = (10 / n - 0.1916) / math.sqrt(0.1916 * 0.8084 / n)
        assert math.isclose(k2["z"], z) and math.isclose(k2["p_support"], phi(z))
        # alone: K2 and K3 with the other two at p = 1; Holm multiplier 4 for the smallest p
        ps = sorted(x for x in (k2["p_support"], alone["hypotheses"][1]["p_support"]) if x is not None)
        assert math.isclose(min(h["p_support_holm"] for h in alone["hypotheses"]), min(1.0, 4 * ps[0]))
        assert [t["id"] for t in alone["group_tests"]] == ["K2", "K3"]
        assert all(t["benchmark"] == "livecodebench-pro-25q2" for t in alone["group_tests"])
        other = Path(tmp) / "scicode.json"
        other.write_text(json.dumps({"group_tests": [
            {"benchmark": "scicode", "id": "K2", "z": -5.0, "p_support": phi(-5.0), "p_refute": 1 - phi(-5.0)},
            {"benchmark": "scicode", "id": "K3", "z": None, "p_support": None, "p_refute": None}]}))
        grouped = compare.analyse(res, other)
        family = {(t["benchmark"], t["id"]): t for t in grouped["holm"]["family"]}
        # Holm over the four p_support, computed here step by step
        tests = [family[k]["p_support"] for k in family]
        filled = sorted((1.0 if p is None else p, k) for p, k in zip(tests, family))
        expected, running = {}, 0.0
        for rank, (p, k) in enumerate(filled):
            running = max(running, min(1.0, (4 - rank) * p))
            expected[k] = running
        for k, t in family.items():
            if t["p_support"] is not None:
                assert math.isclose(t["p_support_holm"], expected[k])
        assert family[("scicode", "K3")]["p_support_holm"] is None and len(family) == 4
        assert grouped["hypotheses"][0]["read"] is True
        # a failed control marks every hypothesis as not read
        write_results(res, {compare.ON: [1] * 20 + [0] * (n - 20)})
        failed = compare.analyse(res, other)
        assert failed["control"]["status"] == "failed" and not any(h["read"] for h in failed["hypotheses"])


def test_explore_budget_boundary_and_compile_error_causes():
    sys.path.insert(0, str(BENCH))
    try:
        import explore
    finally:
        sys.path.remove(str(BENCH))
    rs = [{"accepted": True, "output_tokens": 4096}, {"accepted": True, "output_tokens": 4097},
          {"accepted": False, "output_tokens": 10}, {"accepted": True, "output_tokens": 32768},
          {"accepted": False, "output_tokens": None}]
    assert explore.budgets(rs) == {"4096": 1, "8192": 2, "16384": 2, "32768": 3}  # at most B tokens counts
    note = ("main.cpp:3:5: error: 'set' was not declared in this scope\nnote: 'std::set' is defined in header "
            "'<set>'; did you forget to '#include <set>'?")
    assert explore.cause(note) == "compiler_says_missing_include"
    assert explore.cause("main.cpp:19:25: error: 'gcd' was not declared in this scope\n") == "undeclared_std_name"
    assert explore.cause("x.cpp:1: error: 'numeric_limits' is not a member of 'std'") == "undeclared_std_name"
    assert explore.cause("main.cpp:5:1: error: 'result' was not declared in this scope") == "other"
    assert explore.cause("main.cpp:9: error: expected ';' at end of input\nerror: 'gcd' was not declared") == "other"


def test_readme_blocks_are_the_generator_output():
    sys.path.insert(0, str(BENCH))
    try:
        import readme
    finally:
        sys.path.remove(str(BENCH))
    results = BENCH / "results"
    text = (BENCH / "README.md").read_text(encoding="utf-8")
    bodies = readme.blocks(results)
    assert readme.render(text, bodies) == text  # byte for byte: no number edited by hand, none stale
    line = next(x for x in text.splitlines() if x.startswith("| Bielik 11B v3.1 (`bielik-11b-v3.1`) |"))
    swapped = text.replace(line, line.replace(" | 1.80 | ", " | 1.81 | ", 1), 1)
    assert swapped != text and readme.render(swapped, bodies) != swapped  # one swapped number is caught
