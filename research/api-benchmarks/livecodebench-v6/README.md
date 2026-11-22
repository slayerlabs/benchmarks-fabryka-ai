# LiveCodeBench v6

Whether a model writes a Python program that passes the hidden tests of a competitive-programming problem
(LeetCode, AtCoder, Codeforces). The pre-registered question, hypotheses and verdict rules are in
[PROTOCOL.md](PROTOCOL.md) (with Amendments 1 to 3); this file says how the run is done. Refs #295.

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
  setting, temperature 0.6, top_p 0.95, seed 20261122 on every request, output limited only by the context
  (`max_tokens` = context minus prompt tokens; on the API also minus a margin, see Deviations). On our vLLM also
  frequency and presence penalty 0, as `oai_runner.py` sends them. The code is LiveCodeBench's extraction (last
  ```` ``` ```` block) of the text after the last `</think>`. Evaluator: 6 s per test case, 12 processes (its
  defaults in `lcb_runner/runner/parser.py`)
- Extra services: the Fabryka AI API for Bielik. LFM3-1.7B needs one GPU (written for an H100 80 GB)

## Results

| model | how it runs | score | stderr | n | date |
|---|---|---|---|---|---|
| LFM3-1.7B (`lfm3-1.7b`) | vLLM 0.34.0, bf16, context 262144 | | | | |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | Fabryka AI API, context 32768, with the API's provider system prompt | | | | |
| Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`) | not run, see Deviations | | | | |

No model has been run yet. Qwen3.5-4B and Qwen3.5-9B were dropped before any of their output (PROTOCOL.md,
Amendment 1).

## Deviations

- **The dataset is read from its files, not through its loading script.** LiveCodeBench loads the data with
  `load_dataset(..., trust_remote_code=True)`, which runs the dataset's `code_generation_lite.py` and takes no
  revision. `lcb.py` downloads the files that script lists for `release_v6` (`test.jsonl` to `test6.jsonl`) at the
  pinned revision and reads their json lines in the same order, which is all the script's generator does; the
  v6-only set is the `release_v6` problems whose `question_id` is not in the `release_v5` files. The rows go into
  LiveCodeBench's own `CodeGenerationProblem`, sorted by `question_id` as its runner sorts them.
- **Generation goes through an OpenAI-compatible chat endpoint, scoring through LiveCodeBench's evaluator.**
  LiveCodeBench's own runners call either `vllm.LLM` with a hand-written prompt string per model family, or an API
  client. We need the model's own chat template and its default system prompt (PROTOCOL.md), so `lcb.py` sends the
  `OpenAIChat` messages to `vllm serve` (LFM3-1.7B) or the Fabryka API (Bielik) and passes the answers to
  `codegen_metrics`, as `custom_evaluator.py` does with a file of outputs.
- **Bielik runs on the Fabryka AI API, with its hidden provider system prompt** (PROTOCOL.md, Amendment 1; #277).
  The API applies Bielik's chat template itself and rejects `chat_template_kwargs` and every reasoning switch, so
  the template defaults hold: its provider system prompt (model identity, knowledge cutoff, the live date) comes
  first, and LiveCodeBench's system message is appended to that system block under "Additional Instructions". The
  default `reasoning_effort` is `none`, so the generation prompt ends in an empty `<think></think>` and Bielik
  answers without thinking. Both are what the pinned template renders locally; the API's own rendering is not
  visible. The request carries only the fields the API accepted in the IFEval run (`model`, `messages` as plain
  role and content, `temperature`, `top_p`, `max_tokens`, `seed`): no `n`, penalties or `stop`, so any server-side
  sampling defaults apply and are not visible to us.
- **Bielik's output limit is counted locally, with a margin.** The API has no `/tokenize`. `lcb.py` counts each
  prompt with Bielik's own tokenizer and chat template at the pinned revision
  (`speakleash/Bielik-11B-v3.1-Instruct` @ `d6e755d356ad418d0f0e30b8c428db267415ddb9`, gated) at the template
  defaults, provider prompt included, and sets `max_tokens` = 32768 − that count − 64. The 64 tokens cover what the
  API's rendering may add: the live date and time words in the provider prompt, and a one-sentence message counted
  locally at 1058 tokens against about 1065 billed by the API (ifeval README). The local counts over the 1055
  prompts: mean 1720, median 1682, max 3086, so every answer may use at least 29618 tokens. Each answer records the
  API's own `usage.prompt_tokens`; the result file reports the API count minus ours (`api_prompt_minus_local`) and
  the largest prompt plus output the API billed, to check the margin. The count needs `transformers` 4.57.6 (as
  for Bielik in `ifeval/vllm.sh`; LiveCodeBench's lock pins 4.51.3, which cannot load this tokenizer) with
  `sentencepiece`, `protobuf` and `jinja2` in the LiveCodeBench venv; the evaluator does not import them.
- **Bielik's answers are scored on the machine that runs the API requests** (a Mac or a Linux CPU box), LFM3-1.7B's
  on the GPU box. LiveCodeBench's per-test time limit (6 s) depends on the CPU, so a program near the limit can pass
  on one machine and time out on the other.
- **One sample per problem.** LiveCodeBench's runner defaults to 10 samples per problem (`--n 10`); PROTOCOL.md
  fixes one sample with a fixed seed. The stderr is the binomial one over problems.
- **vLLM applies LFM3-1.7B's `generation_config.json` as default sampling.** Parameters the request does not set
  come from it: `repetition_penalty` 1.1 and `top_k` 50. This is vLLM's default, as in the IFEval LFM3-1.7B run;
  run.sh prints the line in which vLLM reports it. PROTOCOL.md did not name these two settings and the LFM3-1.7B
  result file did not record them; the method verification found this after the result existed (PROTOCOL.md,
  Amendment 3). Their effect on the score is not estimated. Each result file now records the sampling in effect:
  `settings.request_sampling` (sent) and `settings.server_defaults` (filled by the server: on vLLM read by lcb.py
  from `generation_config.json` at the pinned revision, on the Fabryka API `unknown (Fabryka API)`).
- **The LFM3-1.7B result's provenance was recorded by hand, after the run.** It was produced before lcb.py
  recorded provenance, so `results/lfm3-1.7b.json` got its `provenance`, `raw_outputs` and sampling fields added
  by hand and nothing was regenerated: the code commit is fc13b0bd, inferred (its `graded.jsonl` lacks the fields
  later code adds; the request and scoring path did not change after it), with the sha256 of the runner files at
  that commit; the hardware is a vast.ai H100 80 GB instance, written by hand (no `nvidia-smi` output was kept),
  which also scored the answers on its CPU; platform, CPU model and `dirty` were not captured. The
  `manifest.json` files in `out/lfm3-1.7b/` and `results/` hold the hashes those files had when they were written
  after the fact, not hashes recorded by the steps that wrote them.
- **The `output` of a `.jsonl.gz` line is the extracted code, not the whole model output.** METHODOLOGY.md asks
  for the model output per task; the raw output with its thinking is about 16 MB for LFM3-1.7B, over the repo's
  10 MB limit, so it stays in `out/<model-id>/` (not committed). Its sha256 is in the result file
  (`raw_outputs.sha256`), so a copy kept elsewhere can be matched to the result.
- **An answer without `</think>` is scored whole.** An answer cut at the context limit inside its thinking has no
  `</think>`, so the last code block of the thinking is extracted. Such answers have `finished: false`, so they never
  count at a budget, and their number is `unfinished` in the result file.
- **Errors are not wrong answers.** A failed request (server error, 429, broken connection, timeout) pauses all
  requests, 10 s doubling up to 5 min while failures continue (as `ifeval/lm_eval_fabryka.py`), and is tried again:
  up to 30 attempts on the API, 3 on our vLLM. A request that still fails, or that the server rejects (another 4xx),
  is `status: error`; a prompt longer than the context is `status: unsupported` and never sent. Both are left out
  of n and counted. A rerun of run.sh tries the errors again. A rejected key (401, 403), a failed TLS certificate
  check or an answer with reasoning in a separate field stops the whole run instead, since every request would fail
  the same way. LiveCodeBench's own grades are kept as they are, including its runner errors (`error_code` -5, which
  it grades as a fail and which include its global timeout); their number is `evaluator_runner_errors`.
- **Slayer 1B 1.09 at update 70 000 is not run** (`slayer1b-1.09-k70000`, PROTOCOL.md, Amendment 2). PROTOCOL.md
  sets LiveCodeBench's base-model prompt (`GenericBase`: one solved example, then the problem), greedy, output up to
  4096 minus the prompt. With the Slayer 1B 1.08 tokenizer these prompts are 1373 tokens on average (median 1484,
  max 2709), which leaves 2.87M output tokens for the 1055 problems (not recounted with the 1.09 checkpoint).
  `research/common/slayer_lm.py` decodes about 29 tokens per second whatever the batch (IFEval README,
  "Deviations": 1280 tokens in about 45 s), so the set takes about 27 h if the outputs run to the limit, as Slayer's
  IFEval outputs mostly do. Under about 3 h it would need fewer than about 300 output tokens per problem on average.
  The batched decoder in `ifeval/lm_eval_slayer.py` belongs to that benchmark; using it here would first need it
  moved to `research/common/`. Until then the row stays empty.
- **Contamination cannot be ruled out.** LiveCodeBench stopped adding problems in 2025, so `release_v6` is older
  than the training data of LFM3-1.7B and Bielik 11B v3.1 (whose template states a knowledge cutoff of 2026-03)
  (PROTOCOL.md, "Limits stated in advance"). The results are not contamination-free.

## Reproduce

LFM3-1.7B, on a Linux machine with an NVIDIA GPU:

```bash
bash run.sh lfm3-1.7b
```

Bielik 11B v3.1, on a Mac or a Linux machine without a GPU, after `hf auth login` with an account that accepted the
licence of `speakleash/Bielik-11B-v3.1-Instruct`:

```bash
export FABRYKA_API_KEY=...
bash run.sh bielik-11b-v3.1 --limit 5   # smoke test: prints the seconds per answer
bash run.sh bielik-11b-v3.1
```

run.sh clones LiveCodeBench into `.cache/` and builds `.venv-lcb` with LiveCodeBench's dependencies (and, for the
GPU run, `.venv-vllm` with vLLM 0.34.0, which serves the model during generation). It sends the requests
(`CONCURRENCY`: default 64 on vLLM, 2 on the API), scores and writes `results/<model-id>.json` and `.jsonl.gz`. The
raw outputs stay in `out/<model-id>/` (not committed); an interrupted run picks up where it stopped. The
`.jsonl.gz` keeps per problem the grade, the token counts, the `finished` flag and the extracted code, not the
thinking.

Provenance: `lcb.py generate` writes to `out/<model-id>/run.json` our code commit (`git rev-parse HEAD`, and
`dirty` when a tracked file of this directory differs from it), the sha256 of the runner files, the machine (GPU
from `nvidia-smi`, CPU, platform) and the sampling in effect; `lcb.py score` adds the same for the scoring machine,
and summarize.py copies both into the result file under `provenance`. Each step records the sha256 of the file it
writes in `manifest.json` next to it (`out/<model-id>/` for generations and grades, `results/` for the result
files), and lcb.py score, summarize.py and compare.py stop when an input is missing from the manifest or no longer
matches it.

`--limit 5` runs the first 5 problems (by `question_id`) and writes its summary to
`out/<model-id>/<model-id>-limit5.*`, not to `results/`. The `date` in a result file is the UTC day of the first
request.

`python3 ../../tests/test_livecodebench_v6.py` checks offline the summary, the scored text, compare.py (with the
control threshold), the API and vLLM request bodies (against a fake server on 127.0.0.1), the evaluator settings,
the alignment of grades with problems, the problem set's order and v6-only flag, the recorded sampling and
provenance, and that each step refuses a changed input.

## Hypotheses

`python3 compare.py` (from this directory) reads `results/<model-id>.jsonl.gz` and tests L1-L3 of PROTOCOL.md
(Amendment 1) on LFM3-1.7B against Bielik 11B v3.1, paired by problem: the control first (LFM3-1.7B's pass@1 within
2 SE of its card's 73.46), then a Markdown table with each difference (LFM3-1.7B minus Bielik 11B v3.1, percentage
points), its paired SE, z, Holm-adjusted p (m = 3), the verdict and n, and the same paired numbers on the v6-only
problems as descriptive rows. A problem that errored or did not fit the context for either model is left out of
both sides and counted. A hypothesis whose model has not been run is `not run`. The full output goes to
`results/hypotheses.json`; the `deviation:` lines it prints say where the protocol's wording needed a reading (L2's
single p, what counts as parameters in the cost per answer). The parameter counts are pinned in compare.py with
their source.
