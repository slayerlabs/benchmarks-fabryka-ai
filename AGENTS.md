# AGENTS.md

Rules for coding agents and the people who supervise them. Work in `benchmarks/` (the `codesota` package) follows
[`benchmarks/AGENTS.md`](benchmarks/AGENTS.md); this file adds what is specific to `research/`.

## Where things go

- Before creating a file or directory in `research/`, read where it goes:
  [`research/README.md`, "Where things go"](research/README.md#where-things-go). A new benchmark follows
  [`research/api-benchmarks/README.md`](research/api-benchmarks/README.md); a log-likelihood benchmark goes into the
  CodeSOTA runner's catalog
  ([`benchmarks/docs/contributing.md`, "Writing an integration"](benchmarks/docs/contributing.md#5-writing-an-integration)).
- [`research/studies/2026-10-lm-eval-benchmarks/`](research/studies/2026-10-lm-eval-benchmarks/README.md) and the
  central-run scripts in `research/tools/` are the frozen lm-eval run of November 2026: change them only to fix an
  error in that run. Studies, finished or in progress, live in `research/studies/`. The number gate regenerates
  `research/results/LICZBY.*`.
- Test sample data goes in `research/common/tests/data/`.
- `research/slayer-1b/` and `frontend-beta/` are not touched in benchmark work.

## Rules

- Model configuration (precision, decoding, repeats, output limit, standard errors, `null` and "not run") follows
  [`benchmarks/docs/methodology.md`](benchmarks/docs/methodology.md) for every new measurement, in `research/`
  too. A benchmark's README names every deviation with its reason.
- Everything is written in English: documents, code, comments, issues, PRs and commit messages.
- What is never committed (weights, datasets, files over 10 MB, keys) and when `.jsonl.gz` is allowed:
  [`CONTRIBUTING.md`, "Files in the repository"](CONTRIBUTING.md#files-in-the-repository).
- Benchmark questions never go into training data.
- Before a PR in `research/`, the checks of [`CONTRIBUTING.md`](CONTRIBUTING.md#checks-before-a-pr-in-research)
  exit 0. The PR goes to `main` with `Refs #N` of the task.
- Load a checkpoint with `torch.load(..., weights_only=True)`. Other forms unpickle and can run foreign code.

## Training passes a gate before a full run

A run that is alive and writes files looks like working training even when it learns nothing. Before a full run:

1. **Tokenization:** print the tokens of 2 examples and check that Polish words split sensibly.
2. **Overfit test:** 64 examples, 100 steps. The loss must fall close to 0. If it does not, the code has a bug and
   the full run does not start.
3. **Stop rule:** the full run stops itself when the loss after 20% of the steps has not fallen by at least 10% from
   the start.

To "is training working", answer with the latest loss values (train and val) and whether they fall. "The process is
alive" is not an answer.

## Heavy processes on your own computer

- Training longer than an hour goes to a rented GPU, not a laptop.
- At most one heavy process at a time locally (training, model evaluation, weight download). Before starting, check
  `pgrep -fl python` and free memory.
- No "wait and run" chains (`while … sleep; done; python train.py`, overnight queues). The next heavy process starts
  by hand, after the check above.
