# AA-LCR: measurement protocol

Refs #305.

## What had been seen when this was written

Written before any model answered an AA-LCR question and before any judge call. Already seen, and the reason the
protocol below is short: the token length of every prompt (`results/lengths.json`) and a probe of the Fabryka AI API
window (`results/api-window.json`). The probe sent prompts of 1052 to 100913 templated tokens with `max_tokens` 1; only
the HTTP status, the error text and `usage.prompt_tokens` were recorded, no model output was read. Nothing else was run.
Anything added after a result exists is marked as exploratory in the README.

## Question

The LFM3-1.7B card reports AA-LCR 52.83 for LFM3-1.7B. Can Slayer 1B and Bielik 11B v3.1 (through the Fabryka AI API)
be scored on AA-LCR, or does the benchmark's input not fit their context windows?

## Sources

- Dataset and prompts: [ArtificialAnalysis/AA-LCR](https://huggingface.co/datasets/ArtificialAnalysis/AA-LCR) @
  `9a77ef56b717057ade24ceab4d273712a0b4f19e` (version 1.1, 2026-09-04): `AA-LCR_Dataset.csv` (100 questions) and
  `extracted_text/AA-LCR_extracted-text.zip`. The card gives the prompt template, the document order
  (`data_source_filenames`), and the judge prompts. There is no harness repository.
- Version 1.0.0 (`bdae010bbce259820c0e34c1d7cce210d966fb75`) has the same questions and documents, 16 other answer keys
  and a different judge prompt; the card says scores of the two versions are not directly comparable.
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) @
  `1da06bec6a819da10b54c67e5c90972b46d81871`, "Benchmarks" (AA-LCR 52.83) and "Evaluation details".

## What the reference does not state

The card's evaluation details say: every eval served with vLLM in BF16 at full context, temperature 0.6, top_p 0.95, no
output limit other than the context length, unless listed; AA-LCR is not listed. The card does not state the AA-LCR
version (1.0.0 or 1.1), the judge model, the number of repeats per question, or how an output that never finishes is
handled. We do not guess these. Our setting is the dataset card's v1.1; whether the 52.83 was measured on 1.0.0 or 1.1
is unknown, so the comparison with it is approximate even for a model that fits.

## Judge

AA-LCR scores with an LLM equality checker: **GPT-5.6 Luna (medium)** with the v1.1 system and user prompts (card,
"Scoring Approach"; v1.0.0 uses no system prompt and "Reply only with CORRECT or INCORRECT"). It is a paid API and the
methodology forbids paid accounts without agreement in #bench-team, so no judge is run or substituted. A different judge
would change the benchmark and could not be compared with 52.83.

## Models

| model id | weights | serving | window |
|---|---|---|---|
| `bielik-11b-v3.1` | `speakleash/Bielik-11B-v3.1-Instruct` @ `d6e755d356ad418d0f0e30b8c428db267415ddb9` | Fabryka AI API (hidden provider system prompt, #277) | 32768 |
| `slayer1b-1.09-k70000` | `SlayerLab/Slayer1B-1.09-checkpoints` @ `adfaf3fd5402bc7f3adbfe077798f20262979433` `wagi_70000.pt`, as in ruler-128k | `research/common/slayer_lm.py`, raw prompt | 4096 |

Windows: Bielik's from `GET /v1/models` (32768) and checked with the probe: a templated prompt of 32767 tokens with 1
output token is accepted and one of 32768 is rejected (HTTP 400, generic error text, so the limit is inferred from the
boundary); the server's `usage.prompt_tokens` equalled the local count at every accepted size. Bielik's
`max_position_embeddings` is also 32768. Slayer's from the `block` of its config (4096), the window ruler-128k uses.
Token counts: the model's own tokenizer, for Bielik through its chat template with the defaults (which include the
provider system prompt), for Slayer the raw prompt plus BOS.

## Fit rule

A question fits a model when its prompt, counted as above, plus 1 output token is within the model's window. The
benchmark is not cut down: no truncation of documents, no chunking, no retrieval, no dropping of documents.

- **No question fits:** `score: null` with the reason for that model, for the full benchmark. No generation, no judge.
  The README reports the length distribution against the window.
- **Part of the set fits (not the case at the time of writing):** the full-benchmark result is still `null`. A subset
  score would be additional information only, labelled as a subset, and running it needs Dario's decision.

## Result at the time of writing

Measured with the dataset at the pinned revision: the shortest prompt has 100913 templated tokens for Bielik (window
32768) and 85211 for Slayer (window 4096); no question fits either model. Both results are `null`.

## Not in scope

LFM3-1.7B (the card's number is quoted, not rerun), other judges, a subset, a longer-context serving of either model, and
version 1.0.0. Any of these, if run later, is exploratory and needs a decision first.
