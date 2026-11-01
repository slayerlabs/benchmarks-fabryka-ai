"""ARC-Easy: SNR from published Pythia v0 results and the majority / random baselines of the test split.

Follows PROTOCOL-snr-baselines.md (including the addendum written before computing). Inputs:
- Pythia evals: github.com/EleutherAI/pythia @ a19eecb..., evals/pythia-v0/<size>/zero-shot/, 0-shot step143000.
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
import statistics
import sys
import urllib.request
from collections import Counter
from datetime import datetime
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
OUT = Path(__file__).resolve().parent / "results" / "snr_baselines.json"

# <size>-0shot-global_step143000_+eval_results_MM-DD-YYYY-HH-MM-SS.json (pythia-2.8b has a double underscore)
FILE_RE = re.compile(r"^(?P<size>pythia-[^/]+)/zero-shot/(?P=size)-0shot-global_step143000_+eval_results_"
                     r"(?P<date>\d{2}-\d{2}-\d{4}-\d{2}-\d{2}-\d{2})\.json$")


# ---------- pure functions ----------

def git_blob_sha(data: bytes) -> str:
    """Git blob sha1 of raw bytes (what the GitHub tree lists)."""
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def select_files(paths, deduped):
    """{size: path} of the latest (by date in the name) 0-shot step143000 file per size.

    `paths` are relative to PYTHIA_DIR. deduped=False keeps sizes without `-deduped`, True only `-deduped`."""
    best = {}
    for p in paths:
        m = FILE_RE.match(p)
        if not m:
            continue
        size = m.group("size")
        if size.endswith("-deduped") != deduped:
            continue
        date = datetime.strptime(m.group("date"), "%m-%d-%Y-%H-%M-%S")
        if size not in best or date > best[size][0]:
            best[size] = (date, p)
    return {s: p for s, (_, p) in sorted(best.items())}


def sizes_without_file(paths, deduped):
    """Sizes that have a zero-shot directory but no matching step143000 file."""
    sizes = {p.split("/")[0] for p in paths if "/zero-shot/" in p}
    sizes = {s for s in sizes if s.startswith("pythia-") and s.endswith("-deduped") == deduped}
    return sorted(sizes - set(select_files(paths, deduped)))


def typical_se(p, n):
    return math.sqrt(p * (1 - p) / n)


def snr(accs, ddof, se):
    spread = statistics.stdev(accs) if ddof == 1 else statistics.pstdev(accs)
    return {"spread": spread, "se": se, "snr": spread / se}


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
        if name == "literal_label":
            same_top = set(v["top"]) == main_letters
        else:
            same_top = v["top"] == main["top"]
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
        ses = {"formula": typical_se(p_bar, n), "median_acc_stderr": statistics.median(m["acc_stderr"] for m in ms.values())}
        for ddof in (1, 0):
            for se_name, se in ses.items():
                r = snr(accs, ddof, se)
                out.append({"family": family, "ddof": ddof, "se_source": se_name, "k": len(accs), "p_bar": p_bar, **r})
    return out


# ---------- I/O ----------

def fetch(url):
    import ssl
    import certifi  # python.org builds on macOS ship without a CA bundle
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "benchmarks-fabryka-ai/arc-easy-snr"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return r.read()


def pythia_inputs():
    tree = json.loads(fetch(f"https://api.github.com/repos/{PYTHIA_REPO}/git/trees/{PYTHIA_COMMIT}?recursive=1"))
    if tree.get("truncated"):
        sys.exit("GitHub tree truncated")
    prefix = PYTHIA_DIR + "/"
    blobs = {e["path"][len(prefix):]: e["sha"] for e in tree["tree"]
             if e["type"] == "blob" and e["path"].startswith(prefix)}
    families, files, excluded = {}, [], []
    for family, deduped in (("non_deduped", False), ("deduped", True)):
        for s in sizes_without_file(blobs, deduped):
            excluded.append({"family": family, "size": s, "reason": "no 0-shot global_step143000 file"})
        models = {}
        for size, rel in select_files(blobs, deduped).items():
            path = prefix + rel
            data = fetch(f"https://raw.githubusercontent.com/{PYTHIA_REPO}/{PYTHIA_COMMIT}/{path}")
            if git_blob_sha(data) != blobs[rel]:
                sys.exit(f"blob sha mismatch: {path}")
            res = json.loads(data).get("results", {}).get(TASK)
            if not res or "acc" not in res:
                excluded.append({"family": family, "size": size, "reason": f"no results.{TASK}.acc", "path": path})
                continue
            files.append({"family": family, "size": size, "path": path, "blob_sha": blobs[rel]})
            models[size] = {"acc": res["acc"], "acc_stderr": res["acc_stderr"]}
        families[family] = models
    return families, files, excluded


def dataset_rows():
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq
    path = hf_hub_download(HF_REPO, HF_FILE, repo_type="dataset", revision=HF_REVISION)
    data = Path(path).read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    lfs_oid = Path(os.path.realpath(path)).name
    if sha != lfs_oid:
        sys.exit(f"sha256 mismatch for {HF_FILE}: {sha} vs LFS oid {lfs_oid}")
    table = pq.read_table(path).to_pylist()
    rows = [(r["choices"]["label"], r["answerKey"]) for r in table]
    return rows, {"repo": HF_REPO, "revision": HF_REVISION, "file": HF_FILE, "sha256": sha}


def main():
    families, files, excluded = pythia_inputs()
    rows, ds = dataset_rows()
    n = len(rows)
    rnd = random_baseline([len(l) for l, _ in rows])
    if round(rnd, 4) != CARD_RANDOM_BASELINE:
        sys.exit(f"control failed: random baseline {rnd:.6f} != card {CARD_RANDOM_BASELINE}")
    main_maj, variants = majority_variants(rows)
    grid = snr_grid(families, n)
    main_snr = next(g for g in grid if g["family"] == "non_deduped" and g["ddof"] == 1 and g["se_source"] == "formula")
    worst = min(grid, key=lambda g: g["snr"])
    import pyarrow
    import huggingface_hub
    out = {
        "protocol": "benchmarks/arc-easy/PROTOCOL-snr-baselines.md",
        "inputs": {
            "pythia": {"repo": PYTHIA_REPO, "commit": PYTHIA_COMMIT, "dir": PYTHIA_DIR, "task": TASK,
                       "files": files, "excluded": excluded, "models": families},
            "dataset": {**ds, "n": n,
                        "options_per_question": {str(k): v for k, v in sorted(Counter(len(l) for l, _ in rows).items())},
                        "answer_index": {"counts": main_maj["counts"], "shares": main_maj["shares"]}},
        },
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
            "grid": grid,
            "min": worst,
            "threshold": SNR_THRESHOLD,
            "claim_snr_at_least_2_holds": worst["snr"] >= SNR_THRESHOLD,
        },
        "environment": {"python": platform.python_version(), "pyarrow": pyarrow.__version__,
                        "huggingface_hub": huggingface_hub.__version__, "platform": platform.platform()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({"n": n, "random": rnd, "majority": out["baselines"]["majority"],
                      "majority_falsified": out["baselines"]["majority_falsified"],
                      "snr_main": main_snr, "snr_min": worst}, indent=1))


if __name__ == "__main__":
    main()
