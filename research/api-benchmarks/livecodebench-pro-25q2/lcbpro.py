"""LiveCodeBench Pro 25Q2 (`quater_2025_4_6`) with the harness's own prompt, code extraction and judge.

Runs in the venv that run.sh builds, with the pinned harness clone (and its LightCPVerifier submodule) in
`.cache/LiveCodeBench-Pro`:

    python lcbpro.py generate <out-dir> --base-url http://localhost:8000 --model <served-name>
                              --model-repo REPO@REVISION --context N [--chat-template-kwargs JSON] [--limit N]
    python lcbpro.py generate <out-dir> --chat-url https://.../v1/chat/completions --model <name>
                              --api-key-env VAR --tokenizer REPO@REVISION --context N --margin M [--limit N]
    python lcbpro.py tests <out-dir> [--limit N]                 # online; Linux scoring machine
    HF_HUB_OFFLINE=1 python lcbpro.py score <out-dir> [--limit N]  # Docker judge; Linux x86_64

`generate` (GPU box or Mac; needs a Hugging Face login with access to the gated problem set) loads the 167
problems of the pinned split, sorted by `problem_id`, writes their metadata (no statements) to
`<out-dir>/problems.json`, builds each prompt with the harness's `LLMInterface.generate_solution` (its own
`self.prompt + problem_statement`) and sends it as the only user message. Each answer is a line in
`<out-dir>/generations.jsonl` (raw output with thinking; not committed). On our vLLM (`--base-url`) the prompt is
counted by the server's `/tokenize` and the output may use the rest of the context; every request carries the
card's sampling (temperature 0.6, top_p 0.95, top_k 0, repetition_penalty 1.0, no penalties, seed). On a hosted API
(`--chat-url`, the Fabryka API for Bielik) the prompt is counted locally with the model's tokenizer and chat template
and a margin is kept; at most `--concurrency` requests run at once behind one shared pause, and every failed attempt
is a line in `<out-dir>/api-events.jsonl`. A problem that already has an answer is skipped, so an interrupted run
resumes; a request that still fails after its retries is tried once more at the end of the session, then recorded
as `error`.

`tests` downloads the test zip of each problem from the test repository at its pinned revision into the Hugging Face
cache (`HF_HOME`; run.sh uses a cache of its own), notes which problems have no zip there, writes
`<out-dir>/tests.json`, and points the cache's `refs/main` at the pinned revision. The harness's judge downloads
`{pid}.zip` without a revision; under `HF_HUB_OFFLINE=1` that call resolves `main` through `refs/main` to the
pinned files, so the judge code runs unchanged on the pinned tests.

`score` takes the text after the last `</think>`, extracts the code with the harness's `extract_longest_cpp_code`,
and judges it with the harness's `LightCPVerifierJudge` (privileged Docker, image `lightcpverifier` built from the
pinned LightCPVerifier by setup_scoring_vm.sh) with `JUDGE_WORKERS` workers. Each problem gets one category:
accepted, wrong_answer, time_limit, memory_limit, runtime_error, output_limit, compile_error (the judge's
`compile failed` error), no_code (nothing extracted), unfinished (thinking on: no `</think>`, or stopped before
`stop`), no_tests (no zip at the pinned revision), judge_error (any other judge error, retried once),
request_error (generation failed after its retries), unsupported (prompt over the context). Only the harness's
verdict `Accepted` counts as accepted. `<out-dir>/graded.jsonl` gets one line per problem, which summarize.py reads.

Provenance (provenance.py): each step records our code commit, the runner checksums and the machine in
`<out-dir>/run.json` (generation: the sampling in effect and, on vLLM, what the server reports; scoring: the judge
image id, go-judge's version, the worker count, the test revision), and the sha256 of what it wrote in
`<out-dir>/manifest.json`; the next step stops if its input no longer matches.
"""

import argparse
import datetime
import functools
import http.client
import json
import os
import shutil
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import provenance

HERE = Path(__file__).resolve().parent
HARNESS_DIR = Path(os.environ.get("LCBPRO_DIR", HERE / ".cache" / "LiveCodeBench-Pro"))
HARNESS_REPO = "https://github.com/GavinZhengOI/LiveCodeBench-Pro"
HARNESS_COMMIT = "d614eef4f95b3654bf0758c64e1194b2575850b8"
VERIFIER_COMMIT = "021d121c882e70856b66113142495e31b9fe1d80"  # the LightCPVerifier gitlink at HARNESS_COMMIT

DATA_REPO = "QAQAQAQAQ/LiveCodeBench-Pro"
DATA_REVISION = "adebffce047dddb7768a86bace6aea4f7425e3bc"
SPLIT = "quater_2025_4_6"
N_PROBLEMS = 167
TESTS_REPO = "QAQAQAQAQ/LiveCodeBench-Pro-Testcase"  # judge.LightCPVerifierJudge.DATASET_HF_REPO
TESTS_REVISION = "5257736c0a4e30ba0949d41c56a257c323d9c600"
PROBLEM_FIELDS = ("problem_id", "problem_title", "difficulty", "platform", "link", "time_limit", "memory_limit")

# PROTOCOL.md, "Settings"
TEMPERATURE = 0.6
TOP_P = 0.95
SEED = 20261122
# Sent in every vLLM request besides temperature/top_p/seed: without them vLLM 0.34.0 fills repetition_penalty 1.1
# and top_k 50 from the model's generation_config.json. top_k 0 disables the limit in vLLM 0.34.0.
VLLM_SAMPLING = {"top_k": 0, "repetition_penalty": 1.0, "frequency_penalty": 0, "presence_penalty": 0}
# Sampling parameters vLLM v0.34.0 fills from generation_config.json when a request leaves them unset.
VLLM_GENERATION_CONFIG_PARAMS = ("repetition_penalty", "presence_penalty", "frequency_penalty", "temperature", "top_k",
                                 "top_p", "min_p", "max_new_tokens", "skip_special_tokens")
API_SERVER_DEFAULTS = "unknown (Fabryka API)"

# benchmark.py's `worker` (the harness default; its README asks for at most the physical cores)
JUDGE_WORKERS = 8
JUDGE_POLL_S = 1.0
# LightCPVerifier src/gojudge.js prepareProgram: a submission that does not compile ends as `status: error` with
# this text (String(new Error(`compile failed: ...`))); checker and interactor failures say "checker compile failed"
# and "interactor compile failed", which are the judge's own and stay judge errors.
COMPILE_ERROR_PREFIX = "Error: compile failed:"
# The harness's verdict strings (go-judge statuses and the checker's Wrong Answer) and our categories.
VERDICT_CATEGORY = {
    "Accepted": "accepted",
    "Wrong Answer": "wrong_answer",
    "Time Limit Exceeded": "time_limit",
    "Memory Limit Exceeded": "memory_limit",
    "Nonzero Exit Status": "runtime_error",
    "Signalled": "runtime_error",
    "Output Limit Exceeded": "output_limit",
}
CATEGORIES = ("accepted", "wrong_answer", "time_limit", "memory_limit", "runtime_error", "output_limit",
              "compile_error", "no_code", "unfinished", "no_tests", "judge_error", "request_error", "unsupported")

THINK_START, THINK_END = "<think>", "</think>"
# After any failed attempt every request waits: 10 s, doubling up to 5 min while failures continue, back to 10 s
# after a success (ifeval/lm_eval_fabryka.py). A 4xx other than 429 is a rejected request: not retried, no pause.
PAUSE_MIN, PAUSE_MAX = 10.0, 300.0


class SetupError(RuntimeError):
    """The server answered in a shape this script does not score; the whole run stops."""


class Rejected(Exception):
    """The server refused the request (4xx other than 429); the problem is recorded as an error."""


def after_think(output: str) -> str:
    """The text after the last `</think>`; an output without `</think>` unchanged (PROTOCOL.md, "Settings")."""
    if THINK_END not in output:
        return output
    return output.rsplit(THINK_END, 1)[1]


def _git_head(path: Path) -> str | None:
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"], capture_output=True, text=True,
                              check=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def harness_path() -> None:
    """Checks the pinned clone and its submodule, then makes the harness importable from its root (judge.py takes
    `LightCPVerifier` relative to the working directory when it is imported)."""
    head = _git_head(HARNESS_DIR)
    if head != HARNESS_COMMIT:
        sys.exit(f"lcbpro.py: {HARNESS_DIR} is at {head}, expected {HARNESS_COMMIT} (run.sh checks it out)")
    sub = _git_head(HARNESS_DIR / "LightCPVerifier")
    if sub != VERIFIER_COMMIT:
        sys.exit(f"lcbpro.py: {HARNESS_DIR / 'LightCPVerifier'} is at {sub}, expected {VERIFIER_COMMIT} "
                 "(git submodule update --init)")
    os.chdir(HARNESS_DIR)
    if str(HARNESS_DIR) not in sys.path:
        sys.path.insert(0, str(HARNESS_DIR))


def harness_prompt() -> Callable[[str], str]:
    """The user message for a problem statement, made by the harness itself: `LLMInterface.generate_solution`
    builds `self.prompt + problem_statement` and hands it to `call_llm`, which here only returns it."""
    harness_path()
    import api_interface

    class Echo(api_interface.LLMInterface):
        def call_llm(self, user_prompt: str) -> tuple[str, Any]:
            return user_prompt, None

    echo = Echo()
    return lambda statement: echo.generate_solution(statement)[0]


def harness_extract() -> Callable[[str], str | None]:
    harness_path()
    import util
    return util.extract_longest_cpp_code


def load_rows() -> list[dict[str, Any]]:
    """All rows of the pinned split, sorted by problem_id. The dataset is gated: a Hugging Face login that accepted
    its terms is needed."""
    from datasets import load_dataset
    from huggingface_hub.errors import GatedRepoError

    try:
        ds = load_dataset(DATA_REPO, split=SPLIT, revision=DATA_REVISION)
    except GatedRepoError as e:
        sys.exit(f"lcbpro.py: {DATA_REPO} is gated and this Hugging Face login has no access yet: {e}")
    rows = sorted((dict(r) for r in ds), key=lambda r: r["problem_id"])
    ids = [r["problem_id"] for r in rows]
    if len(set(ids)) != len(ids) or len(ids) != N_PROBLEMS:
        sys.exit(f"lcbpro.py: {SPLIT} has {len(ids)} rows ({len(set(ids))} distinct ids), PROTOCOL.md says "
                 f"{N_PROBLEMS}")
    return rows


def problems_record(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """problems.json: the split's metadata, so that scoring needs no access to the gated statements."""
    return {"data": f"{DATA_REPO} @ {DATA_REVISION}", "split": SPLIT,
            "problems": [{k: r.get(k) for k in PROBLEM_FIELDS} for r in rows]}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class Gate:
    """One pause shared by all requests (`pause_min` doubling to `pause_max` after failures, reset by a success)."""

    def __init__(self, pause_min: float = PAUSE_MIN, pause_max: float = PAUSE_MAX) -> None:
        self.lock = threading.Lock()
        self.resume_at = 0.0
        self.pause_min, self.pause_max = pause_min, pause_max
        self.pause = pause_min

    def wait(self) -> None:
        while True:
            with self.lock:
                delay = self.resume_at - time.monotonic()
            if delay <= 0:
                return
            time.sleep(delay)

    def failed(self) -> float:
        """Pauses all requests for the current pause and doubles it; returns the pause applied, in seconds."""
        with self.lock:
            pause = self.pause
            self.resume_at = max(self.resume_at, time.monotonic() + pause)
            self.pause = min(2 * self.pause, self.pause_max)
            return pause

    def succeeded(self) -> None:
        with self.lock:
            self.pause = self.pause_min


def event_counts(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Totals of api-events.jsonl lines: by action, by HTTP status (`none` for a broken connection), problems hit."""
    def tally(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in events:
            k = "none" if e.get(key) is None else str(e[key])
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))

    return {"events": len(events), "by_action": tally("action"), "by_status": tally("status"),
            "problems": len({e.get("problem") for e in events if e.get("problem") is not None})}


class EventLog:
    """Every failed request attempt, and each success after a failure, one json line in `path`: UTC time, problem,
    endpoint, attempt, HTTP status (null for a broken connection), the short error text, what happened
    (`retry` after `pause_s`, `gave_up`, `rejected`, `stop`, `recovered`). Kept as evidence for the API's operators."""

    def __init__(self, path: Path | None = None) -> None:
        self.path, self.lock, self.events = path, threading.Lock(), []
        if path is not None:
            path.touch()

    def write(self, **event: Any) -> None:
        event = {"time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds"), **event}
        with self.lock:
            self.events.append(event)
            if self.path is not None:
                with self.path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def counts(self) -> dict[str, Any]:
        with self.lock:
            return event_counts(self.events)


@dataclass
class Server:
    """Where the requests go. vLLM (`tokenize_url` set) counts the prompt with the served template; a hosted API
    (`count` set) gets the prompt counted locally and a margin for what its own rendering adds."""
    model: str
    chat_url: str
    retries: int
    timeout: float
    headers: dict[str, str] = field(default_factory=dict)
    tokenize_url: str | None = None
    template_kwargs: dict[str, Any] | None = None
    count: Callable[[list[dict[str, str]]], int] | None = None
    context: int = 0
    margin: int = 0
    model_repo: str | None = None  # vLLM: REPO@REVISION it serves, whose generation_config.json sets its defaults
    events: EventLog = field(default_factory=EventLog)
    gate: Gate = field(default_factory=Gate)


def thinking(server: Server) -> str:
    """`on` (vLLM, template default), `off` (vLLM with enable_thinking false) or `none` (hosted API, no switch)."""
    if not server.tokenize_url:
        return "none"
    return "off" if (server.template_kwargs or {}).get("enable_thinking") is False else "on"


@functools.cache
def tls_context() -> ssl.SSLContext:
    """certifi's CA bundle: the python.org Python on macOS has no system certificates for urllib."""
    import certifi
    return ssl.create_default_context(cafile=certifi.where())


def post(url: str, body: dict[str, Any], timeout: float, headers: dict[str, str]) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json", **headers})
    context = tls_context() if url.startswith("https:") else None
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def post_with_retries(server: Server, url: str, body: dict[str, Any], problem: str | None = None) -> dict[str, Any]:
    """Up to `server.retries` attempts for server errors, 429 and broken connections (a reset or a body cut short),
    each failure pausing all requests; 401/403 stop the run (SetupError), any other 4xx raises Rejected at once.
    Every failure goes to `server.events`."""
    endpoint = urllib.parse.urlsplit(url).path

    def log(attempt: int, status: int | None, error: str, action: str, pause: float | None = None) -> None:
        server.events.write(problem=problem, endpoint=endpoint, attempt=attempt, status=status,
                            error=error[:300], action=action, pause_s=pause)

    for attempt in range(1, server.retries + 1):
        server.gate.wait()
        try:
            response = post(url, body, server.timeout, server.headers)
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            if e.code in (401, 403):  # a wrong or missing key fails every request the same way
                log(attempt, e.code, text, "stop")
                raise SetupError(f"HTTP {e.code} from {url}: check the API key") from e
            if e.code != 429 and e.code < 500:
                log(attempt, e.code, text, "rejected")
                raise Rejected(f"HTTP {e.code}: {text[:500]}") from e
            pause = server.gate.failed()
            log(attempt, e.code, text, "gave_up" if attempt == server.retries else "retry", pause)
            if attempt == server.retries:
                raise
        except (urllib.error.URLError, http.client.IncompleteRead, TimeoutError, ConnectionError) as e:
            if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
                log(attempt, None, repr(e), "stop")
                raise SetupError(f"TLS certificate check failed for {url}: {e}") from e
            pause = server.gate.failed()
            log(attempt, None, repr(e), "gave_up" if attempt == server.retries else "retry", pause)
            if attempt == server.retries:
                raise
        else:
            server.gate.succeeded()
            if attempt > 1:
                log(attempt, None, "", "recovered")
            return response
    raise AssertionError("unreachable")


def local_counter(spec: str) -> Callable[[list[dict[str, str]]], int]:
    """Prompt tokens with the model's own tokenizer and chat template (`REPO@REVISION`), at the template defaults,
    as the API renders them. Gated repos need a Hugging Face login with the licence accepted."""
    from huggingface_hub import get_token
    from transformers import AutoTokenizer

    repo, _, revision = spec.partition("@")
    if get_token() is None:
        sys.exit(f"lcbpro.py: the tokenizer of {repo} is gated; log in first (`hf auth login`) with an account that "
                 "accepted its licence on Hugging Face")
    try:
        tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision)
    except OSError as e:  # transformers reports a gated or missing repo as OSError
        sys.exit(f"lcbpro.py: cannot load the tokenizer of {repo} @ {revision}: {e}")
    lock = threading.Lock()

    def count(messages: list[dict[str, str]]) -> int:
        with lock:
            return len(tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True))

    return count


def request_body(server: Server, messages: list[dict[str, str]], max_tokens: int) -> dict[str, Any]:
    if server.tokenize_url:
        extra = {"chat_template_kwargs": server.template_kwargs} if server.template_kwargs else {}
        return {"model": server.model, "messages": messages, "n": 1, "temperature": TEMPERATURE, "top_p": TOP_P,
                "max_tokens": max_tokens, "seed": SEED, **VLLM_SAMPLING, **extra}
    # Only the fields the Fabryka API accepted in the IFEval and LiveCodeBench v6 runs (no `n`, penalties, `stop`,
    # top_k or template switches).
    return {"model": server.model, "messages": messages, "temperature": TEMPERATURE, "top_p": TOP_P,
            "max_tokens": max_tokens, "seed": SEED}


def vllm_defaults(generation_config: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    """What vLLM v0.34.0 takes from `generation_config` for a request with `body`: the parameters it reads from the
    file (non-null), minus those the request sets itself; `max_new_tokens` is vLLM's `max_tokens`."""
    taken = {p: generation_config[p] for p in VLLM_GENERATION_CONFIG_PARAMS if generation_config.get(p) is not None}
    if "max_new_tokens" in taken:
        taken["max_tokens"] = taken.pop("max_new_tokens")
    return {p: v for p, v in taken.items() if p not in body}


def generation_config(model_repo: str) -> dict[str, Any]:
    """The model's generation_config.json at the pinned revision (`REPO@REVISION`), as vLLM reads it."""
    from huggingface_hub import hf_hub_download

    repo, _, revision = model_repo.partition("@")
    return json.loads(Path(hf_hub_download(repo, "generation_config.json", revision=revision)).read_text("utf-8"))


def sampling(server: Server) -> dict[str, Any]:
    """The sampling settings in effect: what the request sends, what the server fills in for the rest, and on vLLM
    the two merged (a value in the request overrides the server default)."""
    body = request_body(server, [], 0)
    sent = {k: v for k, v in body.items() if k not in ("model", "messages", "max_tokens", "chat_template_kwargs")}
    record: dict[str, Any] = {"request_sampling": sent, "chat_template_kwargs": server.template_kwargs,
                              "thinking": thinking(server)}
    if not server.tokenize_url:
        return {**record, "server_defaults": API_SERVER_DEFAULTS}
    if not server.model_repo:
        raise SetupError("vLLM generation needs --model-repo REPO@REVISION to record the sampling defaults")
    defaults = vllm_defaults(generation_config(server.model_repo), body)
    return {**record, "server_defaults": defaults,
            "server_defaults_source": f"vLLM generation_config=auto: {server.model_repo} generation_config.json",
            "effective": {**defaults, **sent}}


def server_info(base_url: str) -> dict[str, Any]:
    """vLLM's `/version` and `/v1/models` (what a reused server reports it serves); an error is recorded, not fatal."""
    info: dict[str, Any] = {"base_url": base_url}
    for key, path in (("version", "/version"), ("models", "/v1/models")):
        try:
            with urllib.request.urlopen(f"{base_url}{path}", timeout=30) as response:
                info[key] = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:
            info[key] = {"error": repr(e)}
    return info


def answer(server: Server, messages: list[dict[str, str]], problem: str | None = None) -> dict[str, Any]:
    """One sample for one prompt; output limited only by the context (max_tokens = context - prompt tokens, minus
    the margin for a hosted API)."""
    extra = {"chat_template_kwargs": server.template_kwargs} if server.template_kwargs else {}
    if server.tokenize_url:
        tokens = post_with_retries(server, server.tokenize_url,
                                   {"model": server.model, "messages": messages, "add_generation_prompt": True, **extra},
                                   problem)
        served = int(tokens["max_model_len"])
        if server.context and served < server.context:
            raise SetupError(f"the server's max_model_len is {served}, below the protocol's context {server.context}")
        prompt_tokens, context = int(tokens["count"]), server.context or served
    else:
        assert server.count is not None
        prompt_tokens, context = server.count(messages), server.context
    record: dict[str, Any] = {"prompt_tokens": prompt_tokens, "context": context}
    max_tokens = context - prompt_tokens - server.margin
    if max_tokens < 1:
        return {**record, "status": "unsupported",
                "error": f"prompt has {prompt_tokens} tokens (margin {server.margin}), the context is {context}"}
    body = request_body(server, messages, max_tokens)
    response = post_with_retries(server, server.chat_url, body, problem)
    choice = response["choices"][0]
    message = choice["message"]
    if message.get("reasoning_content") or message.get("reasoning"):
        raise SetupError("the server returned reasoning in a separate field, which this script does not score; "
                         "the content must hold the whole output (vLLM: serve without --reasoning-parser)")
    usage = response["usage"]
    result = {**record, "status": "ok", "max_tokens": max_tokens, "output": message.get("content") or "",
              "finish_reason": choice["finish_reason"], "output_tokens": int(usage["completion_tokens"])}
    if not server.tokenize_url:
        result["api_prompt_tokens"] = usage.get("prompt_tokens")  # the API's own count, to check the margin
    return result


def server_from(args: argparse.Namespace) -> Server:
    if bool(args.base_url) == bool(args.chat_url):
        sys.exit("lcbpro.py generate: give exactly one of --base-url (vLLM) and --chat-url (hosted API)")
    if args.base_url:
        kwargs = json.loads(args.chat_template_kwargs) if args.chat_template_kwargs else None
        return Server(model=args.model, chat_url=f"{args.base_url}/v1/chat/completions", retries=args.retries,
                      timeout=args.request_timeout, tokenize_url=f"{args.base_url}/tokenize", template_kwargs=kwargs,
                      model_repo=args.model_repo or None, context=args.context)
    if args.chat_template_kwargs:
        sys.exit("lcbpro.py generate: a hosted API takes no --chat-template-kwargs")
    if not (args.api_key_env and args.tokenizer and args.context):
        sys.exit("lcbpro.py generate: --chat-url needs --api-key-env, --tokenizer and --context")
    key = os.environ.get(args.api_key_env)
    if not key:
        sys.exit(f"lcbpro.py generate: set {args.api_key_env}")
    return Server(model=args.model, chat_url=args.chat_url, retries=args.retries, timeout=args.request_timeout,
                  headers={"Authorization": f"Bearer {key}"}, count=local_counter(args.tokenizer),
                  context=args.context, margin=args.margin)


def update_run(out: Path, key: str, value: dict[str, Any]) -> None:
    """`<out>/run.json`: `generation` is a list (one entry per `generate`, as a run may resume elsewhere; key
    `generation_end` adds `value` to the last entry), `tests` and `scoring` the last such step."""
    path = out / "run.json"
    run = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"generation": []}
    if key == "generation":
        run["generation"].append(value)
    elif key == "generation_end":
        run["generation"][-1].update(value)
    else:
        run[key] = value
    path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")


def write_problems(out: Path, rows: list[dict[str, Any]]) -> None:
    """problems.json, written once; a resumed run must see the same problem set."""
    path = out / "problems.json"
    record = problems_record(rows)
    if path.is_file():
        provenance.verify(out, ["problems.json"], "lcbpro.py generate")
        if json.loads(path.read_text(encoding="utf-8")) != record:
            sys.exit(f"lcbpro.py: {path} lists other problems than {DATA_REPO} @ {DATA_REVISION} {SPLIT} now")
        return
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance.record(out, ["problems.json"], "lcbpro.py generate")


SLAYER_CONTEXT = 4096
SLAYER_MIN_ANSWER_TOKENS = 256


def load_slayer(pretrained: str, device: str = "cpu", dtype: str = "bfloat16"):
    common = HERE.parents[1] / "common"
    if str(common) not in sys.path:
        sys.path.insert(0, str(common))
    import torch  # noqa: E402
    import slayer_model  # noqa: E402

    dt = {"bfloat16": torch.bfloat16, "bf16": torch.bfloat16, "float16": torch.float16,
          "fp16": torch.float16, "float32": torch.float32, "fp32": torch.float32}.get(dtype, torch.bfloat16)
    return slayer_model.Slayer(pretrained, device=device, dtype=dt)


def slayer_generate(model: Any, prompt_ids: list[int], max_new_tokens: int) -> list[int]:
    """Batch-1 wrapper around batched greedy generation (same result as sequential)."""
    return slayer_generate_batch(model, [prompt_ids], max_new_tokens=max_new_tokens)[0]


def slayer_generate_batch(model: Any, prompt_ids_list: list[list[int]], max_new_tokens: int | None = None,
                          max_total: int = SLAYER_CONTEXT) -> list[list[int]]:
    from slayer_batch import generate_batch  # research/common on sys.path via load_slayer

    # max_new_tokens kept for compatibility; max_total enforces per-row 4096 total.
    return generate_batch(model, prompt_ids_list, max_total=max_total, stop_id=model.bos)


def _slayer_decode(model: Any, out_ids: list[int]) -> str:
    decoded = model.tok.decode(out_ids, skip_special_tokens=False)
    if decoded.startswith("<|endoftext|>"):
        decoded = decoded[len("<|endoftext|>"):]
    return decoded


def slayer_answer(model: Any, prompt: str, thinking: bool) -> dict[str, Any]:
    return slayer_answer_batch(model, [(prompt, thinking)])[0]


def slayer_answer_batch(model: Any, items: list[tuple[str, bool]]) -> list[dict[str, Any]]:
    """Batched greedy generation; identical per-row results to batch size 1.

    BOS rule: exactly one leading BOS per request (matches IFEval/SlayerLM).
    """
    encoded: list[list[int]] = []
    metas: list[dict[str, Any]] = []
    for prompt, _thinking in items:
        ids = model.encode(prompt)
        prompt_tokens = 1 + len(ids)  # one leading BOS per request
        max_new_tokens = SLAYER_CONTEXT - prompt_tokens
        meta = {"prompt_tokens": prompt_tokens, "context": SLAYER_CONTEXT, "max_tokens": max_new_tokens}
        if max_new_tokens < SLAYER_MIN_ANSWER_TOKENS:
            metas.append({**meta, "status": "unsupported",
                          "error": f"prompt has {prompt_tokens} tokens (including BOS), leaving {max_new_tokens} < "
                                   f"{SLAYER_MIN_ANSWER_TOKENS} for the answer in a {SLAYER_CONTEXT}-token context"})
            encoded.append([])
        else:
            metas.append(meta)
            encoded.append(ids)
    # Generate only supported prompts, in original order mapping.
    idx = [i for i, m in enumerate(metas) if m.get("status") != "unsupported"]
    outs: list[list[int]] = [[] for _ in items]
    if idx:
        batch_ids = [encoded[i] for i in idx]
        batch_outs = slayer_generate_batch(model, batch_ids, max_total=SLAYER_CONTEXT)
        for j, i in enumerate(idx):
            outs[i] = batch_outs[j]
    records: list[dict[str, Any]] = []
    for i, meta in enumerate(metas):
        if meta.get("status") == "unsupported":
            records.append(meta)
            continue
        out_ids = outs[i]
        finish_reason = "stop" if (out_ids and out_ids[-1] == model.bos) else "length"
        decoded_ids = out_ids[:-1] if (out_ids and out_ids[-1] == model.bos) else out_ids
        records.append({"status": "ok", "prompt_tokens": meta["prompt_tokens"], "context": SLAYER_CONTEXT,
                        "max_tokens": meta["max_tokens"], "output": _slayer_decode(model, decoded_ids),
                        "finish_reason": finish_reason, "output_tokens": len(out_ids)})
    return records


def slayer_sampling(pretrained: str) -> dict[str, Any]:
    return {"request_sampling": {"temperature": 0, "top_p": 1, "greedy": True, "seed": None},
            "server_defaults": "none (local Slayer greedy generation)",
            "slayer_pretrained": pretrained, "slayer_loader": "research/common/slayer_lm.py (slayer_model.Slayer)",
            "dtype": "bfloat16", "context": SLAYER_CONTEXT, "thinking": False}


def generate(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    gen_path = out / "generations.jsonl"
    events_path = out / "api-events.jsonl"
    if gen_path.is_file():  # resuming: the answers (and the event log) kept must be the ones the earlier run wrote
        logged = ["api-events.jsonl"] if "api-events.jsonl" in provenance.read_manifest(out)["files"] else []
        provenance.verify(out, ["generations.jsonl", *logged], "lcbpro.py generate")

    prompt = harness_prompt()
    rows = load_rows()
    write_problems(out, rows)
    done = {r["problem_id"] for r in read_jsonl(gen_path) if r["status"] != "error"}

    if args.slayer_pretrained:
        slayer = load_slayer(args.slayer_pretrained, device=args.slayer_device, dtype=args.slayer_dtype)
        args.concurrency = 1
        batch_size = max(1, int(getattr(args, "slayer_batch_size", 8)))
        run_sampling = {**slayer_sampling(args.slayer_pretrained), "slayer_batch_size": batch_size}
        update_run(out, "generation", {**provenance.step("lcbpro.py generate"), "model": args.model,
                                       "limit": args.limit, "harness": f"{HARNESS_REPO} @ {HARNESS_COMMIT}",
                                       "data": f"{DATA_REPO} @ {DATA_REVISION}, {SPLIT}", "sampling": run_sampling})
        todo = [(r["problem_id"], prompt(r["problem_statement"]))
                for r in (rows[:args.limit] if args.limit else rows) if r["problem_id"] not in done]
        del rows
        print(f"lcbpro.py: {len(done)} problems already answered, {len(todo)} to go, slayer_batch_size={batch_size}",
              flush=True)

        def write_record(problem_id: str, started: datetime.datetime, record: dict[str, Any]) -> dict[str, Any]:
            record = {"problem_id": problem_id, "model": args.model, "started": started.isoformat(),
                      "seconds": round(time.time() - started.timestamp(), 1), **record}
            with gen_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"{problem_id}: {record['status']} {record.get('output_tokens', '')} {record.get('finish_reason', '')}"
                  f" {record['seconds']} s", flush=True)
            return record

        try:
            for i in range(0, len(todo), batch_size):
                chunk = todo[i:i + batch_size]
                started = datetime.datetime.now(datetime.timezone.utc)
                try:
                    records = slayer_answer_batch(slayer, [(text, False) for _, text in chunk])
                except Exception as e:  # noqa: BLE001
                    records = [{"status": "error", "error": repr(e)} for _ in chunk]
                for (problem_id, _), rec in zip(chunk, records):
                    write_record(problem_id, started, rec)
        finally:
            if gen_path.is_file():
                provenance.record(out, ["generations.jsonl"], "lcbpro.py generate")
        return

    server = server_from(args)
    server.events = EventLog(events_path)
    update_run(out, "generation", {**provenance.step("lcbpro.py generate"), "model": args.model, "limit": args.limit,
                                   "harness": f"{HARNESS_REPO} @ {HARNESS_COMMIT}",
                                   "data": f"{DATA_REPO} @ {DATA_REVISION}, {SPLIT}",
                                   "sampling": globals()["sampling"](server),
                                   **({"server": server_info(args.base_url)} if args.base_url else {})})
    todo = [(r["problem_id"], [{"role": "user", "content": prompt(r["problem_statement"])}])
            for r in (rows[:args.limit] if args.limit else rows) if r["problem_id"] not in done]
    del rows
    print(f"lcbpro.py: {len(done)} problems already answered, {len(todo)} to go", flush=True)
    lock = threading.Lock()

    def run(item: tuple[str, list[dict[str, str]]]) -> dict[str, Any]:
        problem_id, messages = item
        started = datetime.datetime.now(datetime.timezone.utc)
        try:
            record = answer(server, messages, problem_id)
        except (Rejected, urllib.error.URLError, http.client.IncompleteRead, TimeoutError, ConnectionError, KeyError,
                ValueError) as e:
            record = {"status": "error", "error": repr(e)}
        record = {"problem_id": problem_id, "model": args.model, "started": started.isoformat(),
                  "seconds": round(time.time() - started.timestamp(), 1), **record}
        with lock, gen_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"{problem_id}: {record['status']} {record.get('output_tokens', '')} {record.get('finish_reason', '')}"
              f" {record['seconds']} s", flush=True)
        return record

    try:
        with ThreadPoolExecutor(args.concurrency) as pool:
            records = [f.result() for f in [pool.submit(run, item) for item in todo]]
        # PROTOCOL.md, "Settings": an infrastructure failure is retried once; if it persists it stays an error.
        again = [item for item, r in zip(todo, records) if r["status"] == "error"]
        if again:
            print(f"lcbpro.py: retrying {len(again)} failed requests once", flush=True)
            with ThreadPoolExecutor(args.concurrency) as pool:
                for f in [pool.submit(run, item) for item in again]:
                    f.result()
    finally:  # also after an interrupted run, so that a resumed one can check what it keeps
        update_run(out, "generation_end", {"api_events": server.events.counts()})
        provenance.record(out, ["api-events.jsonl"], "lcbpro.py generate")
        if gen_path.is_file():
            provenance.record(out, ["generations.jsonl"], "lcbpro.py generate")


def read_problems(out: Path, limit: int | None, reader: str) -> list[dict[str, Any]]:
    provenance.verify(out, ["problems.json"], reader)
    problems = json.loads((out / "problems.json").read_text(encoding="utf-8"))["problems"]
    return problems[:limit] if limit else problems


def tests_cache_dir() -> Path:
    from huggingface_hub import constants
    return Path(constants.HF_HUB_CACHE) / ("datasets--" + TESTS_REPO.replace("/", "--"))


def tests(args: argparse.Namespace) -> None:
    """Downloads the pinned test zips of the problems into the Hugging Face cache, records which are missing, and
    points `refs/main` of the cached test repository at the pinned revision."""
    from huggingface_hub import HfApi, hf_hub_download

    out = Path(args.out_dir).resolve()
    problems = read_problems(out, args.limit, "lcbpro.py tests")
    available = set(HfApi().list_repo_files(TESTS_REPO, repo_type="dataset", revision=TESTS_REVISION))

    def fetch(pid: str) -> tuple[str, dict[str, Any] | None]:
        name = f"{pid}.zip"
        if name not in available:
            return pid, None
        path = Path(hf_hub_download(TESTS_REPO, name, repo_type="dataset", revision=TESTS_REVISION))
        return pid, {"sha256": provenance.sha256_file(path), "bytes": path.stat().st_size}

    with ThreadPoolExecutor(8) as pool:
        files = dict(pool.map(fetch, [p["problem_id"] for p in problems]))
    refs = tests_cache_dir() / "refs"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "main").write_text(TESTS_REVISION, encoding="utf-8")
    missing = sorted(pid for pid, f in files.items() if f is None)
    (out / "tests.json").write_text(json.dumps({"repo": TESTS_REPO, "revision": TESTS_REVISION, "files": files,
                                                "missing": missing}, indent=2) + "\n", encoding="utf-8")
    provenance.record(out, ["tests.json"], "lcbpro.py tests")
    update_run(out, "tests", {**provenance.step("lcbpro.py tests"), "limit": args.limit, "repo": TESTS_REPO,
                              "revision": TESTS_REVISION,
                              "tests_json_sha256": provenance.read_manifest(out)["files"]["tests.json"]["sha256"],
                              "missing": missing})
    print(f"lcbpro.py: {len(files) - len(missing)} test zips at {TESTS_REVISION}, missing: {missing or 'none'}")


def is_unfinished(answer_record: dict[str, Any], think: str) -> bool:
    """PROTOCOL.md, "Settings": with thinking on, an answer without `</think>` or stopped by the length limit."""
    return think == "on" and (answer_record["finish_reason"] != "stop" or THINK_END not in answer_record["output"])


def prejudge(answer_record: dict[str, Any], think: str, extract: Callable[[str], str | None]
             ) -> tuple[str | None, str | None]:
    """(category, None) for an answer that never reaches the judge, else (None, code)."""
    if answer_record["status"] == "error":
        return "request_error", None
    if answer_record["status"] == "unsupported":
        return "unsupported", None
    if is_unfinished(answer_record, think):
        return "unfinished", None
    code = extract(after_think(answer_record["output"]))
    if code is None:
        return "no_code", None
    return None, code


def judged(verdict: str, full: dict[str, Any] | None) -> dict[str, Any]:
    """Our record of one judge verdict (the harness's `get_result` string) and the judge's full result.json."""
    full = full or {}
    record: dict[str, Any] = {"verdict": verdict, "accepted": verdict == "Accepted"}
    if verdict == "Judge Failed":
        error = str(full.get("error") or "")
        record["judge_error"] = error[:2000]
        record["category"] = "compile_error" if error.startswith(COMPILE_ERROR_PREFIX) else "judge_error"
        return record
    record["category"] = VERDICT_CATEGORY.get(verdict, "judge_error")
    cases = full.get("cases") or []
    record["cases_run"] = len(cases)
    record["max_time_ns"] = max((c.get("time") or 0 for c in cases), default=None)
    if record["category"] != "accepted" and cases:
        record["judge_message"] = str(cases[-1].get("msg") or "")[:500]
    return record


def judge_all(judge: Any, cpp: Any, not_found: type[Exception], todo: dict[str, str],
              fetch: Callable[[int], dict[str, Any] | None], poll: float = JUDGE_POLL_S) -> dict[str, dict[str, Any]]:
    """Submits every (problem, code) to the harness's judge and waits for each verdict; a judge error that is not a
    compile error is submitted once more (PROTOCOL.md, "Settings")."""
    results: dict[str, dict[str, Any]] = {}
    attempts = dict.fromkeys(todo, 0)
    pending = dict(todo)
    for _ in range(2):
        sids: dict[str, int] = {}
        for pid, code in pending.items():
            attempts[pid] += 1
            try:
                sids[pid] = judge.submit(pid, cpp, code)
            except not_found as e:
                results[pid] = {"verdict": None, "accepted": False, "category": "no_tests", "judge_error": repr(e)}
            except Exception as e:  # the judge's own failure (container, network): an infrastructure error
                results[pid] = {"verdict": None, "accepted": False, "category": "judge_error", "judge_error": repr(e)}
        for pid, sid in sids.items():
            while (verdict := judge.get_result(sid)) == "Judging":
                time.sleep(poll)
            results[pid] = {**judged(verdict, fetch(sid)), "submission_id": sid}
            print(f"{pid}: {results[pid]['category']}", flush=True)
        pending = {pid: todo[pid] for pid in pending if results[pid]["category"] == "judge_error"}
        if not pending:
            break
    for pid in results:
        results[pid]["judge_attempts"] = attempts[pid]
    return results


def check_pinned_tests(tests_record: dict[str, Any]) -> None:
    """The judge's revision-less download must resolve to the pinned tests: offline, with refs/main at the pin."""
    from huggingface_hub import constants

    if not constants.HF_HUB_OFFLINE:
        sys.exit("lcbpro.py score: set HF_HUB_OFFLINE=1, so that the judge's hf_hub_download (no revision) reads the "
                 "pinned test zips from the cache instead of the repository's current main")
    ref = tests_cache_dir() / "refs" / "main"
    if not ref.is_file() or ref.read_text(encoding="utf-8").strip() != TESTS_REVISION:
        sys.exit(f"lcbpro.py score: {ref} does not point at {TESTS_REVISION}; run `lcbpro.py tests` first")
    if tests_record["revision"] != TESTS_REVISION:
        sys.exit(f"lcbpro.py score: tests.json is for {tests_record['revision']}, not {TESTS_REVISION}")


def fresh_problems_dir(problems_dir: Path) -> None:
    """The judge skips the download when `problems/<pid>/config.yaml` exists; a directory filled from another test
    revision (or from before the pin) is emptied first."""
    marker = problems_dir / ".tests_revision"
    if marker.is_file() and marker.read_text(encoding="utf-8").strip() == TESTS_REVISION:
        return
    if problems_dir.exists():
        shutil.rmtree(problems_dir)
    problems_dir.mkdir(parents=True)
    marker.write_text(TESTS_REVISION, encoding="utf-8")


def judge_environment(judge: Any) -> dict[str, Any]:
    """The judge image (id and digests: its Dockerfile pulls go-judge "latest") and go-judge's version."""
    image = judge.docker_client.images.get(judge.IMAGE_NAME)
    try:
        code, output = judge.container.exec_run(["/usr/local/bin/go-judge", "-version"])
        version = output.decode("utf-8", "replace").strip() if code == 0 else f"exit {code}: {output[:200]!r}"
    except Exception as e:  # recorded, not fatal
        version = repr(e)
    return {"image": judge.IMAGE_NAME, "image_id": image.id, "image_repo_digests": image.attrs.get("RepoDigests"),
            "image_created": image.attrs.get("Created"), "go_judge_version": version, "workers": JUDGE_WORKERS}


def score(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    problems = read_problems(out, args.limit, "lcbpro.py score")
    provenance.verify(out, ["generations.jsonl", "tests.json"], "lcbpro.py score")
    tests_record = json.loads((out / "tests.json").read_text(encoding="utf-8"))
    check_pinned_tests(tests_record)
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))
    modes = {g["sampling"]["thinking"] for g in run["generation"]}
    if len(modes) != 1:
        sys.exit(f"lcbpro.py score: the generation sessions ran in different thinking modes: {modes}")
    think = modes.pop()
    answers = {r["problem_id"]: r for r in read_jsonl(out / "generations.jsonl")}  # the last record wins
    missing = [p["problem_id"] for p in problems if p["problem_id"] not in answers]
    if missing:
        sys.exit(f"lcbpro.py score: {len(missing)} problems have no answer yet (first: {missing[0]}); run generate")
    untested = [p["problem_id"] for p in problems if p["problem_id"] not in tests_record["files"]]
    if untested:
        sys.exit(f"lcbpro.py score: tests.json does not cover {untested[0]} ({len(untested)}); run lcbpro.py tests")
    extract = harness_extract()
    import requests
    from judge import LightCPVerifierJudge, ProblemNotFoundError, SupportedLanguage

    records: dict[str, dict[str, Any]] = {}
    todo: dict[str, str] = {}
    for p in problems:
        pid = p["problem_id"]
        category, code = prejudge(answers[pid], think, extract)
        if category is None and tests_record["files"][pid] is None:
            category = "no_tests"
        if category is not None:
            records[pid] = {"verdict": None, "accepted": False, "category": category, "code": code}
        else:
            records[pid] = {"code": code}
            todo[pid] = code
    fresh_problems_dir(Path(LightCPVerifierJudge.PROBLEMS_DIR))
    started = datetime.datetime.now(datetime.timezone.utc)
    with LightCPVerifierJudge(worker=JUDGE_WORKERS) as judge:
        environment = judge_environment(judge)

        def fetch(sid: int) -> dict[str, Any] | None:
            response = requests.get(f"{judge.base_url}/result/{sid}", timeout=60)
            return response.json() if response.status_code == 200 else None

        for pid, r in judge_all(judge, SupportedLanguage.CPP, ProblemNotFoundError, todo, fetch).items():
            records[pid].update(r)
    seconds = round((datetime.datetime.now(datetime.timezone.utc) - started).total_seconds(), 1)
    with (out / "graded.jsonl").open("w", encoding="utf-8") as f:
        for p in problems:
            a, g = answers[p["problem_id"]], records[p["problem_id"]]
            f.write(json.dumps({
                **{k: p.get(k) for k in PROBLEM_FIELDS}, "status": a["status"], "finish_reason": a.get("finish_reason"),
                "unfinished": g["category"] == "unfinished", "think_in_output": THINK_START in (a.get("output") or ""),
                "prompt_tokens": a.get("prompt_tokens"), "output_tokens": a.get("output_tokens"),
                "context": a.get("context"), "max_tokens": a.get("max_tokens"),
                "api_prompt_tokens": a.get("api_prompt_tokens"), "error": a.get("error"), "started": a.get("started"),
                "has_tests": tests_record["files"][p["problem_id"]] is not None,
                **{k: g.get(k) for k in ("category", "accepted", "verdict", "judge_error", "judge_message",
                                         "cases_run", "max_time_ns", "judge_attempts", "code")},
            }, ensure_ascii=False) + "\n")
    provenance.record(out, ["graded.jsonl"], "lcbpro.py score")
    update_run(out, "scoring", {**provenance.step("lcbpro.py score"), "limit": args.limit, "thinking": think,
                                "judge": environment, "judge_seconds": seconds,
                                "tests": f"{TESTS_REPO} @ {TESTS_REVISION}",
                                "harness": f"{HARNESS_REPO} @ {HARNESS_COMMIT}, LightCPVerifier @ {VERIFIER_COMMIT}"})
    counts: dict[str, int] = {}
    for g in records.values():
        counts[g["category"]] = counts.get(g["category"], 0) + 1
    print(f"lcbpro.py: graded {len(problems)} problems in {seconds} s: {counts} -> {out / 'graded.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("out_dir")
    g.add_argument("--base-url", default="", help="our vLLM server (counts the prompt through its /tokenize)")
    g.add_argument("--chat-url", default="", help="a hosted API's chat completions URL")
    g.add_argument("--model-repo", default="", help="vLLM: REPO@REVISION served, to record its sampling defaults")
    g.add_argument("--model", required=True)
    g.add_argument("--limit", type=int)
    g.add_argument("--chat-template-kwargs", default="")
    g.add_argument("--api-key-env", default="", help="hosted API: environment variable with the key")
    g.add_argument("--tokenizer", default="", help="hosted API: REPO@REVISION of the model's tokenizer and template")
    g.add_argument("--context", type=int, default=0,
                   help="context window in tokens: hosted API (required), or vLLM (the protocol's, at most the "
                        "server's max_model_len; default the server's)")
    g.add_argument("--margin", type=int, default=0, help="hosted API: tokens kept free beyond the local prompt count")
    g.add_argument("--retries", type=int, default=3, help="attempts per request")
    g.add_argument("--concurrency", type=int, default=int(os.environ.get("CONCURRENCY", "64")))
    g.add_argument("--request-timeout", type=float, default=float(os.environ.get("REQUEST_TIMEOUT", "21600")))
    g.add_argument("--slayer-pretrained", default="",
                   help="local Slayer checkpoint directory (config.json, tokenizer.json, model.safetensors); plain-text "
                        "greedy generation, no chat template, context 4096")
    g.add_argument("--slayer-device", default="cuda", help="device for local Slayer generation (cuda or cpu)")
    g.add_argument("--slayer-dtype", default="bfloat16", help="dtype for local Slayer generation (bfloat16, float16, float32)")
    g.add_argument("--slayer-batch-size", type=int, default=8,
                   help="batched greedy generation for local Slayer (same per-row result as batch size 1)")
    for name in ("tests", "score"):
        s = sub.add_parser(name)
        s.add_argument("out_dir")
        s.add_argument("--limit", type=int)
    args = parser.parse_args()
    {"generate": generate, "tests": tests, "score": score}[args.command](args)


if __name__ == "__main__":
    main()
