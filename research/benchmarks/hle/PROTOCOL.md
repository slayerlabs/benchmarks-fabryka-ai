# HLE (no tools) protocol decisions

## Subset

- **Decision:** Use the **text-only subset** of `cais/hle` `test` split: questions where `image` is empty/null.
- **Reason:** LFM3-1.7B is a text-only model. The reference score in issue #303 / LFM3-1.7B model card is for HLE (no tools); evaluating image questions through a text-only API is not equivalent to multimodal evaluation and may fail due to image payload handling. We make an explicit decision rather than silently shrinking.
- **Counts:** Full test split = 2500 questions. Text-only = 2158. Image = 342 (per NeMo Gym HLE README; confirm in run log).
- **Reporting:** Excluded image questions are reported/counted, not scored as zero. The chosen subset and counts are written in `README.md` and result metadata.

## Max output tokens

- **Decision:** `max_completion_tokens=8192` for all models.
- **Reason:** Official HLE README recommends not setting below 8192 for reasoning models and uses 8192 in examples. LFM3 card states "no output limit other than context length" generally; we record 8192 as an explicit, uniform deviation. It is also below the 16384 that `benchmarks/docs/methodology.md` (section 5, written after this run) sets for models without reasoning.
- **Truncation:** answers that hit 8192 tokens count as the judge scores them, and their number is recorded in the result (`truncated`); above 5% the result requires verification (methodology section 5).

## Sampling

- `temperature=0.6`, `top_p=0.95`, one sample per question - from LFM3-1.7B card "Evaluation details" general default (HLE not listed as exception). For Bielik 11B v3.1 this is the LFM3-1.7B card's configuration, not Bielik's own (methodology section 1, written after this run); one sample instead of the methodology's 5 per item (section 4) is a cost deviation. Both are named in `README.md`, Deviations.

## Judge

- Official HLE judge: `o3-mini-2025-01-31`, `max_completion_tokens=4096`, 1 call/question - unavailable to us.
- **Deviation (decided before full judging):** Anthropic Claude judge, funded as an exception (AA-Omniscience precedent). Same official `JUDGE_PROMPT` and fields, `max_tokens=4096`, one call per question, Message Batches API. Main judge actually used: `claude-opus-4-6` (planned `claude-opus-5-5`; the incident is described in `README.md`, Deviations). Agreement check on 300 questions with `claude-opus-5-5` and `claude-sonnet-5-5`, stability repeat of the main judge on 100 questions. Results are not directly comparable with o3-mini-judged numbers.
- Unjudged questions (no verdict after one retry) count as incorrect; the score is also reported on the judged subset.

## Slayer 1B (prepared, not run)

- **Status:** not run - maintainer decision 2026-11-25 (cost vs expected ~0 score). The protocol below was written before any generation and is kept for reproducibility only.
- Descriptive only (base model without instruction tuning), not a headline number comparable 1:1 with instruction-tuned models.
- Deviations from the HLE protocol: no chat template (plain prompt `SYSTEM_PROMPT + "

" + question`, `predict_slayer.py`); 4096-token context; greedy decoding, `bf16`, batched, instead of `temperature=0.6, top_p=0.95`; one leading BOS per request (`research/common/slayer_batch.py`); tokenizer v6 (SHA `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`).
- Generation path: local weights via `research/common/slayer_lm.py` / `research/common/slayer_batch.py`, `predict_slayer.py`, `max_new_tokens = 4096 - prompt_tokens`.
- Context overflow (no truncation): 9/2158 (0.42%) text-only questions have `prompt_tokens > 3840`; they would get an empty answer with `slayer_unsupported=true` and count as incorrect (IDs in `README.md`).
