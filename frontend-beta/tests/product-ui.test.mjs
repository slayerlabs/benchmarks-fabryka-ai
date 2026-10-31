import test from "node:test";
import assert from "node:assert/strict";
import { benchmarkSuites } from "../src/features/leaderboard/suites.ts";
import { fixtureProvenance } from "../src/fixtures/provenance.ts";
import { fixtureModels } from "../src/fixtures/models.ts";
import { NATURAL_DIRECTION } from "../src/features/leaderboard/model-board-data.ts";
import { parseModelInput } from "../src/features/autoeval/model-input.ts";
import { benchmarkCatalog, evaluationSuiteCatalog } from "../src/features/benchmarks/catalog.ts";

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
   assert.equal(p.schemaVersion, "fabryka.provenance-ui/2");
   assert.equal(p.source, "synthetic");
   assert.equal(p.checkpoint.sha256, row.checkpoint_sha256);
   assert.equal(p.model.revision, row.revision);
   assert.equal(p.evaluatedAt, row.evaluated_at);
   assert.equal(p.evaluationId, null);
   assert.equal(p.submissionSource, null);
   assert.equal(p.leaderboardCategory, "pl");
   assert.equal(p.suite.id, null);
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
test("AutoEval input parsing is local syntax checking, accepting only repository IDs and root HF URLs", () => {
 for (const value of ["SlayerLab/GoLLeM-v6-250M", "https://huggingface.co/SlayerLab/GoLLeM-v6-250M", " https://huggingface.co/SlayerLab/GoLLeM-v6-250M/ "]) {
   assert.deepEqual(parseModelInput(value), { ok: true, repository: "SlayerLab/GoLLeM-v6-250M" });
 }
 for (const value of ["", "just-a-name", "../model", "https://evil.example/owner/model", "https://huggingface.co.evil.example/owner/model", "https://user:pass@huggingface.co/owner/model", "https://huggingface.co/owner/model/tree/main", "https://huggingface.co/owner/model?revision=main", "https://huggingface.co/owner/model#part", "javascript:alert(1)", "http://huggingface.co/owner/model"]) {
   assert.equal(parseModelInput(value).ok, false, value);
 }
});
test("benchmark catalog distinguishes individual tests, real suites and leaderboard categories", () => {
 assert.equal(benchmarkCatalog.length, 7);
 assert.equal(new Set(benchmarkCatalog.map(b => b.id)).size, benchmarkCatalog.length);
 assert.ok(!benchmarkCatalog.some(b => ["en", "pl", "plen"].includes(b.id)));
 for (const b of benchmarkCatalog) assert.ok(b.purpose && b.task && b.metrics && b.protocol && b.evidence && b.code.startsWith("https://github.com/"));
 for (const suite of evaluationSuiteCatalog) for (const id of suite.components) assert.ok(benchmarkCatalog.some(b => b.id === id));
 assert.equal(benchmarkCatalog.find(b => b.id === "multiblimp-pl").dataset.revision, null);
 assert.equal(benchmarkCatalog.find(b => b.id === "blimp-en").dataset.license, null);
 assert.equal(benchmarkCatalog.find(b => b.id === "arc-easy-pl").dataset.revision, "f2e35fbebdb572a9653eda706b00083b0892ed43");
});
