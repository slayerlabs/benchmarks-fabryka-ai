# RULER 128K: measurement protocol

Written and committed before the first model output. Nothing below changes after a result is seen; anything
added later is marked as exploratory in the README.

Refs #306.

## Question

The LFM3-1.7B card reports RULER 128K 65.56 for LFM3-1.7B and 84.63 / 87.11 for Qwen3.5-4B / Qwen3.5-9B. Does a
1.7B model use a long context as well as larger models, and where does it lose? RULER separates a declared context
window from the length a model actually uses ([Hsieh et al. 2024](https://arxiv.org/abs/2404.06654)).

## Sources

- Paper: Hsieh et al. 2024, RULER: What's the Real Context Size of Your Long-Context Language Models?
  [arXiv 2404.06654](https://arxiv.org/abs/2404.06654).
- Harness: [NVIDIA/RULER](https://github.com/NVIDIA/RULER) @ `db43f92ff634bbce1c33d1fb15858aec4bba509a`, its data
  generation (`scripts/data/prepare.py`) and its scorer (`scripts/eval/evaluate.py`, `string_match_all` /
  `string_match_part` per task).
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

## Settings

- The 13 standard RULER tasks: `niah_single_1`, `niah_single_2`, `niah_single_3`, `niah_multikey_1`,
  `niah_multikey_2`, `niah_multikey_3`, `niah_multivalue`, `niah_multiquery`, `vt`, `cwe`, `fwe`, `qa_1`, `qa_2`.
- Lengths: 4096, 8192, 16384, 32768, 65536, 131072 tokens (RULER `max_seq_length`, counted with each model's own
  tokenizer, as RULER does).
- **50 samples per task and length** (RULER's default is 500): 650 per length. This is a cost decision taken
  before the run and is listed as a deviation.
- Instruction-tuned models (LFM3, Qwen3.5, Bielik): the RULER input as one user message through the model's chat
  template, the template's default system prompt and reasoning setting, temperature 0.6, top_p 0.95 (LFM3-1.7B
  card defaults; RULER is not among the card's exceptions). Output limit: the model's context window minus the
  input. The text after the last `</think>` is scored.
- A model whose context window does not hold a length gets `score: null` with the reason for that length; the
  task is not cut down. Bielik (32 768) is measured up to 32768 when input plus RULER's own answer budget fits;
  Slayer (4096) is measured at 4096 only.
- Slayer is a base model: RULER's raw prompt without a chat template, greedy, RULER's per-task answer budget.
- One seed (20261122) for data generation, shared by all models; one sampling seed (20261122) per request.

## Metrics

- Per task and length: RULER's score (percent), n = 50.
- Per length: the unweighted mean over the 13 tasks; SE from a bootstrap over samples within tasks
  (10 000 resamples).
- **Headline:** the mean at 131072 (the number the card reports as RULER 128K).
- Categories for R3: retrieval = the 8 `niah_*` tasks; tracing = `vt`; aggregation = `cwe`, `fwe`; QA = `qa_1`,
  `qa_2`.

## Control (before any claim)

Qwen3.5-9B at 131072 must land within 2 SE of its card value (87.11). If it does not, the setup is the suspect:
no hypothesis below is read until the gap is explained.

## Hypotheses

Verdicts: |z| ≥ 3 clear, 2–3 likely, < 2 noise. Holm correction over the three hypotheses.

- **R1.** LFM3-1.7B's effective context (the longest length whose mean is ≥ 85.6, the Llama-2-7B 4K score that the
  paper uses as the threshold) is shorter than 131072. Confirmed: the mean at 131072 is below 85.6 with z ≤ −3.
  Refuted: the mean at 131072 is ≥ 85.6.
- **R2.** LFM3-1.7B loses score with length faster than Qwen3.5-4B and Qwen3.5-9B. Measure: slope of the mean
  against log2(length) over 4096–131072, per model; SE of the slope difference from a paired bootstrap over
  samples. Refuted: the slope difference is under 2 SE.
- **R3.** LFM3-1.7B's loss from 4096 to 131072 is larger in tracing and aggregation than in retrieval. Measure:
  drop per category; SE clustered by task. Refuted: the retrieval drop is not smaller than the tracing and
  aggregation drops.

## Not in scope

The API row for Bielik, other sample counts, other templates. Any of these, if run later, is exploratory.

## Amendment 1 (2026-11-22, 04:25 UTC)

Written before any Qwen3.5 or Bielik output. Seen so far: one smoke run of LFM3-1.7B at 4096 (2 samples per task,
`--limit 2`), which checked the pipeline and is not part of any result.

- **Scope.** The issue asks for Slayer 1B and Bielik 11B v3.1, with LFM3-1.7B as the reference. Qwen3.5-4B and
  Qwen3.5-9B are dropped to keep the rented-GPU cost to what the issue needs. Models: `lfm3-1.7b`, `bielik-11b-v3.1`,
  `slayer1b-1.08`.
- **Bielik through the Fabryka API** (`bielik-11b-v3.1`), as the issue asks, replacing the vLLM row. The API adds a
  hidden provider system prompt (#277); this is stated in the README next to the row. Context 32 768 tokens; the
  output limit is 32 768 minus the templated input. The "Not in scope" line above no longer applies to this row.
- **Control** moves from Qwen3.5-9B to LFM3-1.7B: its mean at 131072 must land within 2 SE of its card value
  (65.56) before any hypothesis is read.
- **R1 and R3** are unchanged.
- **R2** compares LFM3-1.7B with Bielik 11B v3.1 instead of the Qwen3.5 models: slope of the mean against
  log2(length) over the lengths both models hold (4096–32768); refuted when the difference is under 2 SE.
  Bootstraps are independent per model, because RULER generates each model's data with its own tokenizer.
