import type { BoardRow } from "../contracts/leaderboard.ts";
// Synthetic examples of already-published rows, NOT measured models or granted real trust.
const base: BoardRow = {
 run_id: "fixture-a", name: "TEST DATA · Bilingual 16M", owner: "fixture-team", kind: "track", trust: "verified", author: null,
 hf_repo: null, revision: null, hf_url: null, n_params: 16_000_000, tokens_seen: 320_000_000,
 checkpoint_sha256: "a".repeat(64), harness: "TEST protocol", harness_sha: "1234567", scale_rev: "TEST Glint scale A",
 step: 1000, label: "final checkpoint (result)", evaluated_at: null, started_at: "2026-10-01T00:00:00Z", finished_at: "2026-10-02T00:00:00Z",
 public_note: "Synthetic test data. No actual benchmark was run.", categories: ["en", "pl", "plen"],
 en: { eff: 55, arc_easy: 45, blimp: 70, wiki_byte_ppl: 3 },
 pl: { eff: 45, multiblimp: 65, arc_easy: 40, byte_ppl: 3.5 }, combined: 50,
};
export const fixtureModels: BoardRow[] = [
 base,
 { ...base, run_id: "fixture-b", name: "TEST DATA · External tie 32M", n_params: 32_000_000, kind: "external", trust: "measured", author: "Fixture authors", hf_repo: "example/test-model", revision: "1234567", checkpoint_sha256: "b".repeat(64) },
 { ...base, run_id: "fixture-c", name: "TEST DATA · Self-reported 64M", n_params: 64_000_000, trust: "reported", checkpoint_sha256: "c".repeat(64), en: { ...base.en, eff: 40 }, combined: 42.5 },
 { ...base, run_id: "fixture-d", name: "TEST DATA · Track PL only 150M", n_params: 150_000_000, trust: "track", categories: ["pl"], en: { eff: null, arc_easy: null, blimp: null, wiki_byte_ppl: null }, pl: { eff: null, multiblimp: 72, arc_easy: null, byte_ppl: null }, combined: null, checkpoint_sha256: null, step: null, tokens_seen: null, label: "latest server evaluation", evaluated_at: "2026-10-03T00:00:00Z", harness_sha: null, scale_rev: null },
 { ...base, run_id: "fixture-e", name: "TEST DATA · EN only 350M", n_params: 350_000_000, trust: "measured", categories: ["en"], pl: { eff: null, multiblimp: null, arc_easy: null, byte_ppl: null }, combined: null, checkpoint_sha256: "e".repeat(64), en: { ...base.en, eff: 30 } },
 { ...base, run_id: "fixture-f", name: "TEST DATA · Partial PL >350M", n_params: 350_000_001, trust: "reported", categories: ["pl"], en: { eff: null, arc_easy: null, blimp: null, wiki_byte_ppl: null }, pl: { eff: null, multiblimp: 60, arc_easy: null, byte_ppl: null }, combined: null, checkpoint_sha256: "f".repeat(64) },
];

