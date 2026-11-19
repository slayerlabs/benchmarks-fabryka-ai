<!--
Title: Conventional Commits in English, e.g. "fix(benchmarks): ..." or "docs: ...". The PR policy check verifies the
title and that each required section below has real content (HTML comments do not count).
Trivial documentation fixes (title starting with "docs:" AND the "Documentation only" box ticked) need only:
Problem, Result, Scope, and Related issue.
PRs that change only files under research/ (benchmarks) need none of the sections below: a title of at most 100
characters in any style (the benchmark and what it measures), a description of what the PR adds and its result, and
"Refs #N". See CONTRIBUTING.md.
Guides: benchmarks/docs/contributing.md (benchmarks/), CONTRIBUTING.md (research/).
-->

## Problem or current behavior
<!-- What was wrong or missing before this PR, and how you reproduced or observed it (command and output, failing
test, or a link). -->

## Result or new behavior
<!-- What changes for users, contributors, or results. Why this solution over the alternatives you considered. -->

## Scope
<!-- Tick every area this PR changes. -->
- [ ] `benchmarks/` (`codesota` package)
- [ ] `research/` (benchmarks, results, research code)
- [ ] `frontend-beta/`
- [ ] Repository infrastructure (`.github/`, CI, policy)
- [ ] Documentation only

## Compatibility and migration
<!-- Who must change what, or "No migration required." Include behavior changes to existing commands, files,
schemas, or results. -->

## Evaluation methodology impact
<!-- Does this change how any score is produced or interpreted (prompts, extraction, scoring, datasets, settings,
statistics)? If yes: which results move, in which direction, and the reference used. Otherwise: "None". -->

## Validation
<!-- Exact commands you ran and their actual outcomes, before and after where relevant. List checks you did not
run and why. Do not repeat routine green CI. -->

## Related issue
<!-- "Refs #123" links without closing (most issues here are closed through the project board). Use "Closes #123"
only when merging should close the issue. With no issue: "No issue: <reason>". -->

## AI assistance
<!-- "None", or: which tools wrote or changed code; whether an independent review ran in a fresh context (tool or
model, number of passes); findings fixed or dismissed, with a one-line reason each. If no review ran, say so. -->

## Reviewer checklist
<!-- For reviewers; authors may leave it unticked. -->
- [ ] The problem is real and this PR addresses it; nothing unrelated is bundled.
- [ ] Reported validation matches the commands run; CI is green or failures are explained.
- [ ] No credentials, model weights, gated datasets, or files over 10 MB are committed.
- [ ] Evaluation changes: official sources pinned, failures not scored as zeros, deviations named, same protocol for
      every model.
- [ ] `research/` benchmark PRs: the steps in `research/METHODOLOGY.md` (or `research/METODOLOGIA.md` for
      `research/benchmarks/`) are met, and the number gate and tests from CONTRIBUTING.md "Przed PR" pass.
