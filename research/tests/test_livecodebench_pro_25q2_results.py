"""LiveCodeBench Pro 25Q2: the committed results recounted without the benchmark's code.

No module of api-benchmarks/livecodebench-pro-25q2 is imported here. From results/<model-id>.jsonl.gz alone this
recounts the headline score and its stderr, accepted/n per difficulty, the judge categories, K1, K2 (with the SE
floor), K3 (paired, with its lead precondition), the exploratory budget table and compile-error totals, and checks
them against results/<model-id>.json, results/hypotheses.json, results/exploratory.json and the numbers printed in
README.md (parsed from its tables and sentences here, not by the generator).
Run: python3 -m pytest research/tests/test_livecodebench_pro_25q2_results.py
"""
import gzip
import json
import math
import os
from pathlib import Path

BENCH = Path(os.environ.get("LCBPRO_BENCH", Path(__file__).resolve().parents[1] / "api-benchmarks" /
                            "livecodebench-pro-25q2"))
RESULTS = BENCH / "results"
RUNS = ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1")
CARD_LFM3, CARD_WEAKEST = 0.3174, 0.1916  # PROTOCOL.md: the card's LFM3-1.7B and LFM2.5-2.6B
N = 167


def rows(run):
    with gzip.open(RESULTS / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def result(run):
    return json.loads((RESULTS / f"{run}.json").read_text(encoding="utf-8"))


def readme():
    return (BENCH / "README.md").read_text(encoding="utf-8")


def cells(text, starts):
    line = next(line for line in text.splitlines() if line.startswith(starts))
    return [c.strip() for c in line.strip().strip("|").split("|")]


def phi(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def paired(d):
    n = len(d)
    m = sum(d) / n
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1)) / math.sqrt(n)
    return m, se, m / se


def accepted(run):
    return {t: int(r["accepted"]) for t, r in rows(run).items()}


def test_scores_and_breakdowns():
    text = readme()
    for run in RUNS:
        rs = rows(run)
        assert len(rs) == N and len({r["task_id"] for r in rs.values()}) == N
        k = sum(r["accepted"] for r in rs.values())
        p = k / N
        score, se = round(100 * p, 2), round(100 * math.sqrt(p * (1 - p) / N), 2)
        res = result(run)
        assert (res["score"], res["stderr"], res["n"]) == (score, se, N), run
        assert cells(text, f"| {run} | ")[1] == f"{score:.2f} ± {se:.2f} ({k}/{N})", run
        for i, d in enumerate(("easy", "medium", "hard")):
            sub = [r for r in rs.values() if r["difficulty"] == d]
            kd = sum(r["accepted"] for r in sub)
            pd = kd / len(sub)
            want = f"{100 * pd:.2f} ± {100 * math.sqrt(pd * (1 - pd) / len(sub)):.2f} ({kd}/{len(sub)})"
            assert cells(text, f"| {run} | ")[4 + i] == want, (run, d)
        kept = [r for r in rs.values() if r["category"] not in ("no_tests", "judge_error", "request_error",
                                                                 "unsupported")]
        ks = sum(r["accepted"] for r in kept)
        ps = ks / len(kept)
        assert cells(text, f"| {run} | ")[2] == f"{100 * ps:.2f} ± {100 * math.sqrt(ps * (1 - ps) / len(kept)):.2f} " \
                                                 f"({ks}/{len(kept)})", run
        # accepted is exactly the harness verdict "Accepted"
        assert all(bool(r["accepted"]) == (r["verdict"] == "Accepted") for r in rs.values()), run
        counts = {}
        for r in rs.values():
            counts[r["category"]] = counts.get(r["category"], 0) + 1
        assert {c: v for c, v in res["other_metrics"]["categories"].items() if v} == counts, run
    names = {"lfm3-1.7b": "| LFM3-1.7B (`lfm3-1.7b`) |", "lfm3-1.7b-nothink": "| LFM3-1.7B (`lfm3-1.7b-nothink`) |",
             "bielik-11b-v3.1": "| Bielik 11B v3.1 (`bielik-11b-v3.1`) |"}
    for run, start in names.items():
        c = cells(text, start)
        assert (c[4], c[5], c[6]) == (f"{result(run)['score']:.2f}", f"{result(run)['stderr']:.2f}", str(N)), run
        tokens = [r["output_tokens"] for r in rows(run).values() if r["status"] == "ok"]
        assert c[7] == f"{sum(tokens) / len(tokens):.1f}", run


def test_k1_k2_k3_and_holm():
    on, off, b = accepted("lfm3-1.7b"), accepted("lfm3-1.7b-nothink"), accepted("bielik-11b-v3.1")
    assert set(on) == set(off) == set(b) and len(on) == N
    h = json.loads((RESULTS / "hypotheses.json").read_text(encoding="utf-8"))
    text = readme()
    p_on = sum(on.values()) / N
    z1 = (p_on - CARD_LFM3) / math.sqrt(p_on * (1 - p_on) / N)
    assert math.isclose(h["control"]["z"], z1) and h["control"]["status"] == ("passed" if abs(z1) <= 2 else "failed")
    assert f"z = {z1:+.2f}" in text.split("## Hypotheses")[1]
    p_b = sum(b.values()) / N
    se2 = max(math.sqrt(p_b * (1 - p_b) / N), math.sqrt(CARD_WEAKEST * (1 - CARD_WEAKEST) / N))
    z2 = (p_b - CARD_WEAKEST) / se2
    ids = sorted(on)
    d3, se3, z3 = paired([off[t] - on[t] / 2 - b[t] / 2 for t in ids])
    lead, lead_se, lead_z = paired([on[t] - b[t] for t in ids])
    k2, k3 = (next(x for x in h["hypotheses"] if x["id"] == i) for i in ("K2", "K3"))
    assert math.isclose(k2["z"], z2) and math.isclose(k2["value"], 100 * p_b) and math.isclose(k2["se"], 100 * se2)
    assert math.isclose(k3["value"], 100 * d3) and math.isclose(k3["se"], 100 * se3)
    assert math.isclose(k3["lead"]["z"], lead_z)
    assert k3["status"] == ("ok" if lead > 0 and lead_z >= 3 else "precondition not met")
    if k3["status"] == "ok":
        assert math.isclose(k3["z"], z3)
    section = text.split("## Hypotheses")[1].split("## Exploratory")[0]
    assert cells(section, "| K2 |")[1:3] == [f"{100 * p_b:+.2f} ± {100 * se2:.2f}", f"{z2:+.2f}"]
    assert cells(section, "| K3 |")[1:3] == [f"{100 * d3:+.2f} ± {100 * se3:.2f}", f"{z3:+.2f}"]
    assert cells(section, "| K3 lead")[1:3] == [f"{100 * lead:+.2f} ± {100 * lead_se:.2f}", f"{lead_z:+.2f}"]
    # Holm, m = 4, SciCode's two tests absent (p = 1): support and refute families separately
    for key, ps in (("p_support", [phi(z2), phi(z3), 1.0, 1.0]), ("p_refute", [1 - phi(z2), 1 - phi(z3), 1.0, 1.0])):
        order = sorted(range(4), key=lambda i: ps[i])
        adj, running = [0.0] * 4, 0.0
        for rank, i in enumerate(order):
            running = max(running, min(1.0, (4 - rank) * ps[i]))
            adj[i] = running
        assert math.isclose(k2[f"{key}_holm"], adj[0], rel_tol=1e-9) and \
            math.isclose(k3[f"{key}_holm"], adj[1], rel_tol=1e-9), key
    for k, z in ((k2, z2), (k3, z3)):
        p_s = k["p_support_holm"]
        p_r = k["p_refute_holm"]
        want = ("supported" if p_s <= phi(-2) else "refuted" if p_r <= phi(-2) else "undetermined")
        assert k["verdict_holm"].split(" ")[0] == want and cells(section, f"| {k['id']} |")[5].split(" ")[0] == want


def test_exploratory_budgets_and_compile_errors():
    e = json.loads((RESULTS / "exploratory.json").read_text(encoding="utf-8"))
    text = readme().split("## Exploratory")[1]
    assert "EXPLORATORY" in text
    for run in RUNS:
        rs = rows(run).values()
        want = [sum(1 for r in rs if r["accepted"] and r["output_tokens"] <= b) for b in (4096, 8192, 16384, 32768)]
        assert [e["budgets"]["accepted"][run][str(b)] for b in (4096, 8192, 16384, 32768)] == want, run
        assert cells(text, f"| {run} | ")[1:6] == [str(x) for x in want] + [str(sum(r["accepted"] for r in rs))]
        ce = [r for r in rs if r["category"] == "compile_error"]
        assert e["compile_errors"][run]["total"] == len(ce)
        assert cells(text.split("Compile errors")[1], f"| {run} | ")[1] == str(len(ce))
        # g++'s own note is an independent fact of the message; the other two causes split the rest
        noted = sum(1 for r in ce if "did you forget to '#include" in (r["judge_error"] or ""))
        by = e["compile_errors"][run]["by_cause"]
        assert by["compiler_says_missing_include"]["count"] == noted
        assert sum(v["count"] for v in by.values()) == len(ce)


def test_no_code_causes_are_the_no_code_problems():
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))
    for run in RUNS:
        listed = sorted(t for ids in raw["runs"][run]["no_code"].values() for t in ids)
        assert listed == sorted(t for t, r in rows(run).items() if r["category"] == "no_code"), run
        assert raw["runs"][run]["sha256"] == result(run)["raw_outputs"]["sha256"] and raw["runs"][run]["matches_result"]


def test_files_fit_the_repo():
    for path in RESULTS.iterdir():
        assert path.stat().st_size <= 10 * 1024 * 1024, path
