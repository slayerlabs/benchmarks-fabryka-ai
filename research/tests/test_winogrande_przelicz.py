"""results/winogrande.json against an independent recount from the raw files, offline.

Does not import przelicz.py. Reads results/*/winogrande.jsonl.gz and klastry.json (twin-pair ids from the
HF split), recounts acc, correct, SE K and the paired differences, and compares them with the json.

Run: python tests/test_winogrande_przelicz.py
"""
import gzip
import hashlib
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


SHA = {
    "pythia-1b-v0": "c05f2202f5053e88da1f41b572323dc9a12e615544bbd9a7e8b2563c92e794c3",
    "pythia-1b-v0-bos": "1a2500d3a918acc25c58b9214654a17eb02e57254ac6c510a8f883dfccf8ac17",
    "slayer-1.06": "07ca6989f6362323727b9c87be982431a6d4f6d2e2d2cb05f4dfb514f5f49288",
}
SE_KARTY = 0.014  # SE of the published 0.5375 in ORIGINAL.md


def se_analityczne(x):
    """s / sqrt(n) with the sample s (ddof = 1)."""
    m = math.fsum(x) / len(x)
    return math.sqrt(math.fsum((v - m) ** 2 for v in x) / (len(x) - 1) / len(x))


def p_t(t, df):
    return 2 * stats.t.sf(abs(t), df)


TR = {m: trafienia(k) for m, k in KATALOGI.items()}


def test_inputs_have_the_committed_sha256():
    for katalog, sha in SHA.items():
        assert hashlib.sha256((WG / "results" / katalog / "winogrande.jsonl.gz").read_bytes()).hexdigest() == sha, katalog
    assert KL["sha256_parquet"] == "f9d914d1818c0aba98cabdf8af2bc4bd943c462b9c5e7062647e05c2ce3315d1"


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
        assert abs(JSON[m]["se_a"] - se_analityczne(x)) < TOL, m
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
        assert abs(r["se_a"] - se_analityczne(d)) < TOL, a + b


def test_holm_over_the_three_comparisons():
    klucze = ["slayer_minus_pythia", "pythia_bos_minus_pythia", "slayer_minus_pythia_bos"]
    p = {c: p_t(JSON[c]["t"], JSON[c]["df"]) for c in klucze}
    kolejne = sorted(klucze, key=p.get)
    poprawione, najwyzsze = {}, 0.0
    for i, c in enumerate(kolejne):
        najwyzsze = max(najwyzsze, min(1.0, (len(kolejne) - i) * p[c]))
        poprawione[c] = najwyzsze
    for c in klucze:
        assert abs(JSON[c]["p_holm"] - poprawione[c]) < 1e-6, c
        assert JSON[c]["po_holmie"] == ("tak" if poprawione[c] <= 2 * stats.norm.sf(2) else "nie"), c


def test_mde_from_the_binding_se_k_of_slayer_minus_pythia():
    d = [u - v for u, v in zip(TR["slayer"], TR["pythia"])]
    se, _ = se_klastrowe(d)
    z_holm = stats.norm.isf(2 * stats.norm.sf(2) / 3 / 2)  # p for |z| = 2, split over m = 3 comparisons
    r = JSON["mde"]
    assert abs(r["se_roznicy_k"] - se) < TOL
    assert abs(r["z_holm_m3"] - z_holm) < 1e-6
    assert abs(r["pelny"] - (2 + 0.84) * se) < TOL
    assert abs(r["pelny_holm_m3"] - (z_holm + 0.84) * se) < 1e-6
    assert abs(r["panel200"] - (2 + 0.84) * se * math.sqrt(len(d) / 200)) < TOL


def test_snr_divides_the_published_spread_by_se_k():
    # published acc of Pythia v0 as in ORIGINAL.md, 4 decimals
    opublikowane = {"70m": 0.4878, "160m": 0.5328, "410m": 0.5312, "1b": 0.5375, "1.4b": 0.5627, "2.8b": 0.6125,
                    "6.9b": 0.6180, "12b": 0.6440}
    se, _ = se_klastrowe(TR["pythia"])
    for nazwa, rozmiary in [("8_rozmiarow", list(opublikowane)), ("trojka_410m_1b_1.4b", ["410m", "1b", "1.4b"]),
                            ("definicja_400m_3b", ["410m", "1b", "1.4b", "2.8b"])]:
        acc = [round(opublikowane[r] * 1267) / 1267 for r in rozmiary]
        sd = stats.tstd(acc)
        r = JSON["snr"][nazwa]
        assert r["modele"] == rozmiary, nazwa
        assert abs(r["rozrzut"] - sd) < TOL, nazwa
        assert abs(r["iloraz_k"] - sd / se) < 1e-6, nazwa


def test_gap_to_published_uses_the_conservative_se():
    se_k, _ = se_klastrowe(TR["pythia"])
    d = math.fsum(TR["pythia"]) / len(TR["pythia"]) - 0.5375
    se = math.sqrt(se_k ** 2 + SE_KARTY ** 2)
    r = JSON["pythia_wobec_opublikowanego"]
    assert abs(r["roznica"] - d) < TOL
    assert abs(r["se"] - se) < TOL
    assert abs(r["t"] - d / se) < 1e-6
    assert r["werdykt"] == werdykt_t(d / se, r["df"])


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
