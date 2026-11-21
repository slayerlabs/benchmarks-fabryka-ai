# GPQA Diamond (DRAFT, exploratory local run)

Graduate-level multiple-choice science questions (biology, physics, chemistry) written to be hard to look up.
The Diamond subset keeps the questions on which expert validators agreed and non-experts failed.

**Status: draft. The main row (Fabryka API, LFM3-1.7B card settings) is NOT computed here.** The numbers below
come from a local exploratory run on rented GPUs and do not close issue #302. See Deviations.

- Paper: [Rein et al. 2023, GPQA: A Graduate-Level Google-Proof Q&A Benchmark](https://arxiv.org/abs/2311.12022)
- Harness: [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) v0.4.13, task
  `gpqa_diamond_cot_zeroshot` (task version 2.2). The repo pin elsewhere is 0.4.9.1 (see Deviations)
- Data: [Idavidrein/gpqa](https://huggingface.co/datasets/Idavidrein/gpqa), config `gpqa_diamond` @
  `83022cefff930aea54f654c0b282e74b9eeda5c6`, 198 questions (full Diamond). Gated: needs consent on Hugging Face
- Metric: `exact_match` with the `flexible-extract` filter (see Deviations for `strict-match`)
- Settings (our run): 0-shot chain of thought, chat template, greedy (`do_sample=false`, `temperature=0.0`),
  stop `</s>`, bf16, `max_gen_toks` 8192 (also 2048 and 16384, see below), 1 trial
- Card settings (reference, LFM3-1.7B): temperature 0.6, top_p 0.95, reasoning on, output limited only by the
  context window (262144), served with vLLM in bf16. GPQA is not among the card's exceptions. CoT, number of
  shots and answer extraction method are not stated on the card
- Extra services: none

## Results

| model | how it runs | score | stderr | n | date |
|---|---|---|---|---|---|
| LFM3-1.7B card | Liquid AI model card, GPQA Diamond (settings above; not reproduced by us) | 63.37 | - | - | - |
| LFM3-1.7B (`lfm3-1.7b`) | local RTX A4000, lm-eval CoT greedy, 8192 tokens, batch 22 | 53.54 | 3.54 | 198 | 2026-11-19 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | local RTX 5090, lm-eval CoT greedy, 8192 tokens, batch 1 | 37.88 | 3.45 | 198 | 2026-11-20 |
| LFM3-1.7B | local RTX 5090, lm-eval CoT greedy, 2048 tokens | 29.29 | 3.24 | 198 | 2026-11-19 |
| Bielik 11B v3.1 | local RTX 5090, lm-eval CoT greedy, 2048 tokens | 36.36 | 3.42 | 198 | 2026-11-19 |
| LFM3-1.7B, combined (projection) | 124 items at 8192 + 74 truncated items re-run at 16384 (RTX 3090, batch 16) | 59.09 | 3.50 | 198 | 2026-11-20 |
| Slayer 1B | not run | null | null | 198 | - |

Rows with a different setup are not interchangeable: compare models only through the paired tests below, never
across rows of different budget or hardware. The "combined" row mixes two token budgets; it is a projection, not
a clean run, and it is not stored in `results/`. The main row (Fabryka API, card settings) is not computed here.
Only the 8192-token runs have files in `results/`.

Paired tests (McNemar, continuity corrected, same 198 questions):

| comparison | net difference (items) | chi2 | p | reading |
|---|---|---|---|---|
| LFM3 vs Bielik, 8192 | +31 for LFM3 | 10.3 | ~0.001 | significant |
| LFM3 vs Bielik, 8192, strict variant (correct only if "answer is" is present) | +27 for LFM3 | - | ~0.006 | significant |
| LFM3 2048 vs 8192 | +48 for 8192 | 30.7 | < 0.001 | strong budget effect |
| Bielik 2048 vs 8192 | +3 for 8192 | 0.12 | ~0.7 | no change |
| LFM3, the 74 truncated items, 8192 vs 16384 | +11 for 16384 | 3.45 | ~0.06 | NOT significant |

## Deviations

- **Not the API, not card settings.** We ran on rented GPUs (vast) with a local lm-eval, greedy decoding and a
  budget of 8192 tokens. The card uses an API-style setup: temperature 0.6, top_p 0.95, reasoning on, a budget up
  to the context window. These numbers are an exploratory variant and a cross-check, not figures to report under
  #302.
- **Token budget and truncation.** At 8192 tokens LFM3-1.7B is cut off: 74 of 198 outputs reach the limit
  (measured with the tokenizer on the pod), and 65.2% reach an "answer is" phrase. The card has an effectively
  unlimited budget, which probably explains most of the gap 53.54 vs 63.37. Budget sweep: 2048 to 8192 adds
  24 points (significant). Re-running only the 74 truncated items at 16384 adds 11 net items, but this is NOT
  significant (p ~0.06). The combined 59.09 mixes two budgets and is a projection. Bielik does not change with
  budget (+3 items, no effect).
- **Harness version.** We used lm-eval 0.4.13 (from `pip freeze` on the pod; it was not saved in `results.json`),
  transformers 5.22.1, torch 2.8.0+cu128. The repo pin elsewhere is 0.4.9.1. Not reconciled.
- **Hardware and batch differ between cells**: LFM3 8192 on RTX A4000 (batch 22), Bielik 8192 on RTX 5090
  (batch 1), LFM3 16384 on RTX 3090 (batch 16), both 2048 runs on RTX 5090 (batch 1). Greedy decoding is
  deterministic in theory, but bf16 with padding flips single tokens (a smoke test showed this). That does not
  explain the 15.7-point gap between the models at 8192.
- **`strict-match` is 0 for LFM3 and about 1% for Bielik, which we treat as a setup finding, not noise.** (On the
  saved 8192 samples we count 0 of 198 for LFM3 and 2 of 198 for Bielik.) We opened the samples. The `strict-match`
  filter only accepts the sentence "The answer is X" and returns `[invalid]` otherwise. LFM3 ends with
  `\boxed{D}` (doc 0), or with `**Answer:** ... Choice **(C)** ... \boxed{11}` (doc 1): there is no "The answer
  is", so strict gives `[invalid]` while `flexible-extract` pulls the letter out of the reasoning and scores 1.
  Bielik doc 0 ends with `Therefore, the correct answer is: \boxed{C}`, again `[invalid]` for strict, and
  `flexible-extract` returns `(C)`. Across the 198 Bielik items strict returns `[invalid]` on 186. Where strict
  does match (Bielik doc 1, "The answer is (B)."), the capture can be wrong or carry extra text, so the filter
  is fragile for chat models. So the zeros come from the models never using the exact 5-shot-style answer
  sentence in zero-shot CoT, not from a broken pipeline: `flexible-extract` is therefore the reported metric.
  The risk is that flexible-extract may also credit a letter that is not the model's final choice; the "answer
  is present" flag below lets a reader check that (157 of 198 for Bielik, 129 of 198 for LFM3 contain the phrase).
- **Slayer 1B is not run on GPQA.** Issue #302 asks for it. The score is `null` ("not run"); this is an open gap.
  No `results/slayer1b-*.json` exists.
- **Per-item files carry flags only.** GPQA is gated behind Hugging Face consent, and the owner's rule is to
  publish per-item flags with no question text and no model output. `results/<model-id>.jsonl.gz` therefore holds
  only `doc_id`, `exact_match` (flexible-extract) and `answer_is_present` (the response contains "answer is").
  This differs from the IFEval card, which stores the model output. A `truncated_8192` flag was not computed,
  because it needs a tokenizer pass over the outputs, which we only did on the pod. This deviation from
  METHODOLOGY.md needs agreement in #bench-team.
- **Not run through `run.sh` from a clean checkout.** `run.sh` is built from the real lm-eval command but has only
  been syntax-checked (`bash -n`), not run on a GPU.

## Reproduce

```bash
export HF_TOKEN=hf_...          # consent to the gated Idavidrein/gpqa dataset required
bash run.sh lfm3-1.7b           # CUDA GPU
bash run.sh bielik-11b-v3.1
bash run.sh lfm3-1.7b --limit 5 # smoke test
```

This reproduces the exploratory local run only. The official path is the Fabryka API at the card settings.
