# Methodology

How to run a benchmark on our models, which files to add and in what format. The goal of every benchmark task is
the score of each model on one benchmark, measured so that anyone can rerun it later and get the same number.

**Everything in this repo is written in English:** documents, code, comments, issues, PRs and commit messages.

## What we measure

We fill in the benchmark table from the [LFM3-1.7B model card](https://huggingface.co/LiquidAI/LFM3-1.7B) for our
models: Slayer 1B and Bielik 11B v3.1. The card lists the benchmarks and, under "Evaluation details", the settings
they were run with (agent, turn limit, tokens per turn, temperature, trials). Use the same settings, so our numbers
are comparable with the card.

## Where to run

- **Models only through the Fabryka AI API:** [fabryka.ai/platform](https://fabryka.ai/platform). Base URL
  `https://fabryka.ai/v1`, OpenAI-compatible (chat completions, streaming, tool calling), so any harness that
  supports an OpenAI-compatible provider works. Create a free account, put the key in `FABRYKA_API_KEY` and never
  commit it. Model IDs are listed at `https://fabryka.ai/v1/models`.
- **Do not use your own GPU or paid accounts.** If the benchmark needs a CPU machine (Docker sandboxes, a browser
  environment, a lot of RAM or disk) or another API (judge model, user simulator, search), write in **#bench-team**
  on [Discord](https://discord.gg/HnTkVR4c5T) and we will give you access to a rented machine or a key.
- **API problems first.** A model missing from `/v1/models`, an API error, a missing feature or a context window
  too short for the benchmark: write in #bench-team right away. Fixing the API has priority.

## How to run

1. **Official harness.** Use the benchmark authors' code at a pinned commit and their data at a pinned revision. Do
   not rewrite the scoring. If you have to change something to make it run, write it under "Deviations".
2. **Same settings for both models**, taken from the LFM3-1.7B card. Main metric: the one the card reports.
3. **Smoke test.** Run about 5 tasks first and read the prompts, model outputs and scores by hand. A score that
   looks wrong (everything 0, every answer the same, a broken tool call format) is usually a setup bug, not a weak
   model. Fix it before the full run.
4. **Full run** on the full set, or on the subset the card names (for example "OpenClaw subset", "public").
5. **When a model cannot run the benchmark** (for example its context window is shorter than the benchmark needs),
   the score is `null` and the reason goes to "Deviations". Do not shorten the benchmark to make it fit.

## Files

One directory per benchmark: `research/api-benchmarks/<name>/`, lowercase with hyphens (`bfcl-v4`, `tau3-bench`).

| file | what it holds |
|---|---|
| `README.md` | the benchmark, its sources, settings, results and deviations (template below) |
| `run.sh` | one command that reproduces the results from a clean checkout: installs the harness at the pinned commit and runs one model, `bash run.sh <model-id>`; `--limit N` runs only N tasks |
| `results/<model-id>.json` | the summary result of one model (format below) |
| `results/<model-id>.jsonl.gz` | one line per task: task id, its score and the model output or trajectory; up to about 10 MB |

Never commit API keys, datasets, model weights or any file over 10 MB.

### `README.md`

````markdown
# <Benchmark name>

<What it measures, one sentence.>

- Paper: <link>
- Harness: <repo link> @ <commit>
- Data: <dataset link> @ <revision>, <n> tasks (<subset>)
- Metric: <main metric, as on the LFM3-1.7B card>
- Settings: <agent, temperature, max tokens per turn, max turns, trials>
- Extra services: <judge model, user simulator, sandbox> or none

## Results

| model | score | stderr | n | date |
|---|---|---|---|---|
| Slayer 1B (`<model-id>`) | | | | |
| Bielik 11B v3.1 (`bielik-11b-v3.1`) | | | | |

## Deviations

<Everything that differs from the official setup or the LFM3-1.7B settings, with the reason. "None" if nothing.>

## Reproduce

```bash
export FABRYKA_API_KEY=...
bash run.sh <model-id>
```
````

### `results/<model-id>.json`

```json
{
  "benchmark": "BFCL V4",
  "model": "bielik-11b-v3.1",
  "metric": "overall accuracy",
  "score": 0.0,
  "stderr": 0.0,
  "n": 0,
  "date": "YYYY-MM-DD",
  "harness": "<repo link> @ <commit>",
  "data": "<dataset link> @ <revision>",
  "settings": {"temperature": 0, "max_tokens_per_turn": 0, "max_turns": 0, "trials": 1},
  "deviations": "none"
}
```

- `score`: on the same scale as the LFM3-1.7B card (most benchmarks: percent, 0–100); `null` when the model cannot
  run the benchmark.
- `stderr`: standard error of the score, from the harness or, for pass/fail tasks, `100 * sqrt(p * (1 - p) / n)`
  with `p` the pass rate; `null` when it cannot be computed (say why in `deviations`).
- `n`: number of tasks scored.

## Done

1. Take an issue, assign yourself and move it to In Progress on the
   [board](https://github.com/orgs/slayerlabs/projects/10).
2. Branch `research/<name>` from `main`, open a draft PR with `Refs #N`.
3. When both models have results, mark the PR ready for review and move the issue to Review.
4. The reviewer reads the README, runs `bash run.sh <model-id> --limit 5` and checks that the outputs look sane and
   the files follow this page. Then merges and moves the issue to Done.
5. Post the scores of both models as a comment on the issue.

Benchmarks in `research/benchmarks/` (the earlier lm-eval run on base models) keep their rules in
[METODOLOGIA.md](METODOLOGIA.md).
