"""tau3-bench: the committed results recounted from their per-item files alone (no harness, no models, no network).

Run: python3 -m pytest research/tests/test_tau3_bench.py
"""
import gzip
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

D = Path(__file__).resolve().parent.parent / "api-benchmarks" / "tau3-bench"
R = D / "results"
_spec = importlib.util.spec_from_file_location("tau3_summarize", D / "summarize.py")  # other benchmarks have a summarize.py too
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def no_duplicate_keys(path):
    def hook(pairs):
        keys = [k for k, _ in pairs]
        assert len(keys) == len(set(keys)), f"duplicate key in {path}: {keys}"
        return dict(pairs)
    return json.loads(Path(path).read_text(), object_pairs_hook=hook)


def items(name):
    with gzip.open(R / name, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def test_summarize_check_passes():
    r = subprocess.run([sys.executable, str(D / "summarize.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_json_has_no_duplicate_keys():
    for p in R.glob("*.json"):
        no_duplicate_keys(p)


def test_main_result_recount():
    j = no_duplicate_keys(R / "bielik-11b-v3.1.json")
    rows = items("bielik-11b-v3.1.jsonl.gz")
    assert len(rows) == 375 and len({(r["domain"], r["task_id"]) for r in rows}) == 375
    assert {r["reward"] for r in rows} <= {0.0, 1.0, None}
    h = S.headline(rows)
    assert (j["score"], j["stderr"], j["n"]) == (round(h["score"], 2), round(h["stderr"], 2), h["n"]) == (20.81, 2.22, 370)
    unassessed = [r for r in rows if r["reward"] is None]
    assert len(unassessed) == 5 and j["other_metrics"]["unassessed"] == 5
    assert sum(r["source"] == "retry" for r in rows) == 74
    assert j["other_metrics"]["unassessed_as_0"] <= j["score"] <= j["other_metrics"]["unassessed_as_1"]


def test_comparison_recount():
    c = no_duplicate_keys(R / "simulator-comparison.json")
    rows = items("simulator-comparison.jsonl.gz")
    assert {d: sum(r["domain"] == d for r in rows) for d in S.SONNET_DOMAINS} == {"airline": 50, "retail": 114, "telecom": 114}
    got = {r["domain"]: r for r in c["paired_final"]}
    assert [got[d]["n"] for d in S.SONNET_DOMAINS] == [50, 97, 113]
    assert got["retail"]["verdict"] == "borderline" and got["retail"]["after_holm"] == "yes"
    assert got["airline"]["verdict"] == "noise" and got["telecom"]["verdict"] == "noise"


def test_slayer_null():
    j = no_duplicate_keys(R / "slayer1b-1.09-k70000.json")
    assert j["score"] is None and j["stderr"] is None and j["n"] is None and "other_metrics" in j


def test_readme_numbers_match_results():
    text = (D / "README.md").read_text()
    j = json.loads((R / "bielik-11b-v3.1.json").read_text())
    assert f"| {j['score']:.2f} | {j['stderr']:.2f} | 370 of 375 |" in text
    for d, v in j["other_metrics"]["per_domain"].items():
        assert f"| {v['score']:.2f} | {v['stderr']:.2f} | {v['passed']} / {v['n']} | {v['tasks']} |" in text
    c = json.loads((R / "simulator-comparison.json").read_text())
    for r in c["paired_final"]:
        cell = f"{100 * r['diff']:+.2f} ± {100 * r['se']:.2f} | z = {r['z']:.2f} | {r['verdict']} |"
        assert cell in text, cell
    for r in c["paired_first_attempt_only"]:
        assert f"| {r['n']} | {100 * r['diff']:+.2f} ± {100 * r['se']:.2f} | z = {r['z']:.2f} |" in text


def test_readme_hand_typed_numbers():
    text = (D / "README.md").read_text()
    j = json.loads((R / "bielik-11b-v3.1.json").read_text())["other_metrics"]
    assert f"Bounds for the 5 tasks without a reward: {j['unassessed_as_0']:.2f} if all count as 0, {j['unassessed_as_1']:.2f}" in text
    al = j["agent_language"]
    assert f"Bielik answered in Polish in {al['with_polish_agent_message']} of {al['simulations']} simulations" in text
    assert f"{al['agent_messages_polish']} of {al['agent_messages']}" in text
    assert f"{100 * al['pass_rate_polish']:.1f}% against {100 * al['pass_rate_other']:.1f}%" in text
    assert j["retried_tasks"] == 74 and j["retried_with_reward"] == 69
    assert j["retried_by_first_attempt_error"] == {"judge_json": 12, "503": 62}
    assert j["unassessed_by_error"] == {"judge_json": 4, "empty_message": 1}
    st = json.loads((R / "simulator-comparison.json").read_text())["style"]
    h, s = st["haiku"], st["sonnet"]
    for x in (h, s):
        assert f"{x['customer_messages_with_bold']} of {x['customer_messages']}" in text
    assert f"| {h['customer_messages_per_simulation']:.1f} | {s['customer_messages_per_simulation']:.1f} |" in text
    assert f"| {h['words_per_customer_message']:.1f} | {s['words_per_customer_message']:.1f} |" in text
    assert f"| {h['simulations_with_polish_agent_message']} | {s['simulations_with_polish_agent_message']} |" in text
    assert f"| {h['agent_replies_of_5_words_or_less']} of {h['agent_messages']} | {s['agent_replies_of_5_words_or_less']} of {s['agent_messages']} |" in text
