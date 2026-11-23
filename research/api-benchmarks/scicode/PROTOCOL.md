# SciCode: measurement protocol

Written and committed before the first model output. Nothing below changes after a result is seen; anything
added later is an amendment with its time and what had been seen by then, or is marked exploratory in the README.

Refs #297. Part of the "Coding" group of the LFM3-1.7B card (LiveCodeBench v6 #295, LiveCodeBench Pro 25Q2 #296,
SciCode #297), measured together for one comparative paper.

## Question

On the LFM3-1.7B card's coding benchmarks, where does Bielik 11B v3.1, as served by the Fabryka AI API, stand
against the six models on the card, and how much of LFM3-1.7B's lead over it comes from LFM3-1.7B thinking before
it answers? LiveCodeBench v6 (#295) is the pilot that raised the question; its numbers are not used for any
verdict here. SciCode differs from the two LiveCodeBench sets: research code in Python, split into dependent
subproblems, with numerical tests.

## Sources

- Paper: Tian et al. 2024, SciCode: A Research Coding Benchmark Curated by Scientists,
  [arXiv 2407.13168](https://arxiv.org/abs/2407.13168).
- Harness: [scicode-bench/SciCode](https://github.com/scicode-bench/SciCode) @
  `e3158ea011d4235245a547460d3688d7ccbf9900`: prompts `eval/scripts/gencode.py` (`Gencode`), code extraction
  `scicode.gen.models.extract_python_script`, scorer `eval/scripts/test_generated_code.py` (subproblems over 288).
- Problems: [SciCode1/SciCode](https://huggingface.co/datasets/SciCode1/SciCode) @
  `4510f6a6aa27c43fad7b43da2c59602a86e88480`, split `test`: 65 problems, 288 scored subproblems (13.6, 62.1 and
  76.3 are supplied by the harness).
- Test targets: `test_data.h5`, 1,049,345,865 bytes, sha256
  `48b0272a88b17dbd29777c217e1b4fb2b019b92e11cc2add847409db9541b890` (the authors' Google Drive file, mirrored
  byte-identical at `xantheocracy/scicode-mirror` @ `2f903a64a1c4eb62c7c649b0caf7ecb2c0217590`).
- Reference: [LiquidAI/LFM3-1.7B](https://huggingface.co/LiquidAI/LFM3-1.7B) card: LFM3-1.7B 28.47, LFM2.5-2.6B
  16.32, MiniCPM5-2B 27.78, Gemma 4 E4B 25.00, Qwen3.5-4B 23.02, Qwen3.5-9B 31.60. Five of six are k/288, the
  subproblem rate of `test_generated_code.py`; the card does not say whether the background was given.

## Models

| model id | what | serving |
|---|---|---|
| `lfm3-1.7b` | `LiquidAI/LFM3-1.7B` @ `1da06bec6a819da10b54c67e5c90972b46d81871`, thinking on (template default) | vLLM 0.34.0, bf16, context 262144 |
| `lfm3-1.7b-nothink` | the same weights, `chat_template_kwargs: {"enable_thinking": false}` | the same server |
| `bielik-11b-v3.1` | Bielik 11B v3.1 through the Fabryka AI API (`https://fabryka.ai/v1`), with the API's hidden provider system prompt and no reasoning switch | API, context 32768 |
| `slayer1b-1.09-k70000` | not run: `null` | — |

Slayer 1B is a base model with a 4096-token context and does not follow chat instructions; on 30 Python tasks in
`research/slayer-1b/rozmowy-1.08` it wrote no function that passed its tests. Its row is `null` with that reason.

## Settings

- Two prompt settings, every model, every subproblem:
  - **primary: with background** (`eval/data/multistep_template.txt`), the setting Artificial Analysis and
    NeMo-Skills use and the one we take for the card's number;
  - **secondary: without background** (`eval/data/background_comment_template.txt`), the paper's standard setup.
- Prompts built by the harness's `Gencode` at the pinned commit, one request per subproblem in step order, each
  prompt carrying the model's own extracted code for the earlier steps, exactly as `generate_response_with_steps`
  does. Sent as the only user message: no system message of ours (LFM3-1.7B gets its template's default system
  prompt, Bielik whatever the API adds).
- LFM3-1.7B sampling, sent in every request: temperature 0.6, top_p 0.95, `top_k` 0, `repetition_penalty` 1.0,
  frequency and presence penalty 0, seed 20261122 (sent explicitly: vLLM 0.34.0 otherwise fills 1.1 and 50 from
  `generation_config.json`). `max_tokens` = 262144 minus the prompt tokens from the server's `/tokenize`.
- Bielik: temperature 0.6, top_p 0.95, seed 20261122; `max_tokens` = 32768 minus the prompt counted locally with
  Bielik's tokenizer and template (with the provider prompt) minus 64. A prompt that does not fit is `unsupported`
  for that subproblem and counts as failed, with the count reported. At most 2 requests at once, shared pause,
  every retry and error in `api-events.jsonl`.
- Code: `extract_python_script` on the text after the last `</think>`, written with `save_response_with_steps`.
  With thinking on, an answer without `</think>` or stopped by the length limit is unfinished and its (empty) code
  is what the next steps receive; the count is reported.
- Scoring: `test_generated_code.py` unchanged (1800 s per step, sequential), all models on the same isolated
  machine, after all generation has finished, BLAS threads 1, Python and package versions recorded from a lock.

## Metrics

- Headline: correct subproblems / 288 × 100 (as printed by `test_generated_code.py`), with background.
- stderr: `sqrt(p(1-p)/n)` and, because steps of one problem depend on each other, the SE clustered by problem
  (65 clusters), both reported; verdicts use the clustered one.
- Main problems solved / 65, both settings. Output tokens per answer, unfinished answers, timeouts.
- For `lfm3-1.7b-nothink`: the share of answers that still contain `<think>`.

## Control (before any claim)

**K1.** `lfm3-1.7b`, with background, lands within 2 clustered SE of its card value 28.47. If it does not, the
setup is the suspect: no hypothesis below is read until the gap is explained in an amendment. The run without <!-- ocena-bez-se: pre-registered rule, not a result -->
background is not a second chance at the control: it is reported next to it whatever it shows.

## Hypotheses

Verdicts from z: |z| ≥ 3 clear, 2–3 likely, < 2 noise (undetermined). One-sided p from z, Holm over the four
hypotheses of the Coding group (K2 and K3 here and in LiveCodeBench Pro 25Q2 #296); the verdict uses the
Holm-adjusted p with the thresholds of z = 2 and z = 3. Both on the primary setting (with background).

- **K2.** Bielik 11B v3.1 (API) scores below the weakest model on the card, 16.32.
  z = (p_Bielik − 0.1632) / SE, SE = max(clustered SE of p_Bielik, sqrt(0.1632 · 0.8368 / 288)).
  Supported when z ≤ −2; refuted when z ≥ 2; otherwise undetermined.
- **K3.** Turning thinking off takes away at least half of LFM3-1.7B's lead over Bielik:
  D = (off − B) − ½ (on − B) < 0. Paired by subproblem: d_i = off_i − ½ on_i − ½ B_i, D = mean(d), SE clustered
  by problem. Supported when z ≤ −2; refuted when z ≥ 2; otherwise undetermined. Read only if the lead itself is
  clear (on − B > 0 with paired clustered z ≥ 3); otherwise "precondition not met".

## Limits stated in advance

- SciCode problems and test targets have been public since July 2024; every model here was trained later.
  Contamination cannot be ruled out.
- SciCode-Verified (arXiv 2608.04975) reports defects in most test problems, many rejecting correct solutions. We
  score the original data, as the card does; the defects lower every model, not one.
- An unparsable early step fails the later steps of the same problem; models that write less code early lose more.
- Numerical tests near `allclose` tolerances can depend on library versions and BLAS threading.
- The card does not say whether it gave the background; if the control passes only in the secondary setting, the
  report says so and the control is failed, not swapped.
- Bielik through the API differs from Bielik on vLLM (provider prompt, unknown serving); the row describes the API.

## Amendment 1 (2026-11-22, 16:55 UTC)

Written after the Bielik smoke (`--limit 2`: problems 77 and 11, 24 steps per setting) and before any other model
output of this benchmark. Seen so far: those 48 Bielik answers and their scores (0 of 24 steps with background,
1 of 24 without). Nothing above is changed.

- **Finding.** 41 of the 48 answers begin with code without an opening ```` ```python ```` line, and 17 close a
  fence they never opened. SciCode's `extract_python_script` then takes the prose after the closing fence, so the
  step's file fails with a SyntaxError and so does every later step of the problem. The same pattern is in 54 of
  1055 Bielik answers of livecodebench-v6. Whether the API or the model drops the opening fence is not known.
- **What stays.** Every headline number, K1, K2 and K3 use SciCode's official extraction, as the card's numbers do.
- **Added, secondary, for every model and both settings: extraction E1.** For each answer (the text after the
  last `</think>` when thinking is on): if it holds a ```` ```python ```` block, or at least two fence lines, E1
  gives what the official extraction gives; if it holds exactly one fence line, E1 takes the text before that line;
  with no fence line, the whole text (as the official one). The same import-line removal follows. Prompts are not
  regenerated: the generation chain used the official extraction, and E1 only rebuilds the scored step files
  (dependencies, earlier steps' E1 code, this step's E1 code) and scores them with the same scorer.
- **Reported next to K2, not instead of it:** K2's z under E1. If K2's verdict differs between the official
  extraction and E1, the report says that K2 depends on code extraction and does not state the official verdict
  alone.

## Amendment 2 (2026-11-23, after the results)

Written after all three runs had been scored (final `--score` at `3b731440`, 2026-11-22 21:10 to 23:51 UTC) and
their results seen: K1 passed, K2 supported, K3 refuted, the same under E1 for K2. Nothing above changes: no
hypothesis, metric, threshold or control is altered, and no verdict is re-computed differently. The numbers below are
in README.md (generated from `results/`) and in `results/scoring-events.json`.

1. **Correction to "Settings".** LFM3-1.7B's chat template at `1da06bec` has no default system prompt (its system
   block is rendered only when a request sends one; LiveCodeBench Pro 25Q2, Amendment 1, for the same template), so
   LFM3-1.7B's prompts had no system block; "gets its template's default system prompt" reads "gets none".
2. **What the K3 switch does.** With `enable_thinking: false` the template ends the prompt with an empty
   `<think></think>`; LFM3-1.7B then still writes reasoning and closes it with its own `</think>` in about half of
   its answers (none of them contains `<think>`, which is what "Metrics" asked to count). K3 is reported as written,
   under the pre-registered switch; it was not checked before the run whether the switch removes thinking, so how
   much of LFM3-1.7B's lead over Bielik the thinking itself buys is undetermined by K3.
3. **Scoring conditions not written above.** (a) The three models were scored side by side, in three containers on
   the one VM (from 18:31 UTC), not one after another; the queue log with the load average is in
   `results/scoring-vm/`. (b) The scoring container has a 48 GB memory limit (run.sh), which the official scorer does
   not; the kernel's OOM killer ended a test script three times, and a killed step counts as failed, as the scorer
   grades it. Two kills are Bielik's step 53.4 without background in the final official and E1 passes; the first
   (20:09:46 UTC) was in Bielik's first scoring, whose without-background logs were later removed (neither LFM3 run
   wrote a verdict between 20:09:30 and 20:10:10 UTC; which step it killed is not recorded). (c) The VM's disk was
   full for about a minute around 20:12 to 20:17 UTC while another job copied data; Bielik's official
   without-background pass, running then, was scored again from scratch, and the official LFM3 verdicts written
   between 20:10 and 20:20 UTC, and the two LFM3 time-outs that ran through that window, were scored again
   afterwards with the same image and compared. (d) The E1 pass gives a step the official verdict without a scorer
   run when its E1 file is byte-identical to the official one (`d83c7b17`); for both LFM3 runs every E1 file was.
4. **Analyses added after the results, all descriptive; no verdict reads them:** answers closing `</think>`, the
   share of characters before it and the passed steps among them (raw_outputs.py), the causes of empty extractions,
   exact 95% intervals where a count is 0, and the without-background forms of K1 to K3 (readme.py).

Added in the first verification round (2026-11-23), nothing above changed:

5. **Correction to Amendment 1's header.** Amendment 1 was written and committed at 16:50:30 UTC (`e65c9c27`), not
   16:55 UTC; its text is left as committed.
6. **A deviation from the reference not named in "Settings".** SciCode @ `e3158ea0` hands the whole answer to
   `extract_python_script` (gencode.py knows no `</think>`); "Settings" cuts after the last `</think>` for every
   model, also for Bielik, which has no thinking. Its effect on Bielik was measured by re-scoring the step files that
   differ (reference_extraction.py; README, Deviations); for the LFM3-1.7B runs the reference extraction would read
   the reasoning, and its effect there is not measured.
7. **More descriptive checks, no verdict reads them:** the group Holm with Student's t (df 64) for K2 and K3, and
   K1 next to the reporting rules' ±2 pt reproduction check (README, Hypotheses); the disk-full window re-scoring of
   3 (c) re-run with its inputs checked (window_rescore.py); K3's robustness to leaving out the problems that
   contribute most, a jackknife and a cluster bootstrap over problems and a sign test (hypotheses.py); K3 with
   nothink's passes from answers that still close `</think>` counted as failed (explore.py, exploratory); and step
   14.2 of nothink, whose test is not deterministic, scored again 10 times in each setting (vm_repeat.sh).

Added after review (2026-11-24), no verdict rule changed:

8. **Slayer 1B's `null` is a cost decision.** "Models" gives the facts it rests on; the reason in its result file now
   says so in the words used across the Coding group: not run because Slayer 1B wrote no passing function on the 30
   Python tasks of `research/slayer-1b/rozmowy-1.08` (PAPER.md, H5.1), not because it cannot run the steps.
9. **Holm over the Coding group without a copy of the other benchmark's file.** The committed `hypotheses.json` is
   computed without `--group`, so LiveCodeBench Pro 25Q2's K2 and K3 enter with p = 1, as "Hypotheses" and
   hypotheses.py already allow when that file is not given; the group Holm over both benchmarks is computed once,
   from both merged files on main.

## Amendment 3 (2026-11-24): Slayer 1B run added

Written after the review that added Amendment 2 points 8-9 (the cost decision recorded a `null` Slayer row). The run
was carried out after that cost decision and confirms it: the measured result is 0.00. Nothing above changes: no
hypothesis, metric, threshold, control, existing K result or Holm correction is altered. Original protocol text for
this amendment was written in commit `07ee0f2aad4dec937b91388d0a8ea29aa2ccdf21` (2026-11-23T18:02:59+01:00), before
any Slayer output; this version updates it with the run outcome and keeps the pre-registered settings.

- **Model:** `slayer1b-1.09-k70000`, checkpoint `SlayerLab/Slayer1B-1.09-checkpoints` @
  `adfaf3fd5402bc7f3adbfe077798f20262979433`, file `wagi_70000.pt` (same source as PR #334), converted with the
  1.08 template `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`. Loader:
  `research/common/slayer_lm.py` (reuses `slayer_model.Slayer`), bf16, greedy (the only decoding
  `SlayerLM.generate` supports), context 4096.
- **Prompt:** the same official prompt text the harness builds for the other models, in both settings (with and
  without background), passed as plain text without a chat template (base model, no chat template). No system
  message; the only addition is raw plain-text prompting as in the IFEval Slayer run. Any other prompt addition is
  a deviation recorded in README.
- **BOS / token counting:** exactly one leading BOS per request, matching `research/api-benchmarks/ifeval/lm_eval_slayer.py` and `research/common/slayer_lm.py` (`SlayerLM.tok_batch_encode`). Prompt token counts and generation both include this BOS. Tokenizer: Slayer v6 (32768 vocab) from `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`, `tokenizer.json` sha256 `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`.
- **Context / output length:** `max_new_tokens = 4096 - prompt_tokens` where `prompt_tokens` includes BOS. An item whose prompt
  alone does not leave at least 256 tokens for the answer is not truncated: it gets an empty answer, which the
  official scorer grades as a failure, and is counted in README as `context_overflow` (number and IDs per setting).
  The headline score stays on the full benchmark (all 288 subproblems, same n as the other models). A second
  number "on items that fit" is reported only in an exploratory section. If more than 50% of items overflow in a
  setting, that setting is reported as `score: null` with the reason and the counts instead.
- **Reading:** the Slayer row is **descriptive**, outside the K1?K3 hypothesis family and the Holm correction. It
  must not change any existing K result. The measured 0.00 confirms the cost decision recorded in Amendment 2 point 8;
  the merge decision belongs to the maintainer.

