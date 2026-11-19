# AGENTS.md

Rules for coding agents (Claude Code, Codex, Cursor, and similar) working in `benchmarks/`, and for the people who
supervise them and submit their work. Humans follow the same rules. Work in `research/` follows the root
[`AGENTS.md`](../AGENTS.md) instead.

The person who opens a pull request is responsible for every line in it, whoever or whatever wrote the line.

## Before writing code

1. **Read first.** Read the source files, tests, and documentation of the area you will change, plus
   [`README.md`](README.md) and [`docs/contributing.md`](docs/contributing.md). Do not infer behavior from file
   names.
2. **Search for existing work.** Search the code for an implementation of what you need before writing a new one.
   Search open issues and pull requests for the same problem. If a PR already addresses it, review or comment there
   instead of opening a competing one.
3. **Find the actual problem.** Reproduce it: a failing test, a command and its output, or a reference that shows
   the expected behavior. State the cause, not only the symptom. If you cannot reproduce or explain the problem,
   stop and write up what you found in an issue.
4. **Establish expected behavior from reliable sources.** For an evaluation, that is the benchmark's paper, its
   official implementation at a pinned commit, and its dataset at a pinned revision. Not a blog post, a summary, or a
   model's memory of either.
5. **State the change before making it.** One or two sentences: what will change, which files, what is out of scope.
   If the change does not fit in a reviewable PR, split it into dependent PRs and say so.
6. **No speculative rewrites.** Do not restructure, rename, or "modernize" code the task does not require you to
   touch. Do not add abstractions, base classes, plugin systems, or directories for future features.

## While writing code

- **English only:** code, identifiers, comments, docstrings, tests, documentation, commit messages, issues, and PR
  descriptions.
- **Small and focused:** one problem per PR. Unrelated fixes you notice go in their own issue or PR.
- **Reuse established interfaces.** Extend what exists; do not build a parallel version of it.
- **Explicit types and configuration.** Typed signatures (mypy runs in strict mode); configuration passed in, not
  read from hidden global state.
- **No unjustified dependencies.** A new dependency needs a reason in the PR description: what it does that the
  standard library or an existing dependency cannot. Heavy frameworks (GPU stacks, evaluation harnesses, HTTP
  clients) arrive only with the code that needs them.
- **No silent behavior changes.** Every behavior change is stated in the PR description, with who is affected.
- **No duplicated logic** and **no compatibility layers** without a named, current consumer.
- **Do not hide failures.** No `except Exception: pass`, no catch-all that returns a default, no fallback that turns
  an error into a plausible value. Catch only the exceptions you expect, where you can handle them correctly.
- **Do not suppress lint or type errors** (`# noqa`, `# type: ignore`) to make a check pass. Fix the code. If a
  suppression is genuinely correct, it names the specific rule and gives the reason on the same line.
- **Do not change a scorer, a metric, or answer extraction to make a benchmark pass** or to move a score toward an
  expected number.
- **Do not weaken, skip, or delete a failing test** as a substitute for fixing the code. A test that is wrong is
  fixed in its own commit with an explanation.
- **Never fabricate** output, results, scores, citations, benchmark numbers, test runs, or review findings.

## When developing evaluations

- **Prefer official implementations and scorers.** Reimplement only when the official one cannot be used, and say why.
- **Pin everything that can change a number:** harness commit, dataset revision, model revision, prompt template,
  generation settings, and scorer version.
- **Separate execution failures from model failures.** An API error, timeout of our own infrastructure, sandbox
  failure, or bug in our code is an error state, not a wrong answer. A model that cannot run the evaluation (for
  example, a context window that is too short, or a missing tool-calling capability) is recorded as unsupported, not
  scored zero. Do not shrink the evaluation to fit a model.
- **Keep raw outputs and provenance** (inputs, outputs, scores, timings, versions) where licensing and security allow.
  Never commit credentials, gated datasets in plain text, or model weights.
- **Name every deviation** from the reference protocol, with the reason, in the integration's documentation.
- **Scoring changes need golden checks.** A change to scoring or answer extraction comes with tests on fixed inputs
  that pin the expected scores, including a correct answer that still scores as correct and a wrong answer that still
  scores as wrong, and shows that reverting the change makes the new tests fail.
- **Never tune the evaluation toward a model.** The same protocol applies to every model compared. Choose metrics,
  subsets, and headline numbers before seeing results, not after.

## Before opening a pull request

1. **Review the full diff against the base branch** (`git diff origin/main...HEAD`), not only your last change.
2. **Remove everything unrelated to the problem:** stray formatting, debug output, experimental files, unrelated
   refactors.
3. **Run the checks** from [`README.md`](README.md#getting-started) and any tests of the area you changed.
4. **Report exact commands and actual outcomes** in the PR's "Validation" section. A test you did not run is
   listed as not run, with the reason. A run that collected no tests counts as not run.
5. **Explain changes to behavior, schemas, compatibility, and results**, including "none" where that is the answer.
6. **Disclose AI assistance** in the PR's "AI assistance" section: which tools wrote or changed code, whether an
   independent review ran in a fresh context (which tool or model, how many passes), what it found, and what was
   fixed or dismissed with a one-line reason. If no independent review ran, say so. Never report a review that did
   not happen.
7. **Open agent-prepared PRs as drafts.** The responsible person reviews the diff before marking it ready.

**Do not submit a PR that contains a long sequence of unreviewed agent-generated corrections.** Before opening it,
reconstruct the original problem, confirm the final solution addresses it, and review the complete diff as one
change. Agent-written code must be readable and understandable by another maintainer without the agent's context.

## Commenting and reviewing

When an agent comments on an issue or PR it was not asked to work on, it identifies itself as an AI agent, does not
claim to speak for the maintainers, and submits any review as a comment, never as an approval or a change request.
