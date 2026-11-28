# benchmarks-fabryka-ai

This repository is **[CodeSOTA](benchmarks/README.md)**: reproducible evaluation of open language models and AI
agents, run by the Benchmark Team of [Fabryka AI](https://fabryka.ai). We measure Slayer 1B, Bielik 11B v3.1 and
reference models with the same protocol, and publish every score with its standard error and settings.

**[Results](benchmarks/results/README.md)**: every published result in one place. The
[Space on Hugging Face](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks) is a copy of these results.

## Start here

1. **Join.** Write in **#bench-team** on [Discord](https://discord.gg/HnTkVR4c5T) with your GitHub login
   ([`CONTRIBUTING.md`](CONTRIBUTING.md)).
2. **Pick a task** from the Up for grabs column of the [board](https://github.com/orgs/slayerlabs/projects/10). The
   benchmarks to work on first are in [research priorities](benchmarks/docs/research-priorities.md).
3. **Read the methodology** before you run anything: [`benchmarks/docs/methodology.md`](benchmarks/docs/methodology.md)
   says how a model is configured (precision, decoding, repeats, output limit, standard errors, `null` and "not run").
4. **Run and deliver** the benchmark:
   - a benchmark through a model API, generative or agentic: a directory in `research/api-benchmarks/<name>/`, as
     [`research/METHODOLOGY.md`](research/METHODOLOGY.md) describes;
   - a log-likelihood benchmark: the CodeSOTA runner and its catalog
     ([`benchmarks/docs/running.md`](benchmarks/docs/running.md)).
5. **Open a PR** to `main` by [`benchmarks/docs/contributing.md`](benchmarks/docs/contributing.md#7-open-the-pull-request),
   with `Refs #N` of the task.

Do not use your own GPU or paid accounts. Model APIs go through the [Fabryka AI Platform](https://fabryka.ai/platform);
for a machine or another API, write in #bench-team.

## Which Slayer to measure

Slayer 1B is still in training. Measure the latest checkpoint published in its Hugging Face repository
(`SlayerLab/Slayer1B-<version>-checkpoints`, today [`Slayer1B-1.09-checkpoints`](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints/tree/main)),
pinned as repository @ revision and file, and say which step it is. The Space and older result pages are not where
the latest version is announced. Details: [methodology, section 1](benchmarks/docs/methodology.md#1-one-configuration-per-model).

## Where things are

| path | what it holds |
|---|---|
| [`benchmarks/`](benchmarks/README.md) | the `codesota` package: runner, result validation, results page, methodology and contributor docs |
| [`research/api-benchmarks/`](research/api-benchmarks/) | benchmarks run through a model API or our own serving, one directory each |
| `research/benchmarks/`, `research/results/`, `research/tools/` | the lm-eval pipeline of the November 2026 full run: benchmark cards, results and tools. Source of the log-likelihood rows on the results page and the evidence behind the runner's catalog. Its protocol, [`research/METODOLOGIA.md`](research/METODOLOGIA.md) (Polish), is frozen |
| `research/common/` | code shared by `research/` benchmarks, including the Slayer serving code |
| `research/slayer-1b/` | work on Slayer 1B itself (data, training, analyses) |
| [`research/archive/`](research/archive/README.md) | retired documents, kept to go back to |
| `frontend-beta/` | the results front end, in development |
