import { Link } from "react-router";
import { PageTop } from "../components/PageTop";
import { benchmarkSuites } from "../features/leaderboard/suites";
export function BenchmarksPage() {
  return <><PageTop title="Benchmarks" description={<p>Initial legacy leaderboard views. Registry versions describe this UI, not an approved evaluation protocol.</p>} />
    <div className="suite-grid">{benchmarkSuites.map(s => <article className="panel" key={s.id}><span className="eyebrow">{s.id} · {s.version}</span><h2>{s.label}</h2><p>{s.summary}</p>
      <p>Primary: <strong>{s.primary.label}</strong> · {s.primary.unit} · {s.primary.direction === "desc" ? "higher" : "lower"} is better</p>
      <p>Secondary: {s.secondary.map(m => `${m.label} (${m.unit})`).join(", ")}</p><Link to={s.documentation}>Metric definitions and limitations →</Link>
    </article>)}</div>
    <aside className="panel"><h2>Protocol compatibility comes first</h2><p>Same metric names do not make measurements comparable. Inspect harness, dataset, checkpoint and scale revisions. More suites need reviewed definitions and contract changes, not another leaderboard page.</p></aside></>;
}
