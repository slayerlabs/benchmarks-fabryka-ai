# Methodology

How to run a benchmark so that its result can be trusted and repeated. Everything in this repo is written in
English: documents, code, comments, issues, PRs and commit messages.

## API

Models run only through the Fabryka AI API: [fabryka.ai/platform](https://fabryka.ai/platform).

- Base URL `https://fabryka.ai/v1`, OpenAI-compatible (chat completions, streaming, tool calls), so most benchmark
  harnesses connect to it as an OpenAI-compatible provider.
- The API serves several models, and the list changes. Check the current models and their context length with
  `curl https://fabryka.ai/v1/models`. Which models to run is written in the task.
- Create a free account and keep the key in `FABRYKA_API_KEY`, never in code or in the repo.

## Problems: report them right away

A model missing from the list, an API error, a missing feature (tool calls, context length) or a harness that does
not work with the API: write in **#bench-team** on [Discord](https://discord.gg/HnTkVR4c5T) right away, instead of
working around it. Fixing the API has priority.

## Machine

Do not use your own GPU or paid accounts. If the benchmark needs a machine (CPU, Docker, a browser, a lot of RAM or
disk) or another API (judge model, user simulator), write in #bench-team and you will get access to a rented one.

## What a well-done benchmark contains

A PR with the directory `research/api-benchmarks/<name>/` (lowercase, hyphens):

| file | content |
|---|---|
| `README.md` | sources (paper, harness repo @ commit, data @ revision), metric, settings, a results table (model, score, stderr, n, date) and deviations from the official setup with the reason, or "none" |
| `run.sh` | reproduces the result from a clean checkout: `bash run.sh <model-id>`; `--limit N` runs only N tasks |
| `results/<model-id>.json` | `benchmark`, `model`, `metric`, `score`, `stderr`, `n`, `date`, `harness`, `data`, `settings`, `deviations` |
| `results/<model-id>.jsonl.gz` | one line per task: task id, score, model output; up to about 10 MB |

The result counts as well done when:

- it uses the official harness and scoring at pinned versions, with the official settings (or those of the reference
  named in the task), the same for every model;
- it runs the full set, or the subset named in the task;
- before the full run you read about 5 tasks by hand (prompt, output, score); all zeros or identical answers mean a
  setup bug, not a weak model;
- `score` and `stderr` are on the scale the benchmark reports (usually percent); for pass/fail tasks `stderr` is
  `sqrt(p * (1 - p) / n)` with `p` the pass rate, on that scale;
- a model that cannot run the benchmark (for example a context window that is too short) gets `score: null` and
  the reason, and the benchmark is not cut down to fit;
- the repo gets no API keys, datasets, model weights or files over 10 MB;
- a reviewer ran `bash run.sh <model-id> --limit 5` and the outputs look sane.

The scores go to the issue as a comment after merge.

Benchmarks in `research/benchmarks/` (the earlier lm-eval run) follow [METODOLOGIA.md](METODOLOGIA.md).
