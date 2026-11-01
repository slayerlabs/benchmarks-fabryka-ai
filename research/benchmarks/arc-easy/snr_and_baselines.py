"""ARC-Easy: SNR from published Pythia v0 results and the majority / random baselines of the test split.

Follows PROTOCOL-snr-baselines.md (addendum written before computing, and the post-result correction). Inputs:
- Pythia evals: github.com/EleutherAI/pythia @ a19eecb..., evals/pythia-v0/<size>/zero-shot/, 0-shot, final
  checkpoint per size (global_step143000; global_step71500 for 160m, 410m, 1.4b, which v0 trained with a 4M-token
  batch for 71500 steps, Pythia README @ a19eecb).
- Dataset: allenai/ai2_arc @ 210d026..., ARC-Easy test parquet (via huggingface_hub; run with HF_HUB_OFFLINE=1
  to use the local cache only).
Every downloaded file is checked against its git blob sha (GitHub) or LFS sha256 (HF) before use.

Writes results/snr_baselines.json (raw inputs + results), read by tools/liczby.py as the `arc-easy` pool.
Exit code != 0 when an integrity check or the random-baseline control fails.

Run: HF_HUB_OFFLINE=1 python benchmarks/arc-easy/snr_and_baselines.py
"""
import hashlib
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import date, datetime
from pathlib import Path

PYTHIA_REPO = "EleutherAI/pythia"
PYTHIA_COMMIT = "a19eecb807ec2c79a39ebf18108816e6ffffc1d5"
PYTHIA_DIR = "evals/pythia-v0"
HF_REPO = "allenai/ai2_arc"
HF_REVISION = "210d026faf9955653af8916fad021475a3f00453"
HF_FILE = "ARC-Easy/test-00000-of-00001.parquet"
TASK = "arc_easy"
CARD_RANDOM_BASELINE = 0.2502  # value already in ORIGINAL.md (protocol control, item 7)
MAJORITY_SHARE_TOLERANCE = 0.01  # protocol addendum, item 5
SNR_THRESHOLD = 2.0
ORIGINAL_STEP = 143000  # protocol before the correction: global_step143000 only
# v0 sizes trained with a 4M-token batch for 71500 steps (Pythia README @ a19eecb): their last step is 71500
FINAL_STEP_4M_BATCH = {"pythia-160m": 71500, "pythia-410m": 71500, "pythia-1.4b": 71500}
NEAR_1B = {"pair_1b_1_4b": ["pythia-1b", "pythia-1.4b"], "triple_410m_1b_1_4b": ["pythia-410m", "pythia-1b", "pythia-1.4b"]}
CHECKPOINT_MODEL = "pythia-1b"
CHECKPOINT_COUNT = 5
OUT = Path(__file__).resolve().parent / "results" / "snr_baselines.json"

# <size>/zero-shot/<size>-0shot-global_step<N>_+eval_results_MM-DD-YYYY-HH-MM-SS.json (2.8b has a double underscore)
FILE_RE = re.compile(r"^(?P<size>pythia-[^/]+)/zero-shot/(?P=size)-0shot-global_step(?P<step>\d+)_+eval_results_"
                     r"(?P<date>\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{2})\.json$")


# ---------- pure functions ----------

def git_blob_sha(data: bytes) -> str:
    """Git blob sha1 of raw bytes (what the GitHub tree lists)."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def final_step(size):
    return FINAL_STEP_4M_BATCH.get(size.removesuffix("-deduped"), ORIGINAL_STEP)


def files_by_step(paths):
    """{size: {step: path}} keeping the latest file (by date in the name) per size and step."""
    best = {}
    for p in paths:
        m = FILE_RE.match(p)
        if not m:
            continue
        key = (m.group("size"), int(m.group("step")))
        d = datetime.strptime(m.group("date"), "%m-%d-%Y-%H-%M-%S")
        if key not in best or d > best[key][0]:
            best[key] = (d, p)
    out = {}
    for (size, step), (_, p) in sorted(best.items()):
        out.setdefault(size, {})[step] = p
    return out


def select_files(paths, deduped, step_of=final_step):
    """{size: path} of the file at step_of(size) per size; deduped=True keeps only `-deduped` sizes."""
    out = {}
    for size, steps in files_by_step(paths).items():
        if size.endswith("-deduped") == deduped and step_of(size) in steps:
            out[size] = steps[step_of(size)]
    return out


def sizes_without_file(paths, deduped, step_of=final_step):
    sizes = {p.split("/")[0] for p in paths if "/zero-shot/" in p}
    sizes = {s for s in sizes if s.startswith("pythia-") and s.endswith("-deduped") == deduped}
    return sorted(sizes - set(select_files(paths, deduped, step_of)))


def typical_se(p, n):
    return math.sqrt(p * (1 - p) / n)


def snr(accs, ddof, se):
    spread = statistics.stdev(accs) if ddof == 1 else statistics.pstdev(accs)
    return {"spread": spread, "se": se, "snr": spread / se}


def snr_formula(accs, n, ddof=1):
    p_bar = statistics.fmean(accs)
    return {"k": len(accs), "p_bar": p_bar, **snr(accs, ddof, typical_se(p_bar, n))}


def verdict(z):
    a = abs(z)
    return "pewne" if a >= 3 else "prawdopodobne" if a >= 2 else "szum"


def answer_index(labels, key):
    """Index of the correct option, as lm-eval: choices.label.index(answerKey)."""
    return list(labels).index(key)


def majority(classes):
    """Most frequent class(es), their share and the full distribution {class: count}."""
    c = Counter(classes)
    n = len(classes)
    top = max(c.values())
    return {"n": n, "top": sorted(k for k, v in c.items() if v == top), "share": top / n,
            "counts": {str(k): v for k, v in sorted(c.items(), key=lambda kv: str(kv[0]))},
            "shares": {str(k): v / n for k, v in sorted(c.items(), key=lambda kv: str(kv[0]))}}


def random_baseline(ks):
    return sum(1 / k for k in ks) / len(ks)


def majority_variants(rows):
    """rows: [(labels, answerKey)]. Main variant and the three falsification variants (addendum item 5)."""
    idx = [(answer_index(l, k), l, k) for l, k in rows]
    main = majority([i for i, _, _ in idx])
    variants = {
        "four_options_only": majority([i for i, l, _ in idx if len(l) == 4]),
        "letter_labels_only": majority([i for i, l, _ in idx if not any(x.isdigit() for x in l)]),
        "literal_label": majority([k for _, _, k in idx]),
    }
    letters = "ABCDE"
    main_letters = {letters[i] for i in main["top"]}
    for name, v in variants.items():
        same_top = set(v["top"]) == main_letters if name == "literal_label" else v["top"] == main["top"]
        v["same_top_as_main"] = same_top
        v["share_diff"] = v["share"] - main["share"]
        v["falsifies"] = (not same_top) or abs(v["share_diff"]) > MAJORITY_SHARE_TOLERANCE
    return main, variants


def snr_grid(models, n):
    """8 SNR values: {non-deduped, deduped} x {ddof 1, 0} x {SE from formula, median acc_stderr}."""
    out = []
    for family, ms in models.items():
        accs = [m["acc"] for m in ms.values()]
        p_bar = statistics.fmean(accs)
        ses = {"formula": typical_se(p_bar, n),
               "median_acc_stderr": statistics.median(m["acc_stderr"] for m in ms.values())}
        for ddof in (1, 0):
            for se_name, se in ses.items():
                out.append({"family": family, "ddof": ddof, "se_source": se_name, "k": len(accs), "p_bar": p_bar,
                            **snr(accs, ddof, se)})
    return out


def near_1b(models, n):
    """SNR of the sizes closest to 1B and the 1b vs 1.4b difference with an independent SE (cautious)."""
    out = {name: {"sizes": sizes, **snr_formula([models[s]["acc"] for s in sizes], n)}
           for name, sizes in NEAR_1B.items()}
    a, b = models["pythia-1b"], models["pythia-1.4b"]
    d = b["acc"] - a["acc"]
    se_d = math.hypot(a["acc_stderr"], b["acc_stderr"])
    out["diff_1_4b_minus_1b"] = {"diff": d, "se_diff_independent": se_d, "ratio": d / se_d, "verdict": verdict(d / se_d)}
    return out


def compute(families, families_original, checkpoints, rows):
    """All results from raw inputs. Exits when the random-baseline control fails."""
    n = len(rows)
    rnd = random_baseline([len(l) for l, _ in rows])
    if round(rnd, 4) != CARD_RANDOM_BASELINE:
        sys.exit(f"control failed: random baseline {rnd:.6f} != card {CARD_RANDOM_BASELINE}")
    main_maj, variants = majority_variants(rows)
    grid = snr_grid(families, n)
    main_snr = next(g for g in grid if g["family"] == "non_deduped" and g["ddof"] == 1 and g["se_source"] == "formula")
    worst = min(grid, key=lambda g: g["snr"])
    nd = families["non_deduped"]
    ck_accs = [c["acc"] for c in checkpoints.values()]
    ck = snr_formula(ck_accs, n)
    return {
        "n": n,
        "options_per_question": {str(k): v for k, v in sorted(Counter(len(l) for l, _ in rows).items())},
        "answer_index": {"counts": main_maj["counts"], "shares": main_maj["shares"]},
        "baselines": {
            "random_mean_1_over_k": rnd,
            "random_control_card_value": CARD_RANDOM_BASELINE,
            "majority": {"top_index": main_maj["top"], "top_letter": ["ABCDE"[i] for i in main_maj["top"]],
                         "share": main_maj["share"]},
            "majority_variants": variants,
            "majority_falsified": any(v["falsifies"] for v in variants.values()),
        },
        "snr": {
            "main": main_snr,
            "ddof0": next(g for g in grid if g["family"] == "non_deduped" and g["ddof"] == 0
                          and g["se_source"] == "formula"),
            "median_acc_stderr": statistics.median(m["acc_stderr"] for m in nd.values()),
            "acc_norm_main": snr_formula([m["acc_norm"] for m in nd.values()], n),
            "grid": grid,
            "min": worst,
            "threshold": SNR_THRESHOLD,
            "claim_snr_at_least_2_holds": worst["snr"] >= SNR_THRESHOLD,
            "original_protocol_step143000_only": snr_formula([m["acc"] for m in families_original.values()], n),
            "near_1b": near_1b(nd, n),
            "checkpoints": {"model": CHECKPOINT_MODEL, "steps": sorted(checkpoints), **ck},
        },
    }


# ---------- I/O ----------

def fetch(url):
    import ssl
    import certifi  # python.org builds on macOS ship without a CA bundle
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "benchmarks-fabryka-ai/arc-easy-snr"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return r.read()


def read_result(blobs, rel, cache):
    """(acc dict or None, file record); checks the git blob sha of the downloaded bytes."""
    if rel not in cache:
        path = f"{PYTHIA_DIR}/{rel}"
        data = fetch(f"https://raw.githubusercontent.com/{PYTHIA_REPO}/{PYTHIA_COMMIT}/{path}")
        if git_blob_sha(data) != blobs[rel]:
            sys.exit(f"blob sha mismatch: {path}")
        res = json.loads(data).get("results", {}).get(TASK)
        acc = None if not res or "acc" not in res else {k: res[k] for k in ("acc", "acc_stderr", "acc_norm",
                                                                             "acc_norm_stderr") if k in res}
        cache[rel] = (acc, {"path": path, "blob_sha": blobs[rel]})
    return cache[rel]


def fetch_tree():
    """Git tree of the Pythia commit; `gh api` (authenticated, higher rate limit) when available."""
    endpoint = f"repos/{PYTHIA_REPO}/git/trees/{PYTHIA_COMMIT}?recursive=1"
    if shutil.which("gh"):
        r = subprocess.run(["gh", "api", endpoint], capture_output=True, text=True)
        if r.returncode == 0:
            return json.loads(r.stdout)
    return json.loads(fetch(f"https://api.github.com/{endpoint}"))


def pythia_inputs():
    tree = fetch_tree()
    if tree.get("truncated"):
        sys.exit("GitHub tree truncated")
    prefix = PYTHIA_DIR + "/"
    blobs = {e["path"][len(prefix):]: e["sha"] for e in tree["tree"]
             if e["type"] == "blob" and e["path"].startswith(prefix)}
    cache, files, excluded = {}, [], []

    def load(selection, family, role):
        models = {}
        for size, rel in selection.items():
            acc, rec = read_result(blobs, rel, cache)
            if acc is None:
                excluded.append({"family": family, "size": size, "role": role, "reason": f"no results.{TASK}.acc",
                                 "path": rec["path"]})
                continue
            files.append({"family": family, "size": size, "role": role, **rec})
            models[size] = acc
        return models

    families = {}
    for family, deduped in (("non_deduped", False), ("deduped", True)):
        for s in sizes_without_file(blobs, deduped):
            excluded.append({"family": family, "size": s, "role": "final", "reason": "no final-step 0-shot file"})
        families[family] = load(select_files(blobs, deduped), family, "final")
    original = load(select_files(blobs, False, lambda s: ORIGINAL_STEP), "non_deduped", "original_protocol")
    steps = files_by_step(blobs)[CHECKPOINT_MODEL]
    last = dict(sorted(steps.items())[-CHECKPOINT_COUNT:])
    ck = load({f"{CHECKPOINT_MODEL}@{s}": p for s, p in last.items()}, "non_deduped", "checkpoint")
    checkpoints = {int(k.split("@")[1]): v for k, v in ck.items()}
    return families, original, checkpoints, files, excluded


def dataset_rows():
    import huggingface_hub
    import pyarrow.parquet as pq
    path = huggingface_hub.hf_hub_download(HF_REPO, HF_FILE, repo_type="dataset", revision=HF_REVISION)
    data = Path(path).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    lfs_oid = Path(os.path.realpath(path)).name
    if sha != lfs_oid:
        sys.exit(f"sha256 mismatch for {HF_FILE}: {sha} vs LFS oid {lfs_oid}")
    table = pq.read_table(path).to_pylist()
    rows = [(r["choices"]["label"], r["answerKey"]) for r in table]
    return rows, {"repo": HF_REPO, "revision": HF_REVISION, "file": HF_FILE, "sha256": sha}


def main():
    families, original, checkpoints, files, excluded = pythia_inputs()
    rows, ds = dataset_rows()
    r = compute(families, original, checkpoints, rows)
    import pyarrow
    import huggingface_hub
    out = {
        "protocol": "benchmarks/arc-easy/PROTOCOL-snr-baselines.md",
        "read_date": date.today().isoformat(),
        "inputs": {
            "pythia": {"repo": PYTHIA_REPO, "commit": PYTHIA_COMMIT, "dir": PYTHIA_DIR, "task": TASK,
                       "final_step_4m_batch": FINAL_STEP_4M_BATCH, "files": files, "excluded": excluded,
                       "models": families, "models_original_protocol": original,
                       "checkpoints": {str(k): v for k, v in checkpoints.items()}},
            "dataset": {**ds, "n": r.pop("n"), "options_per_question": r.pop("options_per_question"),
                        "answer_index": r.pop("answer_index")},
        },
        **r,
        "environment": {"python": platform.python_version(), "pyarrow": pyarrow.__version__,
                        "huggingface_hub": huggingface_hub.__version__, "platform": platform.platform()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    s = out["snr"]
    print(json.dumps({"n": out["inputs"]["dataset"]["n"], "random": out["baselines"]["random_mean_1_over_k"],
                      "majority": out["baselines"]["majority"], "majority_falsified": out["baselines"]["majority_falsified"],
                      "snr_main": s["main"], "snr_min": s["min"], "original": s["original_protocol_step143000_only"],
                      "near_1b": s["near_1b"], "checkpoints": s["checkpoints"], "acc_norm": s["acc_norm_main"],
                      "excluded": excluded}, indent=1))


if __name__ == "__main__":
    main()
