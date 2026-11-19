# Security and governance

How v2 work is reviewed, what the automation can and cannot do, and which repository settings still need a
maintainer with admin rights. The settings below were read from the GitHub API on 2026-11-19 and can change; check
them again before relying on them.

## Trust boundary

Everything that runs on a pull request in this public repository is treated as untrusted, including the PR title,
description, branch name, and changed files.

- **Public PR CI** (`CodeSOTA CI`, `PR policy`) runs on the `pull_request` event. For PRs from forks, GitHub gives
  these workflows a read-only token and no repository secrets. The workflows declare `permissions: {}` at the top
  and grant each job only what it needs (`contents: read`, and `pull-requests: read` for the job that lists changed
  files). They never use `pull_request_target`.
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

A PR can change the workflow files and scripts that check it, because `pull_request` runs the PR's version. Those
checks are therefore a convenience for contributors, not a security control. The control is human review of changes
under `.github/`.

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

## Manual steps for an admin

None of these is done by the foundation PR; each needs an explicit decision.

1. Add members to `benchmark-reviewers`. With one member, requiring code owner review would make that person a
   bottleneck for every v2 PR.
2. Create a core maintainers team (and, if wanted, a security team) with write access, then add owners for
   `/.github/`, `/.github/CODEOWNERS`, and core v2 paths to `CODEOWNERS` in a reviewed PR.
3. In `Protect main`, enable "Require review from Code Owners" only after steps 1 and 2.
4. After `PR policy` and `CodeSOTA CI` have run successfully on real PRs, consider adding them as required status
   checks: the check names are `PR policy` and `CodeSOTA CI`. Both report on every PR (CodeSOTA CI reports success
   without running its tests when a PR does not touch `benchmarks/`), so requiring them does not leave unrelated PRs
   pending.
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
