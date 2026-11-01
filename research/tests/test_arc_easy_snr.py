"""ARC-Easy SNR and baselines (benchmarks/arc-easy/snr_and_baselines.py): logic on dummies, no network.

The last test recomputes the card numbers from the raw inputs stored in results/snr_baselines.json by a separate
path (no import of the script). Run: pytest tests/test_arc_easy_snr.py
"""
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "benchmarks" / "arc-easy" / "snr_and_baselines.py"
RESULT = ROOT / "benchmarks" / "arc-easy" / "results" / "snr_baselines.json"


@pytest.fixture(scope="module")
def m():
    spec = importlib.util.spec_from_file_location("arc_snr", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_git_blob_sha_matches_git(m):
    assert m.git_blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"  # git hash-object


def test_select_files_latest_date_double_underscore_and_dedup_split(m):
    paths = [
        "pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json",
        "pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_01-02-2023-00-00-00.json",
        "pythia-2.8b/zero-shot/pythia-2.8b-0shot-global_step143000__eval_results_11-24-2022-16-20-50.json",
        "pythia-1b-deduped/zero-shot/pythia-1b-deduped-0shot-global_step143000_eval_results_11-28-2022-18-07-27.json",
        "pythia-160m/zero-shot/pythia-160m-0shot-global_step71500_eval_results_12-30-2022-23-06-54.json",
        "pythia-1b/five-shot/pythia-1b-5shot-global_step143000_eval_results_11-28-2022-15-14-35.json",
    ]
    sel = m.select_files(paths, deduped=False)
    assert sel == {"pythia-1b": paths[1], "pythia-2.8b": paths[2]}
    assert m.select_files(paths, deduped=True) == {"pythia-1b-deduped": paths[3]}
    assert m.sizes_without_file(paths, deduped=False) == ["pythia-160m"]


def test_snr_ddof_and_typical_se(m):
    r1 = m.snr([0.4, 0.6], 1, 0.1)
    r0 = m.snr([0.4, 0.6], 0, 0.1)
    assert r1["spread"] == pytest.approx(math.sqrt(0.02))
    assert r0["spread"] == pytest.approx(0.1)
    assert r0["snr"] == pytest.approx(1.0)
    assert m.typical_se(0.5, 100) == pytest.approx(0.05)


def test_majority_tie_and_index_mapping(m):
    assert m.answer_index(["1", "2", "3", "4"], "3") == 2
    r = m.majority([0, 1, 1, 0, 2])
    assert r["top"] == [0, 1] and r["share"] == pytest.approx(0.4)
    assert m.random_baseline([4, 4, 2]) == pytest.approx((0.25 + 0.25 + 0.5) / 3)


def test_majority_variants_flag_falsification(m):
    rows = [(["A", "B", "C", "D"], "C")] * 6 + [(["1", "2", "3", "4"], "1")] * 5
    main, var = m.majority_variants(rows)
    assert main["top"] == [2]
    assert var["literal_label"]["top"] == ["C"] and var["literal_label"]["same_top_as_main"]
    assert var["letter_labels_only"]["falsifies"]  # share 6/6 vs 6/11


@pytest.mark.skipif(not RESULT.exists(), reason="run the script first")
def test_card_numbers_recomputed_independently():
    d = json.loads(RESULT.read_text())
    accs = [v["acc"] for v in d["inputs"]["pythia"]["models"]["non_deduped"].values()]
    k = len(accs)
    mean = sum(accs) / k
    sd1 = math.sqrt(sum((a - mean) ** 2 for a in accs) / (k - 1))
    n = d["inputs"]["dataset"]["n"]
    se = math.sqrt(mean * (1 - mean) / n)
    assert (k, n) == (5, 2376)
    assert f"{sd1:.4f}" == "0.1167" and f"{se:.4f}" == "0.0101" and f"{sd1 / se:.2f}" == "11.57"
    counts = d["inputs"]["dataset"]["answer_index"]["counts"]
    assert sum(counts.values()) == n
    assert f"{max(counts.values()) / n:.4f}" == "0.2664"
