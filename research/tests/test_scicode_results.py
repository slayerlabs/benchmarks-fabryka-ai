"""SciCode: the committed results recounted without the benchmark's code.

No module of api-benchmarks/scicode is imported here. From results/<model-id>.jsonl.gz alone this recounts, per run
and prompt setting, the correct steps, the binomial and the problem-clustered (CR1) SE, main problems solved, the
scorer's verdict counts and the E1 numbers with the steps that took the official verdict; K1, K2 (with its SE floor,
and under E1), K3 (paired, with its lead precondition) and Holm over the Coding group with LiveCodeBench Pro's two
tests; and checks them against results/<model-id>.json, results/hypotheses.json and the numbers printed in README.md
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
    # Holm, m = 4, the other two tests from the committed group file; support and refute families separately
    group = json.loads((RESULTS / "group-tests-livecodebench-pro-25q2.json").read_text(encoding="utf-8"))["group_tests"]
    assert [t["benchmark"] for t in group] == ["livecodebench-pro-25q2"] * 2

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
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))["runs"]
    rs = raw["lfm3-1.7b-nothink"]["settings"]["with_background"]["reasoning"]
    assert (f"**K3** {k3['verdict_holm'].split(' ')[0]} under the pre-registered switch (`enable_thinking: false`): "
            f"with the switch off LFM3 keeps more than half of its lead over Bielik (D = {100 * d:+.2f} ± "
            f"{100 * d_se:.2f}, z = {z3:+.2f}; the lead itself {100 * lead:+.2f}, z = {lead / lead_se:+.2f}). The "
            f"switch removes reasoning only in part: with it off {rs['closing_think']} of {rs['answers']} answers with "
            "background still reason and close a `</think>`") in " ".join(hyp.split())
    assert "How much of the lead thinking itself buys is therefore undetermined by K3" in " ".join(hyp.split())


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
    for tag, w in ev["window_rescore"].items():
        assert f"{tag}: {w['same']} of {w['steps']} verdicts the same" in dev
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
            assert got["reasoning"] == want, (run, s)
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
