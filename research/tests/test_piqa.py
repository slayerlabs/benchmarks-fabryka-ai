"""PIQA T06 (benchmarks/piqa/piqa.py).

Three layers:
- logic on dummies, no network (each test names the mutation it must catch);
- independent recompute of the key numbers of results/piqa.json from the raw files, without importing piqa.py;
- the report PIQA.md is exactly what `piqa.py report` renders from piqa.json.
Run: pytest tests/test_piqa.py
"""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "benchmarks" / "piqa"
RAW = DIR / "results" / "raw"
RESULT = DIR / "results" / "piqa.json"


@pytest.fixture(scope="module")
def m():
    spec = importlib.util.spec_from_file_location("piqa_mod", DIR / "piqa.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- logic on dummies ----------

def sample(lls, target, sol1="ab", sol2="abcdefgh"):
    return {"filtered_resps": [[lls[0], False], [lls[1], False]], "arguments": [["Q", " " + sol1], ["Q", " " + sol2]],
            "target": target, "acc": 0.0, "acc_norm": 0.0}


def test_question_row_normalises_by_option_chars(m):
    # catches: acc_norm divided by bytes with the space, by tokens, or not at all
    row = {"goal": "g", "sol1": "ab", "sol2": "abcdefgh", "label": 1}
    r = m.question_row(sample([-3.0, -8.0], 1), 0, row)
    assert r["pick_acc"] == 0  # larger raw log-probability
    assert r["pick_acc_norm"] == 1  # -8/8 > -3/2
    assert r["chars"] == [2, 8] and r["bytes_cont"] == [3, 9]


def test_question_row_keeps_option_order(m):
    # catches: options swapped or gold taken from the pick
    row = {"goal": "g", "sol1": "xx", "sol2": "yy", "label": 0}
    r = m.question_row(sample([-1.0, -2.0], 0, "xx", "yy"), 7, row)
    assert r["logprob"] == [-1.0, -2.0] and r["gold"] == 0 and r["idx"] == 7


def test_source_id_is_hash_of_canonical_row(m):
    # catches: key order or separators changing the source id
    a = m.source_id({"goal": "g", "sol1": "a", "sol2": "b", "label": 1})
    b = m.source_id({"label": 1, "sol2": "b", "sol1": "a", "goal": "g"})
    assert a == b == hashlib.sha256(b'{"goal":"g","label":1,"sol1":"a","sol2":"b"}').hexdigest()


def test_panel_is_lowest_hashes_in_split_order(m):
    # catches: wrong seed/benchmark in the key, selection by highest hash, unsorted output
    ids = [f"id{i}" for i in range(50)]
    key = lambda s: hashlib.sha256(f"20261028|piqa|piqa|{s}".encode()).hexdigest()
    want = sorted(sorted(range(50), key=lambda i: key(ids[i]))[:10])
    assert m.panel_indices(ids, n=10) == want
    assert m.panel_indices(ids, n=500) == list(range(50))
    with pytest.raises(ValueError):
        m.panel_indices(["a", "a"], n=1)


def test_paired_se_and_verdicts(m):
    # catches: unpaired SE, sign flipped, thresholds off by one
    a = [{"acc_norm": x} for x in (1, 1, 0, 1)]
    b = [{"acc_norm": x} for x in (0, 1, 0, 0)]
    p = m.paired(a, b, "acc_norm")
    d = [1, 0, 0, 1]
    se = math.sqrt(sum((x - 0.5) ** 2 for x in d) / 3 / 4)
    assert p["difference"] == 0.5 and abs(p["se"] - se) < 1e-12
    assert m.verdict(3.0) == "pewne" and m.verdict(-2.0) == "prawdopodobne" and m.verdict(1.99) == "szum"


# ---------- independent recompute from the raw files ----------

def raw(name):
    with gzip.open(RAW / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f]


@pytest.fixture(scope="module")
def data():
    if not RESULT.exists():
        pytest.skip("no results/piqa.json")
    for line in (RAW / "SHA256SUMS").read_text().splitlines():
        h, name = line.split()
        assert hashlib.sha256((RAW / name).read_bytes()).hexdigest() == h, name
    return json.loads(RESULT.read_text()), raw("slayer-1.06"), raw("pythia-1b-v0")


def own_panel(lines):
    key = lambda s: hashlib.sha256(("20261028|piqa|piqa|" + s).encode()).hexdigest()
    order = sorted(range(len(lines)), key=lambda i: key(lines[i]["source_id"]))
    return set(order[:200])


def own_acc_norm(lines, keep=None):
    picks = []
    for i, r in enumerate(lines):
        if keep is not None and i not in keep:
            continue
        a = r["logprob"][0] / r["chars"][0]
        b = r["logprob"][1] / r["chars"][1]
        picks.append((0 if a >= b else 1) == r["gold"])
    return sum(picks) / len(picks), len(picks)


def test_raw_acc_norm_agrees_with_lm_eval(data):
    _, s, p = data
    for lines in (s, p):
        assert all(r["acc_norm"] == float(r["pick_acc_norm"] == r["gold"]) for r in lines)


def test_values_recomputed(data):
    o, s, p = data
    panel = own_panel(s)
    for name, lines in (("slayer-1.06", s), ("pythia-1b-v0", p)):
        for part, keep in (("full", None), ("panel", panel)):
            v, n = own_acc_norm(lines, keep)
            got = o["models"][name][part]["acc_norm"]
            assert got["n"] == n and abs(got["value"] - v) < 1e-12, (name, part)
            se = math.sqrt(v * (1 - v) / (n - 1))
            assert abs(got["se"] - se) < 1e-12


def test_baselines_and_control_recomputed(data):
    o, s, p = data
    golds = [r["gold"] for r in s]
    assert o["baselines"]["full"]["majority"] == max(golds.count(0), golds.count(1)) / len(golds)
    v, _ = own_acc_norm(p)
    assert abs(o["control"]["checks"]["acc_norm"]["difference_pts"] - (v - 0.705114254624592) * 100) < 1e-9
    acc = sum((0 if r["logprob"][0] >= r["logprob"][1] else 1) == r["gold"] for r in p) / len(p)
    assert abs(o["control"]["checks"]["acc"]["ours"] - acc) < 1e-12


def test_paired_difference_recomputed(data):
    o, s, p = data
    d = [a["acc_norm"] - b["acc_norm"] for a, b in zip(s, p)]
    mean = sum(d) / len(d)
    se = math.sqrt(sum((x - mean) ** 2 for x in d) / (len(d) - 1) / len(d))
    c = o["comparisons"]["slayer_minus_pythia_full"]
    assert abs(c["difference"] - mean) < 1e-12 and abs(c["se"] - se) < 1e-12


def test_report_is_rendered_from_json(m, data):
    o, _, _ = data
    metas = {}
    assert (DIR / "results" / "PIQA.md").read_text() == m.render(o, metas)
