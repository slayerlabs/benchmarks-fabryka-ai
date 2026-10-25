import test from "node:test";
import assert from "node:assert/strict";
import { benchmarkSuites } from "../src/features/leaderboard/suites.ts";
import { fixtureProvenance } from "../src/fixtures/provenance.ts";
import { fixtureModels } from "../src/fixtures/models.ts";
import { NATURAL_DIRECTION } from "../src/features/leaderboard/model-board-data.ts";

test("suite registry preserves legacy primary metrics, units and natural directions", () => {
 assert.deepEqual(benchmarkSuites.map(s => [s.id, s.primary.key]), [["en","en_eff"],["pl","pl_eff"],["plen","combined"]]);
 assert.equal(new Set(benchmarkSuites.map(s => s.id)).size, benchmarkSuites.length);
 for (const s of benchmarkSuites) {
   assert.ok(s.version && s.documentation.startsWith("/methodology#"));
   const metrics = [s.primary, ...s.secondary];
   assert.equal(new Set(metrics.map(m => m.key)).size, metrics.length);
   for (const m of metrics) {
     assert.equal(m.direction, NATURAL_DIRECTION[m.key]);
     assert.ok(["score","%","byte-PPL"].includes(m.unit));
   }
 }
});
test("provenance adapter preserves available fixture facts without manufacturing missing evidence", () => {
 for (const row of fixtureModels) {
   const p = fixtureProvenance(row, "pl");
   assert.equal(p.schemaVersion, "fabryka.provenance-ui/1");
   assert.equal(p.source, "synthetic");
   assert.equal(p.checkpoint.sha256, row.checkpoint_sha256);
   assert.equal(p.model.revision, row.revision);
   assert.equal(p.evaluatedAt, row.evaluated_at);
   assert.equal(p.evaluationId, null);
   assert.equal(p.suite.version, null);
   assert.equal(p.datasets, null);
   assert.equal(p.runtime, null);
   assert.equal(p.tokenizerRevision, null);
   assert.equal(p.logs, null);
   assert.equal(p.reproduction, null);
   assert.equal(p.executionStatus, null);
   assert.equal(p.verificationStatus, null);
 }
});
