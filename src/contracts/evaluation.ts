/** Frontend display contract, not the proposed canonical scoring standard. */
export interface EvaluationProvenanceV1 {
  schemaVersion: "fabryka.provenance-ui/1";
  source: "synthetic";
  evaluationId: string | null;
  suite: { id: string; version: string | null };
  scorer: { version: string | null; gitSha: string | null };
  datasets: { id: string; revision: string | null; sha256: string | null }[] | null;
  model: { repository: string | null; revision: string | null };
  checkpoint: { label: string | null; sha256: string | null; step: number | null };
  tokenizerRevision: string | null;
  runtime: { device: string | null; dtype: string | null; seed: number | null; configuration: string | null } | null;
  evaluatedAt: string | null;
  executionStatus: "pending" | "validating" | "loading_model" | "evaluating" | "completed" | "failed" | "cancelled" | null;
  verificationStatus: "unreviewed" | "self_reported" | "awaiting_review" | "officially_verified" | null;
  logs: string | null;
  reproduction: string | null;
}

/** v2 separates submission attribution and leaderboard categories from measured suites. */
export interface EvaluationProvenanceV2 extends Omit<EvaluationProvenanceV1, "schemaVersion" | "suite" | "verificationStatus"> {
  schemaVersion: "fabryka.provenance-ui/2";
  submissionSource: "autoeval" | "imported" | "manually_reported" | null;
  leaderboardCategory: string;
  suite: { id: string | null; version: string | null };
  verificationStatus: "unreviewed" | "reviewed" | "awaiting_review" | "officially_verified" | null;
}
