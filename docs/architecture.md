# Phase 0 architecture and reference

Inspected reference: slayerlabs/fabryka-track commit 73026f45a5350b15e006c15d4341805a73f568e4. Read ModelBoard.tsx, model-board-data.ts, App.tsx, frontend/package.json, model_board.py, docs/model-board.md and tests/model-board.test.mjs. Only the leaderboard UI, pure helpers, formatting and helper tests are reused/adapted. No Track providers, application shell, auth, run detail, comparison page or backend are included. The reference checkout is unchanged. Source attribution is retained here; no license for the original code was present in the inspected root, so this repository does not assert a new license over that code.

## Responsibilities

- components/PageTop: standalone heading and persistent test-data notice.
- features/leaderboard/ModelBoard: reference table, language/size/trust/axis controls, sorting, loading/error/empty states; narrow paper/orange palette and table presentation adapted from the reference CSS.
- contracts/leaderboard: BoardRow and sort/filter contracts.
- features/leaderboard/model-board-data: original pure calculations, with only type imports relocated. Existing tests are adapted only to the new import path.
- data/source: asynchronous read-only load() returning { models: BoardRow[] }; data/fixture-source is the only active implementation. A fresh clone prevents fixture mutation across loads.
- fixtures/models: six explicitly synthetic rows: all trust levels, bilingual ties, category-only rows, missing measurements/provenance and each parameter bucket.

## Preserved semantics

EN ranks by published eff by default; Overall is an optional EN axis. Overall = (BLiMP + ARC-Easy + wikiScore) / 3. wikiScore = 100 × clamp(1 − ln(min(PPL, 500) / 1.86) / ln(500 / 1.86), 0, 1). Any missing/nonfinite input makes Overall null. This is the only score calculated by the browser.

PL ranks by supplied eff-PL. Missing eff-PL stays unranked and follows ranked rows by MultiBLiMP-pl descending. PL+EN uses supplied combined; the server contract defines it as (eff EN + eff-PL)/2 only when both categories and both finite effs exist. Client category filtering trusts supplied membership; it never invents membership or imputes metrics.

Ranks are competition ranks (1, 1, 3), calculated within the current category/size/trust filter and independent of display sorting. Ties preserve input order; null/nonfinite values sort last in either direction. Size buckets are disjoint, decimal millions, inclusive upper bounds at 16, 32, 64, 150 and 350M. Perplexities naturally sort ascending; scores descending.

Trust is a source-granted distinction: verified, measured by Fabryka, self-reported, measured by track. The client does not grant trust. A dagger appears only on nonmissing PL/combined measurements of external models with measured trust, never self-reported. Harness, scale revision, checkpoint SHA, HF revision, owner/author, evaluation date, result step and public note remain available in Details. Compare eff only within the same scale revision: Track Tiny-ML and Glint eff are different formulas/scales.

## Future independent source

Implement LeaderboardSource and pass it to ModelBoardPage. Validate untrusted responses at that boundary before use. Require a separately reviewed, explicitly configured independent read-only origin; do not default to Track or add a production proxy. No HTTP adapter or environment toggle pretending to work exists in Phase 0.

The original anonymous endpoint contract is GET /api/leaderboard/models → { models: BoardRow[] }. Public visibility, owner opt-in, exact result-step lookup, checkpoint deduplication, latest qualifying evaluation, matching checkpoint across languages, parameter counting, score calibration and trust grants belong to the source/backend. They cannot be reproduced or verified against production safely here. Fixtures model the published result, not those server operations. No production calls were made. HF metadata in fixtures is synthetic and has no active outbound link.

