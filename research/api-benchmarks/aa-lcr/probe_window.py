"""Measure the real context window of Bielik 11B v3.1 through the Fabryka AI API, instead of assuming the 32768 that
`GET /v1/models` lists.

Sends chat requests whose templated prompt (the model's chat template with its defaults, which include the provider
system prompt the API adds, counted locally) has a chosen token count, `max_tokens` 1, and records the HTTP status,
the error text and the server's own `usage.prompt_tokens`. The text is the start of AA-LCR question 9's prompt, cut to
size. The last probe is the shortest real AA-LCR prompt, whole.

Run: FABRYKA_API_KEY=... python probe_window.py   (the key is read from the environment and never printed or stored)
Writes results/api-window.json.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import common

BASE = "https://fabryka.ai"
MODEL = "bielik-11b-v3.1"
TARGETS = [1000, 16000, 30000, 32000, 32700, 32767, 32768, 32769, 33000, 40000, 65536]   # templated prompt tokens
OUT = common.HERE / "results" / "api-window.json"


def call(key, body, timeout=600):
    req = urllib.request.Request(f"{BASE}/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
            return {"status": r.status, "usage": d.get("usage"), "finish_reason": d["choices"][0].get("finish_reason"),
                    "seconds": round(time.time() - t0, 1)}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "error": e.read().decode("utf-8", "replace")[:600], "seconds": round(time.time() - t0, 1)}
    except Exception as e:   # noqa: BLE001 - recorded, not hidden
        return {"status": None, "error": f"{type(e).__name__}: {e}"[:300], "seconds": round(time.time() - t0, 1)}


def main():
    key = os.environ.get("FABRYKA_API_KEY")
    if not key:
        sys.exit("probe_window.py: set FABRYKA_API_KEY")
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(snapshot_download(
        common.BIELIK_REPO, revision=common.BIELIK_REVISION,
        allow_patterns=["tokenizer*", "special_tokens_map.json", "chat_template*", "config.json"]))
    rows, lcr, _ = common.fetch_data()
    q9 = next(r for r in rows if r["question_id"] == "9")
    ids = tok(common.build_prompt(q9, lcr), add_special_tokens=False)["input_ids"]

    def templated(text):
        return len(tok.apply_chat_template([{"role": "user", "content": text}], tokenize=True,
                                           add_generation_prompt=True, return_dict=True)["input_ids"])

    def text_for(target):
        """Cut the text until the templated count is exactly `target` (re-tokenizing after decode can shift by a few)."""
        n = target - 1060
        for _ in range(8):
            text = tok.decode(ids[:n])
            got = templated(text)
            if got == target:
                return text, got
            n += target - got
        return text, got

    probes = []
    for target in TARGETS:
        text, got = text_for(target)
        r = call(key, {"model": MODEL, "messages": [{"role": "user", "content": text}], "max_tokens": 1,
                       "temperature": 0.0})
        probes.append({"target_templated_tokens": target, "local_templated_tokens": got, **r})
        print(probes[-1], flush=True)
    shortest = min(rows, key=lambda r: len(tok(common.build_prompt(r, lcr), add_special_tokens=False)["input_ids"]))
    text = common.build_prompt(shortest, lcr)
    got = templated(text)
    r = call(key, {"model": MODEL, "messages": [{"role": "user", "content": text}], "max_tokens": 1, "temperature": 0.0})
    probes.append({"target_templated_tokens": "shortest AA-LCR prompt (question %s)" % shortest["question_id"],
                   "local_templated_tokens": got, **r})
    print(probes[-1], flush=True)
    models = json.load(urllib.request.urlopen(urllib.request.Request(
        f"{BASE}/v1/models", headers={"Authorization": f"Bearer {key}"})))
    OUT.write_text(json.dumps({
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"), "endpoint": f"{BASE}/v1/chat/completions",
        "model": MODEL, "listed_context_length": next(m["context_length"] for m in models["data"] if m["id"] == MODEL),
        "request": "messages = one user message, max_tokens 1, temperature 0",
        "note": "usage.prompt_tokens is the server's count, including the provider system prompt",
        "probes": probes}, indent=1) + "\n")


if __name__ == "__main__":
    sys.exit(main())
