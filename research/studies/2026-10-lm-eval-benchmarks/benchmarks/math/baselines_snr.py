"""MATH (hendrycks_math): sizes, bases, SE, SNR and MDE for the original card (stage A). No model is run.

Inputs:
- Dataset: EleutherAI/hendrycks_math @ 21a5633... (the revision Space T34 pins), 7 test parquet files via
  huggingface_hub; each file's sha256 is checked against its LFS oid before use.
- Scoring: `utils.py` of the lm-eval task `hendrycks_math` from the installed lm-eval (0.4.9.1, the repo lock file),
  loaded from its file so that the bases use exactly the extractor and normalisation the task uses.
- Published results, copied below with their source: MATH paper table 2 (Hendrycks et al. 2021, arXiv:2103.03874v2)
  and Qwen2.5 technical report table 5 (arXiv:2412.15115v2), both read 2026-11-04.

Bases (METHODOLOGY, type `gen +warstwy`): random N/A (0); constant answer = the higher of the empty answer and the most
frequent gold answer, in each subject separately, then the size-weighted mean (the group aggregates with
`weight_by_size: true`). SE W = sqrt(sum w_i^2 SE_i^2) with SE_i = sqrt(p_i (1 - p_i) / n_i).

Writes results/baselines_snr.json, read by tools/liczby.py as the `math` pool.

Run: HF_HUB_OFFLINE=1 python benchmarks/math/baselines_snr.py   (offline after the first download)
"""
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

DATASET = "EleutherAI/hendrycks_math"
REVISION = "21a5633873b6a120296cce3e2df9d5550074f4a3"
# config name -> (lm-eval task, LFS sha256 of test-00000-of-00001.parquet at REVISION)
SUBJECTS = {
    "algebra": ("hendrycks_math_algebra", "0e04a850dac9cfc758eac0c80afd2d0cc65e29ea72f916c8ac1045b12af937f5"),
    "counting_and_probability": ("hendrycks_math_counting_and_prob",
                                 "c324818949c75a6227c0328a8499d58023cbbf6757cfc1736f5ab24cc8d87966"),
    "geometry": ("hendrycks_math_geometry", "98720f3a8134ad9784fd8951195245264495df03ffc5c9485a9a54ff5ae2431a"),
    "intermediate_algebra": ("hendrycks_math_intermediate_algebra",
                             "e859f72486c951c2017da880541ca729940eaa986b0364eb23e238983df9bfeb"),
    "number_theory": ("hendrycks_math_num_theory", "ba156c9c9fa2040836ba12135fd964e6e67d6bccd8c469ec4a3ad941f8f6fbe9"),
    "prealgebra": ("hendrycks_math_prealgebra", "301e5d8ade5c7b5038032532e498bdc9dca799e7f1061a63f2e7d980803240cc"),
    "precalculus": ("hendrycks_math_precalc", "da37474ba3761ae5727af3844a7ba963a735bd6a14c65e6137593669a4fe3b9c"),
}
# MATH paper, table 2 (percent; subject columns in the dataset's config names). `*` = few-shot (8-shot), the rest
# fine-tuned on the MATH train split (GPT-2 also pretrained on AMPS).
PAPER_TABLE2 = {
    "GPT-2 0.1B": {"prealgebra": 5.2, "algebra": 5.1, "number_theory": 5.0, "counting_and_probability": 2.8,
                   "geometry": 5.7, "intermediate_algebra": 6.5, "precalculus": 7.3, "average": 5.4},
    "GPT-2 0.3B": {"prealgebra": 6.7, "algebra": 6.6, "number_theory": 5.5, "counting_and_probability": 3.8,
                   "geometry": 6.9, "intermediate_algebra": 6.0, "precalculus": 7.1, "average": 6.2},
    "GPT-2 0.7B": {"prealgebra": 6.9, "algebra": 6.1, "number_theory": 5.5, "counting_and_probability": 5.1,
                   "geometry": 8.2, "intermediate_algebra": 5.8, "precalculus": 7.7, "average": 6.4},
    "GPT-2 1.5B": {"prealgebra": 8.3, "algebra": 6.2, "number_theory": 4.8, "counting_and_probability": 5.4,
                   "geometry": 8.7, "intermediate_algebra": 6.1, "precalculus": 8.8, "average": 6.9},
    "GPT-3 13B*": {"prealgebra": 4.1, "algebra": 2.4, "number_theory": 3.3, "counting_and_probability": 4.5,
                   "geometry": 1.0, "intermediate_algebra": 3.2, "precalculus": 2.0, "average": 3.0},
    "GPT-3 13B": {"prealgebra": 6.8, "algebra": 5.3, "number_theory": 5.5, "counting_and_probability": 4.1,
                  "geometry": 7.1, "intermediate_algebra": 4.7, "precalculus": 5.8, "average": 5.6},
    "GPT-3 175B*": {"prealgebra": 7.7, "algebra": 6.0, "number_theory": 4.4, "counting_and_probability": 4.7,
                    "geometry": 3.1, "intermediate_algebra": 4.4, "precalculus": 4.0, "average": 5.2},
}
# Qwen2.5 technical report, table 5 "smaller base models", MATH (4-shot), percent, with the parameter count from the
# safetensors metadata of the HF repo (read 2026-11-04). The SNR rule keeps models from 400 M to 3 B parameters.
QWEN25_TABLE5 = {
    "Qwen/Qwen2-0.5B": (11.2, 494032768),
    "Qwen/Qwen2.5-0.5B": (19.5, 494032768),
    "Qwen/Qwen2-1.5B": (21.6, 1543714304),
    "Qwen/Qwen2.5-1.5B": (35.0, 1543714304),
    "google/gemma-2-2b": (18.3, 2614341888),
    "Qwen/Qwen2.5-3B": (42.6, 3085938688),
}
SNR_RANGE = (400e6, 3e9)
Z_POWER = 0.84  # 80% power (METHODOLOGY, core rule 5)
Z_THRESHOLD = 2.0
PANEL = 200
OUT = Path(__file__).resolve().parent / "results" / "baselines_snr.json"


def load_lm_eval_utils():
    """utils.py of lm_eval/tasks/hendrycks_math from the installed lm-eval, without importing all tasks."""
    spec = importlib.util.find_spec("lm_eval")
    if spec is None or not spec.submodule_search_locations:
        sys.exit("lm-eval is not installed (use the environment from common/requirements.lock.txt)")
    path = Path(list(spec.submodule_search_locations)[0]) / "tasks" / "hendrycks_math" / "utils.py"
    mod_spec = importlib.util.spec_from_file_location("hendrycks_math_utils", path)
    mod = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(mod)
    from importlib.metadata import version
    return mod, version("lm_eval"), hashlib.sha256(path.read_bytes()).hexdigest()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_subject(config, oid):
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(DATASET, f"{config}/test-00000-of-00001.parquet", repo_type="dataset", revision=REVISION)
    got = sha256(p)
    if got != oid:
        sys.exit(f"{config}: sha256 {got} != LFS oid {oid}")
    return pd.read_parquet(p).to_dict("records")


def se_w(p_by_subject, n_by_subject):
    """SE W of a size-weighted mean of per-subject accuracies."""
    total = sum(n_by_subject.values())
    return math.sqrt(sum((n_by_subject[s] / total) ** 2 * p_by_subject[s] * (1 - p_by_subject[s]) / n_by_subject[s]
                         for s in n_by_subject))


def main():
    utils, lm_eval_version, utils_sha = load_lm_eval_utils()
    subjects = {}
    for config, (task, oid) in SUBJECTS.items():
        docs = load_subject(config, oid)
        golds = []
        for d in docs:
            boxed = utils.last_boxed_only_string(d["solution"])
            golds.append(utils.remove_boxed(boxed) if boxed is not None else None)
        if any(g is None for g in golds):
            sys.exit(f"{config}: {sum(g is None for g in golds)} solutions without \\boxed")
        score = lambda output: [utils.process_results(d, [output])["exact_match"] for d in docs]
        empty = score("")
        counts = Counter(utils.strip_string(g) for g in golds)
        top_norm, top_count = counts.most_common(1)[0]
        top_raw = next(g for g in golds if utils.strip_string(g) == top_norm)
        top = score(top_raw)
        subjects[config] = {
            "task": task, "n": len(docs), "levels": dict(sorted(Counter(d["level"] for d in docs).items())),
            "types": dict(Counter(d["type"] for d in docs)),
            "empty_answer": sum(empty) / len(docs), "empty_answer_hits": sum(empty),
            "most_frequent_gold": top_raw, "most_frequent_gold_count": top_count,
            "most_frequent_gold_score": sum(top) / len(docs), "most_frequent_gold_hits": sum(top),
        }
        s = subjects[config]
        s["constant"] = max(s["empty_answer"], s["most_frequent_gold_score"])
    n = {s: v["n"] for s, v in subjects.items()}
    total = sum(n.values())
    weights = {s: n[s] / total for s in n}
    constant = sum(weights[s] * subjects[s]["constant"] for s in n)

    # paper table 2: is "Average" the size-weighted mean (pooled over problems) or the plain mean of subjects?
    paper = {}
    for model, row in PAPER_TABLE2.items():
        pooled = sum(weights[s] * row[s] for s in n)
        plain = statistics.mean(row[s] for s in n)
        paper[model] = {"average_reported": row["average"], "size_weighted": pooled, "unweighted": plain}
    # a subject value is rounded to 0.1, so an average from the same rule lands within 0.05 of the reported one
    agrees = lambda key: sum(abs(v[key] - v["average_reported"]) <= 0.05 for v in paper.values())
    paper_check = {"rows": len(paper), "size_weighted_within_0_05": agrees("size_weighted"),
                   "unweighted_within_0_05": agrees("unweighted")}
    in_range = ["GPT-2 0.7B", "GPT-2 1.5B"]  # GPT-2 0.3B is below 400 M, GPT-3 above 3 B

    # SNR from the Qwen2.5 report: models from 400 M to 3 B parameters
    in_snr_range = lambda params: SNR_RANGE[0] <= params <= SNR_RANGE[1]
    snr_models = {m: acc / 100 for m, (acc, params) in QWEN25_TABLE5.items() if in_snr_range(params)}
    vals = list(snr_models.values())
    p_bar = statistics.mean(vals)
    # per-subject results are not published: with the same p in every subject SE W equals sqrt(p(1-p)/N)
    se_full = se_w({s: p_bar for s in n}, n)
    sd = statistics.stdev(vals)
    snr = {"source": "Qwen2.5 technical report, table 5, MATH 4-shot", "models": snr_models,
           "excluded": {m: params for m, (acc, params) in QWEN25_TABLE5.items() if not in_snr_range(params)},
           "sd": sd, "sd_ddof0": statistics.pstdev(vals), "p_bar": p_bar, "se_full": se_full, "ratio": sd / se_full}
    # paper source for comparison: GPT-2 0.7B and 1.5B only (two models in range), SE W from their subject columns
    snr_paper = {"models": {m: PAPER_TABLE2[m]["average"] / 100 for m in in_range},
                 "se_full": {m: se_w({s: PAPER_TABLE2[m][s] / 100 for s in n}, n) for m in in_range}}
    snr_paper["sd"] = statistics.stdev(snr_paper["models"].values())
    snr_paper["ratio"] = snr_paper["sd"] / statistics.mean(snr_paper["se_full"].values())

    # MDE: no per-question results yet, so SE of the difference = sqrt(2) * SE of one result
    def mde(p, n_items):
        se1 = math.sqrt(p * (1 - p) / n_items)
        return {"p": p, "n": n_items, "se_one": se1, "se_diff": math.sqrt(2) * se1,
                "mde": (Z_THRESHOLD + Z_POWER) * math.sqrt(2) * se1}
    mde_out = {"at_p_bar_snr": {"full": mde(p_bar, total), "panel200": mde(p_bar, PANEL)},
               "at_paper_gpt2_1_5b": {"full": mde(PAPER_TABLE2["GPT-2 1.5B"]["average"] / 100, total),
                                      "panel200": mde(PAPER_TABLE2["GPT-2 1.5B"]["average"] / 100, PANEL)},
               "z_threshold": Z_THRESHOLD, "z_power": Z_POWER}

    out = {"dataset": f"{DATASET}@{REVISION}", "split": "test", "lm_eval_version": lm_eval_version,
           "lm_eval_utils_sha256": utils_sha, "n": total, "weights": weights, "subjects": subjects,
           "bases": {"random": 0.0, "constant": constant, "b": max(0.0, constant)},
           "paper_table2": paper, "paper_average_check": paper_check, "snr": snr, "snr_paper_gpt2": snr_paper, "mde": mde_out}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("n", "bases", "snr", "mde")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
