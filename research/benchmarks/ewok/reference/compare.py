"""Stages B and C for gpt2-xl: the EWoK authors' code (results in data.zip and our runs of their code) against ewok.py.

Everything is computed on the 4374 rows of `ewok-core-1.0` (HF), the dataset of the paper's table. An HF row is joined
with the authors' result by its quadruple (C1, C2, T1, T2). The output holds numbers only, no record text (EWoK
TERMS_OF_USE).

  python compare.py --data <unpacked analyses/data.zip> \
      --authors bf16=<run_authors.py dir> fp32=<run_authors.py dir> \
      --ours ours=<ewok.jsonl> ours_bos=<ewok.jsonl> ours_bf16=<ewok.jsonl> \
      --out results/gpt2xl_comparison.json --sample ../../common/tests/data/ewok_zgodnosc.json
"""
import argparse
import glob
import json
import os
import random

import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

DATASET_REPO, DATASET_REV = "ewok-core/ewok-core-1.0", "34d912a608066c92e2990a0328ffc3bd9a716042"
# order as ll[c][t] in ewok.py: (C1,T1), (C1,T2), (C2,T1), (C2,T2)
COLUMNS = ["logp_target1_context1", "logp_target2_context1", "logp_target1_context2", "logp_target2_context2"]
SEED = 20261103


def key(df):
    return list(zip(df.Context1, df.Context2, df.Target1, df.Target2))


def authors_results(pattern, skip):
    """{quadruple: [4 ll]} from results-*.csv of the authors' code (5 versions); repeated quadruples have equal numbers."""
    files = sorted(glob.glob(pattern))
    assert files, pattern
    d = pd.concat([pd.read_csv(f, skiprows=skip) for f in files])
    return {k: list(map(float, v)) for k, v in zip(key(d), d[COLUMNS].values)}


def our_results(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            w = json.loads(line)
            out[w["source_id"]] = [w["ll"][0][0], w["ll"][0][1], w["ll"][1][0], w["ll"][1][1]]
    return out


def decisions(ll):
    """The two decisions of a record: sign of log P(T1|C1) - log P(T1|C2) and of log P(T2|C2) - log P(T2|C1)."""
    return [float(np.sign(ll[0] - ll[2])), float(np.sign(ll[3] - ll[1]))]


def record_score(dec, tie):
    return sum(1.0 if d > 0 else tie if d == 0 else 0.0 for d in dec) / 2


def mean_se(x):
    x = np.asarray(x, dtype=float)
    return {"value": float(x.mean()), "n": len(x), "se": float(x.std(ddof=1) / np.sqrt(len(x)))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--authors", nargs="+", default=[])
    p.add_argument("--ours", nargs="+", default=[])
    p.add_argument("--out", required=True)
    p.add_argument("--sample")
    a = p.parse_args()

    hf = pd.read_parquet(hf_hub_download(DATASET_REPO, "data/test/ewok-core-1.0.parquet", repo_type="dataset",
                                         revision=DATASET_REV))
    keys = key(hf)
    version = {}
    for v in range(5):
        for f in glob.glob(os.path.join(a.data, "data/outputs_20240429/dataset/ewok1.0", f"*__vers={v}", "testsuite-*.csv")):
            for k in key(pd.read_csv(f, skiprows=1)):
                version.setdefault(k, v)

    ll = {"authors_data_zip": authors_results(os.path.join(
        a.data, "data/outputs_20240429/results/ewok1.0/*/eval=logprobs/model=gpt2_xl/results-*.csv"), 1)}
    for x in a.authors:
        name, d = x.split("=", 1)
        ll[f"authors_{name}"] = authors_results(os.path.join(d, "vers=*", "results-*.csv"), 0)
    for x in a.ours:
        name, path = x.split("=", 1)
        ours = our_results(path)
        ll[name] = {k: ours[i] for i, k in enumerate(keys)}

    dec = {n: [decisions(w[k]) for k in keys] for n, w in ll.items()}
    # tie = 0.5 as the authors do (count_equal_as_half); ewok.py counts a tie as 0, both are given
    accuracy = {}
    for n, d in dec.items():
        s = [record_score(x, 0.5) for x in d]
        per_v = [float(np.mean([s[i] for i, k in enumerate(keys) if version[k] == v])) for v in range(5)]
        accuracy[n] = {"records": mean_se(s), "ties_as_0": mean_se([record_score(x, 0.0) for x in d]),
                       "mean_of_versions": float(np.mean(per_v)), "versions": per_v,
                       "ties": int(sum(x == 0 for r in d for x in r))}
    pairs = {}
    names = list(dec)
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            dx, dy = np.array(dec[x]).ravel(), np.array(dec[y]).ravel()
            sx = np.array([record_score(r, 0.5) for r in dec[x]])
            sy = np.array([record_score(r, 0.5) for r in dec[y]])
            lx, ly = np.array([ll[x][k] for k in keys]), np.array([ll[y][k] for k in keys])
            pairs[f"{x} vs {y}"] = {"decision_agreement": float((dx == dy).mean()), "n_decisions": len(dx),
                                    "disagreements": int((dx != dy).sum()), "diff": mean_se(sx - sy),
                                    "max_abs_logp_diff": float(np.abs(lx - ly).max()),
                                    "mean_abs_logp_diff": float(np.abs(lx - ly).mean())}
    out = {"dataset": f"{DATASET_REPO}@{DATASET_REV}", "n": len(keys), "model": "openai-community/gpt2-xl",
           "accuracy": accuracy, "pairs": pairs}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))

    if a.sample:
        # sample for the agreement test (stage C): HF row number and numbers only, no text
        random.seed(SEED)
        idx = sorted(random.sample(range(len(keys)), 16))
        sample = {"dataset": out["dataset"], "model": out["model"], "seed": SEED,
                  "sources": {"authors": "authors' code ewok-paper@9e40d30e, fp32 (run_authors.py)",
                              "ours": "benchmarks/ewok/ewok.py score, fp32"},
                  "records": [{"hf_row": i, "authors": ll["authors_fp32"][keys[i]], "ours": ll["ours"][keys[i]]}
                              for i in idx]}
        with open(a.sample, "w", encoding="utf-8") as f:
            json.dump(sample, f, indent=1)


if __name__ == "__main__":
    main()
