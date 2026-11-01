"""PIQA T06 (benchmarks/piqa/piqa.py).

Two layers:
- logic on dummies, no network (each test names the mutation it must catch);
- independent recompute of every number in results/PIQA.md from the raw files (sha256 checked), WITHOUT importing
  piqa.py: each expected line or row is built here with its own formatting and must appear in the report as is.
  A wrong value, a swapped column, another CI level, a changed tolerance or verdict in piqa.py fails here.
Run: pytest tests/test_piqa.py
"""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "benchmarks" / "piqa"
RAW = DIR / "results" / "raw"
REPORT = DIR / "results" / "PIQA.md"

# published control, Pythia repo @ a19eecb, pythia-1b-0shot-global_step143000 (copied, not imported)
PUB = {"acc": 0.7040261153427638, "acc_stderr": 0.010650414317148112,
       "acc_norm": 0.705114254624592, "acc_norm_stderr": 0.010639030620156987, "n": 1838}


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
    assert r["pick_acc"] == 0 and r["pick_acc_norm"] == 1
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
    # catches: wrong seed/benchmark in the key, selection by highest hash, unsorted output, duplicates accepted
    ids = [f"id{i}" for i in range(50)]
    key = lambda s: hashlib.sha256(f"20261028|piqa|piqa|{s}".encode()).hexdigest()
    assert m.panel_indices(ids, n=10) == sorted(sorted(range(50), key=lambda i: key(ids[i]))[:10])
    assert m.panel_indices(ids, n=500) == list(range(50))
    with pytest.raises(ValueError):
        m.panel_indices(["a", "a"], n=1)


def test_verdict_thresholds(m):
    # catches: thresholds off by one or on the signed z
    assert m.verdict(3.0) == "pewne" and m.verdict(-3.0) == "pewne"
    assert m.verdict(2.99) == "prawdopodobne" and m.verdict(-2.0) == "prawdopodobne" and m.verdict(1.99) == "szum"


# ---------- independent recompute of the report ----------

def f4(x):
    return f"{x:.4f}".replace(".", ",").replace("-", "−")


def f2(x):
    return f"{x:.2f}".replace(".", ",").replace("-", "−")


def verdict(z):
    return "pewne" if abs(z) >= 3 else ("prawdopodobne" if abs(z) >= 2 else "szum")


def load(name):
    with gzip.open(RAW / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(x) for x in f]


@pytest.fixture(scope="module")
def d():
    if not REPORT.exists():
        pytest.skip("no results/PIQA.md")
    for line in (RAW / "SHA256SUMS").read_text().splitlines():
        h, name = line.split()
        assert hashlib.sha256((RAW / name).read_bytes()).hexdigest() == h, name
    s, p = load("slayer-1.06"), load("pythia-1b-v0")
    key = lambda q: hashlib.sha256(("20261028|piqa|piqa|" + q["source_id"]).encode()).hexdigest()
    panel = sorted(sorted(range(len(s)), key=lambda i: key(s[i]))[:200])
    return {"s": s, "p": p, "panel": panel, "text": REPORT.read_text(encoding="utf-8")}


def pick_norm(q):
    return 0 if q["logprob"][0] / q["chars"][0] >= q["logprob"][1] / q["chars"][1] else 1


def pick_raw(q):
    return 0 if q["logprob"][0] >= q["logprob"][1] else 1


def part(lines, idx):
    return lines if idx is None else [lines[i] for i in idx]


def stats(lines):
    x = np.array([float(pick_norm(q) == q["gold"]) for q in lines])
    n = len(x)
    means = x[np.random.default_rng(20261028).integers(0, n, size=(10000, n))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    picks = [pick_norm(q) for q in lines]
    return {"n": n, "v": x.mean(), "se": x.std(ddof=1) / math.sqrt(n), "lo": lo, "hi": hi,
            "acc": np.mean([pick_raw(q) == q["gold"] for q in lines]),
            "sol1": picks.count(0) / n, "most": max(picks.count(0), picks.count(1)) / n}


def has(text, s):
    assert s in text, f"not in PIQA.md: {s}"


def test_result_rows(d):
    for name, lines in (("Slayer 1.06", d["s"]), ("Pythia-1B v0", d["p"])):
        for label, idx in (("full validation", None), ("Space panel", d["panel"])):
            r = stats(part(lines, idx))
            has(d["text"], f"| {name} | {label} | {r['n']} | {f4(r['v'])} | {f4(r['se'])} | {f4(r['lo'])}–{f4(r['hi'])} | "
                           f"{f4(r['acc'])} | {f4(r['sol1'])} | {f4(r['most'])} |")


def test_headline_and_panel_gap(d):
    sf, sp = stats(d["s"]), stats(part(d["s"], d["panel"]))
    pf, pp = stats(d["p"]), stats(part(d["p"], d["panel"]))
    has(d["text"], f"full validation split: {f4(sf['v'])} (n 1838, CI95 {f4(sf['lo'])}–{f4(sf['hi'])}). "
                   f"Space panel: {f4(sp['v'])} (n 200, CI95 {f4(sp['lo'])}–{f4(sp['hi'])}).")
    has(d["text"], f"(Slayer {f2(100 * (sp['v'] - sf['v']))} pts, Pythia {f2(100 * (pp['v'] - pf['v']))} pts)")


def test_baselines_and_ties(d):
    g_full = [q["gold"] for q in d["s"]]
    g_pan = [q["gold"] for q in part(d["s"], d["panel"])]
    maj = lambda g: max(g.count(0), g.count(1)) / len(g)
    has(d["text"], f"Baselines: random {f4(0.5)}; majority (share of the most frequent correct option) {f4(maj(g_full))} "
                   f"on the full split (n 1838) and {f4(maj(g_pan))} on the panel (n 200); share of option 1 among correct "
                   f"answers {f4(g_full.count(0) / 1838)} (full) and {f4(g_pan.count(0) / 200)} (panel).")
    ties = lambda L: (sum(q["logprob"][0] == q["logprob"][1] for q in L),
                      sum(q["logprob"][0] / q["chars"][0] == q["logprob"][1] / q["chars"][1] for q in L))
    (sa, sn), (pa, pn) = ties(d["s"]), ties(d["p"])
    has(d["text"], f"acc {sa} and acc_norm {sn} for Slayer, acc {pa} and acc_norm {pn} for Pythia (full split)")


def test_diagnostics(d):
    for name, L in (("Slayer 1.06", d["s"]), ("Pythia-1B v0", d["p"])):
        nll = [-q["logprob"][q["gold"]] for q in L]
        by = [q["bytes_cont"][q["gold"]] for q in L]
        mean_bpb = sum(a / (math.log(2) * b) for a, b in zip(nll, by)) / len(L)
        pooled = sum(nll) / (math.log(2) * sum(by))
        uneq = [q for q in L if q["chars"][0] != q["chars"][1]]
        longer = lambda q: 0 if q["chars"][0] > q["chars"][1] else 1
        ln = sum(pick_norm(q) == longer(q) for q in uneq) / len(uneq)
        la = sum(pick_raw(q) == longer(q) for q in uneq) / len(uneq)
        has(d["text"], f"| {name} | {f4(mean_bpb)} | {f4(pooled)} | {f4(ln)} | {f4(la)} |")
    uneq = [q for q in d["s"] if q["chars"][0] != q["chars"][1]]
    gl = sum(q["gold"] == (0 if q["chars"][0] > q["chars"][1] else 1) for q in uneq) / len(uneq)
    has(d["text"], f"on the {len(uneq)} questions whose options differ in length (characters); the correct option is the "
                   f"longer one in {f4(gl)} of them")


def test_panel_digest(d):
    dig = hashlib.sha256("\n".join(d["s"][i]["source_id"] for i in d["panel"]).encode()).hexdigest()
    has(d["text"], f"joined with `\\n`: `{dig}`")


def test_control(d):
    ours = {"acc": stats(d["p"])["acc"], "acc_norm": stats(d["p"])["v"]}
    for metric in ("acc", "acc_norm"):
        diff = 100 * (ours[metric] - PUB[metric])
        tol = max(2.0, 200 * PUB[f"{metric}_stderr"])
        has(d["text"], f"| {metric} | {f4(ours[metric])} | {f4(PUB[metric])} | {f2(diff)} | {f2(tol)} | "
                       f"{'yes' if abs(diff) <= tol else 'no'} |")
    se = math.sqrt(PUB["acc_norm"] * (1 - PUB["acc_norm"]) / PUB["n"])
    g = [q["gold"] for q in d["s"]]
    maj = max(g.count(0), g.count(1)) / len(g)
    has(d["text"], f"lies {f2((PUB['acc_norm'] - 0.5) / se)} standard errors over the random baseline and "
                   f"{f2((PUB['acc_norm'] - maj) / se)} over the majority baseline (standard error {f4(se)})")
    passed = all(abs(ours[k] - PUB[k]) <= max(0.02, 2 * PUB[f"{k}_stderr"]) for k in ours) and PUB["acc_norm"] - max(0.5, maj) > 2 * se
    has(d["text"], f"Control passed: {'yes' if passed else 'no'}.")


def test_comparisons(d):
    for label, idx in (("full", None), ("panel", d["panel"])):
        S, P = part(d["s"], idx), part(d["p"], idx)
        r = stats(S)
        g = [q["gold"] for q in S]
        maj = max(g.count(0), g.count(1)) / len(g)
        for name, base in (("random", 0.5), ("majority", maj)):
            z = (r["v"] - base) / r["se"]
            has(d["text"], f"| Slayer 1.06 − {name} baseline | {label} | {f2(100 * (r['v'] - base))} | {f2(z)} | {verdict(z)} |")
        diff = np.array([float(pick_norm(a) == a["gold"]) - float(pick_norm(b) == b["gold"]) for a, b in zip(S, P)])
        se = diff.std(ddof=1) / math.sqrt(len(diff))
        z = diff.mean() / se
        has(d["text"], f"| Slayer 1.06 − Pythia-1B v0 (paired SE) | {label} | {f2(100 * diff.mean())} | {f2(z)} | {verdict(z)} |")
        if label == "full":
            has(d["text"], f"Slayer 1.06 scores {f4(r['v'])} on the full split, {f2(100 * (r['v'] - 0.5))} pts over the random "
                           f"baseline (z {f2((r['v'] - 0.5) / r['se'])}, {verdict((r['v'] - 0.5) / r['se'])})")


def test_gpu_repeats(d):
    names = [n.replace(".jsonl.gz", "") for n in (l.split()[1] for l in (RAW / "SHA256SUMS").read_text().splitlines())
             if n.startswith("pythia-1b-v0_") and n.endswith(".jsonl.gz")]
    assert names
    for k in names:
        L = load(k)
        device = json.loads((RAW / f"{k}.meta.json").read_text())["device"]
        acc = sum(pick_norm(q) == q["gold"] for q in L) / len(L)
        differ = sum(pick_norm(a) != pick_norm(b) for a, b in zip(d["p"], L))
        mx = max(abs(x - y) for a, b in zip(d["p"], L) for x, y in zip(a["logprob"], b["logprob"]))
        has(d["text"], f"| {device} | {len(L)} | {f4(acc)} | {differ} | {mx:.1e} |")
