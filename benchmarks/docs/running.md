# Running benchmarks

`python -m codesota.runner` runs a selection of catalog benchmarks on one model and writes each result as its own run
directory in the [`codesota.results`](result-artifacts.md) format. The benchmarks, their status, and the evidence
behind each status are listed in [`BENCHMARKS.md`](../BENCHMARKS.md).

The runner is a port of the research central run (`research/common/ewaluuj.py`, `zadania.py`, `metryki.py`, and
`research/tools/statystyka.py`) for full test splits: the same lm-eval version, prompts, pinned data, request
construction, scoring arithmetic, bootstrap seeds, and verdict thresholds. Tests compare it with that code
(`tests/test_runner.py`), and real runs reproduce the research pipeline's results ([Verification](#verification)).

## Install

From `benchmarks/`:

```bash
uv sync --extra eval
```

The lock installs the CPU build of torch. To run on an NVIDIA GPU, replace it with the CUDA build of the same version
in the same environment, for example `uv pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128`.
The other packages of the evaluation stack are pinned to the versions of the research central run
(`research/common/requirements.lock.txt`).

## Run

```bash
uv run python -m codesota.runner --list
uv run python -m codesota.runner --benchmarks arc-easy,piqa --model EleutherAI/pythia-1b-v0 \
  --revision f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0 --out runs/
uv run python -m codesota.runner --benchmarks @verified --model ./models/my-model --out runs/
```

**Selection** (`--benchmarks`, comma-separated, in any mix): a benchmark ID (`arc-easy`), an alias (`arce`), a legacy
task ID of the research pipeline (`T51`), a pack (`@verified`, `@needs-reference-check`, `@implemented`,
`@full-run-2026-11`, `@en`, `@pl`), or `all`. Case does not matter, and `_` equals `-`. Every name is resolved
before anything runs; an unknown one is a usage error. A selected benchmark that is not implemented is reported as
`not_run`, with its reason, and is not silently dropped.

**Model** (`--model`): a Hugging Face Hub repository with `--revision` set to a full commit SHA (a branch or tag can
move), or a local directory (`--revision` then optionally names the commit it came from). A private repository reads
its token from the `HF_TOKEN` environment variable; the token is never recorded. The model is loaded with lm-eval's
`HFLM`. Code shipped with a model runs only with `--trust-remote-code`, and the run records it.

**Settings**: `--dtype` (default `float32`), `--device` (default `cuda`), `--batch-size` (default 1), and
`--max-length` (default: from the model's configuration) are those of the research central run unless changed, and
every one is recorded. `--bos one` (default) puts exactly one leading BOS token of the model's tokenizer before every
request with a context, the rule of the research methodology (`research/METODOLOGIA.md`, section on the model input); `--bos none`
keeps lm-eval 0.4.9.1's default, which adds none, as the published Pythia v0 references were computed. The BOS policy
is part of the protocol ID (`codesota.<benchmark>.0shot.<bos>-bos.v1`), so the two are never mixed in one protocol.

The exit code is 0 when every selected benchmark was scored, 1 when any was not, and 2 on a usage error.

## Output

```
runs/
├── index.json                                        one row per selected benchmark: state, value, run directory
└── arc-easy.EleutherAI--pythia-1b-v0.one-bos.<time>/
    ├── manifest.json                                 identity, settings, provenance, observations, assessment
    ├── samples.jsonl                                 one record per question: scores, gold, prediction, log-likelihoods
    └── task-config.json                              the effective lm-eval task configuration
```

Each run is validated with `codesota.results` before the runner reports it. Besides the fields that format defines,
the manifest records:

- `assessment`: the benchmark's catalog status and its evidence, the decision metric with its SE and interval, the
  baselines, and the comparison with b, the higher of the random baseline and the constant answer (as in the research
  methodology);
- `execution.environment`: package versions, GPU, whether the checkout had uncommitted changes, the SHA-256 of every
  weight file, and a BOS probe that shows how many leading BOS tokens a request gets.

A run whose checkout had uncommitted changes, whose model has no recorded revision, or whose data come from an
unpinned branch is marked `provenance_claim: partial`.

**Failures are states, not scores.** A prompt longer than the model's context window makes the benchmark
`unsupported` (the evaluation is not shortened to fit). Missing access to a dataset or model is `blocked_access`.
Anything else, including a split whose size differs from the pinned one, is `failed`, with the error in the run's
`error.log`. Such a run has no value, and no sample carries a score.

## What differs from the research pipeline

None of these changes a reported score; each is checked by `tests/test_runner.py` or the verification runs.

- The unconditional log-likelihoods of `acc_mutual_info` (PMI, a diagnostic) are not requested, which halves the
  requests of a multiple-choice benchmark. Diagnostic variants (ARC-Challenge in letter format, MedMCQA as cloze)
  and per-question traces are not ported.
- The interval method is named for what it is (`percentile_bootstrap`, or `cluster_bootstrap` for WinoGrande and
  WSC273), where the research results label it `paired_bootstrap`. The numbers are the same.
- Verdicts are named in English: `strong` (pewne), `probable` (prawdopodobne), `noise` (szum), and `inconclusive`
  (nierozstrzygalne), with the same thresholds.
- Benchmark IDs are the directory names in `research/benchmarks/`; the research task IDs (`T01`-`T53`) are kept as
  `legacy_id` and accepted as aliases.

## Verification

The runner's results were compared with the research pipeline's on the same model, revision, and settings
(float32, batch 1): EleutherAI/pythia-1b-v0 at `f3f1b6d5`, without BOS against the full run of November 2026
(`research/results/full-run-2026-11/`), and with one BOS against the BOS check of the same run
(`research/results/full-run-2026-11/bos-window-check/`). The research runs used an RTX 5090; the runner's ran on an
RTX 5060 Ti. Identical results on different hardware are not guaranteed in general; the tolerance, fixed before the
runs, was one question.

The table of results is filled in by the verification runs of this change.
