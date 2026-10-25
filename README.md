# Fabryka Benchmarks

Phase 0: an isolated React 19 / TypeScript / Vite / React Router Model Leaderboard playground. All displayed models and measurements are explicitly labeled **synthetic test data**. No backend, credentials, production API, database, training jobs or deployment.

## Local development

Use Node 24 (see `.nvmrc`) and npm:

```sh
npm ci
npm run dev
```

Open the local Vite address printed by the command; the app routes to `/models`. No environment variables or external services are needed. Fixtures are bundled locally; no fetch occurs. All fonts and styles are local.

```sh
npm run check
npm run lint
npm test
npx playwright install chromium
npm run test:ui
npm run build
npm run preview
```

Unit tests use Node's built-in runner. Playwright exercises the actual UI and blocks nonlocal requests. Both use local fixtures only. CI runs checks, lint, tests and build on pull requests and main pushes; there is no deployment workflow. To reuse an installed Chromium locally, set CHROMIUM_PATH to its executable path when running npm run test:ui.

## Working together

Keep `main` stable. Create `feature/*`, `fix/*` or `experiment/*` branches and open a PR. Describe behavior, test results, screenshots for UI changes and any scoring/provenance impact. Request team review before merging. Never modify `slayerlabs/fabryka-track` or production infrastructure. Never configure production API access, credentials, SSH or autodeploy here.

See [architecture and source attribution](docs/architecture.md) for responsibilities, exact calculation semantics and the future read-only adapter boundary. See [AGENTS.md](AGENTS.md) for agent instructions.

