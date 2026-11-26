# Contributing

How the Benchmark Team works: contact, tasks, the board, and review.

## First steps

1. **Join**: write in #bench-team ([Contact](#contact) below).
2. **Take a task** from the board ([Taking a task](#taking-a-task)).
3. **Read the [evaluation methodology](benchmarks/docs/methodology.md)**: how every model is configured for a run.
   It is the one methodology for new work.
4. **Do the work where it belongs**: a new benchmark goes to `research/api-benchmarks/<name>/`, step by step in
   [its guide](research/api-benchmarks/README.md); a log-likelihood benchmark goes into the CodeSOTA runner's
   catalog ([`benchmarks/docs/contributing.md`](benchmarks/docs/contributing.md#5-writing-an-integration)); anything
   else in `research/` goes where [the workspace map](research/README.md#where-things-go) says.
5. **Open a PR** ([Pull requests](#pull-requests)).

<a name="kontakt"></a>

## Contact

We talk on Discord, in **#bench-team**: https://discord.gg/HnTkVR4c5T. To start, write there to LoIlita or Elwenor
with your GitHub login. They add you to the Benchmark Team, which lets you take tasks, move cards on the board and
push branches. Ask there too when something does not work or is missing from the docs, and say at which step you
are stuck.

### Who is who

- **LoIlita and Elwenor** coordinate the team and add new people to it.
- **Arek** owns the Slayer model and the [Space](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks), the
  copy of the [results page](benchmarks/results/README.md) on Hugging Face.

<a name="pierwsze-zadanie"></a>

## Taking a task

Pick a task from the Ready column of the [board](https://github.com/orgs/slayerlabs/projects/10) or one labelled
[`good first issue`](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22),
assign yourself (Assignees → Assign yourself) and move it to In Progress. One task at a time. Which benchmarks come
first: [research priorities](benchmarks/docs/research-priorities.md).

<a name="pr"></a>

## Pull requests

1. Branch from `main`, or open the PR from a fork, which needs no write access.
2. Follow [`benchmarks/docs/contributing.md`](benchmarks/docs/contributing.md): Conventional Commits title, every
   section of the PR template, `Refs #N` of the task. Write `Refs`, not `Closes`: the issue closes when its card
   reaches Done on the board.
3. Open the PR as a **Draft** while you work. When the checks below exit 0 and someone else can take the PR over,
   mark it **Ready for review** and move the task to Review.

<a name="przed-pr"></a>

### Checks before a PR in `research/`

CI for `research/` ([`research-tests.yml`](.github/workflows/research-tests.yml)) runs only the tests without torch
and lm-eval, so run these yourself in `research/`. Each must exit 0:

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
.venv-eval/bin/python tests/test_<name>.py
.venv-eval/bin/python tests/test_liczby_raportow.py
```

The first line is the number gate: every number in a report must match the generated `results/LICZBY.json`. The
number gate and `tests/test_liczby_raportow.py` use only Python's standard library: without the full environment, run
them with `python3` instead of `.venv-eval/bin/python`. A benchmark's own test may need its own environment, named in its
README. The full lm-eval environment of the frozen November 2026 run is set up as in
[`research/README.md`](research/README.md#przygotowanie-raz) (Polish). Checks for `benchmarks/` are in
[`benchmarks/docs/contributing.md`](benchmarks/docs/contributing.md#2-run-the-checks).

<a name="tablica"></a>

## Board

The board is at https://github.com/orgs/slayerlabs/projects/10. A task moves through these Status columns:

1. **Backlog**: waiting, not to be taken yet.
2. **Ready**: can be taken.
3. **In Progress**: someone is doing it. You move it here yourself when you assign yourself.
4. **Review**: first check.
5. **Independent Check**: second, independent check.
6. **Done**: finished. Done closes the issue.

When a task moves from In Progress to Review or Independent Check,
[`board-unassign.yml`](.github/workflows/board-unassign.yml) removes its assignees within a few minutes. In Review
and Independent Check a task can be taken only as a review; a reviewer who assigns themselves stays assigned.

Task fields:

- **Time**: up to 2 h, up to 1 day, or several days.
- **Kind**: "steps given" (follow the listed steps) or "to investigate" (find the way first).
- **Area**: Data, Architecture and learning, Training systems, Infrastructure, or Evaluation and measurement.

### Review path

Each task names its review path in a line "Review path:". The strength of the check follows the cost of a wrong
result:

- **no review**: In Progress → Done after merge, with the checks above at exit 0. Only when the task names this path
  and the change touches no number, for example a link or typo fix.
- **review** (default): In Progress → Review → Done. One person checks the PR and reruns at least one result from
  its recipe or `run.sh --limit 5`.
- **review and recheck** (label `needs-recheck`): In Progress → Review → Independent Check → Done. A second person
  computes the result from scratch, on other hardware. For a result that goes to the results page or into a
  training decision.

## Labels

- `good first issue`: a task for a first contribution.
- `research`: a benchmark, measurement or analysis.
- `dev`: shared code, tools or CI.
- `needs-recheck`: the result needs the independent check above.

## How we write tasks

A benchmark task is short. Title: the benchmark name. Body: which models to run, a link to the reference with
published scores and settings when there is one, links to the [Fabryka AI API](https://fabryka.ai/platform),
[`research/api-benchmarks/README.md`](research/api-benchmarks/README.md) and the
[evaluation methodology](benchmarks/docs/methodology.md),
a note that a machine is available on request, an empty result table with one row per model, and the review path.
How to run the benchmark and what to deliver belongs to the methodology, not the task.

<a name="pliki-w-repo"></a>

## Files in the repository

- Everything is written in English: documents, code, comments, issues, PRs and commit messages.
- Do not commit model weights (`*.safetensors`, `*.bin`, `*.pt`, `models/`), datasets (`*.parquet`, `*.arrow`),
  `*.zip` archives, API keys, or any file over 10 MB. `research/.gitignore` lists the exclusions.
- Per-question results may be committed compressed, as `results/<model-id>.jsonl.gz`, up to about 10 MB per file.
  Raw `*.jsonl` stays on your machine.
