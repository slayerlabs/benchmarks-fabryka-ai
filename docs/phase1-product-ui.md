# Phase 1 — Product UI foundation

This is a frontend-only iteration stacked on `feature/phase-0-foundation`. Remote `main` was verified at the empty bootstrap commit d663389 when work started; it is not a usable application base. Review this branch against Phase 0. Merge Phase 0 first, then retarget this PR to main and re-run CI before considering a merge. No merge is authorized here.

## Run and verify

Use Node 24 and the existing lockfile:

```sh
npm ci
npm run dev
npm run check
npm run lint
npm test
npx playwright install chromium
npm run test:ui
npm run build
```

A local installed browser can be reused with `CHROMIUM_PATH=/usr/bin/chromium npm run test:ui`. Stop other servers on port 4173 before running the browser tests. Their Vite server uses that port. A cloud workspace can use `npm run dev -- --host 0.0.0.0 --port 4173 --strictPort`, but this does not create a public tunnel or guarantee Codex panel availability.

## Routes and responsibilities

- `/models`: legacy fixture leaderboard, primary metric immediately after identity; secondary metrics are opt-in. EN Overall remains an alternate ranking axis. Filters, stable sorts, missing values and competition ranks are unchanged.
- `/autoeval`: editable planning form and explicitly synthetic execution-state examples. Run is disabled. No repository inspection, validation, submission, downloads, jobs or result publication occurs.
- `/benchmarks`: typed suite catalog with metric units/directions and methodology links.
- `/methodology`: established historical formulas, limitations, trust, identity, reproducibility and future plans. The draft fabryka.scoring/1.0 proposal is not presented as approved.
- `components/AppLayout.tsx`: responsive navigation, shared fixture notice, route focus and footer.
- `features/leaderboard/suites.ts`: display configuration for existing EN/PL/PL+EN views. Its legacy-display-v1 version is not an evaluation protocol or proof of compatibility. New views over the supported row metrics can reuse this page; new metric fields require explicit contract/helper/test extensions.
- `contracts/evaluation.ts`: versioned provenance UI contract, distinct execution and verification status fields.
- `fixtures/provenance.ts`: maps existing synthetic facts only; missing evidence stays null and is shown as Unavailable. Run ID is not repurposed as an invented evaluation ID. No trust-to-verification inference.
- `EvaluationDetails.tsx`: keyboard-operable row details with model/checkpoint, dataset, tokenizer, runtime, timestamp, status and logs/reproduction fields.

Scoring/ranking helpers, original BoardRow contract and fixture scores remain byte-for-byte unchanged. No new dependencies, backend, API adapter, protocol implementation or deployment configuration was added. Legacy rows still rank within the existing selected view; the UI explicitly labels their scales and warns that compatibility is unverified. It does not claim scientific comparability merely because rows share a table.

## Review evidence

14 unit assertions/tests cover the existing scoring/display behavior plus registry/provenance configuration. Six Playwright tests cover actual fixture rendering, unchanged sorting/ranking, primary metric order, optional secondary metrics, navigation/direct routing, missing provenance and disconnected AutoEval states. Browser tests reject nonlocal HTTP requests.

Screenshots captured from the built application:

- [Desktop leaderboard](screenshots/phase1-leaderboard-desktop.png)
- [Mobile leaderboard](screenshots/phase1-leaderboard-mobile.png)
- [Desktop AutoEval](screenshots/phase1-autoeval-desktop.png)
- [Mobile AutoEval](screenshots/phase1-autoeval-mobile.png)

Horizontal table scrolling stays inside a labeled, keyboard-focusable results region; navigation and forms fit narrow screens. No avatar, automatic submission countdown or decorative debug panel is included.

## Not implemented

Canonical evaluation package, live data, protocol compatibility enforcement, authentication, worker isolation, job orchestration, GPU access and official verification are future work. Unknown provenance cannot be “filled in” to make the panel appear complete. Prototype status selection never creates a measured result.

Architecture RFCs and scoring compatibility work already present in this workspace are separate review artifacts, not prerequisites implemented by this UI PR. Production Track remains untouched.
