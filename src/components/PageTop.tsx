import type { ReactNode } from "react";
export function PageTop({ description }: { description: ReactNode }) {
 return <header><span className="brand">FABRYKA / BENCHMARKS</span><p className="fixture-banner" role="note">DEVELOPMENT FIXTURES · All models, scores and provenance below are synthetic test data. No production connection.</p><h1>Model Leaderboard</h1>{description}</header>;
}

