# Results

Every published result of this repository in one place, generated from the research pipeline's result files
by `python -m codesota.leaderboard` (do not edit by hand). Slayer 1B first, next to reference models.

[All models](all-models.md) · [Instruction following](instruction-following.md) · [All results as JSONL](results.jsonl) · [Benchmark status](../BENCHMARKS.md)

<p align="center"><img src="charts/headline.png" alt="Slayer 1B 1.09 and reference models, accuracy per benchmark" width="100%"></p>

## Headline

Value ± standard error; accuracies in percent. Protocol: research central run of November 2026: 0-shot log-likelihood scoring through lm-eval, full test sets, float32 (Bielik 11B: bfloat16), batch 1, no chat template. Slayer requests start with one BOS token, the reference models' requests with none (measured on Pythia-1B v0 only: at most 0.0105 difference).

### Reasoning and science

| benchmark | metric | Slayer 1B 1.09 (step 40 000, training in progress) | Bielik 11B v3.0 Instruct | LFM3-1.7B-Base | Bielik 1.5B v3 | Qwen3.5-0.8B-Base |
|---|---|---:|---:|---:|---:|---:|
| ARC-Easy | `acc` ↑ | 66.6 ± 1.0 | 81.9 ± 0.8 | 71.7 ± 0.9 | 54.6 ± 1.0 | 70.5 ± 0.9 |
| ARC-Challenge | `acc_norm` ↑ | 35.0 ± 1.4 | 58.1 ± 1.4 | 42.9 ± 1.4 | 36.1 ± 1.4 | 40.4 ± 1.4 |
| MathQA | `acc_norm` ↑ | 22.5 ± 0.8 | 48.5 ± 0.9 | 39.1 ± 0.9 | 32.4 ± 0.9 | 33.4 ± 0.9 |

### Commonsense

| benchmark | metric | Slayer 1B 1.09 (step 40 000, training in progress) | Bielik 11B v3.0 Instruct | LFM3-1.7B-Base | Bielik 1.5B v3 | Qwen3.5-0.8B-Base |
|---|---|---:|---:|---:|---:|---:|
| HellaSwag | `acc_norm` ↑ | 52.8 ± 0.5 | 79.4 ± 0.4 | 58.9 ± 0.5 | 63.7 ± 0.5 | 54.8 ± 0.5 |
| PIQA | `acc_norm` ↑ | 71.2 ± 1.1 | 78.9 ± 1.0 | 68.6 ± 1.1 | 71.9 ± 1.0 | 71.3 ± 1.1 |
| WinoGrande | `acc` ↑ | 57.7 ± 1.3 | 73.0 ± 1.2 | 58.6 ± 1.3 | 62.4 ± 1.3 | 60.1 ± 1.3 |
| Social IQa | `acc` ↑ | 40.9 ± 1.1 | 51.1 ± 1.1 | 45.4 ± 1.1 | 43.6 ± 1.1 | 41.9 ± 1.1 |
| WSC273 | `acc` ↑ | 63.7 ± 2.4 | 82.4 ± 2.4 | 71.4 ± 2.4 | 76.6 ± 2.4 | 71.4 ± 2.3 |
| EWoK | `ewok` ↑ | 62.8 ± 0.8 | n/a | 66.0 ± 0.8 | 69.5 ± 0.8 | 67.6 ± 0.8 |

### Knowledge (medical)

| benchmark | metric | Slayer 1B 1.09 (step 40 000, training in progress) | Bielik 11B v3.0 Instruct | LFM3-1.7B-Base | Bielik 1.5B v3 | Qwen3.5-0.8B-Base |
|---|---|---:|---:|---:|---:|---:|
| MedMCQA | `acc` ↑ | 30.1 ± 0.7 | 53.6 ± 0.8 | 37.8 ± 0.7 | 39.1 ± 0.8 | 40.3 ± 0.8 |
| PubMedQA | `acc` ↑ | 56.2 ± 2.2 | 73.0 ± 2.0 | 59.4 ± 2.2 | 62.4 ± 2.2 | 67.6 ± 2.1 |

### Language modeling and linguistics

| benchmark | metric | Slayer 1B 1.09 (step 40 000, training in progress) | Bielik 11B v3.0 Instruct | LFM3-1.7B-Base | Bielik 1.5B v3 | Qwen3.5-0.8B-Base |
|---|---|---:|---:|---:|---:|---:|
| LAMBADA (OpenAI) | `acc` ↑ | 45.4 ± 0.7 | 71.4 ± 0.6 | 50.7 ± 0.7 | 61.1 ± 0.7 | 51.2 ± 0.7 |
| WikiText-2 | `byte_perplexity` ↓ | 1.702 ± 0.016 | 1.566 ± 0.011 | 1.616 ± 0.014 | 1.674 ± 0.011 | 1.717 ± 0.013 |
| BLiMP | `acc` ↑ | 81.5 ± 2.1 | 83.2 ± 1.8 | 79.3 ± 2.3 | 81.9 ± 2.0 | 79.9 ± 2.2 |

### Polish

| benchmark | metric | Slayer 1B 1.09 (step 40 000, training in progress) | Bielik 11B v3.0 Instruct | LFM3-1.7B-Base | Bielik 1.5B v3 | Qwen3.5-0.8B-Base |
|---|---|---:|---:|---:|---:|---:|
| MultiBLiMP (Polish) | `accuracy` ↑ | 98.6 ± 0.2 | 99.6 ± 0.1 | 89.2 ± 0.5 | 94.5 ± 0.4 | 84.5 ± 0.6 |

### Instruction following

Bielik 11B is v3.1 here; the log-likelihood tables above have v3.0, the version the full run measured. IFEval (#313): lm-eval 0.4.9.1, 541 prompts. Slayer: local GPU, raw prompt, greedy, up to 1280 tokens. Bielik: Fabryka API with its chat template, temperature 0.6, top_p 0.95. The protocols differ per model. Details: [instruction-following.md](instruction-following.md).

| model | how it ran | prompt-level strict accuracy | n |
|---|---|---:|---:|
| Slayer 1B 1.08 | local GPU, raw prompt, greedy | 18.1 ± 1.7 | 541 |
| Bielik 11B v3.1 Instruct | Fabryka API, chat template, sampled | 55.3 ± 2.1 | 541 |

## Read with care

- **Not one class.** Bielik 11B has ten times the parameters of the others, and it and LFM3-1.7B (in the full tables) are instruction-tuned models scored here on raw text.
- **Slayer 1B 1.09 at step 40 000 is a training checkpoint**, not a release; its result is preliminary.
- **A difference between two models needs a paired test**, not two overlapping intervals; the research report has them ([full run](../../research/results/full-run-2026-11/README.md)).
- **Status.** Only benchmarks marked `verified` in [BENCHMARKS.md](../BENCHMARKS.md) have a reproduced reference result; the others are measurements without that check.

## Sources

- Log-likelihood benchmarks: [`research/results/full-run-2026-11/`](../../research/results/full-run-2026-11/README.md), manifest [`manifest.jsonl`](../../research/results/full-run-2026-11/manifest.jsonl) (commands, revisions, weight checksums).
- IFEval: [`research/api-benchmarks/ifeval/results/`](../../research/api-benchmarks/ifeval/results/), per-prompt outputs in `*.jsonl.gz`.
- Every row of [`results.jsonl`](results.jsonl) names its source file.
