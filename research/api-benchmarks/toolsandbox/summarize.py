"""Merges the per-scenario results of one or more run directories into results/<model>.json and .jsonl.gz.

python summarize.py <model-id> <run-dir> [<run-dir> ...] [--usage usage.jsonl]   # write results/
python summarize.py <model-id> --check                                           # recompute from results/<model>.jsonl.gz

A later run directory (the rerun of infrastructure errors) replaces a scenario's record only when the earlier one was an
InfraError; that scenario carries `rerun_after_infra_error: true` in the per-item file. Infrastructure errors that remain
are excluded from n and score and listed in the result; every other exception is scored 0, as the harness does.

Statistics (all from the per-item file, `compute()`):
- `stderr` is the SE clustered by base scenario: the 8 variants of a base scenario (no distraction tools, 3 and 10
  distraction tools, all tools, four scrambled variants) share one task and are correlated. SE = sqrt(k/(k-1) *
  sum_c (sum_{i in c} (x_i - mean))^2) / n, the same formula as `klastrowe_wazone` in research/tools/statystyka.py;
  with 8 variants in every base it equals sd(base means) / sqrt(k). `stderr_independent` = sample sd / sqrt(n), the
  harness-style SE that treats the n scenarios as independent; it is too small. Other correlations (related bases such as
  `_alt` variants) are not modelled.
- `--check` fails when results/<model>.json disagrees with the per-item file.
"""
import argparse
import datetime
import glob
import gzip
import io
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "c8571d7854316d2e1c5f288e59fe1e34e53f6dd1"
AGENT_ENDPOINT = "https://fabryka.ai/v1"
USER_ENDPOINT = "https://api.anthropic.com/v1/"
SUFFIXES = ["_3_distraction_tools_arg_description_scrambled", "_3_distraction_tools_arg_type_scrambled",
            "_3_distraction_tools_tool_description_scrambled", "_3_distraction_tools_tool_name_scrambled",
            "_10_distraction_tools", "_3_distraction_tools", "_all_tools"]
POLISH = re.compile("[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")


def base_of(name):
    for s in SUFFIXES:
        if name.endswith(s):
            return name[: -len(s)]
    return name


def clustered(items):
    """items: [(cluster, x)] -> (mean, SE independent, SE clustered, n, k), all on the 0-1 scale."""
    n = len(items)
    mean = sum(x for _, x in items) / n
    sums = {}
    for c, x in items:
        sums[c] = sums.get(c, 0.0) + (x - mean)
    k = len(sums)
    se_iid = math.sqrt(sum((x - mean) ** 2 for _, x in items) / (n - 1)) / math.sqrt(n)
    se_c = math.sqrt(k / (k - 1) * sum(v * v for v in sums.values())) / n if k > 1 else None
    return mean, se_iid, se_c, n, k


def r2(x):
    return None if x is None else round(x * 100, 2)


def kept_bases():
    out = {}
    for line in open(HERE / "rapid_api_kept_bases.txt"):
        if line.strip() and not line.startswith("#"):
            b, tool, is_rapid = line.rstrip("\n").split("\t")
            out[b] = is_rapid == "yes"
    return out


def texts(row, role):
    return [m["content"] for m in (row["output"] or []) if m.get("role") == role and isinstance(m.get("content"), str)
            and m["content"].strip()]


def compute(rows):
    """Everything derived from the per-item rows. Returns the JSON fields that depend only on them."""
    scored = [r for r in rows if not r["infrastructure_error"]]
    bases = {}
    for r in scored:
        bases.setdefault(r["base_scenario"], []).append(r)
    assert all(len(v) == 8 for v in bases.values()), "every base scenario must have its 8 variants scored"
    items = [(r["base_scenario"], r["score"]) for r in scored]
    mean, se_iid, se_c, n, k = clustered(items)
    cats = {}
    for r in scored:
        for c in r["categories"]:
            cats.setdefault(c, []).append((r["base_scenario"], r["score"]))
    cat = {c: clustered(v) for c, v in sorted(cats.items())}
    kept = kept_bases()
    sens = {}
    for label, drop in (("without_80_kept_insufficient_information_scenarios", set(kept)),
                        ("without_32_kept_where_minefield_is_not_a_rapid_tool", {b for b, rp in kept.items() if not rp})):
        sub = [(r["base_scenario"], r["score"]) for r in scored if r["base_scenario"] not in drop]
        m, _, s, nn, kk = clustered(sub)
        sens[label] = {"score": r2(m), "stderr": r2(s), "n": nn, "clusters": kk}
    sub = [(r["base_scenario"], r["score"]) for r in scored if "INSUFFICIENT_INFORMATION" not in r["categories"]]
    m, _, s, nn, kk = clustered(sub)
    sens["outside_the_insufficient_information_category"] = {"score": r2(m), "stderr": r2(s), "n": nn, "clusters": kk}
    sens["kept_80_scenarios_scoring_1"] = sum(1 for r in scored if r["base_scenario"] in kept and r["score"] == 1)
    exc = {}
    for r in scored:
        if r["error_type"]:
            exc[r["error_type"]] = exc.get(r["error_type"], 0) + 1
    with_t = [r for r in scored if r["output"]]
    amsgs = [t for r in with_t for t in texts(r, "assistant")]
    rapid_err = sorted({r["task_id"] for r in scored for m in (r["output"] or [])
                        if m.get("role") == "tool" and "RAPID_API_KEY" in str(m.get("content"))})
    return {
        "score": r2(mean), "stderr": r2(se_c), "n": n,
        "other_metrics": {
            "stderr_independent": r2(se_iid), "clusters": k, "scenarios_per_cluster": 8,
            "sensitivity_to_kept_rapid_api_scenarios": sens,
            "scenarios_with_rapid_api_key_error_text": rapid_err,
            "polish_replies": {
                "heuristic": "assistant text messages containing a Polish diacritic (ą ć ę ł ń ó ś ź ż)",
                "scenarios_with_transcript": len(with_t),
                "scenarios_with_a_polish_diacritic_in_an_assistant_message": sum(
                    1 for r in with_t if any(POLISH.search(t) for t in texts(r, "assistant"))),
                "scenarios_with_two_or_more_diacritics_in_one_assistant_message": sum(
                    1 for r in with_t if any(len(POLISH.findall(t)) >= 2 for t in texts(r, "assistant"))),
                "assistant_text_messages": len(amsgs),
                "assistant_text_messages_with_a_diacritic": sum(1 for t in amsgs if POLISH.search(t)),
                "scenarios_with_a_diacritic_in_a_simulator_message": sum(
                    1 for r in with_t if any(POLISH.search(t) for t in texts(r, "user")))},
        },
        "category_scores": {c: r2(v[0]) for c, v in cat.items()},
        "category_stderr_clustered": {c: r2(v[2]) for c, v in cat.items()},
        "category_n": {c: v[3] for c, v in cat.items()},
        "category_clusters": {c: v[4] for c, v in cat.items()},
        "scored_exceptions_by_type": exc,
        "infrastructure_errors": len(rows) - len(scored),
        "infrastructure_error_scenarios": sorted(r["task_id"] for r in rows if r["infrastructure_error"]),
        "scenarios_rerun_after_infra_error": sorted(r["task_id"] for r in rows if r.get("rerun_after_infra_error")),
    }


def load(rundir):
    d = rundir if (Path(rundir) / "progress.jsonl").exists() else sorted(glob.glob(str(Path(rundir) / "agent_*")))[-1]
    recs = {}
    for line in open(Path(d) / "progress.jsonl"):
        r = json.loads(line)
        r["_dir"] = str(d)
        recs[r["name"]] = r
    return recs


def read_rows(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f]


def check(model, res):
    rows = read_rows(res / f"{model}.jsonl.gz")
    committed = json.loads((res / f"{model}.json").read_text())
    want = compute(rows)
    bad = [k for k in want if committed.get(k) != want[k] and k != "other_metrics"]
    bad += [f"other_metrics.{k}" for k in want["other_metrics"]
            if committed.get("other_metrics", {}).get(k) != want["other_metrics"][k]]
    for k in bad:
        print("MISMATCH", k)
    print(f"{model}: {len(rows)} rows, score {want['score']} stderr {want['stderr']} (independent "
          f"{want['other_metrics']['stderr_independent']}), n {want['n']}, "
          + ("consistent with the committed JSON" if not bad else f"{len(bad)} mismatches"))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("runs", nargs="*")
    ap.add_argument("--usage")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=str(HERE / "results"))
    a = ap.parse_args()
    res = Path(a.out)
    if a.check:
        return check(a.model, res)
    assert a.runs, "give at least one run directory"
    final, rerun = {}, set()
    for run in a.runs:
        for name, r in load(run).items():
            if name not in final:
                final[name] = r
            elif final[name]["exception_type"] == "InfraError":
                final[name] = r
                rerun.add(name)
    exclude = {l.strip() for l in open(HERE / "rapid_api_scenarios.txt") if l.strip()}
    assert not (set(final) & exclude), "an excluded RapidAPI scenario was run"
    assert len(final) == 1032 - len(exclude), f"expected {1032 - len(exclude)} scenarios, got {len(final)}"
    infra = {n for n, r in final.items() if r["exception_type"] == "InfraError"}
    rows = []
    for name in sorted(final):
        r = final[name]
        conv = Path(r["_dir"]) / "trajectories" / name / "conversation.json"
        tb = [l for l in (r.get("traceback") or "").splitlines() if l.strip()]
        rows.append({"task_id": name, "base_scenario": base_of(name), "categories": r["categories"],
                     "score": r["similarity"], "milestone_similarity": r["milestone_similarity"],
                     "minefield_similarity": r["minefield_similarity"], "turn_count": r["turn_count"],
                     "error_type": r["exception_type"], "error_message": tb[-1][:500] if tb else None,
                     "infrastructure_error": name in infra, "rerun_after_infra_error": name in rerun,
                     "output": json.loads(conv.read_text()) if conv.exists() else None})
    # the run directory is named agent_<agent>_user_<simulator>_<MM>_<DD>_<YYYY>_<time>
    m = re.match(r"agent_(.+)_user_(.+)_(\d\d)_(\d\d)_(\d{4})_", Path(final[sorted(final)[0]]["_dir"]).name)
    agent_model, user_model = m.group(1), m.group(2)
    date = f"{m.group(5)}-{m.group(3)}-{m.group(4)}"
    cost = None
    if a.usage and Path(a.usage).exists():
        u = [json.loads(l) for l in open(a.usage) if l.strip()]
        us = [x for x in u if x["role"] == "user"]
        cost = {"simulator_calls": len(us), "simulator_prompt_tokens": sum(x["prompt"] for x in us),
                "simulator_completion_tokens": sum(x["completion"] for x in us),
                "simulator_usd": round(sum(x["prompt"] * 0.10 + x["completion"] * 0.50 for x in us) / 1e6, 4),
                "agent_calls": len(u) - len(us)}
    d = compute(rows)
    out = {
        "benchmark": "ToolSandbox", "model": a.model,
        "metric": "mean similarity x 100, SE clustered by base scenario",
        "score": d["score"], "stderr": d["stderr"], "n": d["n"], "date": date,
        "harness": f"https://github.com/apple/ToolSandbox @ {COMMIT}",
        "data": f"scenarios of the harness (code), default tool backend: 1032 in total, {len(exclude)} needing "
                f"RAPID_API_KEY excluded",
        "settings": {"agent": f"{agent_model} via {AGENT_ENDPOINT} (OpenAI-compatible, native `tools` parameter)",
                     "user_simulator": f"{user_model} via {USER_ENDPOINT} (OpenAI-compatible), no temperature or top_p "
                                       f"sent",
                     "temperature": 0, "max_tokens_per_turn": 1024, "max_messages_per_scenario": 30, "trials": 1,
                     "parallel_scenarios": 2, "tool_backend": "DEFAULT"},
        "scenarios_total": 1032, "scenarios_excluded_rapid_api": len(exclude), "scenarios_run": len(final),
        "infrastructure_errors": d["infrastructure_errors"],
        "infrastructure_error_scenarios": d["infrastructure_error_scenarios"],
        "scenarios_rerun_after_infra_error": d["scenarios_rerun_after_infra_error"],
        "scored_exceptions_by_type": d["scored_exceptions_by_type"],
        "category_scores": d["category_scores"], "category_stderr_clustered": d["category_stderr_clustered"],
        "category_n": d["category_n"], "category_clusters": d["category_clusters"],
        "other_metrics": d["other_metrics"], "cost": cost,
        "deviations": "see README.md, Deviations",
    }
    res.mkdir(exist_ok=True)
    (res / f"{a.model}.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    with open(res / f"{a.model}.jsonl.gz", "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as g, \
            io.TextIOWrapper(g, encoding="utf-8") as f:   # mtime 0: the same input gives the same bytes
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    print(json.dumps({k: out[k] for k in ("score", "stderr", "n", "infrastructure_errors", "scored_exceptions_by_type")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
