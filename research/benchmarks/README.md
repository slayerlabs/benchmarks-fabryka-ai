# Adding a benchmark

Every new benchmark that generates answers gets one directory here, `research/benchmarks/<name>/` (lowercase,
hyphens), whatever way the models run: through the Fabryka AI API, our own vLLM server, or a local GPU. A
log-likelihood benchmark goes into the CodeSOTA runner's catalog instead
([guide](../../benchmarks/docs/contributing.md#5-writing-an-integration)). This file says what the directory contains
and the steps to get there. How each model is configured (precision, decoding, repeats, output limit, standard
errors, `null` and "not run") is in the [evaluation methodology](../../benchmarks/docs/methodology.md); it is the
same for every benchmark.

Every benchmark is different: its own harness, scorer, data, metric and traps. The steps below are the same; what
differs goes into the benchmark's own `README.md`.

## Steps

1. **Take the task** from the [board](https://github.com/orgs/slayerlabs/projects/10), assign yourself and move it to
   In Progress. The task names the models and the reference to compare with.
2. **Read the original** before writing code: the paper, the official harness and its scorer, the data, and the
   settings that produced the published scores you will compare with. Write down in your `README.md`: harness @
   commit, data @ revision, the metric, the subset (full set unless the task names one), and the reference numbers
   with their source.
3. **Choose how each model runs** and ask for what you need in **#bench-team** on
   [Discord](https://discord.gg/HnTkVR4c5T):

   | the model | runs through | machine |
   |---|---|---|
   | is on the [Fabryka AI API](https://fabryka.ai/platform) | the API | your computer |
   | is not on the API, or the API cannot apply the model's configuration | our own vLLM server (`vllm.sh`) | a rented GPU |
   | is a base model without a chat template (Slayer 1B) | its own loader on a GPU (`research/common/slayer_lm.py`, served by `research/common/slayer_serving/`) | a rented GPU |

   The benchmark needs Docker, a browser, a judge model or a user simulator: ask in #bench-team as well. Do not
   use your own GPU or paid accounts.
4. **Start from the closest existing benchmark** in this directory and copy its layout. For example `ifeval/` runs
   one harness three ways (API, vLLM, local GPU), `ifbench/` and `multi-if/` run through the API and `vllm.sh`, and
   `scicode/` scores in its own container.
5. **Write `run.sh`**: `bash run.sh <model-id>` reproduces the result from a clean checkout and pins every version;
   `bash run.sh <model-id> --limit N` runs only N items and writes outside `results/`, so a smoke test never replaces
   a published result.
6. **Smoke test**: run `--limit 5` and read the 5 items by hand (prompt, output, score). All zeros or identical
   answers mean a setup bug, not a weak model.
7. **Full run.** On a rented machine, download the outputs and check them before you destroy the instance.
8. **Write the results and the README** in the formats below.
9. **Open the PR** as [`CONTRIBUTING.md`](../../CONTRIBUTING.md#pull-requests) says, with `Refs #N` of the task. After
   the merge, the scores go to the task as a comment.

## What the directory contains

| file | content |
|---|---|
| `README.md` | sources (paper, harness repo @ commit, data @ revision), metric, the configuration of each model, a results table (model, how it runs, score, stderr, n, date), and deviations from the official setup with the reason, or "none" |
| `run.sh` | reproduces the result from a clean checkout: `bash run.sh <model-id>`; `--limit N` runs only N items |
| `results/<model-id>.json` | `benchmark`, `model`, `metric`, `score`, `stderr`, `n`, `date`, `harness`, `data`, `settings` (with what [methodology section 10](../../benchmarks/docs/methodology.md#10-what-every-result-records) asks, `dtype` included), `deviations` |
| `results/<model-id>.jsonl.gz` | one line per item: item id, score, model output; up to about 10 MB |

## Done when

- it uses the official harness and scoring at pinned versions, the same benchmark protocol for every model, and each
  model in its own configuration from the [evaluation methodology](../../benchmarks/docs/methodology.md);
- it runs the full set, or the subset named in the task;
- `score` and `stderr` are on the scale the benchmark reports (usually percent); for pass/fail items `stderr` is
  `sqrt(p * (1 - p) / n)` with `p` the pass rate, on that scale, clustered when items come in groups (several
  trials of one task, steps of one problem);
- a model that cannot run the benchmark (for example a context window that is too short) gets `score: null` and
  the reason, and the benchmark is not cut down to fit; a model not run by decision or for budget is "not run" with
  the reason, not `null`;
- the repo gets no API keys, datasets, model weights or files over 10 MB;
- the benchmark has a test without network or weights, `research/tests/test_<name>.py`, and the checks of
  [`CONTRIBUTING.md`](../../CONTRIBUTING.md#checks-before-a-pr-in-research) exit 0;
- a reviewer ran `bash run.sh <model-id> --limit 5` and the outputs look sane.
