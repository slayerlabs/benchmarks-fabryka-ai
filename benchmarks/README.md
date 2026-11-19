# CodeSOTA

**Reproducible evaluation for language models and AI agents.**

CodeSOTA is an open-source project for building, running, validating, and comparing language model evaluations.
This directory, `benchmarks/`, is where its second version (v2) is being built.

[Status](#status) · [Why](#why-codesota) · [Principles](#principles) · [v2 and `research/`](#v2-and-the-legacy-research-pipeline) ·
[Development](#development) · [Contributing](docs/contributing.md) · [Security and governance](docs/security-and-governance.md) ·
[Agent rules](AGENTS.md)

## Status

**Pre-alpha. v2 does not run evaluations yet.**

What exists today:

- an installable Python package, `codesota`, that contains only its version and type marker;
- a lightweight test suite, linting, type checking, and a CI workflow for this directory;
- contribution, agent, and security rules for v2 work.

What does not exist yet: model backends, benchmark integrations, a CLI, a published package, an API, or results.
Each of these arrives in its own reviewed pull request, with tests, when a concrete requirement needs it. Nothing in
this README describes a feature that is not in the code.

The evaluations this project runs today live in [`research/`](../research/README.md) and keep working as before.

## Why CodeSOTA

A benchmark score is only useful when someone else can reproduce it and knows exactly what it measured. In practice,
reported scores move with prompt formats, answer extraction, truncation, chat templates, scorer versions, and
dataset revisions, and a run that failed for infrastructure reasons can look like a model that scored zero.

CodeSOTA's goal is to make changing the research question cheap (another model, checkpoint, or benchmark suite)
while making changes to evaluation methodology explicit, versioned, and auditable.

## Principles

- **Correctness over impressive abstractions.** Prefer the official implementation and scorer of a benchmark, pinned
  to a revision. Every deviation from the reference protocol is recorded and justified.
- **Evidence over claims.** A score comes with the inputs needed to reproduce it: model and dataset revisions, harness
  version, settings, raw outputs where licensing allows, and an uncertainty estimate where one is meaningful.
- **Explicit failures over misleading zeros.** A model that cannot run an evaluation, or a run that failed for
  infrastructure reasons, is recorded as such, never as a score of zero. The legacy results contract already models
  this with a per-observation `state` field ([`research/common/README.md`](../research/common/README.md)); v2 will
  start from that contract rather than invent a new one.
- **Model-neutral.** No model, family, or checkpoint is special in the code. Research priorities belong in
  configuration and campaigns, not in core interfaces.
- **Small, reviewable changes.** See [`AGENTS.md`](AGENTS.md).

## v2 and the legacy research pipeline

The repository runs a parallel migration:

| | `research/` (legacy) | `benchmarks/` (v2, this directory) |
|---|---|---|
| State | working; produces the current published results | foundation only; no evaluations |
| Instructions | [`research/README.md`](../research/README.md), [`research/METHODOLOGY.md`](../research/METHODOLOGY.md) | this README, [`docs/contributing.md`](docs/contributing.md), [`AGENTS.md`](AGENTS.md) |
| CI | `Research tests (light)` | `CodeSOTA CI` |

v2 does not import from, move, or modify `research/`. Results, the public frontend, and result feeds keep coming from
`research/` until a later, separately reviewed cutover.

## Development

Requirements: Python 3.11 or newer and [uv](https://docs.astral.sh/uv/). No GPU, model weights, API keys, or large
downloads are needed.

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai.git   # or your fork
cd benchmarks-fabryka-ai/benchmarks
uv sync --locked
uv run pytest
uv run ruff format --check
uv run ruff check
uv run mypy
uv build
```

These are the same checks `CodeSOTA CI` runs on every pull request that touches this directory.

Layout:

```
benchmarks/
├── src/codesota/   the package (version and type marker only, for now)
├── tests/          deterministic tests; no network, GPU, or weights
├── docs/           contributor and governance documentation
├── AGENTS.md       rules for coding agents and the people supervising them
└── pyproject.toml  package metadata and tool configuration; uv.lock pins the dev environment
```

## License

The repository has no license file yet. Choosing one is pending a decision by the project owners; until then,
do not assume any license grants. Benchmark datasets, upstream harness code, model weights, and model outputs can
carry their own terms, independent of the license chosen for CodeSOTA's code.
