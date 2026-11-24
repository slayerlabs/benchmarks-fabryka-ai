# ToolSandbox: setup protocol

Written and committed before the full run (see "Post-result note" at the end for two corrections). Refs #289. The first version of this protocol covered setup and a smoke test
only; the amendment at the end ("Amendment 2026-11-24: measurement") authorizes the measurement and was committed
before the full run started.

## Sources

- Paper: Lu et al. 2024, [ToolSandbox](https://arxiv.org/abs/2408.04682).
- Harness: [apple/ToolSandbox](https://github.com/apple/ToolSandbox) @ `c8571d7854316d2e1c5f288e59fe1e34e53f6dd1`
  (`main`, 2 commits, no tags), installed with the exact pins of its `pyproject.toml` on Python 3.9 (the README's version).
- Data: the scenarios are code in the harness (`tool_sandbox/scenarios`): 1032 scenarios with the default tool backend.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) card, 80.36.

## What the card states and what it does not

States: ToolSandbox "greedy decoding, up to 1024 tokens per turn". Does **not** state: the user simulator, the metric
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
- Slayer 1B: `score: null` (base model, no tool-calling format, not served by the API); see `run.sh slayer1b-1.09-k70000`.

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

## Amendment 2026-11-24: measurement (written before any result)

Authorized spend for this task: 5 USD on the Anthropic API (user simulator). Run: `bash run.sh bielik-11b-v3.1`.

**User simulator: Claude Haiku 5.5 instead of GPT-4o.** The card does not name its simulator; the harness's own are
GPT models on the OpenAI API, which we cannot use. The simulator is `claude-haiku-5-5` through Anthropic's
OpenAI-compatible endpoint (`https://api.anthropic.com/v1/`), called with the harness's own messages and its
`end_conversation` tool, no `temperature` or `top_p` (Claude 5.5 models reject them with HTTP 400). Verified on one
scenario and on 10 (see `out/`, not committed) before the full run. A score from a different simulator is not
directly comparable with the card's 80.36: the comparison in the README is indicative only.

**Agent settings (from the LFM3-1.7B card, see "What the card states"):** greedy decoding (`temperature` 0),
`max_tokens` 1024 per turn, one trial, `--preferred_tool_backend DEFAULT`, the harness's own agent prompt and
maximum of 30 messages per scenario. Bielik gets the tools through the API's `tools` parameter (native function
calling), as the harness's OpenAI agent does.

**Excluded: scenarios that need `RAPID_API_KEY`.** We have no RapidAPI key and will not get one. A scenario needs it
when its tool allow-list (the "necessary tools" of the harness) contains one of the five RapidAPI tools
(`search_lat_lon`, `search_location_around_lat_lon`, `search_weather_around_lat_lon`, `search_stock`,
`convert_currency`); without the key the tool raises `PermissionError`, so the milestone that expects its result can
never match and the scenario scores near 0 for every model. The harness builds 8 variants of each base scenario
(no distraction tools, 3 and 10 distraction tools, all tools, 4 scrambled variants), and all variants of a base are
excluded together. Result: **224 of the 1032 scenarios (28 base scenarios x 8), listed in `rapid_api_scenarios.txt`,
are not run; the evaluated set is 808.** The 10 base scenarios x 8 variants (80 scenarios) named
`*_insufficient_information*` keep a RapidAPI tool in the allow-list only as a minefield (the agent must not call it,
they have no milestones) and stay in the set: calling the tool fails without the key, but the minefield matches on the
attempted call, so the score does not depend on the key. Scenarios in which a model calls a RapidAPI tool by itself in
a scored scenario get the tool's error, as the harness would without a key.

*Correction made before any result was recorded.* The first version of this list had 72 scenarios, found by
searching the milestones' text for the tool names; that missed 152 scenarios whose milestones do not name the tool.
It was caught by comparing with the harness's "necessary tool name" table (160 scenarios with
`search_location_around_lat_lon`, 72 with `search_weather_around_lat_lon`, 16 with `convert_currency`) in the log of a
full run started with the 72-list. That run was stopped after 76 scenarios and discarded (its scores were not
used); the full run was restarted with the 224-list.

**Two wrapper fixes found by the 10-scenario check (without them most scenarios score 0 for reasons unrelated to the
model):**
1. The Fabryka API ids tool calls `chatcmpl-tool-<hex>`; the harness builds a Python variable `<id>_parameters` from
   it, so the hyphens give a SyntaxError on every tool call. `ts_run.py` replaces non-word characters in the id with
   `_` (consistently in the call and in the tool result).
2. The Fabryka API rejects the `name` key of tool-result messages (HTTP 400 "This request field is not supported");
   `ts_run.py` drops it (`tool_call_id` identifies the call).
The smoke test above (similarity 0 for both scenarios) predates these fixes and is superseded.

**Infrastructure errors.** The API was overloaded the day before (HTTP 503 "Inference capacity is busy") and tau3-bench
runs on it at the same time. Concurrency is 2 scenarios. HTTP 429 and 5xx, timeouts and connection errors are retried
with exponential back-off (6 attempts, waits 10, 20, 40, 80, 120 s, jittered); an empty agent reply (no text, no tool
call) is retried twice. A scenario that still fails raises `InfraError`, which `summarize.py` counts as an
**infrastructure error, not as similarity 0**: it is excluded from `n` and `score`, reported separately, and rerun once
after the main pass. Errors that remain after the rerun stay excluded and are reported with their number. Any other
exception (a real model or harness failure) is scored 0, as the harness does, and counted separately. The simulator
cost cap (4.5 USD of the 5 USD, from the `usage` fields of every simulator call, `TS_COST_CAP_USD`) also raises
`InfraError`, so a cap hit would show as unscored scenarios, never as zeros.

**Metric and error.** Score = mean `similarity` x 100 over scored scenarios (the harness's metric, milestone and
minefield matching, no judge model). `stderr` = sample standard deviation of per-scenario similarity / sqrt(n) x 100:
similarity is continuous in [0, 1], so the pass/fail formula of METHODOLOGY.md does not apply. Scenarios share
templates (the harness builds variants by adding distraction tools or scrambling descriptions), so they are not
independent and the stderr is too small.

**Slayer 1B:** `score: null` as in the setup (base model without a tool-calling format, not served by the API).

## Post-result note (2026-11-25, after the result)

Corrections to statements above; the original text is left as it was.

1. **Timing.** "Written before any result" holds for the full run, not for every run: the one-scenario and 10-scenario
   checks (run directories `test1` 12:58 and `test10` 13:02 on 2026-11-24, not committed) ran before the amendment was
   committed (13:03:21), and the first full run started 15 seconds after it. The corrected 224-list was committed at
   13:19:28 and the restarted full run began at 13:19:35. These are local author dates of commits that were not pushed
   before the run; no external timestamp exists.
2. **The discarded run.** The paragraph on the correction says the first full run was stopped after 76 scenarios; its
   progress file (not committed) holds 83 records. The 76 was not re-derived. Those 83 scenarios had a mean similarity of
   0.431; the 18 of them that are in the 224-list averaged 0.108. The list was changed after these scores were seen.
3. **The minefield statement.** The amendment says the 10 `*_insufficient_information*` base scenarios keep a RapidAPI
   tool in the allow-list "only as a minefield" and that "the minefield matches on the attempted call". That is true for 6
   of them (48 scenarios: `search_lat_lon` or `search_weather_around_lat_lon` is the forbidden tool). For the other 4 (32
   scenarios) the forbidden tool is `calculate_lat_lon_distance` or `unit_conversion` and the RapidAPI tool is allowed, so
   the missing key can change what the agent does. `rapid_api_kept_bases.txt` lists the tool per base scenario; the
   README gives the score without these 32 and without all 80.
4. **The standard error.** The amendment's `stderr` (sample sd / sqrt(n)) treats the 808 scenarios as independent. The
   result files give the SE clustered by base scenario as `stderr` and the amendment's as
   `other_metrics.stderr_independent`.

