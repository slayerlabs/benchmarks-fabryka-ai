"""PROTOCOL.md hypotheses L1-L3: LFM3-1.7B against Qwen3.5-9B, paired by problem.

Usage: python3 compare.py [results-dir]   (default: results/ next to this file)
Reads <results-dir>/<model-id>.jsonl.gz (and <model-id>.json for the control), prints a Markdown table and writes
<results-dir>/hypotheses.json.

Every difference is LFM3-1.7B minus the other model, in percentage points, over the problems both models answered
(`status: ok`): an error or a prompt over the context on either side leaves the problem out of both sides, and the
count is reported. SE of a paired difference = sd(d) / sqrt(n); z = mean / SE; p two-sided normal. Verdict from the
raw z: |z| >= 3 clear, 2-3 likely, < 2 noise; SE = 0 gives no z and the verdict `undecidable`. Holm over the three
hypotheses with m = 3 always; a hypothesis whose models have not been run is `not run`, and still counts in m.
Qwen3.5-4B and Bielik 11B v3.1 against LFM3-1.7B are printed with the same numbers as descriptive rows, not tested.
"""

import gzip
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
LFM = "lfm3-1.7b"
QWEN9 = "qwen3.5-9b"
DESCRIPTIVE = ("qwen3.5-4b", "bielik-11b-v3.1-vllm")
DIFFICULTIES = ("easy", "medium", "hard")
BUDGETS = (4096, 16384, None)  # PROTOCOL.md, "Metrics"; None = no limit
CONTROL_CARD = 69.86  # PROTOCOL.md, "Control": Qwen3.5-9B on the LFM3-1.7B card

# Parameters used per generated token: the language model's weights (embeddings and LM head included, a tied matrix
# once), without Qwen3.5's vision encoder and multi-token-prediction head, which text generation does not run.
# Qwen3.5 and Bielik: config arithmetic from config.json at the PROTOCOL.md revisions (Qwen3.5: 24 Gated DeltaNet +
# 8 gated-attention layers, the text_config shapes; Bielik: Llama, 50 layers, untied head); each total equals the sum
# of the matching tensor shapes in the model's safetensors headers at that revision. LFM3-1.7B: the model card
# ("Parameters: 1.73B"), exact value the sum of tensor shapes in its safetensors header at the pinned revision.
PARAMETERS = {
    "lfm3-1.7b": 1_728_801_536,
    "qwen3.5-4b": 4_205_751_296,  # card: "4B" with the vision encoder (333.5M) and MTP head (120.6M)
    "qwen3.5-9b": 8_953_803_264,  # card: "9B" with the vision encoder (456.0M) and MTP head (243.3M)
    "bielik-11b-v3.1-vllm": 11_168_796_672,  # card: "11 billion parameters"
}

P_CLEAR = math.erfc(3 / math.sqrt(2))  # two-sided p at |z| = 3
P_LIKELY = math.erfc(2 / math.sqrt(2))  # two-sided p at |z| = 2

HYPOTHESES = {
    "L1": "LFM3-1.7B's lead over Qwen3.5-9B is not larger than 3 SE of the paired difference",
    "L2": "LFM3-1.7B - Qwen3.5-9B is positive on easy and medium, negative on hard",
    "L3": "at an equal cost per answer, LFM3-1.7B's lead over Qwen3.5-9B disappears",
}
DEVIATIONS = [
    "L2 has no single test statistic in PROTOCOL.md; its p for Holm is the largest of the three per-level two-sided "
    "p values (intersection-union: the pattern holds only if every level's sign does), its z the level's with that p.",
    "PROTOCOL.md gives only L2's refutation; L2 is `confirmed` only with signs (+, +, -) and |z| >= 2 on every level, "
    "`refuted` with the same sign on all three levels, otherwise `not established`.",
    "'parameters' in the cost per answer is read as the language model's weights (Qwen3.5: without the vision "
    "encoder and the MTP head), not the rounded card figures.",
]


def load(results: Path, model: str) -> dict[str, dict] | None:
    path = results / f"{model}.jsonl.gz"
    if not path.is_file():
        return None
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def scored(r: dict) -> bool:
    return r["status"] == "ok" and r["pass"] is not None


def passes_within(r: dict, budget: int | None) -> bool:
    """Counts at budget B only if it passed, finished, and used at most B output tokens (PROTOCOL.md, "Metrics")."""
    return bool(r["pass"]) and bool(r["finished"]) and (budget is None or r["output_tokens"] <= budget)


def cost(model: str, r: dict, budget: int | None) -> float:
    """2 x parameters x output tokens, the tokens capped at the budget (an answer cut at B used B tokens)."""
    tokens = r["output_tokens"] if budget is None else min(r["output_tokens"], budget)
    return 2 * PARAMETERS[model] * tokens


def verdict(z: float | None) -> str:
    if z is None:
        return "undecidable"
    return "clear" if abs(z) >= 3 else "likely" if abs(z) >= 2 else "noise"


def verdict_p(p: float | None) -> str:
    if p is None:
        return "undecidable"
    return "clear" if p <= P_CLEAR else "likely" if p <= P_LIKELY else "noise"


def paired(d: list[float]) -> dict[str, Any]:
    """Mean of d in percentage points with SE sd(d)/sqrt(n), z and two-sided p; z None when SE is 0 or n < 2."""
    n = len(d)
    if n < 2:
        return {"value": 100 * d[0] if d else None, "se": None, "z": None, "p": None, "verdict": "undecidable", "n": n}
    mean = statistics.fmean(d)
    se = statistics.stdev(d) / math.sqrt(n)
    z = mean / se if se > 0 else None
    return {"value": 100 * mean, "se": 100 * se, "z": z, "p": None if z is None else math.erfc(abs(z) / math.sqrt(2)),
            "verdict": verdict(z), "n": n}


def pair(a_runs: dict, b_runs: dict) -> tuple[list[str], dict[str, int]]:
    """Problems answered by both; the rest is counted by reason, never scored."""
    ids = sorted(set(a_runs) | set(b_runs))
    keep = [t for t in ids if t in a_runs and t in b_runs and scored(a_runs[t]) and scored(b_runs[t])]
    excluded = {
        "not_scored_a": sum(1 for t in ids if t in a_runs and not scored(a_runs[t])),
        "not_scored_b": sum(1 for t in ids if t in b_runs and not scored(b_runs[t])),
        "missing_a": sum(1 for t in ids if t not in a_runs),
        "missing_b": sum(1 for t in ids if t not in b_runs),
    }
    excluded["total"] = len(ids) - len(keep)
    return keep, excluded


def equal_cost(a: str, b: str, a_runs: dict, b_runs: dict, ids: list[str]) -> dict[str, Any]:
    """The budget pair (one budget per model) whose mean costs are closest (ratio nearest 1) and the paired
    difference of pass-at-budget there; every pair's mean costs are kept."""
    pairs = []
    for ba in BUDGETS:
        for bb in BUDGETS:
            ca = statistics.fmean(cost(a, a_runs[t], ba) for t in ids)
            cb = statistics.fmean(cost(b, b_runs[t], bb) for t in ids)
            pairs.append({"budget_a": ba, "budget_b": bb, "mean_cost_a": ca, "mean_cost_b": cb,
                          "log_ratio": abs(math.log(ca / cb)) if ca > 0 and cb > 0 else math.inf})
    best = min(pairs, key=lambda x: x["log_ratio"])  # first in BUDGETS order on a tie
    d = [int(passes_within(a_runs[t], best["budget_a"])) - int(passes_within(b_runs[t], best["budget_b"])) for t in ids]
    return {**paired(d), **{k: best[k] for k in ("budget_a", "budget_b", "mean_cost_a", "mean_cost_b")},
            "pairs": [{k: v for k, v in x.items() if k != "log_ratio"} for x in pairs]}


def compare(a: str, b: str, a_runs: dict, b_runs: dict) -> dict[str, Any]:
    ids, excluded = pair(a_runs, b_runs)

    def diff(subset: list[str]) -> dict[str, Any]:
        return paired([int(bool(a_runs[t]["pass"])) - int(bool(b_runs[t]["pass"])) for t in subset])

    return {
        "a": a, "b": b, "excluded": excluded,
        "overall": diff(ids),
        "per_difficulty": {lvl: diff([t for t in ids if a_runs[t]["difficulty"] == lvl]) for lvl in DIFFICULTIES},
        "equal_cost": equal_cost(a, b, a_runs, b_runs, ids) if ids else None,
        "v6_only": diff([t for t in ids if a_runs[t]["in_v6_only"]]),
    }


def sign(x: float | None) -> str:
    return "?" if x is None else "+" if x > 0 else "-" if x < 0 else "0"


def l1(c: dict) -> dict[str, Any]:
    o = c["overall"]
    outcome = "undecidable" if o["z"] is None else "refuted" if o["z"] >= 3 else "confirmed"
    return {**o, "measure": "pass@1 difference, all problems", "outcome": outcome}


def l2(c: dict) -> dict[str, Any]:
    levels = c["per_difficulty"]
    signs = "".join(sign(levels[lvl]["value"]) for lvl in DIFFICULTIES)
    weak = [lvl for lvl in DIFFICULTIES if levels[lvl]["z"] is None or abs(levels[lvl]["z"]) < 2]
    if signs in ("+++", "---"):
        outcome = "refuted"
    elif signs == "++-" and not weak:
        outcome = "confirmed"
    else:
        outcome = "not established"
    ps = [levels[lvl]["p"] for lvl in DIFFICULTIES]
    p = None if None in ps else max(ps)
    at = DIFFICULTIES[ps.index(p)] if p is not None else None
    return {"measure": "sign pattern easy/medium/hard", "value": None, "se": None,
            "z": levels[at]["z"] if at else None, "p": p, "verdict": verdict(levels[at]["z"]) if at else "undecidable",
            "n": sum(levels[lvl]["n"] for lvl in DIFFICULTIES), "signs": signs, "sign_not_established": weak,
            "per_difficulty": levels, "outcome": outcome}


def l3(c: dict) -> dict[str, Any]:
    e = c["equal_cost"]
    if e is None:
        return {"measure": "pass@budget difference at equal cost", "value": None, "se": None, "z": None, "p": None,
                "verdict": "undecidable", "n": 0, "outcome": "undecidable"}
    outcome = "undecidable" if e["z"] is None else "refuted" if e["value"] > 0 and e["z"] >= 3 else "confirmed"
    return {**{k: v for k, v in e.items() if k != "pairs"}, "measure": "pass@budget difference at equal cost",
            "outcome": outcome}


def holm(ps: list[float | None], m: int) -> list[float | None]:
    """Holm step-down adjusted p over a family of m; a missing p (not run) is ranked last as p = 1, which never
    lowers another hypothesis's multiplier."""
    filled = [1.0 if p is None else p for p in ps] + [1.0] * (m - len(ps))
    order = sorted(range(len(filled)), key=lambda i: filled[i])
    adjusted, running = [0.0] * len(filled), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * filled[i]))
        adjusted[i] = running
    return [None if p is None else adjusted[i] for i, p in enumerate(ps)]


def control(results: Path) -> dict[str, Any]:
    """Qwen3.5-9B must land within 2 SE of its card value before any hypothesis is read (PROTOCOL.md)."""
    path = results / f"{QWEN9}.json"
    if not path.is_file():
        return {"status": "not run", "card": CONTROL_CARD}
    r = json.loads(path.read_text(encoding="utf-8"))
    if r["score"] is None or not r["stderr"]:
        return {"status": "undecidable", "card": CONTROL_CARD, "score": r["score"], "stderr": r["stderr"]}
    z = (r["score"] - CONTROL_CARD) / r["stderr"]
    return {"status": "passed" if abs(z) <= 2 else "failed", "card": CONTROL_CARD, "score": r["score"],
            "stderr": r["stderr"], "z": z}


def analyse(results: Path) -> dict[str, Any]:
    runs = {m: load(results, m) for m in (LFM, QWEN9, *DESCRIPTIVE)}
    deviations = list(DEVIATIONS)
    main = compare(LFM, QWEN9, runs[LFM], runs[QWEN9]) if runs[LFM] is not None and runs[QWEN9] is not None else None
    missing = [m for m in (LFM, QWEN9) if runs[m] is None]
    rows = []
    for hid, fn in (("L1", l1), ("L2", l2), ("L3", l3)):
        if main is None:
            rows.append({"id": hid, "statement": HYPOTHESES[hid], "outcome": "not run", "missing": missing,
                         "value": None, "se": None, "z": None, "p": None, "verdict": "not run", "n": 0})
        else:
            rows.append({"id": hid, "statement": HYPOTHESES[hid], **fn(main), "excluded": main["excluded"]})
    for row, p in zip(rows, holm([r["p"] for r in rows], m=3)):
        row["p_holm"] = p
        row["verdict_holm"] = "not run" if row["outcome"] == "not run" else verdict_p(p)
    if missing:
        deviations.append("a hypothesis that is not run counts in Holm's m = 3 with p = 1 (ranked last).")
    descriptive = []
    for other in (QWEN9, *DESCRIPTIVE):
        if runs[LFM] is None or runs[other] is None:
            descriptive.append({"a": LFM, "b": other, "status": "not run",
                                "missing": [m for m in (LFM, other) if runs[m] is None]})
        else:
            descriptive.append({"status": "ok", **(main if other == QWEN9 else compare(LFM, other, runs[LFM], runs[other]))})
    return {"benchmark": "LiveCodeBench v6", "protocol": "PROTOCOL.md", "difference": "LFM3-1.7B minus other, pp",
            "control": control(results), "hypotheses": rows, "descriptive": descriptive,
            "parameters": PARAMETERS, "holm_m": 3, "deviations": deviations}


def fmt(x: float | None, spec: str) -> str:
    return "" if x is None else format(x, spec)


def value_se(r: dict) -> str:
    return "" if r.get("value") is None else f"{r['value']:+.2f} ± {fmt(r['se'], '.2f')}"


def budget(b: int | None) -> str:
    return "none" if b is None else str(b)


def report(a: dict) -> str:
    out = []
    c = a["control"]
    if c["status"] in ("passed", "failed"):
        out.append(f"control: Qwen3.5-9B {c['score']:.2f} ± {c['stderr']:.2f} vs card {c['card']}, "
                   f"z = {c['z']:+.2f}: {c['status']}")
        if c["status"] == "failed":
            out.append("control failed: the setup is the suspect; no hypothesis is read until the gap is explained")
    else:
        out.append(f"control: {c['status']}")
    out += ["", "| hypothesis | measure | value ± SE (pp) | z | Holm p | verdict | after Holm | outcome | n |",
            "|---|---|---|---|---|---|---|---|---|"]
    for r in a["hypotheses"]:
        measure = r.get("measure", "")
        if r["outcome"] == "not run":
            out.append(f"| {r['id']} | | | | | not run | not run | not run (missing: {', '.join(r['missing'])}) | |")
            continue
        if r["id"] == "L2":
            weak = r["sign_not_established"]
            measure += f": {r['signs']}" + (f" (sign not established: {', '.join(weak)})" if weak else "")
        if r["id"] == "L3" and "mean_cost_a" in r:
            measure += (f" (LFM3 B = {budget(r['budget_a'])}, Qwen3.5-9B B = {budget(r['budget_b'])}; "
                        f"mean cost {r['mean_cost_a']:.3g} vs {r['mean_cost_b']:.3g} FLOPs)")
        n = f"{r['n']} (excluded {r['excluded']['total']})"
        out.append(f"| {r['id']} | {measure} | {value_se(r)} | {fmt(r['z'], '+.2f')} | {fmt(r['p_holm'], '.3g')} | "
                   f"{r['verdict']} | {r['verdict_holm']} | {r['outcome']} | {n} |")
        if r["id"] == "L2":
            for lvl, x in r["per_difficulty"].items():
                note = " (sign not established)" if lvl in r["sign_not_established"] else ""
                out.append(f"| L2 {lvl} | pass@1 difference, {lvl}{note} | {value_se(x)} | {fmt(x['z'], '+.2f')} | "
                           f"| {x['verdict']} | | | {x['n']} |")
    out += ["", "Descriptive (not tested), LFM3-1.7B minus each model:", "",
            "| model | measure | value ± SE (pp) | z | verdict | n | excluded |", "|---|---|---|---|---|---|---|"]
    for d in a["descriptive"]:
        if d["status"] == "not run":
            out.append(f"| {d['b']} | not run (missing: {', '.join(d['missing'])}) | | | | | |")
            continue
        ex = d["excluded"]["total"]
        lines = [("all problems", d["overall"])]
        lines += [(lvl, d["per_difficulty"][lvl]) for lvl in DIFFICULTIES]
        if d["equal_cost"]:
            e = d["equal_cost"]
            lines.append((f"equal cost (B = {budget(e['budget_a'])} / {budget(e['budget_b'])}; "
                          f"{e['mean_cost_a']:.3g} vs {e['mean_cost_b']:.3g} FLOPs)", e))
        lines.append(("v6-only problems", d["v6_only"]))
        for name, r in lines:
            out.append(f"| {d['b']} | {name} | {value_se(r)} | {fmt(r['z'], '+.2f')} | {r['verdict']} | {r['n']} | {ex} |")
    out.append("")
    out += [f"deviation: {x}" for x in a["deviations"]]
    return "\n".join(out)


def main(results: Path) -> None:
    a = analyse(results)
    print(report(a))
    results.mkdir(parents=True, exist_ok=True)
    (results / "hypotheses.json").write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results")
