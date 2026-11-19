<div align="center">

# CodeSOTA

**Reproducible evaluation for language models and AI agents.**

[![CodeSOTA CI](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/codesota.yml/badge.svg?branch=main)](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/codesota.yml)
[![Research tests](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/research-tests.yml/badge.svg?branch=main)](https://github.com/slayerlabs/benchmarks-fabryka-ai/actions/workflows/research-tests.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)

[Overview](#overview) · [Evaluations](#evaluation-domains) · [Methodology](#methodology-and-reproducibility) ·
[Results](#results) · [Getting started](#getting-started) · [Contributing](docs/contributing.md) ·
[Security](docs/security-and-governance.md)

</div>

## Overview

CodeSOTA is an open-source project for building, running, validating, and comparing evaluations of language models
and AI agents. It is model-neutral: any open-weight or API model can be measured with the same protocol, and no model
family is special in the code.

A benchmark score is only useful when someone else can reproduce it and knows exactly what it measured. Reported
scores move with prompt formats, answer extraction, truncation, chat templates, scorer versions, and dataset
revisions, and a run that failed for infrastructure reasons can look like a model that scored zero. CodeSOTA treats
these as engineering problems:

- **Official implementations, pinned.** Benchmarks run through their official harness and scorer at fixed commits,
  on dataset revisions recorded with every result.
- **Reproduce before you measure.** A benchmark is checked against a published reference result before its numbers
  are used.
- **Explicit failures, not misleading zeros.** A run that failed, or a model that cannot run an evaluation, is
  recorded as such.
- **Uncertainty with every comparison.** Scores come with standard errors, and differences between models with a
  statistical verdict.
- **Raw outputs and provenance.** Per-question outputs, settings, and versions are kept where licenses allow, so any
  number can be recomputed.

## Evaluation domains

The repository holds evaluation code, reference documentation, and results for benchmarks across these areas.
Completeness varies by benchmark (some are fully reproduced against a reference, some are integrated but not yet
documented); [`research/STATUS.md`](../research/STATUS.md) tracks each one.

| Domain | Benchmarks in the repository |
|---|---|
| Reasoning and mathematics | GSM8K, MATH, MathQA, BIG-Bench Hard, LogiQA, ANLI, ARC-Challenge |
| Knowledge and question answering | MMLU, TriviaQA, Natural Questions, SciQ, OpenBookQA, MedMCQA, PubMedQA, TruthfulQA |
| Reading comprehension | SQuAD 2.0, CoQA, DROP, RACE, ReCoRD, BoolQ |
| Commonsense and world knowledge | HellaSwag, PIQA, WinoGrande, Social IQa, COPA, WSC273, EWoK |
| Instruction following | IFEval |
| Language modeling and linguistics | WikiText-2, LAMBADA, BLiMP, CoLA, UncheatableEval |
| Polish language | Belebele (PL), PolEmo 2.0, PolQA, PoQuAD, KLEJ NER, LLMzSzL, 8TAGS, CBD, PSC, PPC, DYK, MultiBLiMP (PL), EWoK (PL) |
| Coding, tool use, and agentic tasks | planned; no integrations in the repository yet |

Each benchmark lives in [`research/benchmarks/<name>/`](../research/benchmarks/) with its code, a card describing
the original benchmark, and, where done, a reproduction report.

## Methodology and reproducibility

- [`research/METHODOLOGY.md`](../research/METHODOLOGY.md): what a well-done benchmark result contains (sources,
  settings, machine-readable results, per-question outputs, deviations) and when it counts as done.
- [`research/METODOLOGIA.md`](../research/METODOLOGIA.md): the full protocol behind the existing benchmarks:
  reproduction against references, test types, baselines, standard errors and verdicts, and the central run that
  evaluates every model with the same settings. Written in Polish.
- [`research/common/README.md`](../research/common/README.md): the machine-readable results format, with schema
  version, protocol and run identifiers, per-observation states for non-success outcomes, confidence intervals, and
  artifact hashes. Written in Polish.
- [`AGENTS.md`](AGENTS.md): the engineering rules every contribution follows, including official scorers, failure
  states, golden checks for scoring changes, and disclosure of AI assistance.

## Results

- [Full run, November 2026](../research/results/full-run-2026-11/README.md): 17 open models on 15 benchmarks, full
  test sets, with standard errors, statistical verdicts, and the settings of every run. Report written in Polish.
- [`research/results/`](../research/results/): all numbers used in reports, generated from raw outputs and checked
  by an automated number gate.
- [Results viewer on Hugging Face](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks): an interactive view
  of results for the Slayer 1B model family.

## Getting started

Clone the repository (or your fork):

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai.git
cd benchmarks-fabryka-ai
```

**Run the benchmark test suite.** The lightweight tests of the evaluation code need no GPU, weights, or network:

```bash
cd research
python -m pip install pytest numpy==2.0.2 scipy==1.13.1
python -m pytest -q tests/test_statystyka.py
```

Running full evaluations needs model weights and the pinned environment described in
[`research/README.md`](../research/README.md) (written in Polish).

**Develop the `codesota` Python package** in this directory. It is the home of new shared tooling and currently
contains packaging, tests, and checks only; it does not run evaluations or provide a command-line interface yet.
It needs Python 3.11+ and [uv](https://docs.astral.sh/uv/):

```bash
cd benchmarks
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
├── docs/           contributor, security, and governance documentation
├── AGENTS.md       engineering rules for contributors and coding agents
└── pyproject.toml  package metadata and tool configuration; uv.lock pins the environment
```

## Contributing

Contributions from researchers and developers are welcome, and no access to private infrastructure is needed.

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
