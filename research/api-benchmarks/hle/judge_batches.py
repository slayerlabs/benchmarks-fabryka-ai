"""Run HLE judging plan via Anthropic Message Batches API.

Order: (1) Opus on all predictions, (2) Opus repeat on 100, (3) Sonnet on same 300.
Cap: 15 USD (estimated before each batch, actual tracked from usage).
"""
from __future__ import annotations

import argparse, json, math, os, random, time
from pathlib import Path

import anthropic
import numpy as np
from datasets import load_dataset

import judge as J

HERE = Path(__file__).resolve().parent
PRICING_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"


def _env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise SystemExit(f"missing required env: {name}")
    return v


def judge_config():
    # Single source of truth: env / run.sh. No hardcoded model IDs.
    judge_model = _env("JUDGE_MODEL")
    agreement_model = _env("AGREEMENT_MODEL")
    stability_model = os.environ.get("STABILITY_MODEL")
    prices = {
        judge_model: {
            "input": float(_env("JUDGE_BATCH_INPUT_USD_PER_MTOK")) / 1e6,
            "output": float(_env("JUDGE_BATCH_OUTPUT_USD_PER_MTOK")) / 1e6,
            "source": PRICING_SOURCE,
        },
        agreement_model: {
            "input": float(_env("AGREEMENT_BATCH_INPUT_USD_PER_MTOK")) / 1e6,
            "output": float(_env("AGREEMENT_BATCH_OUTPUT_USD_PER_MTOK")) / 1e6,
            "source": PRICING_SOURCE,
        },
    }
    if stability_model:
        prices[stability_model] = {
            "input": float(_env("STABILITY_BATCH_INPUT_USD_PER_MTOK")) / 1e6,
            "output": float(_env("STABILITY_BATCH_OUTPUT_USD_PER_MTOK")) / 1e6,
            "source": PRICING_SOURCE,
        }
    return judge_model, agreement_model, stability_model, prices


CAP_USD = 15.0


def load_env():
    J.load_dotenv()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=key, timeout=300.0, max_retries=0)


def load_questions():
    ds = load_dataset("cais/hle", split="test").to_dict()
    qs = [dict(zip(ds.keys(), v)) for v in zip(*ds.values())]
    return {q["id"]: q for q in qs}


def build_requests(questions, predictions, ids, model):
    reqs = []
    for qid in ids:
        if qid not in predictions or qid not in questions:
            continue
        q = questions[qid]
        p = predictions[qid]
        prompt = J.JUDGE_PROMPT.format(question=q["question"], correct_answer=q["answer"], response=p["response"])
        reqs.append({
            "custom_id": qid,
            "params": {
                "model": model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
                "tools": J.TOOLS,
                "tool_choice": {"type": "auto"},
            },
        })
    return reqs


def estimate_usd(reqs, predictions, questions, model, prices):
    # rough char/3.5 for input, 150 output tokens
    inp = 0
    for r in reqs:
        qid = r["custom_id"]
        q, p = questions[qid], predictions[qid]
        inp += (600 + len(q["question"]) + len(q["answer"]) + len(p.get("response", ""))) / 3.5
    out = len(reqs) * 150
    pr = prices[model]
    return inp * pr["input"] + out * pr["output"], inp, out


def submit_and_wait(client, reqs, poll=30):
    batch = client.messages.batches.create(requests=reqs)
    print(f"batch {batch.id} submitted n={len(reqs)}", flush=True)
    while True:
        b = client.messages.batches.retrieve(batch.id)
        counts = getattr(b, "request_counts", None)
        print(f"batch {batch.id} {b.processing_status} {counts}", flush=True)
        if b.processing_status == "ended":
            return batch.id
        time.sleep(poll)


def collect_results(client, batch_id, questions, predictions, configured_model):
    judged = {}
    total_in = total_out = 0
    failed = []
    no_tool = 0
    for entry in client.messages.batches.results(batch_id):
        qid = entry.custom_id
        result = entry.result
        if result.type != "succeeded":
            failed.append((qid, result.type))
            continue
        msg = result.message
        returned_model = getattr(msg, "model", None)
        if not returned_model or not str(returned_model).startswith(configured_model):
            raise SystemExit(f"model mismatch for {qid}: got {returned_model!r}, expected prefix {configured_model!r}")
        usage = msg.usage
        total_in += getattr(usage, "input_tokens", 0)
        total_out += getattr(usage, "output_tokens", 0)
        tool_use = None
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "judge":
                tool_use = block
                break
        if tool_use is None:
            no_tool += 1
            failed.append((qid, "no_tool_call"))
            continue
        try:
            parsed = J.ExtractedAnswer.model_validate(tool_use.input)
        except Exception as e:
            failed.append((qid, f"schema:{e}"))
            continue
        q = questions[qid]
        pred = dict(predictions[qid])
        pred["judge_response"] = {
            "correct_answer": q["answer"],
            "model_answer": parsed.extracted_final_answer,
            "reasoning": parsed.reasoning,
            "correct": parsed.correct,
            "confidence": parsed.confidence,
        }
        pred["_judge_usage"] = {
            "input_tokens": getattr(usage, "input_tokens", 0),
            "output_tokens": getattr(usage, "output_tokens", 0),
        }
        pred["judge_model"] = returned_model
        judged[qid] = pred
    return judged, total_in, total_out, failed, no_tool


def save_judged(path, judged):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(judged, f, indent=2, ensure_ascii=False)


def cost_usd(model, inp, out, prices):
    pr = prices[model]
    return inp * pr["input"] + out * pr["output"]


def calib_err(confidence, correct, p="2", beta=100):
    idxs = np.argsort(confidence)
    confidence = confidence[idxs]
    correct = correct[idxs]
    bins = [[i * beta, (i + 1) * beta] for i in range(len(confidence) // beta)]
    if bins:
        bins[-1] = [bins[-1][0], len(confidence)]
    cerr = 0
    total_examples = len(confidence)
    for i in range(len(bins) - 1):
        bconf = confidence[bins[i][0]:bins[i][1]]
        bcorr = correct[bins[i][0]:bins[i][1]]
        nbin = len(bconf)
        if nbin > 0:
            diff = np.abs(np.nanmean(bconf) - np.nanmean(bcorr))
            if p == "2":
                cerr += nbin / total_examples * np.square(diff)
            elif p == "1":
                cerr += nbin / total_examples * diff
            else:
                cerr = np.maximum(cerr, diff)
    if p == "2":
        cerr = np.sqrt(cerr)
    return float(cerr)


def accuracy_stats(judged, n_total):
    correct = []
    confidence = []
    for v in judged.values():
        jr = v.get("judge_response")
        if not jr:
            continue
        correct.append("yes" in jr.get("correct", ""))
        confidence.append(jr.get("confidence", 100))
    correct = np.array(correct)
    confidence = np.array(confidence) / 100
    n = len(correct)
    acc = 100 * float(correct.sum()) / n_total if n_total else 0.0
    # stderr on percent scale: sqrt(p*(1-p)/n) * 100
    p = acc / 100.0
    stderr = 100 * math.sqrt(p * (1 - p) / n_total) if n_total else 0.0
    cal = 100 * calib_err(confidence, correct, p="2", beta=100) if n else 0.0
    return n, acc, stderr, cal


def cohens_kappa(labels_a, labels_b):
    # labels are 0/1
    n = len(labels_a)
    if n == 0:
        return float("nan")
    a = np.array(labels_a); b = np.array(labels_b)
    po = float((a == b).mean())
    p_yes_a = float(a.mean()); p_yes_b = float(b.mean())
    pe = p_yes_a * p_yes_b + (1 - p_yes_a) * (1 - p_yes_b)
    if pe == 1.0:
        return 1.0
    return (po - pe) / (1 - pe)


def run_plan(client, questions, predictions, outdir, plan, prices, cap_usd):
    spent = 0.0
    tokens_total = {"input": 0, "output": 0}
    runs = []
    for name, model, ids, outpath in plan:
        existing = {}
        if outpath.exists():
            existing = json.load(open(outpath, encoding="utf-8"))
        todo = [i for i in ids if i not in existing]
        if not todo:
            print(f"{name}: already complete n={len(existing)}", flush=True)
            runs.append({"name": name, "model": model, "n": len(existing), "input_tokens": 0, "output_tokens": 0, "usd": 0.0, "skipped": "complete"})
            continue
        reqs = build_requests(questions, predictions, todo, model)
        est, _, _ = estimate_usd(reqs, predictions, questions, model, prices)
        print(f"{name}: todo={len(todo)} est_usd={est:.2f} spent={spent:.2f} cap={cap_usd:.2f}", flush=True)
        if spent + est > cap_usd:
            print(f"{name}: SKIPPED would exceed cap (est {spent+est:.2f} > {cap_usd:.2f})", flush=True)
            runs.append({"name": name, "model": model, "n": 0, "skipped": "cap"})
            continue
        batch_id = submit_and_wait(client, reqs)
        judged, tin, tout, failed, no_tool = collect_results(client, batch_id, questions, predictions, model)
        existing.update(judged)
        save_judged(str(outpath), existing)
        usd = cost_usd(model, tin, tout, prices)
        spent += usd
        tokens_total["input"] += tin
        tokens_total["output"] += tout
        run = {
            "name": name, "model": model, "configured_model": model, "batch_id": batch_id,
            "n_requested": len(todo), "n_judged": len(judged), "n_total_file": len(existing),
            "failed": len(failed), "no_tool": no_tool,
            "input_tokens": tin, "output_tokens": tout, "usd": round(usd, 6),
            "failed_ids": [f[0] for f in failed],
            "returned_models": sorted({v.get("judge_model") for v in judged.values()}),
        }
        runs.append(run)
        print(f"{name}: judged={len(judged)} failed={len(failed)} tokens_in={tin} tokens_out={tout} usd={usd:.6f} spent_total={spent:.6f}", flush=True)
        if failed:
            print(f"{name} failed_ids={failed[:20]}", flush=True)
        if spent > cap_usd:
            print(f"WARNING: spent {spent:.2f} > cap {cap_usd:.2f}", flush=True)
    return runs, spent, tokens_total


def confusion(a_labels, b_labels):
    # rows a, cols b, labels [0=no,1=yes]
    tn = sum(1 for a,b in zip(a_labels,b_labels) if a==0 and b==0)
    fp = sum(1 for a,b in zip(a_labels,b_labels) if a==0 and b==1)
    fn = sum(1 for a,b in zip(a_labels,b_labels) if a==1 and b==0)
    tp = sum(1 for a,b in zip(a_labels,b_labels) if a==1 and b==1)
    return {"tn_no_no": tn, "fp_no_yes": fp, "fn_yes_no": fn, "tp_yes_yes": tp}


def pair_agreement(name_a, name_b, ja, jb, ids):
    common = [qid for qid in ids if qid in ja and qid in jb]
    la = [1 if "yes" in ja[qid]["judge_response"]["correct"] else 0 for qid in common]
    lb = [1 if "yes" in jb[qid]["judge_response"]["correct"] else 0 for qid in common]
    n = len(common)
    agree = sum(1 for x,y in zip(la,lb) if x==y)
    pct = 100 * agree / n if n else float("nan")
    kappa = cohens_kappa(la, lb) if n else float("nan")
    dis = [qid for qid,x,y in zip(common,la,lb) if x!=y]
    return {
        "pair": f"{name_a} vs {name_b}",
        "n": n,
        "agreement_pct": round(pct, 4) if n else None,
        "cohens_kappa": round(kappa, 6) if n else None,
        "confusion": confusion(la, lb) if n else None,
        "disagreement_ids_first_10": dis[:10],
    }


def build_report(predictions, outdir, ids_300, ids_100, runs, spent, tokens_total, cap_usd):
    # Main judge: prefer judged_opus4_all (kept main), else judged_opus_all
    main_path = outdir / "judged_opus4_all.json" if (outdir / "judged_opus4_all.json").exists() else outdir / "judged_opus_all.json"
    opus_main = json.load(open(main_path, encoding="utf-8")) if main_path.exists() else {}
    opus5_300 = json.load(open(outdir / "judged_opus5_300.json", encoding="utf-8")) if (outdir / "judged_opus5_300.json").exists() else {}
    son5_300 = json.load(open(outdir / "judged_sonnet5_300.json", encoding="utf-8")) if (outdir / "judged_sonnet5_300.json").exists() else {}
    opus4_rep = json.load(open(outdir / "judged_opus4_repeat_100.json", encoding="utf-8")) if (outdir / "judged_opus4_repeat_100.json").exists() else {}
    # legacy
    opus_rep = opus4_rep or (json.load(open(outdir / "judged_opus_repeat_100.json", encoding="utf-8")) if (outdir / "judged_opus_repeat_100.json").exists() else {})
    son300 = son5_300 or (json.load(open(outdir / "judged_sonnet_300.json", encoding="utf-8")) if (outdir / "judged_sonnet_300.json").exists() else {})

    n_judged, acc, stderr, cal = accuracy_stats(opus_main, len(predictions))

    three_way = []
    if opus_main and opus5_300:
        three_way.append(pair_agreement("opus4.6", "opus5.5", opus_main, opus5_300, ids_300))
    if opus_main and son5_300:
        three_way.append(pair_agreement("opus4.6", "sonnet5.5", opus_main, son5_300, ids_300))
    if opus5_300 and son5_300:
        three_way.append(pair_agreement("opus5.5", "sonnet5.5", opus5_300, son5_300, ids_300))

    self_ag = None
    if opus_main and opus_rep:
        common100 = [qid for qid in ids_100 if qid in opus_main and qid in opus_rep]
        la = [1 if "yes" in opus_main[qid]["judge_response"]["correct"] else 0 for qid in common100]
        lb = [1 if "yes" in opus_rep[qid]["judge_response"]["correct"] else 0 for qid in common100]
        n = len(common100)
        agree = sum(1 for x,y in zip(la,lb) if x==y)
        self_ag = {"n": n, "self_agreement_pct": round(100*agree/n, 4) if n else None, "cohens_kappa": round(cohens_kappa(la,lb), 6) if n else None, "confusion": confusion(la,lb) if n else None}

    # legacy fields for compatibility
    legacy_pair = three_way[-1] if three_way else None
    return {
        "model": "bielik-11b-v3.1",
        "benchmark": "Humanity's Last Exam (no tools), text-only subset",
        "n_total_predictions": len(predictions),
        "n_judged_main": n_judged,
        "main_judge_model": next((v.get("judge_model") for v in opus_main.values() if v.get("judge_model")), None),
        "accuracy": round(acc, 4),
        "stderr": round(stderr, 4),
        "stderr_formula": "sqrt(p*(1-p)/n)*100, percent scale",
        "calibration_error": round(cal, 4),
        "tokens": tokens_total,
        "usd_spent": round(spent, 6),
        "cap_usd": cap_usd,
        "pricing_source": PRICING_SOURCE,
        "runs": runs,
        "three_way_agreement": three_way,
        "self_agreement_opus4_repeat_100": self_ag,
        "opus_sonnet_agreement_n": legacy_pair["n"] if legacy_pair else 0,
        "opus_sonnet_agreement_pct": legacy_pair["agreement_pct"] if legacy_pair else None,
        "opus_sonnet_cohens_kappa": legacy_pair["cohens_kappa"] if legacy_pair else None,
        "disagreement_ids_first_10": legacy_pair["disagreement_ids_first_10"] if legacy_pair else [],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--predictions", default=str(HERE / "out/bielik-11b-v3.1/hle_bielik-11b-v3.1.json"))
    ap.add_argument("--outdir", default=str(HERE / "out/bielik-11b-v3.1"))
    ap.add_argument("--cap-usd", type=float, default=CAP_USD)
    ap.add_argument("--mode", choices=["pilot5", "full", "agreement"], required=True)
    args = ap.parse_args()

    J.load_dotenv()
    judge_model, agreement_model, stability_model, prices = judge_config()
    client = load_env()
    questions = load_questions()
    predictions = json.load(open(args.predictions, encoding="utf-8"))
    all_ids = sorted(predictions.keys())
    ids_300 = all_ids[:300]
    ids_100 = all_ids[:100]
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if args.mode == "pilot5":
        plan = [("pilot5_opus", judge_model, all_ids[:5], outdir / "judged_pilot5_configured.json")]
    elif args.mode == "agreement":
        if not stability_model:
            raise SystemExit("STABILITY_MODEL required for agreement mode")
        plan = [
            ("opus5_300", judge_model, ids_300, outdir / "judged_opus5_300.json"),
            ("sonnet5_300", agreement_model, ids_300, outdir / "judged_sonnet5_300.json"),
            ("opus4_repeat_100", stability_model, ids_100, outdir / "judged_opus4_repeat_100.json"),
        ]
    else:
        plan = [
            ("opus_all", judge_model, all_ids, outdir / "judged_opus_all.json"),
            ("opus_repeat_100", judge_model, ids_100, outdir / "judged_opus_repeat_100.json"),
            ("sonnet_300", agreement_model, ids_300, outdir / "judged_sonnet_300.json"),
        ]

    runs, spent, tokens_total = run_plan(client, questions, predictions, outdir, plan, prices, args.cap_usd)
    report = build_report(predictions, outdir, ids_300, ids_100, runs, spent, tokens_total, args.cap_usd)
    report["config"] = {
        "judge_model": judge_model,
        "agreement_model": agreement_model,
        "stability_model": stability_model,
        "prices": {k: {"input_usd_per_mtok": v["input"] * 1e6, "output_usd_per_mtok": v["output"] * 1e6, "source": v["source"]} for k, v in prices.items()},
    }
    name = {"pilot5": "judge_pilot5_report.json", "agreement": "judge_agreement_report.json"}.get(args.mode, "judge_report.json")
    report_path = outdir / name
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(json.dumps(report, indent=2, ensure_ascii=False), flush=True)
    return report


if __name__ == "__main__":
    main()
