"""SciCode (api-benchmarks/scicode): checks of the generation path, the request layer, the summary and the
hypotheses, without a model, GPU, test_data.h5 or outside network.

- Prompts and code files: scicode_runner's Generator (Gencode with only the model call replaced) is run on real test
  problems (77 and the first 7 steps of 13, whose step 6 the harness supplies) against SciCode's own uninterrupted
  flow (gencode's main loop with the same answers); the prompt and code files must be byte-identical, also after an
  interrupted and resumed run. Needs the pinned clone in `.cache/SciCode` (run.sh makes it) and problems_test.jsonl
  at the pinned revision in the Hugging Face cache; skipped without them.
- Extraction: SciCode's extract_python_script on the text after the last `</think>`; unfinished (thinking on, no
  `</think>` or a length stop) and unsupported answers give empty code.
- Requests against a fake OpenAI-compatible server on 127.0.0.1: the vLLM body (card sampling, seed,
  chat_template_kwargs only for nothink, max_tokens = context - /tokenize count), the Fabryka API body and its
  max_tokens = context - local count - margin, a prompt over the context never sent, retries with the shared pause
  and the event log.
- Scoring preconditions: an errored or missing step stops scoring; extra code files stop it.
- summarize.py on hand-made graded records (pass rate, binomial and clustered SE computed by hand, main problems,
  the scorer cross-check) and hypotheses.py (K1, K2 with its SE floor, K3 with its precondition, Holm m = 4 with
  and without the other benchmark's group_tests) on hand-made result files.
Run: <benchmark>/.venv-gen/bin/python -m pytest research/tests/test_scicode.py -x -q
"""
import contextlib
import gzip
import json
import math
import os
import sys
import types
import urllib.error
from pathlib import Path

import pytest

BENCH = Path(__file__).resolve().parents[1] / "api-benchmarks" / "scicode"
sys.path.insert(0, str(BENCH))
import hypotheses  # noqa: E402
import provenance  # noqa: E402
import scicode_runner as sr  # noqa: E402
import raw_outputs  # noqa: E402
import summarize  # noqa: E402


# ---------------------------------------------------------------------------------------------------------------
# Extraction

THINKING = "Draft:\n```python\ndef f():\n    return 0\n```\n</think>\nFinal:\n```python\nimport numpy as np\ndef f():\n    return 1\n```\n"


def ok(output, finish="stop", thinking=True):
    return {"status": "ok", "output": output, "finish_reason": finish,
            "unfinished": sr.is_unfinished(output, finish, thinking)}


def test_after_think_and_answer_text():
    assert sr.after_think("a</think>b</think>c") == "c"
    assert sr.after_think("no tags") == "no tags"
    assert sr.answer_text(ok(THINKING), thinking=True) == "\nFinal:\n```python\nimport numpy as np\ndef f():\n    return 1\n```\n"
    # thinking on: no </think>, or stopped by the length limit, is unfinished -> empty text
    assert sr.answer_text(ok("```python\ndef f(): pass\n```"), thinking=True) == ""
    assert sr.answer_text(ok(THINKING, finish="length"), thinking=True) == ""
    # thinking off (nothink, Bielik): the text after the last </think>, as it is, even when cut by the limit
    assert sr.answer_text(ok("```python\nx = 1\n```", finish="length", thinking=False), thinking=False) == \
        "```python\nx = 1\n```"
    assert sr.answer_text({"status": "unsupported"}, thinking=False) == ""
    assert sr.is_unfinished("x", "length", thinking=False) and not sr.is_unfinished("x", "stop", thinking=False)


def harness_or_skip():
    if not (sr.SCICODE_DIR / ".git").exists():
        pytest.skip("no SciCode clone in .cache/ (run.sh makes it)")
    cwd = os.getcwd()
    try:
        return sr.harness()
    finally:
        os.chdir(cwd)


def test_extraction_is_scicodes_on_the_text_after_think():
    h = harness_or_skip()
    code = h.models.extract_python_script(sr.answer_text(ok(THINKING), thinking=True))
    assert code == "\ndef f():\n    return 1\n"  # the final block, its import line removed by SciCode's regex
    assert h.models.extract_python_script(sr.answer_text(ok("```python\ndef f(): pass\n```"), thinking=True)) == ""


def test_stubbed_clients_raise_when_called():
    h = harness_or_skip()
    assert {"openai", "litellm", "config"} <= set(h.stubbed)
    with pytest.raises(RuntimeError, match="stub"):
        sys.modules["openai"].OpenAI(api_key="x")


def test_e1_extraction_cases():
    """PROTOCOL.md Amendment 1: E1 is the official extraction with a python block or two or more fence lines, the
    text before the only fence line when there is exactly one, the whole text without fence lines; imports removed."""
    official = harness_or_skip().models.extract_python_script
    e1 = lambda text: sr.e1_extract(text, official)  # noqa: E731
    # no fence line: the whole text, import lines removed (as the official one)
    assert e1("x = 1\nimport os\ny = 2") == official("x = 1\nimport os\ny = 2") == "x = 1\n\ny = 2"
    # one fence line (a closing fence never opened, the Bielik smoke pattern): the code before it, not the prose after
    lone = "\ndef f():\n    import math\n    return 1\n```\n\nThe function f returns one."
    assert official(lone) == "\n\nThe function f returns one."
    assert e1(lone) == "\ndef f():\n\n    return 1\n"
    assert e1("x = 1\n  ```\nprose") == "x = 1\n"  # an indented fence line counts
    # two fence lines without python: the official result
    two = "```\ndef f(): pass\n```\nprose\n"
    assert e1(two) == official(two) == "\ndef f(): pass\n"
    # a python block, even unclosed: the official result
    block = "Here:\n```python\nfrom os import path\nx = 1\n```\nbye ```"
    assert e1(block) == official(block) == "\nx = 1\n"
    assert e1("```python\nx = 1\n") == official("```python\nx = 1\n") == "\nx = 1\n"
    # ``` inside a line is not a fence line: no fence line, so the whole text
    assert e1("s = 'a ``` b'\n") == "s = 'a ``` b'\n" != official("s = 'a ``` b'\n")
    # with thinking on, E1 reads the text after the last </think>, as the official extraction does
    answer = ok("<think>```python\ndef draft(): pass\n```</think>\ndef f():\n    return 2\n```\nprose")
    assert e1(sr.answer_text(answer, thinking=True)) == "\ndef f():\n    return 2\n"
    assert e1(sr.answer_text(ok("```python\nx\n```"), thinking=True)) == ""  # unfinished: empty


# ---------------------------------------------------------------------------------------------------------------
# Prompts and code files against SciCode's own flow

def load_problems():
    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(sr.DATA_REPO, "problems_test.jsonl", repo_type="dataset", revision=sr.DATA_REVISION,
                               local_files_only=True)
    except Exception:
        pytest.skip("problems_test.jsonl at the pinned revision is not in the Hugging Face cache")
    rows = {r["problem_id"]: r for r in map(json.loads, Path(path).read_text(encoding="utf-8").splitlines())}
    p13 = dict(rows["13"], sub_steps=rows["13"]["sub_steps"][:7])  # step 6 supplied by the harness, 7 uses it
    return [rows["77"], p13]


def next_function(prompt):
    """The function or class the prompt asks for (the header after the NEXT STEP heading)."""
    import re
    tail = prompt.split("NEXT STEP", 1)[1]
    return re.search(r"\b(?:def|class)\s+(\w+)", tail).group(1)


def model_answer(prompt):
    name = next_function(prompt)
    return f"Sure.\n```python\nimport os\ndef {name}(*args):\n    return '{name}'\n```\nmore text\n```python\nx = 1\n```"


def official(h, out, problem, setting):
    """gencode.py main's loop over one problem, with the model call answering `model_answer`."""
    g = h.gencode
    with_bg = setting == "with_background"
    g.get_model_function = lambda model, **kw: model_answer
    gcode = g.Gencode(model="m", output_dir=out / "generated_code", prompt_dir=out / "prompts",
                      with_background=with_bg, temperature=0.6)
    template = g.BACKGOUND_PROMPT_TEMPLATE if with_bg else g.DEFAULT_PROMPT_TEMPLATE
    steps = len(problem["sub_steps"])
    pid = problem["problem_id"]
    for i in range(steps):
        if (pid == "13" and i == 5) or (pid == "62" and i == 0) or (pid == "76" and i == 2):
            continue
        gcode.generate_response_with_steps(problem, i + 1, steps, "m", template)


def files(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def ours(h, out, problems, fail_at=None):
    calls = []

    def respond(prompt, ctx):
        calls.append((ctx["setting"], ctx["problem_id"], ctx["step"]))
        if fail_at == (ctx["setting"], ctx["problem_id"], ctx["step"]):
            raise urllib.error.URLError("refused")
        return {"status": "ok", "output": "<think>```python\ndef draft(): pass\n```</think>" + model_answer(prompt),
                "finish_reason": "stop", "unfinished": False, "output_tokens": 5, "prompt_tokens": 7}

    gen = sr.Generator(h, out, "m", respond, thinking=True)
    for setting in sr.SETTINGS:
        for p in problems:
            gen.run(sr.Chain(setting, p), sr.latest(sr.read_jsonl(out / "generations.jsonl")))
    return calls


def test_prompts_and_code_equal_scicodes_flow_and_survive_resume(tmp_path):
    h = harness_or_skip()
    problems = load_problems()
    cwd = os.getcwd()
    try:
        os.chdir(sr.SCICODE_DIR)
        for setting in sr.SETTINGS:
            for p in problems:
                official(h, tmp_path / "official", p, setting)
        calls = ours(h, tmp_path / "ours", problems)
        fail = ("with_background", "77", 3)
        first = ours(h, tmp_path / "resumed", problems, fail_at=fail)
        second = ours(h, tmp_path / "resumed", problems)
    finally:
        os.chdir(cwd)
    for tree in ("generated_code", "prompts"):
        reference = files(tmp_path / "official" / tree)
        assert len(reference) > 20
        assert files(tmp_path / "ours" / tree) == reference
        assert files(tmp_path / "resumed" / tree) == reference
    assert ("with_background", "13", 6) not in calls  # supplied by the harness, never asked
    assert len(calls) == 2 * (len(problems[0]["sub_steps"]) + 6)
    # the failed step stopped its chain; the rerun asked that step and the rest of the chain, nothing else
    later = [c for c in first if c[:2] == fail[:2] and c[2] > fail[2]]
    assert fail in first and not later
    assert set(second) == {c for c in calls if c[:2] == fail[:2] and c[2] >= fail[2]}
    answers = sr.latest(sr.read_jsonl(tmp_path / "resumed" / "generations.jsonl"))
    assert answers[fail]["status"] == "ok" and len(answers) == len(calls)
    rec = answers[("without_background", "77", 2)]
    assert rec["extracted_code"].startswith("\ndef ") and rec["think_open"] is True


def test_e1_files_rebuild_scicodes_files(tmp_path):
    """Amendment 1: E1 files are Gencode's files with E1 code. When every answer has a python block, E1 is the
    official extraction, so the rebuilt files equal SciCode's own byte for byte (also around the supplied 13.6);
    one answer with a lone closing fence changes its own file and the later files of that problem only."""
    h = harness_or_skip()
    problems = load_problems()
    cwd = os.getcwd()
    try:
        os.chdir(sr.SCICODE_DIR)
        ours(h, tmp_path / "ours", problems)
        answers = sr.latest(sr.read_jsonl(tmp_path / "ours" / "generations.jsonl"))
        codes = sr.build_e1_files(h, problems, answers, list(sr.SETTINGS), True, "m", tmp_path / "e1")
        assert files(tmp_path / "e1") == files(tmp_path / "ours" / "generated_code")
        assert codes[("with_background", "13", 7)] == answers[("with_background", "13", 7)]["extracted_code"]
        lone = ("with_background", "77", 2)
        answers[lone] = dict(answers[lone], output="</think>\ndef dist(*args):\n    return 'E1'\n```\nThis computes.")
        sr.build_e1_files(h, problems, answers, list(sr.SETTINGS), True, "m", tmp_path / "e1b")
    finally:
        os.chdir(cwd)
    before, after = files(tmp_path / "e1"), files(tmp_path / "e1b")
    changed = sorted(k for k in before if before[k] != after[k])
    assert changed == sorted(f"m/with_background/77.{s}.py" for s in range(2, 13))
    assert b"return 'E1'" in after["m/with_background/77.3.py"] and b"This computes" not in after["m/with_background/77.2.py"]


# ---------------------------------------------------------------------------------------------------------------
# Requests

class FakeServer:
    """vLLM-like: /tokenize counts 1000 tokens, max_model_len 262144; chat completions answer `content`. The first
    `fail` chat requests get 503."""

    def __init__(self, fail=0, content="</think>```python\nx = 1\n```", finish="stop"):
        import http.server
        import threading
        self.fail, self.requests, self.tokenize, self.headers = fail, [], [], []
        fake = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                if self.path == "/tokenize":
                    fake.tokenize.append(body)
                    return self.reply(200, {"count": 1000, "max_model_len": 262144})
                fake.requests.append(body)
                fake.headers.append(dict(self.headers))
                if len(fake.requests) <= fake.fail:
                    return self.reply(503, {"error": "busy"})
                self.reply(200, {"choices": [{"message": {"role": "assistant", "content": content},
                                              "finish_reason": finish}],
                                 "usage": {"prompt_tokens": 1003, "completion_tokens": 9}})

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

    def close(self):
        self.server.shutdown()


MESSAGES = [{"role": "user", "content": "prompt"}]


@contextlib.contextmanager
def fake(**kw):
    s = FakeServer(**kw)
    try:
        yield s
    finally:
        s.close()


def vllm(base, kwargs=None):
    return sr.Server(model="lfm3-1.7b", chat_url=f"{base}/v1/chat/completions", retries=3, timeout=10,
                     tokenize_url=f"{base}/tokenize", template_kwargs=kwargs, context=262144,
                     gate=sr.Gate(0.01, 0.02))


def test_vllm_body_thinking_and_nothink():
    with fake() as s:
        on = sr.ask(vllm(s.base), MESSAGES, thinking=True)
        off = sr.ask(vllm(s.base, {"enable_thinking": False}), MESSAGES, thinking=False)
    body_on, body_off = s.requests
    expected = {"model": "lfm3-1.7b", "messages": MESSAGES, "n": 1, "temperature": 0.6, "top_p": 0.95, "top_k": 0,
                "repetition_penalty": 1.0, "frequency_penalty": 0, "presence_penalty": 0, "seed": 20261122,
                "max_tokens": 262144 - 1000}
    assert body_on == expected
    assert body_off == {**expected, "chat_template_kwargs": {"enable_thinking": False}}
    assert "chat_template_kwargs" not in s.tokenize[0]
    assert s.tokenize[1]["chat_template_kwargs"] == {"enable_thinking": False}  # counted with the same template
    assert (on["status"], on["prompt_tokens"], on["max_tokens"], on["output_tokens"]) == ("ok", 1000, 261144, 9)
    assert on["unfinished"] is False and off["unfinished"] is False


def api(base, count=1000, retries=30, events=None):
    return sr.Server(model="bielik-11b-v3.1", chat_url=f"{base}/v1/chat/completions", retries=retries, timeout=10,
                     headers={"Authorization": "Bearer t"}, count=lambda m: count, context=32768, margin=64,
                     gate=sr.Gate(0.01, 0.02), events=events or sr.EventLog())


def test_api_body_margin_and_unsupported(tmp_path):
    with fake(fail=2) as s:
        log = sr.EventLog(tmp_path / "api-events.jsonl")
        r = sr.ask(api(s.base, events=log), MESSAGES, thinking=False, step="with_background/77.1")
        over = sr.ask(api(s.base, count=32768 - 64), MESSAGES, thinking=False)
    body = s.requests[-1]
    assert sorted(body) == ["max_tokens", "messages", "model", "seed", "temperature", "top_p"]
    assert (body["temperature"], body["top_p"], body["seed"]) == (0.6, 0.95, 20261122)
    assert body["max_tokens"] == 32768 - 1000 - 64 == r["max_tokens"]
    assert r["api_prompt_tokens"] == 1003 and r["status"] == "ok"
    assert over["status"] == "unsupported" and len(s.requests) == 3  # 2 x 503, 1 answer; the long prompt not sent
    events = sr.read_jsonl(tmp_path / "api-events.jsonl")
    assert [e["action"] for e in events] == ["retry", "retry", "recovered"]
    assert {e["status"] for e in events[:2]} == {503} and events[0]["step"] == "with_background/77.1"
    assert sr.event_counts(events)["by_action"] == {"recovered": 1, "retry": 2}


def test_api_gives_up_after_retries():
    with fake(fail=100) as s:
        with pytest.raises(urllib.error.HTTPError):
            sr.ask(api(s.base, retries=3), MESSAGES, thinking=False)
    assert len(s.requests) == 3


def test_sampling_record_lists_what_is_sent():
    server = api("http://127.0.0.1:1")
    assert sr.sampling(server) == {"request_sampling": {"temperature": 0.6, "top_p": 0.95, "seed": 20261122},
                                   "server_defaults": "unknown (Fabryka API)"}
    assert sr.vllm_defaults({"repetition_penalty": 1.1, "top_k": 50, "temperature": 0.1},
                            sr.request_body(vllm("http://x"), [], 0)) == {}


# ---------------------------------------------------------------------------------------------------------------
# Scoring preconditions and scorer output

def test_check_answers_requires_every_step_and_only_those_files(tmp_path):
    expected = [("1", 1), ("1", 2)]
    code = tmp_path / "m"
    (code / "with_background").mkdir(parents=True)
    for s in (1, 2):
        (code / "with_background" / f"1.{s}.py").write_text("")
    good = {("with_background", "1", 1): {"status": "ok"}, ("with_background", "1", 2): {"status": "unsupported"}}
    assert sr.check_answers(good, expected, code) == ["with_background"]
    bad = {**good, ("with_background", "1", 2): {"status": "error"}}
    with pytest.raises(SystemExit, match="1 steps have no answer"):
        sr.check_answers(bad, expected, code)
    (code / "with_background" / "9.1.py").write_text("")
    with pytest.raises(SystemExit, match="code files differ"):
        sr.check_answers(good, expected, code)


def e1_case(tmp_path, identical):
    """out/ with official and E1 files for steps 1.1-1.3; the E1 file differs where `identical` is False. Official
    verdicts: all fail."""
    out = tmp_path / "out"
    expected = [("1", 1), ("1", 2), ("1", 3)]
    for (pid, step), same in zip(expected, identical):
        for kind in ("generated_code", "generated_code_e1"):
            path = out / kind / "m" / "with_background" / f"{pid}.{step}.py"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("code" if same or kind == "generated_code" else "other code")
    verdicts = {("official", "with_background", p, s): "fail" for p, s in expected}
    return out, expected, verdicts


def fake_scorer(seen):
    """Like test_generated_code.py: a step with a log keeps it; any other file it is given passes."""
    def run(root, env, args, setting, code_dir, score_dir, logs_name, tag):
        files = sorted(p.name for p in (code_dir / args.model_id / setting).iterdir())
        seen.append(files)
        logs = score_dir / logs_name / args.model_id / setting
        logs.mkdir(parents=True, exist_ok=True)
        for name in files:
            log = logs / name.replace(".py", ".txt")
            if not log.exists():
                log.write_text("pass")
        return {"command": ["fake"], "seconds": 0.0, "printed": {"correct_steps": len(files)}}
    return run


def test_e1_reuses_official_verdicts_for_identical_files(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(sr, "run_scorer", fake_scorer(seen))
    args = types.SimpleNamespace(model_id="m")
    out, expected, verdicts = e1_case(tmp_path, identical=[True, False, True])
    r = sr.score_e1(None, {}, args, "with_background", out, out / "score", expected, verdicts)
    assert seen == [["1.2.py"]]  # only the differing file reaches the scorer
    assert [verdicts[("e1", "with_background", "1", s)] for s in (1, 2, 3)] == ["fail", "pass", "fail"]
    assert (r["reused_identical"], r["scored"], r["reused_passes"]) == (2, 1, 0)
    assert r["reused_steps"] == [("1", 1), ("1", 3)] and r["printed"] == {"correct_steps": 1}
    # all identical: no scorer run at all, every E1 verdict is the official one
    seen.clear()
    out, expected, verdicts = e1_case(tmp_path / "same", identical=[True, True, True])
    verdicts[("official", "with_background", "1", 2)] = "time out"
    r = sr.score_e1(None, {}, args, "with_background", out, out / "score", expected, verdicts)
    assert seen == [] and r["printed"] is None and (r["reused_identical"], r["scored"]) == (3, 0)
    assert [verdicts[("e1", "with_background", "1", s)] for s in (1, 2, 3)] == ["fail", "time out", "fail"]


def test_e1_logs_kept_only_for_the_same_scored_files(tmp_path, monkeypatch):
    monkeypatch.setattr(sr, "run_scorer", fake_scorer([]))
    args = types.SimpleNamespace(model_id="m")
    out, expected, verdicts = e1_case(tmp_path, identical=[True, False, True])
    logs = out / "score" / "logs_e1" / "m" / "with_background"
    logs.mkdir(parents=True)
    (logs / "1.3.txt").write_text("pass")  # a log from before the stamp existed: removed
    sr.score_e1(None, {}, args, "with_background", out, out / "score", expected, verdicts)
    assert sorted(p.name for p in logs.iterdir()) == ["1.2.txt"]
    (logs / "1.2.txt").write_text("fail")  # the same files again: the scorer reuses this log
    v = dict(verdicts)
    sr.score_e1(None, {}, args, "with_background", out, out / "score", expected, v)
    assert v[("e1", "with_background", "1", 2)] == "fail"
    (out / "generated_code_e1" / "m" / "with_background" / "1.2.py").write_text("changed")
    v = dict(verdicts)
    sr.score_e1(None, {}, args, "with_background", out, out / "score", expected, v)
    assert v[("e1", "with_background", "1", 2)] == "pass"  # other E1 file: its old log went, it was scored again


def test_official_logs_survive_a_runner_change(tmp_path):
    score = tmp_path / "score"
    (score / "logs").mkdir(parents=True)
    (score / "logs" / "1.1.txt").write_text("pass")
    # a stamp written by 2ade850c, with the runner's sha256: the official logs stay for the same answers
    (score / "stamp.json").write_text(json.dumps({"generations_sha256": "a", "runner_sha256": "old"}))
    sr.keep_official_logs(score, "a")
    assert (score / "logs" / "1.1.txt").read_text() == "pass"
    assert json.loads((score / "stamp.json").read_text()) == {"generations_sha256": "a"}
    sr.keep_official_logs(score, "b")  # other answers: everything goes
    assert not (score / "logs").exists()


def test_parse_scorer_output_and_expected_steps():
    stdout = "Testing function 1.1 ...\ncorrect problems: 3/65\ncorrect steps: 40/288\n"
    stderr = ("Using the latest cached version of the dataset since SciCode1/SciCode couldn't be found\n"
              "Found the latest cached dataset configuration 'default' at /c/datasets/SciCode1___sci_code/default/"
              "0.0.0/4510f6a6aa27c43fad7b43da2c59602a86e88480 (last modified on Sun Nov 22 2026).\n")
    p = sr.parse_scorer_output(stdout, stderr)
    assert p == {"correct_problems": 3, "problems_denominator": 65, "correct_steps": 40, "steps_denominator": 288,
                 "dataset_revision_seen": sr.DATA_REVISION}
    assert sr.parse_scorer_output(stdout, "")["dataset_revision_seen"] is None
    rows = [{"problem_id": "13", "sub_steps": [{}] * 7}, {"problem_id": "62", "sub_steps": [{}] * 2},
            {"problem_id": "76", "sub_steps": [{}] * 3}, {"problem_id": "5", "sub_steps": [{}] * 2}]
    assert sr.expected_steps(rows) == [("13", 1), ("13", 2), ("13", 3), ("13", 4), ("13", 5), ("13", 7), ("62", 2),
                                       ("76", 1), ("76", 2), ("5", 1), ("5", 2)]


# ---------------------------------------------------------------------------------------------------------------
# summarize.py

def g(setting, pid, step, passed, status="ok", verdict=None, tokens=100, finish="stop", unfinished=False,
      think_open=False, pass_e1=None):
    """A graded line; an E1 verdict given here means the E1 file differed and was scored, else the official one is
    reused."""
    reused = pass_e1 is None
    pass_e1 = passed if reused else pass_e1
    return {"setting": setting, "problem_id": pid, "step": step, "step_id": f"{pid}.{step}",
            "verdict": verdict or ("pass" if passed else "fail"), "pass": passed, "status": status,
            "verdict_e1": "pass" if pass_e1 else "fail", "pass_e1": pass_e1, "e1_reused": reused,
            "prompt_tokens": 50, "output_tokens": tokens if status == "ok" else None, "max_tokens": 1000,
            "context": 1050, "finish_reason": finish if status == "ok" else None,
            "unfinished": unfinished if status == "ok" else None, "think_open": think_open,
            "api_prompt_tokens": None, "error": None, "started": "2026-11-23T10:00:00+00:00", "code": "x",
            "code_e1": "y"}


# problem 1: 2 of 2 pass (solved); problem 2: 1 of 3; problem 3: 0 of 1 (unsupported) -> p = 3/6
GRADED = [g("with_background", "1", 1, True), g("with_background", "1", 2, True, think_open=True),
          g("with_background", "2", 1, True, tokens=300), g("with_background", "2", 2, False, verdict="time out"),
          g("with_background", "2", 3, False, finish="length", unfinished=True, pass_e1=True),
          g("with_background", "3", 1, False, status="unsupported")]


def test_setting_metrics_by_hand():
    m = summarize.setting_metrics(GRADED)
    p = 0.5
    # clustered: residuals per problem 1: (0.5 + 0.5) = 1, 2: (0.5 - 0.5 - 0.5) = -0.5, 3: -0.5
    se_cl = math.sqrt(3 / 2 * (1 + 0.25 + 0.25)) / 6
    assert (m["score"], m["n"], m["correct"]) == (50.0, 6, 3)
    assert m["stderr"] == round(100 * math.sqrt(p * (1 - p) / 6), 2) == 20.41
    assert m["stderr_clustered"] == round(100 * se_cl, 2) == 25.0
    assert m["main_problems"] == {"solved": 1, "of": 3, "solved_ids": ["1"]}
    assert (m["timeouts"], m["unfinished"], m["length_stops"], m["unsupported"]) == (1, 1, 1, 1)
    assert m["answers_with_think_open"] == {"count": 1, "of": 5, "share": 0.2}
    assert m["output_tokens"] == {"mean": 140.0, "median": 100, "max": 300}


def test_clustered_se_equals_binomial_shape_with_singleton_clusters():
    ys = [1.0, 0.0, 1.0, 1.0]
    se = summarize.clustered_se(ys, ["a", "b", "c", "d"])
    p = 0.75
    assert math.isclose(se, math.sqrt(4 / 3 * 4 * (p * (1 - p))) / 4)
    assert summarize.clustered_se([1.0, 0.0], ["a", "a"]) is None


def test_scorer_cross_check_stops_on_mismatch():
    m = summarize.setting_metrics(GRADED)
    summarize.check_against_scorer("with_background", m, {"correct_steps": 3, "correct_problems": 1})
    with pytest.raises(SystemExit):
        summarize.check_against_scorer("with_background", m, {"correct_steps": 4, "correct_problems": 1})


def write_out(out, records, limit=None):
    out.mkdir(parents=True)
    (out / "graded.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")
    provenance.record(out, ["graded.jsonl"], "test")
    printed = {}
    for s in {r["setting"] for r in records}:
        rs = [r for r in records if r["setting"] == s]
        printed[s] = {"printed": {"correct_steps": sum(r["pass"] for r in rs),
                                  "correct_problems": summarize.problems_solved(rs)["solved"]}}
        scored = [r for r in rs if not r["e1_reused"]]
        printed[f"e1/{s}"] = {"printed": {"correct_steps": sum(r["pass_e1"] for r in scored)} if scored else None,
                              "reused_identical": len(rs) - len(scored),
                              "reused_passes": sum(r["pass"] for r in rs if r["e1_reused"])}
    run = {"generation": [{"step": "gen", "thinking": True, "sampling": {"request_sampling": {"temperature": 0.6}}}],
           "scoring": {"step": "score", "split": "test", "limit": limit, "runs": printed}}
    (out / "run.json").write_text(json.dumps(run), encoding="utf-8")


def test_summary_file_limit_and_full_count(tmp_path):
    # without background: nothing passes officially, only step 1.1 under E1 (scored, not reused)
    records = GRADED + [dict(r, setting="without_background", **{"pass": False, "verdict": "fail",
                                                                  "pass_e1": r["step_id"] == "1.1",
                                                                  "verdict_e1": "pass" if r["step_id"] == "1.1" else "fail",
                                                                  "e1_reused": r["step_id"] != "1.1"})
                        for r in GRADED]
    write_out(tmp_path / "out", records, limit=3)
    summarize.main(str(tmp_path / "out"), str(tmp_path / "results" / "m"), 3)
    result = json.loads((tmp_path / "out" / "m-limit3.json").read_text())
    assert (result["score"], result["n"], result["stderr_clustered"]) == (50.0, 6, 25.0)
    assert result["other_metrics"]["without_background"]["score"] == 0.0
    # E1 (Amendment 1) only in other_metrics: step 2.3 passes under E1, so 4 of 6 and problem 2 still unsolved
    e1 = result["other_metrics"]["extraction_e1"]["with_background"]
    assert (e1["score"], e1["correct"], e1["main_problems"]["solved"]) == (66.67, 4, 1)
    assert result["other_metrics"]["extraction_e1"]["without_background"]["correct"] == 1
    assert (e1["reused_identical"], e1["scored"]) == (5, 1)
    with gzip.open(tmp_path / "out" / "m-limit3.jsonl.gz", "rt") as f:
        lines = [json.loads(x) for x in f]
    assert len(lines) == 12 and lines[0]["task_id"] == "with_background/1.1" and lines[0]["score"] == 1
    assert [x["score_e1"] for x in lines[:6]] == [1, 1, 1, 0, 1, 0] and lines[0]["output_e1"] == "y"
    assert [x["e1_reused"] for x in lines[:6]] == [True, True, True, True, False, True]
    # the scorer's E1 counts plus the reused official passes must match ours
    run = json.loads((tmp_path / "out" / "run.json").read_text())
    run["scoring"]["runs"]["e1/with_background"]["printed"]["correct_steps"] = 0
    (tmp_path / "out" / "run.json").write_text(json.dumps(run))
    with pytest.raises(SystemExit, match="e1/with_background"):
        summarize.main(str(tmp_path / "out"), str(tmp_path / "results" / "m"), 3)
    run["scoring"]["runs"]["e1/with_background"]["printed"]["correct_steps"] = 1
    run["scoring"]["runs"]["e1/with_background"]["reused_identical"] = 4
    (tmp_path / "out" / "run.json").write_text(json.dumps(run))
    with pytest.raises(SystemExit, match="e1/with_background"):
        summarize.main(str(tmp_path / "out"), str(tmp_path / "results" / "m"), 3)
    assert not (tmp_path / "results").exists()
    write_out(tmp_path / "full", records)
    with pytest.raises(SystemExit, match="expected 288"):
        summarize.main(str(tmp_path / "full"), str(tmp_path / "results" / "m"), None)


def test_null_result(tmp_path):
    summarize.null_result(str(tmp_path / "slayer"), "base model")
    r = json.loads((tmp_path / "slayer.json").read_text())
    assert r["score"] is None and r["reason"] == "base model" and r["n"] == 0


# ---------------------------------------------------------------------------------------------------------------
# hypotheses.py

def write_model(results, model, passes, clusters, e1=None):
    """`passes` per item (0/1), items numbered within their problem in `clusters` order; `e1` the per-item passes
    under extraction E1 (default: the same)."""
    results.mkdir(exist_ok=True)
    counter = {}
    rows = []
    for y, y_e1, pid in zip(passes, e1 or passes, clusters):
        counter[pid] = counter.get(pid, 0) + 1
        for setting in sr.SETTINGS:
            rows.append({"task_id": f"{setting}/{pid}.{counter[pid]}", "setting": setting, "problem_id": pid,
                         "step": counter[pid], "score": y, "score_e1": y_e1})
    with gzip.open(results / f"{model}.jsonl.gz", "wt") as f:
        f.write("".join(json.dumps(r) + "\n" for r in rows))
    provenance.record(results, [f"{model}.jsonl.gz"], "test")


CLUSTERS = [str(i // 4 + 1) for i in range(40)]  # 10 problems x 4 steps


def by_hand(d, clusters):
    """mean, clustered SE (CR1) recomputed here without summarize."""
    n, mean = len(d), sum(d) / len(d)
    sums = {}
    for v, c in zip(d, clusters):
        sums[c] = sums.get(c, 0.0) + v - mean
    G = len(sums)
    return mean, math.sqrt(G / (G - 1) * sum(s * s for s in sums.values())) / n


def test_k1_k2_k3_by_hand(tmp_path):
    r = tmp_path / "results"
    on = [1, 1, 1, 0] * 10                      # 75 %
    off = [1, 0, 0, 0] * 5 + [1, 1, 0, 0] * 5   # 37.5 %
    b = [0, 0, 0, 0] * 8 + [1, 0, 0, 0] * 2     # 5 %
    write_model(r, "lfm3-1.7b", on, CLUSTERS)
    write_model(r, "lfm3-1.7b-nothink", off, CLUSTERS)
    write_model(r, "bielik-11b-v3.1", b, CLUSTERS)
    a = hypotheses.analyse(r)
    # K1: (0.75 - 0.2847) / SE_cl; every problem has 3 of 4, so SE_cl = 0 -> undetermined
    assert a["control"]["status"] == "undetermined" and a["control"]["se_clustered"] == 0.0
    k2, k3 = a["hypotheses"]
    mean_b, se_b = by_hand(b, CLUSTERS)
    se = max(se_b, math.sqrt(0.1632 * 0.8368 / 288))
    assert math.isclose(k2["z"], (mean_b - 0.1632) / se)
    assert math.isclose(k2["se"], 100 * se_b) and se_b > math.sqrt(0.1632 * 0.8368 / 288)
    lead, lead_se = by_hand([x - y for x, y in zip(on, b)], CLUSTERS)
    d, d_se = by_hand([o - x / 2 - y / 2 for o, x, y in zip(off, on, b)], CLUSTERS)
    assert math.isclose(k3["precondition"]["z"], lead / lead_se) and k3["precondition"]["met"]
    assert math.isclose(k3["z"], d / d_se) and math.isclose(k3["value"], 100 * d)
    assert k3["outcome_raw"] == ("supported" if d / d_se <= -2 else "refuted" if d / d_se >= 2 else "undetermined")
    # Holm m = 4 with the two missing group tests as p = 1
    ps = sorted([hypotheses.phi(k2["z"]), hypotheses.phi(k3["z"]), 1.0, 1.0])
    adj = [min(1, 4 * ps[0])]
    adj.append(max(adj[0], min(1, 3 * ps[1])))
    assert math.isclose(min(k2["p_support_holm"], k3["p_support_holm"]), adj[0])
    assert math.isclose(max(k2["p_support_holm"], k3["p_support_holm"]), adj[1])
    assert a["holm"]["m"] == 4 and a["holm"]["missing_counted_as_p_1"] == 2
    assert [t["id"] for t in a["group_tests"]] == ["K2", "K3"] and a["group_tests"][0]["benchmark"] == "scicode"
    assert all(row["read"] is False for row in a["hypotheses"])  # K1 did not pass


def test_k1_passes_within_two_clustered_se(tmp_path):
    r = tmp_path / "results"
    lfm = [1, 0, 0, 0] * 5 + [1, 1, 0, 0] * 5   # 37.5 %, varies by problem
    write_model(r, "lfm3-1.7b", lfm, CLUSTERS)
    c = hypotheses.analyse(r)["control"]
    mean, se = by_hand(lfm, CLUSTERS)
    assert math.isclose(c["z"], (mean - 0.2847) / se)
    assert c["status"] == ("passed" if abs((mean - 0.2847) / se) <= 2 else "failed")
    assert hypotheses.analyse(r)["hypotheses"][0]["status"] == "not run"


def test_k3_precondition_not_met_counts_as_p_1(tmp_path):
    r = tmp_path / "results"
    same = [1, 0, 0, 0] * 10
    for m in ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1"):
        write_model(r, m, same, CLUSTERS)
    k3 = hypotheses.analyse(r)["hypotheses"][1]
    assert k3["status"] == "precondition not met" and k3["z"] is None and k3["p_support"] is None
    assert k3["verdict_holm"] == "precondition not met"
    # Bielik ahead of LFM3 (lead negative, z defined): still not met
    r2 = tmp_path / "results2"
    write_model(r2, "lfm3-1.7b", [1, 0, 0, 0] * 5 + [0, 0, 0, 0] * 5, CLUSTERS)
    write_model(r2, "lfm3-1.7b-nothink", [1, 0, 0, 0] * 10, CLUSTERS)
    write_model(r2, "bielik-11b-v3.1", [1, 1, 0, 0] * 10, CLUSTERS)
    k3 = hypotheses.analyse(r2)["hypotheses"][1]
    assert k3["precondition"]["z"] is not None and k3["precondition"]["z"] < 0
    assert k3["status"] == "precondition not met" and k3["z"] is None


def test_k2_se_floor_binds_when_clustered_se_is_small(tmp_path):
    r = tmp_path / "results"
    b = [1, 0, 0, 0] * 10  # 25 % in every problem: clustered SE 0, so the binomial floor at 16.32 % is the SE
    for m in ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1"):
        write_model(r, m, b, CLUSTERS)
    k2 = hypotheses.analyse(r)["hypotheses"][0]
    floor = math.sqrt(0.1632 * 0.8368 / 288)
    assert k2["se_clustered"] == 0.0 and math.isclose(k2["z"], (0.25 - 0.1632) / floor)


def test_k2_under_e1_and_dependence_on_extraction(tmp_path):
    on = [1, 1, 1, 0] * 5 + [1, 1, 0, 0] * 5
    off = [1, 0, 0, 0] * 10
    b_official = [0, 0, 0, 0] * 10                    # 0 %: K2 supported
    b_e1 = [1, 1, 0, 0] * 5 + [1, 0, 0, 0] * 5        # 37.5 %: K2 refuted under E1
    r = tmp_path / "results"
    write_model(r, "lfm3-1.7b", on, CLUSTERS)
    write_model(r, "lfm3-1.7b-nothink", off, CLUSTERS)
    write_model(r, "bielik-11b-v3.1", b_official, CLUSTERS, e1=b_e1)
    a = hypotheses.analyse(r)
    k2 = a["hypotheses"][0]
    mean, se_cl = by_hand(b_e1, CLUSTERS)
    se = max(se_cl, math.sqrt(0.1632 * 0.8368 / 288))
    assert math.isclose(k2["e1"]["z"], (mean - 0.1632) / se) and k2["e1"]["outcome_raw"] == "refuted"
    assert k2["outcome_raw"] == "supported" and k2["z"] < -2       # the official z is unchanged by E1
    assert k2["depends_on_extraction"] is True and "depends on code extraction" in k2["extraction_note"]
    assert a["group_tests"][0]["z"] == k2["z"] and a["group_tests"][0]["z_e1"] == k2["e1"]["z"]
    # E1's Holm p uses the same family with K2's p replaced
    family = [hypotheses.phi(k2["e1"]["z"]), a["hypotheses"][1]["p_support"]]
    assert math.isclose(k2["e1"]["p_support_holm"], hypotheses.holm(family)[0])
    assert "depends on code extraction" in hypotheses.report(a)
    r2 = tmp_path / "same"
    write_model(r2, "lfm3-1.7b", on, CLUSTERS)
    write_model(r2, "lfm3-1.7b-nothink", off, CLUSTERS)
    write_model(r2, "bielik-11b-v3.1", b_official, CLUSTERS, e1=[0, 0, 0, 0] * 9 + [1, 0, 0, 0])
    k2 = hypotheses.analyse(r2)["hypotheses"][0]
    assert k2["depends_on_extraction"] is False and k2["e1"]["outcome_raw"] == k2["outcome_raw"] == "supported"


def test_holm_and_verdicts():
    # sorted 0.01, 0.03, 0.04, 1 -> 4 x 0.01, max(., 3 x 0.03), max(., 2 x 0.04), 1
    assert all(math.isclose(x, e) for x, e in zip(hypotheses.holm([0.01, 0.04, None, 0.03]), [0.04, 0.09, 1.0, 0.09]))
    assert hypotheses.verdict(hypotheses.phi(-3.5), 1) == "supported (clear)"
    assert hypotheses.verdict(hypotheses.phi(-2.5), 1) == "supported (likely)"
    assert hypotheses.verdict(0.5, hypotheses.phi(-2.1)) == "refuted (likely)"
    assert hypotheses.verdict(0.2, 0.8) == "undetermined"


def test_group_file_enters_holm(tmp_path):
    r = tmp_path / "results"
    on = [1, 1, 1, 0] * 10
    b = [0, 0, 0, 0] * 9 + [1, 0, 0, 0]
    write_model(r, "lfm3-1.7b", on, CLUSTERS)
    write_model(r, "lfm3-1.7b-nothink", [1, 0, 0, 0] * 10, CLUSTERS)
    write_model(r, "bielik-11b-v3.1", b, CLUSTERS)
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"group_tests": [
        {"benchmark": "livecodebench-pro-25q2", "id": "K2", "z": -5.0, "p_support": hypotheses.phi(-5.0),
         "p_refute": 1 - hypotheses.phi(-5.0), "outcome_raw": "supported"},
        {"benchmark": "livecodebench-pro-25q2", "id": "K3", "z": None, "p_support": None, "p_refute": None,
         "outcome_raw": "precondition not met"}]}))
    a = hypotheses.analyse(r, other)
    family = [t["p_support"] for t in a["holm"]["family"]]
    assert len(family) == 4 and a["holm"]["missing_counted_as_p_1"] == 1
    k2 = a["hypotheses"][0]
    assert math.isclose(k2["p_support_holm"], hypotheses.holm(family)[0])
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"group_tests": [{"benchmark": "x", "id": "K2"}]}))
    with pytest.raises(SystemExit):
        hypotheses.analyse(r, bad)


def test_changed_result_file_is_refused(tmp_path):
    r = tmp_path / "results"
    write_model(r, "lfm3-1.7b", [1, 0, 0, 0] * 10, CLUSTERS)
    with gzip.open(r / "lfm3-1.7b.jsonl.gz", "at") as f:
        f.write("\n")
    with pytest.raises(SystemExit, match="sha256"):
        hypotheses.analyse(r)


def test_raw_outputs_reads_after_the_last_think_end():
    """raw_outputs.py on a synthetic run: two `</think>` in one answer (the text after the last counts), a lone fence
    after it, a python block, a stray `</think>` with nothing after it, an unclosed ```python line alone (one fence
    line, but not a lone fence), and an unfinished answer."""
    import statistics

    def rec(step, output, passed, code, unfinished=False):
        return ({"setting": "with_background", "problem_id": "1", "step": step, "status": "ok", "output": output,
                 "unfinished": unfinished}, {"pass": passed, "output": code})
    pairs = {("with_background", "1", 1): rec(1, "a</think>```python\nx\n```\n</think>def f(): pass\n```\nprose",
                                               True, "prose"),
             ("with_background", "1", 2): rec(2, "```python\ny = 1\n```", False, "\ny = 1\n"),
             ("with_background", "1", 3): rec(3, "draft</think>", False, ""),
             ("with_background", "1", 4): rec(4, "```python\n", False, ""),
             ("with_background", "1", 5): rec(5, "reasoning, cut", False, "", unfinished=True)}
    last = {k: v[0] for k, v in pairs.items()}
    graded = {k: v[1] for k, v in pairs.items()}
    x = raw_outputs.per_setting(last, graded, "with_background")
    out1 = pairs[("with_background", "1", 1)][0]["output"]
    assert x["reasoning"] == {"answers": 5, "closing_think": 2,
                              "median_share_before_last_think_end": round(
                                  statistics.median([out1.rindex("</think>") / len(out1), 5 / 13]), 4),
                              "passed": 1, "passed_closing_think": 1}
    assert x["extraction"] == {"empty_official": 3, "empty_by_cause": {"other": ["1.3", "1.4"], "unfinished": ["1.5"]},
                               "answers_lone_fence": 1, "answers_without_fence_line": 2}
