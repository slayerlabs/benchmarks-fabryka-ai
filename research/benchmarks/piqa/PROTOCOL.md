# PIQA (Space T06): protocol written BEFORE the measurement

Written 2026-11-01 for issue #16, before any PIQA log-likelihood of Slayer 1.06 or Pythia-1B v0 was computed.
Committed in branch `research/piqa-slayer106` before the commit with raw results. The variant, the thresholds and
the claims below are not changed after the results are seen. Anything added after the measurement is marked
"exploratory" in the report.

Decision this result serves: T06 in the Space stops being `not_run` for Slayer 1.06 (METODOLOGIA.md, "Wyjątek: 7
testów Space do 8.11"). Already known: nothing about Slayer on PIQA; Pythia-1B v0 has a published value.

## What is measured

- Data: `ybisk/piqa` @ `2e8ac2dffd59bac8c3c6714948f4c551a0848bb0` (revision in the Space `tasks_50.json`, entry T06;
  it is also the head of `main` on 2026-11-01). The repo has a loading script, so, as METHOD.md section 8 says, the
  data are read from the auto-converted parquet: `refs/convert/parquet` @ `142c51238b3ca2bc61e9a075913871b8b600e8e1`,
  file `plain_text/validation/0000.parquet`, sha256 `40e1677bba609c8801deacc171d76f3e24c083f365c95a1cbda7520c923dfea2`,
  1838 rows, columns `goal`, `sol1`, `sol2`, `label`. No loading script is executed.
- Split `validation`, 0-shot, 2 options.
- Task: `lm_eval/tasks/piqa/piqa.yaml`. The blob differs between the Space commit `6d2abda4`
  (`1a34cc6670bffba45b9a2c3613cca7a60b37bb36`) and `v0.4.9.1` (`b147daea44b3bf3cd8f795be37dd3522f88afa3a`) only in
  `dataset_path` (`piqa` vs `baber/piqa`) and in `dataset_kwargs: trust_remote_code: true` at `6d2abda4`;
  `README.md` is the same blob (`e0d7d05d99fee62fed27374e5cf9f2daee9032b8`). Prompt `"Question: {{goal}}\nAnswer:"`,
  choices `[sol1, sol2]`, target `label`, target delimiter `" "`, metrics `acc` and `acc_norm` are identical.
  `piqa.py` passes this config to lm-eval 0.4.9.1 (lockfile `common/requirements.lock.txt`) with the parquet above
  as `dataset_path: parquet`. So `--tasks piqa` is never used: it would read `baber/piqa`.
- Settings as METHOD.md section 2: float32, batch 1, no chat template, seeds (0, 1234, 1234, 1234). Inputs are far
  below 4096 tokens. BOS: Slayer through the `slayer` wrapper of `common/slayer_lm.py` (#44), one BOS before every
  request, as in the Space. Pythia through `HFLM` with its own tokenizer convention (no BOS added), as the 2022
  harness that produced the published value.
- Models: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`;
  control `EleutherAI/pythia-1b-v0` @ `step143000`.
- Primary metric: `acc_norm` (tasks_50.json T06). Also reported, not used for any claim: `acc`, BPB of the correct
  answer, share of predictions of option 1. Letter (MC) format is not computed: the Space protocol scores PIQA as
  cloze, and the other formats belong to stages A–C (#57).

## Panel (Space sample) and full split

- Panel: `min(200, 1838)` = 200 rows, ascending SHA-256 of `20261028|piqa|piqa|<source id>` (METHOD.md section 3;
  `benchmark_id` and `task` from tasks_50.json). PIQA rows have no native id, so the source id is the SHA-256 of the
  canonical row (JSON with sorted keys, separators `,` and `:`, UTF-8, the four parquet columns). The validation
  split has no byte-identical rows (1838 distinct), so no ordinal is needed. The Space has no T06 value and no
  `source_id_digest` for any model, so the panel cannot be checked against the Space; the report gives the digest
  of our source ids.
- Full split: all 1838 rows (`fullB` in METHOD.md). Both come from one full run (batch 1, each question scored
  independently), the panel is the subset.
- Per model and part: value, n, SE (sample sd / sqrt n), CI95 by percentile bootstrap, 10 000 replicates, seed
  20261028 (METHOD.md section 5).

## Baselines

- Random: 0.5.
- Majority: share of the most frequent correct option on the same questions (full split: 928/1838 for option 2,
  counted from the parquet before any model run).
- Share of the model's most frequent prediction (constant-prediction check).

## Control (threshold fixed here)

- Published: Pythia-1B v0 step143000, acc 0.7040, acc_norm 0.7051, n 1838, from
  `EleutherAI/pythia@a19eecb807ec2c79a39ebf18108816e6ffffc1d5`,
  `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`
  (lm-eval of 2022, piqa version 0, fp16 NeoX run).
- Discriminates: 0.7051 lies far over 2 SE (SE 0.0106) above random 0.5 and majority 0.5049.
- Passes when our Pythia on the full split is within the tolerance for BOTH acc and acc_norm. Tolerance = max(2 pts,
  2 × published SE) = 2.13 pts for acc and 2.13 pts for acc_norm (2 SE > 2 pts here).
- Outside the tolerance: stop, no Slayer value goes out, the miss goes as a comment to #16.

## Claims and how they are falsified

- Verdicts: z = difference / SE; |z| ≥ 3 "pewne", 2–3 "prawdopodobne", < 2 "szum".
- C1 (main): Slayer 1.06 acc_norm on the full split is above the random baseline. Falsified if z = (value − 0.5) /
  SE < 3. Same test reported against the majority baseline, and both on the panel (panel n 200 resolves only
  differences of about 7 pts).
- C2: Slayer 1.06 minus Pythia-1B v0, acc_norm, same questions, paired SE (sd of per-question differences / sqrt n),
  on the full split and the panel. No direction is claimed in advance; the verdict is reported as it comes. A
  certain difference is not its cause: Slayer is a checkpoint at about 1/8 of its plan without LR decay, with about
  10% English in its data.
- The Space flags T06 for Slayer 1.06 as contaminated (`contamination: flagged`, receipt
  `bc6c168cf6ef35bce80b70f3bf582853526b558cb7f37e30101e35f3c2342de7`). We have no training corpus, so we cannot
  compute the hit-free value; our numbers are on the full sample and the report says so.

## GPU comparison (cost, not results)

The same Pythia full-split run on 2–3 GPU types. Recorded: price per hour before the rental, setup, download and
scoring times, cost. The main results are the run on the first GPU; the repeats only report how many acc_norm
decisions differ from it and the largest log-probability difference.
