"""Entry point for the ToolSandbox CLI with configurable endpoints, without editing the pinned clone.

The harness hardcodes `base_url="https://api.openai.com/v1"` in its OpenAI agent and user roles and fixes the role
types in an enum. This script registers two roles in the slot `GPT_4_o_2024_05_13` of the harness's factory tables
(select them with `--agent GPT_4_o_2024_05_13 --user GPT_4_o_2024_05_13`). Registration is at module level, so it also
holds in the worker processes the harness spawns.

Environment:
  TS_AGENT_BASE_URL, TS_AGENT_API_KEY_FILE, TS_AGENT_MODEL     agent endpoint (default: Fabryka AI API, Bielik 11B v3.1)
  TS_USER_BASE_URL,  TS_USER_API_KEY_FILE,  TS_USER_MODEL      user simulator endpoint (default: same as the agent)
  TS_USAGE_LOG        JSONL file; every model call appends its token usage (role, model, prompt/completion tokens)
  TS_COST_CAP_USD, TS_USER_PRICE_IN, TS_USER_PRICE_OUT          simulator spend guard (USD, USD per 1M tokens)
Infrastructure errors (HTTP 429/5xx, timeouts, an empty agent reply after retries, the cost cap) raise `InfraError`;
the harness records such a scenario as similarity 0 with exception_type "InfraError", and `summarize.py` counts it
separately and does not score it.
Keys are read from the files and never printed. Card settings for the agent: greedy decoding, up to 1,024 tokens per
turn (LFM3-1.7B card, "Evaluation details"); the stock agent sends neither.
"""
import json
import os
import random
import re
import time
from pathlib import Path
from typing import Any

import openai

from openai import OpenAI

import tool_sandbox.cli.utils as U
from tool_sandbox.cli import main
from tool_sandbox.common.utils import all_logging_disabled
from tool_sandbox.roles.openai_api_agent import OpenAIAPIAgent
from tool_sandbox.roles.openai_api_user import OpenAIAPIUser

FABRYKA = "https://fabryka.ai/v1"
FABRYKA_KEY = "~/.config/fabryka-api.key"


def _client(prefix: str) -> OpenAI:
    base = os.environ.get(f"{prefix}_BASE_URL") or os.environ.get("TS_AGENT_BASE_URL") or FABRYKA
    keyfile = os.environ.get(f"{prefix}_API_KEY_FILE") or os.environ.get("TS_AGENT_API_KEY_FILE") or FABRYKA_KEY
    return OpenAI(base_url=base, api_key=Path(keyfile).expanduser().read_text().strip(), max_retries=0)


def _model(prefix: str) -> str:
    return os.environ.get(f"{prefix}_MODEL") or os.environ.get("TS_AGENT_MODEL") or "bielik-11b-v3.1"


class InfraError(RuntimeError):
    """The API did not deliver (overload, timeout, empty reply, cost cap): not a model failure."""


BACKOFF = [10, 20, 40, 80, 120]   # 6 attempts


def _log_usage(role: str, model: str, usage: Any) -> None:
    path = os.environ.get("TS_USAGE_LOG")
    if path and usage is not None:
        with open(path, "a") as f:   # single short append: atomic enough across the 2 worker processes
            f.write(json.dumps({"role": role, "model": model, "prompt": usage.prompt_tokens,
                                "completion": usage.completion_tokens}) + "\n")


def spent_usd() -> float:
    path = os.environ.get("TS_USAGE_LOG")
    if not path or not Path(path).exists():
        return 0.0
    pin, pout = float(os.environ.get("TS_USER_PRICE_IN", "0.10")), float(os.environ.get("TS_USER_PRICE_OUT", "0.50"))
    tot = 0.0
    for line in Path(path).read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r["role"] == "user":
            tot += (r["prompt"] * pin + r["completion"] * pout) / 1e6
    return tot


def _call(role: str, model: str, make: Any, empty_is_error: bool) -> Any:
    last: Any = None
    for i in range(len(BACKOFF) + 1):
        try:
            with all_logging_disabled():
                r = make()
            _log_usage(role, model, r.usage)
            m = r.choices[0].message
            if empty_is_error and not m.tool_calls and not (m.content or "").strip():
                last = "empty reply"
                if i >= 2:
                    break
                time.sleep(2)
                continue
            return r
        except (openai.APIStatusError, openai.APIConnectionError, openai.APITimeoutError) as e:
            code = getattr(e, "status_code", None)
            if code is not None and code < 500 and code != 429:
                raise   # 4xx other than 429 is a real request problem, not infrastructure
            last = f"HTTP {code}" if code else type(e).__name__
            if i == len(BACKOFF):
                break
            time.sleep(BACKOFF[i] * random.uniform(0.8, 1.2))
    raise InfraError(f"{role}: {last} after retries")


def _strip_tool_name(messages):
    """The Fabryka API answers HTTP 400 "This request field is not supported" (param messages.N.name) to the `name` key
    the harness puts on tool-result messages; `tool_call_id` already identifies the call."""
    return [{k: v for k, v in m.items() if not (m.get("role") == "tool" and k == "name")} for m in messages]


class ConfiguredAgent(OpenAIAPIAgent):
    model_name = _model("TS_AGENT")

    def __init__(self) -> None:
        self.openai_client = _client("TS_AGENT")

    def model_inference(self, openai_messages: Any, openai_tools: Any) -> Any:
        r = _call("agent", self.model_name, lambda: self.openai_client.chat.completions.create(
            model=self.model_name, messages=_strip_tool_name(openai_messages), tools=openai_tools, temperature=0,
            max_tokens=1024), empty_is_error=True)
        # The harness turns the tool-call id into a Python variable name (`<id>_parameters = {...}`). The Fabryka API
        # returns ids like "chatcmpl-tool-9a1a..." whose hyphens make that a SyntaxError, so every call would fail.
        for tc in r.choices[0].message.tool_calls or []:
            tc.id = re.sub(r"\W", "_", tc.id)
        return r


def _hoist_system(messages):
    """One leading system message. The harness's simulator history holds several system messages in the middle (its
    few-shot conversations); the Fabryka API answers HTTP 400 "The model rejected this request" to that, and
    Anthropic's OpenAI-compatible endpoint hoists system messages the same way. Order and text are kept."""
    system = [m["content"] for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    return ([{"role": "system", "content": "\n\n".join(system)}] if system else []) + rest


class ConfiguredUser(OpenAIAPIUser):
    model_name = _model("TS_USER")

    def __init__(self) -> None:
        self.openai_client = _client("TS_USER")

    def model_inference(self, openai_messages: Any, openai_tools: Any) -> Any:
        cap = os.environ.get("TS_COST_CAP_USD")
        if cap and spent_usd() >= float(cap):
            raise InfraError(f"simulator cost cap {cap} USD reached")
        # no temperature / top_p: Claude 5.5 models reject them (HTTP 400)
        return _call("user", self.model_name, lambda: self.openai_client.chat.completions.create(
            model=self.model_name, messages=_hoist_system(openai_messages), tools=openai_tools),
            empty_is_error=False)


def run_scenario_logged(name_and_scenario, *, agent_type, user_type, output_directory):
    """Original run_scenario, plus one line per finished scenario in <output>/progress.jsonl (the harness writes its
    summary only at the very end, so a killed run would otherwise lose every score)."""
    res = U.run_scenario(name_and_scenario, agent_type=agent_type, user_type=user_type,
                         output_directory=output_directory)
    with open(Path(output_directory) / "progress.jsonl", "a") as f:
        f.write(json.dumps(res, default=str) + "\n")
    return res


SLOT = U.RoleImplType.GPT_4_o_2024_05_13
U.AGENT_TYPE_TO_FACTORY[SLOT] = ConfiguredAgent
U.USER_TYPE_TO_FACTORY[SLOT] = ConfiguredUser

import tool_sandbox.cli as C
C.run_scenario = run_scenario_logged

if __name__ == "__main__":
    main()
