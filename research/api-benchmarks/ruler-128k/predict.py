"""Send RULER samples of one length to an OpenAI-compatible chat endpoint and store the raw outputs.

Two servers, one request shape:
  vLLM (local GPU):   --base-url http://localhost:8000  [--chat-template-kwargs JSON]
      prompts are counted by the server's /tokenize with its chat template; the window is its max_model_len.
  Fabryka AI API:     --base-url https://fabryka.ai --api-key-env FABRYKA_API_KEY --tokenizer DIR --context 32768
      the API has no /tokenize: prompts are counted here with the model's own tokenizer and chat template at the
      pinned revision, template defaults (which include the provider system prompt the API adds), and --margin
      tokens are kept free for what the local count cannot see (template version, date line on the API side).

Each sample is one user message with plain string content: RULER's `input` + `answer_prefix`, as RULER's own
OpenAI client sends it (scripts/pred/call_api.py, client_wrappers.OpenAIClient @ db43f92). Body: model, messages,
max_tokens, temperature, top_p, seed (the fields the Fabryka API accepted in ../ifeval; no `stop`, no
`chat_template_kwargs` unless given). max_tokens = window - counted prompt - margin (PROTOCOL.md: output limit is
the context window minus the templated input).

Fit check, before any generation: if a counted prompt + margin + RULER's answer budget exceeds the window, the whole
length is written to `skip.json` with the reason and nothing is sent (PROTOCOL.md: `score: null`, not cut down).

Failures: transport errors (a reset connection, a body cut short of its Content-Length) and HTTP 408/429/5xx are
retried (--max-retries). Any such failure pauses every request (10 s, doubling up to 5 min while failures continue,
back to 10 s after a success), as ../ifeval/lm_eval_fabryka.py does for the same API. Other HTTP errors (e.g. 400)
are not retried. A sample whose last attempt failed is recorded as {"index", "error"}: never scored, sent again on
the next run. Every failed attempt and each recovery is a line in <length-dir>/api-events.jsonl (EventLog), as
../livecodebench-v6/lcb.py keeps it: UTC time, length, task, index, endpoint, attempt, HTTP status (null for a
broken connection), the first 300 characters of the error, the action (`retry` after `pause_s`, `gave_up`,
`rejected`, `recovered`) and the pause in seconds.

Raw records go to <length-dir>/raw/<task>.jsonl, appended, one per finished attempt:
  {"index", "output", "finish_reason", "prompt_tokens" (server's usage), "counted_prompt_tokens", "output_tokens"}
The last record of an index wins; a rerun skips indices with an output. One process per length: predict.py holds
<length-dir>/generate.lock (ruler.generation_lock) from before it reads raw/ to its end, and a second one stops. The
API key is read from the environment variable named by --api-key-env and is never printed.
"""

import argparse
import datetime
import http.client
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ruler import answer_budgets, generation_lock, latest_records, read_jsonl

RETRY_STATUS = {408, 429, 500, 502, 503, 504}
PAUSE_MIN, PAUSE_MAX = 10.0, 300.0
EVENTS = "api-events.jsonl"


class Gate:
    """One pause shared by all requests: after a retryable failure nobody sends until it ends."""

    def __init__(self, pause_min=PAUSE_MIN, pause_max=PAUSE_MAX):
        self.lock = threading.Lock()
        self.resume_at = 0.0
        self.pause_min, self.pause_max = pause_min, pause_max
        self.pause = pause_min

    def wait(self):
        while (wait := self.resume_at - time.monotonic()) > 0:
            time.sleep(wait)

    def failed(self):
        """Pauses all requests for the current pause and doubles it; returns the pause applied, in seconds."""
        with self.lock:
            pause = self.pause
            self.resume_at = max(self.resume_at, time.monotonic() + pause)
            self.pause = min(2 * self.pause, self.pause_max)
            return pause

    def succeeded(self):
        with self.lock:
            self.pause = self.pause_min


def event_counts(events):
    """Totals of api-events.jsonl lines: by action, by HTTP status (`none` for a broken connection), samples hit."""
    def tally(key):
        out = {}
        for e in events:
            k = "none" if e.get(key) is None else str(e[key])
            out[k] = out.get(k, 0) + 1
        return dict(sorted(out.items()))

    return {"events": len(events), "by_action": tally("action"), "by_status": tally("status"),
            "samples": len({(e.get("length"), e.get("task"), e.get("index")) for e in events
                            if e.get("task") is not None})}


class EventLog:
    """Every failed request attempt, and each success after a failure, one json line in `path`. Kept as evidence
    for the API's operators."""

    def __init__(self, path=None, length=None):
        self.path, self.length, self.lock, self.events = path, length, threading.Lock(), []
        if path is not None:
            Path(path).touch()

    def write(self, **event):
        event = {"time": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds"),
                 "length": self.length, **event}
        with self.lock:
            self.events.append(event)
            if self.path is not None:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def counts(self):
        with self.lock:
            return event_counts(self.events)


class Client:
    def __init__(self, base_url, timeout, max_retries, gate, api_key=None, events=None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.gate = gate
        self.events = events or EventLog()
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def post(self, path, body, task=None, index=None):
        """POST JSON; retries retryable failures behind the shared pause. Returns the response or raises RuntimeError.
        Every failure and a success after failures go to `self.events`."""
        data = json.dumps(body).encode("utf-8")
        last = None

        def log(attempt, status, error, action, pause=None):
            self.events.write(task=task, index=index, endpoint=path, attempt=attempt, status=status,
                              error=error[:300], action=action, pause_s=pause)

        for attempt in range(1, self.max_retries + 2):
            self.gate.wait()
            request = urllib.request.Request(self.base_url + path, data=data, headers=self.headers)
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    result = json.loads(response.read().decode("utf-8"))
                self.gate.succeeded()
                if attempt > 1:
                    log(attempt, None, "", "recovered")
                return result
            except urllib.error.HTTPError as e:
                text = e.read().decode("utf-8", "replace")
                last = f"HTTP {e.code}: {text[:500]}"
                if e.code not in RETRY_STATUS:
                    log(attempt, e.code, text, "rejected")
                    raise RuntimeError(last) from None
                status = e.code
            except (urllib.error.URLError, http.client.IncompleteRead, TimeoutError, ConnectionError) as e:
                last, text, status = f"{type(e).__name__}: {e}", repr(e), None
            pause = self.gate.failed()
            log(attempt, status, text, "gave_up" if attempt == self.max_retries + 1 else "retry", pause)
            print(f"predict.py: {path} attempt {attempt} failed: {last}", file=sys.stderr)
        raise RuntimeError(last)


def messages(sample):
    return [{"role": "user", "content": sample["input"] + sample.get("answer_prefix", "")}]


def request_body(args, sample, counted, window, extra):
    """The chat request for one sample: the output limit is the window minus the counted prompt and the margin."""
    return {"model": args.model, "messages": messages(sample), "max_tokens": window - counted - args.margin,
            "temperature": args.temperature, "top_p": args.top_p, "seed": args.seed, **extra}


def count_prompt(tokenizer, sample):
    """Tokens of one templated prompt as the API sees it: the model's chat template with its defaults (provider
    system prompt, BOS where the template puts it) and the generation prompt."""
    ids = tokenizer.apply_chat_template(messages(sample), add_generation_prompt=True, tokenize=True)
    ids = ids["input_ids"] if hasattr(ids, "keys") else ids
    return len(ids)


def local_counter(tokenizer_dir, context):
    """Prompt counter with the model's own chat template (template defaults), for an API without /tokenize."""
    from transformers import AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_dir)
    return lambda sample: (count_prompt(tokenizer, sample), context)


def too_long_prompts(jobs, counts, margin, budgets):
    """(task, index, counted prompt, window) of every job whose counted prompt + margin + RULER's answer budget
    exceeds the window: one is enough to skip the whole length (PROTOCOL.md: `score: null`, not cut down)."""
    return [(task, s["index"], n, ctx) for (task, s), (n, ctx) in zip(jobs, counts)
            if n + margin + budgets[task] > ctx]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--length-dir", type=Path, required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--temperature", type=float, required=True)
    ap.add_argument("--top-p", type=float, required=True)
    ap.add_argument("--ruler-dir", type=Path, required=True, help="the pinned RULER checkout (answer budgets)")
    ap.add_argument("--chat-template-kwargs", type=json.loads, default=None)
    ap.add_argument("--api-key-env", default=None, help="name of the environment variable that holds the key")
    ap.add_argument("--tokenizer", default=None, help="count prompts locally with this tokenizer (no /tokenize)")
    ap.add_argument("--context", type=int, default=None, help="context window, with --tokenizer")
    ap.add_argument("--margin", type=int, default=0, help="tokens kept free beyond the counted prompt")
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--timeout", type=float, default=7200, help="seconds per request")
    ap.add_argument("--max-retries", type=int, default=8)
    ap.add_argument("--pause-min", type=float, default=PAUSE_MIN, help="seconds; for tests against a mock server")
    args = ap.parse_args()
    if args.tokenizer and not args.context:
        ap.error("--tokenizer needs --context")
    with generation_lock(args.length_dir, "predict.py"):
        generate_length(args)


def generate_length(args):
    length = int(args.length_dir.name)
    budgets = answer_budgets(args.ruler_dir)
    api_key = None
    if args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            sys.exit(f"predict.py: set {args.api_key_env}")
    client = Client(args.base_url, args.timeout, args.max_retries, Gate(args.pause_min, max(args.pause_min, PAUSE_MAX)),
                    api_key, EventLog(args.length_dir / EVENTS, length))
    extra = {"chat_template_kwargs": args.chat_template_kwargs} if args.chat_template_kwargs else {}
    raw_dir = args.length_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pending = {}  # task -> samples still without an output
    for task in args.tasks:
        if (args.length_dir / "data" / task / "skip.json").exists():  # RULER could not generate it (run.sh)
            print(f"predict.py: {task} @ {length}: skipped, no RULER data")
            continue
        samples = read_jsonl(args.length_dir / "data" / task / "validation.jsonl")
        if not samples:
            sys.exit(f"predict.py: no data for {task} at {length}")
        done = {i for i, r in latest_records(raw_dir / f"{task}.jsonl").items() if "output" in r}
        pending[task] = [s for s in samples if s["index"] not in done]
        print(f"predict.py: {task} @ {length}: {len(samples) - len(pending[task])} done, {len(pending[task])} to send")
    jobs = [(task, s) for task, samples in pending.items() for s in samples]
    if not jobs:
        return

    if args.tokenizer:
        counter = local_counter(args.tokenizer, args.context)
        counts = [counter(s) for _, s in jobs]
    else:
        def count(job):
            """(templated prompt tokens, window); the token list itself is dropped (up to 131k ints)."""
            body = {"model": args.model, "messages": messages(job[1]), "add_generation_prompt": True, **extra}
            response = client.post("/tokenize", body, job[0], job[1]["index"])
            return response["count"], response["max_model_len"]
        with ThreadPoolExecutor(max_workers=min(args.concurrency, 16)) as pool:
            counts = list(pool.map(count, jobs))

    # Samples with an output already passed this check on an earlier run.
    too_long = too_long_prompts(jobs, counts, args.margin, budgets)
    if too_long:
        task, index, n, ctx = max(too_long, key=lambda t: t[2])
        reason = (f"{len(too_long)} of {len(jobs)} prompts do not fit: with the chat template the longest "
                  f"({task} #{index}) has {n} tokens, which with a {args.margin}-token margin and RULER's answer "
                  f"budget of {budgets[task]} exceeds the {ctx}-token context window")
        (args.length_dir / "skip.json").write_text(json.dumps({"reason": reason}, indent=2) + "\n", encoding="utf-8")
        print(f"predict.py: {length} skipped: {reason}")
        return

    def generate(task, sample, n, ctx):
        body = request_body(args, sample, n, ctx, extra)
        try:
            response = client.post("/v1/chat/completions", body, task, sample["index"])
            choice = response["choices"][0]
            record = {"index": sample["index"], "output": choice["message"]["content"] or "",
                      "finish_reason": choice["finish_reason"], "prompt_tokens": response["usage"]["prompt_tokens"],
                      "counted_prompt_tokens": n, "output_tokens": response["usage"]["completion_tokens"]}
        except RuntimeError as e:
            record = {"index": sample["index"], "error": str(e)}
        return task, record

    files = {task: open(raw_dir / f"{task}.jsonl", "a", encoding="utf-8", buffering=1) for task in pending}
    errors, gaps = 0, []
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = [pool.submit(generate, task, s, n, ctx) for (task, s), (n, ctx) in zip(jobs, counts)]
            for i, future in enumerate(as_completed(futures), 1):
                task, record = future.result()
                files[task].write(json.dumps(record, ensure_ascii=False) + "\n")
                errors += "error" in record
                if "output" in record:
                    gaps.append(record["prompt_tokens"] - record["counted_prompt_tokens"])
                if i % 50 == 0 or i == len(jobs):
                    print(f"predict.py: {length}: {i}/{len(jobs)} ({errors} errors)")
    finally:
        for f in files.values():
            f.close()
    if gaps:
        print(f"predict.py: server prompt tokens minus counted: min {min(gaps)}, max {max(gaps)} "
              f"(margin {args.margin})")
        if max(gaps) > args.margin:
            print(f"predict.py: WARNING: a prompt exceeded the counted size by more than the margin", file=sys.stderr)
    if errors:
        print(f"predict.py: {errors} samples at {length} ended with an error; rerun to retry them", file=sys.stderr)


if __name__ == "__main__":
    main()
