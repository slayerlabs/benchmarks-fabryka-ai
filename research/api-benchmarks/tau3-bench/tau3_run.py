"""Entry point for `tau2 run` with one change: the model that judges NL assertions is configurable.

The pinned harness (tau2-bench v1.0.1) hardcodes the NL-assertion judge to `gpt-4.1-2025-04-14`
(`tau2.config.DEFAULT_LLM_NL_ASSERTIONS`, imported by value into `tau2.evaluator.evaluator_nl_assertions`) and has no
CLI flag for it. Environment variables set it here, and nothing else in the harness is touched:

  NL_JUDGE_LLM   litellm model id of the judge (required)
  TAU3_USAGE_LOG optional path: append one JSON line of token usage per successful model call
  EMPTY_RETRIES / TAU3_EMPTY_LOG  repeat empty completions (see below) up to N times / log them
  NL_JUDGE_ARGS  JSON dict of extra litellm arguments (default {"temperature": 0.0}, the harness default)

All other arguments are passed to `tau2 run` unchanged: python tau3_run.py run --domain airline ...
"""

import json
import os
import sys
import threading

import litellm
import tau2.evaluator.evaluator_nl_assertions as nl
from tau2.cli import main

nl.DEFAULT_LLM_NL_ASSERTIONS = os.environ["NL_JUDGE_LLM"]
nl.DEFAULT_LLM_NL_ASSERTIONS_ARGS = json.loads(os.environ.get("NL_JUDGE_ARGS") or '{"temperature": 0.0}')

# Usage log: every successful litellm call (also the ones of task attempts that the harness discards and retries, which
# are not in results.json) is appended to $TAU3_USAGE_LOG as one JSON line. The harness's own cost field reads 0 for
# models litellm has no price for.
_LOG, _LOCK = os.environ.get("TAU3_USAGE_LOG"), threading.Lock()


def _log_usage(kwargs, response, start, end):
    u = getattr(response, "usage", None)
    if u is not None:
        line = json.dumps({"model": kwargs.get("model"), "prompt_tokens": u.prompt_tokens,
                           "completion_tokens": u.completion_tokens})
        with _LOCK, open(_LOG, "a") as f:
            f.write(line + "\n")


if _LOG:
    litellm.success_callback = [_log_usage]

# Empty completions. Bielik through the Fabryka API sometimes returns a message with neither content nor tool calls
# (seen in the smoke test, as agent and as simulator); the harness validates every message and aborts the whole task
# attempt with an infrastructure error. Such a call is repeated here, up to EMPTY_RETRIES times (default 5), with the
# same arguments; every repetition is appended to $TAU3_EMPTY_LOG if set. Calls that return something are untouched.
import tau2.utils.llm_utils as _llm

_completion = _llm.completion
_EMPTY_RETRIES = int(os.environ.get("EMPTY_RETRIES", "5"))
_EMPTY_LOG = os.environ.get("TAU3_EMPTY_LOG")


def _completion_no_empty(*args, **kwargs):
    for attempt in range(_EMPTY_RETRIES + 1):
        r = _completion(*args, **kwargs)
        try:
            m = r.choices[0].message
            empty = not (m.content or "").strip() and not m.tool_calls
        except (AttributeError, IndexError):
            empty = False
        if not empty or attempt == _EMPTY_RETRIES:
            return r
        if _EMPTY_LOG:
            with _LOCK, open(_EMPTY_LOG, "a") as f:
                f.write(json.dumps({"model": kwargs.get("model"), "attempt": attempt + 1,
                                "finish_reason": r.choices[0].finish_reason, "content": m.content,
                                "completion_tokens": r.usage.completion_tokens,
                                "n_messages": len(kwargs.get("messages", [])), "has_tools": bool(kwargs.get("tools"))}) + "\n")


_llm.completion = _completion_no_empty

if __name__ == "__main__":
    sys.exit(main())
