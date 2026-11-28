"""LiveCodeBench Pro 25Q2: the committed results recounted without the benchmark's code.

No module of benchmarks/livecodebench-pro-25q2 is imported here. From results/<model-id>.jsonl.gz alone this
recounts the headline score and its stderr, accepted/n per difficulty, the judge categories, K1, K2 (with the SE
floor), K3 (paired, with its lead precondition), the exploratory budget table and compile-error totals, and checks
them against results/<model-id>.json, results/hypotheses.json, results/exploratory.json and the numbers printed in
README.md (parsed from its tables and sentences here, not by the generator). README's reasoning counts and labels
are checked against the committed results/raw-outputs.json; where the raw outputs are on this machine
(LCBPRO_RAW_ARCHIVE, out/bielik-11b-v3.1), the counts in that file are recounted from them too (skipped otherwise).
Needs only pytest and the standard library.
Run: python3 -m pytest research/tests/test_livecodebench_pro_25q2_results.py
"""
import gzip
import json
import math
import os
import re
from pathlib import Path

BENCH = Path(os.environ.get("LCBPRO_BENCH", Path(__file__).resolve().parents[1] / "benchmarks" /
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


def share_cell(k, n):
    """`p ± SE (k/n)`; for k = 0 the exact two-sided 95% upper end 1 - 0.025^(1/n) instead of the zero SE."""
    if k == 0:
        return f"0.00 (0/{n}; exact 95% CI 0 to {100 * (1 - 0.025 ** (1 / n)):.2f})"
    p = k / n
    return f"{100 * p:.2f} ± {100 * math.sqrt(p * (1 - p) / n):.2f} ({k}/{n})"


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
            assert cells(text, f"| {run} | ")[4 + i] == share_cell(kd, len(sub)), (run, d)
        kept = [r for r in rs.values() if r["category"] not in ("no_tests", "judge_error", "request_error",
                                                                 "unsupported")]
        ks = sum(r["accepted"] for r in kept)
        assert cells(text, f"| {run} | ")[2] == share_cell(ks, len(kept)), run
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


def test_k1_k2_k3_each_test_alone():
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
    # each test on its own: one-sided p from z and the verdict from the raw z (no Holm here; PROTOCOL.md, Amendment 2)
    for k, z in ((k2, z2), (k3, z3)):
        assert math.isclose(k["p_support"], phi(z)) and math.isclose(k["p_refute"], 1 - phi(z))
        want = ("supported" if z <= -2 else "refuted" if z >= 2 else "undetermined")
        assert k["verdict"].split(" ")[0] == want and cells(section, f"| {k['id']} |")[4].split(" ")[0] == want
        assert cells(section, f"| {k['id']} |")[3] == f"{phi(z):.3g} / {1 - phi(z):.3g}"


def test_no_holm_over_another_benchmarks_file():
    """The Coding group's Holm is computed once on main from both merged hypotheses.json files (PROTOCOL.md,
    Amendment 2): nothing here pins or reads another benchmark's file."""
    h = json.loads((RESULTS / "hypotheses.json").read_text(encoding="utf-8"))
    assert "holm" not in h and "group_file" not in h
    assert not any(k.endswith("_holm") for x in h["hypotheses"] for k in x)
    assert {(t["benchmark"], t["id"]) for t in h["group_tests"]} == {("livecodebench-pro-25q2", "K2"),
                                                                     ("livecodebench-pro-25q2", "K3")}
    text = readme()
    assert "scicode/results/hypotheses.json" not in text and not re.search(r"sha256 `[0-9a-f]{64}`\)\.", text)
    assert "Amendment 2" in (BENCH / "PROTOCOL.md").read_text(encoding="utf-8")


def test_k3_robustness_and_reading():
    on, off, b = accepted("lfm3-1.7b"), accepted("lfm3-1.7b-nothink"), accepted("bielik-11b-v3.1")
    ids = sorted(on)
    d = {t: off[t] - on[t] / 2 - b[t] / 2 for t in ids}
    mean = sum(d.values()) / len(ids)
    contests = {}
    for t in ids:
        contests.setdefault(re.match(r"\d+", t).group(0), []).append(d[t])
    g = len(contests)
    se = math.sqrt(g / (g - 1) * sum(sum(x - mean for x in v) ** 2 for v in contests.values())) / len(ids)
    pos = sum(1 for v in contests.values() if sum(v) > 0)
    neg = sum(1 for v in contests.values() if sum(v) < 0)
    p_sign = sum(math.comb(pos + neg, i) for i in range(min(pos, neg) + 1)) / 2 ** (pos + neg)
    r = json.loads((RESULTS / "hypotheses.json").read_text(encoding="utf-8"))["k3_robustness"]
    assert r["clustered_by_contest"]["contests"] == g and math.isclose(r["clustered_by_contest"]["se"], 100 * se)
    assert math.isclose(r["clustered_by_contest"]["z"], mean / se)
    assert (r["sign_test_contests"]["positive"], r["sign_test_contests"]["negative"]) == (pos, neg)
    assert math.isclose(r["sign_test_contests"]["p_one_sided"], p_sign)
    section = readme().split("## Hypotheses")[1].split("## Exploratory")[0]
    assert cells(section, "| SE clustered by contest |")[1:4] == [f"{100 * mean:+.2f} ± {100 * se:.2f}",
                                                                   f"{mean / se:+.2f}", f"{g} contests"]
    assert f"{pos} with D > 0, {neg} with D < 0" in section and f"p = {p_sign:.2g}" in section
    diff = {t: r["difficulty"] for t, r in rows("lfm3-1.7b").items()}
    for level in ("easy", "medium"):
        dl, sel, zl = paired([d[t] for t in ids if diff[t] == level])
        assert cells(section, f"| {level} only")[1:3] == [f"{100 * dl:+.2f} ± {100 * sel:.2f}", f"{zl:+.2f}"]
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))["runs"]["lfm3-1.7b-nothink"]
    rs = raw["reasoning"]
    assert rs["answers"] == N and rs["accepted"] == sum(off.values())
    k3 = next(x for x in json.loads((RESULTS / "hypotheses.json").read_text(encoding="utf-8"))["hypotheses"]
              if x["id"] == "K3")
    assert (f"**K3** refuted under the pre-registered switch (`enable_thinking: false`): with the switch off LFM3 "
            f"keeps most of its lead (D = {k3['value']:+.2f} ± {k3['se']:.2f}, z = {k3['z']:+.2f}); the switch does "
            f"not remove reasoning ({rs['closing_think']}/{rs['answers']} answers reason and close `</think>`), so "
            "how much of the lead thinking itself buys is undetermined.") in " ".join(section.split())


def test_rejudge_and_test_zip_provenance():
    rj = json.loads((RESULTS / "rejudge.json").read_text(encoding="utf-8"))
    text = readme()
    deviations = text.split("## Deviations")[1]
    for run in RUNS:
        w = rj["variants"]["whole_answer"][run]
        official = sum(r["accepted"] for r in rows(run).values())
        assert w["accepted_official"] == official
        assert w["accepted_variant"] == official - len(w["lost"]) + len(w["gained"]) and w["changed_code"] == len(w["results"])
        assert all(rows(run)[p]["accepted"] for p in w["lost"]) and not any(rows(run)[p]["accepted"] for p in w["gained"])
        assert cells(deviations, f"| {run} | ")[1:3] == [str(official), str(w["accepted_variant"])]
    bp = rj["variants"]["bits_prefix"]["bielik-11b-v3.1"]
    ce = sorted(t for t, r in rows("bielik-11b-v3.1").items() if r["category"] == "compile_error")
    assert sorted(bp["results"]) == ce and bp["problems"] == len(ce) and sum(bp["categories"].values()) == len(ce)
    protocol = (BENCH / "PROTOCOL.md").read_text(encoding="utf-8")
    pinned = re.search(r"LiveCodeBench-Pro-Testcase\]\([^)]*\)\s*@\s*`([0-9a-f]{40})`", protocol).group(1)
    tests = [result(run)["provenance"]["tests"] for run in RUNS]
    assert len({json.dumps({k: v for k, v in t.items() if k not in ("file", "step")}, sort_keys=True)
                for t in tests}) == 1  # the same manifest for all three runs
    for run, t in zip(RUNS, tests):
        assert t["revision"] == pinned and len(t["zip_sha256"]) + len(t["missing"]) == N
        assert sorted(t["missing"]) == sorted(p for p, r in rows(run).items() if not r["has_tests"])
        assert f"tests.json sha256 `{t['sha256']}`" in text


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


def test_reasoning_labels_match_the_committed_raw_outputs_json():
    """Without the raw archive: every reasoning count README prints (Bielik's label in the results table, the
    reasoning table, K3's reading) is the one in the committed results/raw-outputs.json, and that file agrees with
    the result files on answers and accepted problems."""
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))["runs"]
    text = readme()
    flat = " ".join(text.split())
    for run in RUNS:
        rs = raw[run]["reasoning"]
        acc = sum(1 for r in rows(run).values() if r["accepted"])
        assert rs["answers"] == N and rs["accepted"] == acc, run
        assert 0 <= rs["accepted_closing_think"] <= min(rs["accepted"], rs["closing_think"]) <= rs["answers"], run
        assert 0 <= rs["think_end_then_fence"] <= rs["closing_think"], run
        c = cells(text, f"| {run} | {result(run)['other_metrics']['output_tokens']['mean']:.1f} / ")
        share = rs["median_share_before_last_think_end"]
        assert c[5:8] == [f"{rs['closing_think']} of {rs['answers']}",
                          "" if share is None else f"{100 * share:.1f}%",
                          f"{rs['accepted_closing_think']} of {rs['accepted']}"], run
    b = raw["bielik-11b-v3.1"]["reasoning"]
    label = cells(text, "| Bielik 11B v3.1 (`bielik-11b-v3.1`) |")[1]
    assert label == (f"no reasoning switch through the API; {b['closing_think']}/{b['answers']} answers close a "
                     "`</think>` draft")
    off = raw["lfm3-1.7b-nothink"]["reasoning"]
    assert (f"the switch does not remove reasoning ({off['closing_think']}/{off['answers']} answers reason and close "
            "`</think>`)") in flat


def test_files_fit_the_repo():
    for path in RESULTS.iterdir():
        assert path.stat().st_size <= 10 * 1024 * 1024, path


RAW_ARCHIVE = Path(os.environ.get("LCBPRO_RAW_ARCHIVE", Path.home() / "Documents/GitHub/labaj-agency/out/"
                                                                       "coding-group/box/export.tgz"))
ARCHIVE_PREFIX = "lcbpro/research/api-benchmarks/livecodebench-pro-25q2/out"


def raw_generations():
    """run -> raw generations.jsonl bytes, from the archive (LFM3 runs) and out/ (Bielik); None when absent."""
    import tarfile
    local = BENCH / "out" / "bielik-11b-v3.1" / "generations.jsonl"
    if not RAW_ARCHIVE.is_file() or not local.is_file():
        return None
    with tarfile.open(RAW_ARCHIVE) as t:
        data = {run: t.extractfile(f"{ARCHIVE_PREFIX}/{run}/generations.jsonl").read()
                for run in ("lfm3-1.7b", "lfm3-1.7b-nothink")}
    return {**data, "bielik-11b-v3.1": local.read_bytes()}


def test_reasoning_counts_recounted_from_the_raw_outputs():
    import hashlib
    import statistics
    import pytest
    data = raw_generations()
    if data is None:
        pytest.skip(f"raw outputs not on this machine ({RAW_ARCHIVE}, out/bielik-11b-v3.1)")
    raw = json.loads((RESULTS / "raw-outputs.json").read_text(encoding="utf-8"))["runs"]
    text = " ".join(readme().split())
    for run, blob in data.items():
        assert hashlib.sha256(blob).hexdigest() == result(run)["raw_outputs"]["sha256"], run
        last = {}
        for line in blob.decode("utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                last[r["problem_id"]] = r
        ok = [r for r in last.values() if r["status"] == "ok"]
        closing = [r for r in ok if "</think>" in r["output"]]
        acc = {t for t, r in rows(run).items() if r["accepted"]}
        share = statistics.median(r["output"].rindex("</think>") / len(r["output"]) for r in closing)
        want = {"answers": len(ok), "closing_think": len(closing),
                "median_share_before_last_think_end": round(share, 4), "accepted": len(acc),
                "accepted_closing_think": sum(1 for r in closing if r["problem_id"] in acc),
                "think_end_then_fence": sum(1 for r in closing if "</think>```" in r["output"])}
        assert raw[run]["reasoning"] == want, run
        assert (f"| {run} |" in text and f"| {len(closing)} of {len(ok)} | {100 * round(share, 4):.1f}% | "
                f"{want['accepted_closing_think']} of {len(acc)} |" in text), run
    bielik = raw["bielik-11b-v3.1"]["reasoning"]
    assert (f"no reasoning switch through the API; {bielik['closing_think']}/{bielik['answers']} answers close a "
            "`</think>` draft") in text
