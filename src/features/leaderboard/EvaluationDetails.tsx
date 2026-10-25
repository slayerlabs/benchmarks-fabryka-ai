import type { BoardRow } from "../../contracts/leaderboard";
import { fixtureProvenance } from "../../fixtures/provenance";
import { checkpointDetails } from "./model-board-data";
const unavailable = (value: string | number | null | undefined) => value ?? "Unavailable";

export function EvaluationDetails({ row, suiteId }: { row: BoardRow; suiteId: string }) {
  const p = fixtureProvenance(row, suiteId);
  const facts = [
    ["Contract", p.schemaVersion], ["Evaluation ID", p.evaluationId],
    ["Benchmark suite", p.suite.id], ["Evaluation suite version", p.suite.version],
    ["Scorer version", p.scorer.version], ["Scorer Git SHA (fixture harness)", p.scorer.gitSha],
    ["Dataset ID / revision / SHA-256", p.datasets?.map(d => [d.id, d.revision, d.sha256].map(unavailable).join(" / ")).join("; ")],
    ["Model repository", p.model.repository], ["Pinned model revision", p.model.revision],
    ["Checkpoint label", p.checkpoint.label], ["Checkpoint SHA-256", p.checkpoint.sha256], ["Checkpoint step", p.checkpoint.step],
    ["Tokenizer revision", p.tokenizerRevision], ["Runtime device", p.runtime?.device], ["Numerical dtype", p.runtime?.dtype],
    ["Random seed", p.runtime?.seed], ["Runtime / numerical configuration", p.runtime?.configuration],
    ["Evaluation timestamp", p.evaluatedAt], ["Execution status", p.executionStatus],
    ["Verification status", p.verificationStatus], ["Scale revision", row.scale_rev], ["Evaluation harness", row.harness],
  ];
  return <details className="mb-model-details">
    <summary aria-label={`Details for ${row.name}`}>Details</summary>
    <section className="provenance" aria-label={`Evaluation details for ${row.name}`}>
      <h2>Evaluation provenance</h2>
      <p>Synthetic fixture only. Historical trust badges do not establish execution or official verification.</p>
      <p>{checkpointDetails(row)}</p>
      <dl>{facts.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{unavailable(value)}</dd></div>)}</dl>
      <details><summary>Logs and reproduction</summary><p>Logs: {unavailable(p.logs)}</p><p>Reproduction instructions: {unavailable(p.reproduction)}</p><p>No evaluation was executed to create this fixture.</p></details>
      {row.public_note && <p>{row.public_note}</p>}
    </section>
  </details>;
}
