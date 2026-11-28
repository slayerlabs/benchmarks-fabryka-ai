"""Humanity's Last Exam (no tools): the committed result checked against its stored counts and README.md.

No module of api-benchmarks/hle is imported here. The per-question file (results/bielik-11b-v3.1.jsonl.gz) is
git-ignored: correct answers would reveal HLE answers. So from results/bielik-11b-v3.1.json alone this recounts the
score and stderr from the stored counts (both denominators), the unjudged IDs, the judge agreement tables (agreement
and Cohen's kappa from each confusion table) and the cost total, and checks the numbers printed in README.md. Where
the per-question file is on this machine (HLE_PER_QUESTION, or results/bielik-11b-v3.1.jsonl.gz), its SHA-256 is
checked against README.md and the correct count and the truncation count are recounted from it (skipped otherwise).
The committed results/bielik-11b-v3.1.verdicts.csv (id, verdict, truncated: no question content) is always used to
recompute the score, n, the unjudged IDs and the truncation count. The methodology fields (samples per item, the
section 10 inference record with a reason for every unknown) are checked too.
Needs only pytest and the standard library.
Run: python3 -m pytest research/tests/test_hle_results.py
"""
import csv
import gzip
import hashlib
import json
import math
import os
import re
from pathlib import Path

import pytest

BENCH = Path(os.environ.get("HLE_BENCH", Path(__file__).resolve().parents[1] / "api-benchmarks" / "hle"))
RESULTS = BENCH / "results"
RUN = "bielik-11b-v3.1"
PER_QUESTION = Path(os.environ.get("HLE_PER_QUESTION", RESULTS / f"{RUN}.jsonl.gz"))
N, CORRECT, UNJUDGED = 2158, 117, 5


def result():
    return json.loads((RESULTS / f"{RUN}.json").read_text(encoding="utf-8"))


def readme():
    return (BENCH / "README.md").read_text(encoding="utf-8")


def cells(text, starts):
    line = next(line for line in text.splitlines() if line.startswith(starts))
    return [c.strip() for c in line.strip().strip("|").split("|")]


def score(k, n):
    p = k / n
    return 100 * p, 100 * math.sqrt(p * (1 - p) / n)


def test_score_and_stderr_from_counts():
    res = result()
    full, judged = res["score_with_unresolved_as_incorrect"], res["score_judged_subset_only"]
    assert (full["correct"], full["n"]) == (CORRECT, N)
    assert (judged["correct"], judged["n"]) == (CORRECT, N - UNJUDGED)
    for block in (full, judged):
        s, se = score(block["correct"], block["n"])
        assert (block["accuracy"], block["stderr"]) == (round(s, 4), round(se, 4))
    assert (res["score"], res["stderr"], res["n"]) == (full["accuracy"], full["stderr"], N)
    assert res["n_judged"] == judged["n"] and res["n_unresolved_counted_incorrect"] == UNJUDGED
    assert len(set(res["unresolved_ids"])) == UNJUDGED


def test_readme_numbers():
    text, res = readme(), result()
    s, se = score(CORRECT, N)
    sj, sej = score(CORRECT, N - UNJUDGED)
    assert f"**{s:.2f} ± {se:.2f}** ({CORRECT}/{N})" in text
    row = cells(text, "| Bielik 11B v3.1 | no tools |")
    assert row[2:5] == [f"{s:.2f}", f"{se:.2f}", str(N)]
    assert f"({sj:.2f} ± {sej:.2f} on n={N - UNJUDGED})" in row[6]
    assert f"Score both ways: {s:.2f} ± {se:.2f} (n={N}) vs {sj:.2f} ± {sej:.2f} (n={N - UNJUDGED}" in text
    unjudged = next(line for line in text.splitlines() if line.startswith("- **Unjudged IDs.**"))
    assert re.findall(r"`([0-9a-f]{24})`", unjudged) == res["unresolved_ids"]
    assert f"Calibration error (official harness metric): {res['calibration_error']:.2f}." in text


def kappa(c):
    n = sum(c.values())
    yes_a, yes_b = c["tp_yes_yes"] + c["fn_yes_no"], c["tp_yes_yes"] + c["fp_no_yes"]
    po = (c["tp_yes_yes"] + c["tn_no_no"]) / n
    pe = (yes_a * yes_b + (n - yes_a) * (n - yes_b)) / n ** 2
    return (po - pe) / (1 - pe)


def test_judge_agreement_tables():
    agreement = result()["agreement"]
    pairs = agreement["three_way"] + [agreement["self_agreement_opus4_repeat_100"]]
    for pair in pairs:
        c = pair["confusion"]
        assert sum(c.values()) == pair["n"]
        pct = pair.get("agreement_pct", pair.get("self_agreement_pct"))
        assert pct == round(100 * (c["tp_yes_yes"] + c["tn_no_no"]) / pair["n"], 2)
        assert pair["cohens_kappa"] == round(kappa(c), 4)
    for run in agreement["runs"]:
        assert run["n_judged"] + run["failed"] == run["n_requested"] and len(run["failed_ids"]) == run["failed"]


def test_cost_total():
    res, text = result(), readme()
    b = res["usd_breakdown"]
    parts = (b["main_opus4_all"]["usd"], b["pilot5_opus5"]["usd"], b["recovery_retries_estimate"]["usd_est"],
             b["agreement_stability"]["usd"])
    assert res["usd_total"] == round(sum(parts), 4)
    assert f"= ${b['main_opus4_all']['usd']:.2f}" in text
    assert f"agreement and stability runs ${b['agreement_stability']['usd']:.2f}" in text
    assert f"**Total ≈ ${res['usd_total']:.2f}.**" in text


def test_truncation_recorded_or_marked():
    res, text = result(), readme()
    t = res["truncated"]
    if isinstance(t, int):
        flagged = t / N > 0.05
    else:
        assert set(t) == {"unknown"} and t["unknown"]
        flagged = True
    row = cells(text, "| Bielik 11B v3.1 | no tools |")
    assert ("requires verification" in row[6]) == flagged


@pytest.mark.skipif(not PER_QUESTION.exists(), reason="per-question file is git-ignored and not on this machine")
def test_per_question_file():
    sha = hashlib.sha256(PER_QUESTION.read_bytes()).hexdigest()
    assert f"SHA-256 `{sha}`" in readme()
    with gzip.open(PER_QUESTION, "rt", encoding="utf-8") as f:
        rows = [json.loads(line) for line in f]
    assert len(rows) == N and len({r["question_id"] for r in rows}) == N
    assert sum("yes" in (r.get("judge_correct") or "") for r in rows) == CORRECT
    truncated = sum((r.get("usage") or {}).get("completion_tokens", 0) >= 8192 for r in rows)
    t = result()["truncated"]
    if isinstance(t, int):
        assert t == truncated


def verdicts():
    with (RESULTS / f"{RUN}.verdicts.csv").open(encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def test_verdicts_file_holds_no_content():
    rows = verdicts()
    assert rows[0] == ["id", "verdict", "truncated"]
    body = rows[1:]
    assert len(body) == N and len({r[0] for r in body}) == N
    for r in body:
        assert len(r) == 3 and re.fullmatch(r"[0-9a-f]{24}", r[0])
        assert r[1] in ("yes", "no", "none") and r[2] in ("0", "1")


def test_score_recomputed_from_verdicts():
    res = result()
    body = verdicts()[1:]
    correct = sum(r[1] == "yes" for r in body)
    unjudged = sorted(r[0] for r in body if r[1] == "none")
    assert (correct, len(body)) == (CORRECT, N)
    assert unjudged == sorted(res["unresolved_ids"])
    s, se = score(correct, len(body))
    assert (res["score"], res["stderr"]) == (round(s, 4), round(se, 4))
    sj, sej = score(correct, len(body) - len(unjudged))
    assert (res["score_judged_subset_only"]["accuracy"], res["score_judged_subset_only"]["stderr"]) == (round(sj, 4), round(sej, 4))
    truncated = sum(r[2] == "1" for r in body)
    assert truncated == res["truncated"]
    detail = res["truncated_detail"]
    assert detail["pct"] == round(100 * truncated / N, 2) and detail["limit"] == res["settings"]["max_completion_tokens"]
    assert detail["requires_verification"] == (truncated / N > 0.05)


def test_methodology_record():
    res = result()
    assert res["samples_per_item"] == res["settings"]["trials"] == 1
    assert res["stderr_method"]
    inf = res["inference"]
    for key in ("weights", "dtype", "quantization", "serving_stack", "hardware", "concurrency", "chat_template",
                "system_prompt", "reasoning_mode", "decoding"):
        v = inf[key]
        assert (set(v) == {"unknown"} and v["unknown"].strip()) if isinstance(v, dict) else v.strip(), key
