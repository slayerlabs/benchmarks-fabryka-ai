# LiveCodeBench Pro 25Q2: measurement protocol

Written and committed before the first model output. Nothing below changes after a result is seen; anything
added later is an amendment with its time and what had been seen by then, or is marked exploratory in the README.

Refs #296. Part of the "Coding" group of the LFM3-1.7B card (LiveCodeBench v6 #295, LiveCodeBench Pro 25Q2 #296,
SciCode #297), measured together for one comparative paper.

## Question

On the LFM3-1.7B card's coding benchmarks, where does Bielik 11B v3.1, as served by the Fabryka AI API, stand
against the six models on the card, and how much of LFM3-1.7B's lead over it comes from LFM3-1.7B thinking before
it answers? LiveCodeBench v6 (#295) is the pilot that raised the question (LFM3-1.7B 72.23 vs Bielik 16.68, with
LFM3-1.7B thinking and Bielik not); its numbers are not used for any verdict here.

## Sources

- Paper: Zheng et al. 2025, LiveCodeBench Pro: How Do Olympiad Medalists Judge LLMs in Competitive Programming?,
  [arXiv 2506.11928](https://arxiv.org/abs/2506.11928).
- Harness: [GavinZhengOI/LiveCodeBench-Pro](https://github.com/GavinZhengOI/LiveCodeBench-Pro) @
  `d614eef4f95b3654bf0758c64e1194b2575850b8` (last code change `31ad6e44`), with its judge submodule
  [LightCPVerifier](https://github.com/YanagiOrigami/LightCPVerifier) @ `021d121c882e70856b66113142495e31b9fe1d80`:
  prompt `api_interface.LLMInterface().prompt`, code extraction `util.extract_longest_cpp_code`, judge
  `judge.LightCPVerifierJudge`, aggregation as `benchmark.print_stats`.
- Problems: [QAQAQAQAQ/LiveCodeBench-Pro](https://huggingface.co/datasets/QAQAQAQAQ/LiveCodeBench-Pro) @
  `adebffce047dddb7768a86bace6aea4f7425e3bc`, split `quater_2025_4_6` (= 25Q2, 167 problems, April–June 2025).
- Tests: [QAQAQAQAQ/LiveCodeBench-Pro-Testcase](https://huggingface.co/datasets/QAQAQAQAQ/LiveCodeBench-Pro-Testcase)
  @ `5257736c0a4e30ba0949d41c56a257c323d9c600`, one zip per problem.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) card, "Benchmarks" and "Evaluation
  details": LFM3-1.7B 31.74, LFM2.5-2.6B 19.16, MiniCPM5-2B 29.34, Gemma 4 E4B 29.94, Qwen3.5-4B 24.25,
  Qwen3.5-9B 34.43. Every value is k/167 or k/334, so the card scores accepted problems over all 167.

## Models

| model id | what | serving |
|---|---|---|
| `lfm3-1.7b` | `LiquidAI/LFM3-1.7B` @ `1da06bec6a819da10b54c67e5c90972b46d81871`, thinking on (template default) | vLLM 0.34.0, bf16, context 262144 |
| `lfm3-1.7b-nothink` | the same weights, `chat_template_kwargs: {"enable_thinking": false}` | the same server |
| `bielik-11b-v3.1` | Bielik 11B v3.1 through the Fabryka AI API (`https://fabryka.ai/v1`), with the API's hidden provider system prompt and no reasoning switch | API, context 32768 |
| `slayer1b-1.09-k70000` | `SlayerLab/Slayer1B-1.09-checkpoints` @ `adfaf3fd5402bc7f3adbfe077798f20262979433`, file `wagi_70000.pt`, 1.08 template `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c` | local, `research/common/slayer_lm.py`, bf16, greedy, context 4096 |

Slayer 1B is a base model with a 4096-token context and does not follow chat instructions; on 30 Python tasks in
`research/slayer-1b/rozmowy-1.08` it wrote no function that passed its tests. Olympiad problems in C++ are below
its floor; it was run after the Amendment 2 cost decision, the measured result is 0.00 and confirms that decision (see Amendment 3).

## Settings

- Problem set: all 167 problems of `quater_2025_4_6`, sorted by `problem_id`. One sample per problem (pass@1).
- Prompt: the harness's own string, `LLMInterface().prompt + problem_statement`, imported from the pinned checkout,
  sent as the only user message. No system message of ours: LFM3-1.7B gets its chat template's default system
  prompt; Bielik gets whatever the API adds.
- LFM3-1.7B sampling, sent in every request: temperature 0.6, top_p 0.95, `top_k` 0 (no limit),
  `repetition_penalty` 1.0, frequency and presence penalty 0, seed 20261122. These are the card's settings; they are
  sent explicitly because vLLM 0.34.0 otherwise fills `repetition_penalty` 1.1 and `top_k` 50 from the model's
  `generation_config.json` (livecodebench-v6, Amendments 3–4). `max_tokens` = 262144 minus the prompt tokens
  counted by the server's `/tokenize`.
- Bielik: temperature 0.6, top_p 0.95, seed 20261122 (whatever the API honours is recorded). `max_tokens` = 32768
  minus the prompt counted locally with Bielik's tokenizer and chat template (with the provider prompt) minus a
  margin of 64, as in livecodebench-v6 at `7d931ba2`. At most 2 requests at once, retries behind a shared pause,
  every retry and error logged to `api-events.jsonl`. <!-- ocena-bez-se: pre-registered rule, not a result -->
- Code: `extract_longest_cpp_code` on the text after the last `</think>`. With thinking on, an answer without
  `</think>` or stopped by the length limit is unfinished: it counts as a fail and the count is reported.
- Judge: LightCPVerifier at the pinned commit, its image built once and its digest recorded (the Dockerfile pulls
  go-judge "latest"). All three models are judged on the same machine with the same worker count, after all
  generation has finished. The machine (CPU model, cores, worker count) is recorded.
- Infrastructure failures (a request that fails in our code or the API after all retries, a judge `error` that is
  not a compile error) are retried once; if they persist they are recorded as errors, not as wrong answers.

## Metrics

- Headline: accepted / 167 × 100, a problem whose test zip is missing or whose judging errors persist counting as
  not accepted (the card's denominator). Secondary: the same with those problems left out, with their count.
- stderr `sqrt(p(1-p)/n)`.
- Per difficulty (easy, medium, hard from the dataset): accepted / n.
- Judge verdicts (accepted, wrong answer, time limit, memory limit, runtime error, compile error, no code
  extracted), output tokens per answer (mean, median, max), unfinished answers.
- For `lfm3-1.7b-nothink`: the share of answers that still contain `<think>` (the card says the switch is
  inconsistent on reasoning-heavy tasks).

## Control (before any claim)

**K1.** `lfm3-1.7b` lands within 2 SE of its card value 31.74 (SE from our run). If it does not, the setup is the
suspect: no hypothesis below is read until the gap is explained in an amendment. <!-- ocena-bez-se: pre-registered rule, not a result -->

## Hypotheses

Verdicts from z: |z| ≥ 3 clear, 2–3 likely, < 2 noise (undetermined). One-sided p from z, Holm over the four
hypotheses of the Coding group (K2 and K3 here and in SciCode #297); the verdict uses the Holm-adjusted p with the
thresholds of z = 2 and z = 3.

- **K2.** Bielik 11B v3.1 (API) scores below the weakest model on the card, 19.16.
  z = (p_Bielik − 0.1916) / SE, SE = max(sqrt(p(1−p)/n), sqrt(0.1916 · 0.8084 / n)), n = 167.
  Supported when z ≤ −2; refuted when z ≥ 2; otherwise undetermined.
- **K3.** Turning thinking off takes away at least half of LFM3-1.7B's lead over Bielik:
  D = (off − B) − ½ (on − B) < 0, with on = `lfm3-1.7b`, off = `lfm3-1.7b-nothink`, B = Bielik. Paired by
  problem: d_i = off_i − ½ on_i − ½ B_i, D = mean(d), SE = sd(d)/sqrt(n). Supported when z ≤ −2; refuted when
  z ≥ 2; otherwise undetermined. Read only if the lead itself is clear (on − B > 0 with paired z ≥ 3); otherwise
  K3 is reported as "precondition not met".

## Limits stated in advance

- 25Q2 problems and their editorials have been public since mid-2025, before LFM3-1.7B, Qwen3.5 and Bielik v3.1
  were trained. Contamination cannot be ruled out; no contamination-free claim is made.
- n = 167 gives an SE of about 3.6 points at p ≈ 0.3, so the control window is about ±7 points and K3 has low power.
- Time-limit verdicts depend on the CPU; the card's judging machine is unknown.
- The card's k/334 values suggest it averaged two samples for some models; we take one.
- Bielik through the API differs from Bielik on vLLM (provider prompt, unknown serving); the row describes the API.

## Amendment 1 (2026-11-22, after the results)

Written after all three runs had been judged and their results committed (`b96ad6ba`: K1 passed, K2 supported,
K3 refuted), and after the first verification of those results. Nothing above changes: no hypothesis, metric,
threshold or control is altered, and no official verdict is re-judged.

1. **Correction to "Settings".** LFM3-1.7B's chat template at `1da06bec` has no default system prompt (its system
   block is rendered only when a request sends one), so LFM3-1.7B's prompts had no system block at all; "gets its
   chat template's default system prompt" reads "gets none".
2. **What the K3 switch does.** With `enable_thinking: false` the template ends the prompt with an empty
   `<think></think>`; LFM3-1.7B then still reasons in most answers and closes that reasoning with its own
   `</think>` (counts in README, Results). K3 is reported as written, under the pre-registered switch. Whether the
   switch removes thinking was not checked before the run; how much of LFM3-1.7B's advantage over Bielik the
   thinking itself buys is therefore undetermined by K3.
3. **Analyses added after the results, all descriptive; no verdict reads them:** K3 with its SE clustered by
   contest, a sign test over contests and K3 per difficulty (compare.py); accepted answers within output budgets
   and compile errors by cause (explore.py); answers closing `</think>` and the causes of answers without code
   (raw_outputs.py); the effect of extracting from the whole answer, as the harness does, and Bielik's compile
   errors with a `bits/stdc++.h` prefix, both re-judged with 4 workers on the scoring VM while it was shared with
   another job (rejudge.py); exact 95% intervals where no problem of a group was accepted (readme.py).
4. **Provenance added to the results:** the test-zip manifest each run was judged on (`tests.json`: revision and
   sha256 of every zip), written into the result files by re-running `summarize.py` on the same `graded.jsonl`.

## Amendment 2 (2026-11-24, after review)

Written after review of the results; no hypothesis, metric, threshold or control changes, and nothing is re-run.

1. **Where Holm over the Coding group is computed.** The Holm correction of "Hypotheses" (m = 4: K2 and K3 here
   and in SciCode #297) is not computed in this benchmark. A copy here would have to pin the other benchmark's
   `hypotheses.json` while both are still on branches. It is computed once, after both benchmarks are merged, from
   their two `hypotheses.json` files on main (for example `research/api-benchmarks/coding-group/holm.json`), with
   the thresholds stated in "Hypotheses". Until then this benchmark reports each test's own z, one-sided p and
   verdict; Holm can only raise a p, so a verdict can weaken there but not strengthen.

## Amendment 3 (2026-11-24): Slayer 1B run added

Written after the review that added Amendment 2 (the cost decision recorded a `null` Slayer row). The run was carried
out after that cost decision and confirms it: the measured result is 0.00. Nothing above changes: no hypothesis,
metric, threshold, control, existing K result or Holm correction is altered. Original protocol text for this amendment
was written in commit `721c3a2474a75b1872674d41149b83e47818046e` (2026-11-23T18:20:39+01:00), before any Slayer output;
this version updates it with the run outcome and keeps the pre-registered settings.

- **Model:** `slayer1b-1.09-k70000`, checkpoint `SlayerLab/Slayer1B-1.09-checkpoints` @
  `adfaf3fd5402bc7f3adbfe077798f20262979433`, file `wagi_70000.pt` (same source as PR #334), converted with the
  1.08 template `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`. Loader:
  `research/common/slayer_lm.py` (reuses `slayer_model.Slayer`), bf16, greedy (the only decoding
  `SlayerLM.generate` supports), context 4096.
- **Prompt:** the same official prompt text the harness builds for the other models (the same problem prompt and
  language), passed as plain text without a chat template (base model, no chat template). No system message; the
  only addition is raw plain-text prompting as in the IFEval Slayer run. Any other prompt addition is a deviation
  recorded in README.
- **BOS / token counting:** exactly one leading BOS per request, matching `research/api-benchmarks/ifeval/lm_eval_slayer.py` and `research/common/slayer_lm.py` (`SlayerLM.tok_batch_encode`). Prompt token counts and generation both include this BOS. Tokenizer: Slayer v6 (32768 vocab) from `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`, `tokenizer.json` sha256 `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`.
- **Context / output length:** `max_new_tokens = 4096 - prompt_tokens` where `prompt_tokens` includes BOS. An item whose prompt
  alone does not leave at least 256 tokens for the answer is not truncated: it gets an empty answer, which the
  official scorer grades as a failure, and is counted in README as `context_overflow` (number and IDs per setting).
  The headline score stays on the full benchmark (all 167 problems, same n as the other models). A second number
  "on items that fit" is reported only in an exploratory section. If more than 50% of items overflow in a setting,
  that setting is reported as `score: null` with the reason and the counts instead.
- **Reading:** the Slayer row is **descriptive**, outside the K1–K3 hypothesis family and the Holm correction. It
  must not change any existing K result. The measured 0.00 confirms the cost decision recorded in Amendment 2;
  the merge decision belongs to the maintainer.

