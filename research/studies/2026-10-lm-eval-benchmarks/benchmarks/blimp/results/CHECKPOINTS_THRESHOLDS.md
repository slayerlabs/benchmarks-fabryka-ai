# BLiMP over training checkpoints and weight averaging: protocol written BEFORE the measurement

> Moved unchanged from the old layout (`research/slayer-1b/wyniki/blimp/`); only this note and the link to
> `THRESHOLDS.md` are new. Paths in the text are those of the old layout: `slayer_eval/` is now `common/` or
> `benchmarks/blimp/`, `wyniki/blimp/raw/<model>.jsonl.gz` is `results/<model>/blimp.jsonl.gz`,
> `wygaszanie/` is `slayer-1b/wygaszanie/` (full map in [`../RECIPE.md`](../RECIPE.md)).

Written 2026-10-31 (task #52, fabryka-ai), before any BLiMP log-likelihood or held-out loss of the
checkpoints or averaged models below was computed. Committed before the first raw result; the
thresholds are not changed after the results are seen. The scoring method is the one of
[`THRESHOLDS.md`](../THRESHOLDS.md) (Slayer 1.06 vs Pythia-1B), unchanged.

## Scoring (same as THRESHOLDS.md)

- BLiMP `nyu-mll/blimp` @ `877fba0801ffb7cbd8c39c1ff314a46f053f6036`, all 67 paradigms x 1000 pairs
  = 67 000 pairs. Each sentence scored as the summed log-probability of `" " + sentence` after one
  unscored BOS `<|endoftext|>` (`slayer_eval/hipoteza_formatu.py licz --zadania blimp`, forward
  `slayer_eval/slayer_model.py`). A pair is correct when the good sentence has the higher sum; a
  tie and the 7 pairs with identical sentences count as correct (`blimp.trafienie_pary`).
- float32, TF32 matmul off, batch 64 with right padding (as the 1.06 run), CUDA GPU on vast.ai.
- Pythia-1B per-pair results are the existing `wyniki/blimp/raw/pythia-1b.jsonl.gz` (not re-scored).

## Models

Checkpoints are the trainer files `ckpt_<step>.pt` of the HF repos `SlayerLab/Slayer1B-1.0x-checkpoints`
(revision = repo head at download time, written to the run log with the SHA-256 of every file),
converted to model weights by `wygaszanie/konwertuj.py` (keys and shapes from Slayer 1.06 weights,
fp32). Tokens seen D = step x 2^20 (batch 256 x block 4096), in billions (bn).

| point | repo | step | D (bn tokens) |
|---|---|---:|---:|
| end of 1.00 | 1.00-checkpoints | 1430 | 1.50 |
| end of 1.01 | 1.01-checkpoints | 2860 | 3.00 |
| end of 1.02 | 1.02-checkpoints | 5720 | 6.00 |
| end of 1.03 | 1.03-checkpoints | 7150 | 7.50 |
| intermediate | 1.04-checkpoints | 8600 | 9.02 |
| 1.04 | 1.04-checkpoints | 10010 | 10.50 |
| intermediate | 1.04-checkpoints | 11450 | 12.01 |
| 1.05 | 1.05-checkpoints | 12870 | 13.50 |
| 1.06 | 1.06-checkpoints | 13848 | 14.52 |

Lineage (from the LFS object ids in the HF listings, before the measurement): steps 10050-13848 are
the same files in the 1.04, 1.05 and 1.06 repos, so 7150 (assumed) and 8600-13848 are one run. The
1.00/1.01 overlap (1200, 1350) and the 1.01/1.02 overlap (2400-2850) are DIFFERENT files: 1.01
restarted from an earlier 1.00 point and 1.02 from an earlier 1.01 point, so 1430 and 2860 are ends
of side branches, not points of the final run. They are shown on the curve and excluded from the
primary slope.

Controls (stop and report, no measurement of the rest, when one fails):
- `ckpt_13848.pt` converted must equal the published 1.06 weights (`SlayerLab/Slayer1B-1.06` @
  `ef81be58742544ad32e1afab38db011fec209609`): max |difference| = 0.
- Device: 1.06 re-scored on CUDA vs the existing MPS raw file `wyniki/blimp/raw/1.06.jsonl.gz`:
  at most 30 of 67 000 pairs may change outcome (the MPS run had 11 pairs closer than 1e-3), else
  the CUDA run is not comparable with Pythia's MPS file and the gap is reported as not determined.
  All checkpoint numbers use the CUDA run of each model, the 1.06 point included.

Weight averages (question 2): uniform mean, in float64, of the converted model weights of the last
K trainer checkpoints of the 1.06 run, cast to float32. Constant LR 6e-4 over this window.

| model | K | steps |
|---|---:|---|
| avg3 | 3 | 13750, 13800, 13848 |
| avg5 | 5 | 13650, 13700, 13750, 13800, 13848 |
| avg10 | 10 | 13400, 13450, ..., 13800, 13848 |

## Reported for every model

Overall accuracy with n = 67 000, SE stratified by paradigm and bootstrap CI95 (as THRESHOLDS.md);
per phenomenon (12) and per paradigm (67) accuracy, n, SE, CI95; chance 0.5 (a majority baseline does
not apply, see THRESHOLDS.md).

## Question 1: the curve

1. **Primary slope.** OLS of overall accuracy on D (bn tokens) over the six points of the final run
   (7150, 8600, 10010, 11450, 12870, 13848). Two SEs, both reported:
   - pairs: bootstrap over pairs within paradigms, the same resampled pairs for all six checkpoints
     (2000 replicates, seed 20261028); z = slope / SE, verdict |z| >= 3 certain, 2-3 probable, < 2 noise;
   - paradigms (clustered): the slope computed per paradigm, SE over the 67 paradigm slopes,
     t = mean / SE, df = 66, verdict from the p of the t distribution with the p thresholds of
     |z| = 3 (certain) and |z| = 2 (probable).
   The slope of the gap to Pythia equals this slope (Pythia is fixed), so **"the gap to Pythia
   shrinks" is CONFIRMED when the primary slope is > 0 with verdict "certain" or "probable" in BOTH
   SEs; REFUTED ("no detectable shrinking") when the pair-level CI95 of the slope contains 0 or is
   below 0.** Anything else: "not determined".
2. **Gap per checkpoint.** acc(checkpoint) - acc(Pythia-1B) on the same pairs, paired SE (as
   THRESHOLDS.md), z and verdict, for all nine points.
3. **Step-to-step changes.** Adjacent points of the final run and 7150 -> 13848: paired difference,
   SE, z, verdict (pairs), plus the paradigm-clustered t verdict.
4. **Phenomena.** Primary slope per phenomenon (12), pair-level bootstrap SE and z (verdict by the
   |z| thresholds), paradigm-clustered t with df = k - 1 (k < 3: undetermined), Holm correction over
   the 12 phenomena on the pair-level p. "Phenomenon X grows" only when its slope is > 0, certain or
   probable after Holm on pairs AND not "noise" in the clustered verdict.
5. **Whole curve (descriptive).** OLS of accuracy on ln D over all nine points, with the same two SEs;
   no verdict on lineage (side branches included), reported as context only.
6. **Projection (only if the primary slope is "certain" in both SEs):** bn tokens to close the gap
   at 13848 at the primary slope, with a CI from the pair bootstrap. Marked as a linear extrapolation.

## Question 2: weight averaging vs 1.06

For each of avg3, avg5, avg10 against 1.06 (CUDA run):

- BLiMP: paired difference on the 67 000 pairs, SE, z and verdict (pairs) plus clustered t over
  paradigms (df = 66); per phenomenon (pairs, with Holm over 12 x 3).
- Held-out loss (nat/token) with `wygaszanie/heldout.py` on the held-out windows of the annealing
  run (`wygaszanie/dane.py`, same arguments as there; `val.bin` must have SHA-256
  `86ebed396365110cfce1305d0647dbc0122031239af13e17c08ef62ba173b2d3`, else the comparison with the
  annealing numbers is reported as "different held-out set"). Control: our 1.06 loss must reproduce
  the annealing run's 2.33104 within 0.0005 nat.
  Paired difference per window, SE = sd / sqrt(n windows), z, verdict, and BPB alongside.
- **Averaging helps the loss** when Δ = L(avgK) - L(1.06) <= -0.01 nat with |z| >= 3. Compared with
  annealing (annealed arm − 1.06 = -0.0504 nat, annealed − constant-LR arm = -0.047 nat, same windows):
  share = Δ / (-0.0504). **"Averaging is a substitute for annealing" is CONFIRMED when the share is
  >= 0.5 (Δ <= -0.0252) with |z| >= 3 for at least one K; REFUTED when every K has Δ > -0.0252 or
  |z| < 3.**
- BLiMP: no expected change; any certain difference is reported, none is the claim.

## Amendment 1 (scope cut, 2026-10-31 ~14:00 UTC, before any accuracy of a curve point or average was read)

Decision of the task owner (time and cost; the dashboard already shows the BLiMP trend): the curve uses
only the checkpoints whose BLiMP run had finished at that moment, and K = 10 is not measured unless K = 3/5
shows an effect. Thresholds are unchanged; what changes is the set of points:

- Curve points measured: 1430, 2860, 7150, 8600, 10010, 13848. Not measured: 5720, 11450, 12870. 5720 and
  11450 had been downloaded and their BLiMP runs were stopped part-way (35 840 and 18 240 of 67 000 pairs
  by the instance logs, 53.5% and 27.2%);
  12870 was not downloaded.
- **Primary slope: OLS over 7150, 8600, 10010, 13848 (four points of the final run)** with the same two
  SEs and the same verdict rule. Fewer points widen the SE; the rule is not relaxed for that.
- Averages: avg3 and avg5 (BLiMP and held-out). avg10: not measured. Held-out: Slayer 1.06, avg3, avg5.
- The only numbers seen before this amendment: run times, download speeds, SHA checks, the conversion
  check (max |difference| 0) and the device control of 1.06 (CUDA vs MPS, 0 changed pairs).

## Amendment 2 (avg10, decision at 2026-10-31 14:10 UTC; written down after the results, at verification)

- avg10 was built and measured under the condition of amendment 1 ("K = 3/5 shows an effect"). The decision
  was taken at 14:10 UTC (session log), after the BLiMP results of avg3 and avg5 against Slayer 1.06 had been
  read (both certain on pairs) and before any held-out loss was computed (avg3 held-out at 14:25 UTC).
- The question 2 verdict rests on avg3 and avg5, the averages kept by amendment 1; avg10 is reported beside it
  with the same thresholds.
- The wording of amendment 1 was corrected at verification: "already downloaded" read "whose BLiMP run had
  finished". The set of points is unchanged.
- Added at verification, as robustness checks of question 1 and not as rules: the slope without the last
  point, an SE from the residuals of the checkpoint accuracies around the line (df = points - 2), all pairs of
  final-run points, and the paradigms that carry the largest change. A failed or missing control turns a
  verdict into "not determined".

## GPU comparison (operations, not a model measurement)

The same job on each rented GPU type: download the 1.06 weights and BLiMP data, download
`ckpt_13848.pt`, convert, full BLiMP (67 000 pairs) on the converted model, download `ckpt_13800.pt`
and `ckpt_13750.pt`, build avg3, full BLiMP on avg3. Recorded: offer price ($/h), billed cost from
`vastai`, time from create to SSH ready, HF download speed per file, conversion time, averaging time,
BLiMP time, peak GPU memory at batch 64, GPU and CPU utilisation sampled during BLiMP. The BLiMP
results of the same model on different GPUs must change at most 30 pair outcomes (else device noise
is larger than assumed and it is reported).
