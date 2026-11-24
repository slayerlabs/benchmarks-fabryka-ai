# SciCode

Whether a model writes research code in Python that passes the authors' numerical tests, one subproblem at a time,
where each step builds on the model's own code for the earlier steps. The pre-registered question, control and
hypotheses are in [PROTOCOL.md](PROTOCOL.md); this file says how the run is done. Refs #297.

- Paper: [Tian et al. 2024, SciCode: A Research Coding Benchmark Curated by Scientists](https://arxiv.org/abs/2407.13168)
- Harness and scorer: [scicode-bench/SciCode](https://github.com/scicode-bench/SciCode) @
  `e3158ea011d4235245a547460d3688d7ccbf9900`: prompts and code files by `Gencode` in `eval/scripts/gencode.py`
  (with background: `eval/data/multistep_template.txt`; without: `eval/data/background_comment_template.txt`), code
  extraction `scicode.gen.models.extract_python_script`, scorer `eval/scripts/test_generated_code.py`, unchanged
- Data: [SciCode1/SciCode](https://huggingface.co/datasets/SciCode1/SciCode) @
  `4510f6a6aa27c43fad7b43da2c59602a86e88480`, split `test`: 65 problems, 291 subproblems, of which 288 are
  answered and scored (13.6, 62.1 and 76.3 are supplied by the harness). Test targets `test_data.h5`,
  1,049,345,865 bytes, sha256 `48b0272a88b17dbd29777c217e1b4fb2b019b92e11cc2add847409db9541b890`, from the
  byte-identical mirror `xantheocracy/scicode-mirror` @ `2f903a64a1c4eb62c7c649b0caf7ecb2c0217590`
- Metric: subproblem pass rate, correct steps / 288 × 100 as `test_generated_code.py` prints it, **with
  background** (headline); `stderr` is `sqrt(p(1-p)/n)` and `stderr_clustered` the SE clustered by problem (65
  clusters), which the verdicts use. `other_metrics`: the same without background, main problems solved out of 65
  in both settings, the scorer's verdicts (pass, fail, time out), output tokens per answer (mean, median, max),
  unfinished answers, length stops, prompts over the context, the share of answers that contain `<think>`, on
  the API the API's prompt count minus ours, and `extraction_e1`: pass rate, clustered SE and main problems of
  both settings under the secondary extraction E1 (PROTOCOL.md Amendment 1), never the headline
- Settings: one request per subproblem in step order, the prompt Gencode builds as the only user message (no
  system message of ours), temperature 0.6, top_p 0.95, seed 20261122; LFM3-1.7B also `top_k` 0,
  `repetition_penalty` 1.0, frequency and presence penalty 0, `max_tokens` = 262144 minus the prompt counted by
  vLLM's `/tokenize`; Bielik `max_tokens` = 32768 minus the local count minus 64. Scorer: 1800 s per step,
  sequential, BLAS threads 1, in the container of `Dockerfile.scoring` (python 3.11.9, packages from
  `requirements-scoring.lock`)
- Extra services: the Fabryka AI API for Bielik; one GPU for LFM3-1.7B; a Linux VM with Docker for scoring
- Fabryka AI API, listed at `https://fabryka.ai/v1/models` on 2026-11-23: two models, `bielik-11b-v3.1`
  (`context_length` 32768) and `basal-2.0-max` (`context_length` 32768). The exact id sent for this benchmark is
  `bielik-11b-v3.1` and the maximum context as served is 32768 tokens, which is the context the requests are
  budgeted against (Settings). Slayer 1B is not on that list, as in `ifeval`, which is why its row is `null`.

## Results

<!-- readme.py: results (generated from results/ by readme.py; edit readme.py, not this block) -->

Headline: correct subproblems with background, out of 288 (test_generated_code.py). Verdicts read the SE clustered by problem (65 clusters).

| model | thinking | serving | output limit | correct (%) | stderr | stderr clustered | n | main problems | mean output tokens | date |
|---|---|---|---|---|---|---|---|---|---|---|
| LFM3-1.7B (`lfm3-1.7b`) | on (template default) | vLLM 0.34.0, bf16, one H100 | context minus prompt tokens (context 262144) | 32.64 | 2.76 | 3.63 | 288 | 5/65 (7.69%) | 7708.5 | 2026-11-22 |
| LFM3-1.7B (`lfm3-1.7b-nothink`) | off requested (`enable_thinking: false`) | the same vLLM server | context minus prompt tokens (context 262144) | 24.65 | 2.54 | 3.04 | 288 | 4/65 (6.15%) | 5203.3 | 2026-11-22 |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | no reasoning switch through the API | Fabryka AI API, with the API's provider system prompt | context minus prompt tokens minus a margin of 64 (context 32768) | 2.43 | 0.91 | 1.01 | 288 | 0/65 (exact 95% CI 0 to 5.52%) | 655.2 | 2026-11-22 |
| Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`) | no (base model) | local, research/common/slayer_lm.py, bf16, greedy | context minus prompt tokens (context 4096) | 0.00 | 0.00 | 0.00 | 288 | 0/65 (exact 95% CI 0 to 5.52%) | 3185.4 | 2026-11-24 |

Both prompt settings: correct (%) ± stderr (correct/288; clustered SE), main problems solved (all scored steps pass) out of 65, and the scorer's verdicts per step:

| run | setting | correct | main problems | pass | fail | time out |
|---|---|---|---|---|---|---|
| lfm3-1.7b | with background | 32.64 ± 2.76 (94/288; clustered 3.63) | 5/65 (7.69%) | 94 | 193 | 1 |
| lfm3-1.7b | without background | 22.92 ± 2.48 (66/288; clustered 3.02) | 1/65 (1.54%) | 66 | 219 | 3 |
| lfm3-1.7b-nothink | with background | 24.65 ± 2.54 (71/288; clustered 3.04) | 4/65 (6.15%) | 71 | 216 | 1 |
| lfm3-1.7b-nothink | without background | 17.36 ± 2.23 (50/288; clustered 2.75) | 0/65 (exact 95% CI 0 to 5.52%) | 50 | 236 | 2 |
| bielik-11b-v3.1 | with background | 2.43 ± 0.91 (7/288; clustered 1.01) | 0/65 (exact 95% CI 0 to 5.52%) | 7 | 281 | 0 |
| bielik-11b-v3.1 | without background | 1.74 ± 0.77 (5/288; clustered 0.75) | 0/65 (exact 95% CI 0 to 5.52%) | 5 | 281 | 2 |
| slayer1b-1.09-k70000 | with background | 0.00 (0/288; exact 95% CI 0 to 1.27) | 0/65 (exact 95% CI 0 to 5.52%) | 0 | 288 | 0 |
| slayer1b-1.09-k70000 | without background | 0.00 (0/288; exact 95% CI 0 to 1.27) | 0/65 (exact 95% CI 0 to 5.52%) | 0 | 288 | 0 |

| run | setting | output tokens mean / median / max | unfinished (thinking on) | stopped by the length limit | prompts over the context | answers containing `<think>` |
|---|---|---|---|---|---|---|
| lfm3-1.7b | with background | 7708.5 / 6814.0 / 39805 | 0 | 0 | 0 | 0 of 288 |
| lfm3-1.7b | without background | 8232.5 / 7638.5 / 23673 | 0 | 0 | 0 | 0 of 288 |
| lfm3-1.7b-nothink | with background | 5203.3 / 3710.0 / 31765 | 0 | 0 | 0 | 0 of 288 |
| lfm3-1.7b-nothink | without background | 5324.0 / 3896.5 / 27465 | 0 | 0 | 0 | 0 of 288 |
| bielik-11b-v3.1 | with background | 655.2 / 562.0 / 2716 | 0 | 0 | 0 | 0 of 288 |
| bielik-11b-v3.1 | without background | 697.2 / 626.5 / 1918 | 0 | 0 | 0 | 0 of 288 |
| slayer1b-1.09-k70000 | with background | 3185.4 / 3257.0 / 3624 | 72 | 72 | 216 | 0 of 72 |
| slayer1b-1.09-k70000 | without background | 3082.7 / 3215.0 / 3611 | 288 | 288 | 0 | 0 of 288 |

Secondary extraction E1 (PROTOCOL.md Amendment 1), the same answers: a step whose E1 file is byte-identical to its official file took the official verdict, the others were scored by the same scorer:

| run | setting | correct, official | correct, E1 | main problems, E1 | steps with the official verdict (identical file) | steps scored under E1 |
|---|---|---|---|---|---|---|
| lfm3-1.7b | with background | 94/288 | 32.64 ± 2.76 (94/288; clustered 3.63) | 5/65 (7.69%) | 288 | 0 |
| lfm3-1.7b | without background | 66/288 | 22.92 ± 2.48 (66/288; clustered 3.02) | 1/65 (1.54%) | 288 | 0 |
| lfm3-1.7b-nothink | with background | 71/288 | 24.65 ± 2.54 (71/288; clustered 3.04) | 4/65 (6.15%) | 288 | 0 |
| lfm3-1.7b-nothink | without background | 50/288 | 17.36 ± 2.23 (50/288; clustered 2.75) | 0/65 (exact 95% CI 0 to 5.52%) | 288 | 0 |
| bielik-11b-v3.1 | with background | 7/288 | 3.12 ± 1.03 (9/288; clustered 1.20) | 0/65 (exact 95% CI 0 to 5.52%) | 84 | 204 |
| bielik-11b-v3.1 | without background | 5/288 | 1.74 ± 0.77 (5/288; clustered 0.75) | 0/65 (exact 95% CI 0 to 5.52%) | 157 | 131 |
| slayer1b-1.09-k70000 | with background | 0/288 | 0.00 (0/288; exact 95% CI 0 to 1.27) | 0/65 (exact 95% CI 0 to 5.52%) | 288 | 0 |
| slayer1b-1.09-k70000 | without background | 0/288 | 0.00 (0/288; exact 95% CI 0 to 1.27) | 0/65 (exact 95% CI 0 to 5.52%) | 288 | 0 |

Bielik's prompt: the API's `usage.prompt_tokens` minus our local count with Bielik's own template, with background: min 0, max 0. Its request log holds 2 events (recovered 1, retry 1; HTTP 503 1, none 1).

Baselines: 0 for random and majority answers (no fixed output passes a step's numerical tests). The LFM3-1.7B card reports 28.47; the control is in Hypotheses.

Scoring: all three runs on one VM (AMD EPYC 7302P 16-Core Processor, 30 vCPUs), SciCode `e3158ea0`, container image `sha256:261432609549a9638b735a97e423d9b2b2aa952754dfd2b649cd6b02c09c59cb` (network none; python 3.11.9, numpy 1.26.4 with openblas64 0.3.23.dev, scipy 1.13.1, sympy 1.12.1, h5py 3.11.0), BLAS threads 1, 1800 s per step; `test_data.h5` sha256 `48b0272a88b17dbd29777c217e1b4fb2b019b92e11cc2add847409db9541b890` checked; dataset revision the scorer loaded: `4510f6a6aa27c43fad7b43da2c59602a86e88480`.
Slayer was scored separately on AMD EPYC 7B13 64-Core Processor, 30 vCPUs, container image `sha256:1dcf9f45f290156b182c2aa0d3be8efaba386fdad9a03c0f9ace45ae080d981e` (network none); see Deviations.

Raw outputs (with thinking, not committed): the LFM3-1.7B runs in `labaj-agency/out/coding-group/box/export.tgz`, sha256 `2bcf89771f031feb5fbae69617bcd5a60d2d73359c58cadf3c62e7ba218c51c6`; Bielik's in `out/bielik-11b-v3.1/generations.jsonl on the generating Mac`. Each run's generations.jsonl sha256 equals its result file's `raw_outputs.sha256` (results/raw-outputs.json).

Setup check (not a model): the dev split's `ground_truth_code`, fed through the same Gencode files and scorer, passes 48 of 50 steps and 13 of 15 problems (results/checks/dev-ground-truth.json); the 2 failing steps fail with the authors' own code (SciCode issue #43).

<!-- readme.py: end results -->

## Reference results

The cited table's SciCode row, each model's own reported value (LFM3-1.7B card, "Benchmarks", read on
2026-11-23). **28.47 is this benchmark's headline metric: correct subproblems / 288 x 100 (82/288).** The card
does not say whether the background was given (PROTOCOL.md, "Sources" and "Limits"); five of the six values are
k/288 and Qwen3.5-4B's 23.02 is not (66/288 = 22.92, 67/288 = 23.26). All six are downloadable on Hugging Face:
`LiquidAI/LFM3-1.7B`, `LiquidAI/LFM2.5-2.6B`, `openbmb/MiniCPM5-2B`, `google/gemma-4-e4b`,
`Qwen/Qwen3.5-4B`, `Qwen/Qwen3.5-9B` (the card names no repository; these are the repositories of its names,
checked on 2026-11-23).

| model | SciCode on the card | k/288 |
|---|---|---|
| LFM3-1.7B, the reference here | **28.47** | 82 |
| LFM2.5-2.6B | 16.32 | 47 |
| MiniCPM5-2B | 27.78 | 80 |
| Gemma 4 E4B | 25.00 | 72 |
| Qwen3.5-4B | 23.02 | not k/288 |
| Qwen3.5-9B | 31.60 | 91 |

The card's "Evaluation details" for that table: every model on vLLM in BF16 at its full context (262144 tokens
for LFM3-1.7B, Qwen3.5-4B and Qwen3.5-9B; 131072 for LFM2.5-2.6B, MiniCPM5-2B and Gemma 4 E4B), temperature
0.6 and top_p 0.95 for every evaluation it does not list, and no output limit other than the context. SciCode is
not listed among the exceptions, so those are its settings; this run sends the same temperature, top_p and seed
to every model and takes the output limit from the context (Settings above).

## Hypotheses

<!-- readme.py: hypotheses (generated from results/ by readme.py; edit readme.py, not this block) -->

K1 control: LFM3-1.7B 32.64 ± 3.63 (clustered) vs card 28.47, z = +1.15: passed

| test | value (pp) | SE (pp) | z | Holm p support | Holm p refute | raw | verdict after Holm | read |
|---|---|---|---|---|---|---|---|---|
| K2 | -13.89 | 2.18 | -6.38 | 3.58e-10 | 1 | supported | supported (clear) | True |
| K2 under E1 (Amendment 1) | -13.20 | 2.18 | -6.06 | 2.73e-09 | 1 | supported | supported (clear) | True |
| K3 | +7.12 | 2.02 | +3.52 | 1 | 0.000659 | refuted | refuted (clear) | True |
Holm m = 4, family: scicode K2, scicode K3, livecodebench-pro-25q2 K2, livecodebench-pro-25q2 K3

Without background (descriptive, not tested; PROTOCOL.md: the without-background run is no second chance at the control):

| test form | value (pp) | SE (pp) | z |
|---|---|---|---|
| K1 form: LFM3-1.7B minus the card's 28.47 | -5.55 | 3.02 | -1.84 |
| K2 form | -14.58 | 2.18 | -6.70 |
| K3 form | +5.03 | 1.76 | +2.87 |

Reading:

- **K1** passed by PROTOCOL.md's rule: LFM3-1.7B with background lands within 2 clustered SE of its card value (+4.17 pt, z = +1.15), so K2 and K3 are read. The reporting rules' reproduction check (within ±2 pt of a published number) is not met: the gap is 4.17 pt; at n = 288 that check cannot be decided either way, since 2 clustered SE are 7.26 pt.
- **K2** (supported (clear)) compares Bielik through the API with a number on the card, not with a model run here: LFM2.5-2.6B's 16.32, with the SE floor of PROTOCOL.md. Under E1 (Amendment 1) z = -6.06, supported (clear): K2 does not depend on code extraction: official and E1 both supported (supported (clear) after Holm).
- **K3** refuted under the pre-registered switch (`enable_thinking: false`): with the switch off LFM3 keeps more than half of its lead over Bielik (D = +7.12 ± 2.02, z = +3.52; the lead itself +30.21, z = +8.18). *Descriptive, from the raw outputs, added after the results (Amendment 2):* the switch removes reasoning only in part: with it off 147 of 288 answers with background still reason and close a `</think>` (median 93.3% of an answer's characters before it), against 288 of 288 with thinking on; 17 of its 71 passed steps come from such answers, and it writes 5203 output tokens per answer on average against 7708. How much of the lead thinking itself buys is therefore undetermined by K3.
  - *Exploratory (explore.py):* counting those 17 passes as failed gives D = +1.22 ± 1.99 (z = +0.61): the lead that survives the switch sits in answers that still reason.
  - *Descriptive:* `lfm3-1.7b-nothink` with background step 14.2 (officially fail; its test checks a simulation the step's code runs on random numbers without a seed) re-scored with the same image: fail 1 of 10, pass 9 of 10. The refuter reports SciCode-Verified flagging problem 14 (not checked here). A pass there would raise D, not lower it.
  - *Descriptive:* `lfm3-1.7b-nothink` without background step 14.2 (officially fail; its test checks a simulation the step's code runs on random numbers without a seed) re-scored with the same image: fail 10 of 10. The refuter reports SciCode-Verified flagging problem 14 (not checked here).
- **With Student's t instead of the normal** (descriptive, df = 64, our two tests; LiveCodeBench Pro's p as recorded) the verdicts are the same: K2 Holm p 3.39e-08, supported (clear); K3 Holm p 0.00122, refuted (clear), against 0.00135 for "clear" (z = 3), a small margin.
- **Holm over the Coding group** (m = 4) used LiveCodeBench Pro 25Q2's K2 and K3 from `results/group-tests-livecodebench-pro-25q2.json`, copied from branch `research/livecodebench-pro-25q2` at `f16b862b`.

K3 robustness (descriptive, added after the results; no verdict reads it): D without the problems that contribute most to it, with the Holm p of "refuted" (the other three tests unchanged):

| problems left out | D (pp) | SE (pp) | z | Holm p | verdict after Holm |
|---|---|---|---|---|---|
| 77 | +6.52 | 2.01 | +3.24 | 0.0018 | refuted (likely) |
| 77, 42 | +5.86 | 1.91 | +3.07 | 0.00324 | refuted (likely) |
| 77, 42, 15 | +5.35 | 1.85 | +2.90 | 0.00567 | refuted (likely) |
| 77, 42, 15, 72 | +4.96 | 1.86 | +2.66 | 0.0116 | refuted (likely) |
| 77, 42, 15, 72, 13 | +4.84 | 1.96 | +2.46 | 0.0206 | refuted (likely) |
| 77, 42, 15, 72, 13, 21 | +4.49 | 1.95 | +2.30 | 0.0319 | undetermined |

Jackknife over problems: SE 2.04, z = +3.50. Cluster bootstrap over problems (10000 draws, seed 20261122): 95% interval of D [3.18; 11.13] pp. Sign of each problem's contribution: 33 positive, 8 negative, 24 zero (exact sign test p = 5.6e-05 one-sided, 0.00011 two-sided). "Clear" rests on problem 77: without it K3 is refuted (likely).

<!-- readme.py: end hypotheses -->

## Exploratory

<!-- readme.py: exploratory (generated from results/ by readme.py; edit readme.py, not this block) -->

**EXPLORATORY: added after the results were seen (PROTOCOL.md, Amendment 2); no verdict reads it.** From the raw outputs (raw_outputs.py), the last answer of each step:

| run | setting | answers closing a reasoning block with `</think>` | median share of the answer before its last `</think>` | passed steps whose answer closes `</think>` |
|---|---|---|---|---|
| lfm3-1.7b | with background | 288 of 288 | 93.3% | 94 of 94 |
| lfm3-1.7b | without background | 288 of 288 | 92.3% | 66 of 66 |
| lfm3-1.7b-nothink | with background | 147 of 288 | 93.3% | 17 of 71 |
| lfm3-1.7b-nothink | without background | 146 of 288 | 92.6% | 23 of 50 |
| bielik-11b-v3.1 | with background | 8 of 288 | 63.3% | 0 of 7 |
| bielik-11b-v3.1 | without background | 0 of 288 | none | 0 of 5 |

Bielik's API template ends the prompt with an empty `<think></think>`, so each `</think>` in its output is a stray tag it wrote: 8 answers with background, 0 without. The official extraction reads only the text after it.

Empty official extractions (no code at all) and their cause, read from the text the extraction saw (`lone fence`: exactly one fence line and no ```` ```python ````, so the official rule took the text after a fence that closes code never opened, here nothing), and over all answers how many have such a lone fence (where E1 differs) or no fence line:

| run | setting | empty extractions | lone fence | unfinished | other | answers with a lone fence | answers without a fence line |
|---|---|---|---|---|---|---|---|
| lfm3-1.7b | with background | 0 | 0 | 0 | 0 | 0 | 0 |
| lfm3-1.7b | without background | 0 | 0 | 0 | 0 | 0 | 0 |
| lfm3-1.7b-nothink | with background | 0 | 0 | 0 | 0 | 0 | 0 |
| lfm3-1.7b-nothink | without background | 0 | 0 | 0 | 0 | 0 | 0 |
| bielik-11b-v3.1 | with background | 35 | 33 | 0 | 2 | 120 | 68 |
| bielik-11b-v3.1 | without background | 32 | 32 | 0 | 0 | 60 | 1 |

<!-- readme.py: end exploratory -->

## Deviations

How the measurement ran (facts from results/scoring-events.json and the result files; PROTOCOL.md Amendment 2):

<!-- readme.py: scoring (generated from results/ by readme.py; edit readme.py, not this block) -->

- Generation (commit at the start of each session): lfm3-1.7b: `e65c9c27` (2026-11-22T16:51:37+00:00, AMD EPYC 9684X 96-Core Processor, NVIDIA H100 80GB HBM3); lfm3-1.7b-nothink: `e65c9c27` (2026-11-22T16:51:26+00:00, AMD EPYC 9684X 96-Core Processor, NVIDIA H100 80GB HBM3); bielik-11b-v3.1: `04eb5c19` (2026-11-22T16:33:53+00:00, Apple M5 Pro, limit 2), `2ade850c` (2026-11-22T17:05:18+00:00, Apple M5 Pro).
- Scoring code: `3b731440030a178e73f660c632c2df68fd2fce29` for all three runs (final `--score`).
- Side by side: 2026-11-22T18:31:32Z parallel: bielik and nothink start next to lfm3-1.7b (deviation: models scored side by side) — the three models were scored at the same time in three containers on one VM (results/scoring-vm/score-scicode.log, with the load average at each start and end); a step near the 1800 s limit can time out under load that it would pass on an idle machine.
- Container memory limit 48g (run.sh --score, docker --memory); the official scorer has none. The kernel's OOM killer ended 3 test scripts: Nov 22 20:09:46 UTC (container `3eeaa55f5947`, 47.7 GiB resident); Nov 22 22:45:12 UTC (container `a7f34304de3a`, 47.7 GiB resident); Nov 22 23:50:55 UTC (container `a7f34304de3a`, 47.7 GiB resident). In the final scorer output the killed steps are: bielik-11b-v3.1 e1_without_background 53.4, bielik-11b-v3.1 without_background 53.4; each counts as a failed step, as the scorer grades it.
- Disk full: the journal logged 250 "No space left on device" lines at Nov 22 20:17:04 UTC. Queue log, 2026-11-22T21:08:49Z: final: removed Bielik official without_background logs (disk-full window) for rescoring. Queue log, 2026-11-22T21:10:16Z: final: removed Bielik official without_background logs (disk-full window) for rescoring. The official LFM3 steps whose verdicts were written between 20:10 and 20:20 UTC, and the time-outs that ran through that window, were re-scored afterwards with the same image and compared with the kept verdicts: lfm3-1.7b without background (lfm3-63.6): 1 of 1 the same; lfm3-1.7b-nothink without background (nothink-64.6): 1 of 1 the same; lfm3-1.7b-nothink without background (nothink-window): 42 of 42 the same.
- E1 identity reuse: lfm3-1.7b with background: 288 reused, 0 scored; lfm3-1.7b without background: 288 reused, 0 scored; lfm3-1.7b-nothink with background: 288 reused, 0 scored; lfm3-1.7b-nothink without background: 288 reused, 0 scored; bielik-11b-v3.1 with background: 84 reused, 204 scored; bielik-11b-v3.1 without background: 157 reused, 131 scored.
- **Extraction after the last `</think>` for a model without thinking.** SciCode @ `e3158ea0` hands the whole answer to `extract_python_script` (it knows no `</think>`); PROTOCOL.md cuts after the last `</think>` for every model. Re-scored where it matters for `bielik-11b-v3.1` (reference_extraction.py on the scoring VM): with background: 8 answers contain `</think>`, 6 give other code, 28 step files differ (with the later steps that include that code), passed 7 after the last `</think>` and 7 from the whole answer, 0 verdicts change (the differing files: fail -> fail); without background: 0 answers contain `</think>`, 0 give other code, 0 step files differ (with the later steps that include that code), passed 5 after the last `</think>` and 5 from the whole answer, 0 verdicts change. For the LFM3-1.7B runs the reference extraction would read the reasoning too; its effect there is not measured.

<!-- readme.py: end scoring -->

- **The scoring commit differs from the generation commits, and two scoring records say `dirty: true`.**
  Generation and scoring are separate steps (PROTOCOL.md): the LFM3-1.7B runs were generated on the H100 box at
  `e65c9c27` and Bielik's on the Mac (its first 2 problems, 77 and 11, 48 answers, in the smoke session at
  `04eb5c19`, the other 528 at `2ade850c`, resuming that session); the generation path of `scicode_runner.py` is the
  same in all three commits (between them only the docstring and the scoring functions change). All three were
  scored at `3b731440`; each record's `runner_sha256` equals the files at the commit it names. `dirty` is git's view
  of the VM checkout when a step started: after the first model's summary, `results/manifest.json` there was
  modified, so the later two scoring steps saw a tracked file changed; no runner file differed (the tests compare
  the recorded runner sha256 with the commits).
- **The dev check's 2 failing steps fail with the authors' own code**: 78.3 (the target has shape (2, 2), the
  reference returns (10001, 2)) and 70.8 (`np.allclose` false), as SciCode issue #43 reports.
- **Only the model call is ours.** `scicode_runner.py` runs `Gencode.generate_response_with_steps` itself, which
  builds the prompt from the model's extracted code for the earlier steps, takes the code with
  `extract_python_script` and writes `<problem>.<step>.py` with `save_response_with_steps`; it replaces
  `gencode.get_model_function` by a function that sends the prompt to vLLM or the Fabryka API. gencode's own
  clients cannot send `top_p`, `seed`, `max_tokens` or the template switch (it passes only the temperature), and its
  OpenAI path adds the system message "You are a helpful assistant.", which PROTOCOL.md excludes (its litellm path
  sends the prompt alone, as we do).
- **SciCode's API clients are stubs, not installed.** `scicode/gen/models.py` imports `openai`, `anthropic`,
  `google.generativeai`, `config` and `litellm` (and `litellm.utils`) when it loads. None is used on our path, so
  `scicode_runner.harness()` puts stub modules under these names in `sys.modules` of the generating process (a
  `google` package only when none is installed); calling anything from them raises. The scorer and the test scripts
  never import `models.py`. `rich`, which `scicode/utils/log.py` imports, is installed.
- **Steps run in parallel across chains.** gencode's `main` goes through the problems one by one. A chain here is
  one problem in one setting; its steps run in order through one `Gencode` instance, and chains run in parallel
  (`CONCURRENCY`, also the number of requests in flight: 64 on vLLM, 2 on the API).
- **A resumed run gives the prompts of an uninterrupted one.** A step already answered is not asked again; its
  recorded extracted code goes into `previous_llm_code`, which is what Gencode would hold in an uninterrupted run.
  (Gencode's own resume would rebuild it from the code file with `get_function_from_code`, which keeps only the
  step's function and so changes later prompts.) A failed request (after the retries) stops its chain at that
  step; a rerun asks it again and continues. Scoring refuses while any step lacks an answer, because the scorer
  tests only the files present and counts a problem as solved when all its present files pass.
- **The scorer's unpinned dataset load is pinned through the cache.** `test_generated_code.py` calls
  `load_dataset('SciCode1/SciCode', split=...)` without a revision. Unchanged, it runs offline
  (`HF_DATASETS_OFFLINE=1`) against a cache that holds only the pinned revision (`prefetch` loads it with
  `revision=`, and `score` checks the cache before running), so `datasets` takes that revision and logs its sha;
  `score` stops unless the logged sha is the pin and records it (`provenance.scoring.runs.<setting>.printed.
  dataset_revision_seen`), with the sha256 of both data files and what `main` pointed to at prefetch.
  `datasets` 2.20.0 cannot load this dataset (cast error: `problems_dev.jsonl` has a `general_solution` column
  that `problems_test.jsonl` lacks, SciCode issue #44); 3.6.0 can, and is used for generation and scoring.
- **Dependency versions are ours; SciCode pins none.** Scoring: python 3.11.9 (`python:3.11.9-slim-bookworm` by
  digest), numpy 1.26.4, scipy 1.13.1, sympy 1.12.1, h5py 3.11.0, matplotlib 3.9.0, datasets 3.6.0, pandas 2.3.3,
  pyarrow 17.0.0, huggingface-hub 0.36.2 (`requirements-scoring.lock`, with hashes; the full list of packages and
  numpy's BLAS is recorded in each result's `provenance.scoring.packages`). scipy is kept below 1.14 because two
  problems list `from scipy.integrate import simps` in their dependencies, removed in 1.14; numpy below 2 for the
  API of SciCode's time. Generation uses the same scientific versions (`requirements-generate.lock`). A numerical
  test near the `allclose` tolerance can depend on these versions and on BLAS threading (PROTOCOL.md, Limits).
- **Scoring runs in a container without network.** The scorer executes the models' code as plain `python`
  subprocesses. run.sh runs it in the `scicode-scoring` image with `--network none`, 48 GB memory, this directory
  read-only and only `out/<model-id>/` (and the dataset cache) writable, on the scoring VM only. The code can still
  write into `out/<model-id>/`, including the scorer's per-step logs; nothing checks those logs against a second
  run.
- **Unfinished and over-long answers.** With thinking on (`lfm3-1.7b`), an answer without `</think>` or stopped by
  the length limit gives empty code, which the next steps receive (PROTOCOL.md). Without thinking (nothink,
  Bielik), PROTOCOL.md defines no unfinished case: the text after the last `</think>` is extracted as it is, also
  from an answer stopped by the length limit, and such answers are counted (`length_stops`). A prompt over the
  context is `unsupported`: not sent, empty code, and it fails like a wrong answer (PROTOCOL.md).
- **Answers are extracted by SciCode's rule, whatever their fences.** `extract_python_script` takes the first
  ```` ```python ```` block, else the text after the first ```` ``` ````, else the whole response (printing "Fail to
  extract python code from specific format."); this is kept. In the 2-problem Bielik smoke test (24 steps per
  setting, not committed) 41 of 48 answers began directly with code, without an opening fence, and 17 of them
  closed a fence they never opened; for those the rule takes the prose after the closing fence, a SyntaxError
  that every later step of the problem inherits through its code file (with background 0 of 24 steps passed,
  without 1 of 24). Whether the Fabryka API drops the opening fence or Bielik writes it so is not known (logged in
  the API problems note); the same pattern is in 54 of the 1055 Bielik answers of livecodebench-v6. PROTOCOL.md
  Amendment 1 adds extraction E1 as a secondary number for every model and both settings: `--score` also rebuilds
  each step file from the recorded answers with E1 (the text before the only fence line when there is exactly one;
  otherwise the official result; Gencode assembles the files with the earlier steps' E1 code) into
  `out/<model-id>/generated_code_e1/`. A step whose E1 file is byte-identical to its official file is the same
  program under the same tests, so it takes the official verdict without a second scorer run; the other steps' E1
  files are copied alone into `out/<model-id>/generated_code_e1_scored/` and scored there by the same, unchanged
  scorer. Each result counts both (`other_metrics.extraction_e1.<setting>.reused_identical` and `scored`); since
  that scorer run sees only the differing files, its printed problem count is not compared, and the E1
  main-problem count comes from the per-step verdicts (its printed correct steps plus the reused passes must equal
  ours). Prompts are not regenerated, so later
  steps were asked with the official extraction's code. A text whose only ```` ``` ```` sits inside a line has no
  fence line, so E1 keeps the whole text there, where the official rule splits on it (the amendment's wording;
  rare). hypotheses.py reports K2's z under E1 next to K2 and, when the verdicts differ, says K2 depends on code
  extraction.
- **Bielik runs on the Fabryka AI API, with its hidden provider system prompt** and no reasoning switch, as in
  livecodebench-v6: the request carries only `model`, `messages`, `temperature`, `top_p`, `max_tokens` and `seed`,
  and the prompt is counted locally with Bielik's tokenizer and chat template
  (`speakleash/Bielik-11B-v3.1-Instruct` @ `d6e755d356ad418d0f0e30b8c428db267415ddb9`, gated) with a margin of 64.
- **The clustered SE** is `sqrt(G/(G-1) · Σ_g (Σ_{i∈g} (y_i − ȳ))²) / n` (the CR1 small-sample factor
  G/(G−1); PROTOCOL.md names the clustering, not the factor). For K3 the same formula on `d_i`.
- **K1 "within 2 clustered SE"** is `|p − 0.2847| / SE_cl ≤ 2`; with SE_cl = 0 it is `undetermined`. When K1
  fails, hypotheses.py still computes K2 and K3 and marks them `read: false`.
- **Holm over the Coding group** (agreed with the LiveCodeBench Pro 25Q2 harness): each test has
  `p_support = Φ(z)` and `p_refute = 1 − Φ(z)`; Holm with m = 4 runs separately over the four `p_support` and the
  four `p_refute`; a test with no p (K3 "precondition not met", or the other benchmark's file not given) enters as
  p = 1. `hypotheses.json` lists our two tests under `group_tests` (`benchmark`, `id`, `z`, `p_support`,
  `p_refute`, `outcome_raw`), and `--group <other>/hypotheses.json` reads the other benchmark's.
- **`--limit N`** takes the first N problems of the split in dataset order (all their steps, both settings).
- **The `output` of a `.jsonl.gz` line is the extracted code of that step**, not the whole model output (which
  with thinking would exceed the repo's 10 MB limit); the raw outputs stay in `out/<model-id>/generations.jsonl`
  and their sha256 is in the result file.
- **Slayer 1B 1.09 at update 70 000 is not run** (PROTOCOL.md, Models); `bash run.sh slayer1b-1.09-k70000`
  writes its `score: null` file with the reason.
- **Contamination cannot be ruled out** (PROTOCOL.md, Limits); SciCode-Verified's defects are not corrected.

## Hand check

Read by hand before trusting the run, five subproblems per model: prompt, committed output of the step and its
verdict, on the primary setting (with background), subproblems **77.1, 13.1, 42.3, 65.4, 11.3** (2026-11-23).
The prompts are not in the repo: `prompt_replay.py` rebuilds them with the pinned harness from the committed
code of the earlier steps, the path a resumed run uses
(`.venv-gen/bin/python prompt_replay.py --hand 77.1 13.1 42.3 65.4 11.3`).

- **Prompts**: the same text in the three runs for the first step of a problem (77.1 is 2536 characters
  everywhere, 13.1 is 2800), the multistep template with background — PROBLEM DESCRIPTION, PROBLEM STEPS AND
  FUNCTION CODE, NEXT STEP, DEPENDENCIES, RESPONSE GUIDELINES — 2536 to 8547 characters over these five; later
  steps differ only through the code carried over.
- **lfm3-1.7b**: 77.1, 13.1 and 11.3 pass, 42.3 and 65.4 fail; five distinct functions with docstrings
  (`wrap`, `partial_derivs_vec`, `threshold_current`, `ghz_protocol`, `tensor`), 1211 to 24280 output tokens.
  94/288 pass in this setting.
- **lfm3-1.7b-nothink**: the same five prompts, different answers: 42.3 and 65.4 pass here, 11.3 fails.
  71/288 pass.
- **bielik-11b-v3.1**: all five fail. 77.1 and 11.3 answer in prose the official extraction keeps no code from,
  13.1, 42.3 and 65.4 write code that fails the tests; its 7 passes with background sit on other subproblems
  (32.1, 39.1, 58.1, 64.1, 64.3, 66.5, 80.1).

Neither all zeros nor identical between models or between the two LFM3 runs, so Bielik's low score is the model
and the extraction of Amendment 1, not a setup bug; the same pipeline passes 48 of 50 dev steps with the
authors' own code (Results). What is read here is the committed output of each step, which is what the scorer
tests; the full answers are not in the repo (their sha256 is in `results/raw-outputs.json`).

## Slayer 1B's context

Slayer 1B was not run, so its row is `score: null` (Results, "Reproduce"). Its served context is 4096 tokens
and the prompts of this benchmark are longer than that for a large part of the split. Counted with Slayer's own
tokenizer (`research/slayer-1b/tokenizer/tokenizer.json`, 16384 tokens) over the prompts the pinned harness
builds (`prompt_replay.py` prints this table):

| run the prompt carries the code of | with background | without background | median, with bg | max, with bg |
|---|---|---|---|---|
| lfm3-1.7b | 88/288 steps, 29/65 problems | 73/288 steps, 20/65 problems | 2702 | 14518 |
| lfm3-1.7b-nothink | 134/288 steps, 41/65 problems | 113/288 steps, 36/65 problems | 3610 | 30159 |
| bielik-11b-v3.1 | 49/288 steps, 13/65 problems | 46/288 steps, 12/65 problems | 2166 | 10167 |

A prompt over the context is not sent and counts as failed (PROTOCOL.md, "Settings"); the benchmark is not cut
down to fit it, and a prompt that does fit still has to leave room for the answer. These are counts of prompts,
not of a Slayer run: a run would carry Slayer's own earlier code, which does not exist, so how many tasks
Slayer itself could not answer within its context is not known without running it.

## Reproduce

Each model is generated once (both settings), then scored on the scoring VM. Every step resumes where it stopped.

LFM3-1.7B, on a Linux box with one NVIDIA GPU and a vLLM 0.34.0 server already serving `LiquidAI/LFM3-1.7B` @
`1da06bec6a819da10b54c67e5c90972b46d81871` as `lfm3-1.7b` with `--max-model-len 262144` and no reasoning parser
(without `BASE_URL` run.sh starts one):

```bash
BASE_URL=http://localhost:8000 bash run.sh lfm3-1.7b
BASE_URL=http://localhost:8000 bash run.sh lfm3-1.7b-nothink
```

Bielik 11B v3.1, on a Mac or Linux machine, after `hf auth login` with access to the gated Bielik repo:

```bash
FABRYKA_API_KEY=... bash run.sh bielik-11b-v3.1 --limit 2   # smoke test
FABRYKA_API_KEY=... bash run.sh bielik-11b-v3.1
```

Scoring, on a fresh Ubuntu 22.04 x86_64 VM with Docker, as root, in a checkout of this repo: once
`bash setup_scoring_vm.sh` (clones SciCode, downloads and checks `test_data.h5`, builds the image, caches the
pinned dataset), then copy each `out/<model-id>/` from the generating machine into this directory's `out/` and run

```bash
bash run.sh lfm3-1.7b --score
bash run.sh lfm3-1.7b-nothink --score
bash run.sh bielik-11b-v3.1 --score
bash run.sh dev-ground-truth && bash run.sh dev-ground-truth --score   # setup check, no model
python3 hypotheses.py results --group results/group-tests-livecodebench-pro-25q2.json
```

`--score` writes `results/<model-id>.json` and `.jsonl.gz` (with `--limit N`: `out/<model-id>/<model-id>-limitN.*`).
Provenance as in livecodebench-v6: `out/<model-id>/run.json` holds each step's code commit, runner checksums,
machine and sampling in effect, plus for scoring the image id, `test_data.h5` sha256, the dataset revision the
scorer loaded and the package versions; `manifest.json` holds the sha256 each step wrote, which the next step
checks; `api-events.jsonl` every failed request attempt and each recovery.

After scoring, checks on the scoring VM (scoring image, no network; written for coding-judge-vm's paths):

```bash
bash vm_checks.sh   # window_rescore.py on the disk-full window steps, reference_extraction.py for Bielik
bash vm_repeat.sh lfm3-1.7b-nothink with_background 14.2 10 /root/scicode/round1/repeat-14.2-wb   # a step re-scored N times
```

Their outputs and the VM's logs are copied into `results/scoring-vm/`: the queue log, the final scorer outputs, the
kernel's OOM lines, the journal's disk-full lines, `window-*.json` (window_rescore.py), `reference-extraction-*.json`
(reference_extraction.py) and `repeat-*-run*.json` (vm_repeat.sh). Then, on the machine with the raw outputs
(stdlib only):

```bash
python3 raw_outputs.py ~/Documents/GitHub/labaj-agency/out/coding-group/box/export.tgz   # results/raw-outputs.json
python3 scoring_events.py   # results/scoring-events.json, from results/scoring-vm/
python3 hypotheses.py results --group results/group-tests-livecodebench-pro-25q2.json   # results/hypotheses.json
python3 explore.py          # results/exploratory.json
python3 readme.py           # the generated blocks of this README; --check compares byte for byte
```

Prompts of the committed runs, rebuilt with the pinned harness for the hand check and for the Slayer-context
table (needs the SciCode clone and the pinned dataset, both made by `run.sh`, and `.venv-gen`):

```bash
.venv-gen/bin/python prompt_replay.py --hand 77.1 13.1 42.3 65.4 11.3   # replay, then those five subproblems
.venv-gen/bin/python prompt_replay.py --reuse                            # the counts of "Slayer 1B's context"
```

Tests: `.venv-gen/bin/python -m pytest ../../tests/test_scicode.py ../../tests/test_scicode_results.py -q` (no GPU,
network or `test_data.h5`; the raw-output recount runs where the archive and `out/bielik-11b-v3.1/` are).
`uv pip sync` in run.sh makes `.venv-gen` match the lock exactly, so it removes what the lock does not hold:
install pytest there once with `uv pip install --python .venv-gen/bin/python pytest`.
