"""lm_eval CLI with request fixes and gentler retries for the Fabryka AI API; otherwise the stock `lm_eval` CLI.

lm-eval 0.4.9.1 builds requests the Fabryka API rejects with 400:
- every chat message gets "type": "text" (models/api_models.py, apply_chat_template):
  "This request field is not supported" (param messages.0.type). Dropped here.
- `ifeval` has no stop sequences, so the request carries "stop": []:
  "Input should contain between 1 and 4 items" (param stop). An empty list is dropped here.

Retries: lm-eval starts one task per prompt, and each retries on its own. During a short burst of 503s that
sent over 100 requests per second to the API, although no more than 4 were in flight. Here every request first
takes one of `num_concurrent` slots and then waits while the API is paused. Any failed request pauses all
requests: 10 s after the first failure, doubling up to 5 minutes while failures continue, back to 10 s after a
success. During an outage the API gets at most `num_concurrent` requests per pause.

EXTRA_BODY (environment, JSON object): fields added to every request, e.g. `chat_template_kwargs` for a vLLM
server (vllm.sh). lm-eval's `--gen_kwargs` cannot pass nested values. The Fabryka API rejects such fields.

Usage: python lm_eval_fabryka.py <lm_eval arguments>
"""

import asyncio
import json
import os
import time

from lm_eval.__main__ import cli_evaluate
from lm_eval.models.openai_completions import LocalChatCompletion

PAUSE_MIN, PAUSE_MAX = 10.0, 300.0

_create_payload = LocalChatCompletion._create_payload
_amodel_call = LocalChatCompletion.amodel_call
_gate = {"slots": None, "resume_at": 0.0, "pause": PAUSE_MIN}
EXTRA_BODY = json.loads(os.environ.get("EXTRA_BODY") or "{}")


def _create_payload_for_fabryka(self, messages, *args, **kwargs):
    messages = [{k: v for k, v in m.items() if k != "type"} for m in messages]
    payload = _create_payload(self, messages, *args, **kwargs)
    if not payload.get("stop"):
        payload.pop("stop", None)
    return {**payload, **EXTRA_BODY}


async def _amodel_call_gently(self, *args, **kwargs):
    if _gate["slots"] is None:
        _gate["slots"] = asyncio.Semaphore(self._concurrent)
    async with _gate["slots"]:
        while (wait := _gate["resume_at"] - time.monotonic()) > 0:
            await asyncio.sleep(wait)
        try:
            result = await _amodel_call(self, *args, **kwargs)
        except Exception:
            _gate["resume_at"] = max(_gate["resume_at"], time.monotonic() + _gate["pause"])
            _gate["pause"] = min(2 * _gate["pause"], PAUSE_MAX)
            raise
        _gate["pause"] = PAUSE_MIN
        return result


LocalChatCompletion._create_payload = _create_payload_for_fabryka
LocalChatCompletion.amodel_call = _amodel_call_gently

if __name__ == "__main__":
    cli_evaluate()
