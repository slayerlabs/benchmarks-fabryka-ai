import type { BoardRow } from "../contracts/leaderboard.ts";
import type { EvaluationProvenanceV2 } from "../contracts/evaluation.ts";

/** Preserve only facts already present in a synthetic row. Never infer execution or review from its trust badge. */
export function fixtureProvenance(row: BoardRow, suiteId: string): EvaluationProvenanceV2 {
  return {
    schemaVersion: "fabryka.provenance-ui/2", source: "synthetic",
    submissionSource: null, leaderboardCategory: suiteId,
    evaluationId: null, suite: { id: null, version: null },
    scorer: { version: null, gitSha: row.harness_sha }, datasets: null,
    model: { repository: row.hf_repo, revision: row.revision },
    checkpoint: { label: row.label, sha256: row.checkpoint_sha256, step: row.step },
    tokenizerRevision: null, runtime: null, evaluatedAt: row.evaluated_at,
    executionStatus: null, verificationStatus: null, logs: null, reproduction: null,
  };
}
