# Fabryka Benchmarks agent instructions

- Work only in this repository. Never modify slayerlabs/fabryka-track, including the reference checkout.
- Production is out of bounds: no production APIs, database, credentials, SSH, deployment, training or benchmark jobs. Tests must never call external services.
- Stack: React 19, TypeScript strict, Vite, React Router; keep dependencies minimal. UI copy is English.
- Architecture: src/components is shared UI; src/features/leaderboard contains the page and pure ranking/filter/sort helpers; src/contracts defines the published row contract; src/data provides the read-only source interface and fixture adapter; src/fixtures is synthetic test data; tests contains local unit and UI tests.
- Use Node 24. Commands: npm ci; npm run dev; npm run check; npm run lint; npm test; npm run build.
- Before a PR run check, lint, test and build. Test missing values, ties, category membership, size boundaries, trust and scoring whenever affected. Preserve source calculation semantics; never impute missing scores or grant trust in the client.
- Use feature/*, fix/* or experiment/* branches. Keep PRs small; explain behavior, checks and screenshots for UI changes. Do not merge or deploy without explicit authorization.
- Each cloud task is isolated: use the existing checkout; do not create a worktree unless requested.
- Routes share components/AppLayout; pages contains AutoEval, Benchmarks and Methodology. features/leaderboard/suites.ts is the display registry, not an approved protocol registry. Keep scoring helpers unchanged in UI-only tasks.
- contracts/evaluation.ts versions the frontend provenance display; unknown evidence is null/Unavailable. Never derive execution or verification status from a legacy trust badge. AutoEval is disconnected: no submit, inspection or model download may be implied to work.
- Run browser tests with npm run test:ui (install Chromium with npx playwright install chromium, or use CHROMIUM_PATH for an existing executable). All routes must keep synthetic-data notices and tests must block external requests.
