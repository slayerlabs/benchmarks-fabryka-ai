# BLiMP full set: thresholds written BEFORE the measurement

Written 2026-10-31, before any BLiMP log-likelihood of Slayer 1.06 or Pythia-1B was computed on this
machine. Committed in the same branch before the results commit. Thresholds are not changed after
the results are seen.

## What is measured

- BLiMP (`nyu-mll/blimp` @ `877fba0801ffb7cbd8c39c1ff314a46f053f6036`), all 67 paradigms x 1000
  minimal pairs = 67 000 pairs, split `train` (the only split).
- Scoring as lm-eval `blimp` at commit `6d2abda4` (`lm_eval/tasks/blimp/_template_yaml`): empty
  context, choices `[sentence_good, sentence_bad]`, default target delimiter `" "`, metric `acc`.
  So each sentence is scored as the summed log-probability of `" " + sentence` after exactly one
  unscored BOS/EOT token; a pair is correct when the good sentence gets the higher sum
  (a tie counts as correct, as lm-eval's argmax picks the first choice).
- float32, no truncation (sentences are far shorter than the context).
- Models: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` (forward from
  `common/slayer_model.py`), `EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`
  (transformers).

## Reported for every model

- Overall accuracy (mean over 67 paradigms with equal weights = mean over 67 000 pairs, since every
  paradigm has 1000 pairs), n, SE (stratified by paradigm), CI95 (bootstrap, 10 000 replicates,
  seed 20261028, resampling pairs within each paradigm).
- Per paradigm (67): accuracy, n = 1000, SE, Wilson CI95.
- Per phenomenon (12 groups of the BLiMP paper; the Hugging Face `linguistics_term` value
  `s-selection` is folded into `argument_structure`, as in Warstadt et al. 2020, Table 4).
- Reference values: chance = 0.5. A majority baseline does not apply: the gold label is always the
  first choice by construction and the model scores each sentence without seeing the other, so
  "always the majority class" would be 1.0 and measures nothing. It is reported as not applicable.

## Comparison Slayer 1.06 vs Pythia-1B

- Difference d = acc(Slayer) - acc(Pythia) on the same pairs. SE(d) is paired: per pair
  c_S - c_P in {-1, 0, 1}, SE = sd / sqrt(n) per paradigm; stratified over paradigms for the
  overall value and the phenomena.
- z = d / SE(d). Verdict: |z| >= 3 "certain", 2 <= |z| < 3 "probable", |z| < 2 "noise".
- 67 paradigm comparisons are made. Under no true difference, about 3 of them are expected at
  |z| >= 2 and about 0.2 at |z| >= 3 by chance alone, so single "probable" paradigms are not read
  as findings; "certain" ones are.

## Control: Pythia-1B against a published value

- Passes when our Pythia-1B overall accuracy is within +-2 points (0.02) of the reference.
- Reference: the only published BLiMP number found for a 1B Pythia is the EleutherAI/pythia repo
  file `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`
  (mean of the 67 `blimp_*` acc values). It is for the v0 weights (before the Pythia re-train) and
  the old harness, which scores the sentence WITHOUT the leading space. The v1 eval folders of that
  repo have no BLiMP. So this is a sanity range, not an exact reference: a miss beyond 2 points is
  reported as "control not confirmed", together with the two known differences.

## Agreement with the Space (panel of 200 documents)

- The Space T01 value for Slayer 1.06 is 0.8407960199 on n = 200 (`acc,none`, members weighted
  equally: 66 paradigms with 3 pairs and 1 with 2 pairs give 338/402).
- We rebuild the panel with METHOD.md section 3 (SHA-256 of `20261028|blimp|<member task>|<source id>`,
  2 per member, then the remaining 66 slots by largest deficit, ties by member task name) for the
  candidate source-id definitions (`pair_id`, SHA-256 of the canonical document) and check which
  one reproduces the Space `source_id_digest`.
- If the panel is reproduced: our value must equal the Space value up to one flipped pair (one pair
  moves the value by 1/201 in a 3-pair member, 1/134 in the 2-pair member). If not reproduced: our value on our panel must lie inside
  the Space CI95 (0.806-0.876), and the difference is reported as "panel not identical".
