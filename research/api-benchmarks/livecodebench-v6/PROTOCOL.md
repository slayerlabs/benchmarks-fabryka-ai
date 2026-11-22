# LiveCodeBench v6: measurement protocol

Written and committed before the first model output. Nothing below changes after a result is seen; anything
added later is marked as exploratory in the README.

Refs #295.

## Question

The LFM3-1.7B card reports LiveCodeBench v6 73.46 for LFM3-1.7B against 61.99 / 69.86 for Qwen3.5-4B /
Qwen3.5-9B: the one coding result on the card where the 1.7B model is ahead of a model five times its size. Is
the lead larger than noise, on which problems does it come from, and does it survive at an equal cost per answer?
Test-time compute lets a smaller model beat a larger one on easy and medium problems but not on the hardest
([Snell et al. 2024](https://arxiv.org/abs/2408.03314)).

## Sources

- Paper: Jain et al. 2024, LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for
  Code, [arXiv 2403.07974](https://arxiv.org/abs/2403.07974).
- Harness and scorer: [LiveCodeBench/LiveCodeBench](https://github.com/LiveCodeBench/LiveCodeBench) @
  `28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24`: its prompt builder for chat models and its code-generation evaluator
  (hidden tests, its own timeouts).
- Data: [livecodebench/code_generation_lite](https://huggingface.co/datasets/livecodebench/code_generation_lite)
  @ `0fe84c3912ea0c4d4a78037083943e8f0c4dd505`, `release_v6`.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) card, "Benchmarks" and "Evaluation
  details".

## Models

| model id | weights @ revision | serving |
|---|---|---|
| `lfm3-1.7b` | `LiquidAI/LFM3-1.7B` @ `1da06bec6a819da10b54c67e5c90972b46d81871` | vLLM, bf16 |
| `qwen3.5-4b` | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | vLLM, bf16 |
| `qwen3.5-9b` | `Qwen/Qwen3.5-9B` @ `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | vLLM, bf16 |
| `bielik-11b-v3.1-vllm` | `speakleash/Bielik-11B-v3.1-Instruct` @ `d6e755d356ad418d0f0e30b8c428db267415ddb9` | vLLM, bf16 |
| `slayer1b-1.08` | `SlayerLab/Slayer1B-1.08` @ `ea0945b11153e67517b70d21192e6076d161f658` (as in the IFEval benchmark) | `research/common/slayer_lm.py` |

Bielik runs on vLLM, not the Fabryka API: the API adds a hidden system prompt and cannot be configured (#277).

## Settings

- **Problem set (main):** all problems of `release_v6`. The card does not say which date window it used; the
  window is fixed here, before any result. Secondary, reported next to it: only the problems added in v6 (the
  `release_v6` problems not in `release_v5`).
- Instruction-tuned models: LiveCodeBench's chat prompt, the model's chat template with its default system prompt
  and reasoning setting, temperature 0.6, top_p 0.95 (card defaults), output limited only by the context window.
  The text after the last `</think>` goes to LiveCodeBench's code extraction.
- One sample per problem (pass@1), sampling seed 20261122 per request.
- Slayer is a base model with a 4096-token context: the raw prompt, greedy, output up to 4096 minus the prompt.
- A request that fails in our infrastructure is retried and, if it still fails, recorded as an error, not as a
  wrong answer. A problem whose prompt does not fit the context is `null` for that model, with the reason.

## Metrics

- pass@1 over the problem set (percent), stderr `sqrt(p(1-p)/n)`.
- Per difficulty (`easy`, `medium`, `hard`, from the dataset): pass@1 and n.
- Output tokens per answer (model tokenizer), and whether the answer finished before the limit.
- Cost per answer ≈ 2 × parameters × output tokens (prompt tokens are shared by all models and left out).
- Budgets for L3 come from the same run: an answer counts at budget B only if it finished within B output tokens.
  The models are not told their budget, so a hard limit at B would produce the same prefix; B = 4096, 16384 and no
  limit.

## Control (before any claim)

Qwen3.5-9B must land within 2 SE of its card value (69.86). If it does not, the setup is the suspect: no hypothesis
below is read until the gap is explained.

## Hypotheses

Verdicts: |z| ≥ 3 clear, 2–3 likely, < 2 noise. Comparisons paired by problem. Holm correction over the three
hypotheses.

- **L1.** LFM3-1.7B's lead over Qwen3.5-9B is not larger than 3 SE of the paired difference. Refuted: LFM3-1.7B is
  ahead with z ≥ 3.
- **L2.** The difference LFM3-1.7B − Qwen3.5-9B is positive on `easy` and `medium` problems and negative on
  `hard` ones. Refuted: the difference has the same sign on all three levels.
- **L3.** At an equal cost per answer, LFM3-1.7B's lead over Qwen3.5-9B disappears. Measure: pass@1 against cost
  per answer from the budgets above; the comparison is at the budget pair whose mean costs are closest. Refuted:
  LFM3-1.7B is ahead with z ≥ 3 at equal cost.

## Limits stated in advance

LiveCodeBench stopped adding problems in 2025, so `release_v6` is older than the training data of LFM3-1.7B and
Qwen3.5. Contamination cannot be ruled out by the release-date split this benchmark was designed for; the report
says so and does not claim a contamination-free result.

## Amendment 1 (2026-11-22, 04:25 UTC)

Written before any Qwen3.5 or Bielik output. Seen so far: a smoke run of LFM3-1.7B on 5 problems (`--limit 5`),
and the running full LFM3-1.7B generation, whose scores have not been computed or read.

- **Scope.** The issue asks for Slayer 1B and Bielik 11B v3.1, with LFM3-1.7B as the reference. Qwen3.5-4B and
  Qwen3.5-9B are dropped to keep the rented-GPU cost to what the issue needs. Models: `lfm3-1.7b`, `bielik-11b-v3.1`;
  `slayer1b-1.08` stays `null` (README, Deviations).
- **Bielik through the Fabryka API** (`bielik-11b-v3.1`), as the issue asks, replacing the vLLM row. The API adds a
  hidden provider system prompt (#277); this is stated in the README next to the row. Context 32 768 tokens; the
  output limit is 32 768 minus the prompt as counted with Bielik's tokenizer and template.
- **Control** moves from Qwen3.5-9B to LFM3-1.7B: its pass@1 must land within 2 SE of its card value (73.46)
  before any hypothesis is read.
- **L1–L3** compare LFM3-1.7B with Bielik 11B v3.1 instead of Qwen3.5-9B, with the same measures and thresholds:
  L1 refuted when LFM3-1.7B is ahead with z ≥ 3 (the original prediction, that a 1.7B model's lead over a larger
  model is within noise, is kept as stated); L2 and L3 unchanged apart from the comparator.

## Amendment 2 (2026-11-22, 04:40 UTC)

- **Slayer checkpoint:** the latest published one, Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`,
  `wagi_70000.pt` from `SlayerLab/Slayer1B-1.09-checkpoints` @ `adfaf3fd5402bc7f3adbfe077798f20262979433`),
  replaces 1.08. Its row stays `null` for the reason in the README (decoding speed), now under this id.

## Amendment 3 (2026-11-22, 05:35 UTC)

Written after the LFM3-1.7B result existed (generated and scored). Nothing above is changed.

- **Two sampling settings this protocol does not name were in effect for LFM3-1.7B.** "Settings" fixes
  temperature 0.6 and top_p 0.95; the request sends those, the seed, and frequency and presence penalty 0. vLLM
  0.34.0 (`generation_config="auto"`) fills the sampling parameters a request leaves unset from the model's
  `generation_config.json` (`LiquidAI/LFM3-1.7B` @ `1da06bec6a819da10b54c67e5c90972b46d81871`). That gave
  `repetition_penalty` 1.1 and `top_k` 50 on every LFM3-1.7B request, instead of vLLM's neutral 1.0 and no top-k
  limit. The README named this as a deviation before the first request, but this protocol did not, and the result
  file did not record it. The method verification of the result found the gap, after the result existed.
- **Effect not estimated.** How much `repetition_penalty` 1.1 and `top_k` 50 move LFM3-1.7B's pass@1 is not
  known. A rerun with them set to neutral values (an ablation) is a separate decision and is not part of this
  amendment. This amendment does not rerun or change the LFM3-1.7B result; the two settings are named next to it.
- **From now on** the result file records the sampling settings in effect: `settings.request_sampling` (what the
  request sends) and `settings.server_defaults` (what the server fills in; on vLLM read from
  `generation_config.json` at the pinned revision, on the Fabryka API `unknown`).
