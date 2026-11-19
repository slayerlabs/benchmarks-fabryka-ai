"""slayer_server.py v3 - an OpenAI-compatible server (/v1/models, /v1/completions, /v1/chat/completions) for Slayer1B on
slayer_lm.py (fp32, TF32 off), so that API harnesses can run the base model.
Text format:
- completions: the prompt unchanged;
- chat, one user message without a system message: the text is the content alone (the same path as the raw IFEval and
  IFBench prompts), no stop string;
- system (if present): its content + "\\n\\n" before the first turn;
- several turns: "User: {u1}\\n\\nAssistant: {a1}\\n\\nUser: {u2}\\n\\nAssistant:" and the stop "\\n\\nUser:" only on this path.
Sampling: temperature (0..2; 0 = argmax), top_p (0 < p <= 1; absent -> --default-top-p), seed (int; absent ->
--default-seed, logged).
Batching: requests are collected up to --batch (default 32) within --window-ms, prefill per row on the single-row path,
batched decoding (slayer_batch.py); --batch 1 = one at a time (the same decoding code with B=1).
--limit-mode fixed (limit = min(max_tokens, 1280), input + limit > 4096 = 400) or window (limit = min(max_tokens,
4096 - input); no max_tokens = window - input; input >= 4096 = 400 "out of the model's window"). The prompt is never cut.
Restrictions: listens on 127.0.0.1 only; n > 1, tools, functions, response_format, logprobs, stream = 400.
Per-request log without content: requests.jsonl {nr, sha256 of the text, input_tokens, max_tokens, default_limit, limit,
T, top_p, seed, default_seed, stops_n, stops_sha256, batch_n, generated, reason, seconds}.
  python slayer_server.py --pkg <package dir> --port 8001 --log <log dir> [--batch 32 --window-ms 50
                          --limit-mode fixed|window --default-seed 20261119 --default-top-p 1.0]"""
import argparse
import hashlib
import json
import os
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

FIXED_LIMIT = 1280
MODEL_NAME = "slayer"
TURN_STOP = "\n\nUser:"


class RequestError(Exception):
    pass


def chat_text(messages):
    """messages -> (text, until) in the format described above."""
    if not isinstance(messages, list) or not messages:
        raise RequestError("messages: empty list")
    system_parts, turns = [], []
    for m in messages:
        role, content = m.get("role"), m.get("content")
        if isinstance(content, list):  # OpenAI text parts
            if any(c.get("type") != "text" for c in content):
                raise RequestError("text content only")
            content = "".join(c.get("text", "") for c in content)
        if not isinstance(content, str):
            raise RequestError(f"content of role {role!r} is not text")
        if role == "system":
            if turns:
                raise RequestError("system after the first turn")
            system_parts.append(content)
        elif role in ("user", "assistant"):
            turns.append((role, content))
        else:
            raise RequestError(f"role {role!r} is not supported (base model, no tools)")
    if not turns or turns[-1][0] != "user":
        raise RequestError("the last message must be user")
    pre = "".join(s + "\n\n" for s in system_parts)
    if len(turns) == 1:
        return pre + turns[0][1], []
    parts = [("User: " if r == "user" else "Assistant: ") + t for r, t in turns]
    return pre + "\n\n".join(parts) + "\n\nAssistant:", [TURN_STOP]


def sampling_params(b, default_seed, default_top_p=1.0):
    """-> (T, top_p, seed, default_seed_used). Invalid values = 400. No top_p -> default_top_p."""
    t = b.get("temperature", 0)
    t = 0.0 if t is None else t
    p = b.get("top_p", default_top_p)
    p = default_top_p if p is None else p
    s = b.get("seed")
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not 0 <= t <= 2:
        raise RequestError(f"temperature {t!r} outside 0..2")
    if isinstance(p, bool) or not isinstance(p, (int, float)) or not 0 < p <= 1:
        raise RequestError(f"top_p {p!r} outside (0, 1]")
    if s is not None and (isinstance(s, bool) or not isinstance(s, int)):
        raise RequestError(f"seed {s!r} is not an integer")
    return float(t), float(p), (default_seed if s is None else s), s is None


class Engine:
    """Request queue -> BatchGenerator batches; token counting, window, log without content."""

    def __init__(self, lm, gen, log_dir, batch, window_ms, limit_mode, default_seed, default_top_p=1.0):
        self.lm, self.gen = lm, gen
        self.batch, self.window, self.mode, self.default_seed = batch, window_ms / 1000.0, limit_mode, default_seed
        self.default_top_p = default_top_p
        self.q, self.nr, self.lock = queue.Queue(), 0, threading.Lock()
        os.makedirs(log_dir, exist_ok=True)
        self.log = os.path.join(log_dir, "requests.jsonl")
        threading.Thread(target=self._loop, daemon=True).start()

    def limit(self, n_in, max_tokens):
        is_default = max_tokens is None
        if not is_default and (not isinstance(max_tokens, int) or isinstance(max_tokens, bool) or max_tokens <= 0):
            raise RequestError(f"max_tokens {max_tokens!r}")
        blk = self.lm.block
        if self.mode == "fixed":
            lim = FIXED_LIMIT if is_default else min(max_tokens, FIXED_LIMIT)
            if n_in + lim > blk:
                raise RequestError(f"out of the model's window: input {n_in} + limit {lim} > {blk}")
        else:
            if n_in >= blk:
                raise RequestError(f"out of the model's window: input {n_in} >= {blk}")
            lim = blk - n_in if is_default else min(max_tokens, blk - n_in)
        return lim, is_default

    def generate(self, route, text, max_tokens, until, b):
        from slayer_batch import Job
        T, P, S, seed_was_default = sampling_params(b, self.default_seed, self.default_top_p)
        pref = [0] + self.lm.enc(text)  # start token 0 + text, as in slayer_lm.generate_until
        lim, limit_was_default = self.limit(len(pref), max_tokens)
        z = Job(pref, lim, until, T, P, S)
        ev, result = threading.Event(), {}
        self.q.put((z, ev, result))
        ev.wait()
        if "error" in result:
            raise RuntimeError(result["error"])
        text_out, generated, reason = result["out"]
        with self.lock:
            self.nr += 1
            nr = self.nr
            entry = {"nr": nr, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "route": route,
                     "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "input_tokens": len(pref),
                     "max_tokens": max_tokens, "default_limit": limit_was_default, "limit_mode": self.mode, "limit": lim,
                     "T": T, "top_p": P, "seed": S, "default_seed": seed_was_default, "stops_n": len(until),
                     "stops_sha256": hashlib.sha256(json.dumps(list(until), ensure_ascii=False).encode("utf-8")).hexdigest(),
                     "batch_n": result["batch_n"], "generated": generated, "reason": reason, "seconds": result["seconds"]}
            with open(self.log, "a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(entry) + "\n")
        fr = {"eos": "stop", "until": "stop"}.get(reason, "length")
        return text_out, fr, {"prompt_tokens": len(pref), "completion_tokens": generated, "total_tokens": len(pref) + generated}, lim, nr

    def _loop(self):
        while True:
            items = [self.q.get()]
            deadline = time.time() + self.window
            while len(items) < self.batch:
                try:
                    items.append(self.q.get(timeout=max(0.0, deadline - time.time())))
                except queue.Empty:
                    break
            t0 = time.time()
            try:
                out = self.gen.generate([x[0] for x in items])
                for (z, ev, w), o in zip(items, out):
                    w.update(out=o, batch_n=len(items), seconds=round(time.time() - t0, 2))
                    ev.set()
            except Exception as e:  # batch error: every request of the batch gets 500, the server keeps running
                for z, ev, w in items:
                    w["error"] = f"{type(e).__name__}"
                    ev.set()


def check_params(b):
    if int(b.get("n", 1) or 1) != 1:
        raise RequestError("n > 1 is not supported")
    for k in ("tools", "functions", "response_format", "logprobs", "tool_choice"):
        if b.get(k) not in (None, False, [], "none"):
            raise RequestError(f"{k} is not supported (base model without tools or formats)")
    if b.get("stream"):
        raise RequestError("stream is not supported")


def request_stops(b):
    s = b.get("stop")
    if s is None:
        return []
    return [s] if isinstance(s, str) else list(s)


def make_handler(engine):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # no content or paths on stdout
            pass

        def _json(self, code, obj):
            data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path.rstrip("/") == "/v1/models":
                return self._json(200, {"object": "list", "data": [{"id": MODEL_NAME, "object": "model", "owned_by": "local",
                                                                    "max_model_len": engine.lm.block}]})
            self._json(404, {"error": {"message": "not found"}})

        def do_POST(self):
            try:
                b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                if b.get("model") not in (None, MODEL_NAME):
                    raise RequestError(f"model {b.get('model')!r} != {MODEL_NAME}")
                check_params(b)
                if self.path.rstrip("/") == "/v1/completions":
                    p = b.get("prompt")
                    if isinstance(p, list) and len(p) == 1 and isinstance(p[0], str):
                        p = p[0]
                    if not isinstance(p, str):
                        raise RequestError("prompt: a single text")
                    answer, reason, usage, limit, nr = engine.generate("completions", p, b.get("max_tokens"), request_stops(b), b)
                    return self._json(200, {"id": f"cmpl-{nr}", "object": "text_completion", "model": MODEL_NAME,
                                            "created": int(time.time()), "usage": usage, "output_limit": limit,
                                            "choices": [{"index": 0, "text": answer, "finish_reason": reason, "logprobs": None}]})
                if self.path.rstrip("/") == "/v1/chat/completions":
                    text, until = chat_text(b.get("messages"))
                    until = until + request_stops(b)
                    mt = b.get("max_completion_tokens", b.get("max_tokens"))
                    answer, reason, usage, limit, nr = engine.generate("chat", text, mt, until, b)
                    return self._json(200, {"id": f"chatcmpl-{nr}", "object": "chat.completion", "model": MODEL_NAME,
                                            "created": int(time.time()), "usage": usage, "output_limit": limit,
                                            "choices": [{"index": 0, "finish_reason": reason,
                                                         "message": {"role": "assistant", "content": answer}}]})
                self._json(404, {"error": {"message": "not found"}})
            except RequestError as e:
                self._json(400, {"error": {"message": str(e), "type": "invalid_request_error"}})
            except (ValueError, TypeError) as e:
                self._json(400, {"error": {"message": f"bad request: {type(e).__name__}", "type": "invalid_request_error"}})
            except RuntimeError as e:
                self._json(500, {"error": {"message": f"generation error: {e}", "type": "server_error"}})

    return H


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pkg", required=True)
    ap.add_argument("--port", type=int, default=8001)
    ap.add_argument("--log", default="out/server-log")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--window-ms", type=int, default=50)
    ap.add_argument("--limit-mode", choices=("fixed", "window"), default="fixed")
    ap.add_argument("--default-seed", type=int, default=20261119)
    ap.add_argument("--default-top-p", type=float, default=1.0)
    a = ap.parse_args()
    if not 1 <= a.batch <= 64 or not 0 <= a.window_ms <= 1000 or not 0 < a.default_top_p <= 1:
        raise SystemExit("STOP: --batch 1..64, --window-ms 0..1000, --default-top-p (0, 1]")
    import slayer_lm
    import slayer_batch
    lm = slayer_lm.build_lm()(a.pkg, "cuda", 32, kv=True)
    gen = slayer_batch.BatchGenerator(lm)
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(Engine(lm, gen, a.log, a.batch, a.window_ms, a.limit_mode,
                                                                         a.default_seed, a.default_top_p)))
    print(f"SLAYER-SERVER-OK v3 127.0.0.1:{a.port} block {lm.block} mode {a.limit_mode} batch {a.batch} window {a.window_ms} ms "
          f"default_seed {a.default_seed} default_top_p {a.default_top_p} step {lm.cfg.get('step')} "
          f"ckpt {str(lm.cfg.get('ckpt_sha256'))[:8]}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
