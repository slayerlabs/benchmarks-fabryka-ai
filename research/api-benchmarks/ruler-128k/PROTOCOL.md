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

## Amendment 2 (2026-11-22, 04:40 UTC)

Written before any Slayer output (a 1.08 data-generation step was stopped before generation).

- **Slayer checkpoint:** the latest published one, Slayer 1B 1.09 at update 70 000, replaces 1.08. Model id
  `slayer1b-1.09-k70000`: `wagi_70000.pt` from `SlayerLab/Slayer1B-1.09-checkpoints` @
  `adfaf3fd5402bc7f3adbfe077798f20262979433` (sha256 `9ed73494fc139422f5314f72b4f970242454a7ab9d8caceee6b52fe5bdfc40c0`
  in that revision's `SHA256SUMS`), converted with `research/tools/konwertuj.py` against
  `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`, as the full run does for this checkpoint
  (`research/tools/przebieg_centralny.sh`). The converted `model.safetensors` must have the sha256 the full run
  recorded (`b9e31fc953af44638fd64ca163dd8d5658cfe02928445fa9a412f11a618bb24e`, `research/tools/ewaluacja/ewaluacja.py`).
  Everything else about the Slayer row is unchanged (4096 only, raw prompt, greedy).

## Amendment 3 (2026-11-22, 05:35 UTC)

Written before any LFM3-1.7B RULER result was summarized: the LFM3-1.7B run was generating on the rented GPU and
none of its outputs had been scored or read.

- **Sampling settings the protocol did not name.** The settings above name temperature 0.6, top_p 0.95 and the
  seed, and the requests send only these (plus the output limit). vLLM 0.34.0, started with its default
  `--generation-config auto`, fills every sampling field a request does not set from the model's
  `generation_config.json` (priority: request, then the model's generation config, then vLLM's defaults). For
  `LiquidAI/LFM3-1.7B` @ `1da06bec6a819da10b54c67e5c90972b46d81871` that adds **`repetition_penalty` 1.1 and `top_k`
  50** to every LFM3-1.7B request; its `temperature` 0.1 there is overridden by the request's 0.6. This was not
  stated here when the protocol was written. It was found by the independent verification of the LiveCodeBench v6
  LFM3-1.7B result (same serving setup), after the LFM3-1.7B run of this benchmark had started.
- The requests are not changed: the run in progress and any later LFM3-1.7B run use the same settings, and every
  result records the sampling in effect in `settings.sampling`. Bielik through the Fabryka API: only what is sent is
  known, the API's own defaults are recorded as unknown. Slayer decodes greedily and is not affected.
- The effect of `repetition_penalty` 1.1 and `top_k` 50 on the RULER score is not estimated. An ablation (the same
  requests with `repetition_penalty` 1.0 and `top_k` 0 sent explicitly) is a separate decision; until it is made,
  the control and the hypotheses are read with these settings as part of the LFM3-1.7B setup.

## Amendment 4 (2026-11-22, 11:20 UTC)

**Written after the result.** The LFM3-1.7B run was scored and the control had failed before this amendment was
decided. Nothing below changes a number that was computed; it changes how the control is read and adds a second
scoring next to the pre-registered one.

- **The control as measured stays reported.** LFM3-1.7B at 131072: 71.69 +- 0.93 against the card's 65.56,
  z = 6.62, FAIL under the rule above (within 2 SE).
- **Why the card value is not a comparable target.** The card's evaluation details (LFM3-1.7B card @ `1da06bec`,
  line 536) say only: "All models were served with vLLM in BF16 at their full context length [...] Unless listed
  below, every eval uses temperature 0.6 and top_p 0.95, with no output limit other than the context length."
  RULER is not among the listed exceptions. The card does not state the harness (RULER's own scripts or another
  implementation), the thinking mode, the number of samples, how an output that never closes its reasoning is
  scored, or any output cap or timeout. The review of the run found no scoring bug; the gap can come from any of
  these unstated choices, so 65.56 cannot serve as a pass/fail target for this setup. Liquid was not asked.
- **The control is marked `not comparable (Amendment 4)` instead of passed,** and the hypotheses R1-R3 are read
  with that mark. compare.py still prints the measured z and FAIL against 65.56.
- **Every score is reported twice.** Pre-registered, as above: the text after the last `</think>` is scored, and
  the whole text when there is none. Strict: an output without `</think>` scores 0 (errors stay out of the score,
  as before). This holds for the headline and for every per-length and per-task score of the runs whose chat
  template opens a reasoning block (LFM3-1.7B, Bielik); Slayer's raw prompt has none, so it has only the
  pre-registered score. Reason: at 131072, 10 LFM3-1.7B outputs loop to the length limit without `</think>`,
  they are scored on their whole text, and 8 of them score above 0; strict scoring gives 70.51 at 131072.
- **Verdicts.** R1-R3 verdicts are computed on the pre-registered scoring. The verdict under strict scoring (its own
  Holm family, m = 3) is shown next to each; it does not replace it.

## Amendment 5 (2026-11-22, 16:00 UTC)

**Written after the Bielik result**, which got strict 0.00 at every length. Correction of Amendment 4: its rule
(strict scoring for the runs whose chat template opens a reasoning block) stands, but its example "(LFM3-1.7B,
Bielik)" was wrong. Bielik's template at `d6e755d3`, with its defaults, ends the generation prompt `<think></think>`:
the reasoning block is closed before the model's first token, so its outputs never contain `</think>`. Only
LFM3-1.7B's prompt (`...<|im_start|>assistant\n<think>`) opens one. Whether a prompt opens it is decided from the
rendered prompt (it ends with an open `<think>`), recorded at generation or rendered from the pinned template; where
it does not, strict scoring is null with the reason, as for Slayer. Bielik is reported with its pre-registered
score only. No pre-registered number changes.
