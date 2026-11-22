"""LiveCodeBench v6 code generation with LiveCodeBench's own prompt builder, code extraction and evaluator.

Runs in the LiveCodeBench venv that run.sh builds, with the pinned clone in `.cache/LiveCodeBench`:

    python lcb.py generate <out-dir> --base-url http://localhost:8000 --model <served-name> [--limit N]
                           [--chat-template-kwargs JSON]
    python lcb.py score <out-dir> [--limit N]

`generate` sends one chat request per problem to an OpenAI-compatible server (vLLM) and appends each answer to
`<out-dir>/generations.jsonl` (raw output with thinking; not committed). A problem that already has an answer is
skipped, so an interrupted run resumes; a problem whose request failed is tried again. `score` extracts the code
from the text after the last `</think>` and runs LiveCodeBench's evaluator on it, writing one line per problem to
`<out-dir>/graded.jsonl`, which summarize.py reads. `--limit N` takes the first N problems in LiveCodeBench's
order (sorted by question_id).
"""

import argparse
import datetime
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
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
RETRIES = 3          # attempts per request
RETRY_SLEEP = 30     # seconds between attempts, as in oai_runner.py


class SetupError(RuntimeError):
    """The server answered in a shape this script does not score; the whole run stops."""


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


def post(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def post_with_retries(url: str, body: dict[str, Any], timeout: float) -> dict[str, Any]:
    """Retries server errors and broken connections; a 4xx answer is not retried."""
    for attempt in range(1, RETRIES + 1):
        try:
            return post(url, body, timeout)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == RETRIES:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == RETRIES:
                raise
        time.sleep(RETRY_SLEEP)
    raise AssertionError("unreachable")


def answer(base_url: str, model: str, messages: list[dict[str, str]], template_kwargs: dict[str, Any] | None,
           timeout: float) -> dict[str, Any]:
    """One sample for one prompt; output limited only by the context (max_tokens = context - prompt tokens)."""
    extra = {"chat_template_kwargs": template_kwargs} if template_kwargs else {}
    tokens = post_with_retries(f"{base_url}/tokenize",
                               {"model": model, "messages": messages, "add_generation_prompt": True, **extra}, timeout)
    prompt_tokens, context = int(tokens["count"]), int(tokens["max_model_len"])
    record: dict[str, Any] = {"prompt_tokens": prompt_tokens, "context": context}
    max_tokens = context - prompt_tokens
    if max_tokens < 1:
        return {**record, "status": "unsupported",
                "error": f"prompt has {prompt_tokens} tokens, the context is {context}"}
    # Sampling as oai_runner.py sends it (no stop for chat models), with the PROTOCOL.md temperature, top_p and seed.
    body = {"model": model, "messages": messages, "n": 1, "temperature": TEMPERATURE, "top_p": TOP_P,
            "max_tokens": max_tokens, "seed": SEED, "frequency_penalty": 0, "presence_penalty": 0, **extra}
    response = post_with_retries(f"{base_url}/v1/chat/completions", body, timeout)
    choice = response["choices"][0]
    message = choice["message"]
    if message.get("reasoning_content") or message.get("reasoning"):
        raise SetupError("the server returned reasoning in a separate field; serve without --reasoning-parser so "
                         "the content holds the whole output")
    return {**record, "status": "ok", "max_tokens": max_tokens, "output": message.get("content") or "",
            "finish_reason": choice["finish_reason"], "finished": choice["finish_reason"] == "stop",
            "output_tokens": int(response["usage"]["completion_tokens"])}


def generate(args: argparse.Namespace) -> None:
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    gen_path = out / "generations.jsonl"
    lcb = lcb_modules()
    rows = load_rows(args.limit)
    done = {r["question_id"] for r in read_jsonl(gen_path) if r["status"] != "error"}
    # Prompts first: building a CodeGenerationProblem decodes its hidden tests, which the requests do not need.
    todo = [(r["question_id"], lcb.prompts.format_prompt_generation(problem(lcb, r), lcb.style))
            for r in rows if r["question_id"] not in done]
    del rows
    template_kwargs = json.loads(args.chat_template_kwargs) if args.chat_template_kwargs else None
    print(f"lcb.py: {len(done)} problems already answered, {len(todo)} to go", flush=True)
    lock = threading.Lock()

    def run(item: tuple[str, list[dict[str, str]]]) -> None:
        question_id, messages = item
        started = datetime.datetime.now(datetime.timezone.utc)
        try:
            record = answer(args.base_url, args.model, messages, template_kwargs, args.request_timeout)
        except (urllib.error.URLError, TimeoutError, ConnectionError, KeyError, ValueError) as e:
            record = {"status": "error", "error": repr(e)}
        record = {"question_id": question_id, "model": args.model, "started": started.isoformat(),
                  "seconds": round(time.time() - started.timestamp(), 1), **record}
        with lock, gen_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"{question_id}: {record['status']} {record.get('output_tokens', '')} {record.get('finish_reason', '')}",
              flush=True)

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
            }, ensure_ascii=False) + "\n")
    print(f"lcb.py: graded {len(scored)} of {len(rows)} problems -> {out / 'graded.jsonl'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    g = sub.add_parser("generate")
    g.add_argument("out_dir")
    g.add_argument("--base-url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--limit", type=int)
    g.add_argument("--chat-template-kwargs", default="")
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
