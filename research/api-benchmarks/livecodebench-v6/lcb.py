"""LiveCodeBench v6 code generation with LiveCodeBench's own prompt builder, code extraction and evaluator.

Runs in the LiveCodeBench venv that run.sh builds, with the pinned clone in `.cache/LiveCodeBench`:

    python lcb.py generate <out-dir> --base-url http://localhost:8000 --model <served-name> [--limit N]
                           [--chat-template-kwargs JSON]
    python lcb.py generate <out-dir> --chat-url https://.../v1/chat/completions --model <name> --api-key-env VAR
                           --tokenizer REPO@REVISION --context N --margin M [--retries R] [--limit N]
    python lcb.py score <out-dir> [--limit N]

`generate` sends one chat request per problem and appends each answer to `<out-dir>/generations.jsonl` (raw
output with thinking; not committed). With `--base-url` the server is our vLLM: its `/tokenize` counts the prompt
with the served template, and the output may use the rest of the context. With `--chat-url` it is a hosted API
(the Fabryka API for Bielik): the prompt is counted locally with the model's own tokenizer and chat template at
the pinned revision, and the output may use the context minus that count minus a margin for what the API's own
rendering adds. A problem that already has an answer is skipped, so an interrupted run resumes; a problem whose
request failed is tried again. `score` extracts the code from the text after the last `</think>` and runs
LiveCodeBench's evaluator on it, writing one line per problem to `<out-dir>/graded.jsonl`, which summarize.py
reads. `--limit N` takes the first N problems in LiveCodeBench's order (sorted by question_id).
"""

import argparse
import datetime
import functools
import json
import os
import ssl
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LCB_DIR = Path(os.environ.get("LCB_DIR", HERE / ".cache" / "LiveCodeBench"))
LCB_COMMIT = "28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24"

DATA_REPO = "livecodebench/code_generation_lite"
DATA_REVISION = "0fe84c3912ea0c4d4a78037083943e8f0c4dd505"
# ALLOWED_FILES of the dataset script (code_generation_lite.py @ DATA_REVISION): a release is the json lines of
# these files, in this order. Reading them directly gives the rows the script yields, without running its code.
RELEASE_FILES = {
    "release_v5": ["test.jsonl", "test2.jsonl", "test3.jsonl", "test4.jsonl", "test5.jsonl"],
    "release_v6": ["test.jsonl", "test2.jsonl", "test3.jsonl", "test4.jsonl", "test5.jsonl", "test6.jsonl"],
}

# PROTOCOL.md, "Settings"
TEMPERATURE = 0.6
TOP_P = 0.95
SEED = 20261122
# LiveCodeBench's style for chat models behind an OpenAI-compatible API (oai_runner.py): its system message plus
# the generic question template, and code taken from the last ``` block of the answer.
PROMPT_STYLE = "OpenAIChat"
# lcb_runner/runner/parser.py defaults of the evaluator: seconds per test case, and worker processes.
EVAL_TIMEOUT = 6
EVAL_PROCESSES = 12

THINK_END = "</think>"
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


def lcb_modules() -> Any:
    """Imports the pinned LiveCodeBench. Its prompt module opens few-shot files relative to the repo root."""
    head = (LCB_DIR / ".git" / "HEAD").read_text(encoding="utf-8").strip()
    if head != LCB_COMMIT:
        sys.exit(f"lcb.py: {LCB_DIR} is at {head}, expected {LCB_COMMIT} (run.sh checks it out)")
    os.chdir(LCB_DIR)
    sys.path.insert(0, str(LCB_DIR))
    import lcb_runner.benchmarks.code_generation as benchmark
    import lcb_runner.evaluation as evaluation
    import lcb_runner.lm_styles as lm_styles
    import lcb_runner.prompts.code_generation as prompts
    import lcb_runner.utils.extraction_utils as extraction
    return argparse.Namespace(benchmark=benchmark, evaluation=evaluation, prompts=prompts, extraction=extraction,
                              style=lm_styles.LMStyle(PROMPT_STYLE))


def load_rows(limit: int | None) -> list[dict[str, Any]]:
    """release_v6 rows sorted by question_id (as build_prompt_benchmark sorts them), with `in_v6_only`."""
    from huggingface_hub import hf_hub_download

    rows, v5_ids = [], set()
    for name in RELEASE_FILES["release_v6"]:
        path = hf_hub_download(DATA_REPO, name, repo_type="dataset", revision=DATA_REVISION)
        with open(path, encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                rows.append(row)
                if name in RELEASE_FILES["release_v5"]:
                    v5_ids.add(row["question_id"])
    ids = [r["question_id"] for r in rows]
    if len(set(ids)) != len(ids):
        sys.exit("lcb.py: duplicate question_id in release_v6")
    rows.sort(key=lambda r: r["question_id"])
    for r in rows:
        r["in_v6_only"] = r["question_id"] not in v5_ids
    return rows[:limit] if limit else rows


def problem(lcb: Any, row: dict[str, Any]) -> Any:
    return lcb.benchmark.CodeGenerationProblem(**{k: v for k, v in row.items() if k != "in_v6_only"})


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

    def failed(self) -> None:
        with self.lock:
            self.resume_at = max(self.resume_at, time.monotonic() + self.pause)
            self.pause = min(2 * self.pause, self.pause_max)

    def succeeded(self) -> None:
        with self.lock:
            self.pause = self.pause_min


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


def post_with_retries(server: Server, url: str, body: dict[str, Any]) -> dict[str, Any]:
    """Up to `server.retries` attempts for server errors, 429 and broken connections, each failure pausing all
    requests; 401/403 stop the run (SetupError), any other 4xx raises Rejected at once."""
    for attempt in range(1, server.retries + 1):
        server.gate.wait()
        try:
            response = post(url, body, server.timeout, server.headers)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):  # a wrong or missing key fails every request the same way
                raise SetupError(f"HTTP {e.code} from {url}: check the API key") from e
            if e.code != 429 and e.code < 500:
                raise Rejected(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}") from e
            server.gate.failed()
            if attempt == server.retries:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if isinstance(getattr(e, "reason", None), ssl.SSLCertVerificationError):
                raise SetupError(f"TLS certificate check failed for {url}: {e}") from e
            server.gate.failed()
            if attempt == server.retries:
                raise
        else:
            server.gate.succeeded()
            return response
    raise AssertionError("unreachable")


def local_counter(spec: str) -> Callable[[list[dict[str, str]]], int]:
    """Prompt tokens with the model's own tokenizer and chat template (`REPO@REVISION`), at the template defaults,
    as the API renders them. Gated repos need a Hugging Face login with the licence accepted."""
    from huggingface_hub import get_token
    from transformers import AutoTokenizer

    repo, _, revision = spec.partition("@")
    if get_token() is None:
        sys.exit(f"lcb.py: the tokenizer of {repo} is gated; log in first (`hf auth login`) with an account that "
                 "accepted its licence on Hugging Face")
    try:
        tokenizer = AutoTokenizer.from_pretrained(repo, revision=revision)
    except OSError as e:  # transformers reports a gated or missing repo as OSError
        sys.exit(f"lcb.py: cannot load the tokenizer of {repo} @ {revision}: {e}")
    lock = threading.Lock()

    def count(messages: list[dict[str, str]]) -> int:
        with lock:
            return len(tokenizer.apply_chat_template(messages, add_generation_prompt=True, tokenize=True))

    return count


def answer(server: Server, messages: list[dict[str, str]]) -> dict[str, Any]:
    """One sample for one prompt; output limited only by the context (max_tokens = context - prompt tokens, minus
    the margin for a hosted API)."""
    extra = {"chat_template_kwargs": server.template_kwargs} if server.template_kwargs else {}
    if server.tokenize_url:
        tokens = post_with_retries(server, server.tokenize_url,
                                   {"model": server.model, "messages": messages, "add_generation_prompt": True, **extra})
        prompt_tokens, context = int(tokens["count"]), int(tokens["max_model_len"])
    else:
        assert server.count is not None
        prompt_tokens, context = server.count(messages), server.context
    record: dict[str, Any] = {"prompt_tokens": prompt_tokens, "context": context}
    max_tokens = context - prompt_tokens - server.margin
    if max_tokens < 1:
        return {**record, "status": "unsupported",
                "error": f"prompt has {prompt_tokens} tokens (margin {server.margin}), the context is {context}"}
    if server.tokenize_url:
        # Sampling as oai_runner.py sends it (no stop for chat models), with the PROTOCOL.md temperature, top_p, seed.
        body = {"model": server.model, "messages": messages, "n": 1, "temperature": TEMPERATURE, "top_p": TOP_P,
                "max_tokens": max_tokens, "seed": SEED, "frequency_penalty": 0, "presence_penalty": 0, **extra}
    else:
        # Only the fields the Fabryka API accepted in the IFEval run (no `n`, penalties, `stop` or template switches).
        body = {"model": server.model, "messages": messages, "temperature": TEMPERATURE, "top_p": TOP_P,
                "max_tokens": max_tokens, "seed": SEED}
    response = post_with_retries(server, server.chat_url, body)
    choice = response["choices"][0]
    message = choice["message"]
    if message.get("reasoning_content") or message.get("reasoning"):
        raise SetupError("the server returned reasoning in a separate field, which this script does not score; "
                         "the content must hold the whole output (vLLM: serve without --reasoning-parser)")
    usage = response["usage"]
    result = {**record, "status": "ok", "max_tokens": max_tokens, "output": message.get("content") or "",
              "finish_reason": choice["finish_reason"], "finished": choice["finish_reason"] == "stop",
              "output_tokens": int(usage["completion_tokens"])}
    if not server.tokenize_url:
        result["api_prompt_tokens"] = usage.get("prompt_tokens")  # the API's own count, to check the margin
    return result


def server_from(args: argparse.Namespace) -> Server:
    if bool(args.base_url) == bool(args.chat_url):
        sys.exit("lcb.py generate: give exactly one of --base-url (vLLM) and --chat-url (hosted API)")
    if args.base_url:
        kwargs = json.loads(args.chat_template_kwargs) if args.chat_template_kwargs else None
        return Server(model=args.model, chat_url=f"{args.base_url}/v1/chat/completions", retries=args.retries,
                      timeout=args.request_timeout, tokenize_url=f"{args.base_url}/tokenize", template_kwargs=kwargs)
    if args.chat_template_kwargs:
        sys.exit("lcb.py generate: a hosted API takes no --chat-template-kwargs")
    if not (args.api_key_env and args.tokenizer and args.context):
        sys.exit("lcb.py generate: --chat-url needs --api-key-env, --tokenizer and --context")
    key = os.environ.get(args.api_key_env)
    if not key:
        sys.exit(f"lcb.py generate: set {args.api_key_env}")
    return Server(model=args.model, chat_url=args.chat_url, retries=args.retries, timeout=args.request_timeout,
                  headers={"Authorization": f"Bearer {key}"}, count=local_counter(args.tokenizer),
                  context=args.context, margin=args.margin)


def generate(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    gen_path = out / "generations.jsonl"
    server = server_from(args)
    lcb = lcb_modules()
    rows = load_rows(args.limit)
    done = {r["question_id"] for r in read_jsonl(gen_path) if r["status"] != "error"}
    # Prompts first: building a CodeGenerationProblem decodes its hidden tests, which the requests do not need.
    todo = [(r["question_id"], lcb.prompts.format_prompt_generation(problem(lcb, r), lcb.style))
            for r in rows if r["question_id"] not in done]
    del rows
    print(f"lcb.py: {len(done)} problems already answered, {len(todo)} to go", flush=True)
    lock = threading.Lock()

    def run(item: tuple[str, list[dict[str, str]]]) -> None:
        question_id, messages = item
        started = datetime.datetime.now(datetime.timezone.utc)
        try:
            record = answer(server, messages)
        except (Rejected, urllib.error.URLError, TimeoutError, ConnectionError, KeyError, ValueError) as e:
            record = {"status": "error", "error": repr(e)}
        record = {"question_id": question_id, "model": args.model, "started": started.isoformat(),
                  "seconds": round(time.time() - started.timestamp(), 1), **record}
        with lock, gen_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"{question_id}: {record['status']} {record.get('output_tokens', '')} {record.get('finish_reason', '')}"
              f" {record['seconds']} s", flush=True)

    with ThreadPoolExecutor(args.concurrency) as pool:
        for future in [pool.submit(run, item) for item in todo]:
            future.result()


def score(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    lcb = lcb_modules()
    rows = load_rows(args.limit)
    answers = {r["question_id"]: r for r in read_jsonl(out / "generations.jsonl")}  # the last record wins
    missing = [r["question_id"] for r in rows if r["question_id"] not in answers]
    if missing:
        sys.exit(f"lcb.py: {len(missing)} problems have no answer yet (first: {missing[0]}); run generate")
    scored = [r for r in rows if answers[r["question_id"]]["status"] == "ok"]
    codes = [lcb.extraction.extract_code(after_think(answers[r["question_id"]]["output"]), lcb.style) for r in scored]
    graded: list[bool] = []
    metadata: list[list[str]] = []
    if scored:
        samples = [problem(lcb, r).get_evaluation_sample() for r in scored]
        _, results, metadata = lcb.evaluation.codegen_metrics(
            samples, [[c] for c in codes], num_process_evaluate=EVAL_PROCESSES, timeout=EVAL_TIMEOUT)
        graded = [g[0] for g in lcb.evaluation.extract_instance_results(results)]
    by_id = {r["question_id"]: (passed, json.loads(meta[0]), code)
             for r, passed, meta, code in zip(scored, graded, metadata, codes)}
    with (out / "graded.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            a = answers[r["question_id"]]
            passed, meta, code = by_id.get(r["question_id"], (None, None, None))
            f.write(json.dumps({
                "question_id": r["question_id"], "platform": r["platform"], "difficulty": r["difficulty"],
                "contest_date": r["contest_date"], "in_v6_only": r["in_v6_only"], "status": a["status"],
                "pass": passed, "prompt_tokens": a.get("prompt_tokens"), "output_tokens": a.get("output_tokens"),
                "context": a.get("context"), "finished": a.get("finished"), "finish_reason": a.get("finish_reason"),
                "error": a.get("error"), "eval_metadata": meta, "code": code, "started": a.get("started"),
                "max_tokens": a.get("max_tokens"), "api_prompt_tokens": a.get("api_prompt_tokens"),
            }, ensure_ascii=False) + "\n")
    print(f"lcb.py: graded {len(scored)} of {len(rows)} problems -> {out / 'graded.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("out_dir")
    g.add_argument("--base-url", default="", help="our vLLM server (counts the prompt through its /tokenize)")
    g.add_argument("--chat-url", default="", help="a hosted API's chat completions URL")
    g.add_argument("--model", required=True)
    g.add_argument("--limit", type=int)
    g.add_argument("--chat-template-kwargs", default="")
    g.add_argument("--api-key-env", default="", help="hosted API: environment variable with the key")
    g.add_argument("--tokenizer", default="", help="hosted API: REPO@REVISION of the model's tokenizer and template")
    g.add_argument("--context", type=int, default=0, help="hosted API: context window in tokens")
    g.add_argument("--margin", type=int, default=0, help="hosted API: tokens kept free beyond the local prompt count")
    g.add_argument("--retries", type=int, default=3, help="attempts per request")
    g.add_argument("--concurrency", type=int, default=int(os.environ.get("CONCURRENCY", "64")))
    g.add_argument("--request-timeout", type=float, default=float(os.environ.get("REQUEST_TIMEOUT", "21600")))
    s = sub.add_parser("score")
    s.add_argument("out_dir")
    s.add_argument("--limit", type=int)
    args = parser.parse_args()
    if args.command == "generate":
        generate(args)
    else:
        score(args)


if __name__ == "__main__":
    main()
