"""EWoK (Elements of World Knowledge, Ivanova et al. 2024, arXiv:2405.09605), English original.

Our implementation of the authors' LOGPROBS mode (ewok-paper @ 9e40d30e, `Model._score` with `surprisal` @ 366b074,
`use_bos_token=False`). The query f"{context} {target}" and the context are tokenized with the tokenizer's own
special tokens (`add_special_tokens=True`), so a tokenizer that prepends BOS (Bielik, EuroLLM, LFM2.5) gives the
query a BOS and one that does not (gpt2, Qwen3.5, LFM3, Slayer) gives none. The target is the query tokens from
len(tokens(context)) on. Before the softmax the pad token's logit is set to -inf (pad = the tokenizer's pad token,
else EOS), as `surprisal` does. The target's log-probabilities are summed.

A record has two contexts (C1, C2) and two targets (T1, T2); T1 fits C1, T2 fits C2.
  s1 = [log P(T1|C1) > log P(T1|C2)],  s2 = [log P(T2|C2) > log P(T2|C1)],  score = (s1 + s2) / 2,  chance 0.5.
A tie counts as 0 here and as 0.5 in the authors' analysis; in float32 no model had a tie (REPRODUCTION.md).
Agreement with the authors' code: tests/test_ewok_zgodnosc.py.

  python benchmarks/ewok/ewok.py score --model <dir> --out benchmarks/ewok/results/<model>
  python benchmarks/ewok/ewok.py report --results benchmarks/ewok/results --models <m>,<m>,... --measured Slayer1B-1.06

`score` writes <out>/ewok.jsonl, one line per record: id, source_id (row of ewok-core-1.0), `ll` (ll[c][t] =
log P(T_t | C_c)), `bezw` (log P(T) without context, with BOS; diagnostic only) and `ntok` (tokens of T1, T2). No
record text (EWoK TERMS_OF_USE).

`--rule` picks the method. `authors` (default) is the one above. `plain` never adds special tokens and masks
nothing: it equals `authors` only for tokenizers without special tokens, up to the pad mask (first runs of this
benchmark). `bos` puts one BOS before the context, the way benchmarks/ewok-pl scored so far. Both are additional
methods next to the authors' one, never instead of it.
"""

import argparse
import json
import math
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "common"))
sys.path.insert(0, str(HERE.parents[1] / "tools"))

from statystyka import p_t as p_student, p_z, po_holmie, werdykt as verdict, werdykt_p  # noqa: E402,F401
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

    def encode_special(self, s):
        return self.tok(s).input_ids

    def masked_id(self):
        # `Model._prep_tokenizer` of the authors: pad token, else EOS
        return self.tok.pad_token_id if self.tok.pad_token_id is not None else self.tok.eos_token_id

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


RULES = ("authors", "plain", "bos")
MODES = {"authors": "tokenizer's special tokens (BOS where the tokenizer adds it), pad masked, C + ' ' + T, float32",
         "plain": "no special tokens, no pad mask, C + ' ' + T, float32",
         "bos": "one BOS before the context, C + ' ' + T, float32"}


def build_model(path, device, rule="authors"):
    """Slayer (config.json without model_type) through common/slayer_model.py, anything else through transformers.
    Only `bos` keeps a BOS in `prefiks`; `authors` takes special tokens from the tokenizer instead (`authors_pair`).
    A target without context keeps its BOS, since its first token needs something before it (only the `bezw`
    diagnostic uses it)."""
    assert rule in RULES, rule
    cfg = json.loads((Path(path) / "config.json").read_text())
    if "n_embd" in cfg and "model_type" not in cfg:
        model = ModelSlayer(path, device)
        # Slayer's tokenizer.json has no post-processor (no special tokens) and no pad token: EOS is <|endoftext|>
        model.encode_special = lambda s: model.s.tok.encode(s).ids
        model.masked_id = lambda: model.s.bos
    else:
        model = HFModel(path, device)
    model.rule = rule
    if rule != "bos":
        model.prefiks = []
    return model


# ---------------------------------------------------------------- data

def load_records():
    """The 4374 rows of ewok-core-1.0 (gated on HF, pinned revision), in file order."""
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download(DATASET_REPO, DATASET_FILE, repo_type="dataset", revision=DATASET_REV)
    return [{"id": f"ewok-en-{i:04d}", "source_id": i, **r} for i, r in enumerate(pd.read_parquet(p).to_dict("records"))]


def authors_pair(model, context, target):
    """(context ids, target ids) as `Model._score`: tokens of the query with the tokenizer's special tokens, split at
    the length of the context tokenized the same way."""
    full = model.encode_special(f"{context} {target}")
    start = len(model.encode_special(context))
    return full[:start], full[start:]


def record_pairs(model, r):
    """6 pairs (context ids, target ids): (C1,T1), (C1,T2), (C2,T1), (C2,T2), then T1 and T2 without context."""
    if getattr(model, "rule", "plain") == "authors":
        pairs = [authors_pair(model, r[c], r[t]) for c in ("Context1", "Context2") for t in ("Target1", "Target2")]
    else:
        pairs = [para(model, r[c], " " + r[t]) for c in ("Context1", "Context2") for t in ("Target1", "Target2")]
    return pairs + [para(model, "", r[t]) for t in ("Target1", "Target2")]


def logliks(model, pairs, batch=32):
    """As `hipoteza_formatu.licz_logliki` (right padding, head only on the target positions), but with the `authors`
    rule the logit of `model.masked_id()` is -inf before the softmax, as in `surprisal`."""
    if getattr(model, "rule", "plain") != "authors":
        return licz_logliki(model, pairs, batch)
    masked = model.masked_id()
    out = [None] * len(pairs)
    for c, t in pairs:
        if len(c) + len(t) - 1 > model.max_len:
            raise ValueError(f"input of {len(c) + len(t) - 1} tokens exceeds the context of {model.max_len}")
    order = sorted(range(len(pairs)), key=lambda i: -(len(pairs[i][0]) + len(pairs[i][1])))
    for s in range(0, len(order), batch):
        idx = order[s:s + batch]
        seqs = [(pairs[i][0] + pairs[i][1], len(pairs[i][1])) for i in idx]
        T = max(len(p) - 1 for p, _ in seqs)
        x = torch.full((len(seqs), T), model.pad, dtype=torch.long)
        for j, (p, _) in enumerate(seqs):
            x[j, :len(p) - 1] = torch.tensor(p[:-1])
        h = model.ukryte(x.to(model.device))
        for j, (i, (p, nc)) in enumerate(zip(idx, seqs)):
            L = len(p) - 1
            logits = model.glowa(h[j, L - nc:L])
            if masked is not None:
                logits[:, masked] = -float("inf")
            lp = torch.log_softmax(logits, -1).cpu()
            out[i] = (lp.gather(1, torch.tensor(p[-nc:])[:, None]).sum().item(), nc)
    return out


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
        ll = logliks(model, [p for r in part for p in record_pairs(model, r)], batch)
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


def domain_clusters(diffs):
    """Domains as clusters (as paradigms in benchmarks/blimp): unweighted mean of the k domain means, SE = sd / sqrt(k),
    t with df = k - 1, two-sided p from Student's t, verdict from p at the thresholds of |z| = 3 and |z| = 2. Answers
    whether the difference holds for other domains, not only for these records."""
    x = np.array(diffs, dtype=float)
    k = len(x)
    se = float(x.std(ddof=1) / math.sqrt(k))
    t = float(x.mean() / se) if se else 0.0
    p = p_student(t, k - 1)
    return {"k": k, "value": float(x.mean()), "se": se, "t": t, "df": k - 1, "p": p, "verdict": werdykt_p(p)}


def contrast(a, b, name_a, name_b, meta, tmpl):
    """Paired difference of `ewok` on the same records: SE over records and, the one that decides, over templates;
    per domain (SE over templates within the domain) and over the domains as clusters."""
    common = sorted(set(a) & set(b))
    d = [a[k]["ewok"] - b[k]["ewok"] for k in common]
    cl = [tmpl[meta[k]["source_id"]] for k in common]
    r = cluster_mean(d, cl)
    r["z"] = r["value"] / r["se"] if r["se"] else 0.0
    r["verdict"] = verdict(r["z"])
    per = defaultdict(lambda: ([], []))
    for k, x, c in zip(common, d, cl):
        per[meta[k]["Domain"]][0].append(x)
        per[meta[k]["Domain"]][1].append(c)
    domains = {}
    for dom, (xs, cs) in sorted(per.items()):
        m = cluster_mean(xs, cs)
        m["z"] = m["value"] / m["se"] if m["se"] else 0.0
        m["verdict"] = verdict(m["z"])
        m["a"] = float(np.mean([a[k]["ewok"] for k in common if meta[k]["Domain"] == dom]))
        m["b"] = float(np.mean([b[k]["ewok"] for k in common if meta[k]["Domain"] == dom]))
        domains[dom] = m
    return {"a": name_a, "b": name_b, "n": len(d), "diff": srednia_z_niepewnoscia(d), "a_better": sum(x > 0 for x in d),
            "b_better": sum(x < 0 for x in d), "diff_by_template": r, "p_by_template": permutation_test(d, clusters=cl),
            "domains": domains, "diff_by_domain_clusters": domain_clusters([v["value"] for v in domains.values()])}


def add_holm(report):
    """Holm columns (tools/statystyka.py po_holmie; family = one table): the measured model against every other
    model by template (p of z) and over domains as clusters (p of t), and per contrast its domain table (p of z)."""
    ks = report["contrasts"]
    for key, col, p in (("diff_by_template", "holm_by_template", lambda k: p_z(k["diff_by_template"]["z"])),
                        ("diff_by_domain_clusters", "holm_by_domain_clusters", lambda k: k["diff_by_domain_clusters"]["p"])):
        for k, h in zip(ks, po_holmie([p(k) for k in ks])):
            k[col] = h
    for k in ks:
        doms = k["domains"]
        for d, h in zip(doms, po_holmie([p_z(v["z"]) for v in doms.values()])):
            doms[d]["holm"] = h
    return report


# ---------------------------------------------------------------- commands

def cmd_score(a):
    model = build_model(a.model, a.device, rule=a.rule)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    score(model, load_records(), out / "ewok.jsonl", batch=a.batch)


def cmd_report(a):
    recs = load_records()
    meta = {r["id"]: {"source_id": r["source_id"], "Domain": r["Domain"]} for r in recs}
    tmpl = templates(recs)
    models = a.models.split(",")
    rows = {m: read_rows(Path(a.results) / m / "ewok.jsonl") for m in models}
    report = {"protocol": {"dataset": f"{DATASET_REPO}@{DATASET_REV}", "rule": a.rule, "mode": MODES[a.rule],
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
                r, g = k["diff_by_template"], k["diff_by_domain_clusters"]
                print(f"{a.measured} - {m:24s} {100 * r['value']:+.2f} pts  SE {100 * r['se']:.2f}  z {r['z']:+.1f}  "
                      f"{r['verdict']}  |  domains (k={g['k']}): {100 * g['value']:+.2f} SE {100 * g['se']:.2f} "
                      f"t {g['t']:+.2f} p {g['p']:.4f} {g['verdict']}")
    Path(a.out).write_text(json.dumps(add_holm(report), indent=1, ensure_ascii=False), encoding="utf-8")


def przebieg_wynik(task_id, recs, rows, tmpl):
    """Observation of one (model, EWoK) pair for tools/przebieg_centralny.sh: the main score is the mean over records
    with the SE by template (METODOLOGIA, type `para +klastry`), chance 0.5 (a constant preference gets exactly 1/2)."""
    scores = {r["id"]: evaluate(rows[r["id"]]) for r in recs}
    meta = {r["id"]: {"source_id": r["source_id"], "Domain": r["Domain"]} for r in recs}
    space = summarize(scores, meta, tmpl)
    space["glowna"] = {**space["ewok_by_template"], "metryka": "ewok"}
    space["bazy"] = {"chance_value": 0.5, "majority_value": None}
    space["ties"] = sum(ties(rows[r["id"]]) for r in recs)
    return {"task_id": task_id, "metric": "ewok", "state": "ok", "value": space["glowna"]["value"],
            "n_scored": len(recs), "dodatkowe": {"space": space}}


def cmd_przebieg(a):
    """One (model, task) pair of the central run, same flags as common/ewaluuj.py: rule `authors`, records in file
    order (`--probka N`: the first N, a load test), per-record rows in <wyjscie>/probki/ewok.jsonl (a rerun resumes),
    <wyjscie>/results_rozszerzone.json. A failure is an observation with state `failed` and exit code 1."""
    out = Path(a.wyjscie)
    (out / "probki").mkdir(parents=True, exist_ok=True)
    protokol = {"dataset": f"{DATASET_REPO}@{DATASET_REV}", "rule": "authors", "mode": MODES["authors"],
                "probka": a.probka, "batch": a.batch, "device": a.device}
    try:
        recs = load_records()
        tmpl = templates(recs)
        wybrane = recs if a.probka == "pelna" else recs[:int(a.probka)]
        plik = out / "probki" / "ewok.jsonl"
        score(build_model(a.model_path, a.device), wybrane, plik, batch=a.batch)
        obs = przebieg_wynik(a.zadania, wybrane, read_rows(plik), tmpl)
        obs["n_population"] = len(recs)
    except Exception as e:  # noqa: BLE001 - the run records the failure and goes on with the next pair
        obs = {"task_id": a.zadania, "metric": "ewok", "state": "failed", "reason": f"{type(e).__name__}: {e}"}
    obs.update(model=a.etykieta, repo=a.repo, revision=a.revision, protocol=protokol)
    (out / "results_rozszerzone.json").write_text(json.dumps({"observations": [obs]}, indent=1, ensure_ascii=False),
                                                  encoding="utf-8")
    print(json.dumps({k: obs.get(k) for k in ("task_id", "model", "state", "value", "n_scored", "reason")}))
    return 0 if obs["state"] == "ok" else 1


def cmd_holm(a):
    """Holm columns on a report already in the repo (the records' text, and so the templates, are not in the repo)."""
    path = Path(a.report)
    path.write_text(json.dumps(add_holm(json.loads(path.read_text(encoding="utf-8"))), indent=1, ensure_ascii=False),
                    encoding="utf-8")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score", help="log P per record for one model")
    s.add_argument("--model", required=True)
    s.add_argument("--out", required=True, help="directory; the run writes <out>/ewok.jsonl")
    s.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    s.add_argument("--batch", type=int, default=32)
    s.add_argument("--rule", choices=RULES, default="authors",
                   help="authors (default), plain (no special tokens, no pad mask) or bos (one BOS before the context)")
    r = sub.add_parser("report", help="accuracy, SE by template and contrasts from <results>/<model>/ewok.jsonl")
    r.add_argument("--results", default=str(HERE / "results"))
    r.add_argument("--models", required=True)
    r.add_argument("--measured", help="model compared with every other one, e.g. Slayer1B-1.06")
    r.add_argument("--out", default=str(HERE / "results" / "ewok.json"))
    r.add_argument("--rule", choices=RULES, default="authors",
                   help="the rule the per-record files were scored with; only labels the report")
    h = sub.add_parser("holm", help="add the Holm columns to an existing report")
    h.add_argument("--report", default=str(HERE / "results" / "ewok.json"))
    c = sub.add_parser("przebieg", help="one (model, task) pair of tools/przebieg_centralny.sh")
    c.add_argument("--model_path", required=True)
    c.add_argument("--zadania", required=True, help="task id of common/zadania.py ZADANIA")
    c.add_argument("--probka", default="pelna", help="pelna | number of records (first in file order)")
    c.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    c.add_argument("--batch", type=int, default=1)
    c.add_argument("--etykieta", default="")
    c.add_argument("--repo", default="")
    c.add_argument("--revision", default="")
    c.add_argument("--wyjscie", required=True)
    a = p.parse_args()
    kod = {"score": cmd_score, "report": cmd_report, "holm": cmd_holm, "przebieg": cmd_przebieg}[a.cmd](a)
    sys.exit(kod or 0)


if __name__ == "__main__":
    main()
