# ToolSandbox

Refs #289. Setup, measurement plan and post-result corrections: [PROTOCOL.md](PROTOCOL.md).

- Paper: Lu et al. 2024, [ToolSandbox](https://arxiv.org/abs/2408.04682).
- Harness: [apple/ToolSandbox](https://github.com/apple/ToolSandbox) @ `c8571d7854316d2e1c5f288e59fe1e34e53f6dd1`,
  Python 3.9.6, installed from the clone with its own pins, then every dependency version of the runs from
  `requirements.lock.txt` (`common.sh`).
- Data: the scenarios are code in the harness: 1032 with the default tool backend, 129 base scenarios x 8 variants.
  **808 are evaluated** (101 base scenarios x 8); 224 (28 base scenarios x 8) need a paid RapidAPI key and are excluded
  (Deviations; the list is rebuilt from the harness by `make_rapid_list.py`).
- Metric: mean `similarity` x 100 over the scenarios (milestone and minefield matching, no judge model; a scenario that
  raises an exception scores 0, as in the harness).
- Standard error: **clustered by base scenario** (`stderr`, 101 clusters). The 8 variants of one base scenario (no
  distraction tools, 3 and 10 distraction tools, all tools, four scrambled variants) share one task, so they are not
  independent; SE = sqrt(k / (k - 1) x sum over clusters of (sum of x - mean)^2) / n, the formula of
  `klastrowe_wazone` in `research/tools/statystyka.py`, which with 8 variants in every base equals the standard
  deviation of the 101 base-scenario means divided by sqrt(101). The harness-style SE that treats the 808 scenarios as
  independent is 1.49 and is too small; it is given only for comparison. Related base scenarios (for example `_alt`
  variants) may still be correlated, which neither SE models.
- Settings: agent Bielik 11B v3.1 through the Fabryka AI API (`https://fabryka.ai/v1`, native `tools` parameter),
  temperature 0, 1024 tokens per turn (as in the LFM3-1.7B card), one trial, at most 30 messages per scenario, 2
  scenarios in parallel; user simulator Claude Haiku 5.5 (`claude-haiku-5-5`, Anthropic's OpenAI-compatible endpoint,
  no temperature or top_p sent). Run of 2026-11-24.

## Results

| model | score | stderr (clustered by base scenario, k = 101) | stderr (808 scenarios as independent) | n | date |
|---|---|---|---|---|---|
| Bielik 11B v3.1 (API) | 45.18 | 3.72 | 1.49 | 808 | 2026-11-24 |
| Slayer 1B 1.09, update 70 000 | null | - | - | 0 | 2026-11-24 |
| LFM3-1.7B, model card (card only, not measured here) | 80.36 | not given | not given | not given | card |

**The result is 45.18, stderr 3.72 (clustered), n = 808.** The scores in the section on INSUFFICIENT_INFORMATION below
(39.16, 42.92, 28.96) are descriptive composition checks, not alternative headlines.

Slayer 1B: `score: null`, `results/slayer1b-1.09-k70000.json`. The harness sends tools through the OpenAI `tools`
parameter and returns results as `tool` messages. Slayer 1B is a base model without a chat template or tool-calling
format; the Slayer server of this repository (`common/slayer_serving/slayer_server.py`) answers HTTP 400 to `tools`,
`tool_choice` and the `tool` role, and the Fabryka AI API does not serve Slayer (its `/v1/models` lists no Slayer; a
request for it returned HTTP 400 "Input should be a published model ID", with or without tools; seen during setup,
no log is committed). No tool call can be made, so the benchmark was not run.

**LFM3-1.7B is only the card's number.** We did not run LFM3 on ToolSandbox; the 80.36 is quoted from the
[model card](https://huggingface.co/LiquidAI/LFM3-1.7B). It is not like-for-like with our Bielik row, and no test of
the two numbers is possible or made. What differs or is unknown:

- the card does not name its user simulator; the harness's own are GPT models, ours is Claude Haiku 5.5;
- the card does not say which scenarios were run: whether the 224 that need a RapidAPI key were included is unknown,
  and 224 of the 1032 are missing from our 808;
- the card gives no SE, n, number of trials or tool backend;
- the Fabryka API adds a hidden provider system prompt (#277) to Bielik's requests, and its context is 32768 tokens.

The two numbers are therefore reported side by side as they are, with no reading of the difference.

### Scores by the harness's scenario categories

A scenario has several categories, so the rows overlap and are not a partition. `k` = number of base scenarios in the
category; for the eight categories that hold one variant per base scenario (`k` = 101) the clustered and the independent
SE are equal. Descriptive, no tests between categories.

| category | score | stderr (clustered) | n | k |
|---|---|---|---|---|
| ALL_TOOLS_AVAILABLE | 40.42 | 4.23 | 101 | 101 |
| ARG_DESCRIPTION_SCRAMBLED | 40.20 | 4.20 | 101 | 101 |
| ARG_TYPE_SCRAMBLED | 47.35 | 4.25 | 101 | 101 |
| CANONICALIZATION | 23.85 | 3.67 | 288 | 36 |
| INSUFFICIENT_INFORMATION | 87.49 | 4.19 | 224 | 28 |
| MULTIPLE_TOOL_CALL | 22.32 | 3.03 | 480 | 60 |
| MULTIPLE_USER_TURN | 16.44 | 4.90 | 160 | 20 |
| NO_DISTRACTION_TOOLS | 48.08 | 4.27 | 101 | 101 |
| SINGLE_TOOL_CALL | 59.56 | 8.07 | 104 | 13 |
| SINGLE_USER_TURN | 33.68 | 4.00 | 424 | 53 |
| STATE_DEPENDENCY | 37.29 | 5.50 | 104 | 13 |
| TEN_DISTRACTION_TOOLS | 45.71 | 4.20 | 101 | 101 |
| THREE_DISTRACTION_TOOLS | 45.45 | 3.79 | 505 | 101 |
| TOOL_DESCRIPTION_SCRAMBLED | 43.79 | 4.27 | 101 | 101 |
| TOOL_NAME_SCRAMBLED | 47.03 | 4.21 | 101 | 101 |

### What the INSUFFICIENT_INFORMATION scenarios add to the score

INSUFFICIENT_INFORMATION has 224 scenarios (28 base scenarios; unrelated to the 224 excluded RapidAPI scenarios) whose
task is to not use a tool, or to ask the user.
It scores 87.49, against 28.96 ± 3.31 (n = 584, k = 73) outside the category. Of these, 80 scenarios (10 base
scenarios) keep a RapidAPI tool in their allow-list and stay in the evaluated set (Deviations); **Bielik scored exactly
1.0 on all 80**, so they carry 9.9 percent of n at the maximum. Without them the score is 39.16 ± 3.61 (n = 728, k =
91). So the headline 45.18 depends on this part of the benchmark. `rapid_api_kept_bases.txt` lists the 10 base
scenarios with the tool each minefield forbids: in 6 of them (48 scenarios) it is a RapidAPI tool itself (the
attempted call is what is scored, so the missing key cannot change the score); in 4 (32 scenarios) it is another tool
(`calculate_lat_lon_distance` or `unit_conversion`) and a RapidAPI tool is allowed, so with a key an agent could look
a place up and then go on to the forbidden tool. For those 32 the score is not shown to be independent of the key;
without them the score is 42.92 ± 3.70 (n = 776, k = 97).

How much the missing key can have moved the score in the runs as they happened: the key error appeared in 3 scored
scenarios only (none of the 48, 2 of the 32, and one outside the category; see below), so the other 805 trajectories
never reached a failing RapidAPI call. If those 3 scenarios had scored anything between 0 and 1 with a key, the mean
would move between -0.25 and +0.10 points (the two at 1.0 could fall to 0, the one at 0.18 could rise to 1). A trajectory
that avoided a RapidAPI tool because of the missing key cannot be ruled out, since the tool list is the same with or
without a key.

## Counts for the infrastructure and error cases

- **Infrastructure errors: 0 remain.** One scenario (`update_contact_relationship_with_relationship_alt`) hit HTTP 503
  after all retries in the main pass, was rerun once and scored (similarity 0.0); it carries
  `rerun_after_infra_error: true` in the per-item file and is counted in n.
- **Scenarios scored 0 by an exception: 2**, both `KeyError` raised by the harness because Bielik called a tool that
  is not in the scenario (`get_contacts` in `remove_contact_by_phone_no_search_contacts_insufficient_information_alt_10_distraction_tools`;
  `datetime_to_timestamp` in `search_reminder_with_recency_upcoming_insufficient_information_implicit_3_distraction_tools_tool_description_scrambled`).
  The harness writes no transcript when a scenario raises, so `output` is `null` for these
  two rows and the message is in `error_message`.
- **RapidAPI key error in a scored scenario: 3 scenarios.** Bielik called a RapidAPI tool in 3 scored scenarios and
  got `PermissionError: Please provide 'RAPID_API_KEY'`: two `find_temperature_f_with_location_insufficient_information_alt`
  variants (score 1.0; their minefield is `unit_conversion`) and `search_relationship_with_phone_number_10_distraction_tools`
  (score 0.18, the call was a distraction tool; its score was not recomputed with a key). Listed in
  `other_metrics.scenarios_with_rapid_api_key_error_text`.
- **Polish replies (limitation).** In the 806 scenarios with a transcript, 284 (35.2 percent) have at least one
  assistant text message with a Polish diacritic (277 with two or more in one message), and 1134 of the 3374 assistant
  text messages do, although the harness prompts and the simulator are English (no simulator message has a diacritic).
  The heuristic misses Polish without diacritics and counts quoted Polish names; the cause was not isolated (the API's
  hidden provider system prompt, #277, is one candidate); whether it changes the score through the simulator's replies
  was not measured. No score is given by language: the groups differ in task mix, so it would read as an effect.

Each line of `results/bielik-11b-v3.1.jsonl.gz` is one scenario: `task_id`, `base_scenario`, `categories`, `score`,
`milestone_similarity`, `minefield_similarity`, `turn_count`, `error_type`, `error_message`, `infrastructure_error`,
`rerun_after_infra_error`, and `output` (the conversation, with the tool calls). The scores, SEs, category and
sensitivity tables, counts and Polish-reply numbers in this README are recomputed from it by
`python summarize.py bielik-11b-v3.1 --check` and `tests/test_toolsandbox_results.py`. Not recomputable from committed
files: the cost, token and time figures and the numbers about the discarded partial run, which come from logs in the
git-ignored `out/`.

## Cost and time

The simulator calls of the final run cost 1.13 USD (3386 calls, 6828799 input and 901056 output tokens from the
`usage` fields, at 0.10 / 0.50 USD per million input / output tokens as the run script assumed; not checked against an
invoice); the log of all recorded calls adds up to 1.15 USD. The setup checks and the discarded partial run were not
logged separately, so a total for the task is an estimate of about 1.3 USD. The cap for this task was 5 USD. The main
pass took about 2.6 hours (13:19 to 15:57 local time, with 2 scenarios in parallel while tau3-bench used the same API).

## Deviations

Each is a choice or a fix of this repository; none edits the harness clone, and none changes how a trajectory is
scored (milestone and minefield matching, similarity, the 0 for an exception).

- **User simulator: Claude Haiku 5.5, not GPT-4o.** The harness's simulators are GPT models on the OpenAI API, which we
  cannot use; the card does not name its simulator. A different simulator can change both the dialogue and the score.
- **224 of 1032 scenarios are not run** because they need `RAPID_API_KEY` (no key, none will be obtained). Rule (in
  `make_rapid_list.py`, which rebuilds `rapid_api_scenarios.txt` from the pinned harness and fails on a difference): a
  base scenario whose tool allow-list contains `search_lat_lon`, `search_location_around_lat_lon`,
  `search_weather_around_lat_lon`, `search_stock` or `convert_currency` is excluded with its 8 variants, except the
  `*_insufficient_information*` scenarios (which have no milestones, only minefields), kept so that the agent's
  behaviour of not acting is measured. That exception existed before the partial run, but the first protocol text names 48 scenarios
  (equal to the 6 base scenarios whose forbidden tool is a RapidAPI tool; how it was counted is not recorded); the 80
  (10 base scenarios) come from the corrected rule and were fixed after the partial run was seen (5 of the 83 partial-run scenarios are among
  them).
  **The list was corrected after a partial run:** a first list of 72 scenarios (found by searching milestone text for
  the tool names) was used for a first full run, stopped after about 80 scenarios (its progress file, not committed,
  holds 83) and discarded; comparing the harness's "necessary tool name" counts printed in its log showed that 152 more
  scenarios need a RapidAPI tool. What was visible at that point: the scores of those 83 scenarios (mean 43.08; the 18
  of them that are in the final list averaged 10.8) and the log. The rule was then applied to all scenarios alike and
  the whole run restarted with the 224-list; the corrected list was committed before the restarted run began. The
  decision was not blind to those partial scores. The score the 72-list would have given was not measured.
- **Wrapper fixes for the Fabryka API (`ts_run.py`).** (1) Tool-call ids such as `chatcmpl-tool-<hex>` are turned into
  `chatcmpl_tool_<hex>` (hyphens to `_`, in the call and in its result): the harness builds a Python variable
  `<id>_parameters` from the id, so a hyphen is a SyntaxError on every call. (2) The `name` key of tool-result
  messages is dropped (the API answers HTTP 400 "This request field is not supported"; `tool_call_id` identifies the
  call). (3) The simulator's several system messages (its few-shot examples) are merged, in order, into one leading
  system message, because the API rejects system messages after the first and Anthropic's endpoint hoists them the
  same way; this applies to every simulator model and may change the simulator's replies, which was not measured.
  (4) HTTP 429 and 5xx, timeouts and connection errors are retried with back-off (6 attempts, waits of 10 to 120 s),
  an empty agent reply (no text, no tool call) is retried twice; the number of retries was not recorded, so a
  retried empty reply that differed from the first is not visible in the data. A scenario that still fails is an
  infrastructure error: excluded from n and score, not scored 0, rerun once (here 1 case, 0 remained).
  (5) The agent sends `temperature=0` and `max_tokens=1024` as the card states; the harness's stock agent sends
  neither. (6) `progress.jsonl` is written after each scenario, because the harness writes its summary only at the end.
- **`httpx==0.27.2`** on top of the harness pins (via `requirements.lock.txt`): `openai==1.17.0` passes `proxies=` to
  httpx, which httpx 0.28 removed.
- **The Fabryka API adds a hidden provider system prompt** (#277); its context is 32768 tokens. No scenario ended with a
  context-length error (the only exceptions are the 2 `KeyError`s).
- **Run settings not in the card:** tool backend `DEFAULT`, 30 messages per scenario (the harness's own), one trial.
- **A scenario that raises is scored 0** (2 cases), as the harness does.

## Reproduce

```bash
cd research/api-benchmarks/toolsandbox
export TS_USER_BASE_URL=https://api.anthropic.com/v1/ TS_USER_API_KEY_FILE=<file with the key> TS_USER_MODEL=claude-haiku-5-5
RUN_TAG=full TS_USAGE_LOG=$PWD/out/usage_full.jsonl bash run.sh bielik-11b-v3.1      # 808 scenarios; paid simulator calls
# scenarios that ended as InfraError (one name per line) are rerun once:
RUN_TAG=rerun bash run.sh bielik-11b-v3.1 --only $PWD/out/infra_rerun.txt
python summarize.py bielik-11b-v3.1 out/data/full out/data/rerun --usage out/usage_full.jsonl
RESULT_DATE=2026-11-24 bash run.sh slayer1b-1.09-k70000                              # writes the null result, no model call
.venv/bin/python make_rapid_list.py                    # rebuilds the excluded list from the harness and compares
python summarize.py bielik-11b-v3.1 --check            # recomputes everything in results/ from the per-item file
```

The harness writes into a timestamped directory under `out/data/<RUN_TAG>/`, so a second run does not overwrite the
first. `run.sh` pins the ToolSandbox commit (`common.sh` refuses any other checkout) and the dependencies
(`requirements.lock.txt`). `results/*` are written only by `summarize.py` and `run.sh` (the Slayer null), and
`summarize.py` writes the same bytes for the same inputs.

Files: `run.sh`, `common.sh`, `ts_run.py` (endpoint wrapper, retries, usage log), `summarize.py`,
`make_rapid_list.py`, `rapid_api_scenarios.txt` (224 excluded), `rapid_api_kept_bases.txt` (10 kept
INSUFFICIENT_INFORMATION bases), `requirements.lock.txt`, `smoke.sh` (free setup check with Bielik as agent and
simulator, not a result), `results/`. `out/` (harness clone, transcripts, logs) is git-ignored.
