"""SciCode generation with SciCode's own prompt builder, code extraction and code files, and scoring with its
unchanged `eval/scripts/test_generated_code.py`.

Runs with the pinned clone in `.cache/SciCode` (run.sh makes it):

    python scicode_runner.py generate <out-dir> --base-url http://localhost:8000 --model <served-name>
                             --model-id <model-id> --model-repo REPO@REVISION --context N [--thinking]
                             [--chat-template-kwargs JSON] [--limit N]
    python scicode_runner.py generate <out-dir> --chat-url https://.../v1/chat/completions --model <name>
                             --model-id <model-id> --api-key-env VAR --tokenizer REPO@REVISION --context N
                             --margin M [--retries R] [--limit N]
    python scicode_runner.py generate <out-dir> --oracle --model-id dev-ground-truth --split validation
    python scicode_runner.py prefetch                (scoring container, with network)
    python scicode_runner.py score <out-dir> --model-id <model-id> [--split S] [--limit N]
                                                     (scoring container, without network)

`generate` runs SciCode's `Gencode.generate_response_with_steps` (eval/scripts/gencode.py) for every subproblem in
step order, in both prompt settings (with background: `multistep_template.txt`; without: `background_comment_template.txt`),
skipping 13.6, 62.1 and 76.3 as gencode's `main` does. Gencode builds each prompt from the model's own extracted code
for the earlier steps and writes `<out-dir>/generated_code/<model-id>/<setting>/<problem>.<step>.py` with
`save_response_with_steps`; the only thing replaced is the model call (`gencode.get_model_function`), which sends the
prompt as the only user message to our vLLM (`--base-url`) or the Fabryka API (`--chat-url`) and hands Gencode the
text after the last `</think>` (PROTOCOL.md, "Settings"). One chain (problem x setting) runs its steps in order;
chains run in parallel. Every answer is a line in `<out-dir>/generations.jsonl` (raw output with thinking, the
extracted code; not committed). A step that already has an answer is not asked again: its recorded extracted code
is what the next step receives, as in an uninterrupted run, so an interrupted run resumes; a step whose request
failed is asked again and its chain waits for it. `--oracle` answers each step with the split's
`ground_truth_code` in a ```python block instead of a model (dev split only; checks that passing is reachable).

SciCode's `scicode/gen/models.py` imports the API clients openai, anthropic, google.generativeai, config and litellm
at module load. None of them is called on this path, so `harness()` puts stub modules under those names in
`sys.modules` (only in this process) instead of installing them; a stub raises if anything calls it.

`score` runs SciCode's scorer unchanged (`python eval/scripts/test_generated_code.py`, 1800 s per step,
sequential) from a scratch copy of the pinned clone with `eval/data/test_data.h5` linked to the checked file. The
scorer loads the dataset with `load_dataset('SciCode1/SciCode', split=...)` and no revision; `prefetch` loads the
pinned revision into an otherwise empty Hugging Face cache, and `score` runs the scorer offline
(`HF_DATASETS_OFFLINE=1`), where datasets takes the only cached revision and logs its sha, which `score` checks
against the pin and records. One line per scored subproblem goes to `<out-dir>/graded.jsonl`, which summarize.py
reads. `--limit N` takes the first N problems of the split in dataset order.

PROTOCOL.md Amendment 1: `score` also rebuilds every step file from the recorded answers with extraction E1
(`e1_extract`; Gencode assembles the files, `build_e1_files`) into `<out-dir>/generated_code_e1/` and scores them
with the same scorer (logs in `score/logs_e1/`); graded.jsonl carries both verdicts. Prompts are not regenerated.

Provenance (provenance.py) as in livecodebench-v6: run.json holds each step's code commit, runner checksums,
machine and the sampling in effect; manifest.json the sha256 of each step's output, which the next step checks;
api-events.jsonl every failed request attempt and each recovery.
"""

import argparse
import datetime
import functools
import hashlib
import http.client
import importlib.util
import json
import os
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import types
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
SCICODE_DIR = Path(os.environ.get("SCICODE_DIR", HERE / ".cache" / "SciCode"))
SCICODE_COMMIT = "e3158ea011d4235245a547460d3688d7ccbf9900"

DATA_REPO = "SciCode1/SciCode"
DATA_REVISION = "4510f6a6aa27c43fad7b43da2c59602a86e88480"
# test_data.h5: the authors' Google Drive file, byte-identical at this mirror (PROTOCOL.md, "Sources")
H5_URL = ("https://huggingface.co/datasets/xantheocracy/scicode-mirror/resolve/"
          "2f903a64a1c4eb62c7c649b0caf7ecb2c0217590/test_data.h5")
H5_SHA256 = "48b0272a88b17dbd29777c217e1b4fb2b019b92e11cc2add847409db9541b890"
H5_SIZE = 1_049_345_865
H5_PATH = Path(os.environ.get("SCICODE_H5", HERE / ".cache" / "test_data.h5"))
HF_CACHE = Path(os.environ.get("SCICODE_HF_HOME", HERE / ".cache" / "hf-scoring"))

SETTINGS = ("with_background", "without_background")  # primary first (PROTOCOL.md, "Settings")
# Steps gencode's main skips: their code is supplied from eval/data/<problem>.<step>.txt (1-based steps)
HARNESS_STEPS = frozenset({("13", 6), ("62", 1), ("76", 3)})
# test_generated_code.py: STEP_NUM, DEV_STEP_NUM, and PROB_NUM - DEV_PROB_NUM, DEV_PROB_NUM
SPLIT_SIZES = {"test": {"problems": 65, "steps": 288}, "validation": {"problems": 15, "steps": 50}}
SCORER = "eval/scripts/test_generated_code.py"
SCORER_TIMEOUT_S = 1800  # per step, in the scorer's run_script
BLAS_THREADS = {k: "1" for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                                 "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}
SCORING_PACKAGES = ("numpy", "scipy", "sympy", "h5py", "matplotlib", "datasets", "huggingface-hub", "pyarrow")
# The modules scicode/gen/models.py imports at load and never uses on our path
STUBBED_MODULES = ("openai", "anthropic", "google.generativeai", "config", "litellm", "litellm.utils")

# PROTOCOL.md, "Settings"
TEMPERATURE = 0.6
TOP_P = 0.95
SEED = 20261122
# LFM3-1.7B on our vLLM: the card's sampling, sent in every request (vLLM 0.34.0 otherwise fills
# repetition_penalty 1.1 and top_k 50 from generation_config.json); top_k 0 disables the limit.
VLLM_SAMPLING = {"top_k": 0, "repetition_penalty": 1.0, "frequency_penalty": 0, "presence_penalty": 0}
VLLM_GENERATION_CONFIG_PARAMS = ("repetition_penalty", "presence_penalty", "frequency_penalty", "temperature", "top_k",
                                 "top_p", "min_p", "max_new_tokens", "skip_special_tokens")
API_SERVER_DEFAULTS = "unknown (Fabryka API)"

THINK_START, THINK_END = "<think>", "</think>"
PAUSE_MIN, PAUSE_MAX = 10.0, 300.0


class SetupError(RuntimeError):
    """The server answered in a shape this script does not handle, or the key is wrong; the whole run stops."""


class Rejected(Exception):
    """The server refused the request (4xx other than 429); the step is recorded as an error."""


def after_think(output: str) -> str:
    """The text after the last `</think>`; an output without `</think>` unchanged."""
    if THINK_END not in output:
        return output
    return output.rsplit(THINK_END, 1)[1]


def answer_text(record: dict[str, Any], thinking: bool) -> str:
    """What Gencode receives as the model's response (PROTOCOL.md, "Settings"): the text after the last `</think>`.
    With thinking on, an answer without `</think>` or stopped by the length limit is unfinished: empty text, so
    empty code. A prompt over the context (`unsupported`) also gives empty text."""
    if record["status"] != "ok":
        return ""
    if thinking and record["unfinished"]:
        return ""
    return after_think(record["output"])


def is_unfinished(output: str, finish_reason: str | None, thinking: bool) -> bool:
    """Thinking on: no `</think>` or not stopped by the model; otherwise: stopped by the length limit."""
    if thinking:
        return THINK_END not in output or finish_reason != "stop"
    return finish_reason != "stop"


class _Stub(types.ModuleType):
    """A module that exists so `import x` / `from x import y` succeed; calling anything from it raises."""

    def __getattr__(self, attr: str) -> Any:
        if attr.startswith("__"):
            raise AttributeError(attr)

        def unavailable(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError(f"{self.__name__}.{attr} is a stub (scicode_runner.harness): SciCode's API clients "
                               "are not installed and must not be called")
        return unavailable


def stub_model_clients() -> list[str]:
    """Stub modules for the API clients scicode/gen/models.py imports at load (and does not use on our path);
    a `google` package is stubbed only when none is installed. Returns the names stubbed."""
    names = list(STUBBED_MODULES)
    if importlib.util.find_spec("google") is None:
        names.insert(0, "google")
    for name in names:
        sys.modules[name] = _Stub(name)
    return names


def harness() -> Any:
    """Imports the pinned SciCode: gencode (its templates load from eval/data relative to the repo root, and
    so does the supplied code of 13.6, 62.1 and 76.3), its code extraction and its parser."""
    head = (SCICODE_DIR / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head != SCICODE_COMMIT:
        sys.exit(f"scicode_runner.py: {SCICODE_DIR} is at {head}, expected {SCICODE_COMMIT} (run.sh checks it out)")
    os.chdir(SCICODE_DIR)
    for p in (SCICODE_DIR / "eval" / "scripts", SCICODE_DIR / "src"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    stubbed = stub_model_clients()
    import gencode
    from scicode.gen import models
    from scicode.parse import parse
    return argparse.Namespace(gencode=gencode, models=models, parse=parse, stubbed=stubbed)


def load_split(split: str, limit: int | None) -> list[dict[str, Any]]:
    """The split's problems at the pinned revision, in dataset order (the order gencode's main iterates)."""
    from datasets import load_dataset

    rows = [dict(r) for r in load_dataset(DATA_REPO, split=split, revision=DATA_REVISION)]
    expected = SPLIT_SIZES[split]
    scored = len(expected_steps(rows))
    if (len(rows), scored) != (expected["problems"], expected["steps"]):
        sys.exit(f"scicode_runner.py: {split} has {len(rows)} problems and {scored} scored steps, expected "
                 f"{expected['problems']} and {expected['steps']}")
    return rows[:limit] if limit else rows


def expected_steps(rows: list[dict[str, Any]]) -> list[tuple[str, int]]:
    """(problem_id, 1-based step) of every step a model answers: all sub_steps but the three gencode supplies."""
    return [(r["problem_id"], i + 1) for r in rows for i in range(len(r["sub_steps"]))
            if (r["problem_id"], i + 1) not in HARNESS_STEPS]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def step_key(r: dict[str, Any]) -> tuple[str, str, int]:
    return r["setting"], r["problem_id"], int(r["step"])


def latest(records: list[dict[str, Any]]) -> dict[tuple[str, str, int], dict[str, Any]]:
    """The last record per (setting, problem, step): a step asked again after an error replaces the error."""
    return {step_key(r): r for r in records}


# ---------------------------------------------------------------------------------------------------------------
# Requests (as livecodebench-v6/lcb.py)

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
        with self.lock:
            pause = self.pause
            self.resume_at = max(self.resume_at, time.monotonic() + pause)
            self.pause = min(2 * self.pause, self.pause_max)
            return pause

    def succeeded(self) -> None:
        with self.lock:
            self.pause = self.pause_min


def event_counts(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Totals of api-events.jsonl lines: by action, by HTTP status (`none` for a broken connection), steps hit."""
    def tally(key: str) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in events:
            k = "none" if e.get(key) is None else str(e[key])
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))

    return {"events": len(events), "by_action": tally("action"), "by_status": tally("status"),
            "steps": len({e.get("step") for e in events if e.get("step") is not None})}


class EventLog:
    """Every failed request attempt, and each success after a failure, one json line: UTC time, step, endpoint,
    attempt, HTTP status (null for a broken connection), the short error text, what happened (`retry` after
    `pause_s`, `gave_up`, `rejected`, `stop`, `recovered`)."""

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
    model_repo: str | None = None
    events: EventLog = field(default_factory=EventLog)
    gate: Gate = field(default_factory=Gate)


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


def post_with_retries(server: Server, url: str, body: dict[str, Any], step: str | None = None) -> dict[str, Any]:
    """Up to `server.retries` attempts for server errors, 429 and broken connections (a reset or a body cut short),
    each failure pausing all requests; 401/403 stop the run (SetupError), any other 4xx raises Rejected at once."""
    endpoint = urllib.parse.urlsplit(url).path

    def log(attempt: int, status: int | None, error: str, action: str, pause: float | None = None) -> None:
        server.events.write(step=step, endpoint=endpoint, attempt=attempt, status=status, error=error[:300],
                            action=action, pause_s=pause)

    for attempt in range(1, server.retries + 1):
        server.gate.wait()
        try:
            response = post(url, body, server.timeout, server.headers)
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            if e.code in (401, 403):
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
        sys.exit(f"scicode_runner.py: the tokenizer of {repo} is gated; log in first (`hf auth login`)")
    try:
        tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision)
    except OSError as e:
        sys.exit(f"scicode_runner.py: cannot load the tokenizer of {repo} @ {revision}: {e}")
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
    # Only the fields the Fabryka API accepted in the IFEval run (no `n`, penalties, `stop` or template switches).
    return {"model": server.model, "messages": messages, "temperature": TEMPERATURE, "top_p": TOP_P,
            "max_tokens": max_tokens, "seed": SEED}


def vllm_defaults(generation_config: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    """What vLLM v0.34.0 takes from `generation_config` for a request with `body` (non-null parameters it reads,
    minus those the request sets); `max_new_tokens` is vLLM's `max_tokens`."""
    taken = {p: generation_config[p] for p in VLLM_GENERATION_CONFIG_PARAMS if generation_config.get(p) is not None}
    if "max_new_tokens" in taken:
        taken["max_tokens"] = taken.pop("max_new_tokens")
    return {p: v for p, v in taken.items() if p not in body}


def generation_config(model_repo: str) -> dict[str, Any]:
    from huggingface_hub import hf_hub_download

    repo, _, revision = model_repo.partition("@")
    return json.loads(Path(hf_hub_download(repo, "generation_config.json", revision=revision)).read_text("utf-8"))


def sampling(server: Server) -> dict[str, Any]:
    """The sampling settings in effect: what the request sends, what the server fills in for the rest, and on vLLM
    the two merged."""
    body = request_body(server, [], 0)
    sent = {k: v for k, v in body.items() if k not in ("model", "messages", "max_tokens", "chat_template_kwargs")}
    if not server.tokenize_url:
        return {"request_sampling": sent, "server_defaults": API_SERVER_DEFAULTS}
    if not server.model_repo:
        raise SetupError("vLLM generation needs --model-repo REPO@REVISION to record the sampling defaults")
    defaults = vllm_defaults(generation_config(server.model_repo), body)
    return {"request_sampling": sent, "chat_template_kwargs": server.template_kwargs, "server_defaults": defaults,
            "server_defaults_source": f"vLLM generation_config=auto: {server.model_repo} generation_config.json",
            "effective": {**defaults, **sent}}


def server_info(base_url: str) -> dict[str, Any]:
    info: dict[str, Any] = {"base_url": base_url}
    for key, path in (("version", "/version"), ("models", "/v1/models")):
        try:
            with urllib.request.urlopen(f"{base_url}{path}", timeout=30) as response:
                info[key] = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, ConnectionError, ValueError) as e:
            info[key] = {"error": repr(e)}
    return info


def ask(server: Server, messages: list[dict[str, str]], thinking: bool, step: str | None = None) -> dict[str, Any]:
    """One sample for one prompt; output limited only by the context (max_tokens = context - prompt tokens, minus
    the margin for a hosted API)."""
    if server.tokenize_url:
        extra = {"chat_template_kwargs": server.template_kwargs} if server.template_kwargs else {}
        tokens = post_with_retries(server, server.tokenize_url,
                                   {"model": server.model, "messages": messages, "add_generation_prompt": True, **extra},
                                   step)
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
        return {**record, "status": "unsupported", "unfinished": None,
                "error": f"prompt has {prompt_tokens} tokens (margin {server.margin}), the context is {context}"}
    response = post_with_retries(server, server.chat_url, request_body(server, messages, max_tokens), step)
    choice = response["choices"][0]
    message = choice["message"]
    if message.get("reasoning_content") or message.get("reasoning"):
        raise SetupError("the server returned reasoning in a separate field, which this script does not score; "
                         "the content must hold the whole output (vLLM: serve without --reasoning-parser)")
    output = message.get("content") or ""
    result = {**record, "status": "ok", "max_tokens": max_tokens, "output": output,
              "finish_reason": choice["finish_reason"],
              "unfinished": is_unfinished(output, choice["finish_reason"], thinking),
              "output_tokens": int(response["usage"]["completion_tokens"])}
    if not server.tokenize_url:
        result["api_prompt_tokens"] = response["usage"].get("prompt_tokens")
    return result


def server_from(args: argparse.Namespace) -> Server:
    if bool(args.base_url) == bool(args.chat_url):
        sys.exit("scicode_runner.py generate: give exactly one of --base-url (vLLM), --chat-url (hosted API), --oracle")
    if args.base_url:
        kwargs = json.loads(args.chat_template_kwargs) if args.chat_template_kwargs else None
        return Server(model=args.model, chat_url=f"{args.base_url}/v1/chat/completions", retries=args.retries,
                      timeout=args.request_timeout, tokenize_url=f"{args.base_url}/tokenize", template_kwargs=kwargs,
                      model_repo=args.model_repo or None, context=args.context)
    if args.chat_template_kwargs or args.thinking:
        sys.exit("scicode_runner.py generate: a hosted API takes no --chat-template-kwargs or --thinking")
    if not (args.api_key_env and args.tokenizer and args.context):
        sys.exit("scicode_runner.py generate: --chat-url needs --api-key-env, --tokenizer and --context")
    key = os.environ.get(args.api_key_env)
    if not key:
        sys.exit(f"scicode_runner.py generate: set {args.api_key_env}")
    return Server(model=args.model, chat_url=args.chat_url, retries=args.retries, timeout=args.request_timeout,
                  headers={"Authorization": f"Bearer {key}"}, count=local_counter(args.tokenizer),
                  context=args.context, margin=args.margin)


def update_run(out: Path, key: str, value: dict[str, Any]) -> None:
    """`<out>/run.json`: `generation` is a list (one entry per `generate`; `generation_end` adds to the last),
    `prefetch` and `scoring` the last of each."""
    path = out / "run.json"
    run = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"generation": []}
    if key == "generation":
        run["generation"].append(value)
    elif key == "generation_end":
        run["generation"][-1].update(value)
    else:
        run[key] = value
    path.write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------------------------------------------
# Generation through Gencode

@dataclass
class Chain:
    """One problem in one prompt setting: its steps in order, through one Gencode instance."""
    setting: str
    problem: dict[str, Any]


def code_path(out: Path, model_id: str, setting: str, problem_id: str, step: int) -> Path:
    """Where Gencode.save_response_with_steps writes a step's code (`<output_dir>/<model>/<setting>/<id>.<step>.py`)."""
    return out / "generated_code" / model_id / setting / f"{problem_id}.{step}.py"


class Generator:
    """Runs chains through Gencode with the model call replaced; one answer record per step to generations.jsonl."""

    def __init__(self, h: Any, out: Path, model_id: str, respond: Callable[[str, dict[str, Any]], dict[str, Any]],
                 thinking: bool) -> None:
        self.h, self.out, self.model_id, self.respond, self.thinking = h, out, model_id, respond, thinking
        self.gen_path = out / "generations.jsonl"
        self.lock = threading.Lock()
        self.local = threading.local()
        # gencode.py calls `get_model_function(model, **model_kwargs)` and then the function with the prompt; this
        # is the one name replaced in its module (its temperature and the claude max_tokens are not used).
        h.gencode.get_model_function = self.model_function

    def model_function(self, model: str, **kwargs: Any) -> Callable[[str], str]:
        def call(prompt: str) -> str:
            ctx = self.local.ctx
            record = self.respond(prompt, ctx)
            ctx["record"] = record
            return answer_text(record, self.thinking)
        return call

    def append(self, record: dict[str, Any]) -> None:
        with self.lock, self.gen_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def run(self, chain: Chain, done: dict[tuple[str, str, int], dict[str, Any]]) -> None:
        g = self.h.gencode
        with_background = chain.setting == "with_background"
        template = g.BACKGOUND_PROMPT_TEMPLATE if with_background else g.DEFAULT_PROMPT_TEMPLATE
        gcode = g.Gencode(model=self.model_id, output_dir=self.out / "generated_code",
                          prompt_dir=self.out / "prompts", with_background=with_background, temperature=TEMPERATURE)
        prob = chain.problem
        pid, steps = prob["problem_id"], len(prob["sub_steps"])
        gcode.previous_llm_code = [None] * steps
        for i in range(steps):
            step = i + 1
            if (pid, step) in HARNESS_STEPS:
                continue
            earlier = done.get((chain.setting, pid, step))
            path = code_path(self.out, self.model_id, chain.setting, pid, step)
            if earlier is not None and earlier["status"] != "error" and path.is_file():
                # answered before: the next step gets the code Gencode extracted then, as in an uninterrupted run
                gcode.previous_llm_code[i] = earlier["extracted_code"]
                continue
            path.unlink(missing_ok=True)  # a file without its record (interrupted between the two): ask again
            ctx: dict[str, Any] = {"setting": chain.setting, "problem_id": pid, "step": step,
                                   "sub_step": prob["sub_steps"][i]}
            self.local.ctx = ctx
            started = datetime.datetime.now(datetime.timezone.utc)
            base = {"setting": chain.setting, "problem_id": pid, "step": step,
                    "step_id": prob["sub_steps"][i]["step_number"], "model": self.model_id,
                    "started": started.isoformat()}
            try:
                g.Gencode.generate_response_with_steps(gcode, prob, step, steps, self.model_id, template)
            except (Rejected, urllib.error.URLError, http.client.IncompleteRead, TimeoutError, ConnectionError,
                    KeyError, ValueError) as e:
                path.unlink(missing_ok=True)
                self.append({**base, "seconds": round(time.time() - started.timestamp(), 1), "status": "error",
                             "error": repr(e)})
                print(f"{chain.setting} {pid}.{step}: error {e!r}; the rest of this chain waits for a rerun",
                      flush=True)
                return
            record = ctx["record"]
            prompt_file = self.out / "prompts" / self.model_id / chain.setting / f"{pid}.{step}.txt"
            self.append({**base, "seconds": round(time.time() - started.timestamp(), 1), **record,
                         "prompt_sha256": hashlib.sha256(prompt_file.read_bytes()).hexdigest(),
                         "think_open": THINK_START in record.get("output", ""),
                         "extracted_code": gcode.previous_llm_code[i]})
            print(f"{chain.setting} {pid}.{step}: {record['status']} {record.get('output_tokens', '')} "
                  f"{record.get('finish_reason', '')}", flush=True)


def api_responder(server: Server, thinking: bool) -> Callable[[str, dict[str, Any]], dict[str, Any]]:
    def respond(prompt: str, ctx: dict[str, Any]) -> dict[str, Any]:
        # The prompt as the only user message: no system message of ours (PROTOCOL.md, "Settings")
        return ask(server, [{"role": "user", "content": prompt}], thinking,
                   f"{ctx['setting']}/{ctx['problem_id']}.{ctx['step']}")
    return respond


def oracle_responder(prompt: str, ctx: dict[str, Any]) -> dict[str, Any]:
    """The dev split's ground truth for the step, in the form a model would answer it."""
    code = ctx["sub_step"].get("ground_truth_code")
    if not code:
        raise SetupError(f"{ctx['problem_id']}.{ctx['step']} has no ground_truth_code (only the dev split has it)")
    return {"status": "ok", "output": f"```python\n{code}\n```\n", "finish_reason": "stop", "unfinished": False,
            "output_tokens": None, "prompt_tokens": None, "oracle": True}


def generate(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    gen_path = out / "generations.jsonl"
    if gen_path.is_file():  # resuming: what is kept must be what the earlier run wrote
        logged = ["api-events.jsonl"] if "api-events.jsonl" in provenance.read_manifest(out)["files"] else []
        provenance.verify(out, ["generations.jsonl", *logged], "scicode_runner.py generate")
    settings = SETTINGS if not args.oracle else ("with_background",)
    if args.oracle:
        if args.split != "validation":
            sys.exit("scicode_runner.py generate: --oracle needs --split validation (only the dev split has "
                     "ground_truth_code)")
        server, respond, run_sampling = None, oracle_responder, {"oracle": "ground_truth_code of the dev split"}
    else:
        server = server_from(args)
        server.events = EventLog(out / "api-events.jsonl")
        respond, run_sampling = api_responder(server, args.thinking), sampling(server)
    update_run(out, "generation", {**provenance.step("scicode_runner.py generate"), "model": args.model,
                                   "model_id": args.model_id, "split": args.split, "limit": args.limit,
                                   "settings": list(settings), "thinking": args.thinking, "sampling": run_sampling,
                                   **({"server": server_info(args.base_url)} if args.base_url else {})})
    h = harness()
    update_run(out, "generation_end", {"stubbed_modules": h.stubbed})
    rows = load_split(args.split, args.limit)
    gen = Generator(h, out, args.model_id, respond, args.thinking)
    done = latest(read_jsonl(gen_path))
    chains = [Chain(s, r) for s in settings for r in rows]
    todo = sum(1 for c in chains for pid, step in expected_steps([c.problem])
               if done.get((c.setting, pid, step), {}).get("status", "error") == "error")
    print(f"scicode_runner.py: {len(chains)} chains, {todo} steps to answer", flush=True)
    try:
        with ThreadPoolExecutor(args.concurrency) as pool:
            for future in [pool.submit(gen.run, c, done) for c in chains]:
                future.result()
    finally:
        if server is not None:
            update_run(out, "generation_end", {"api_events": server.events.counts()})
            provenance.record(out, ["api-events.jsonl"], "scicode_runner.py generate")
        if gen_path.is_file():
            provenance.record(out, ["generations.jsonl"], "scicode_runner.py generate")


# ---------------------------------------------------------------------------------------------------------------
# Scoring

def sha256_file(path: Path) -> str:
    return provenance.sha256_file(path)


def check_h5(path: Path) -> dict[str, Any]:
    if not path.is_file():
        sys.exit(f"scicode_runner.py: {path} is missing; setup_scoring_vm.sh downloads it from {H5_URL}")
    size, sha = path.stat().st_size, sha256_file(path)
    if (size, sha) != (H5_SIZE, H5_SHA256):
        sys.exit(f"scicode_runner.py: {path} has {size} bytes and sha256 {sha}; expected {H5_SIZE} and {H5_SHA256}")
    return {"path": str(path), "bytes": size, "sha256": sha, "sha256_ok": True}


def cached_revisions(hf_home: Path) -> list[str]:
    """Revisions of SciCode1/SciCode in the datasets cache (datasets names the directory after the commit)."""
    root = hf_home / "datasets" / "SciCode1___sci_code" / "default" / "0.0.0"
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


def prefetch(args: argparse.Namespace) -> None:
    """With network, in the scoring container: the pinned revision into the scoring cache, both splits, and what
    `main` points to today (recorded only). The cache must hold no other revision, since the scorer, offline,
    takes the latest cached one."""
    from datasets import load_dataset
    from huggingface_hub import HfApi, hf_hub_download

    HF_CACHE.mkdir(parents=True, exist_ok=True)
    for split in SPLIT_SIZES:
        load_dataset(DATA_REPO, split=split, revision=DATA_REVISION)
    revisions = cached_revisions(HF_CACHE)
    if revisions != [DATA_REVISION]:
        sys.exit(f"scicode_runner.py prefetch: {HF_CACHE} holds revisions {revisions}, expected only {DATA_REVISION}")
    files = {name: sha256_file(Path(hf_hub_download(DATA_REPO, name, repo_type="dataset", revision=DATA_REVISION)))
             for name in ("problems_test.jsonl", "problems_dev.jsonl")}
    record = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "revision": DATA_REVISION, "files_sha256": files,
              "main_at_prefetch": HfApi().dataset_info(DATA_REPO).sha}
    (HF_CACHE / "prefetch.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


SCORER_SUMMARY = re.compile(r"^correct (problems|steps): (\d+)/(\d+)$", re.MULTILINE)
DATASET_SEEN = re.compile(r"Found the latest cached dataset configuration '[^']*' at (\S+?)/?\s")


def parse_scorer_output(stdout: str, stderr: str) -> dict[str, Any]:
    """The counts the scorer prints, and the cached dataset revision datasets reports it took (offline)."""
    found = {kind: (int(k), int(n)) for kind, k, n in SCORER_SUMMARY.findall(stdout)}
    if set(found) != {"problems", "steps"}:
        raise SetupError(f"the scorer printed no 'correct problems/steps' lines: {stdout[-2000:]}")
    seen = DATASET_SEEN.findall(stdout + "\n" + stderr + "\n")
    return {"correct_problems": found["problems"][0], "problems_denominator": found["problems"][1],
            "correct_steps": found["steps"][0], "steps_denominator": found["steps"][1],
            "dataset_revision_seen": Path(seen[-1]).name if seen else None}


def scratch_copy(work: Path, h5: Path) -> Path:
    """The pinned clone's eval/ and src/ in a writable directory (the scorer writes tmp_<time>/ in its working
    directory), with eval/data/test_data.h5 a link to the checked file."""
    root = work / "SciCode"
    for part in ("eval", "src"):
        shutil.copytree(SCICODE_DIR / part, root / part, ignore=shutil.ignore_patterns("test_data.h5"))
    (root / "eval" / "data" / "test_data.h5").symlink_to(h5)
    return root


def package_versions() -> dict[str, Any]:
    from importlib import metadata

    versions: dict[str, Any] = {}
    for name in SCORING_PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    try:
        import numpy
        versions["numpy_blas"] = numpy.show_config(mode="dicts")["Build Dependencies"]["blas"]
    except Exception as e:  # recorded, never fatal: only describes the build
        versions["numpy_blas"] = {"error": repr(e)}
    return versions


# Amendment 1, extraction E1. A fence line is a line whose first non-blank characters are ```.
FENCE_LINE = re.compile(r"^[ \t]*```", re.MULTILINE)
# The import-line removal of scicode.gen.models.extract_python_script, applied after E1 as after the official one
IMPORT_LINES = re.compile(r'^\s*(import .*|from .*\s+import\s+.*)', re.MULTILINE)


def e1_extract(response: str, official: Callable[[str], str]) -> str:
    """PROTOCOL.md Amendment 1: with a ```python block or at least two fence lines, what the official extraction
    gives; with exactly one fence line, the text before that line; with none, the whole text; then the same
    import-line removal."""
    fences = list(FENCE_LINE.finditer(response))
    if "```python" in response or len(fences) >= 2:
        return official(response)
    text = response[:fences[0].start()] if fences else response
    return IMPORT_LINES.sub("", text)


def build_e1_files(h: Any, rows: list[dict[str, Any]], answers: dict[tuple[str, str, int], dict[str, Any]],
                   settings: list[str], thinking: bool, model_id: str, code_dir: Path) -> dict[tuple, str]:
    """The scored step files under E1, as save_response_with_steps writes them: Gencode's
    `{dependencies}\\n{earlier steps' code}\\n` (here the earlier steps' E1 code, and the harness's code for 13.6,
    62.1 and 76.3, loaded as generate_response_with_steps loads it), then this step's E1 code. Returns the E1 code
    per step. Prompts are not rebuilt: the answers were generated with the official extraction."""
    g, parse = h.gencode, h.parse
    codes: dict[tuple, str] = {}
    for setting in settings:
        with_background = setting == "with_background"
        template = g.BACKGOUND_PROMPT_TEMPLATE if with_background else g.DEFAULT_PROMPT_TEMPLATE
        for prob in rows:
            gcode = g.Gencode(model=model_id, output_dir=code_dir, prompt_dir=code_dir,
                              with_background=with_background, temperature=TEMPERATURE)
            pid, steps = prob["problem_id"], len(prob["sub_steps"])
            gcode.previous_llm_code = [None] * steps
            for i in range(steps):
                step = i + 1
                if (pid, step) in HARNESS_STEPS:
                    supplied = (SCICODE_DIR / "eval" / "data" / f"{pid}.{step}.txt").read_text(encoding="utf-8")
                    name = parse.extract_function_name(prob["sub_steps"][i]["function_header"])
                    gcode.previous_llm_code[i] = parse.get_function_from_code(supplied, name)
                    continue
                code = e1_extract(answer_text(answers[(setting, pid, step)], thinking), h.models.extract_python_script)
                _, previous_code = gcode.generate_prompt_with_steps(prob, step, template)
                path = code_dir / model_id / setting / f"{pid}.{step}.py"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(f"{previous_code}\n{code}", encoding="utf-8")
                gcode.previous_llm_code[i] = code
                codes[(setting, pid, step)] = code
    return codes


def run_scorer(root: Path, env: dict[str, str], args: argparse.Namespace, setting: str, code_dir: Path,
               score_dir: Path, logs_name: str, tag: str) -> dict[str, Any]:
    """test_generated_code.py, unchanged, on one setting of `code_dir`; its output kept, its counts parsed."""
    cmd = ["python", SCORER, "--model", args.model_id, "--split", args.split, "--code-dir", str(code_dir),
           "--log-dir", str(score_dir / logs_name), "--output-dir", str(score_dir / f"results_{logs_name}")] + \
        (["--with-background"] if setting == "with_background" else [])
    started = time.time()
    proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True)
    (score_dir / f"{tag}.stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (score_dir / f"{tag}.stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        sys.exit(f"scicode_runner.py score: the scorer exited with {proc.returncode}: {proc.stderr[-3000:]}")
    printed = parse_scorer_output(proc.stdout, proc.stderr)
    if printed["dataset_revision_seen"] != DATA_REVISION:
        sys.exit(f"scicode_runner.py score: the scorer loaded dataset revision {printed['dataset_revision_seen']}, "
                 f"not {DATA_REVISION}")
    return {"command": cmd, "seconds": round(time.time() - started, 1), "printed": printed}


def check_answers(answers: dict[tuple[str, str, int], dict[str, Any]], expected: list[tuple[str, int]],
                  code_dir: Path) -> list[str]:
    """The settings to score. Every expected step must have an answer (`ok` or `unsupported`; a step whose request
    failed is asked again by `generate`, never scored as a fail), and the code files in each setting's directory must
    be exactly the expected steps, as the scorer tests every file there."""
    settings = sorted({k[0] for k in answers}, key=SETTINGS.index)
    if not settings:
        sys.exit("scicode_runner.py score: no answers; run generate")
    for setting in settings:
        missing = [f"{p}.{s}" for p, s in expected if answers.get((setting, p, s), {}).get("status") in (None, "error")]
        if missing:
            sys.exit(f"scicode_runner.py score: {setting}: {len(missing)} steps have no answer (first: {missing[0]}); "
                     "run generate again (it resumes)")
        directory = code_dir / setting
        on_disk = sorted(p.name for p in directory.iterdir()) if directory.is_dir() else []
        wanted = sorted(f"{p}.{s}.py" for p, s in expected)
        if on_disk != wanted:
            sys.exit(f"scicode_runner.py score: {setting}: the code files differ from the expected steps "
                     f"({len(on_disk)} files, {len(wanted)} steps); the scorer would test every file there")
    return settings


def score(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    hashes = provenance.verify(out, ["generations.jsonl"], "scicode_runner.py score")
    head = (SCICODE_DIR / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head != SCICODE_COMMIT:
        sys.exit(f"scicode_runner.py: {SCICODE_DIR} is at {head}, expected {SCICODE_COMMIT}")
    h5 = check_h5(H5_PATH)
    revisions = cached_revisions(HF_CACHE)
    if revisions != [DATA_REVISION]:
        sys.exit(f"scicode_runner.py score: {HF_CACHE} holds revisions {revisions}; run prefetch (only "
                 f"{DATA_REVISION} may be cached, as the offline scorer takes the latest cached one)")
    os.environ["HF_HOME"] = str(HF_CACHE)
    os.environ["HF_HUB_OFFLINE"] = os.environ["HF_DATASETS_OFFLINE"] = "1"
    rows = load_split(args.split, args.limit)
    answers = latest(read_jsonl(out / "generations.jsonl"))
    expected = expected_steps(rows)
    settings = check_answers(answers, expected, out / "generated_code" / args.model_id)
    score_dir = out / "score"
    stamp = score_dir / "stamp.json"
    # the scorer reuses its per-step logs; they hold only for these answers and this runner (which builds E1 files)
    key = {"generations_sha256": hashes["generations.jsonl"], "runner_sha256": sha256_file(HERE / "scicode_runner.py")}
    if stamp.is_file() and json.loads(stamp.read_text()) != key:
        shutil.rmtree(score_dir)
    score_dir.mkdir(parents=True, exist_ok=True)
    stamp.write_text(json.dumps(key) + "\n", encoding="utf-8")
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))
    thinking = bool(run["generation"][0].get("thinking"))
    # Amendment 1: E1 step files rebuilt from the recorded answers, scored by the same scorer
    e1_dir = out / "generated_code_e1"
    if e1_dir.exists():
        shutil.rmtree(e1_dir)
    e1_codes = build_e1_files(harness(), rows, answers, settings, thinking, args.model_id, e1_dir)
    runs: dict[str, Any] = {}
    verdicts: dict[tuple[str, str, str, int], str] = {}
    with tempfile.TemporaryDirectory() as work:
        root = scratch_copy(Path(work), H5_PATH)
        env = {**os.environ, **BLAS_THREADS, "PYTHONPATH": str(root / "src"), "PYTHONUNBUFFERED": "1"}
        for extraction, code_dir, logs_name in (("official", out / "generated_code", "logs"),
                                                ("e1", e1_dir, "logs_e1")):
            for setting in settings:
                key = setting if extraction == "official" else f"e1/{setting}"
                runs[key] = run_scorer(root, env, args, setting, code_dir, score_dir, logs_name, key.replace("/", "_"))
                logs = score_dir / logs_name / args.model_id / setting
                for pid, step in expected:
                    first = (logs / f"{pid}.{step}.txt").read_text(encoding="utf-8").splitlines()
                    verdicts[(extraction, setting, pid, step)] = first[0] if first else ""
    with (out / "graded.jsonl").open("w", encoding="utf-8") as f:
        for setting in settings:
            for pid, step in expected:
                a = answers[(setting, pid, step)]
                verdict, verdict_e1 = (verdicts[(x, setting, pid, step)] for x in ("official", "e1"))
                f.write(json.dumps({
                    "setting": setting, "problem_id": pid, "step": step, "step_id": a["step_id"],
                    "verdict": verdict, "pass": verdict == "pass", "status": a["status"],
                    "verdict_e1": verdict_e1, "pass_e1": verdict_e1 == "pass",
                    "prompt_tokens": a.get("prompt_tokens"), "output_tokens": a.get("output_tokens"),
                    "max_tokens": a.get("max_tokens"), "context": a.get("context"),
                    "finish_reason": a.get("finish_reason"), "unfinished": a.get("unfinished"),
                    "think_open": a.get("think_open"), "api_prompt_tokens": a.get("api_prompt_tokens"),
                    "error": a.get("error"), "started": a.get("started"), "code": a.get("extracted_code"),
                    "code_e1": e1_codes[(setting, pid, step)],
                }, ensure_ascii=False) + "\n")
    provenance.record(out, ["graded.jsonl"], "scicode_runner.py score")
    prefetched = HF_CACHE / "prefetch.json"
    update_run(out, "scoring", {
        **provenance.step("scicode_runner.py score"), "split": args.split, "limit": args.limit,
        "scicode_commit": head, "test_data_h5": h5, "dataset_cache_revisions": revisions,
        "dataset_prefetch": json.loads(prefetched.read_text()) if prefetched.is_file() else None,
        "blas_threads": BLAS_THREADS, "packages": package_versions(), "scorer_timeout_s": SCORER_TIMEOUT_S,
        "container": {"image_id": os.environ.get("SCICODE_IMAGE_ID"), "network": os.environ.get("SCICODE_NETWORK")},
        "runs": runs})
    for setting, r in runs.items():
        p = r["printed"]
        print(f"{setting}: correct steps {p['correct_steps']}/{p['steps_denominator']}, correct problems "
              f"{p['correct_problems']}/{p['problems_denominator']}, dataset {p['dataset_revision_seen']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("out_dir")
    g.add_argument("--model-id", required=True, help="our model id: the directory name of its code files")
    g.add_argument("--model", default="", help="the model name the server serves")
    g.add_argument("--split", default="test", choices=sorted(SPLIT_SIZES))
    g.add_argument("--limit", type=int)
    g.add_argument("--base-url", default="", help="our vLLM server (counts the prompt through its /tokenize)")
    g.add_argument("--chat-url", default="", help="a hosted API's chat completions URL")
    g.add_argument("--oracle", action="store_true", help="answer with the dev split's ground_truth_code")
    g.add_argument("--model-repo", default="", help="vLLM: REPO@REVISION served, to record its sampling defaults")
    g.add_argument("--thinking", action="store_true",
                   help="the model thinks before answering: no </think> or a length stop means unfinished")
    g.add_argument("--chat-template-kwargs", default="")
    g.add_argument("--api-key-env", default="")
    g.add_argument("--tokenizer", default="", help="hosted API: REPO@REVISION of the model's tokenizer and template")
    g.add_argument("--context", type=int, default=0)
    g.add_argument("--margin", type=int, default=0)
    g.add_argument("--retries", type=int, default=3)
    g.add_argument("--concurrency", type=int, default=int(os.environ.get("CONCURRENCY", "64")),
                   help="chains (problem x setting) in flight, so also requests in flight")
    g.add_argument("--request-timeout", type=float, default=float(os.environ.get("REQUEST_TIMEOUT", "21600")))
    sub.add_parser("prefetch")
    s = sub.add_parser("score")
    s.add_argument("out_dir")
    s.add_argument("--model-id", required=True)
    s.add_argument("--split", default="test", choices=sorted(SPLIT_SIZES))
    s.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "generate":
        if args.oracle and (args.base_url or args.chat_url):
            sys.exit("scicode_runner.py generate: --oracle takes no server")
        generate(args)
    elif args.command == "prefetch":
        prefetch(args)
    else:
        score(args)


if __name__ == "__main__":
    main()
