"""SciCode: the committed results recounted without the benchmark's code.

No module of api-benchmarks/scicode is imported here. From results/<model-id>.jsonl.gz alone this recounts, per run
and prompt setting, the correct steps, the binomial and the problem-clustered (CR1) SE, main problems solved, the
scorer's verdict counts and the E1 numbers with the steps that took the official verdict; K1, K2 (with its SE floor,
and under E1), K3 (paired, with its lead precondition) and Holm over the Coding group with LiveCodeBench Pro's two
tests at p = 1 (no copy of its file); and checks them against results/<model-id>.json, results/hypotheses.json and
the numbers printed in README.md
(parsed from its tables and sentences here, not by the generator). The README's generated blocks must equal what
readme.py writes, byte for byte (`readme.py --check`, run as a separate process). The scoring-VM facts are recounted
from the copied logs in results/scoring-vm/, and where the raw outputs are on this machine (SCICODE_RAW_ARCHIVE,
out/bielik-11b-v3.1) the reasoning and extraction counts of results/raw-outputs.json are recounted from them.
Run: python3 -m pytest research/tests/test_scicode_results.py
"""
import gzip
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

BENCH = Path(os.environ.get("SCICODE_BENCH", Path(__file__).resolve().parents[1] / "api-benchmarks" / "scicode"))
RESULTS = BENCH / "results"
RUNS = ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1")
SETTINGS = ("with_background", "without_background")
LABEL = {"with_background": "with background", "without_background": "without background"}
CARD_LFM3, CARD_WEAKEST = 0.2847, 0.1632  # PROTOCOL.md: the card's LFM3-1.7B and LFM2.5-2.6B
N, PROBLEMS = 288, 65


def rows(run):
    with gzip.open(RESULTS / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def result(run):
    return json.loads((RESULTS / f"{run}.json").read_text(encoding="utf-8"))


def readme():
    return (BENCH / "README.md").read_text(encoding="utf-8")


def section(name):
    text = readme()
    return text.split(f"## {name}\n", 1)[1].split("\n## ", 1)[0]


def cells(text, starts):
    line = next(line for line in text.splitlines() if line.startswith(starts))
    return [c.strip() for c in line.strip().strip("|").split("|")]


def phi(z):
    return 0.5 * math.erfc(-z / math.sqrt(2))


def clustered(values, clusters):
    """mean and CR1 SE clustered by `clusters`, written out here."""
    n = len(values)
    mean = sum(values) / n
    sums = {}
    for v, c in zip(values, clusters):
        sums[c] = sums.get(c, 0.0) + v - mean
    g = len(sums)
    return mean, math.sqrt(g / (g - 1) * sum(s * s for s in sums.values())) / n


def setting_rows(run, setting):
    rs = [r for r in rows(run).values() if r["setting"] == setting]
    return sorted(rs, key=lambda r: (int(r["problem_id"]), int(r["step"])))


def solved(rs, key="score"):
    by = {}
    for r in rs:
        by.setdefault(r["problem_id"], []).append(r[key])
    return sum(1 for v in by.values() if all(v)), len(by)


def zero_cell(n):
    return f"0.00 (0/{n}; exact 95% CI 0 to {100 * (1 - 0.025 ** (1 / n)):.2f})"


def share_cell(k, n, se_cl):
    if k == 0:
        return zero_cell(n)
    p = k / n
    return f"{100 * p:.2f} ± {100 * math.sqrt(p * (1 - p) / n):.2f} ({k}/{n}; clustered {100 * se_cl:.2f})"


def problems_cell(k, of):
    if k == 0:
        return f"0/{of} (exact 95% CI 0 to {100 * (1 - 0.025 ** (1 / of)):.2f}%)"
    return f"{k}/{of} ({100 * k / of:.2f}%)"


def test_generated_blocks_are_byte_for_byte_what_readme_py_writes():
    run = subprocess.run([sys.executable, "readme.py", "--check"], cwd=BENCH, capture_output=True, text=True)
    assert run.returncode == 0, run.stderr


def test_scores_se_main_problems_and_verdicts():
    results = section("Results")
    for run in RUNS:
        res = result(run)
        assert len(rows(run)) == 2 * N
        for s in SETTINGS:
            rs = setting_rows(run, s)
            assert len(rs) == N and len({r["problem_id"] for r in rs}) == PROBLEMS
            assert all(r["score"] == int(r["verdict"] == "pass") for r in rs)
            k = sum(r["score"] for r in rs)
            p = k / N
            _, se_cl = clustered([float(r["score"]) for r in rs], [r["problem_id"] for r in rs])
            m = res["other_metrics"][s] if s != "with_background" else {
                **res["other_metrics"][s], "score": res["score"], "stderr": res["stderr"]}
            assert (m["score"], m["stderr"]) == (round(100 * p, 2), round(100 * math.sqrt(p * (1 - p) / N), 2))
            assert m["stderr_clustered"] == round(100 * se_cl, 2) and m["correct"] == k, (run, s)
            sv, of = solved(rs)
            assert (m["main_problems"]["solved"], m["main_problems"]["of"]) == (sv, of)
            assert m["timeouts"] == sum(1 for r in rs if r["verdict"] == "time out"), (run, s)
            verdicts = {v: sum(1 for r in rs if r["verdict"] == v) for v in ("pass", "fail", "time out")}
            c = cells(results, f"| {run} | {LABEL[s]} | ")
            assert c[2:7] == [share_cell(k, N, se_cl), problems_cell(sv, of), str(verdicts["pass"]),
                              str(verdicts["fail"]), str(verdicts["time out"])], (run, s)
        if run == "lfm3-1.7b":
            assert res["stderr_clustered"] == round(100 * clustered(
                [float(r["score"]) for r in setting_rows(run, "with_background")],
                [r["problem_id"] for r in setting_rows(run, "with_background")])[1], 2)
    names = {"lfm3-1.7b": "| LFM3-1.7B (`lfm3-1.7b`) |", "lfm3-1.7b-nothink": "| LFM3-1.7B (`lfm3-1.7b-nothink`) |",
             "bielik-11b-v3.1": "| Bielik 11B v3.1 (`bielik-11b-v3.1`) |"}
    for run, start in names.items():
        rs = setting_rows(run, "with_background")
        k = sum(r["score"] for r in rs)
        p = k / N
        _, se_cl = clustered([float(r["score"]) for r in rs], [r["problem_id"] for r in rs])
        tokens = [r["output_tokens"] for r in rs if r["status"] == "ok"]
        c = cells(results, start)
        assert c[4:10] == [f"{100 * p:.2f}", f"{100 * math.sqrt(p * (1 - p) / N):.2f}", f"{100 * se_cl:.2f}", str(N),
                           problems_cell(*solved(rs)), f"{sum(tokens) / len(tokens):.1f}"], run
    assert "null (" in cells(results, "| Slayer 1B 1.09")[4]


def test_e1_numbers_and_reuse():
    results = section("Results")
    lines = [line for line in results.split("Secondary extraction E1")[1].splitlines() if line.startswith("| ")]
    for run in RUNS:
        for s in SETTINGS:
            rs = setting_rows(run, s)
            k1 = sum(r["score_e1"] for r in rs)
            assert all(r["score_e1"] == int(r["verdict_e1"] == "pass") for r in rs)
            # a reused step has the official verdict
            assert all(r["verdict_e1"] == r["verdict"] for r in rs if r["e1_reused"])
            reused = sum(1 for r in rs if r["e1_reused"])
            _, se_cl = clustered([float(r["score_e1"]) for r in rs], [r["problem_id"] for r in rs])
            e = result(run)["other_metrics"]["extraction_e1"][s]
            assert (e["correct"], e["reused_identical"], e["scored"]) == (k1, reused, N - reused)
            assert e["stderr_clustered"] == round(100 * se_cl, 2)
            line = next(x for x in lines if x.startswith(f"| {run} | {LABEL[s]} |"))
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            assert c[2:7] == [f"{sum(r['score'] for r in rs)}/{N}", share_cell(k1, N, se_cl),
                              problems_cell(*solved(rs, "score_e1")), str(reused), str(N - reused)], (run, s)


def test_k1_k2_k3_holm_and_reading():
    on = {r["task_id"]: r for r in setting_rows("lfm3-1.7b", "with_background")}
    off = {r["task_id"]: r for r in setting_rows("lfm3-1.7b-nothink", "with_background")}
    b = {r["task_id"]: r for r in setting_rows("bielik-11b-v3.1", "with_background")}
    assert set(on) == set(off) == set(b) and len(on) == N
    ids = sorted(on, key=lambda t: (int(on[t]["problem_id"]), int(on[t]["step"])))
    cl = [on[t]["problem_id"] for t in ids]
    h = json.loads((RESULTS / "hypotheses.json").read_text(encoding="utf-8"))
    p_on, se1 = clustered([float(on[t]["score"]) for t in ids], cl)
    z1 = (p_on - CARD_LFM3) / se1
    assert math.isclose(h["control"]["z"], z1) and h["control"]["status"] == ("passed" if abs(z1) <= 2 else "failed")
    floor = math.sqrt(CARD_WEAKEST * (1 - CARD_WEAKEST) / N)
    p_b, se_b = clustered([float(b[t]["score"]) for t in ids], cl)
    z2 = (p_b - CARD_WEAKEST) / max(se_b, floor)
    p_b1, se_b1 = clustered([float(b[t]["score_e1"]) for t in ids], cl)
    z2e = (p_b1 - CARD_WEAKEST) / max(se_b1, floor)
    lead, lead_se = clustered([on[t]["score"] - b[t]["score"] for t in ids], cl)
    d, d_se = clustered([off[t]["score"] - on[t]["score"] / 2 - b[t]["score"] / 2 for t in ids], cl)
    z3 = d / d_se
    k2, k3 = h["hypotheses"]
    assert math.isclose(k2["z"], z2) and math.isclose(k2["e1"]["z"], z2e) and math.isclose(k2["se"], 100 * max(se_b, floor))
    assert math.isclose(k3["precondition"]["z"], lead / lead_se)
    met = lead > 0 and lead / lead_se >= 3
    assert k3["precondition"]["met"] == met and (not met or math.isclose(k3["z"], z3))
    assert math.isclose(k3["value"], 100 * d) and math.isclose(k3["se"], 100 * d_se)
    # Holm, m = 4: no copy of LiveCodeBench Pro's file here, its two tests enter with p = 1 (the group Holm is computed
    # on main from both merged files); support and refute families separately
    assert not (RESULTS / "group-tests-livecodebench-pro-25q2.json").exists()
    assert h["holm"]["other_benchmark_file"] is None and h["holm"]["missing_counted_as_p_1"] == 2
    group = [{"p_support": 1.0, "p_refute": 1.0}] * 2

    def holm(ps):
        order = sorted(range(4), key=lambda i: ps[i])
        adj, running = [0.0] * 4, 0.0
        for rank, i in enumerate(order):
            running = max(running, min(1.0, (4 - rank) * ps[i]))
            adj[i] = running
        return adj

    zs = [z2, z3 if met else None]
    for key, f in (("p_support", phi), ("p_refute", lambda z: 1 - phi(z))):
        ps = [1.0 if z is None else f(z) for z in zs] + [t[key] if t[key] is not None else 1.0 for t in group]
        adj = holm(ps)
        assert math.isclose(k2[f"{key}_holm"], adj[0], rel_tol=1e-9) and math.isclose(k3[f"{key}_holm"], adj[1], rel_tol=1e-9)
        ps_e1 = [f(z2e)] + ps[1:]
        assert math.isclose(k2["e1"][f"{key}_holm"], holm(ps_e1)[0], rel_tol=1e-9)

    def verdict(ps, pr):
        for p, side in ((ps, "supported"), (pr, "refuted")):
            if p <= phi(-3):
                return f"{side} (clear)"
            if p <= phi(-2):
                return f"{side} (likely)"
        return "undetermined"

    assert k2["verdict_holm"] == verdict(k2["p_support_holm"], k2["p_refute_holm"])
    assert k3["verdict_holm"] == verdict(k3["p_support_holm"], k3["p_refute_holm"])
    assert k2["depends_on_extraction"] == (k2["e1"]["verdict_holm"] != k2["verdict_holm"]
                                           or k2["e1"]["outcome_raw"] != k2["outcome_raw"])
    hyp = section("Hypotheses")
    assert f"z = {z1:+.2f}: {h['control']['status']}" in hyp
    assert cells(hyp, "| K2 |")[1:4] == [f"{100 * (p_b - CARD_WEAKEST):+.2f}", f"{100 * max(se_b, floor):.2f}", f"{z2:+.2f}"]
    assert cells(hyp, "| K2 under E1")[1:4] == [f"{100 * (p_b1 - CARD_WEAKEST):+.2f}", f"{100 * max(se_b1, floor):.2f}",
                                                f"{z2e:+.2f}"]
    assert cells(hyp, "| K3 |")[1:4] == [f"{100 * d:+.2f}", f"{100 * d_se:.2f}", f"{z3:+.2f}"]
    assert cells(hyp, "| K2 |")[7] == k2["verdict_holm"] and cells(hyp, "| K3 |")[7] == k3["verdict_holm"]
    assert "Holm m = 4, family: scicode K2, scicode K3; 2 of the 4 without a p here, counted as p = 1" in hyp
    flat = " ".join(hyp.split())
    gap = 100 * (p_on - CARD_LFM3)
    assert (f"({gap:+.2f} pt, z = {z1:+.2f})" in flat and f"the gap is {abs(gap):.2f} pt" in flat
            and f"2 clustered SE are {200 * se1:.2f} pt" in flat and abs(gap) > 2)
    # Student's t (df = problems - 1) for our K2 and K3, by numerical integration of the density, then Holm m = 4
    df = len(set(cl)) - 1

    def t_cdf(x):
        dens = lambda u: math.exp(math.lgamma((df + 1) / 2) - math.lgamma(df / 2)) / math.sqrt(df * math.pi) * \
            (1 + u * u / df) ** (-(df + 1) / 2)  # noqa: E731
        lo, n = -60.0, 200000
        hstep = (x - lo) / n
        s = dens(lo) + dens(x) + sum((4 if i % 2 else 2) * dens(lo + i * hstep) for i in range(1, n))
        return s * hstep / 3
    ps_t = [t_cdf(z2), t_cdf(z3) if met else None]
    sup_t = holm([1.0 if p is None else p for p in ps_t] + [t["p_support"] for t in group])
    ref_t = holm([1.0 if p is None else 1 - p for p in ps_t] + [t["p_refute"] for t in group])
    tc = h["t_check"]
    assert math.isclose(tc["K2"]["p_support_holm"], sup_t[0], rel_tol=1e-4)
    assert math.isclose(tc["K3"]["p_refute_holm"], ref_t[1], rel_tol=1e-4)
    assert (tc["K2"]["verdict_holm"], tc["K3"]["verdict_holm"]) == (verdict(sup_t[0], ref_t[0]), verdict(sup_t[1], ref_t[1]))
    assert (f"K2 Holm p {sup_t[0]:.3g}, {tc['K2']['verdict_holm']}; K3 Holm p {ref_t[1]:.3g}, "
            f"{tc['K3']['verdict_holm']}") in flat
    gap_wb = 100 * (sum(float(r["score"]) for r in setting_rows("lfm3-1.7b", "without_background")) / N - CARD_LFM3)
    _, se_wb = clustered([float(r["score"]) for r in setting_rows("lfm3-1.7b", "without_background")],
                         [r["problem_id"] for r in setting_rows("lfm3-1.7b", "without_background")])
    assert abs(gap_wb) <= 200 * se_wb and abs(gap) <= 200 * se1  # both settings pass the control's rule
    assert (f"without background LFM3-1.7B ({100 * CARD_LFM3 + gap_wb:.2f}, {gap_wb:+.2f} pt, "
            f"z = {gap_wb / (100 * se_wb):+.2f}) lands within 2 clustered SE") in flat
    assert "the control cannot tell the two settings apart" in flat
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))["runs"]
    rs = raw["lfm3-1.7b-nothink"]["settings"]["with_background"]["reasoning"]
    assert (f"**K3** {k3['verdict_holm'].split(' ')[0]} under the pre-registered switch (`enable_thinking: false`): "
            f"with the switch off LFM3 keeps more than half of its lead over Bielik (D = {100 * d:+.2f} ± "
            f"{100 * d_se:.2f}, z = {z3:+.2f}; the lead itself {100 * lead:+.2f}, z = {lead / lead_se:+.2f}). "
            f"*Descriptive, from the raw outputs, added after the results (Amendment 2):* the switch removes reasoning "
            f"only in part: with it off {rs['closing_think']} of {rs['answers']} answers with "
            "background still reason and close a `</think>`") in " ".join(hyp.split())
    assert "How much of the lead thinking itself buys is therefore undetermined by K3" in " ".join(hyp.split())
    # K3 robustness (descriptive): per-problem contributions, dropping the largest, jackknife, bootstrap, sign test
    dd = {t: off[t]["score"] - on[t]["score"] / 2 - b[t]["score"] / 2 for t in ids}
    contrib = {}
    for t in ids:
        contrib.setdefault(on[t]["problem_id"], []).append(dd[t])
    order = sorted(contrib, key=lambda g: (-sum(contrib[g]), int(g)))
    rob = h["k3_robustness"]
    for k, x in enumerate(rob["drop_top_problems"], 1):
        keep = [t for t in ids if on[t]["problem_id"] not in order[:k]]
        m_k, se_k = clustered([dd[t] for t in keep], [on[t]["problem_id"] for t in keep])
        p_k = holm([1 - phi(z2), 1 - phi(m_k / se_k)] + [t["p_refute"] for t in group])[1]
        assert x["dropped"] == order[:k] and math.isclose(x["z"], m_k / se_k) and math.isclose(x["p_refute_holm"], p_k)
        assert x["verdict_holm"] == verdict(1.0, p_k)
        assert cells(hyp, f"| {', '.join(order[:k])} |")[1:6] == [f"{100 * m_k:+.2f}", f"{100 * se_k:.2f}", f"{m_k / se_k:+.2f}",
                                                                 f"{p_k:.3g}", verdict(1.0, p_k)]
    total, g = sum(dd.values()), len(contrib)
    loo = [(total - sum(v)) / (N - len(v)) for v in contrib.values()]
    se_jk = math.sqrt((g - 1) / g * sum((x - sum(loo) / g) ** 2 for x in loo))
    assert math.isclose(rob["jackknife"]["z"], (total / N) / se_jk)
    import random
    rng, names, draws = random.Random(rob["cluster_bootstrap"]["seed"]), sorted(contrib, key=int), []
    for _ in range(rob["cluster_bootstrap"]["draws"]):
        pick = [rng.choice(names) for _ in names]
        draws.append(sum(sum(contrib[c]) for c in pick) / sum(len(contrib[c]) for c in pick))
    draws.sort()
    lo_hi = [100 * draws[int(0.025 * len(draws))], 100 * draws[int(0.975 * len(draws)) - 1]]
    assert rob["cluster_bootstrap"]["ci95"] == lo_hi and lo_hi[0] < 100 * d < lo_hi[1]
    pos = sum(1 for v in contrib.values() if sum(v) > 0)
    neg = sum(1 for v in contrib.values() if sum(v) < 0)
    one = sum(math.comb(pos + neg, i) for i in range(min(pos, neg) + 1)) / 2 ** (pos + neg)
    assert (rob["sign_test_problems"]["positive"], rob["sign_test_problems"]["negative"]) == (pos, neg)
    assert math.isclose(rob["sign_test_problems"]["p_one_sided"], one)
    bs = rob["cluster_bootstrap"]
    assert (f"Jackknife over problems: SE {100 * se_jk:.2f}, z = {(total / N) / se_jk:+.2f}. Cluster bootstrap over "
            f"problems ({len(draws)} draws, seed {bs['seed']}): 95% interval of D [{lo_hi[0]:.2f}; {lo_hi[1]:.2f}] pp. "
            f"Sign of each problem's contribution: {pos} positive, {neg} negative, {g - pos - neg} zero (exact sign test "
            f"p = {one:.2g} one-sided, {min(1.0, 2 * one):.2g} two-sided). \"Clear\" rests on problem {order[0]}: "
            f"without it K3 is {rob['drop_top_problems'][0]['verdict_holm']}.") in flat
    assert math.isclose(rob["jackknife"]["se"], 100 * se_jk) and rob["drop_top_problems"][0]["dropped"] == [order[0]]
    # exploratory: nothink's passes from answers closing </think> counted as failed
    steps = {f"with_background/{s}" for s in rs["passed_closing_think_steps"]}
    assert len(steps) == rs["passed_closing_think"] and all(off[t]["score"] == 1 for t in steps)
    d0, se0 = clustered([(0 if t in steps else off[t]["score"]) - on[t]["score"] / 2 - b[t]["score"] / 2 for t in ids], cl)
    cf = json.loads((RESULTS / "exploratory.json").read_text(encoding="utf-8"))["k3_without_reasoning_passes"]
    assert math.isclose(cf["value"], 100 * d0) and math.isclose(cf["z"], d0 / se0)
    assert f"gives D = {100 * d0:+.2f} ± {100 * se0:.2f} (z = {d0 / se0:+.2f})" in flat


def test_scoring_vm_facts_recounted_from_the_copied_logs():
    folder = RESULTS / "scoring-vm"
    killed = {}
    for path in folder.glob("*.stdout.txt"):
        text = path.read_text(encoding="utf-8")
        for step in re.findall(r"/(\d+\.\d+)\.py: Command .* died with <Signals\.SIGKILL: 9>", text):
            killed.setdefault(path.name, []).append(step)
        printed = int(re.findall(r"^correct steps: (\d+)/288$", text, re.M)[-1])
        run, pas = path.name[:-len(".stdout.txt")].rsplit(".", 1)
        rs = setting_rows(run, pas.removeprefix("e1_"))
        if pas.startswith("e1_"):  # the E1 scorer ran only on the steps that were not reused
            assert printed == sum(r["score_e1"] for r in rs if not r["e1_reused"]), path.name
        else:
            assert printed == sum(r["score"] for r in rs), path.name
    oom = (folder / "kernel-oom.txt").read_text(encoding="utf-8")
    kills = re.findall(r"^(\w{3} \d+ [\d:]{8}) .*Memory cgroup out of memory: Killed process", oom, re.M)
    ev = json.loads((RESULTS / "scoring-events.json").read_text(encoding="utf-8"))
    assert [k["time_utc"] for k in ev["kernel_oom_kills"]] == kills
    recorded = {f"{run}.{p}.stdout.txt": x["killed_sigkill"] for run, ps in ev["scorer_runs_final"].items()
                for p, x in ps.items() if x["killed_sigkill"]}
    assert recorded == killed
    for name, steps in killed.items():  # a killed step counts as failed
        run, pas = name[:-len(".stdout.txt")].rsplit(".", 1)
        key = "score_e1" if pas.startswith("e1_") else "score"
        rs = {f"{r['problem_id']}.{r['step']}": r for r in setting_rows(run, pas.removeprefix("e1_"))}
        assert all(rs[s][key] == 0 for s in steps)
    dev = " ".join(section("Deviations").split())
    assert f"The kernel's OOM killer ended {len(kills)} test scripts" in dev
    for t in kills:
        assert f"{t} UTC" in dev
    windows = sorted(folder.glob("window-*.json"))
    assert windows and len(windows) == len(ev["window_rescore"])
    for path in windows:
        w = json.loads(path.read_text(encoding="utf-8"))
        tag = path.stem[len("window-"):]
        kept = {f"{r['problem_id']}.{r['step']}": r["verdict"] for r in setting_rows(w["model"], w["setting"])}
        assert all(kept[r["step"]] == r["kept"] for r in w["rows"])  # the kept verdicts are the committed ones
        same = sum(1 for r in w["rows"] if r["kept"] == r["rescored"])
        assert (same, len(w["rows"])) == (ev["window_rescore"][tag]["same"], ev["window_rescore"][tag]["steps"])
        assert f"({tag}): {same} of {len(w['rows'])} the same" in dev
        assert w["graded_sha256"] == result(w["model"])["provenance"]["inputs_sha256"]["graded.jsonl"]
    for path in sorted(folder.glob("reference-extraction-*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        run = r["model"]
        assert r["inputs_sha256"]["graded.jsonl"] == result(run)["provenance"]["inputs_sha256"]["graded.jsonl"]
        assert r["inputs_sha256"]["generations.jsonl"] == result(run)["raw_outputs"]["sha256"]
        raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))["runs"][run]["settings"]
        for s, x in r["settings"].items():
            kept = {f"{q['problem_id']}.{q['step']}": q["verdict"] for q in setting_rows(run, s)}
            assert all(kept[n] == v[0] for n, v in x["verdicts_of_differing_files"].items())
            assert sorted(x["verdicts_of_differing_files"]) == sorted(x["files_differing"])
            assert x["passed_after_think"] == sum(v == "pass" for v in kept.values())
            changed = x["verdicts_changed"]
            assert x["passed_whole_answer"] == x["passed_after_think"] + sum(
                (b == "pass") - (a == "pass") for a, b in changed.values())
            assert len(x["answers_with_think_end"]) == raw[s]["reasoning"]["closing_think"]
            assert (f"{LABEL[s]}: {len(x['answers_with_think_end'])} answers contain `</think>`, "
                    f"{len(x['answers_whose_code_differs'])} give other code, {len(x['files_differing'])} step files "
                    f"differ") in dev
            assert (f"passed {x['passed_after_think']} after the last `</think>` and {x['passed_whole_answer']} from the "
                    f"whole answer, {len(changed)} verdicts change") in dev
    repeats = {}
    for path in folder.glob("repeat-*-run*.json"):
        repeats.setdefault(path.stem.rsplit("-run", 1)[0], []).append(json.loads(path.read_text(encoding="utf-8")))
    hyp = " ".join(section("Hypotheses").split())
    assert len(repeats) == len(ev["repeated_steps"])
    for r in ev["repeated_steps"]:
        runs = repeats[r["tag"]]
        rows_ = [x["rows"][0] for x in runs]
        kept = {f"{q['problem_id']}.{q['step']}": q["verdict"] for q in setting_rows(r["model"], r["setting"])}
        assert all(x["kept"] == kept[x["step"]] for x in rows_) and {x["step"] for x in rows_} == {r["step"]}
        counts = {}
        for x in rows_:
            counts[x["rescored"]] = counts.get(x["rescored"], 0) + 1
        assert counts == r["rescored"] and len(runs) == r["runs"]
        assert all(x["graded_sha256"] == result(r["model"])["provenance"]["inputs_sha256"]["graded.jsonl"] for x in runs)
        assert (f"step {r['step']} (officially {kept[r['step']]};" in hyp
                and "re-scored with the same image: "
                + ", ".join(f"{v} {n} of {len(runs)}" for v, n in sorted(counts.items())) in hyp)
    for name in ev["inputs_sha256"]:
        assert hashlib.sha256((folder / name).read_bytes()).hexdigest() == ev["inputs_sha256"][name]


def test_generation_and_scoring_commits():
    git = lambda *a: subprocess.run(["git", "-C", str(BENCH), *a], capture_output=True)  # noqa: E731
    if git("rev-parse", "HEAD").returncode != 0:
        pytest.skip("no git checkout")
    for run in RUNS:
        p = result(run)["provenance"]
        for step in [*p["generation"], p["scoring"]]:
            for name in ("scicode_runner.py", "run.sh"):
                blob = git("show", f"{step['code_commit']}:research/api-benchmarks/scicode/{name}")
                assert blob.returncode == 0
                assert hashlib.sha256(blob.stdout).hexdigest() == step["runner_sha256"][name], (run, step["step"], name)
    dev = " ".join(section("Deviations").split())
    assert "`3b731440030a178e73f660c632c2df68fd2fce29` for all three runs" in dev


def test_files_fit_the_repo():
    for path in RESULTS.rglob("*"):
        if path.is_file():
            assert path.stat().st_size <= 10 * 1024 * 1024, path


RAW_ARCHIVE = Path(os.environ.get("SCICODE_RAW_ARCHIVE", Path.home() / "Documents/GitHub/labaj-agency/out/"
                                                                         "coding-group/box/export.tgz"))
ARCHIVE_PREFIX = "scicode/research/api-benchmarks/scicode/out"


def raw_generations():
    import tarfile
    local = BENCH / "out" / "bielik-11b-v3.1" / "generations.jsonl"
    if not RAW_ARCHIVE.is_file() or not local.is_file():
        return None
    with tarfile.open(RAW_ARCHIVE) as t:
        data = {run: t.extractfile(f"{ARCHIVE_PREFIX}/{run}/generations.jsonl").read()
                for run in ("lfm3-1.7b", "lfm3-1.7b-nothink")}
    return {**data, "bielik-11b-v3.1": local.read_bytes()}


def test_reasoning_and_extraction_counts_recounted_from_the_raw_outputs():
    data = raw_generations()
    if data is None:
        pytest.skip(f"raw outputs not on this machine ({RAW_ARCHIVE}, out/bielik-11b-v3.1)")
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(RAW_ARCHIVE.read_bytes()).hexdigest() == raw["archive"]["sha256"]
    text = " ".join(section("Exploratory").split())
    for run, blob in data.items():
        assert hashlib.sha256(blob).hexdigest() == result(run)["raw_outputs"]["sha256"] == raw["runs"][run]["sha256"]
        last = {}
        for line in blob.decode("utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                last[f"{r['setting']}/{r['problem_id']}.{r['step']}"] = r
        graded = rows(run)
        for s in SETTINGS:
            ids = [t for t in graded if t.startswith(s + "/")]
            ok = [last[t] for t in ids if last[t]["status"] == "ok"]
            closing = [r for r in ok if "</think>" in r["output"]]
            passed = [t for t in ids if graded[t]["score"]]
            share = statistics.median(r["output"].rindex("</think>") / len(r["output"]) for r in closing) if closing else None
            want = {"answers": len(ok), "closing_think": len(closing),
                    "median_share_before_last_think_end": None if share is None else round(share, 4),
                    "passed": len(passed), "passed_closing_think": sum(1 for t in passed if "</think>" in last[t]["output"])}
            got = raw["runs"][run]["settings"][s]
            assert {k: v for k, v in got["reasoning"].items() if k != "passed_closing_think_steps"} == want, (run, s)
            assert sorted(got["reasoning"]["passed_closing_think_steps"]) == sorted(
                t.split("/")[1] for t in passed if "</think>" in last[t]["output"]), (run, s)
            after = {t: last[t]["output"].split("</think>")[-1] for t in ids}
            fence = {t: [ln for ln in a.split("\n") if ln.lstrip(" \t").startswith("```")] for t, a in after.items()}
            lone = {t for t in ids if len(fence[t]) == 1 and "```python" not in after[t]}
            empty = [t for t in ids if not (graded[t]["output"] or "").strip()]
            x = got["extraction"]
            assert x["empty_official"] == len(empty) and x["answers_lone_fence"] == len(lone)
            assert x["answers_without_fence_line"] == sum(1 for t in ids if not fence[t])
            assert sorted(x["empty_by_cause"].get("lone_fence", [])) == sorted(
                t.split("/")[1] for t in empty if t in lone and not last[t].get("unfinished"))
            sh = "none" if share is None else f"{100 * round(share, 4):.1f}%"
            assert (f"| {run} | {LABEL[s]} | {len(closing)} of {len(ok)} | {sh} | {want['passed_closing_think']} of "
                    f"{len(passed)} |") in text, (run, s)
