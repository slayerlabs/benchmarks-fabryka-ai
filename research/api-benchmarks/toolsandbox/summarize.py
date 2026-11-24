"""Merges the per-scenario results of one or more run directories into results/<model>.json and .jsonl.gz.

python summarize.py <model-id> <run-dir> [<run-dir> ...] [--usage usage.jsonl]

A later run directory (the rerun of infrastructure errors) replaces a scenario's record only when the earlier one was an
InfraError. Infrastructure errors that remain are excluded from n and score and listed in the result; every other
exception is scored 0, as the harness does. stderr = sample sd of similarity / sqrt(n), x 100.
"""
import argparse
import datetime
import glob
import gzip
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "c8571d7854316d2e1c5f288e59fe1e34e53f6dd1"


def load(rundir):
    d = rundir if (Path(rundir) / "progress.jsonl").exists() else sorted(glob.glob(str(Path(rundir) / "agent_*")))[-1]
    recs = {}
    for line in open(Path(d) / "progress.jsonl"):
        r = json.loads(line)
        r["_dir"] = str(d)
        recs[r["name"]] = r
    return recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--usage")
    ap.add_argument("--out", default=str(HERE / "results"))
    a = ap.parse_args()
    final = {}
    for run in a.runs:
        for name, r in load(run).items():
            if name not in final or final[name]["exception_type"] == "InfraError":
                final[name] = r
    exclude = {l.strip() for l in open(HERE / "rapid_api_scenarios.txt") if l.strip()}
    assert not (set(final) & exclude), "an excluded RapidAPI scenario was run"
    assert len(final) == 1032 - len(exclude), f"expected {1032 - len(exclude)} scenarios, got {len(final)}"
    infra = sorted(n for n, r in final.items() if r["exception_type"] == "InfraError")
    scored = {n: r for n, r in final.items() if n not in infra}
    sims = [r["similarity"] for r in scored.values()]
    n = len(sims)
    mean = sum(sims) / n
    sd = math.sqrt(sum((s - mean) ** 2 for s in sims) / (n - 1))
    other_exc = {}
    for r in scored.values():
        if r["exception_type"]:
            other_exc[r["exception_type"]] = other_exc.get(r["exception_type"], 0) + 1
    cats = {}
    for r in scored.values():
        for c in r["categories"]:
            cats.setdefault(c, []).append(r["similarity"])
    cost = None
    if a.usage and Path(a.usage).exists():
        u = [json.loads(l) for l in open(a.usage) if l.strip()]
        us = [x for x in u if x["role"] == "user"]
        cost = {"simulator_calls": len(us), "simulator_prompt_tokens": sum(x["prompt"] for x in us),
                "simulator_completion_tokens": sum(x["completion"] for x in us),
                "simulator_usd": round(sum(x["prompt"] * 0.10 + x["completion"] * 0.50 for x in us) / 1e6, 4),
                "agent_calls": len(u) - len(us)}
    out = {
        "benchmark": "ToolSandbox", "model": a.model, "metric": "mean_similarity",
        "score": round(mean * 100, 2), "stderr": round(sd / math.sqrt(n) * 100, 2), "n": n,
        "date": datetime.date.today().isoformat(),
        "harness": f"https://github.com/apple/ToolSandbox @ {COMMIT}",
        "data": f"scenarios of the harness (code), default tool backend: 1032 in total, {len(exclude)} needing RAPID_API_KEY excluded",
        "settings": {"temperature": 0, "max_tokens_per_turn": 1024, "max_messages_per_scenario": 30, "trials": 1,
                     "parallel_scenarios": 2,
                     "user_simulator": "claude-haiku-5-5 via https://api.anthropic.com/v1/ (OpenAI-compatible), "
                                       "no temperature or top_p sent"},
        "scenarios_total": 1032, "scenarios_excluded_rapid_api": len(exclude), "scenarios_run": len(final),
        "infrastructure_errors": len(infra), "infrastructure_error_scenarios": infra,
        "scored_exceptions_by_type": other_exc,
        "category_scores": {c: round(sum(v) / len(v) * 100, 2) for c, v in sorted(cats.items())},
        "cost": cost,
        "deviations": "see README.md, Deviations",
    }
    res = Path(a.out)
    res.mkdir(exist_ok=True)
    (res / f"{a.model}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    with gzip.open(res / f"{a.model}.jsonl.gz", "wt", encoding="utf-8") as f:
        for name in sorted(final):
            r = final[name]
            conv = Path(r["_dir"]) / "trajectories" / name / "conversation.json"
            msgs = json.loads(conv.read_text()) if conv.exists() else None
            f.write(json.dumps({"task_id": name, "categories": r["categories"], "score": r["similarity"],
                                "milestone_similarity": r["milestone_similarity"],
                                "minefield_similarity": r["minefield_similarity"], "turn_count": r["turn_count"],
                                "error_type": r["exception_type"], "infrastructure_error": name in infra,
                                "output": msgs}, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: out[k] for k in ("score", "stderr", "n", "infrastructure_errors", "scored_exceptions_by_type")}))


if __name__ == "__main__":
    sys.exit(main())
