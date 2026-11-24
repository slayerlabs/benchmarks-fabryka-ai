# ToolSandbox

Refs #289. Setup and deviations: [PROTOCOL.md](PROTOCOL.md) (written before the results).

- Paper: Lu et al. 2024, [ToolSandbox](https://arxiv.org/abs/2408.04682).
- Harness: [apple/ToolSandbox](https://github.com/apple/ToolSandbox) @ `c8571d7854316d2e1c5f288e59fe1e34e53f6dd1`,
  Python 3.9, exact pins of its `pyproject.toml` (plus `httpx==0.27.2`).
- Data: the scenarios are code in the harness: 1032 with the default tool backend; **808 are evaluated**, 224 need a
  paid RapidAPI key and are excluded (see Deviations).
- Metric: mean `similarity` x 100 (milestone and minefield matching, no judge model). `stderr` = sample sd /
  sqrt(n), scenarios treated as independent (they are not: each base scenario has 8 variants), so it is too small.
- Settings: agent Bielik 11B v3.1 through the Fabryka AI API, temperature 0, 1024 tokens per turn (as in the LFM3-1.7B
  card), one trial, at most 30 messages per scenario; user simulator Claude Haiku 5.5 (`claude-haiku-5-5`, Anthropic's
  OpenAI-compatible endpoint).

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1 (API) | 45.18 | 1.49 | 808 | 2026-11-24 |
| Slayer 1B | null | | 0 | |
| LFM3-1.7B, model card | 80.36 | not given | not given | |

Slayer 1B: `score: null`, `results/slayer1b.json` (base model without a tool-calling format, not served by the API).

Bielik is 35.2 points below the card's LFM3-1.7B number (45.18 - 80.36, our SE 1.49, the card gives no SE, so no z can
be computed). That is a rough comparison only: the card's simulator (not named), scenario subset and tool backend are <!-- ocena-bez-se: the card gives no SE, so no z exists -->
unknown, our simulator is Claude Haiku 5.5 and 224 scenarios are missing; the size of the gap makes a reversal by
these differences unlikely but nothing here measures how much they move a score.

Infrastructure errors: 1 scenario hit HTTP 503 after all retries in the main pass, was rerun once and scored
(similarity 0.0); **0 remain**. 2 scenarios scored 0 because Bielik called a tool name that does not exist
(`KeyError` in the harness, which counts it as 0 as in the official run).

Scores by the harness's scenario categories (a scenario has several; these are means of similarity x 100):

| category | score |
|---|---|
| ALL_TOOLS_AVAILABLE | 40.42 |
| ARG_DESCRIPTION_SCRAMBLED | 40.20 |
| ARG_TYPE_SCRAMBLED | 47.35 |
| CANONICALIZATION | 23.85 |
| INSUFFICIENT_INFORMATION | 87.49 |
| MULTIPLE_TOOL_CALL | 22.32 |
| MULTIPLE_USER_TURN | 16.44 |
| NO_DISTRACTION_TOOLS | 48.08 |
| SINGLE_TOOL_CALL | 59.56 |
| SINGLE_USER_TURN | 33.68 |
| STATE_DEPENDENCY | 37.29 |
| TEN_DISTRACTION_TOOLS | 45.71 |
| THREE_DISTRACTION_TOOLS | 45.45 |
| TOOL_DESCRIPTION_SCRAMBLED | 43.79 |
| TOOL_NAME_SCRAMBLED | 47.03 |

`INSUFFICIENT_INFORMATION` is high because 80 of its scenarios only need the agent not to call a tool; categories
with several user turns or several tool calls are low. In the transcripts Bielik answers in Polish although the harness
prompt and the simulator are English (the API's hidden provider system prompt, #277); whether that costs score through
the simulator's replies was not measured.

Each line of `results/bielik-11b-v3.1.jsonl.gz` is one scenario: `task_id`, `categories`, `score`,
`milestone_similarity`, `minefield_similarity`, `turn_count`, `error_type`, `infrastructure_error`, and `output` (the
conversation, with the tool calls).

## Cost and time

The simulator calls cost about 1.3 USD in total (1.13 USD for the final run, from the `usage` fields of every call,
at 0.10 / 0.50 USD per million input / output tokens; the rest are the setup checks and a discarded partial run).
The cap for this task was 5 USD. The final run took about 2.6 hours with 2 scenarios in parallel while tau3-bench used
the same API.

## Deviations

- **User simulator: Claude Haiku 5.5, not GPT-4o.** The harness's simulators are GPT models on the OpenAI API.
- **224 of 1032 scenarios are not run** because their tools need `RAPID_API_KEY`; list in `rapid_api_scenarios.txt`,
  method in PROTOCOL.md (a first list of 72 was wrong and was replaced before any result). A few scored scenarios still
  show the key error when Bielik calls a RapidAPI tool that is only a distraction or a minefield.
- **Two wrapper fixes for the Fabryka API** (tool-call ids with hyphens break the harness's generated code; the `name`
  field of tool messages is rejected), the simulator history is merged into one system message, and the agent sends
  `temperature=0`, `max_tokens=1024`; see PROTOCOL.md. Nothing in the harness clone is edited.
- **The Fabryka API adds a hidden provider system prompt** (#277); context is 32768 tokens.
- **Infrastructure errors** (HTTP 429/5xx, timeouts, empty replies) are retried with back-off and, if they persist,
  excluded from `n` instead of scored 0; here none persisted.
- **stderr** treats scenarios as independent; the 8 variants of a base scenario are correlated.

## Files

`run.sh <model-id> [--limit N | --only FILE]` (`--only` needs an absolute path), `summarize.py` (writes `results/`),
`smoke.sh` (free setup check, not a result), `ts_run.py` (endpoint wrapper, retries, usage log), `common.sh`,
`rapid_api_scenarios.txt`. Reproduce: set `TS_USER_BASE_URL=https://api.anthropic.com/v1/`,
`TS_USER_API_KEY_FILE`, `TS_USER_MODEL=claude-haiku-5-5`, then `bash run.sh bielik-11b-v3.1` and
`python summarize.py bielik-11b-v3.1 out/data/<run> [rerun dir]`.
