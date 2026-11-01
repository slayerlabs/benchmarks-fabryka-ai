"""PIQA (Space T06): raw per-question results with lm-eval 0.4.9.1 and the Space protocol (PROTOCOL.md).

  python benchmarks/piqa/piqa.py fetch --out DIR
      validation parquet of ybisk/piqa from refs/convert/parquet, revisions, sha256 -> DIR/data.json;
      METHOD.md, tasks_50.json and results.json of the Space -> DIR/space/ (needs network to HF)
  python benchmarks/piqa/piqa.py score --model hf|slayer --pretrained PATH --repo REPO --revision REV \
      --data DIR --out FILE.jsonl --device cuda [--batch 1] [--limit N]
      full validation split, one line per question: logprob of each option, choices, gold (needs GPU/CPU)
  python benchmarks/piqa/piqa.py report
      results/piqa.json and results/PIQA.md from results/raw/*.jsonl.gz (sha256 checked against results/raw/SHA256SUMS)

The prompt, choices and target are piqa.yaml of lm-eval (identical in 6d2abda4 and v0.4.9.1 except dataset_path).
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent.parent
sys.path.insert(0, str(RESEARCH / "common"))

DATA_REPO = "ybisk/piqa"
DATA_REVISION = "2e8ac2dffd59bac8c3c6714948f4c551a0848bb0"  # tasks_50.json; the loading script's commit
PARQUET_REF = "refs/convert/parquet"
SPACE = "SlayerLab/Slayer1B-Benchmarks"
BENCHMARK_ID = "piqa"  # tasks_50.json (checked in PROTOCOL.md)
MEMBER_TASK = "piqa"
PANEL_N = 200
SEED = 20261028
REPLICATES = 10000

# Published control: Pythia-1B v0 @ step143000, lm-eval 2022, piqa version 0 (PROTOCOL.md, "Control").
CONTROL = {"model": "EleutherAI/pythia-1b-v0", "revision": "step143000",
           "acc": 0.7040261153427638, "acc_stderr": 0.010650414317148112,
           "acc_norm": 0.705114254624592, "acc_norm_stderr": 0.010639030620156987, "n": 1838,
           "source": "EleutherAI/pythia@a19eecb807ec2c79a39ebf18108816e6ffffc1d5 evals/pythia-v0/pythia-1b/zero-shot/"
                     "pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json"}
CONTROL_TOLERANCE = 0.02  # +-2 pts, or 2 SE of the published value when 2 SE > 2 pts


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical(row):
    return json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def source_id(row):
    """Source id in the panel hash (PROTOCOL.md, "Panel"): PIQA rows have no native id, so METHOD.md section 3 takes
    the SHA-256 of the canonical document (sorted-key compact JSON, the reading that reproduced the BLiMP panel).
    The validation split has no byte-identical rows, so no ordinal is needed."""
    return hashlib.sha256(canonical(row).encode()).hexdigest()


def panel_indices(source_ids, n=PANEL_N):
    """min(n, N) indices, ascending SHA-256 of `20261028|benchmark_id|member_task|source_id` (METHOD.md section 3)."""
    if len(set(source_ids)) != len(source_ids):
        raise ValueError("duplicate source ids: METHOD.md section 8 needs an ordinal, not implemented")

    def key(i):
        return hashlib.sha256(f"{SEED}|{BENCHMARK_ID}|{MEMBER_TASK}|{source_ids[i]}".encode()).hexdigest()
    return sorted(sorted(range(len(source_ids)), key=key)[:min(n, len(source_ids))])


# ---------------------------------------------------------------- fetch

def fetch(args):
    from huggingface_hub import HfApi, hf_hub_download
    out = Path(args.out)
    (out / "space").mkdir(parents=True, exist_ok=True)
    api = HfApi()
    refs = api.list_repo_refs(DATA_REPO, repo_type="dataset")
    commits = [c.commit_id for c in api.list_repo_commits(DATA_REPO, repo_type="dataset")]
    files = [f for f in api.list_repo_files(DATA_REPO, repo_type="dataset", revision=PARQUET_REF)
             if f.endswith(".parquet") and "validation" in f]
    converts = {r.ref: r.target_commit for r in getattr(refs, "converts", [])}
    parquet_commit = converts.get(PARQUET_REF) or next(iter(converts.values()), None)
    pliki = []
    for name in sorted(files):
        path = hf_hub_download(DATA_REPO, name, repo_type="dataset", revision=parquet_commit or PARQUET_REF,
                               local_dir=str(out / "parquet"))
        pliki.append({"name": name, "sha256": sha256_file(path), "path": str(Path(path).resolve())})
    import pyarrow.parquet as pq
    n_rows = sum(pq.read_metadata(p["path"]).num_rows for p in pliki)
    space_commit = api.space_info(SPACE).sha
    for name in ("METHOD.md", "tasks_50.json", "results.json"):
        hf_hub_download(SPACE, name, repo_type="space", revision=space_commit, local_dir=str(out / "space"))
    manifest = {"repo": DATA_REPO, "revision_in_tasks_50": DATA_REVISION,
                "revision_in_history": DATA_REVISION in commits,
                "main_head": next((b.target_commit for b in refs.branches if b.name == "main"), None),
                "parquet_ref": PARQUET_REF, "parquet_commit": parquet_commit, "files": pliki, "n_rows": n_rows,
                "space": SPACE, "space_commit": space_commit}
    (out / "data.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


# ---------------------------------------------------------------- score

def task_config(data_files):
    """piqa.yaml of lm-eval with the data from local parquet files (PROTOCOL.md, "Task")."""
    return {"task": "piqa_t06", "task_alias": "piqa_t06", "dataset_path": "parquet", "dataset_name": None,
            "dataset_kwargs": {"data_files": {"validation": data_files}},
            "validation_split": "validation", "output_type": "multiple_choice", "num_fewshot": 0,
            "doc_to_text": "Question: {{goal}}\nAnswer:", "doc_to_target": "label",
            "doc_to_choice": "{{[sol1, sol2]}}",
            "metric_list": [{"metric": "acc", "aggregation": "mean", "higher_is_better": True},
                            {"metric": "acc_norm", "aggregation": "mean", "higher_is_better": True}],
            "metadata": {"version": 1.0}}


def build_lm(args):
    if args.model == "slayer":
        import slayer_lm
        return slayer_lm.SlayerLM(pretrained=args.pretrained, dtype="float32", batch_size=args.batch,
                                  device=args.device)
    from lm_eval.models.huggingface import HFLM
    return HFLM(pretrained=args.pretrained, revision=args.revision, dtype="float32", batch_size=args.batch,
                device=args.device)


def question_row(sample, row_index, row):
    """One raw line: logprob of each option, lm-eval decisions and our recomputation of them."""
    lls = [float(r[0]) for r in sample["filtered_resps"]]
    greedy = [bool(r[1]) for r in sample["filtered_resps"]]
    conts = [a[1] for a in sample["arguments"]]
    chars = [len(c) for c in (row["sol1"], row["sol2"])]
    gold = int(sample["target"])
    pick = max(range(2), key=lambda i: lls[i])
    pick_norm = max(range(2), key=lambda i: lls[i] / chars[i])
    return {"idx": row_index, "source_id": source_id(row),
            "gold": gold, "logprob": lls, "greedy": greedy, "chars": chars,
            "bytes_cont": [len(c.encode("utf-8")) for c in conts],
            "pick_acc": pick, "pick_acc_norm": pick_norm,
            "acc": float(sample["acc"]), "acc_norm": float(sample["acc_norm"])}


def score(args):
    import lm_eval
    import torch
    import transformers
    from lm_eval import simple_evaluate
    from lm_eval.tasks import TaskManager, get_task_dict
    import pyarrow.parquet as pq

    manifest = json.loads((Path(args.data) / "data.json").read_text())
    data_files = [f["path"] for f in manifest["files"]]
    for f in manifest["files"]:
        if sha256_file(f["path"]) != f["sha256"]:
            sys.exit(f"sha256 mismatch: {f['path']}")
    rows = []
    for p in data_files:
        rows.extend(pq.read_table(p).to_pylist())
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    t0 = time.time()
    lm = build_lm(args)
    t_load = time.time() - t0
    cfg = task_config(data_files)
    task = list(get_task_dict([copy.deepcopy(cfg)], TaskManager()).values())[0]  # get_task_dict pops keys
    task.config.task = cfg["task"]  # lm-eval 0.4.9.1 drops the name when loading a dict
    limit = None if args.limit is None else int(args.limit)
    t1 = time.time()
    res = simple_evaluate(model=lm, tasks=[task], log_samples=True, bootstrap_iters=0, limit=limit,
                          random_seed=0, numpy_random_seed=1234, torch_random_seed=1234, fewshot_random_seed=1234)
    t_score = time.time() - t1
    samples = sorted(res["samples"][cfg["task"]], key=lambda s: s["doc_id"])
    for s in samples:
        d, r = s["doc"], rows[s["doc_id"]]
        if (d["goal"], d["sol1"], d["sol2"], int(d["label"])) != (r["goal"], r["sol1"], r["sol2"], int(r["label"])):
            sys.exit(f"doc {s['doc_id']} is not row {s['doc_id']} of the parquet")
    lines = [question_row(s, s["doc_id"], rows[s["doc_id"]]) for s in samples]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
    meta = {"model": args.repo, "revision": args.revision, "wrapper": args.model, "pretrained": args.pretrained,
            "n": len(lines), "lm_eval": lm_eval.__version__, "torch": torch.__version__,
            "transformers": transformers.__version__, "cuda": torch.version.cuda,
            "device": torch.cuda.get_device_name(0) if args.device.startswith("cuda") else args.device,
            "batch": args.batch, "dtype": "float32", "seeds": {"python": 0, "numpy": 1234, "torch": 1234},
            "data": {k: manifest[k] for k in ("repo", "revision_in_tasks_50", "parquet_commit")},
            "data_files_sha256": [f["sha256"] for f in manifest["files"]],
            "lm_eval_acc": res["results"][cfg["task"]].get("acc,none"),
            "lm_eval_acc_norm": res["results"][cfg["task"]].get("acc_norm,none"),
            "seconds_load": round(t_load, 1), "seconds_score": round(t_score, 1),
            "date": time.strftime("%Y-%m-%d", time.gmtime()),
            # UTC start (before loading the model) and end (after scoring): the order against the protocol commit
            "started_utc": started, "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    Path(str(out).replace(".jsonl.gz", ".meta.json")).write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


# ---------------------------------------------------------------- report

def mean_ci(values, seed=SEED, replicates=REPLICATES):
    """Mean, n, SE (sample sd / sqrt n) and percentile bootstrap CI95 (10 000 replicates, seed 20261028)."""
    import numpy as np
    x = np.asarray(values, dtype=float)
    n = len(x)
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, n, size=(replicates, n))].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"value": float(x.mean()), "n": n, "se": float(x.std(ddof=1) / math.sqrt(n)), "ci95": [float(lo), float(hi)]}


def verdict(z):
    a = abs(z)
    return "pewne" if a >= 3 else ("prawdopodobne" if a >= 2 else "szum")


def read_raw(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def model_stats(lines, idx=None):
    sel = lines if idx is None else [lines[i] for i in idx]
    out = {}
    for m in ("acc_norm", "acc"):
        out[m] = mean_ci([r[m] for r in sel])
    # BPB of the correct answer, bytes of the continuation with its leading space (what the model predicted):
    # mean over questions of per-question BPB, and pooled = sum of NLL / (ln 2 * sum of bytes)
    out["bpb_correct"] = sum(-r["logprob"][r["gold"]] / (math.log(2) * r["bytes_cont"][r["gold"]]) for r in sel) / len(sel)
    out["bpb_correct_pooled"] = (sum(-r["logprob"][r["gold"]] for r in sel)
                                 / (math.log(2) * sum(r["bytes_cont"][r["gold"]] for r in sel)))
    picks = [r["pick_acc_norm"] for r in sel]
    out["share_pick_sol1_acc_norm"] = picks.count(0) / len(picks)
    out["share_most_frequent_prediction"] = max(picks.count(0), picks.count(1)) / len(picks)
    out["ties_acc"] = sum(r["logprob"][0] == r["logprob"][1] for r in sel)
    out["ties_acc_norm"] = sum(r["logprob"][0] / r["chars"][0] == r["logprob"][1] / r["chars"][1] for r in sel)
    unequal = [r for r in sel if r["chars"][0] != r["chars"][1]]
    longer = lambda r: 0 if r["chars"][0] > r["chars"][1] else 1
    out["n_unequal_length"] = len(unequal)
    out["share_pick_longer_acc_norm"] = sum(r["pick_acc_norm"] == longer(r) for r in unequal) / len(unequal)
    out["share_pick_longer_acc"] = sum(r["pick_acc"] == longer(r) for r in unequal) / len(unequal)
    out["share_gold_longer"] = sum(r["gold"] == longer(r) for r in unequal) / len(unequal)
    out["n"] = len(sel)
    return out


def baselines(lines, idx=None):
    sel = lines if idx is None else [lines[i] for i in idx]
    golds = [r["gold"] for r in sel]
    return {"random": 0.5, "majority": max(golds.count(0), golds.count(1)) / len(golds),
            "share_gold_sol1": golds.count(0) / len(golds), "n": len(golds)}


def paired(a, b, metric, idx=None):
    """Difference a - b on the same questions, paired SE (sd of per-question differences / sqrt n)."""
    sa = a if idx is None else [a[i] for i in idx]
    sb = b if idx is None else [b[i] for i in idx]
    d = [x[metric] - y[metric] for x, y in zip(sa, sb)]
    n = len(d)
    mean = sum(d) / n
    se = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1) / n)
    return {"difference": mean, "difference_pts": mean * 100, "se": se, "z": mean / se, "verdict": verdict(mean / se), "n": n}


def against(value, se, base):
    z = (value - base) / se
    return {"difference_pts": (value - base) * 100, "z": z, "verdict": verdict(z)}


def report(args):
    res = HERE / "results"
    raw = res / "raw"
    sums = {}
    for line in (raw / "SHA256SUMS").read_text().splitlines():
        h, name = line.split()
        sums[name] = h
    for name, h in sums.items():
        if sha256_file(raw / name) != h:
            sys.exit(f"sha256 mismatch: {name}")
    data = {name.replace(".jsonl.gz", ""): read_raw(raw / name) for name in sums if name.endswith(".jsonl.gz")}
    metas = {k: json.loads((raw / f"{k}.meta.json").read_text()) for k in data}
    slayer, pythia = data["slayer-1.06"], data["pythia-1b-v0"]
    for k, lines in data.items():
        if [r["idx"] for r in lines] != list(range(len(lines))):
            sys.exit(f"{k}: rows are not the full split in order")
    panel = panel_indices([r["source_id"] for r in slayer])
    for k, lines in data.items():
        if [(r["source_id"], r["gold"]) for r in lines] != [(r["source_id"], r["gold"]) for r in slayer]:
            sys.exit(f"{k}: questions or gold differ from slayer-1.06")

    out = {"protocol": "benchmarks/piqa/PROTOCOL.md", "n_full": len(slayer), "n_panel": len(panel),
           "panel_source_ids_sha256": hashlib.sha256("\n".join(slayer[i]["source_id"] for i in panel).encode()).hexdigest(),
           "raw_sha256": sums, "baselines": {"full": baselines(slayer), "panel": baselines(slayer, panel)},
           "models": {}}
    for k, lines in data.items():
        if not k.startswith(("slayer", "pythia")) or "_" in k:
            continue
        out["models"][k] = {"full": model_stats(lines), "panel": model_stats(lines, panel),
                            "meta": {m: metas[k][m] for m in ("model", "revision", "device", "lm_eval", "torch",
                                                              "transformers", "batch", "dtype")}}
        out["models"][k]["panel_minus_full_pts"] = 100 * (out["models"][k]["panel"]["acc_norm"]["value"]
                                                          - out["models"][k]["full"]["acc_norm"]["value"])

    # control
    pf = out["models"]["pythia-1b-v0"]["full"]
    control = {"published": CONTROL, "checks": {}}
    for m in ("acc", "acc_norm"):
        tol = max(CONTROL_TOLERANCE, 2 * CONTROL[f"{m}_stderr"])
        diff = pf[m]["value"] - CONTROL[m]
        control["checks"][m] = {"ours": pf[m]["value"], "published": CONTROL[m], "difference_pts": diff * 100,
                                "tolerance_pts": tol * 100, "within": abs(diff) <= tol}
    maj = out["baselines"]["full"]["majority"]
    se_pub = math.sqrt(CONTROL["acc_norm"] * (1 - CONTROL["acc_norm"]) / CONTROL["n"])
    control["discriminates"] = {"se_published": se_pub,
                                "z_over_random": (CONTROL["acc_norm"] - 0.5) / se_pub,
                                "z_over_majority": (CONTROL["acc_norm"] - maj) / se_pub,
                                "ok": CONTROL["acc_norm"] - max(0.5, maj) > 2 * se_pub}
    control["passed"] = all(c["within"] for c in control["checks"].values()) and control["discriminates"]["ok"]
    out["control"] = control

    # comparisons fixed in PROTOCOL.md
    comps = {}
    for part, idx in (("full", None), ("panel", panel)):
        s = out["models"]["slayer-1.06"][part]["acc_norm"]
        b = out["baselines"][part]
        comps[f"slayer_vs_random_{part}"] = against(s["value"], s["se"], 0.5)
        comps[f"slayer_vs_majority_{part}"] = against(s["value"], s["se"], b["majority"])
        comps[f"slayer_minus_pythia_{part}"] = paired(slayer, pythia, "acc_norm", idx)
    out["comparisons"] = comps

    # same Pythia run on other GPUs: per-question agreement with the main run
    repeats = {}
    for k, lines in data.items():
        if k.startswith("pythia-1b-v0_"):
            diffs = [abs(x - y) for a, b in zip(pythia, lines) for x, y in zip(a["logprob"], b["logprob"])]
            repeats[k.split("_", 1)[1]] = {
                "device": metas[k]["device"], "n": len(lines),
                "acc_norm": sum(r["acc_norm"] for r in lines) / len(lines),
                "decisions_differ": sum(a["pick_acc_norm"] != b["pick_acc_norm"] for a, b in zip(pythia, lines)),
                "max_abs_logprob_diff": max(diffs), "seconds_score": metas[k]["seconds_score"]}
    out["gpu_repeats"] = repeats
    out["seconds_score"] = {k: metas[k]["seconds_score"] for k in data}
    (res / "piqa.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    for name, text in pliki(None, out).items():
        (res / name).write_text(text)
    print(json.dumps({"control_passed": control["passed"]}, indent=1))


def pliki(liczby, o):
    """{file name: text} for gate (g) of tools/sprawdz_raporty.py: the report must equal this output from piqa.json."""
    return {"PIQA.md": render(o)}


def f3(x):
    return f"{x:.4f}".replace(".", ",").replace("-", "−")


def p1(x):
    return f"{x:.2f}".replace(".", ",").replace("-", "−")


def render(o):
    s, pt = o["models"]["slayer-1.06"], o["models"]["pythia-1b-v0"]
    c = o["control"]
    sf, sp = s["full"]["acc_norm"], s["panel"]["acc_norm"]
    cr = o["comparisons"]["slayer_vs_random_full"]
    lines = [
        "# PIQA (T06): Slayer 1.06 and control Pythia-1B v0",
        "",
        "Generated by `benchmarks/piqa/piqa.py report` from `results/piqa.json`; do not edit by hand (gate (g) of "
        "`tools/sprawdz_raporty.py`).",
        "Protocol: [`PROTOCOL.md`](../PROTOCOL.md), committed before the first raw result. Recipe: [`RECIPE.md`](../RECIPE.md).",
        "Slayer 1.06 is a checkpoint at about 1/8 of its training plan, without LR decay; Pythia-1B v0 finished its training.",
        "",
        "## Number for the Space",
        "",
        f"Slayer 1.06, acc_norm, full validation split: {f3(sf['value'])} (n {sf['n']}, CI95 {f3(sf['ci95'][0])}–"
        f"{f3(sf['ci95'][1])}). Space panel: {f3(sp['value'])} (n {sp['n']}, CI95 {f3(sp['ci95'][0])}–{f3(sp['ci95'][1])}).",
        f"The panel is easier than the full split for both models (Slayer {p1(s['panel_minus_full_pts'])} pts, Pythia "
        f"{p1(pt['panel_minus_full_pts'])} pts), so the panel value alone overstates the result; the full split is the "
        "headline number and the panel value goes with its n.",
        "",
        f"Main claim: Slayer 1.06 scores {f3(sf['value'])} on the full split, {p1(cr['difference_pts'])} pts over the random "
        f"baseline (z {p1(cr['z'])}, {cr['verdict']}). The claim is about the score, not about physical reasoning: the "
        "Space flags T06 for Slayer 1.06 as contaminated (`contamination: flagged`), and without the training corpus we "
        "cannot say how much of the margin comes from questions seen in training (no hit-free value). Falsified if z "
        "against the random baseline were below 3, or if the control fell outside its tolerance.",
        "",
        "## Results (acc_norm, 0-shot, lm-eval 0.4.9.1, float32, batch 1)",
        "",
        "| model | split | n | acc_norm | SE | CI95 | acc | share of option 1 (acc_norm) | most frequent prediction |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for name, m in (("Slayer 1.06", s), ("Pythia-1B v0", pt)):
        for part, label in (("full", "full validation"), ("panel", "Space panel")):
            r = m[part]
            lines.append(f"| {name} | {label} | {r['n']} | {f3(r['acc_norm']['value'])} | {f3(r['acc_norm']['se'])} | "
                         f"{f3(r['acc_norm']['ci95'][0])}–{f3(r['acc_norm']['ci95'][1])} | {f3(r['acc']['value'])} | "
                         f"{f3(r['share_pick_sol1_acc_norm'])} | {f3(r['share_most_frequent_prediction'])} |")
    bf, bp = o["baselines"]["full"], o["baselines"]["panel"]
    lines += ["",
              "SE = sample sd / sqrt n; CI95 = percentile bootstrap over questions, 10 000 replicates, seed 20261028.",
              f"Baselines: random {f3(bf['random'])}; majority (share of the most frequent correct option) "
              f"{f3(bf['majority'])} on the full split (n {bf['n']}) and {f3(bp['majority'])} on the panel (n {bp['n']}); "
              f"share of option 1 among correct answers {f3(bf['share_gold_sol1'])} (full) and {f3(bp['share_gold_sol1'])} (panel).",
              f"Ties (equal scores of both options): acc {s['full']['ties_acc']} and acc_norm {s['full']['ties_acc_norm']} "
              f"for Slayer, acc {pt['full']['ties_acc']} and acc_norm {pt['full']['ties_acc_norm']} for Pythia (full split); "
              "a tie would go to option 1, as lm-eval's argmax.",
              "",
              "## Diagnostics (full split, not used for any claim)",
              "",
              "| model | BPB of the correct answer, mean over questions | BPB, pooled | picks the longer option (acc_norm) | "
              "picks the longer option (acc) |",
              "|---|---:|---:|---:|---:|"]
    for name, m in (("Slayer 1.06", s), ("Pythia-1B v0", pt)):
        r = m["full"]
        lines.append(f"| {name} | {f3(r['bpb_correct'])} | {f3(r['bpb_correct_pooled'])} | "
                     f"{f3(r['share_pick_longer_acc_norm'])} | {f3(r['share_pick_longer_acc'])} |")
    lines += ["",
              "BPB counts the bytes of the continuation with its leading space (what the model predicted). Mean over "
              "questions averages per-question BPB; pooled is the sum of NLL / (ln 2 × sum of bytes).",
              f"Longer option: on the {s['full']['n_unequal_length']} questions whose options differ in length (characters); "
              f"the correct option is the longer one in {f3(s['full']['share_gold_longer'])} of them. Whether the length "
              "preference differs between the models is undetermined (no test was fixed in the protocol).",
              "",
              "## Panel",
              "",
              f"{o['n_panel']} questions, ascending SHA-256 of `20261028|piqa|piqa|<source id>` (METHOD.md section 3). "
              "Source id = SHA-256 of the canonical row (JSON with sorted keys, separators `,` and `:`, UTF-8; PIQA rows "
              "have no native id). Digest of the panel = SHA-256 of the 200 source ids in split order joined with `\\n`: "
              f"`{o['panel_source_ids_sha256']}`.",
              "The Space has no T06 value and no `source_id_digest` for any model, so the panel is not checked against the "
              "Space. Excerpt of METHOD.md and tasks_50.json at the Space revision: [`../SPACE_METHOD.md`](../SPACE_METHOD.md).",
              "",
              "## Control", "",
              "| metric | Pythia-1B v0, ours | published | difference, pts | tolerance, pts | within |",
              "|---|---:|---:|---:|---:|---|"]
    for m in ("acc", "acc_norm"):
        k = c["checks"][m]
        lines.append(f"| {m} | {f3(k['ours'])} | {f3(k['published'])} | {p1(k['difference_pts'])} | "
                     f"{p1(k['tolerance_pts'])} | {'yes' if k['within'] else 'no'} |")
    d = c["discriminates"]
    lines += ["",
              "Tolerance = max(2 pts, 2 × published SE).",
              f"The published acc_norm lies {p1(d['z_over_random'])} standard errors over the random baseline and "
              f"{p1(d['z_over_majority'])} over the majority baseline (standard error {f3(d['se_published'])}), so the control "
              f"tells working code from guessing. Control passed: {'yes' if c['passed'] else 'no'}.",
              "",
              "BOS differs between the models: Slayer gets one BOS before every request (as in the Space), Pythia none (its "
              "tokenizer convention and the 2022 harness of the published value). Effect of a BOS on Pythia, and so on the "
              "Slayer − Pythia comparison: NOT RUN (it needs a second Pythia run with a BOS; the control itself is "
              "computed as the published value was).",
              "",
              "## Comparisons (verdict: |z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum)", "",
              "| comparison | split | difference, pts | z | verdict |", "|---|---|---:|---:|---|"]
    names = {"slayer_vs_random": "Slayer 1.06 − random baseline", "slayer_vs_majority": "Slayer 1.06 − majority baseline",
             "slayer_minus_pythia": "Slayer 1.06 − Pythia-1B v0 (paired SE)"}
    for part in ("full", "panel"):
        for key, label in names.items():
            k = o["comparisons"][f"{key}_{part}"]
            lines.append(f"| {label} | {part} | {p1(k['difference_pts'])} | {p1(k['z'])} | {k['verdict']} |")
    lines += ["",
              "z against a baseline = (value − baseline) / SE of the value; Slayer − Pythia uses the paired SE "
              "(sd of per-question differences / sqrt n).",
              "A certain difference between Slayer and Pythia is not its cause. Alternatives: the share of English in the "
              "training data (about 10% for Slayer, 100% for Pythia) and the training stage. Possible contamination of "
              "Slayer on PIQA works the other way: it would raise Slayer's score, so without it the gap could be larger. "
              "The BOS difference above is unmeasured. "
              "<!-- ocena-bez-se: alternative causes of the gap whose z is in the table above, no new comparison -->",
              "", "## Same Pythia run on other GPUs", "",
              "| GPU | n | acc_norm | decisions that differ from the main run | max abs logprob difference |",
              "|---|---:|---:|---:|---|"]
    for k, r in o["gpu_repeats"].items():
        lines.append(f"| {r['device']} | {r['n']} | {f3(r['acc_norm'])} | {r['decisions_differ']} | "
                     f"{r['max_abs_logprob_diff']:.1e} |")
    lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--out", required=True)
    s = sub.add_parser("score")
    s.add_argument("--model", choices=["hf", "slayer"], required=True)
    s.add_argument("--pretrained", required=True)
    s.add_argument("--repo", required=True)
    s.add_argument("--revision", required=True)
    s.add_argument("--data", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--device", default="cuda")
    s.add_argument("--batch", default="1")
    s.add_argument("--limit")
    sub.add_parser("report")
    a = p.parse_args()
    {"fetch": fetch, "score": score, "report": report}[a.cmd](a)


if __name__ == "__main__":
    main()
