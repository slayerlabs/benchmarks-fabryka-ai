"""Entry point for `tau2 run` with one change: the model that judges NL assertions is configurable.

The pinned harness (tau2-bench v1.0.1) hardcodes the NL-assertion judge to `gpt-4.1-2025-04-14`
(`tau2.config.DEFAULT_LLM_NL_ASSERTIONS`, imported by value into `tau2.evaluator.evaluator_nl_assertions`) and has no
CLI flag for it. Environment variables set it here, and nothing else in the harness is touched:

  NL_JUDGE_LLM   litellm model id of the judge (required)
  TAU3_USAGE_LOG optional path: append one JSON line of token usage per successful model call
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

if __name__ == "__main__":
    sys.exit(main())
