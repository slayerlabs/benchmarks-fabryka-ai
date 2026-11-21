<div align="center">

# CodeSOTA

**Reproducible evaluation for language models and AI agents.**

[![CodeSOTA CI](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/codesota.yml/badge.svg?branch=main)](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/codesota.yml)
[![Research tests](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/research-tests.yml/badge.svg?branch=main)](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/research-tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

[Overview](#overview) · [Run](#run) · [Evaluations](#evaluation-domains) · [Methodology](#methodology-and-reproducibility) ·
[Results](#results) · [Getting started](#getting-started) · [Contributing](docs/contributing.md) ·
[Security](docs/security-and-governance.md)

</div>

## Overview

CodeSOTA is an open-source project for building, running, validating, and comparing evaluations of language models
and AI agents. It is model-neutral: any open-weight or API model can be measured with the same protocol, and no model
family is special in the code.

A benchmark score is only useful when someone else can reproduce it and knows exactly what it measured. Reported
scores move with prompt formats, answer extraction, truncation, chat templates, scorer versions, and dataset
revisions, and a run that failed for infrastructure reasons can look like a model that scored zero.

**Methodology.** These are the standards every CodeSOTA evaluation is held to. They are requirements for new and
updated work, not a claim that every benchmark already meets all of them; the next section says where things stand.

- **Official implementations, pinned.** Run the benchmark's official harness and scorer at a fixed commit, on a
  recorded dataset revision. Any deviation is recorded with its reason.
- **Reproduce before you compare.** Results enter comparison tables only after a published reference result has been
  reproduced, or the benchmark is documented as having no reference to reproduce.
- **Explicit failures, not misleading zeros.** A run that failed, or a model that cannot run an evaluation, is
  recorded as such.
- **Uncertainty with every comparison.** Scores carry standard errors, and differences between models a statistical
  verdict.
- **Raw outputs and provenance.** Per-question outputs, settings, and versions are kept where licenses allow, so
  numbers can be recomputed.

**Where the repository stands.** What is in place today, checked against the repository:

- 55 benchmark directories, each with a card describing the original benchmark (`ORIGINAL.md`) and a run recipe
  (`RECIPE.md`).
- 25 of them have a reproduction report (`REPRODUCTION.md`). Its verdict is stated in each report and is not always
  a pass: some reproductions are met, some wait for the central run, some are inconclusive.
- The central run evaluates every model with the same pinned settings and dataset revisions
  ([`research/common/zadania.py`](../research/common/zadania.py)).
- In the published results, only benchmarks with a met reproduction appear in the comparison table, every score has a
  standard error, and comparisons have a statistical verdict.
- Per-question outputs are stored in the repository for some benchmarks and runs, not yet for all.

## Run

Run benchmarks on any Hugging Face model, from the Hub or a local directory. Each benchmark writes its own result
directory, checked by the validator before it is reported:

```bash
cd "$(git rev-parse --show-toplevel)/benchmarks"
uv sync --extra eval --python 3.12
uv run python -m codesota.runner --list
uv run python -m codesota.runner --benchmarks @verified --model EleutherAI/pythia-1b-v0 \
  --revision f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0 --out runs/
```

Select benchmarks by name (`arc-easy`), alias, pack (`@verified`, `@small`, `@pl`), or `all`. The list of
benchmarks and their status is in [`BENCHMARKS.md`](BENCHMARKS.md); options, output, and how the results were
verified are in [`docs/running.md`](docs/running.md). On a GPU, install the CUDA build of torch 2.8.0 first
(`docs/running.md`, "Install").

## Evaluation domains

The table lists the benchmarks that have a directory in the repository, grouped by area. A listed benchmark is not
necessarily a completed, reproducible integration: [`research/STATUS.md`](../research/STATUS.md) (written in Polish,
last updated 16 Nov 2026) counts 23 as complete (documented, prepared, and in the central run), 30 as in the central
run without full documentation, and 2 as documented but outside the run.

| Domain | Benchmarks with a directory in the repository |
|---|---|
| Reasoning and mathematics | GSM8K, MATH, MathQA, BIG-Bench Hard, LogiQA, ANLI, ARC-Challenge |
| Knowledge and question answering | MMLU, TriviaQA, Natural Questions, SciQ, OpenBookQA, MedMCQA, PubMedQA, TruthfulQA |
| Reading comprehension | SQuAD 2.0, CoQA, DROP, RACE, ReCoRD, BoolQ |
| Commonsense and world knowledge | HellaSwag, PIQA, WinoGrande, Social IQa, COPA, WSC273, EWoK |
| Instruction following | IFEval |
| Language modeling and linguistics | WikiText-2, LAMBADA, BLiMP, CoLA, UncheatableEval |
| Polish language | Belebele (PL), PolEmo 2.0, PolQA, PoQuAD, KLEJ NER, LLMzSzL, 8TAGS, CBD, PSC, PPC, DYK, MultiBLiMP (PL), EWoK (PL) |
| Coding, tool use, and agentic tasks | planned; no integrations in the repository yet |

Each benchmark lives in [`research/benchmarks/<name>/`](../research/benchmarks/) with its card, recipe, any
benchmark-specific code, and, where done, a reproduction report.

## Methodology and reproducibility

- [`research/METODOLOGIA.md`](../research/METODOLOGIA.md): the full protocol behind the benchmarks in
  `research/benchmarks/`: reproduction against references, test types, baselines, standard errors and verdicts, and
  the central run that evaluates every model with the same settings. Written in Polish.
- [`research/METHODOLOGY.md`](../research/METHODOLOGY.md): how a benchmark run through a model API is documented:
  sources, settings, machine-readable results, per-question outputs, deviations, and when it counts as done.
- [`research/common/README.md`](../research/common/README.md): the machine-readable results format, with schema
  version, protocol and run identifiers, per-observation states for non-success outcomes, confidence intervals, and
  artifact hashes. Written in Polish.
- [`AGENTS.md`](AGENTS.md): the engineering rules for contributions to `benchmarks/`, including official scorers,
  failure states, golden checks for scoring changes, and disclosure of AI assistance.

## Results

- [Full run, November 2026](../research/results/full-run-2026-11/README.md): 15 benchmarks on full test sets for
  8 open reference models and 9 development checkpoints of one 1B model under development, with standard errors,
  statistical verdicts, and the settings of every run. Report written in Polish; an interactive view of the same
  results is on [Hugging Face](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks).
- [`research/results/`](../research/results/): all numbers used in reports, generated from raw outputs and checked
  by an automated number gate.

## Getting started

Clone the repository (or your fork):

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai.git
cd benchmarks-fabryka-ai
```

The blocks below can run in any order. Each starts by moving into its directory from wherever you are inside the
clone, so running them one after another works.

**Test the evaluation code.** The lightweight tests need no GPU, weights, or network. This runs one of them; CI runs
the full lightweight set listed in [`research-tests.yml`](../.github/workflows/research-tests.yml):

```bash
cd "$(git rev-parse --show-toplevel)/research"
python -m pip install pytest numpy==2.0.2 scipy==1.13.1
python -m pytest -q tests/test_statystyka.py
```

Running full evaluations needs model weights and the pinned environment described in
[`research/README.md`](../research/README.md) (written in Polish).

**Develop the `codesota` Python package** in `benchmarks/`. It is the home of new shared tooling. Today it
runs the benchmarks of its catalog on a model (`python -m codesota.runner`, see [`docs/running.md`](docs/running.md)
and [`BENCHMARKS.md`](BENCHMARKS.md)) and validates result artifacts (`python -m codesota.results`, see
[`docs/result-artifacts.md`](docs/result-artifacts.md)). It needs Python 3.11+ and [uv](https://docs.astral.sh/uv/);
running benchmarks also needs the `eval` extra (`uv sync --extra eval`):

```bash
cd "$(git rev-parse --show-toplevel)/benchmarks"
uv sync --locked
uv run pytest
uv run ruff format --check
uv run ruff check
uv run mypy
uv build
```

```
benchmarks/
├── src/codesota/   the package
├── tests/          deterministic tests; no network, GPU, or weights
├── docs/           running benchmarks, result artifacts, contributor, security, and governance documentation
├── BENCHMARKS.md   every benchmark and its status, generated from the catalog
├── AGENTS.md       engineering rules for contributors and coding agents
└── pyproject.toml  package metadata and tool configuration; uv.lock pins the environment
```

## Contributing

Contributions from researchers and developers are welcome. Work on the `codesota` package needs no access to
private infrastructure; running full evaluations on rented machines or the project's model API is coordinated with
the maintainers ([`research/METHODOLOGY.md`](../research/METHODOLOGY.md)).

- [`docs/contributing.md`](docs/contributing.md): how to set up, choose a task, find official sources, prepare
  reproducible evidence, and open a pull request.
- [`AGENTS.md`](AGENTS.md): rules for coding agents and the people who supervise them.
- [`docs/security-and-governance.md`](docs/security-and-governance.md): review roles, CI trust boundaries, and how
  to report a security problem.
- Pull requests use the [template](../.github/pull_request_template.md), checked automatically for structure.

## Community

CodeSOTA is maintained by the Benchmark Team of [Fabryka AI](https://fabryka.ai) in the
[`slayerlabs`](https://github.com/slayerlabs) GitHub organization. Discussion happens in
[issues](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues) and on
[Discord](https://discord.gg/HnTkVR4c5T).

## License

The repository does not yet have a license; one is pending a decision by the project owners, and until then no
license grant should be assumed. Benchmark datasets, upstream harness code, model weights, and model outputs carry
their own terms, independent of CodeSOTA's code.
