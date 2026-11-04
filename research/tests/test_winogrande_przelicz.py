"""results/winogrande.json against an independent recount from the raw files, offline.

Does not import przelicz.py. Reads results/*/winogrande.jsonl.gz and klastry.json (twin-pair ids from the
HF split), recounts acc, correct, SE K and the paired differences, and compares them with the json.

Run: python tests/test_winogrande_przelicz.py
"""
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

from scipy import stats

WG = Path(__file__).resolve().parent.parent / "benchmarks" / "winogrande"
JSON = json.loads((WG / "results" / "winogrande.json").read_text())
KL = json.loads((WG / "klastry.json").read_text())
KATALOGI = {"pythia": "pythia-1b-v0", "pythia_bos": "pythia-1b-v0-bos", "slayer": "slayer-1.06"}
TOL = 1e-9


def trafienia(katalog):
    """acc per item recounted from logliki: the higher loglik wins, a tie goes to option 1."""
    out = {}
    with gzip.open(WG / "results" / katalog / "winogrande.jsonl.gz", "rt") as f:
        for linia in f:
            r = json.loads(linia)
            wybor = 2 if r["logliki"][1] > r["logliki"][0] else 1
            out[r["doc_id"]] = 1.0 if wybor == KL["zloto"][r["doc_id"]] else 0.0
    return [out[i] for i in range(len(out))]


def se_klastrowe(x):
    """Cluster-robust SE: residuals summed inside each twin pair, k/(k-1) correction."""
    grupy = defaultdict(list)
    for c, v in zip(KL["klaster"], x):
        grupy[c].append(v)
    srednia = math.fsum(x) / len(x)
    k = len(grupy)
    suma = math.fsum((math.fsum(g) - len(g) * srednia) ** 2 for g in grupy.values())
    return math.sqrt(suma * k / (k - 1)) / len(x), k


def werdykt_t(t, df):
    p = 2 * stats.t.sf(abs(t), df)
    if p <= 2 * stats.norm.sf(3):
        return "pewne"
    return "prawdopodobne" if p <= 2 * stats.norm.sf(2) else "szum"


TR = {m: trafienia(k) for m, k in KATALOGI.items()}


def test_twin_pairs_are_adjacent_and_counted():
    ids = KL["klaster"]
    assert len(ids) == 1267
    rozmiary = defaultdict(int)
    for i, c in enumerate(ids):
        assert c == 0 if i == 0 else c - ids[i - 1] in (0, 1)
        rozmiary[c] += 1
    assert sorted(set(rozmiary.values())) == [1, 2]
    assert (KL["pary"], KL["pojedyncze"], KL["k"]) == (284, 699, 983)
    assert sum(1 for v in rozmiary.values() if v == 2) == 284 and len(rozmiary) == 983


def test_each_model_acc_correct_and_se_k():
    for m, x in TR.items():
        se, k = se_klastrowe(x)
        assert JSON[m]["correct"] == int(sum(x)), m
        assert abs(JSON[m]["acc"] - sum(x) / len(x)) < TOL, m
        assert abs(JSON[m]["se_k"] - se) < TOL, m
        assert JSON[m]["k"] == k == 983, m


def test_paired_differences_se_k_t_and_verdict():
    for a, b in [("slayer", "pythia"), ("pythia_bos", "pythia"), ("slayer", "pythia_bos")]:
        d = [u - v for u, v in zip(TR[a], TR[b])]
        r = JSON[f"{a}_minus_{b}"]
        se, k = se_klastrowe(d)
        diff = math.fsum(d) / len(d)
        assert abs(r["roznica"] - diff) < TOL, a + b
        assert abs(r["se_k"] - se) < TOL, a + b
        assert abs(r["t"] - diff / se) < 1e-6, a + b
        assert r["df"] == k - 1
        assert r["werdykt"] == werdykt_t(diff / se, k - 1), a + b


def test_control_is_paired_with_always_option_2():
    stala = [1.0 if g == 2 else 0.0 for g in KL["zloto"]]
    assert abs(JSON["bazy"]["wiekszosciowa"] - sum(stala) / len(stala)) < TOL
    for m in ("pythia", "slayer"):
        d = [u - v for u, v in zip(TR[m], stala)]
        se, k = se_klastrowe(d)
        r = JSON[f"{m}_wobec_b"]
        assert abs(r["roznica"] - math.fsum(d) / len(d)) < TOL, m
        assert abs(r["se_k"] - se) < TOL, m
        assert r["werdykt"] == werdykt_t(r["roznica"] / se, k - 1), m


if __name__ == "__main__":
    failed = 0
    for name, fn in list(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print("ok", name)
        except Exception as exc:
            failed += 1
            print("FAIL", name, type(exc).__name__, exc)
    if failed:
        sys.exit(1)
    print("OK")
