import { useState } from "react";
import { Link } from "react-router";
import { PageTop } from "../components/PageTop";
import { parseModelInput } from "../features/autoeval/model-input";

export function AutoEvalPage() {
  const [input, setInput] = useState("");
  const [repository, setRepository] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  return <><PageTop title="AutoEval" description={<p>Start with a Hugging Face model. AutoEval is intended to inspect the repository and resolve the technical details for you.</p>} />
    <section className="panel model-entry">
      <span className="eyebrow">ONE MODEL INPUT · FRONTEND PREVIEW</span>
      <h2>Which model would you like to evaluate?</h2>
      <form onSubmit={e => {
        e.preventDefault();
        const result = parseModelInput(input);
        setError(result.ok ? null : result.error);
        setRepository(result.ok ? result.repository : null);
      }}>
        <label htmlFor="model-input">Hugging Face model URL or repository ID</label>
        <div className="inspection-input"><input id="model-input" value={input} onChange={e => { setInput(e.target.value); setRepository(null); setError(null); }} placeholder="SlayerLab/GoLLeM-v6-250M" autoComplete="off" aria-describedby="inspection-boundary" aria-invalid={!!error} />
          <button className="primary-action" type="submit">Prepare inspection</button></div>
        <p id="inspection-boundary">Inspection is not connected. This action checks the input format locally only; it does not contact Hugging Face or start a job.</p>
        {error && <p role="alert">{error}</p>}
      </form>
      <p className="input-example">Accepts owner/model or https://huggingface.co/owner/model. No manual revision, checkpoint or runtime configuration is needed at this stage.</p>
      {repository && <div className="inspection-blocked" role="status"><strong>Repository format checked: {repository}</strong><p>Remote inspection unavailable. No revision has been resolved, no model has been validated, and no request was sent.</p><button disabled>Inspect model — service not connected</button></div>}
    </section>
    <div className="autoeval-grid"><section className="panel"><h2>Automatic inspection · intended workflow</h2>
      <ol className="workflow-list"><li>Resolve and pin a repository revision.</li><li>Inspect architecture, checkpoints and tokenizer artifacts.</li><li>Determine compatible benchmarks and resource requirements.</li><li>Select a supported checkpoint when unambiguous; ask only if a necessary choice remains.</li><li>Run through an isolated official runner and retain the result manifest.</li><li>Publish to the leaderboard only after eligibility and review gates pass.</li></ol>
      <p>These steps require a backend. None runs in this frontend.</p><Link to="/benchmarks">Explore individual benchmarks →</Link>
    </section><section className="panel"><h2>Inspection and evaluation evidence</h2>
      <dl className="inspection-facts"><div><dt>Requested repository</dt><dd>{repository ?? "Not provided"}</dd></div><div><dt>Pinned revision / checkpoint / tokenizer</dt><dd>Unavailable — remote inspection not connected</dd></div><div><dt>Compatible suites / resource validation</dt><dd>Unavailable — not inferred from the repository name</dd></div><div><dt>Submission source</dt><dd>AutoEval intent only — nothing submitted</dd></div><div><dt>Execution status</dt><dd>Unavailable — no evaluation exists</dd></div><div><dt>Verification status</dt><dd>Unavailable — no review exists</dd></div><div><dt>Results / manifest</dt><dd>Unavailable</dd></div></dl>
      <details><summary>Logs and reproducibility</summary><p>Unavailable: no execution occurred. Successful execution would not, by itself, establish official verification.</p></details>
      <Link to="/methodology#autoeval">How inspection and official scoring are intended to work →</Link>
    </section></div></>;
}
