"""BLiMP: our scorer against lm-eval 0.4.9.1 per pair, and the Pythia-1B v0 control (LM_EVAL_PROTOCOL.md).

  python benchmarks/blimp/lm_eval_compare.py extract --samples <lm-eval --output_path dir> --out <model>.jsonl.gz
  python benchmarks/blimp/lm_eval_compare.py compare --results <dir> --out benchmarks/blimp/results/lm_eval_agreement.json
  python benchmarks/blimp/lm_eval_compare.py sample --results <dir> --pythia <tokenizer dir> --slayer <tokenizer dir> \
      --out tests/dane/blimp_zgodnosc.json   # sample of tests/test_blimp_zgodnosc.py

<dir> holds pythia-1b-v0/blimp.jsonl.gz (P1, our code), lm-eval/pythia-1b-v0.jsonl.gz (P2),
lm-eval/slayer-1.06.jsonl.gz (P3) and optionally gpu-check/slayer-1.06.jsonl.gz (P4, our code on the same GPU).
The repo result of Slayer 1.06 (our code, MPS) is benchmarks/blimp/results/1.06/blimp.jsonl.gz.
"""

import argparse
import glob
import gzip
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import blimp as B  # noqa: E402

PUBLISHED_V0 = B.REFERENCJA_PYTHIA["wartosc"]
POINTS_2 = 0.02
MIN_AGREEMENT = 0.99
SENSE_MIN = 0.45
SLAYER_REPO = B.KORZEN / "benchmarks/blimp/results/1.06/blimp.jsonl.gz"


def sample_row(s):
    """One `--log_samples` record of a blimp_* subtask -> {id, ll [good, bad], acc} with our pair id."""
    d = s["doc"]
    ll = [float(r[0]) for r in s["filtered_resps"]]
    return {"id": f"blimp_{d['UID']}/{d['pair_id']}", "ll": ll, "acc": int(round(float(s["acc"])))}


def read_samples(directory):
    """All samples_blimp_*.jsonl under an lm-eval output dir -> {id: row}; a repeated id is an error."""
    rows = {}
    files = sorted(glob.glob(str(Path(directory) / "**" / "samples_blimp_*.jsonl"), recursive=True))
    if not files:
        raise SystemExit(f"no samples_blimp_*.jsonl under {directory}")
    for f in files:
        with open(f) as fh:
            for line in fh:
                if line.strip():
                    r = sample_row(json.loads(line))
                    if r["id"] in rows:
                        raise SystemExit(f"duplicate pair {r['id']} in {f}")
                    rows[r["id"]] = r
    return rows


def read_rows(path):
    """jsonl(.gz) with an `id` per line -> {id: row}."""
    return B.wczytaj_wyniki(path)


def accuracy(hits, docs):
    """Equal-weight mean of paradigm accuracies and its stratified SE, over the docs present in `hits`."""
    per = {}
    for d in docs:
        if d["id"] in hits:
            per.setdefault(d["grupa"], []).append(hits[d["id"]])
    strata = [per[g] for g in sorted(per)]
    acc = sum(sum(x) / len(x) for x in strata) / len(strata)
    return {"acc": acc, "se": B.se_warstwowe(strata), "n": sum(len(x) for x in strata), "n_paradigms": len(strata)}


def our_hits(rows, docs):
    return {d["id"]: B.trafienie_pary(d, rows[d["id"]]) for d in docs if d["id"] in rows}


def ref_hits(rows):
    return {i: r["acc"] for i, r in rows.items()}


def agreement(ours, ref, docs, partial=False):
    """Our decisions (blimp.trafienie_pary) against lm-eval decisions (`acc`) on the same pairs."""
    sel = [d for d in docs if d["id"] in ours and d["id"] in ref]
    ids = [d["id"] for d in sel]
    if not partial and len(ids) != len(docs):
        raise SystemExit(f"only {len(ids)} of {len(docs)} pairs in both results")
    h_o, h_r = our_hits(ours, sel), ref_hits({i: ref[i] for i in ids})
    a_o, a_r = accuracy(h_o, sel), accuracy(h_r, sel)
    disagree = []
    for d in sel:
        i = d["id"]
        if h_o[i] != h_r[i]:
            lo, lr = ours[i]["ll"], ref[i]["ll"]
            disagree.append({"id": i, "ours": h_o[i], "lm_eval": h_r[i], "ll_ours": lo, "ll_lm_eval": lr,
                             "margin_ours": lo[0] - lo[1], "margin_lm_eval": lr[0] - lr[1],
                             "identical_sentences": d["opcje"][0] == d["opcje"][1]})
    dll = [abs(ours[i]["ll"][k] - ref[i]["ll"][k]) for i in ids for k in (0, 1)]
    agree = len(ids) - len(disagree)
    return {"n": len(ids), "agree": agree, "share": agree / len(ids), "acc_ours": a_o["acc"], "se_ours": a_o["se"],
            "acc_lm_eval": a_r["acc"], "se_lm_eval": a_r["se"], "diff": a_o["acc"] - a_r["acc"],
            "max_abs_dll": max(dll), "mean_abs_dll": sum(dll) / len(dll), "disagreements": disagree}


def verdict_agreement(ag):
    """Protocol conditions (b)/(c): >= 99% same decisions and |accuracy difference| <= 1 SE of the lm-eval result."""
    share_ok = ag["share"] >= MIN_AGREEMENT
    se_ok = abs(ag["diff"]) <= ag["se_lm_eval"]
    return {"share_ok": share_ok, "within_1_se": se_ok, "pass": share_ok and se_ok}


def verdict_published(acc, se, published=PUBLISHED_V0):
    """Protocol condition (a): within 2 points of the published value, or within 2 SE when 2 SE > 2 points."""
    threshold = max(POINTS_2, 2 * se)
    diff = acc - published
    return {"published": published, "acc": acc, "se": se, "diff": diff, "threshold": threshold,
            "pass": abs(diff) <= threshold}


def sense(acc):
    """Full-result sanity check: 1.000 or below 0.45 is a code error, not a result."""
    return SENSE_MIN <= acc < 1.0


def compare(results, docs, slayer_repo=SLAYER_REPO, partial=False):
    R = Path(results)
    p1 = read_rows(R / "pythia-1b-v0/blimp.jsonl.gz")
    p2 = read_rows(R / "lm-eval/pythia-1b-v0.jsonl.gz")
    p3 = read_rows(R / "lm-eval/slayer-1.06.jsonl.gz")
    s_repo = read_rows(slayer_repo)
    out = {"protocol": "benchmarks/blimp/LM_EVAL_PROTOCOL.md", "n_docs": len(docs), "partial": partial}
    lm_v0 = accuracy(ref_hits(p2), [d for d in docs if d["id"] in p2])
    our_v0 = accuracy(our_hits(p1, docs), [d for d in docs if d["id"] in p1])
    out["a"] = {"lm_eval": verdict_published(lm_v0["acc"], lm_v0["se"]),
                "ours_info": verdict_published(our_v0["acc"], our_v0["se"])}
    b = agreement(p1, p2, docs, partial)
    out["b"] = {**b, **verdict_agreement(b)}
    c = agreement(s_repo, p3, docs, partial)
    out["c"] = {**c, **verdict_agreement(c)}
    p4_path = R / "gpu-check/slayer-1.06.jsonl.gz"
    if p4_path.exists():
        p4 = read_rows(p4_path)
        d_lm = agreement(p4, p3, docs, partial)
        # the repo file as the reference side: its decisions are ours (trafienie_pary), not lm-eval's
        repo_as_ref = {d["id"]: {**s_repo[d["id"]], "acc": B.trafienie_pary(d, s_repo[d["id"]])}
                       for d in docs if d["id"] in s_repo}
        d_repo = agreement(p4, repo_as_ref, docs, partial)
        out["d"] = {"gpu_ours_vs_lm_eval": d_lm, "gpu_ours_vs_repo_mps": d_repo}
    out["sense"] = {k: sense(v) for k, v in (("pythia_v0_lm_eval", lm_v0["acc"]), ("pythia_v0_ours", our_v0["acc"]),
                                             ("slayer_lm_eval", out["c"]["acc_lm_eval"]))}
    return out


def pick_sample(docs):
    """Pairs at file positions 0 and 500 of every paradigm plus the pairs with identical sentences."""
    per = {}
    for d in docs:
        per.setdefault(d["grupa"], []).append(d)
    picked = [x for g in sorted(per) for x in (per[g][0], per[g][min(500, len(per[g]) - 1)])]
    seen = {d["id"] for d in picked}
    picked += [d for d in docs if d["opcje"][0] == d["opcje"][1] and d["id"] not in seen]
    return picked


def lm_eval_encodings(sample_docs, pythia_dir, slayer_dir):
    """Token ids lm-eval 0.4.9.1 feeds the model for each sentence of `sample_docs`: the blimp `_template_yaml`
    config builds the requests (ConfigurableTask.construct_requests), HFLM / SlayerLM.loglikelihood encodes them
    (prefix token, `_encode_pair`); the model forward is replaced, so no weights are loaded.
    -> {model: {"prefix_token_id", "bos", "eos", "pairs": {id: [[ctx ids, cont ids] x 2]}}}"""
    import yaml
    import lm_eval
    import transformers
    from lm_eval.api.task import ConfigurableTask
    from lm_eval.models.huggingface import HFLM
    sys.path.insert(0, str(B.KORZEN / "common"))
    import slayer_lm
    template = yaml.safe_load((Path(lm_eval.__file__).parent / "tasks/blimp/_template_yaml").read_text())

    def requests(doc):
        cfg = dict(template)
        files = sorted((B.katalog_danych() / doc["grupa"]).glob("train-*.parquet"))
        cfg.update({"task": f"blimp_{doc['grupa']}", "dataset_path": "parquet", "dataset_name": None,
                    "dataset_kwargs": {"data_files": {"train": [str(p) for p in files]}}})
        task = ConfigurableTask(config=cfg)
        ctx = task.fewshot_context(doc["rekord"], num_fewshot=0)
        return [i.args for i in task.construct_requests(doc=doc["rekord"], ctx=ctx, metadata=(cfg["task"], 0, 1))]

    def encoder(cls, tok):
        lm = object.__new__(cls)
        lm.tokenizer, lm.custom_prefix_token_id, lm.backend, lm.add_bos_token = tok, None, "causal", False
        lm.AUTO_MODEL_CLASS = transformers.AutoModelForCausalLM
        caught = []
        lm._loglikelihood_tokens = lambda reqs, disable_tqdm=False: caught.extend(reqs) or [(0.0, True)] * len(reqs)

        class Req:
            def __init__(self, args):
                self.args = args

        def encode(args):
            caught.clear()
            lm.loglikelihood([Req(x) for x in args], disable_tqdm=True)
            return [[list(c), list(k)] for _, c, k in caught]
        return lm, encode

    tok_p = transformers.AutoTokenizer.from_pretrained(pythia_dir)
    tok_s = slayer_lm.set_slayer_tokens(transformers.PreTrainedTokenizerFast(tokenizer_file=str(Path(slayer_dir) / "tokenizer.json")))
    out = {}
    for name, cls, tok in (("pythia-1b-v0", HFLM, tok_p), ("slayer-1.06", slayer_lm.SlayerLM, tok_s)):
        lm, encode = encoder(cls, tok)
        out[name] = {"prefix_token_id": lm.prefix_token_id, "bos": tok.bos_token_id, "eos": tok.eos_token_id,
                     "pairs": {d["id"]: encode(requests(d)) for d in sample_docs}}
    return out


def build_sample(results, docs, pythia_dir, slayer_dir, slayer_repo=SLAYER_REPO):
    """Test sample for tests/test_blimp_zgodnosc.py: pairs of pick_sample with both codes' log-likelihoods and
    decisions and the lm-eval token ids, for Pythia-1B v0 (P1, P2) and Slayer 1.06 (repo file, P3)."""
    R = Path(results)
    picked = pick_sample(docs)
    enc = lm_eval_encodings(picked, pythia_dir, slayer_dir)
    sources = {"pythia-1b-v0": (read_rows(R / "pythia-1b-v0/blimp.jsonl.gz"), read_rows(R / "lm-eval/pythia-1b-v0.jsonl.gz")),
               "slayer-1.06": (read_rows(slayer_repo), read_rows(R / "lm-eval/slayer-1.06.jsonl.gz"))}
    out = {"protocol": "benchmarks/blimp/LM_EVAL_PROTOCOL.md", "lm_eval": "0.4.9.1", "dataset": f"{B.REPO}@{B.REWIZJA}",
           "pairs": [{"id": d["id"], "grupa": d["grupa"], "zjawisko": d["zjawisko"], "opcje": d["opcje"]} for d in picked],
           "models": {}}
    for name, (ours, ref) in sources.items():
        e = enc[name]
        out["models"][name] = {
            "prefix_token_id": e["prefix_token_id"], "bos": e["bos"], "eos": e["eos"],
            "rows": {d["id"]: {"ll_ours": ours[d["id"]]["ll"], "ntok_ours": ours[d["id"]]["ntok"],
                               "ll_lm_eval": ref[d["id"]]["ll"], "acc_lm_eval": ref[d["id"]]["acc"],
                               "lm_eval_tokens": e["pairs"][d["id"]]} for d in picked}}
    return out


def cmd_sample(a):
    docs = B.wczytaj(a.dane)
    out = build_sample(a.results, docs, a.pythia, a.slayer, Path(a.slayer_repo))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"pairs": len(out["pairs"]), "bytes": Path(a.out).stat().st_size}))


def cmd_extract(a):
    rows = read_samples(a.samples)
    docs_order = sorted(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(a.out, "wt") as f:
        for i in docs_order:
            f.write(json.dumps(rows[i]) + "\n")
    print(json.dumps({"pairs": len(rows), "out": a.out}))


def cmd_compare(a):
    docs = B.wczytaj(a.dane)
    out = compare(a.results, docs, Path(a.slayer_repo), a.partial)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"a": out["a"]["lm_eval"]["pass"], "b": out["b"]["pass"], "c": out["c"]["pass"],
                      "acc_v0_lm_eval": out["a"]["lm_eval"]["acc"], "acc_v0_ours": out["b"]["acc_ours"],
                      "agree_b": out["b"]["share"], "agree_c": out["c"]["share"], "sense": out["sense"]}))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--samples", required=True)
    e.add_argument("--out", required=True)
    c = sub.add_parser("compare")
    c.add_argument("--results", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--slayer-repo", default=str(SLAYER_REPO))
    c.add_argument("--dane")
    c.add_argument("--partial", action="store_true", help="smoke test on a subset: compare the pairs present in both")
    s = sub.add_parser("sample")
    s.add_argument("--results", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--pythia", required=True, help="directory with the Pythia-1B v0 tokenizer files")
    s.add_argument("--slayer", required=True, help="directory with the Slayer 1.06 tokenizer.json")
    s.add_argument("--slayer-repo", default=str(SLAYER_REPO))
    s.add_argument("--dane")
    a = p.parse_args(argv)
    return {"extract": cmd_extract, "compare": cmd_compare, "sample": cmd_sample}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
