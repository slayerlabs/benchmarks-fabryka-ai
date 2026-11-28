# benchmarks-fabryka-ai

This repository is **[CodeSOTA](benchmarks/README.md)**: reproducible evaluation of open language models and AI
agents, run by the Benchmark Team of [Fabryka AI](https://fabryka.ai). We measure Slayer 1B, Bielik 11B v3.1 and
reference models with the same protocol, and publish every score with its standard error and settings.

**[Results](benchmarks/results/README.md)**: every published result in one place. The
[Space on Hugging Face](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks) is a copy of these results.

## Where things are

| path | what it holds |
|---|---|
| [`benchmarks/`](benchmarks/README.md) | CodeSOTA, the `codesota` package: runner, result validation, results page, and the [evaluation methodology](benchmarks/docs/methodology.md). Start here to use or extend it |
| [`research/`](research/README.md) | the Benchmark Team's workspace: benchmarks in progress, analyses, work on Slayer 1B, and the frozen lm-eval run of November 2026 behind the log-likelihood results |
| `frontend-beta/` | the results front end, in development |

## Join the Benchmark Team

Write in **#bench-team** on [Discord](https://discord.gg/HnTkVR4c5T) with your GitHub login. How the team works,
from the first task to a merged PR: [`CONTRIBUTING.md`](CONTRIBUTING.md).
