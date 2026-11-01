"""ARC-Easy SNR and baselines (benchmarks/arc-easy/snr_and_baselines.py).

Three layers:
- logic on dummies, no network (each test names the mutation it must catch);
- every number in the card rows "Bazy" and "SNR: ..." bound to one key of results/snr_baselines.json, in order;
- independent recompute of the card numbers from the raw sources (HF parquet from the local cache, Pythia files
  from GitHub by commit sha) without importing the author's script; skipped when the source is unavailable.
Run: pytest tests/test_arc_easy_snr.py
"""
import hashlib
import importlib.util
import json
import math
import os
import re
import statistics
import urllib.request
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "benchmarks" / "arc-easy" / "snr_and_baselines.py"
RESULT = ROOT / "benchmarks" / "arc-easy" / "results" / "snr_baselines.json"
CARD = ROOT / "benchmarks" / "arc-easy" / "ORIGINAL.md"


@pytest.fixture(scope="module")
def m():
    spec = importlib.util.spec_from_file_location("arc_snr", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------- logic on dummies ----------

def test_git_blob_sha_matches_git(m):
    assert m.git_blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"  # git hash-object


def test_select_final_step_latest_date_double_underscore_and_dedup_split(m):
    paths = [
        "pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json",
        "pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_01-02-2023-00-00-00.json",
        "pythia-2.8b/zero-shot/pythia-2.8b-0shot-global_step143000__eval_results_11-24-2022-16-20-50.json",
        "pythia-1b-deduped/zero-shot/pythia-1b-deduped-0shot-global_step143000_eval_results_11-28-2022-18-07-27.json",
        "pythia-1.4b/zero-shot/pythia-1.4b-0shot-global_step71500_eval_results_12-29-2022-16-23-33.json",
        "pythia-1.4b/zero-shot/pythia-1.4b-0shot-global_step66500_eval_results_12-29-2022-17-00-50.json",
        "pythia-70m/zero-shot/pythia-70m-0shot-global_step71500_eval_results_11-25-2022-07-31-37.json",
        "pythia-1b/five-shot/pythia-1b-5shot-global_step143000_eval_results_11-28-2022-15-14-35.json",
    ]
    sel = m.select_files(paths, deduped=False)
    assert sel == {"pythia-1b": paths[1], "pythia-2.8b": paths[2], "pythia-1.4b": paths[4]}  # 70m@71500 is not final
    assert m.select_files(paths, deduped=True) == {"pythia-1b-deduped": paths[3]}
    assert m.sizes_without_file(paths, deduped=False) == ["pythia-70m"]
    assert m.final_step("pythia-410m-deduped") == 71500 and m.final_step("pythia-12b") == 143000


def test_snr_ddof_and_typical_se(m):
    assert m.snr([0.4, 0.6], 1, 0.1)["spread"] == pytest.approx(math.sqrt(0.02))
    assert m.snr([0.4, 0.6], 0, 0.1)["snr"] == pytest.approx(1.0)
    assert m.typical_se(0.5, 100) == pytest.approx(0.05)


def test_grid_uses_median_not_mean_acc_stderr(m):
    """Mutation: median -> mean of acc_stderr."""
    ms = {"a": {"acc": 0.4, "acc_stderr": 0.01}, "b": {"acc": 0.5, "acc_stderr": 0.01}, "c": {"acc": 0.6, "acc_stderr": 0.04}}
    grid = m.snr_grid({"non_deduped": ms}, 100)
    med = [g for g in grid if g["se_source"] == "median_acc_stderr"]
    assert len(grid) == 4 and all(g["se"] == pytest.approx(0.01) for g in med)


def test_majority_tie_and_index_mapping(m):
    assert m.answer_index(["1", "2", "3", "4"], "3") == 2
    r = m.majority([0, 1, 1, 0, 2])
    assert r["top"] == [0, 1] and r["share"] == pytest.approx(0.4)
    assert m.random_baseline([4, 4, 2]) == pytest.approx((0.25 + 0.25 + 0.5) / 3)


def test_literal_label_variant_uses_labels_not_indices(m):
    """Mutation: variant (c) computed from the index. Index: position 0 has 5; literal: B has 4 > A 3 > '1' 2."""
    abcd, digits = ["A", "B", "C", "D"], ["1", "2", "3", "4"]
    rows = [(abcd, "A")] * 3 + [(digits, "1")] * 2 + [(abcd, "B")] * 4
    main, var = m.majority_variants(rows)
    assert main["top"] == [0] and main["share"] == pytest.approx(5 / 9)
    lit = var["literal_label"]
    assert lit["top"] == ["B"] and lit["share"] == pytest.approx(4 / 9)
    assert not lit["same_top_as_main"] and lit["falsifies"]
    assert var["letter_labels_only"]["n"] == 7


def test_four_options_variant_excludes_three_and_five(m):
    """Mutation: variant (a) as len >= 4."""
    rows = [(["A", "B", "C", "D"], "A")] * 4 + [(["A", "B", "C", "D", "E"], "B")] * 3 + [(["A", "B", "C"], "B")] * 2
    _, var = m.majority_variants(rows)
    assert var["four_options_only"]["n"] == 4 and var["four_options_only"]["share"] == 1.0


def _rows_with_random_baseline(target):
    """Rows of 3-, 4- and 5-option questions whose mean 1/k rounds to `target` (4 decimals)."""
    for a in range(0, 60):
        for b in range(0, 60):
            rows = [(["A", "B", "C"], "A")] * a + [(["A", "B", "C", "D", "E"], "A")] * b + [(["A", "B", "C", "D"], "A")] * 2000
            ks = [len(l) for l, _ in rows]
            if round(sum(1 / k for k in ks) / len(ks), 4) == target:
                return rows
    raise AssertionError("no dummy found")


def _models(n_sizes=2):
    sizes = ["pythia-1b", "pythia-1.4b", "pythia-410m"][:max(n_sizes, 3)]
    return {s: {"acc": 0.5 + 0.01 * i, "acc_stderr": 0.01, "acc_norm": 0.5} for i, s in enumerate(sizes)}


def test_random_baseline_control_exits_on_other_value(m):
    """Mutation: random-baseline control disabled."""
    fam = {"non_deduped": _models(), "deduped": _models()}
    ck = {1: {"acc": 0.5, "acc_stderr": 0.01}, 2: {"acc": 0.51, "acc_stderr": 0.01}}
    ok = _rows_with_random_baseline(0.2502)
    assert m.compute(fam, fam["non_deduped"], ck, ok)["baselines"]["random_mean_1_over_k"] == pytest.approx(0.2502, abs=5e-5)
    with pytest.raises(SystemExit):
        m.compute(fam, fam["non_deduped"], ck, _rows_with_random_baseline(0.2510))


def test_hf_sha_mismatch_exits(m, tmp_path, monkeypatch):
    """Mutation: HF sha256 check disabled. The cached blob name is the LFS oid; tampered bytes must stop the run."""
    import huggingface_hub
    blob = tmp_path / ("0" * 64)
    blob.write_bytes(b"tampered")
    link = tmp_path / "test.parquet"
    os.symlink(blob, link)
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", lambda *a, **k: str(link))
    with pytest.raises(SystemExit):
        m.dataset_rows()


def test_github_blob_mismatch_exits(m, monkeypatch):
    """Mutation: git blob check disabled."""
    rel = "pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json"
    good = json.dumps({"results": {"arc_easy": {"acc": 0.5, "acc_stderr": 0.01}}}).encode()
    tree = {"truncated": False, "tree": [{"type": "blob", "path": f"{m.PYTHIA_DIR}/{rel}", "sha": m.git_blob_sha(good)}]}

    def fake_fetch(url):
        return json.dumps(tree).encode() if "api.github.com" in url else good.replace(b"0.5", b"0.9")

    monkeypatch.setattr(m, "fetch", fake_fetch)
    with pytest.raises(SystemExit):
        m.pythia_inputs()


# ---------- every card number bound to one JSON key ----------

NUM = re.compile(r"(?<![\d,.\w])([−+-]?\d+,\d+)|\bn = (\d+)")


def _get(d, path):
    for k in path.split("."):
        d = d[int(k)] if isinstance(d, list) else d[k]
    return d


def _bindings(d):
    """{row label: [(json path, decimals)]} in the order the numbers appear in the card row."""
    var = sorted(v["share_diff"] for v in d["baselines"]["majority_variants"].values())
    shares = [(f"inputs.dataset.answer_index.shares.{i}", 4) for i in range(5)]
    return {
        "Bazy": [("baselines.random_mean_1_over_k", 4), ("baselines.majority.share", 4), ("inputs.dataset.n", 0),
                 *shares, (var[0], 4), (var[-1], 4)],
        "SNR: rozrzut": [("snr.main.spread", 4), ("snr.ddof0.spread", 4), ("snr.checkpoints.spread", 4)],
        "SNR: SE": [("snr.main.se", 4), ("snr.main.p_bar", 4), ("inputs.dataset.n", 0), ("snr.median_acc_stderr", 4)],
        "SNR: iloraz": [("snr.main.snr", 2), ("snr.acc_norm_main.snr", 2), ("snr.original_protocol_step143000_only.snr", 2),
                        ("snr.min.snr", 2), ("snr.near_1b.pair_1b_1_4b.snr", 2),
                        ("snr.near_1b.triple_410m_1b_1_4b.snr", 2), ("snr.checkpoints.snr", 2),
                        ("snr.near_1b.diff_1_4b_minus_1b.diff", 4),
                        ("snr.near_1b.diff_1_4b_minus_1b.se_diff_independent", 4),
                        ("snr.near_1b.diff_1_4b_minus_1b.ratio", 2)],
    }


def _card_numbers(label):
    row = next(l for l in CARD.read_text().splitlines() if l.startswith(f"| {label} |"))
    out = []
    for dec, n in NUM.findall(row):
        out.append(n if n else dec.replace("−", "-").replace("+", "").replace(",", "."))
    return out


def _fmt(v, k):
    return str(int(v)) if k == 0 else f"{v:.{k}f}"


@pytest.mark.skipif(not RESULT.exists(), reason="run the script first")
@pytest.mark.parametrize("label", ["Bazy", "SNR: rozrzut", "SNR: SE", "SNR: iloraz"])
def test_card_row_numbers_bound_to_json_keys(label):
    d = json.loads(RESULT.read_text())
    expected = [_fmt(p if isinstance(p, float) else _get(d, p), k) for p, k in _bindings(d)[label]]
    assert _card_numbers(label) == expected


# ---------- independent recompute from raw sources (no import of the script) ----------

def _parquet_or_skip(d):
    try:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from huggingface_hub import hf_hub_download
        import pyarrow.parquet as pq
        ds = d["inputs"]["dataset"]
        path = hf_hub_download(ds["repo"], ds["file"], repo_type="dataset", revision=ds["revision"])
    except Exception as e:  # noqa: BLE001 - no cache / no package: the check cannot run here
        pytest.skip(f"dataset unavailable: {e}")
    data = Path(path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == ds["sha256"] == Path(os.path.realpath(path)).name
    return pq.read_table(path).to_pylist()


@pytest.mark.skipif(not RESULT.exists(), reason="run the script first")
def test_baselines_recomputed_from_parquet():
    d = json.loads(RESULT.read_text())
    table = _parquet_or_skip(d)
    pos = [r["choices"]["label"].index(r["answerKey"]) for r in table]
    n = len(pos)
    c = Counter(pos)
    rnd = statistics.fmean(1 / len(r["choices"]["label"]) for r in table)
    card = _card_numbers("Bazy")
    assert card[:3] == [f"{rnd:.4f}", f"{max(c.values()) / n:.4f}", str(n)]
    assert card[3:8] == [f"{c[i] / n:.4f}" for i in range(5)]
    literal = Counter(r["answerKey"] for r in table)
    assert f"{max(literal.values()) / n - max(c.values()) / n:.4f}" == card[8]


def _github(url):
    import ssl
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "test"}), timeout=60, context=ctx) as r:
        return r.read()


@pytest.mark.skipif(not RESULT.exists(), reason="run the script first")
def test_snr_recomputed_from_github():
    d = json.loads(RESULT.read_text())
    commit = d["inputs"]["pythia"]["commit"]
    try:
        tree = json.loads(_github(f"https://api.github.com/repos/EleutherAI/pythia/git/trees/{commit}?recursive=1"))
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"GitHub unavailable: {e}")
    final = {"160m": 71500, "410m": 71500, "1.4b": 71500}
    pick = {}
    for e in tree["tree"]:
        mt = re.fullmatch(r"evals/pythia-v0/pythia-(\w+?|\d\.\d+b)/zero-shot/pythia-\1-0shot-global_step(\d+)_+eval_results_"
                          r"(\d\d)-(\d\d)-(\d{4})-(\d\d-\d\d-\d\d)\.json", e["path"])
        if not mt or mt.group(1).endswith("deduped"):
            continue
        size, step = mt.group(1), int(mt.group(2))
        stamp = (mt.group(5), mt.group(3), mt.group(4), mt.group(6))
        if step == final.get(size, 143000) and (size not in pick or stamp > pick[size][0]):
            pick[size] = (stamp, e["path"], e["sha"])
    acc = {}
    for size, (_, path, sha) in pick.items():
        data = _github(f"https://raw.githubusercontent.com/EleutherAI/pythia/{commit}/{path}")
        assert hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest() == sha
        acc[size] = json.loads(data)["results"]["arc_easy"]
    assert sorted(acc) == sorted(["70m", "160m", "410m", "1b", "1.4b", "2.8b", "6.9b", "12b"])
    a = [v["acc"] for v in acc.values()]
    se = math.sqrt(statistics.fmean(a) * (1 - statistics.fmean(a)) / 2376)
    sd = statistics.stdev(a)
    pair = statistics.stdev([acc["1b"]["acc"], acc["1.4b"]["acc"]])
    pse = math.sqrt(statistics.fmean([acc["1b"]["acc"], acc["1.4b"]["acc"]]) * (1 - statistics.fmean([acc["1b"]["acc"], acc["1.4b"]["acc"]])) / 2376)
    assert _card_numbers("SNR: rozrzut")[0] == f"{sd:.4f}"
    assert _card_numbers("SNR: SE")[0] == f"{se:.4f}"
    il = _card_numbers("SNR: iloraz")
    assert il[0] == f"{sd / se:.2f}" and il[4] == f"{pair / pse:.2f}"
