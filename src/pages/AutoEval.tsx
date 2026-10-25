import { useState } from "react";
import { PageTop } from "../components/PageTop";
import { benchmarkSuites } from "../features/leaderboard/suites";
const phases = ["Pending", "Validating", "Loading model", "Evaluating", "Completed", "Failed"] as const;
export function AutoEvalPage() {
  const [example, setExample] = useState<typeof phases[number]>("Pending");
  return <><PageTop title="AutoEval" description={<p>Explore the intended submission workflow. AutoEval execution is not yet connected.</p>} />
    <div className="autoeval-grid"><section className="panel"><h2>1–4 · Describe a checkpoint</h2><p>Editable planning inputs only. Nothing is validated, uploaded or submitted.</p>
      <form onSubmit={e => e.preventDefault()}>
        <label>Hugging Face repository<input placeholder="owner/model" autoComplete="off" /></label>
        <label>Pinned model revision<input placeholder="Full immutable commit SHA" autoComplete="off" /></label>
        <label>Checkpoint selection<input placeholder="Exact checkpoint filename or artifact set" autoComplete="off" /></label>
        <label>Benchmark suite<select>{benchmarkSuites.map(s => <option key={s.id} value={s.id}>{s.label} · {s.version} (display fixture)</option>)}</select></label>
        <p id="execution-unavailable">Execution unavailable: no model inspection, validation, downloads or evaluation service is connected.</p>
        <button type="submit" disabled aria-describedby="execution-unavailable">Run evaluation — not connected</button>
      </form>
    </section><section className="panel"><span className="eyebrow">SYNTHETIC STATUS EXAMPLES</span><h2>5–7 · Validation, execution, results</h2>
      <label>Inspect an example state<select value={example} onChange={e => setExample(e.target.value as typeof example)}>{phases.map(p => <option key={p}>{p}</option>)}</select></label>
      <p role="status">Illustrative execution status: <strong>{example}</strong>. No job is running.</p>
      <p>Validation: unavailable · no repository has been inspected.</p><p>Progress: unavailable · no samples have been evaluated.</p>
      <p>Verification status: <strong>Unreviewed</strong> (illustrative). Awaiting review and Officially verified require a future authenticated review workflow.</p>
      <p>Results and provenance: unavailable. Completed in this example does not create a result or grant verification.</p>
      <details><summary>Logs and reproducibility</summary><p>Unavailable: this is a disconnected UI prototype. No execution logs or reproduction command exist.</p></details>
    </section></div></>;
}
