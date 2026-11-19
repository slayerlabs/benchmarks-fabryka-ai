# Contributing to CodeSOTA

Which guide applies depends on where your change goes:

| You are changing | Follow |
|---|---|
| `benchmarks/`: the `codesota` package, its tests and docs | this guide and [`../AGENTS.md`](../AGENTS.md) |
| `research/`: existing benchmarks, results, research code | the root [`CONTRIBUTING.md`](../../CONTRIBUTING.md) and [`research/METHODOLOGY.md`](../../research/METHODOLOGY.md) |

If your change touches both, follow both. The `codesota` package does not run evaluations yet (see
[Getting started](../README.md#getting-started)), so most useful contributions to it right now are small: improving
the package foundation and these documents, or proposing its first evaluation integration through an issue.

## 1. Fork, clone, and set up

You do not need access to any private infrastructure, chat, or credentials to contribute.

```bash
# Fork slayerlabs/benchmarks-fabryka-ai on GitHub, then:
git clone https://github.com/<your-account>/benchmarks-fabryka-ai.git
cd benchmarks-fabryka-ai/benchmarks
uv sync --locked
```

Install [uv](https://docs.astral.sh/uv/) first if you do not have it. `uv sync --locked` creates `.venv` from
`uv.lock` and fails if the lock file and `pyproject.toml` disagree.

## 2. Run the checks

```bash
uv run pytest
uv run ruff format --check
uv run ruff check
uv run mypy
uv build
```

All five must pass before you open a pull request. They need no network access after `uv sync`, no GPU, and no keys.

## 3. Choose a task

- Pick an open issue, or open one describing the problem with evidence (a reproduction, a failing test, or a
  reference). For new functionality, open the issue first and wait for a maintainer to agree on scope before
  writing code: unrequested features are likely to be declined however good they are.
- Search open pull requests for the same work before starting.
- Say on the issue that you are working on it.

## 4. Identify the official benchmark sources

Before integrating or changing an evaluation, record:

- the paper or official specification that defines the benchmark;
- the official implementation and scorer, at a pinned commit;
- the dataset, at a pinned revision, and its license and access terms;
- a published reference result with the exact settings that produced it (model and revision, prompt format,
  number of examples, decoding settings), if one exists.

Prefer primary sources. If a source is inaccessible, say so; do not reconstruct it from memory.

## 5. Writing an integration

The `codesota` package has no evaluation integrations yet, so there is no template to copy. The first integration
will define the layout, and is expected to:

- run through the official implementation and scorer where one exists, pinned;
- record failures as failures: an infrastructure error, a timeout of our own machinery, or a model that cannot run the
  benchmark is an explicit state, not a score of zero;
- write machine-readable results that reuse the existing results contract described in
  [`research/common/README.md`](../../research/common/README.md) where it fits, and say where it deviates;
- come with deterministic tests that need no network, GPU, weights, or keys (fixed inputs and expected scores).

Propose the layout in the issue before building it.

## 6. Prepare reproducible evidence

A pull request that adds or changes an evaluation shows:

- the exact command(s) used, from a clean checkout;
- versions: harness commit, dataset revision, model revision, package versions;
- a reproduction of a published reference result within a tolerance stated before the run, or an explanation of
  why none exists;
- a manual read of a handful of samples (prompt, raw output, extracted answer, score); all zeros or identical
  answers usually mean a setup bug;
- every deviation from the official protocol, with the reason.

## 7. Open the pull request

- **Title:** [Conventional Commits](https://www.conventionalcommits.org/) in English, for example
  `feat(benchmarks): add GPQA Diamond integration` or `docs: fix setup command`.
- **Description:** fill in every section of the [pull request template](../../.github/pull_request_template.md).
  A trivial documentation fix (a `docs:` title and the "Documentation only" scope box ticked) needs only Problem,
  Result, Scope, and Related issue.
  The `PR policy` check verifies the structure (not the quality) of the description.
- **Issue reference:** `Refs #123` links an issue without closing it. Many issues here are closed through the project
  board, so use `Closes #123` only when merging the PR should close the issue. With no issue, write
  `No issue: <reason>`.
- **Agent-prepared PRs** are opened as drafts and marked ready only after the responsible person has reviewed them.

## 8. What reviewers verify

- The problem is real and the PR solves it; nothing unrelated is bundled.
- The checks pass, and the reported validation matches what was run.
- For evaluations: sources are official and pinned, failures are not scored as zeros, deviations are named, and the
  same protocol applies to every model.
- No credentials, weights, gated data, or large files are committed.
- Documentation describes what the code does, not what it might do later.

## 9. AI-assisted contributions

AI coding tools are welcome. You must understand, and be able to explain and defend, every line you submit. Follow
[`AGENTS.md`](../AGENTS.md) and fill in the "AI assistance" section of the PR description, including any independent
review and its findings.
