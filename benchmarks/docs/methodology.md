# Evaluation methodology

How CodeSOTA configures a model for a benchmark run: precision, decoding, repeats, output length, uncertainty, and
what a missing result means. It applies to every model we measure, from about 125M to about 120B parameters, and to
every benchmark, in `benchmarks/` and in `research/`.

The rules follow what independent evaluators and model labs publish (see [Sources](#sources)). Where the sources
disagree or say nothing, the rule is our own decision and is marked **(our decision)**.

## Status and scope

- **New measurements** from 24 November 2026 follow this document. A benchmark's own README may be stricter, never
  looser, and names every deviation with its reason.
- **Existing results** keep the protocol they were measured with. Where that protocol differs from this document,
  the result is labelled as a different configuration, not as an error. Example: the Bielik 11B v3.1 rows that use
  the LFM3-1.7B card's sampling.
- Benchmark-specific protocols (prompt format, few-shot examples, scorer, subsets) stay in the benchmark's directory:
  [`research/METHODOLOGY.md`](../../research/METHODOLOGY.md) for `research/api-benchmarks/`,
  [`research/METODOLOGIA.md`](../../research/METODOLOGIA.md) for the lm-eval benchmarks in `research/benchmarks/`.
  This document sets the model side, which is the same across benchmarks.

## 1. One configuration per model

Each model is measured with one configuration, written down once and used on every benchmark: weights and revision,
precision, serving stack, chat template, system prompt, reasoning mode, and decoding. A model is not run with another
model's settings. Comparing two models means comparing each in its own configuration, under the same benchmark
protocol.

## 2. Precision

- **Native release precision.** Load the weights in the precision they were released in: `torch_dtype` in the
  model's `config.json`. For almost every current model that is bfloat16. A model released with quantized layers is
  run as released (gpt-oss-120b: MXFP4 MoE weights, bfloat16 elsewhere). This follows OLMES ("use the default model
  precision") and the Open LLM Leaderboard, which runs in bfloat16.
- **No quantization below the release precision** in a headline result. FP8 or INT4 is measured only as its own row,
  labelled with its scheme. FP8 is close to lossless on Llama 3.1 (about 99.75% recovery in Red Hat's study), but it
  is still another configuration.
- **A model that does not fit** the available hardware in its release precision is "not run" (section 7), or gets a
  labelled quantized row. It is never quantized silently.
- **Log-likelihood benchmarks.** The central lm-eval run of `research/benchmarks/` was measured in float32 (bfloat16
  for Bielik 11B and the controls named in METODOLOGIA.md). That run stays a closed configuration. Before new
  log-likelihood results in release precision are put in the same table as float32 ones, one control measures 2 to 3
  models in both precisions on the same benchmarks. If the differences are within the standard errors, the tables
  are merged with a `dtype` column; if not, they stay apart **(our decision)**.

## 3. Decoding

Settings are chosen in this order:

1. **The model's own recommendation** for evaluation: its model card or technical report, then its
   `generation_config.json`, for the reasoning mode the card evaluates in. Qwen3, DeepSeek-R1 and NVIDIA Nemotron
   publish such settings, and Artificial Analysis uses a lab's recommendation when there is one.
2. **No recommendation, model without reasoning:** greedy decoding (temperature 0), as Artificial Analysis does for
   non-reasoning models.
3. **No recommendation, reasoning model:** temperature 0.6, top_p 0.95, no top_k, as Artificial Analysis does for
   reasoning models. Greedy decoding is not used for reasoning models: Qwen3 and DeepSeek-R1 warn that it causes
   endless repetition.

Only the parameters the recommendation names are set; everything else stays at the serving stack's neutral value
(top_k off, no repetition or presence penalty). A benchmark whose official protocol fixes decoding (for example a
judge model, or a harness that sends its own temperature) uses the protocol's setting and says so.

## 4. Repeats and scoring

- **Greedy decoding:** one run.
- **Sampling:** several samples per item, scored as pass@1 averaged over the samples. Published practice ranges from
  Qwen3's 10 samples on GPQA Diamond to Epoch's 16 and DeepSeek-R1's 64. We use **10 samples per item for sets up
  to about 500 items and 5 above that (our decision)**.
- **Agentic benchmarks:** the number of trials the benchmark's official protocol or leaderboard asks for (for
  example 5 per task on Terminal-Bench 2.1).
- The score is the mean of the per-item means. Other aggregations (maj@k, pass@k with k > 1) are reported only as
  extra metrics, named as such.

## 5. Output length and truncation

- **Limit:** 16 384 output tokens for models without reasoning (Artificial Analysis), lowered only where the context
  window is smaller. For reasoning models, the maximum the model's creator gives; without one, 32 768 (the limit
  DeepSeek-R1 and Qwen3 evaluate with). The limit never cuts into the prompt: prompt plus limit fit the window.
- **A truncated answer is scored as the benchmark scores it** (usually wrong) and counted. The result records how
  many answers hit the limit. When more than 5% did, the result is marked "requires verification" until a run with a
  higher limit shows the effect **(our decision)**.

## 6. Prompting

- Zero-shot with the benchmark's instruction, unless the benchmark's official protocol uses few-shot examples.
- The model's official chat template, from the pinned revision. Base models without a template get the benchmark's
  raw-text prompt and are labelled so.
- The model's default system prompt, or none when it has no default (Epoch uses an empty one, gpt-oss its default).

## 7. Uncertainty

- Every score has n and a standard error on the benchmark's scale.
- The standard error comes from the per-item scores: `sd / sqrt(n)` over items, which for pass/fail items is
  `sqrt(p(1 - p) / n)`. With several samples per item, it is computed from the per-item means. When items come in
  groups (several trials of one task, questions on one passage, steps of one problem), it is clustered by group, as
  [Miller 2024](https://arxiv.org/abs/2411.00640) recommends. The result says which.
- A difference between two results comes with its standard error and the verdict rule of METODOLOGIA.md (|z| of 2
  and 3).

## 8. Missing results

| shown as | meaning | example |
|---|---|---|
| `null` | the model cannot run the benchmark, with the reason | the context window holds no prompt; no tool-call format for an agentic benchmark |
| `not run` | no score: not run yet, not run by decision, or stopped for budget, with the reason | a cost decision; a run stopped after 2 of 3 turns |
| (no result) | an infrastructure failure: retried, never scored | API errors, timeouts of our own machine |

A benchmark is never cut down to fit a model, and a failure of our infrastructure is never a wrong answer. Requests
that fail for infrastructure reasons are retried (Artificial Analysis retries up to 30 times) and, if they still
fail, the result is not published.

## 9. Reproducibility

vLLM and similar servers are not bit-for-bit deterministic even under greedy decoding: a request's output depends on
the batch it runs in. vLLM's batch-invariant mode (`VLLM_BATCH_INVARIANT=1`) removes that only on some GPUs. So a
result records its concurrency and hardware, and a re-run is expected to agree within the standard error, not
exactly.

## 10. What every result records

In `results/<model-id>.json` (or the run manifest of [`result-artifacts.md`](result-artifacts.md), section
`inference`):

- weights repository and revision, precision (`dtype`) and quantization (or none);
- serving stack and its version, hardware, concurrency;
- chat template, system prompt, reasoning mode;
- decoding: temperature, top_p, top_k and any other parameter set, and where they come from (model card, generation
  config, or this document's default);
- number of samples or trials per item;
- output limit and the number of truncated answers;
- the standard error's method.

A value that cannot be established is written as unknown with the reason, never guessed.

## Where each rule comes from

| rule | source |
|---|---|
| native release precision | OLMES; Open LLM Leaderboard (bfloat16) |
| quantized only as its own row | Red Hat / Neural Magic quantization study |
| lab recommendation first | Artificial Analysis; Qwen3, DeepSeek-R1, Nemotron cards |
| greedy without reasoning | Artificial Analysis |
| 0.6 / 0.95 for reasoning models without a recommendation; no greedy | Artificial Analysis; Qwen3, DeepSeek-R1 |
| no top_k unless recommended | none of the sources sets it otherwise |
| repeats when sampling, pass@1 averaged | Qwen3 (10), Epoch (8 to 16), DeepSeek-R1 (64), Artificial Analysis |
| 10 / 5 samples by set size | our decision |
| output limits 16 384 / 32 768 | Artificial Analysis; DeepSeek-R1, Qwen3 |
| 5% truncation mark | our decision |
| empty or default system prompt | Epoch; gpt-oss card |
| standard errors, clustering | Miller 2024; Epoch |
| retries, infrastructure failures not scored | Artificial Analysis |
| bfloat16 against float32 control before merging tables | our decision |

Meta's Llama 3.1 evaluation details and the Gemma 3 report give no temperature and no evaluation precision, so they
are not used for those rules.

## Sources

- Artificial Analysis, [Intelligence Benchmarking Methodology](https://artificialanalysis.ai/methodology/intelligence-benchmarking), version 5.0.1
- Epoch AI, [Benchmarking hub: about](https://epoch.ai/benchmarks/about)
- Gu et al., [OLMES: A Standard for Language Model Evaluations](https://arxiv.org/abs/2406.08446)
- EleutherAI, [lm-evaluation-harness, leaderboard tasks](https://github.com/EleutherAI/lm-evaluation-harness/blob/main/lm_eval/tasks/leaderboard/README.md)
- DeepSeek, [DeepSeek-R1](https://github.com/deepseek-ai/DeepSeek-R1)
- Qwen Team, [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388), section 4.6
- OpenAI, [gpt-oss-120b and gpt-oss-20b model card](https://arxiv.org/abs/2508.10925)
- NVIDIA, [NVIDIA-Nemotron-Nano-9B-v2](https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2)
- Meta, [Llama 3.1 evaluation details](https://github.com/meta-llama/llama-models/blob/main/models/llama3_1/eval_details.md)
- Google, [Gemma 3 Technical Report](https://arxiv.org/abs/2503.19786)
- Kurtic et al., ["Give Me BF16 or Give Me Death"? Accuracy-Performance Trade-Offs in LLM Quantization](https://arxiv.org/abs/2411.02355)
- Miller, [Adding Error Bars to Evals](https://arxiv.org/abs/2411.00640)
- Thinking Machines Lab, [Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)
