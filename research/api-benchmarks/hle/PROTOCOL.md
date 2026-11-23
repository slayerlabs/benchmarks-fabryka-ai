# HLE (no tools) protocol decisions

## Subset

- **Decision:** Use the **text-only subset** of `cais/hle` `test` split: questions where `image` is empty/null.
- **Reason:** LFM3-1.7B is a text-only model. The reference score in issue #303 / LFM3-1.7B model card is for HLE (no tools); evaluating image questions through a text-only API is not equivalent to multimodal evaluation and may fail due to image payload handling. We make an explicit decision rather than silently shrinking.
- **Counts:** Full test split = 2,500 questions. Text-only = 2,158. Image = 342 (per NeMo Gym HLE README; confirm in run log).
- **Reporting:** Excluded image questions are reported/counted, not scored as zero. The chosen subset and counts are written in `README.md` and result metadata.

## Max output tokens

- **Decision:** `max_completion_tokens=8192` for all models.
- **Reason:** Official HLE README recommends not setting below 8192 for reasoning models and uses 8192 in examples. LFM3 card states "no output limit other than context length" generally; we record 8192 as an explicit, uniform deviation.

## Sampling

- `temperature=0.6`, `top_p=0.95`, single trial - from LFM3-1.7B card "Evaluation details" general default (HLE not listed as exception).

## Judge

- Official HLE judge: `o3-mini-2025-01-31`, `max_completion_tokens=4096`, 1 call/question. **Pending #bench-team access. No substitution.**

## Slayer 1B (prepared, not run)

- Local generation path prepared: `predict_slayer.py`, wired in `run.sh`, plain prompt (`SYSTEM_PROMPT + "\n\n" + question`), no chat template, greedy bf16, context 4096, loader `research/common/slayer_model.Slayer` (same as `slayer_lm.py` path).
- Prompt tokens counted with Slayer v6 tokenizer on text-only subset (2,158): 9/2158 (0.42%) have `prompt_tokens > 3840` (leave <256 answer tokens); 7 > 4096; max 14098, min 62, mean 334.08. These overflow questions will be recorded as `slayer_unsupported` empty responses and counted in denominator (no cutting, rule 8).
- Before first local Slayer run: stop and ask owner (heavy-process rule).
