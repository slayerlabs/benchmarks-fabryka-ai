# Security and governance

How v2 work is reviewed, what the automation can and cannot do, and which repository settings still need a
maintainer with admin rights. The settings below were read from the GitHub API on 2026-11-19 and can change; check
them again before relying on them.

## Trust boundary

Everything that runs on a pull request in this public repository is treated as untrusted, including the PR title,
description, branch name, and changed files.

There are two kinds of PR checks, with different trust:

| Workflow (check names) | Event | Code it runs | Trusted for |
|---|---|---|---|
| `pr-policy.yml` (`PR policy`) | `pull_request_target` | workflow definition and `.github/scripts/pr_policy.py` from the PR's **base branch**; nothing from the PR | enforcing the PR title and description policy, for PRs into `main` |
| `codesota.yml` (`CodeSOTA CI`) | `pull_request` | the PR's own workflow, scripts, and v2 code | testing contributor code; a PR can weaken it, so `.github/` changes need human review |
| `repo-checks.yml` (`Repository scripts tests`, `CODEOWNERS validation`) | `pull_request` | the PR's own `.github/scripts` and their tests; GitHub's parser for the PR's `CODEOWNERS` | testing changes to the repository scripts; validating `CODEOWNERS` |

- **Why the policy check uses `pull_request_target`.** On `pull_request`, the workflow definition itself comes from
  the PR, so a contributor could edit the workflow or the checker and make the check pass; no step inside such a
  workflow can prevent that. On `pull_request_target`, GitHub runs the workflow file from the base branch. The job
  checks out only `pr_policy.py` from the base branch, never anything from the PR head, references no secrets, has a
  read-only token that checkout does not persist, and passes the title and body only through environment variables.
  For PRs into `main`, the checker is therefore protected code. For a PR into another branch, it is as trusted as that
  branch. Because the definition comes from the base branch, a change to `pr-policy.yml` or `pr_policy.py` takes effect
  for other PRs only after it is merged, and the PR that introduces or changes it is checked by the version already on
  its base branch.
- **The other workflows** run on `pull_request`. For PRs from forks, GitHub gives them a read-only token and no
  repository secrets.
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
- **Model-generated code runs only in a sandbox.** v2 has no code-executing evaluations yet; the first one must bring
  its sandboxing design for review.

`CodeSOTA CI` and `Repository checks` run the PR's own version of their workflows and scripts, so a PR that edits them
can weaken them. They are trustworthy only together with human review of changes under `.github/`, which today rests
on the general one-approval rule (see [Code owners](#code-owners)). `PR policy` does not have this weakness.

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
ordinary v2 benchmark PRs can be reviewed by that team without the two lead maintainers.

Sensitive paths (`.github/`, including workflows and `CODEOWNERS` itself, and core v2 architecture once it exists) have
**no owner yet**, because no core or security team exists. Assigning them to individual people or to an invented team
would give a false impression that they are protected. Until a team exists, these paths are protected only by the
general one-approval rule.

Two checks cover the file, and neither enforces permissions: `.github/scripts/test_codeowners.py` checks offline
invariants (only owners recorded as verified, valid spelling, existing paths), and the `CODEOWNERS validation` job asks
GitHub's own parser for errors in the PR's version (unknown owner, owner without write access, bad syntax). Whether an
owner's approval is required is set in the ruleset, and that is the only thing that turns ownership into enforcement.

## Manual steps for an admin

None of these is done by the foundation PR; each needs an explicit decision.

1. Add members to `benchmark-reviewers`. With one member, requiring code owner review would make that person a
   bottleneck for every v2 PR.
2. Create a core maintainers team (and, if wanted, a security team) with write access, then add owners for
   `/.github/`, `/.github/CODEOWNERS`, and core v2 paths to `CODEOWNERS` in a reviewed PR.
3. In `Protect main`, enable "Require review from Code Owners" only after steps 1 and 2.
4. After the checks have run successfully on real PRs, consider adding them as required status checks. The check
   names are `PR policy`, `CodeSOTA CI`, `Repository scripts tests`, and `CODEOWNERS validation`. All report on every
   PR (`CodeSOTA CI` reports success without running its tests when a PR does not touch v2), so requiring them does
   not leave unrelated PRs pending. `PR policy` runs from the base branch, so it starts reporting only after this
   foundation is merged; require it only once it has reported on later PRs. For `PR policy`, set the expected source
   to GitHub Actions so that only this repository's workflow can satisfy it.
5. Decide whether `benchmark-team` keeps write access or moves to triage, once review responsibility is clear.
6. Enable private vulnerability reporting, then add a `SECURITY.md` that points to it. Do not publish a contact
   address or a response time the project has not committed to.
7. Choose and add a license (Apache-2.0 has been proposed but not approved). Record third-party terms for datasets,
   harness code, and model outputs separately.
8. Consider requiring SHA-pinned actions at the repository level, and pinning the actions in the existing legacy
   workflows (`ci.yml`, `research-tests.yml`, `board-unassign.yml`, `stage-bc-after-card.yml`), which use tags.

## Reporting a vulnerability

Until private vulnerability reporting is enabled, do not open a public issue for a suspected vulnerability. Contact
a repository admin privately and ask how to send details.
