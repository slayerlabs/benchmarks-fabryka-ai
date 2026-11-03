"""WSC273 (benchmarks/wsc273/wsc273.py).

Three layers:
- logic on dummies, no network (each test names the mutation it must catch);
- the task directory against the pinned lm-eval files;
- results/wsc273.json recomputed from the per-question files, without the author's report code.
Run: pytest tests/test_wsc273.py
"""
import gzip
import hashlib
import importlib.util
import json
import statistics
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "benchmarks" / "wsc273"
SCRIPT = BENCHMARK / "wsc273.py"
RESULT = BENCHMARK / "results" / "wsc273.json"
PANEL = BENCHMARK / "panel200.json"
TASK = BENCHMARK / "lm_eval_tasks" / "wsc273"
UTILS_BLOB = "97a0c529d07f440e31373e0a3f4ec92c54db7cbf"  # lm_eval/tasks/wsc273/utils.py @ 6d2abda4 and v0.4.9.1
DATA_LINES = ("dataset_path:", "dataset_name:", "dataset_kwargs:", "data_files:", "test: hf://", "trust_remote_code:")


@pytest.fixture(scope="module")
def m():
    spec = importlib.util.spec_from_file_location("wsc273_bench", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_gz(model, sample):
    with gzip.open(BENCHMARK / "results" / model / f"{sample}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def git_blob(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


# ---------- logic on dummies ----------

def test_identical_documents_get_an_ordinal(m):
    # mutation: dropping the ordinal gives two documents the same identity, so the sample can no longer tell them apart
    ids = m.tozsamosci([{"a": 1}, {"a": 1}, {"a": 2}])
    assert ids[0] != ids[1] and ids[1] == f"{ids[0]}#1" and len(set(ids)) == 3


def test_document_identity_ignores_key_order(m):
    # mutation: without sort_keys the id depends on the column order of the source file
    assert m.id_dokumentu({"a": 1, "b": 2}) == m.id_dokumentu({"b": 2, "a": 1})


def test_rows_take_gold_from_label_and_pred_from_the_higher_loglikelihood(m):
    # mutation: `target` is the shared continuation text here, and argmin instead of argmax flips every prediction
    sample = {"doc_id": 7, "doc": {"label": 1}, "target": " feared violence.", "acc": 1.0,
              "filtered_resps": [(-3.0, False), (-2.0, False)]}
    assert m.wiersze([sample])[0] | {"id": ""} == {"k": 7, "id": "", "gold": 1, "logliki": [-3.0, -2.0], "pred": 1,
                                                  "acc": 1.0}


def test_rows_are_sorted_by_document_index(m):
    # mutation: lm-eval returns samples in its own order, and the report indexes the full run by k
    make = lambda i: {"doc_id": i, "doc": {"label": 0}, "acc": 0.0, "filtered_resps": [(0.0, False), (1.0, False)]}
    assert [w["k"] for w in m.wiersze([make(2), make(0), make(1)])] == [0, 1, 2]


def test_tied_loglikelihoods_take_the_first_option_like_lm_eval(m):
    # mutation: a last-index tie break makes `pred` disagree with the `acc` lm-eval computed
    sample = {"doc_id": 0, "doc": {"label": 0}, "acc": 1.0, "filtered_resps": [(-2.0, False), (-2.0, False)]}
    assert m.wiersze([sample])[0]["pred"] == 0


def test_majority_comparison_uses_the_paired_se(m):
    # mutation: the SE of the score alone hides that the model and the constant answer the same questions
    rows = [{"acc": 1.0, "gold": 1}] * 2 + [{"acc": 0.0, "gold": 1}] + [{"acc": 1.0, "gold": 0}] * 2
    wynik = m.wobec_wiekszosciowej(rows)
    assert wynik["roznica"] == pytest.approx(0.2)
    assert wynik["se"] == pytest.approx(mean_se([0.0, 0.0, -1.0, 1.0, 1.0])[1])


def test_field_subsets_are_the_strict_ones_that_keep_text_and_options(m):
    # mutation: a wrong range counts the full document twice or drops the two-field subset
    docs = [{"text": str(i), "options": "o", "a": i % 2, "b": 0} for i in range(250)]
    rows = [{"acc": float(i % 2)} for i in range(250)]
    assert m.podzbiory_pol(rows, docs)["n"] == 3


def test_subsample_sd_vanishes_on_the_full_split(m):
    # mutation: without the finite population term the sample would look noisy against itself
    rows = [{"acc": float(i % 2)} for i in range(10)]
    assert m.sd_podproby(rows, n=10) == 0
    assert m.sd_podproby(rows, n=5) == pytest.approx((statistics.variance(r["acc"] for r in rows) / 5 * 0.5) ** 0.5)


def test_summary_uses_two_options_for_chance_and_the_split_for_majority(m):
    # mutation: k as the document index would make the chance level meaningless
    rows = [{"acc": 1.0, "gold": 0, "pred": 0}, {"acc": 0.0, "gold": 1, "pred": 0}, {"acc": 1.0, "gold": 0, "pred": 0}]
    wynik = m.podsumuj(rows, [137, 136])
    assert wynik["bazy"]["chance_value"] == 0.5
    assert wynik["bazy"]["majority_value"] == pytest.approx(2 / 3)
    assert wynik["bazy"]["constant_prediction"] is True
    assert wynik["baza_wiekszosciowa_split"] == pytest.approx(137 / 273)


# ---------- task directory ----------

def test_utils_is_the_lm_eval_file():
    assert git_blob((TASK / "utils.py").read_bytes().replace(b"\r\n", b"\n")) == UTILS_BLOB


def test_yaml_differs_from_lm_eval_only_in_the_data_source():
    lm_eval = pytest.importorskip("lm_eval")
    original = Path(lm_eval.__file__).parent / "tasks" / "wsc273" / "default.yaml"
    keep = lambda text: [ln for ln in text.splitlines() if ln.strip() and not ln.strip().startswith(DATA_LINES)]
    assert keep((TASK / "wsc273.yaml").read_text(encoding="utf-8")) == keep(original.read_text(encoding="utf-8"))


def test_panel_is_the_frozen_ranking(m):
    # mutation: any list of 200 sorted indices passes the shape checks; only the ranking of the ids pins this one
    panel = json.loads(PANEL.read_text(encoding="utf-8"))
    assert panel["n_splitu"] == 273 and len(panel["indeksy"]) == 200
    assert panel["indeksy"] == sorted(set(panel["indeksy"])) and max(panel["indeksy"]) < 273
    assert panel["indeksy"] == m.panel_z([r["id"] for r in read_gz("slayer-1.06", "full")])


# ---------- report recomputed from per-question files ----------

@pytest.fixture(scope="module")
def report():
    if not RESULT.exists():
        pytest.skip("no results yet")
    return json.loads(RESULT.read_text(encoding="utf-8"))


def mean_se(values):
    return statistics.fmean(values), statistics.stdev(values) / len(values) ** 0.5


@pytest.mark.parametrize("key,model,sample,n", [("kontrola", "bloom-560m", "full", 273),
                                                ("slayer_panel200", "slayer-1.06", "panel200", 200),
                                                ("slayer_pelny", "slayer-1.06", "full", 273)])
def test_values_recompute_from_the_per_question_files(report, key, model, sample, n):
    rows = read_gz(model, sample)
    value, se = mean_se([r["acc"] for r in rows])
    assert report[key]["n"] == n == len(rows)
    assert report[key]["value"] == pytest.approx(value) and report[key]["se"] == pytest.approx(se)


@pytest.mark.parametrize("model,sample", [("bloom-560m", "full"), ("slayer-1.06", "panel200"), ("slayer-1.06", "full")])
def test_acc_agrees_with_the_loglikelihoods(model, sample):
    # mutation: a pipeline that shifted gold or pred by one document keeps the average plausible and fails here
    for r in read_gz(model, sample):
        assert r["pred"] == max((0, 1), key=lambda i: r["logliki"][i])
        assert r["acc"] == float(r["pred"] == r["gold"])


@pytest.mark.parametrize("key,sample,klasa", [("slayer_panel200", "panel200", 1), ("slayer_pelny", "full", 0)])
def test_majority_comparison_recomputes_from_the_per_question_files(report, key, sample, klasa):
    # mutation: comparing with the unpaired SE turns the verdict into "prawdopodobne"
    rows = read_gz("slayer-1.06", sample)
    value, se = mean_se([r["acc"] - (r["gold"] == klasa) for r in rows])
    wiersz = report[key]["wobec_wiekszosciowej"]
    assert wiersz["roznica"] == pytest.approx(value) and wiersz["se"] == pytest.approx(se)
    assert wiersz["z"] == pytest.approx(value / se) and wiersz["werdykt"] == "szum"
    assert report[key]["value"] - report[key]["bazy"]["majority_value"] == pytest.approx(value)


def test_sample_run_is_the_frozen_list_and_matches_the_full_run():
    panel = json.loads(PANEL.read_text(encoding="utf-8"))["indeksy"]
    full = read_gz("slayer-1.06", "full")
    sample = read_gz("slayer-1.06", "panel200")
    assert [r["k"] for r in sample] == panel
    assert all(r["id"] == full[r["k"]]["id"] and r["acc"] == full[r["k"]]["acc"] for r in sample)


def test_control_is_inside_the_threshold(report):
    assert 0.6095 <= report["kontrola"]["value"] <= 0.7238


def test_per_question_files_hold_no_question_text():
    # the public repo keeps hashes and scores, not the dataset
    for model, sample in [("bloom-560m", "full"), ("slayer-1.06", "panel200"), ("slayer-1.06", "full")]:
        assert all(set(r) == {"k", "id", "gold", "logliki", "pred", "acc"} for r in read_gz(model, sample))
