"""Send RULER samples of one length to an OpenAI-compatible chat endpoint (vLLM) and store the raw outputs.

Usage: python predict.py --base-url URL --model NAME --length-dir out/<model-id>/<length> --tasks t1 t2 ...
       --seed S --temperature T --top-p P [--chat-template-kwargs JSON] [--concurrency N]

Each sample is one user message: RULER's `input` + `answer_prefix`, as RULER's own OpenAI client sends it
(scripts/pred/call_api.py and client_wrappers.OpenAIClient @ db43f92). The model's chat template is applied by the
server. Output limit: the server's context window minus the templated input (PROTOCOL.md, Settings).

Before any generation, every sample of the length is tokenized through the server's /tokenize with the same
messages. If one does not leave room for RULER's own answer budget, the whole length is written to `skip.json` with
the reason and nothing is generated (PROTOCOL.md: a length the context does not hold gets `score: null`).

Raw records go to <length-dir>/raw/<task>.jsonl, appended, one per attempt that ended:
  {"index", "output", "finish_reason", "prompt_tokens", "output_tokens"}  or  {"index", "error"}.
The last record of an index wins. A rerun skips indices with an output and retries the ones with an error, so a
(task, length) with an output for every sample is not sent again. Only the Python standard library is used.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from ruler import answer_budgets, latest_records, read_jsonl

# Transport failures and server-side overload: retried. Anything else (e.g. 400) is recorded as an error at once.
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


class Client:
    def __init__(self, base_url, model, timeout, max_retries):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    def post(self, path, body):
        """POST JSON with retries on transport errors; returns the decoded response or raises RuntimeError."""
        data = json.dumps(body).encode("utf-8")
        last = None
        for attempt in range(self.max_retries + 1):
            if attempt:
                time.sleep(min(300, 5 * 2 ** (attempt - 1)))
            request = urllib.request.Request(self.base_url + path, data=data,
                                             headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                detail = e.read().decode("utf-8", "replace")[:500]
                last = f"HTTP {e.code}: {detail}"
                if e.code not in RETRY_STATUS:
                    break
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last = f"{type(e).__name__}: {e}"
            print(f"predict.py: {path} attempt {attempt + 1} failed: {last}", file=sys.stderr)
        raise RuntimeError(last)


def messages(sample):
    return [{"role": "user", "content": sample["input"] + sample.get("answer_prefix", "")}]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--length-dir", type=Path, required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--temperature", type=float, required=True)
    ap.add_argument("--top-p", type=float, required=True)
    ap.add_argument("--chat-template-kwargs", type=json.loads, default=None)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--timeout", type=float, default=7200, help="seconds per request")
    ap.add_argument("--max-retries", type=int, default=8)
    ap.add_argument("--ruler-dir", type=Path, required=True, help="the pinned RULER checkout (answer budgets)")
    args = ap.parse_args()

    length = int(args.length_dir.name)
    budgets = answer_budgets(args.ruler_dir)
    client = Client(args.base_url, args.model, args.timeout, args.max_retries)
    extra = {"chat_template_kwargs": args.chat_template_kwargs} if args.chat_template_kwargs else {}
    raw_dir = args.length_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pending = {}  # task -> samples still without an output
    for task in args.tasks:
        samples = read_jsonl(args.length_dir / "data" / task / "validation.jsonl")
        if not samples:
            sys.exit(f"predict.py: no data for {task} at {length}")
        done = {i for i, r in latest_records(raw_dir / f"{task}.jsonl").items() if "output" in r}
        pending[task] = [s for s in samples if s["index"] not in done]
        print(f"predict.py: {task} @ {length}: {len(samples) - len(pending[task])} done, {len(pending[task])} to send")
    jobs = [(task, s) for task, samples in pending.items() for s in samples]
    if not jobs:
        return

    def count(job):
        """(templated prompt tokens, context window); the token list itself is dropped (up to 131k ints)."""
        task, sample = job
        body = {"model": args.model, "messages": messages(sample), "add_generation_prompt": True, **extra}
        response = client.post("/tokenize", body)
        return response["count"], response["max_model_len"]

    # Samples with an output already passed this check on an earlier run.
    with ThreadPoolExecutor(max_workers=min(args.concurrency, 16)) as pool:
        counts = list(pool.map(count, jobs))
    too_long = [(task, s["index"], n, ctx) for (task, s), (n, ctx) in zip(jobs, counts)
                if n + budgets[task] > ctx]
    if too_long:
        task, index, n, ctx = max(too_long, key=lambda t: t[2])
        reason = (f"{len(too_long)} of {len(jobs)} prompts do not fit: with the chat template the longest "
                  f"({task} #{index}) has {n} tokens, which with RULER's answer budget of {budgets[task]} exceeds "
                  f"the {ctx}-token context window")
        (args.length_dir / "skip.json").write_text(json.dumps({"reason": reason}, indent=2) + "\n", encoding="utf-8")
        print(f"predict.py: {length} skipped: {reason}")
        return

    def generate(task, sample, n, ctx):
        body = {"model": args.model, "messages": messages(sample), "temperature": args.temperature,
                "top_p": args.top_p, "seed": args.seed, "max_completion_tokens": ctx - n, **extra}
        try:
            response = client.post("/v1/chat/completions", body)
            choice = response["choices"][0]
            record = {"index": sample["index"], "output": choice["message"]["content"] or "",
                      "finish_reason": choice["finish_reason"], "prompt_tokens": response["usage"]["prompt_tokens"],
                      "output_tokens": response["usage"]["completion_tokens"]}
        except RuntimeError as e:
            record = {"index": sample["index"], "error": str(e)}
        return task, record

    files = {task: open(raw_dir / f"{task}.jsonl", "a", encoding="utf-8", buffering=1) for task in pending}
    errors = 0
    try:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = [pool.submit(generate, task, s, n, ctx) for (task, s), (n, ctx) in zip(jobs, counts)]
            for i, future in enumerate(as_completed(futures), 1):
                task, record = future.result()
                files[task].write(json.dumps(record, ensure_ascii=False) + "\n")
                errors += "error" in record
                if i % 50 == 0 or i == len(jobs):
                    print(f"predict.py: {length}: {i}/{len(jobs)} ({errors} errors)")
    finally:
        for f in files.values():
            f.close()
    if errors:
        print(f"predict.py: {errors} samples at {length} ended with an error; rerun to retry them", file=sys.stderr)


if __name__ == "__main__":
    main()
