# Phase 0: isolated Model Leaderboard developer foundation

## Change

Create a standalone React 19 / TypeScript / Vite / React Router leaderboard using synthetic, visibly labeled local fixtures. Adapt the reference /models table and controls; reuse the original pure ranking, filtering, sorting, Overall formula and provenance helpers. Preserve EN / PL / PL+EN, ties, missing values, trust distinctions, size buckets and scoring scales.

Separate contracts, fixture source adapter, fixtures, leaderboard UI/logic and shared header. Add PR CI, README, AGENTS.md and architecture/source attribution. No production API integration, authentication, backend, jobs, deployment or changes to fabryka-track.

## Validation

TypeScript, ESLint, 12 local unit tests, 2 Chromium interaction tests and production build passed locally. Browser tests block nonlocal requests and cover the actual fixture UI. GitHub Actions execution is pending an actual PR.

## Repository initialization

The supplied repository was empty and had no main branch. The feature history begins with an empty initialization commit, followed by Phase 0 implementation. A maintainer can establish main at that empty commit, then review the feature branch against it. No application implementation has been merged to main.

