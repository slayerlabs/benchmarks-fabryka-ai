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

## Results

| model | how it runs | score (with background) | stderr | stderr clustered | n | date |
|---|---|---|---|---|---|---|
| LFM3-1.7B (`lfm3-1.7b`) | vLLM 0.34.0, bf16, context 262144, thinking on | | | | | |
| LFM3-1.7B without thinking (`lfm3-1.7b-nothink`) | the same server, `enable_thinking: false` | | | | | |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | Fabryka AI API, context 32768, with the API's provider system prompt, no thinking | | | | | |
| Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`) | not run (PROTOCOL.md, Models) | null | | | | |

No model has been run yet. The without-background scores are in each result file under
`other_metrics.without_background`.

Setup check (not a model): the dev split's `ground_truth_code`, fed through the same Gencode files and the same
scorer (`bash run.sh dev-ground-truth`, `--split validation`), in `results/checks/dev-ground-truth.json`. Two of
its 50 steps fail with the authors' own code (78.3: the target has shape (2, 2), the reference returns
(10001, 2); 70.8: `np.allclose` false), as SciCode issue #43 reports for some dev ground truth.

## Deviations

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
python3 hypotheses.py results --group ../livecodebench-pro-25q2/results/hypotheses.json
```

`--score` writes `results/<model-id>.json` and `.jsonl.gz` (with `--limit N`: `out/<model-id>/<model-id>-limitN.*`).
Provenance as in livecodebench-v6: `out/<model-id>/run.json` holds each step's code commit, runner checksums,
machine and sampling in effect, plus for scoring the image id, `test_data.h5` sha256, the dataset revision the
scorer loaded and the package versions; `manifest.json` holds the sha256 each step wrote, which the next step
checks; `api-events.jsonl` every failed request attempt and each recovery.

Tests: `.venv-gen/bin/python -m pytest ../../tests/test_scicode.py -x -q` (no GPU, network or `test_data.h5`).
