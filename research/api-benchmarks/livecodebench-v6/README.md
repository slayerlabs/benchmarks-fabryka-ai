# LiveCodeBench v6

Whether a model writes a Python program that passes the hidden tests of a competitive-programming problem
(LeetCode, AtCoder, Codeforces). The pre-registered question, hypotheses and verdict rules are in
[PROTOCOL.md](PROTOCOL.md); this file says how the run is done. Refs #295.

- Paper: [Jain et al. 2024, LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for
  Code](https://arxiv.org/abs/2403.07974)
- Harness and scorer: [LiveCodeBench/LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) @
  `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`: its prompt builder (`lcb_runner/prompts/code_generation.py`), code
  extraction (`lcb_runner/utils/extraction_utils.py`) and evaluator (`codegen_metrics` in
  `lcb_runner/evaluation/compute_code_generation_metrics.py`, the function `custom_evaluator.py` calls), with its
  dependencies at the versions of its `uv.lock`
- Data: [livecodebench/code_generation_lite](https://huggingface.co/datasets/livecodebench/code_generation_lite) @
  `0fe84c3912ea0c4d4a78037083943e8f0c4dd505`, `release_v6`: 1055 problems (easy 322, medium 383, hard 350;
  AtCoder 602, LeetCode 444, Codeforces 9; contests 2023-05-07 to 2025-04-06). Secondary set, the problems not in
  `release_v5`: 175 (easy 43, medium 52, hard 80; AtCoder 112, LeetCode 63; contests 2025-01-04 to 2025-04-06)
- Metric: pass@1 in percent (one sample per problem; a problem passes when the extracted program passes all its
  public and hidden tests), stderr `sqrt(p(1-p)/n)`. `other_metrics` in each result file: pass@1 on the v6-only
  problems, pass@1 and n per difficulty, output tokens per answer (mean, median, max), pass@1 at budgets of 4096 and
  16384 output tokens (an answer counts only if it passed, finished, and used at most that many tokens), and the
  counts of unfinished answers, request errors, prompts over the context and evaluator runner errors
- Settings: LiveCodeBench's `OpenAIChat` prompt (its system message and generic question template, as its
  `oai_runner.py` sends to chat models), the model's chat template with its default system prompt and reasoning
  setting, temperature 0.6, top_p 0.95, frequency and presence penalty 0 (as `oai_runner.py` sends them), seed
  20261122 on every request, `max_tokens` = context minus prompt tokens. The code is LiveCodeBench's extraction
  (last ```` ``` ```` block) of the text after the last `</think>`. Evaluator: 6 s per test case, 12 processes
  (its defaults in `lcb_runner/runner/parser.py`)
- Extra services: none. Each model needs one GPU (written for an H100 80 GB)

## Results

| model | how it runs | score | stderr | n | date |
|---|---|---|---|---|---|
| LFM3-1.7B (`lfm3-1.7b`) | vLLM 0.34.0, bf16, context 262144 | | | | |
| Qwen3.5-4B (`qwen3.5-4b`) | vLLM 0.34.0, bf16, context 262144 | | | | |
| Qwen3.5-9B (`qwen3.5-9b`) | vLLM 0.34.0, bf16, context 262144 | | | | |
| Bielik 11B v3.1 (`bielik-11b-v3.1-vllm`) | vLLM 0.34.0, bf16, context 32768 | | | | |
| Slayer 1B 1.08 (`slayer1b-1.08`) | not run, see Deviations | | | | |

No model has been run yet.

## Deviations

- **The dataset is read from its files, not through its loading script.** LiveCodeBench loads the data with
  `load_dataset(..., trust_remote_code=True)`, which runs the dataset's `code_generation_lite.py` and takes no
  revision. `lcb.py` downloads the files that script lists for `release_v6` (`test.jsonl` to `test6.jsonl`) at the
  pinned revision and reads their json lines in the same order, which is all the script's generator does; the
  v6-only set is the `release_v6` problems whose `question_id` is not in the `release_v5` files. The rows go into
  LiveCodeBench's own `CodeGenerationProblem`, sorted by `question_id` as its runner sorts them.
- **Generation goes through vLLM's OpenAI-compatible server, scoring through LiveCodeBench's evaluator.**
  LiveCodeBench's own runners call either `vllm.LLM` with a hand-written prompt string per model family, or an API
  client. We need the model's own chat template and its default system prompt (PROTOCOL.md), so `lcb.py` sends the
  `OpenAIChat` messages to `vllm serve` and passes the answers to `codegen_metrics`, as `custom_evaluator.py` does
  with a file of outputs.
- **Bielik runs on vLLM, not the Fabryka API.** The API adds a hidden system prompt and cannot be configured (#277).
  Its template's default provider system prompt is kept, with the date in it pinned to 2026-11-22 (the day of
  PROTOCOL.md) so a rerun sends the same prompt. LiveCodeBench's system message is sent as the `system` role; how
  Bielik's (gated) template combines it with the provider prompt is not checked here.
- **One sample per problem.** LiveCodeBench's runner defaults to 10 samples per problem (`--n 10`); PROTOCOL.md fixes one sample
  with a fixed seed. The stderr is the binomial one over problems.
- **vLLM applies each model's `generation_config.json` as default sampling.** Parameters the request does not set
  come from it: for LFM3-1.7B `repetition_penalty` 1.1 and `top_k` 50 (Qwen3.5 has no such file). This is vLLM's
  default, as in the IFEval LFM3-1.7B run; run.sh prints the line in which vLLM reports it.
- **An answer without `</think>` is scored whole.** An answer cut at the context limit inside its thinking has no
  `</think>`, so the last code block of the thinking is extracted. Such answers have `finished: false`, so they never
  count at a budget, and their number is `unfinished` in the result file.
- **Errors are not wrong answers.** A request that still fails after 3 attempts (30 s apart) is `status: error`; a
  prompt longer than the context is `status: unsupported`. Both are left out of n and counted. LiveCodeBench's own
  grades are kept as they are, including its runner errors (`error_code` -5, which it grades as a fail and which
  include its global timeout); their number is `evaluator_runner_errors`.
- **Slayer 1B 1.08 is not run.** PROTOCOL.md sets LiveCodeBench's base-model prompt (`GenericBase`: one solved
  example, then the problem), greedy, output up to 4096 minus the prompt. With Slayer's tokenizer these prompts are
  1373 tokens on average (median 1484, max 2709), which leaves 2.87M output tokens for the 1055 problems.
  `research/common/slayer_lm.py` decodes about 29 tokens per second whatever the batch (IFEval README,
  "Deviations": 1280 tokens in about 45 s), so the set takes about 27 h if the outputs run to the limit, as Slayer's
  IFEval outputs mostly do. Under about 3 h it would need fewer than about 300 output tokens per problem on average.
  The batched decoder in `ifeval/lm_eval_slayer.py` belongs to that benchmark; using it here would first need it
  moved to `research/common/`. Until then the row stays empty.
- **Contamination cannot be ruled out.** LiveCodeBench stopped adding problems in 2025, so `release_v6` is older
  than the training data of LFM3-1.7B and Qwen3.5 (PROTOCOL.md, "Limits stated in advance"). The results are not
  contamination-free.

## Reproduce

On a Linux machine with an NVIDIA GPU:

```bash
bash run.sh lfm3-1.7b
bash run.sh qwen3.5-4b
bash run.sh qwen3.5-9b
HF_TOKEN=hf_... bash run.sh bielik-11b-v3.1-vllm
```

run.sh clones LiveCodeBench into `.cache/`, builds two venvs (`.venv-vllm` with vLLM 0.34.0, `.venv-lcb` with
LiveCodeBench's dependencies), serves the model, sends the requests (`CONCURRENCY`, default 64), scores and writes
`results/<model-id>.json` and `.jsonl.gz`. The raw outputs, thinking included, stay in `out/<model-id>/`
(not committed); an interrupted run picks up where it stopped. The `.jsonl.gz` keeps per problem the grade, the
token counts, the `finished` flag and the extracted code, not the thinking.

`--limit 5` runs the first 5 problems (by `question_id`) and writes its summary to
`out/<model-id>/<model-id>-limit5.*`, not to `results/`. The `date` in a result file is the UTC day of the first
request.

`python3 ../../tests/test_livecodebench_v6.py` checks the summary and the scored text offline.
