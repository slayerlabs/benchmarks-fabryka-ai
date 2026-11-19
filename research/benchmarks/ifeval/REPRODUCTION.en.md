# IFEval: reproduction (stage B)

English version of REPRODUCTION.md. The verdict and reviewer sentence are filled by the reviewer at PR merge (as in winogrande).

The procedure is described in [METODOLOGIA.md](../../METODOLOGIA.md), section "B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)". Command and environment: [`RECIPE.md`](RECIPE.md). Whatever was not recorded at measurement time is marked "not recorded".

| | value |
|---|---|
| reference code @ commit | lm-eval `0.4.9.1`, task `ifeval` (central-run protocol `bench50-v0.3.1-fullB`, entry `T36`). The reference candidate ran the OLL v2 harness at git hash `a781a6b`, task version 2.0 (task `leaderboard_ifeval`), so this is the code the repo points to, not that file byte for byte. |
| why this code | Issue #40 and the T36 entry require lm-eval `ifeval`. The control candidate was computed by an older harness (task version 2.0, before lm-eval commit `2de3688f`, which raised `leaderboard_ifeval` to 3.0 and switched the NLTK sentence tokenizer from `punkt` to `punkt_tab`). Differences (5)-(7) in `ORIGINAL.md` (BOS, batch, task version) are the first places to check when the condition fails. |
| control model @ revision | `EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`, dtype float32, leading BOS `<\|endoftext\|>` (id 0), exactly one |
| why this model | The only candidate for which the OLL v2 run satisfies the card's point 3 in full (revision, prompt, 0-shot, metric, greedy decoding, code version). See `ORIGINAL.md`, row "Kandydat kontroli etapu B". |
| dataset @ revision, split, n | `google/IFEval` @ `966cd89545d6b6acfd7638bc708b98261ca58e84`, `train`, n = 541. (The candidate used `wis-k/instruction-following-eval`, content identical; see `ORIGINAL.md`, row "Znane rozbieżności".) |
| result (SE) | `prompt_level_strict_acc` 0.2033 (110 of 541), CI95 [0.1701, 0.2384] (paired bootstrap, 10000 reps, seed 20261028). SE A 0.017304 informational (computed here as √(p(1−p)/n)). The 0-BOS control run is reported separately under "BOS diagnostic" (its CI95 is a normal approximation, a different method). |
| reference value and source | 0.168207 = 91/541. OLL v2, run 2025-01-27, `EleutherAI/pythia-1b` @ `f73d7dcc`, float16, harness `a781a6b`, task version 2.0, dataset `wis-k/instruction-following-eval`. Per-prompt details are behind an HF gate (403), so the comparison cannot be paired. |
| difference | +0.035120, i.e. +3.51 pts. Conservative unpaired SE (upper bound: same prompts, no per-prompt reference results) √(0.017304² + 0.016082²) = 0.023623, z = 1.487, noise. |
| control tells working code from broken (column "control" of the type): b, result − b in SE, extra run if the type requires it | b = 0 (empty answer, type `ifeval`). Pythia − b = +0.2033, SE A 0.017304, z = 11.75, certain, i.e. result > b + 2 SE. Informational only: the echo-the-prompt predictor (135 of 541 = 0.249538) is above the control result (difference −0.046211 for the reference, z = −1.82 unpaired), so the b = 0 check alone does not catch a prompt-echoing bug; the ±2 SE reproduction condition below is what does. |
| reproduction condition | ±2 pts, and when 2 SE > 2 pts, within 2 SE. Reference SE 0.016082, so 2 SE = 0.032163 > 0.02. Window 0.168207 ± 0.032163 = [0.136, 0.200] (about 73.6 to 108.2 prompts of 541). Written before the run (card `ORIGINAL.md`, row "Kandydat: warunek odtworzenia"). |
| verdict | `[for reviewer]` (one of: met / not met / ...; filled by the reviewer at merge, see "Facts for the verdict sentence" below) |

## Facts for the verdict sentence (not a verdict)

- Point estimate 0.2033 = 110/541 is about 2 prompts above the window ceiling 0.200 (= 108.2 prompts). Formally the stage-B condition is **not met by a hair**. It must not be written as "met".
- The control CI95 [0.1701, 0.2384] contains the reference 0.168 and overlaps most of the window. The difference to the reference is statistically indistinguishable from noise (z = 1.487, conservative unpaired).
- `ORIGINAL.md` named BOS as suspect no. 1 in advance, should the condition fail: the candidate most likely ran without a leading BOS (`add_bos_token` defaults to `False` in HFLM), the repo run uses exactly one. The 0-BOS control run (0.1701 = 92/541, inside the window) is consistent with that suspicion, but it is a diagnostic: it does not make the stage-B condition met after the fact, because the condition concerns the 1-BOS protocol run, which stays about 2 prompts outside the window.

### BOS diagnostic (Pythia-1b, `prompt_level_strict_acc`, n = 541)

| engine | 1 BOS | 0 BOS |
|---|---:|---:|
| CUDA (lm-eval) | 0.2033 (110/541) | 0.1701 (92/541) |
| MLX | 0.2107 (114/541) | 0.1793 (97/541) |

CI95 methods differ between the CUDA arms. 1 BOS: [0.1701, 0.2384], paired bootstrap (10000 reps, seed 20261028). 0 BOS: [0.1384, 0.2017], normal approximation, not a bootstrap, so it is a different method from the 1-BOS row. The value 0.1701 appears twice by coincidence of two different quantities: the lower CI bound of the 1-BOS run and the point estimate of the 0-BOS run (92/541). Both are correct.

Paired test (McNemar, prompt_level_strict_acc, the same 541 prompts, continuity-corrected). The two engines share the same prompts and the same weights, so these are not independent replications - do not pool the p-values and do not read this as "confirmed twice".

| engine | 1 BOS | 0 BOS | discordant (helped / hurt) | net | chi2 (cc) | p |
|---|---:|---:|:---:|:---:|:---:|:---:|
| CUDA (lm-eval) | 0.2033 (110/541) | 0.1701 (92/541) | 68 (43 / 25) | +18 = +3.33 pts | 4.250 | 0.039 |
| MLX | 0.2107 (114/541) | 0.1793 (97/541) | 75 (46 / 29) | +17 = +3.14 pts | 3.413 | 0.065 |

Reading: the sign and the size agree across engines (+3.3 and +3.1 pts, BOS helps net), with the pre-fixed 3.841 threshold crossed on CUDA (p = 0.039) and just missed on MLX (p = 0.065). BOS is not one-sided: on both engines some prompts lose it (25 and 29). This is a directional diagnostic, not a confirmation. Source: CUDA per-prompt from the vast run (2026-11-19, exploratory/control; per-prompt flags in `results/pythia-1b-1bos/` and `results/pythia-1b-0bos/`), MLX from `BOS_PAIRED_TEST.md` (overnight, Mac, exploratory).

Relation to the external reference (91/541 = 0.168): the 0-BOS CUDA count (92/541 = 0.1701) is consistent with the reference count (91/541). This is agreement of two counts, not a paired test (the per-prompt reference results are behind an HF gate), and the reference also differs in float16, harness `a781a6b`, task version 2.0 and dataset repo. It does not show that the reference ran without BOS, and BOS is not shown to be the whole cause. The 1-BOS difference to the reference was already classed as noise above (z = 1.487).

## Prediction before the run

Before the run (`ORIGINAL.md`, stage A) the control Pythia-1b was expected to land in the window [0.136, 0.200]. It was also recorded in advance that, should the condition fail, the leading BOS is suspect no. 1 (the candidate most likely ran without BOS, differences 5-7). Source: `ORIGINAL.md`, rows "Kandydat: warunek odtworzenia" and "Kandydat: BOS, batch i wersja zadania".

## Reviewer sentence

`[for reviewer]`

---

Fields not recorded at measurement time: driver version and thread count of the RTX 5090 host: not recorded.

Command and environment: [`RECIPE.md`](RECIPE.md) (lm_eval 0.4.9.1, transformers 4.57.6, torch 2.8.0+cu128, RTX 5090, batch 1, `max_gen_toks` 1280, greedy, 0-shot, no chat template).
