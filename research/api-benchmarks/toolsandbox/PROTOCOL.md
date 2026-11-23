# ToolSandbox: setup protocol

Written and committed before any result. Refs #289. This directory is **setup and a smoke test only**: no
measurement of any model has been run, and none is planned in this protocol. A measurement (or a user-simulator probe
like the one in `../tau3-bench/PROTOCOL.md`) needs its own amendment here first.

## Sources

- Paper: Lu et al. 2024, [ToolSandbox](https://arxiv.org/abs/2408.04682).
- Harness: [apple/ToolSandbox](https://github.com/apple/ToolSandbox) @ `c8571d7854316d2e1c5f288e59fe1e34e53f6dd1`
  (`main`, 2 commits, no tags), installed with the exact pins of its `pyproject.toml` on Python 3.9 (the README's version).
- Data: the scenarios are code in the harness (`tool_sandbox/scenarios`): 1032 scenarios with the default tool backend.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) card, 80.36.

## What the card states and what it does not

States: ToolSandbox "greedy decoding, up to 1,024 tokens per turn". Does **not** state: the user simulator, the metric
(the harness reports mean `similarity`, 0 to 1, from milestone and minefield matching, no judge model), the tool
backend, the subset, whether scenarios with `RAPID_API_KEY` tools were run. Our assumptions: all 1032 scenarios,
`--preferred_tool_backend DEFAULT`, score = mean similarity x 100.

## Settings

- Agent: Bielik 11B v3.1 through the Fabryka AI API (OpenAI-compatible, `https://fabryka.ai/v1`), temperature 0,
  `max_tokens` 1024 per turn, 2 workers.
- User simulator: configurable (`TS_USER_BASE_URL`, `TS_USER_API_KEY_FILE`, `TS_USER_MODEL`). The harness's own
  simulators are GPT-3.5/4/4o on the OpenAI API; the card does not name its simulator. Candidates, as in tau3-bench:
  Claude Haiku 5.5 and Sonnet 5.5 through Anthropic's OpenAI-compatible endpoint (not tested).
- The harness hardcodes `https://api.openai.com/v1` in its OpenAI roles, so `ts_run.py` registers two roles with
  configurable endpoints in the harness's factory tables. Nothing in the clone is edited.

## Known risks for a full run

- Some scenarios call a search tool that needs `RAPID_API_KEY` (a paid external service). The harness scores a scenario
  that raises an exception as similarity 0, so a missing key silently lowers the score. Count and list such
  scenarios (`exception_type` in the result summary) before reading any score.
- The Fabryka API adds a hidden provider system prompt (#277), and its context is 32 768 tokens.
- Slayer 1B: `score: null` (base model, no tool-calling format, not served by the API); see `run.sh slayer1b`.

## Deviations of the wrapper

- `httpx==0.27.2` is installed on top of the harness pins: `openai==1.17.0` passes `proxies=` to httpx, which httpx
  0.28 removed, and the harness does not pin httpx.
- The simulator's message history holds several system messages (its few-shot conversations). They are merged, in
  order, into one leading system message (`_hoist_system` in `ts_run.py`): the Fabryka API rejects system messages
  after the first (HTTP 400 "The model rejected this request"), and Anthropic's OpenAI-compatible endpoint hoists
  them the same way. This applies to every simulator model.
- The agent sends `temperature=0` and `max_tokens=1024`, as the card says; the harness's stock agent sends neither.

## Smoke test (not a result)

`smoke.sh`: 2 scenarios (`send_message_with_contact_content_cellular_off_multiple_user_turn`,
`find_temperature_f_with_location_and_time_diff_multiple_user_turn`), Bielik as agent and as user simulator, 2026-11-23.
Both ran to the end (26 and 30 messages) with no exception and wrote transcripts; similarity 0.0 for both. Its output is
not written to `results/` and is not a result.
