"""EWoK (Elements of World Knowledge, Ivanova et al. 2024, arXiv:2405.09605), English original.

Our implementation of the authors' LOGPROBS mode (ewok-paper @ 9e40d30e, `Model._score` with `surprisal`,
`use_bos_token=False`): the query is f"{context} {target}" without BOS, the target's log-probabilities are summed.

A record has two contexts (C1, C2) and two targets (T1, T2); T1 fits C1, T2 fits C2.
  s1 = [log P(T1|C1) > log P(T1|C2)],  s2 = [log P(T2|C2) > log P(T2|C1)],  score = (s1 + s2) / 2,  chance 0.5.
A tie counts as 0 here and as 0.5 in the authors' analysis; in float32 no model had a tie (REPRODUCTION.md).
Agreement with the authors' code: tests/test_ewok_zgodnosc.py.

  python benchmarks/ewok/ewok.py score --model <dir> --out benchmarks/ewok/results/<model>
  python benchmarks/ewok/ewok.py report --results benchmarks/ewok/results --models <m>,<m>,... --measured Slayer1B-1.06

`score` writes <out>/ewok.jsonl, one line per record: id, source_id (row of ewok-core-1.0), `ll` (ll[c][t] =
log P(T_t | C_c)), `bezw` (log P(T) without context, with BOS; diagnostic only) and `ntok` (tokens of T1, T2). No
record text (EWoK TERMS_OF_USE). `--bos` puts one BOS before the context: the way benchmarks/ewok-pl scored so far,
an additional method next to the authors' one, never instead of it.
"""

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "common"))

from hipoteza_formatu import ModelSlayer, licz_logliki, para  # noqa: E402
from metryki import POWTORZENIA, SEED, srednia_z_niepewnoscia  # noqa: E402

DATASET_REPO = "ewok-core/ewok-core-1.0"
DATASET_REV = "34d912a608066c92e2990a0328ffc3bd9a716042"
DATASET_FILE = "data/test/ewok-core-1.0.parquet"
FIELDS = ("Context1", "Context2", "Target1", "Target2")
METRICS = ("ewok", "both", "constant_target")


# ---------------------------------------------------------------- models

class HFModel:
    """A transformers model in float32 with the interface `hipoteza_formatu.licz_logliki` expects."""

    def __init__(self, path, device):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tok = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
        self.m = AutoModelForCausalLM.from_pretrained(path, dtype=torch.float32, trust_remote_code=True).to(device).eval()
        self.device = device
        bos = self.tok.bos_token_id if self.tok.bos_token_id is not None else self.tok.eos_token_id
        self.prefiks, self.prefiks_pusty = [bos], [bos]
        self.pad = self.tok.pad_token_id if self.tok.pad_token_id is not None else bos
        self.max_len = min(getattr(self.m.config, "max_position_embeddings", 2048), 4096)
        # a model without a separate base model (base_model_prefix = "") has no last_hidden_state, and the default
        # logits_to_keep=1 returns only the last position: compute full logits directly then
        self.no_base = self.m.base_model is self.m

    def encode(self, s):
        return self.tok(s, add_special_tokens=False).input_ids

    @torch.no_grad()
    def ukryte(self, ids):
        if self.no_base:
            return self.logits(ids)
        return self.m.base_model(ids).last_hidden_state

    @torch.no_grad()
    def glowa(self, h):
        if self.no_base:
            return h.float()
        return self.m.get_output_embeddings()(h).float()

    @torch.no_grad()
    def logits(self, ids):
        if self.no_base:
            return self.m(ids, use_cache=False, logits_to_keep=0).logits.float()
        return self.m(ids).logits.float()


def build_model(path, device, bos=False):
    """Slayer (config.json without model_type) through common/slayer_model.py, anything else through transformers.
    Without `bos` the context gets no BOS, as in the authors' code; a target without context keeps its BOS, since
    its first token needs something before it (only the `bezw` diagnostic uses it)."""
    cfg = json.loads((Path(path) / "config.json").read_text())
    model = ModelSlayer(path, device) if "n_embd" in cfg and "model_type" not in cfg else HFModel(path, device)
    if not bos:
        model.prefiks = []
    return model


# ---------------------------------------------------------------- data

def load_records():
    """The 4374 rows of ewok-core-1.0 (gated on HF, pinned revision), in file order."""
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(DATASET_REPO, DATASET_FILE, repo_type="dataset", revision=DATASET_REV)
    return [{"id": f"ewok-en-{i:04d}", "source_id": i, **r} for i, r in enumerate(pd.read_parquet(p).to_dict("records"))]


def record_pairs(model, r):
    """6 pairs (context ids, target ids): (C1,T1), (C1,T2), (C2,T1), (C2,T2), then T1 and T2 without context."""
    pairs = [para(model, r[c], " " + r[t]) for c in ("Context1", "Context2") for t in ("Target1", "Target2")]
    return pairs + [para(model, "", r[t]) for t in ("Target1", "Target2")]


# ---------------------------------------------------------------- scoring

def score(model, recs, path, chunk=128, batch=32):
    """Append one line per record to `path`; records already in the file are skipped (a run can be resumed)."""
    done = set()
    if path.exists():
        done = {json.loads(line)["id"] for line in path.read_text().splitlines() if line.strip()}
    recs = [r for r in recs if r["id"] not in done]
    t0 = time.time()
    for s in range(0, len(recs), chunk):
        part = recs[s:s + chunk]
        ll = licz_logliki(model, [p for r in part for p in record_pairs(model, r)], batch)
        write_rows(path, part, ll)
        print(f"[{path.stem}] {s + len(part)}/{len(recs)}  {time.time() - t0:.0f}s", flush=True)


def write_rows(path, recs, ll):
    with open(path, "a", encoding="utf-8") as f:
        for j, r in enumerate(recs):
            w = ll[6 * j:6 * j + 6]
            f.write(json.dumps({"id": r["id"], "source_id": r["source_id"],
                                "ll": [[w[0][0], w[1][0]], [w[2][0], w[3][0]]],
                                "bezw": [w[4][0], w[5][0]],
                                "ntok": [w[0][1], w[1][1]]}) + "\n")


def read_rows(path):
    """Rows of `score` from <path>, or from the compressed copy in the repo, <path>.gz."""
    path = Path(path)
    if path.exists():
        text = path.read_text()
    else:
        import gzip
        text = gzip.decompress(path.with_name(path.name + ".gz").read_bytes()).decode()
    return {w["id"]: w for w in map(json.loads, text.splitlines()) if w}


# ---------------------------------------------------------------- evaluation

def evaluate(w):
    """Scores of one record. `constant_target`: with both contexts the model prefers the same target, a trace of the
    target's prior (the analogue of always picking one option); a tie T1 = T2 is no choice, not a choice of T2."""
    ll = w["ll"]
    s1, s2 = ll[0][0] > ll[1][0], ll[1][1] > ll[0][1]
    k1, k2 = ll[0][0] > ll[0][1], ll[1][1] > ll[1][0]
    return {"ewok": (s1 + s2) / 2, "both": float(s1 and s2),
            "constant_target": float(ll[0][0] != ll[0][1] and ll[1][0] != ll[1][1] and k1 != k2)}


def ties(w):
    ll = w["ll"]
    return int(ll[0][0] == ll[1][0]) + int(ll[1][1] == ll[0][1])


def templates(recs, threshold=0.3):
    """source_id -> template id. EWoK fills one template with several sets of names and objects (usually 5), and
    those records are not independent. Within (concept pair, domain) the words present in fewer than `threshold` of
    the records are fillers and get masked; what remains identifies the template."""
    words = lambda s: re.findall(r"[A-Za-z']+", s)
    groups = defaultdict(list)
    for r in recs:
        groups[(r["ConceptA"], r["ConceptB"], r["Domain"])].append(r)
    keys = {}
    for g, xs in groups.items():
        df = Counter(w for x in xs for w in set(words(" ".join(x[f] for f in FIELDS))))
        for x in xs:
            keys[x["source_id"]] = (g,) + tuple(" ".join(w if df[w] >= threshold * len(xs) else "_" for w in words(x[f]))
                                                for f in FIELDS)
    number = {k: i for i, k in enumerate(sorted(set(keys.values())))}
    return {s: number[k] for s, k in keys.items()}


def _cluster_sums(values, clusters):
    sums, counts = defaultdict(float), Counter()
    for v, k in zip(values, clusters):
        sums[k] += v
        counts[k] += 1
    ks = sorted(sums)
    return np.array([sums[k] for k in ks]), np.array([counts[k] for k in ks], dtype=float)


def cluster_mean(values, clusters, seed=SEED, reps=POWTORZENIA):
    """Mean over records with SE and CI95 from a bootstrap over templates (whole templates are resampled)."""
    s, n = _cluster_sums(values, clusters)
    idx = np.random.default_rng(seed).integers(0, len(s), size=(reps, len(s)))
    means = s[idx].sum(1) / n[idx].sum(1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return {"value": float(s.sum() / n.sum()), "n": int(n.sum()), "n_templates": len(s), "se": float(means.std(ddof=1)),
            "ci95": [float(lo), float(hi)]}


def verdict(z):
    """As the number gate (tools/liczby.py): |z| >= 3 pewne, 2-3 prawdopodobne, < 2 szum."""
    return "pewne" if abs(z) >= 3 else "prawdopodobne" if abs(z) >= 2 else "szum"


def permutation_test(diffs, seed=SEED, reps=POWTORZENIA, clusters=None):
    """Paired two-sided permutation test (random sign flips); with `clusters` a whole template flips at once."""
    d = np.asarray(diffs, dtype=float)
    if clusters is not None:
        d, _ = _cluster_sums(d, clusters)
    obs = abs(d.mean())
    signs = np.random.default_rng(seed).choice([-1.0, 1.0], size=(reps, len(d)))
    return float(((np.abs((signs * d).mean(axis=1)) >= obs - 1e-12).sum() + 1) / (reps + 1))


def summarize(scores, meta, tmpl):
    out = {m: srednia_z_niepewnoscia([s[m] for s in scores.values()]) for m in METRICS}
    out["ewok_by_template"] = cluster_mean([s["ewok"] for s in scores.values()], [tmpl[meta[i]["source_id"]] for i in scores])
    bins = defaultdict(list)
    for i, s in scores.items():
        bins[meta[i]["Domain"]].append(s["ewok"])
    out["by_domain"] = {k: srednia_z_niepewnoscia(v) for k, v in sorted(bins.items())}
    return out


def contrast(a, b, name_a, name_b, meta, tmpl):
    """Paired difference of `ewok` on the same records: SE over records and, the one that decides, over templates."""
    common = sorted(set(a) & set(b))
    d = [a[k]["ewok"] - b[k]["ewok"] for k in common]
    cl = [tmpl[meta[k]["source_id"]] for k in common]
    r = cluster_mean(d, cl)
    r["z"] = r["value"] / r["se"] if r["se"] else 0.0
    r["verdict"] = verdict(r["z"])
    return {"a": name_a, "b": name_b, "n": len(d), "diff": srednia_z_niepewnoscia(d), "a_better": sum(x > 0 for x in d),
            "b_better": sum(x < 0 for x in d), "diff_by_template": r, "p_by_template": permutation_test(d, clusters=cl)}


# ---------------------------------------------------------------- commands

def cmd_score(a):
    model = build_model(a.model, a.device, bos=a.bos)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    score(model, load_records(), out / "ewok.jsonl", batch=a.batch)


def cmd_report(a):
    recs = load_records()
    meta = {r["id"]: {"source_id": r["source_id"], "Domain": r["Domain"]} for r in recs}
    tmpl = templates(recs)
    models = a.models.split(",")
    rows = {m: read_rows(Path(a.results) / m / "ewok.jsonl") for m in models}
    report = {"protocol": {"dataset": f"{DATASET_REPO}@{DATASET_REV}", "mode": "no BOS, C + ' ' + T, float32",
                           "chance": 0.5, "n_templates": len(set(tmpl.values())),
                           "bootstrap": {"reps": POWTORZENIA, "seed": SEED}}, "models": {}, "contrasts": []}
    scores = {}
    for m in models:
        assert len(rows[m]) == len(recs), (m, len(rows[m]))
        scores[m] = {i: evaluate(w) for i, w in rows[m].items()}
        report["models"][m] = {**summarize(scores[m], meta, tmpl), "ties": sum(ties(w) for w in rows[m].values())}
        e, t = report["models"][m]["ewok"], report["models"][m]["ewok_by_template"]
        print(f"{m:28s} {100 * e['value']:.2f}  n={e['n']}  SE {100 * e['se']:.2f}  by template ({t['n_templates']}): "
              f"SE {100 * t['se']:.2f} CI95 [{100 * t['ci95'][0]:.1f}, {100 * t['ci95'][1]:.1f}]  "
              f"constant target {100 * report['models'][m]['constant_target']['value']:.1f}")
    if a.measured:
        for m in models:
            if m != a.measured:
                k = contrast(scores[a.measured], scores[m], a.measured, m, meta, tmpl)
                report["contrasts"].append(k)
                r = k["diff_by_template"]
                print(f"{a.measured} - {m:24s} {100 * r['value']:+.2f} pts  SE {100 * r['se']:.2f}  z {r['z']:+.1f}  "
                      f"{r['verdict']}")
    Path(a.out).write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score", help="log P per record for one model")
    s.add_argument("--model", required=True)
    s.add_argument("--out", required=True, help="directory; the run writes <out>/ewok.jsonl")
    s.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    s.add_argument("--batch", type=int, default=32)
    s.add_argument("--bos", action="store_true", help="one BOS before the context (not the authors' method)")
    r = sub.add_parser("report", help="accuracy, SE by template and contrasts from <results>/<model>/ewok.jsonl")
    r.add_argument("--results", default=str(HERE / "results"))
    r.add_argument("--models", required=True)
    r.add_argument("--measured", help="model compared with every other one, e.g. Slayer1B-1.06")
    r.add_argument("--out", default=str(HERE / "results" / "ewok.json"))
    a = p.parse_args()
    {"score": cmd_score, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
