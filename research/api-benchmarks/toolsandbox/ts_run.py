"""Entry point for the ToolSandbox CLI with configurable endpoints, without editing the pinned clone.

The harness hardcodes `base_url="https://api.openai.com/v1"` in its OpenAI agent and user roles and fixes the role
types in an enum. This script registers two roles in the slot `GPT_4_o_2024_05_13` of the harness's factory tables
(select them with `--agent GPT_4_o_2024_05_13 --user GPT_4_o_2024_05_13`). Registration is at module level, so it also
holds in the worker processes the harness spawns.

Environment:
  TS_AGENT_BASE_URL, TS_AGENT_API_KEY_FILE, TS_AGENT_MODEL     agent endpoint (default: Fabryka AI API, Bielik 11B v3.1)
  TS_USER_BASE_URL,  TS_USER_API_KEY_FILE,  TS_USER_MODEL      user simulator endpoint (default: same as the agent)
Keys are read from the files and never printed. Card settings for the agent: greedy decoding, up to 1,024 tokens per
turn (LFM3-1.7B card, "Evaluation details"); the stock agent sends neither.
"""
import os
from pathlib import Path
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential

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


class ConfiguredAgent(OpenAIAPIAgent):
    model_name = _model("TS_AGENT")

    def __init__(self) -> None:
        self.openai_client = _client("TS_AGENT")

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(5))
    def model_inference(self, openai_messages: Any, openai_tools: Any) -> Any:
        with all_logging_disabled():
            return self.openai_client.chat.completions.create(
                model=self.model_name, messages=openai_messages, tools=openai_tools, temperature=0, max_tokens=1024)


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

    @retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(5))
    def model_inference(self, openai_messages: Any, openai_tools: Any) -> Any:
        with all_logging_disabled():
            return self.openai_client.chat.completions.create(
                model=self.model_name, messages=_hoist_system(openai_messages), tools=openai_tools)


SLOT = U.RoleImplType.GPT_4_o_2024_05_13
U.AGENT_TYPE_TO_FACTORY[SLOT] = ConfiguredAgent
U.USER_TYPE_TO_FACTORY[SLOT] = ConfiguredUser

if __name__ == "__main__":
    main()
