# BFCL V4

Whether a model calls functions correctly: picks the right function (or none), fills its arguments, calls several in
parallel or in sequence, and keeps state over multi-turn and memory tasks. Calls are checked against ground truth
by the harness (AST match, executed state or memory answers), without a judge model.

- Leaderboard and method: [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)
- Harness: [ShishirPatil/gorilla](https://github.com/ShishirPatil/gorilla) @ `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`,
  `berkeley-function-call-leaderboard` (`bfcl generate`, `bfcl evaluate`)
- Data: bundled with the harness, `bfcl_eval/data` @ the same commit. 20 named test categories, 4906 scored tasks
  (all of V4 except `web_search`, see Deviations)
- Metric: Overall Acc of the harness (`score/data_overall.csv`), reported as `score: null` here because it needs
  `web_search`; the five group scores the harness computes are in `other_metrics` (see Results)
- Settings: function-calling mode (`bielik-FC`: native tool calls through the vLLM tool parser), BFCL's default
  temperature 0.001, no output limit other than the 32768-token context, 1 trial (LFM3-1.7B card: "greedy
  decoding, up to 32,768 output tokens") <!-- liczba-spoza-wynikow: dosłowny cytat karty LFM3, separator tysięcy -->
- Extra services: none (multi-turn and memory tasks run locally in the harness)

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Bielik 11B v3.1, own vLLM (`bielik-11b-v3.1-vllm`) | null | | 4906 | 2026-11-19 |
| Slayer 1B, step 60000 (`slayer1b-60000`) | null | | 0 | 2026-11-19 |
| LFM3-1.7B, model card | 71.39 | | | |

Group scores of the harness for Bielik (percent, stderr in brackets):

| non-live AST | live AST | irrelevance | relevance | multi-turn | memory | Overall, lower bound |
|---|---|---|---|---|---|---|
| 85.50 (1.18) | 72.91 (1.21) | 75.68 (1.57) | 93.75 (6.05) | 5.62 (0.81) | 16.56 (1.70) | 28.41 (0.48) |

**Overall, lower bound** is the harness's own Overall Acc with `web_search` counted as 0, which is what its formula
does with a missing category. It is not comparable with 71.39 and is not the score.

Per-category pass rates are in `categories` of `results/bielik-11b-v3.1-vllm.json`, and each line of the
`.jsonl.gz` holds one task: `task_id`, `category`, `score` (0/1), the harness's `error_type` for failed tasks, and
the raw `output`.

## Deviations

- **`web_search` is not run, so there is no Overall score.** Its two categories (`web_search_base`,
  `web_search_no_snippet`, 100 tasks each) call a live search API that needs a key (SerpAPI). BFCL's Overall Acc is
  10% non-live + 10% live + 10% irrelevance + 30% multi-turn + 40% agentic, with agentic = mean(web search,
  memory) (`bfcl_eval/eval_checker/eval_runner_helper.py`), and a missing category counts as 0. Without web search
  Overall would lose half of the agentic weight, so we leave `score` null and report the group scores instead.
  If these categories are run later, the search API key must be a team key, not a personal account.
- **Self-hosted vLLM, not the fabryka.ai API.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) is served by vLLM 0.34.0 on a rented GPU (NVIDIA RTX 6000
  Ada Generation), with the tool-call and reasoning parsers from
  [speakleash/bielik-tools](https://github.com/speakleash/bielik-tools) @ `2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09`
  (`vllm.sh`). It runs the chat template's defaults, including the provider system prompt, with the date pinned to
  2026-11-18. This is the setup of the `-vllm` rows of the IFEval benchmark (#313), not the API row: on
  IFEval the two differed by about 5 points.
- **The model is added to the harness's model table.** BFCL has no entry for Bielik. `run.sh` appends one entry
  (`model_config_bielik.py`): `bielik-FC`, OpenAI-compatible handler, function-calling mode, the harness's
  standard option for models whose function names cannot hold dots. Nothing else in the harness changes.
- **Temperature 0.01 instead of BFCL's 0.001.** BFCL sends 0.001 (its near-greedy default, also on its own
  leaderboard); vLLM 0.34 raises any temperature below 0.01 to 0.01 and logs it.
- **Requests are batched.** The harness sends 16 requests at a time and vLLM batches them. Greedy outputs under
  batching can differ slightly from one-at-a-time decoding. The same vLLM server also served other benchmarks
  during this run, so the batch composition varied.
- **One extra package.** `qwen-agent`, a harness dependency, imports `soundfile` without declaring it; `run.sh`
  installs `soundfile==0.13.1`.
- **Standard errors.** For the group scores: sqrt(sum w^2 p (1 - p) / n) over the categories, with the group's
  weights from the harness. This treats tasks as independent, which multi-turn tasks built on the same scenario
  are not fully, so the multi-turn error is somewhat too small.
- **Memory prerequisites.** The memory categories first generate 37 prerequisite conversations per backend (111
  in total), which fill the memory; the harness does not score them, and neither does `summarize.py`.
- **17 multi-turn tasks hit the context limit.** In `multi_turn_long_context`, 17 of 200 conversations grew past
  the 32768-token context and vLLM rejected the next request (HTTP 400, "maximum context length"). The harness
  scores them as failed, and so do we, in the full N; they are listed in `context_window_exceeded` of
  `results/bielik-11b-v3.1-vllm.json`. No other request failed.
- **Slayer cannot run the benchmark; the Slayer path of `run.sh` was not run.** Slayer 1B is a base model without a
  chat template or tool-calling format. Expected outcome: the Slayer server rejects requests with tools (HTTP 400),
  as observed in AutomationBench (PR #326), so no syntactically valid call is possible.
  `results/slayer1b-60000.json` has `score: null` with that reason.

## Reproduce

```bash
HF_TOKEN=hf_... bash vllm.sh                # one GPU with at least 48 GB; serves on 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # in another shell
bash run.sh slayer1b-60000                  # writes the null result
```

`--limit 5` runs the first 5 tasks of each category (with the memory prerequisites) and writes to `out/limit/`.
`BASE_URL` points `run.sh` at another endpoint that serves the model as `bielik`. `summarize.py` stops if any task
has no model answer for any reason other than the context limit (`Error during inference`, e.g. a dropped
connection), because the harness would score it as a wrong call: rerun those IDs with
`bfcl generate --run-ids --allow-overwrite` first.
