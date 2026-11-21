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
| LFM3-1.7B (`lfm3-1.7b-2048`) | local RTX 5090, lm-eval CoT greedy, 2048 tokens, batch 1 | 29.29 | 3.24 | 198 | 2026-11-19 |
| Bielik 11B v3.1 (`bielik-11b-v3.1-2048`) | local RTX 5090, lm-eval CoT greedy, 2048 tokens, batch 1 | 36.36 | 3.43 | 198 | 2026-11-19 |
| LFM3-1.7B (`lfm3-1.7b-16k`) | rented RTX 3090, lm-eval CoT greedy, 16384 tokens, batch 16 | 58.59 | 3.51 | 198 | 2026-11-21 |
| Slayer 1B | not run | null | null | 198 | - |

Rows with a different setup are not interchangeable: compare models only through the paired tests below, never
across rows of different budget or hardware. The main row (Fabryka API, card settings) is not computed here.
The 2048, 8192 and 16384 runs each have files in `results/`. The 16384 run is a clean full-198 run (it replaces an
earlier two-budget projection of 59.09 that was never stored). A 32768 pass on the items still truncated at 16384 is
running and will land as a follow-up commit.

![LFM3-1.7B GPQA Diamond accuracy by token budget, 2048 to 32768; 32768 is a projection](charts/budget-curve.svg)

The curve reads left to right as the budget doubles (x axis is log2). The three measured points are 2048, 8192 and
16384; 32768 is a projection, drawn with a dashed segment and a hollow marker: the 162 items that concluded by 16384
are kept and the 36 still truncated are re-scored at the rate truncated items reached once unblocked (~32%). It is
not a measurement; the running 32768 pass will replace it.

Paired tests (same 198 questions, paired difference per item, z = Δ / SE; the SE is the paired SE over the items,
and the reading follows the repo convention |z| < 2 noise, 2-3 borderline, >= 3 clear):

| comparison | net (items) | Δ ± SE (points) | z | reading |
|---|---|---|---|---|
| LFM3 vs Bielik, 8192 | +31 for LFM3 | +15.66 ± 4.59 | z = 3.41 | clear lead for LFM3 |
| LFM3 vs Bielik, 8192, strict variant (correct only if "answer is" is present) | +27 for LFM3 | +13.64 ± 4.73 | z = 2.88 | LFM3 ahead, just under the clear line |
| LFM3, 2048 vs 8192 | +48 for 8192 | +24.24 ± 3.93 | z = 6.16 | large budget effect for LFM3 |
| Bielik, 2048 vs 8192 | +3 for 8192 | +1.52 ± 2.91 | z = 0.52 | noise |
| LFM3, 8192 vs 16384 (full 198) | +10 for 16384 | +5.05 ± 3.26 | z = 1.55 | noise on the full set |
| LFM3, 8192 vs 16384 (the 74 items truncated at 8192) | +11 for 16384 | +14.86 ± 7.12 | z = 2.09 | borderline; selected subset |

Reading the budget bump: on the full 198 the 8192 -> 16384 move is within noise (z = 1.55), and the headline rises
53.54 -> 58.59. The gain is concentrated in the items that were truncated at 8192 (the 74-item subset, z = 2.09),
but even there it is borderline. At 16384, 36 of 198 (18%) still reach the cap, so 16384 is not the ceiling; the
32768 pass on those items is being computed and will land as a follow-up commit.

## Deviations

- **Not the API, not card settings.** We ran on rented GPUs (vast) with a local lm-eval, greedy decoding and a
  budget of 8192 tokens. The card uses an API-style setup: temperature 0.6, top_p 0.95, reasoning on, a budget up
  to the context window. These numbers are an exploratory variant and a cross-check, not figures to report under
  #302.
- **Token budget and truncation.** At 8192 tokens LFM3-1.7B is cut off: 74 of 198 outputs reach the limit
  (measured with the tokenizer on the pod), and 65.2% reach an "answer is" phrase. The card has an effectively
  unlimited budget, which probably explains most of the distance from the card: at 8192 our 53.54 sits 2.8 SE below
  the card's 63.37 (z = -2.8, using our run's SE 3.54); at 16384 the full run reaches 58.59, 1.4 SE below the card
  (z = -1.36). Budget sweep for LFM3: 2048 to 8192 adds 24.24 ± 3.93 points (z = 6.16); 8192 to 16384 adds
  5.05 ± 3.26 (z = 1.55, within noise on the full 198), with the gain concentrated in the items truncated at 8192.
  At 16384, 36 of 198 (18%) still reach the cap, so the budget is still biting and 16384 is not the ceiling; a 32768
  pass on those items is being computed. Bielik barely moves with budget (+1.52 ± 2.91 points, z = 0.52, noise).
- **Harness version.** We used lm-eval 0.4.13 (from `pip freeze` on the pod; it was not saved in `results.json`),
  transformers 5.22.1, torch 2.8.0+cu128. The repo pin elsewhere is 0.4.9.1. Not reconciled.
- **Hardware and batch differ between cells**: LFM3 8192 on RTX A4000 (batch 22), Bielik 8192 on RTX 5090
  (batch 1), LFM3 16384 on RTX 3090 (batch 16), both 2048 runs on RTX 5090 (batch 1). Greedy decoding is
  deterministic in theory, but bf16 with padding flips single tokens (a smoke test showed this). That does not
  explain the 15.66 ± 4.59 point difference between the models at 8192 (z = 3.41).
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
- **Slayer 1B is not run on GPQA.** Issue #302 asks for it. The score is `null` ("not run"); this is still open.
  No `results/slayer1b-*.json` exists; this item is still open.
- **Per-item files carry flags only.** GPQA is gated by Hugging Face consent, and the owner's rule is to
  publish per-item flags with no question text and no model output. `results/<model-id>.jsonl.gz` therefore holds
  only `doc_id`, `exact_match` (flexible-extract) and `answer_is_present` (the response contains "answer is").
  This differs from the IFEval card, which stores the model output. The 16384 file
  (`results/lfm3-1.7b-16k.jsonl.gz`) additionally carries a `truncated_16384` flag (the tokenizer pass was run on
  the pod); the 8192 and 2048 files do not, so a `truncated_8192` flag is not present. This deviation from
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
