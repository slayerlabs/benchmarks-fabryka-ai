# Security and governance

How changes to CodeSOTA are reviewed, what the automation can and cannot do, and which repository settings still need a
maintainer with admin rights. The settings below were read from the GitHub API on 2026-11-19 and can change; check
them again before relying on them.

## Trust boundary

Everything that runs on a pull request in this public repository is treated as untrusted, including the PR title,
description, branch name, and changed files.

All PR workflows run on `pull_request`. For PRs from forks, GitHub gives them a read-only token and no repository
secrets. On this event the workflow definition comes from the PR itself, which decides what each check can be trusted
for:

| Workflow (check names) | Code that decides | Trusted for |
|---|---|---|
| `pr-policy.yml` (`PR policy`) | `.github/scripts/pr_policy.py` from the **default branch**, checked out explicitly; nothing from the PR runs | the PR title and description policy, against a PR that edits the checker. Not against a PR that edits `pr-policy.yml` itself (see below) |
| `codesota.yml` (`CodeSOTA CI`) | the PR's own workflow, scripts, and `benchmarks/` code | testing contributor code; a PR can weaken it |
| `repo-checks.yml` (`Repository scripts tests`, `CODEOWNERS validation`) | the PR's own `.github/scripts` and their tests; GitHub's parser for the PR's `CODEOWNERS` | testing changes to repository scripts; validating `CODEOWNERS` |

- **What the policy check does and does not resist.** Because the checker comes from the default branch, editing
  `pr_policy.py` in a PR does not change the policy that PR is checked against; the change is tested by
  `Repository scripts tests` and takes effect after merge. A PR that edits `pr-policy.yml` itself could still skip
  the check, because the workflow definition comes from the PR. That gap is closed by a GitHub setting, not by code:
  an organization ruleset that requires this workflow from the default branch, or code owner review of `.github/` by
  a trusted team. Until one of them is in place, every change to `.github/workflows/` needs a careful human review,
  and `PR policy` should not be treated as an enforcement control.
- **Why not `pull_request_target`.** It would take the workflow definition from the default branch, but it runs with
  the base repository's context, and GitHub blocks it by default in public repositories from 2026-12-02 unless an
  admin allows it in an Actions event policy
  ([changelog](https://github.blog/changelog/2026-11-02-pull_request_target-blocked-by-default-december-2/)).
- **Missing checker.** If the default branch has no checker, `PR policy` fails for every PR numbered above 310 (the
  PR that introduced the check), so deleting the checker cannot silently turn it off.
- **Every workflow** declares `permissions: {}` at the top and grants each job only what it needs (`contents: read`;
  `pull-requests: read` for the job that lists changed files). Every job has a timeout.
- **Untrusted text is never interpolated into a shell.** PR title and body reach scripts only through environment
  variables and are parsed in Python.
- **Actions are pinned to full commit SHAs**, with the release tag in a comment.
- **Trusted evaluation infrastructure** (rented GPUs, inference API keys, gated datasets, private result stores) is
  not reachable from public PR CI and must stay that way. An evaluation that needs it runs outside GitHub Actions, by
  a maintainer, on code that has been reviewed and merged. The absence of secrets in the source code does not make
  evaluation assets safe: datasets, model outputs, and recordings can be sensitive or licensed, and are published
  only when their terms allow.
- **Model weights and checkpoints are untrusted input.** Load them with formats or options that do not execute code
  (`safetensors`, or `torch.load(..., weights_only=True)`), never with plain pickle.
- **Model-generated code runs only in a sandbox.** CodeSOTA has no code-executing evaluations yet; the first one must bring
  its sandboxing design for review.

`CodeSOTA CI` and `Repository checks` run the PR's own version of their workflows and scripts, so a PR that edits them
can weaken them. They are trustworthy only together with human review of changes under `.github/`, which today rests
on the general one-approval rule (see [Code owners](#code-owners)). `PR policy` resists edits to its checker but
not to its own workflow file (above).

## Review roles

Five different things, often confused:

| | granted by |
|---|---|
| Comment on or review a PR | anyone with read access (public repo: anyone) |
| Have an approval count toward the merge requirement | write access to the repository |
| Push branches to the repository | write access |
| Merge a PR | write access, once the branch ruleset's requirements are met |
| Bypass the ruleset | the ruleset's bypass list (currently empty) |

`CODEOWNERS` adds one more: it routes review requests to owners, and only when the ruleset requires code owner
review does an owner's approval become mandatory. It grants no write permission and hides nothing in a public
repository.

## Current settings (read 2026-11-19)

- Ruleset `Protect main`, active, on the default branch: pull request required, 1 approving review, stale approvals
  dismissed on push, approval of the most recent push required, conversations resolved, no deletion, no force push,
  no bypass actors. **Code owner review is not required. No status checks are required.**
- Teams with write access: `benchmark-team` (15 members), `benchmark-reviewers` (1 member), `slayer`.
- No team for core maintainers or security exists.
- Workflow token default: read-only; Actions cannot approve PRs. Fork PR workflows from first-time contributors need
  approval. Actions are not required to be SHA-pinned at the repository level.
- No license file. Private vulnerability reporting is disabled.

## Code owners

[`.github/CODEOWNERS`](../../.github/CODEOWNERS) assigns `benchmarks/` to `@slayerlabs/benchmark-reviewers`, so
ordinary `benchmarks/` PRs can be reviewed by that team without the two lead maintainers.

Sensitive paths (`.github/`, including workflows and `CODEOWNERS` itself, and core architecture under `benchmarks/` once it exists) have
**no owner yet**, because no core or security team exists. Assigning them to individual people or to an invented team
would give a false impression that they are protected. Until a team exists, these paths are protected only by the
general one-approval rule.

Two checks cover the file, and neither enforces permissions: `.github/scripts/test_codeowners.py` checks offline
invariants (only owners recorded as verified, valid spelling, existing paths), and the `CODEOWNERS validation` job asks
GitHub's own parser for errors in the PR's version (unknown owner, owner without write access, bad syntax). Whether an
owner's approval is required is set in the ruleset, and that is the only thing that turns ownership into enforcement.

## Manual steps for an admin

None of these is done in code; each needs an explicit decision by an admin.

1. Add members to `benchmark-reviewers`. With one member, requiring code owner review would make that person a
   bottleneck for every `benchmarks/` PR.
2. Create a core maintainers team (and, if wanted, a security team) with write access, then add owners for
   `/.github/`, `/.github/CODEOWNERS`, and core `benchmarks/` paths to `CODEOWNERS` in a reviewed PR.
3. In `Protect main`, enable "Require review from Code Owners" only after steps 1 and 2.
4. After the checks have run successfully on real PRs, consider adding them as required status checks. The check
   names are `PR policy`, `CodeSOTA CI`, `Repository scripts tests`, and `CODEOWNERS validation`. Each workflow runs
   on every PR that GitHub runs workflows for (`CodeSOTA CI` reports success without running its tests when a PR does
   not touch `benchmarks/`), so requiring them does not hold back unrelated PRs. GitHub runs no `pull_request` workflows while a
   PR has merge conflicts, and a first-time contributor's fork PR waits for an approval to run them; those PRs stay
   pending until resolved, as with any required check. Require `PR policy` only after it has reported on real PRs.
   **A required check is matched by name, so any workflow can satisfy it,** including a workflow a PR adds or edits:
   a job named `PR policy` that exits 0 would pass. Requiring these checks therefore adds protection only together
   with a control on `.github/workflows/` changes: an organization ruleset that requires the workflow from the
   default branch, or code owner review of `.github/` by a trusted team.
5. Decide whether `benchmark-team` keeps write access or moves to triage, once review responsibility is clear.
6. Enable private vulnerability reporting, then add a `SECURITY.md` that points to it. Do not publish a contact
   address or a response time the project has not committed to.
7. Choose and add a license (Apache-2.0 has been proposed but not approved). Record third-party terms for datasets,
   harness code, and model outputs separately.
8. Consider requiring SHA-pinned actions at the repository level, and pinning the actions in the other
   workflows (`ci.yml`, `research-tests.yml`, `board-unassign.yml`, `stage-bc-after-card.yml`), which use tags.

## Reporting a vulnerability

Until private vulnerability reporting is enabled, do not open a public issue for a suspected vulnerability. Contact
a repository admin privately and ask how to send details.
