"""generate.py - answers from an OpenAI-compatible chat endpoint for a question file, one request per question.
Input rows {idx, id, system, user} (system = the AA OMNISCIENCE_ANSWER_PROMPT, user = the question) or {idx, prompt}. The
answer key is never in the input (grading is a separate step). Parameters are explicit and saved in meta: --temperature,
--top-p, --seed-base (seed = base + idx), --max-tokens (0 = no limit in the request, i.e. window - prompt on the
server). One attempt per question; a transport error = no answer with its cause (not a zero); retried only on
transport errors (up to 2 more times), never based on the content.
  python generate.py --api http://127.0.0.1:8000/v1 --model bielik --input questions.jsonl --n 600 --kwargs '{...}'
                     --temperature 0.6 --top-p 0.95 --seed-base 20261119 --max-tokens 0 --output answers.json"""

import argparse
import concurrent.futures as cf
import hashlib
import json
import time

import httpx


def messages(w):
    if "prompt" in w and "user" not in w:
        return [{"role": "user", "content": w["prompt"]}]
    if "user" in w:
        m = [{"role": "system", "content": w["system"]}] if w.get("system") else []
        return m + [{"role": "user", "content": w["user"]}]
    raise SystemExit(f"STOP: row idx {w.get('idx')} without prompt/user")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--kwargs", required=True)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=None)
    ap.add_argument("--seed-base", type=int, default=None)
    ap.add_argument("--max-tokens", type=int, required=True)
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    kw = json.loads(a.kwargs)
    raw = open(a.input, "rb").read()
    rows = [
        json.loads(l) for l in raw.decode("utf-8").split("\n") if l.strip()
    ]  # not splitlines: \u2028 etc. in the text
    if len(rows) != a.n or [w["idx"] for w in rows] != list(range(a.n)):
        raise SystemExit(f"STOP: input has {len(rows)} rows (expected {a.n}) or idx is not 0..n-1")
    if any(k in w for w in rows for k in ("answer", "correct_index", "correct_answer", "Correct Answer")):
        raise SystemExit("STOP: answer-key field in the input file")
    if a.max_tokens < 0 or a.temperature < 0 or (a.top_p is not None and not 0 < a.top_p <= 1):
        raise SystemExit(f"STOP: parameters {a.max_tokens} {a.temperature} {a.top_p}")
    client = httpx.Client(timeout=3600)

    def one(w):
        body = {"model": a.model, "temperature": a.temperature, "chat_template_kwargs": kw, "messages": messages(w)}
        if a.max_tokens:
            body["max_tokens"] = a.max_tokens
        if a.top_p is not None:
            body["top_p"] = a.top_p
        if a.seed_base is not None:
            body["seed"] = a.seed_base + w["idx"]
        error = None
        for attempt in range(3):
            try:
                r = client.post(f"{a.api}/chat/completions", json=body)
                r.raise_for_status()
                j = r.json()
                c = j["choices"][0]
                return str(w["idx"]), {
                    "id": w.get("id"),
                    "response": c["message"].get("content"),
                    "finish_reason": c.get("finish_reason"),
                    "usage": j.get("usage"),
                    "transport_attempts": attempt + 1,
                    "error": None,
                }
            except Exception as e:  # transport/HTTP - retried, the content is not judged
                error = repr(e)[:300]
                time.sleep(5)
        return str(w["idx"]), {
            "id": w.get("id"),
            "response": None,
            "finish_reason": None,
            "usage": None,
            "transport_attempts": 3,
            "error": error,
        }

    t0 = time.time()
    with cf.ThreadPoolExecutor(a.concurrency) as ex:
        results = dict(ex.map(one, rows))
    meta = {
        "model": a.model,
        "api": a.api,
        "input_sha256": hashlib.sha256(raw).hexdigest(),
        "chat_template_kwargs": kw,
        "temperature": a.temperature,
        "top_p": a.top_p,
        "max_tokens": a.max_tokens or "window - prompt (no limit in the request)",
        "seed": None if a.seed_base is None else f"{a.seed_base} + idx",
        "n": len(rows),
        "errors": sum(1 for v in results.values() if v["error"]),
        "cut_at_length": sum(1 for v in results.values() if v["finish_reason"] == "length"),
        "empty": sum(1 for v in results.values() if v["response"] is not None and not v["response"].strip()),
        "seconds": round(time.time() - t0, 1),
    }
    json.dump({"meta": meta, "answers": results}, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(
        f"GENERATE-OK n={meta['n']} errors={meta['errors']} cut={meta['cut_at_length']} empty={meta['empty']} {meta['seconds']} s"
    )


if __name__ == "__main__":
    main()
