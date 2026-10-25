import test from "node:test";
import assert from "node:assert/strict";
import { fixtureModels } from "../src/fixtures/models.ts";
import { fixtureSource } from "../src/data/fixture-source.ts";
import { TRUST_LABELS } from "../src/features/leaderboard/model-board-data.ts";
test("fixtures represent consistent published combined/category semantics and all trust labels", () => {
 assert.equal(new Set(fixtureModels.map(r => r.run_id)).size, fixtureModels.length);
 assert.deepEqual(new Set(fixtureModels.map(r => r.trust)), new Set(["verified", "measured", "reported", "track"]));
 assert.deepEqual(TRUST_LABELS, { verified: "verified ✓", measured: "measured by Fabryka", reported: "self-reported", track: "measured by track" });
 for (const row of fixtureModels) {
  assert.match(row.name, /TEST DATA/);
  const both = row.categories.includes("en") && row.categories.includes("pl") && Number.isFinite(row.en.eff) && Number.isFinite(row.pl.eff);
  assert.equal(row.categories.includes("plen"), both);
  assert.equal(row.combined, both ? (row.en.eff + row.pl.eff) / 2 : null);
 }
});
test("fixture adapter returns isolated snapshots without external services", async () => {
 const first = await fixtureSource.load();
 first.models[0].en.eff = -1;
 assert.equal((await fixtureSource.load()).models[0].en.eff, 55);
 assert.equal(fixtureModels[0].en.eff, 55);
});

