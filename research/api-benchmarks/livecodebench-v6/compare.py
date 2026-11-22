"""PROTOCOL.md hypotheses L1-L3 (Amendment 1): LFM3-1.7B against Bielik 11B v3.1, paired by problem.

Usage: python3 compare.py [results-dir]   (default: results/ next to this file)
Reads <results-dir>/<model-id>.jsonl.gz (and <model-id>.json for the control), prints a Markdown table and writes
<results-dir>/hypotheses.json, recording its sha256 in <results-dir>/manifest.json.

Every difference is LFM3-1.7B minus the other model, in percentage points, over the problems both models answered
(`status: ok`): an error or a prompt over the context on either side leaves the problem out of both sides, and the
count is reported. SE of a paired difference = sd(d) / sqrt(n); z = mean / SE; p two-sided normal. Verdict from the
raw z: |z| >= 3 clear, 2-3 likely, < 2 noise; SE = 0 gives no z and the verdict `undecidable`. Holm over the three
hypotheses with m = 3 always; a hypothesis whose models have not been run is `not run`, and still counts in m.
The control (Amendment 1) is LFM3-1.7B's own pass@1 against its card value, from the card-sampling run
(`lfm3-1.7b-cardsampling`, Amendment 4) when it exists, with the original `lfm3-1.7b` run shown next to it as
descriptive. L1-L3 are decided on the original `lfm3-1.7b` run (the verdict run, #170); as Amendment 4 reports both
numbers when A1 does not show the samplings equivalent, they are also computed on `lfm3-1.7b-cardsampling` (its own
Holm, m = 3), and the `reading` line of each hypothesis gives both outcomes: where they differ, the hypothesis
depends on the sampling settings and the question it asks is unresolved. The v6-only problems and every budget pair
of L3 are printed as descriptive rows, not tested.
L1 and L3 also get a clustered SE, descriptive (the rules note: an SE over problems treats problems of one contest
as independent): the same mean difference with the SE from the spread between clusters, by contest (platform and
contest time; the data has no contest id) and by platform (k = 3), t = mean / SE read at df = k - 1 with the verdict
from its two-sided p at the p of |z| = 3 and 2 (research/tools/statystyka.py, `se_k`; fewer than 3 clusters is
`undecidable`).
Exploratory rows, added after the results and labelled so: L1 and L3 after extraction rule F1 (extraction.py), and
L3 at an exactly equal mean cost and with the prompt counted in the cost (`exploratory_cost`). They never change an
outcome under PROTOCOL.md.
Every result file read must have the sha256 summarize.py recorded in <results-dir>/manifest.json; otherwise
nothing is computed.
"""

import gzip
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

import provenance

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import statystyka  # noqa: E402  (research/tools: SE clustered with unequal cluster sizes, t at df = k - 1)

HERE = Path(__file__).parent
LFM = "lfm3-1.7b"
BIELIK = "bielik-11b-v3.1"  # the Fabryka API run (PROTOCOL.md, Amendment 1)
DIFFICULTIES = ("easy", "medium", "hard")
BUDGETS = (4096, 16384, None)  # PROTOCOL.md, "Metrics"; None = no limit
CONTROL_CARD = 73.46  # PROTOCOL.md, Amendment 1, "Control": LFM3-1.7B on its own card
# PROTOCOL.md, Amendment 4: A1 was not shown equivalent, so the card-sampling run is the one compared with the card
CONTROL_RUN = "lfm3-1.7b-cardsampling"
EXTRACTION = "extraction-f1.json"  # exploratory, written by extraction.py (rule F1); read only when present
# Clusters for the clustered SE of L1 and L3: problems of one contest share setters, date and topics
CLUSTERS = {
    "contest": lambda r: f"{r['platform']} {r['contest_date']}",  # a contest's start time on its platform
    "platform": lambda r: r["platform"],
}
VERDICT_EN = {"pewne": "clear", "prawdopodobne": "likely", "szum": "noise", statystyka.NIEROZSTRZYGALNE: "undecidable",
              None: "undecidable"}

# Parameters used per generated token: the language model's weights (embeddings and LM head included, a tied matrix
# once). Bielik: config arithmetic from config.json at the PROTOCOL.md revision (Llama, 50 layers, untied head),
# equal to the sum of the tensor shapes in its safetensors headers there; the API serves the same model name, its
# weights are not visible. LFM3-1.7B: the model card ("Parameters: 1.73B"), exact value the sum of tensor shapes in
# its safetensors header at the pinned revision.
PARAMETERS = {
    "lfm3-1.7b": 1_728_801_536,
    "bielik-11b-v3.1": 11_168_796_672,  # card: "11 billion parameters"
}
WEIGHTS = {LFM: LFM, CONTROL_RUN: LFM, BIELIK: BIELIK}  # run -> model weights (the card-sampling run: same weights)

P_CLEAR = math.erfc(3 / math.sqrt(2))  # two-sided p at |z| = 3
P_LIKELY = math.erfc(2 / math.sqrt(2))  # two-sided p at |z| = 2

HYPOTHESES = {
    "L1": "LFM3-1.7B's lead over Bielik 11B v3.1 is not larger than 3 SE of the paired difference",
    "L2": "LFM3-1.7B - Bielik 11B v3.1 is positive on easy and medium, negative on hard",
    "L3": "at an equal cost per answer, LFM3-1.7B's lead over Bielik 11B v3.1 disappears",
}
DEVIATIONS = [
    "L2 has no single test statistic in PROTOCOL.md; its p for Holm is the largest of the three per-level two-sided "
    "p values (intersection-union: the pattern holds only if every level's sign does), its z the level's with that p.",
    "PROTOCOL.md gives only L2's refutation; L2 is `confirmed` only with signs (+, +, -) and |z| >= 2 on every level, "
    "`refuted` with the same sign on all three levels, otherwise `not established`.",
    "'parameters' in the cost per answer is read as the language model's exact weight count from the safetensors "
    "headers, not the rounded card figures.",
]


def load(results: Path, model: str) -> dict[str, dict] | None:
    path = results / f"{model}.jsonl.gz"
    if not path.is_file():
        return None
    provenance.verify(results, [path.name], "compare.py")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def scored(r: dict) -> bool:
    return r["status"] == "ok" and r["pass"] is not None


def passes_within(r: dict, budget: int | None) -> bool:
    """Counts at budget B only if it passed, finished, and used at most B output tokens (PROTOCOL.md, "Metrics")."""
    return bool(r["pass"]) and bool(r["finished"]) and (budget is None or r["output_tokens"] <= budget)


def cost(run: str, r: dict, budget: int | None) -> float:
    """2 x parameters x output tokens, the tokens capped at the budget (an answer cut at B used B tokens)."""
    tokens = r["output_tokens"] if budget is None else min(r["output_tokens"], budget)
    return 2 * PARAMETERS[WEIGHTS[run]] * tokens


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
            **prompt_cost(a, b, a_runs, b_runs, ids, best),
            "clustered": clustered(d, [a_runs[t] for t in ids]),
            "pairs": [{k: v for k, v in x.items() if k != "log_ratio"} for x in pairs]}


def prompt_cost(a: str, b: str, a_runs: dict, b_runs: dict, ids: list[str], best: dict) -> dict[str, float]:
    """Descriptive: PROTOCOL.md leaves the prompt out of the cost ("shared by all models"), but each model's prompt
    is its own count with its own template (Bielik's with the API's provider system prompt). The mean prompt tokens
    and the mean cost at the chosen pair with the prompt counted, 2 x parameters x (prompt + output tokens)."""
    pa = statistics.fmean(a_runs[t]["prompt_tokens"] for t in ids)
    pb = statistics.fmean(b_runs[t]["prompt_tokens"] for t in ids)
    return {"mean_prompt_tokens_a": pa, "mean_prompt_tokens_b": pb,
            "mean_cost_with_prompt_a": best["mean_cost_a"] + 2 * PARAMETERS[WEIGHTS[a]] * pa,
            "mean_cost_with_prompt_b": best["mean_cost_b"] + 2 * PARAMETERS[WEIGHTS[b]] * pb}


def clustered(d: list[int], rows: list[dict]) -> dict[str, Any] | None:
    """The mean of d (pp) with its SE clustered by each of CLUSTERS: t = mean / SE at df = k - 1, the verdict from
    the t's p (statystyka.se_k; k < 3 `undecidable`). Descriptive; None without problems."""
    if not d:
        return None
    out = {}
    for name, key in CLUSTERS.items():
        r = statystyka.se_k([float(x) for x in d], [key(row) for row in rows])
        out[name] = {"k": r["k"], "value": 100 * r["roznica"], "se": None if r["se"] is None else 100 * r["se"],
                     "t": r["t"], "df": r["df"], "p": r["p_t"], "verdict": VERDICT_EN[r["werdykt"]]}
    return out


def compare(a: str, b: str, a_runs: dict, b_runs: dict) -> dict[str, Any]:
    ids, excluded = pair(a_runs, b_runs)

    def diff(subset: list[str]) -> dict[str, Any]:
        return paired([int(bool(a_runs[t]["pass"])) - int(bool(b_runs[t]["pass"])) for t in subset])

    return {
        "a": a, "b": b, "excluded": excluded,
        "overall": {**diff(ids), "clustered": clustered(
            [int(bool(a_runs[t]["pass"])) - int(bool(b_runs[t]["pass"])) for t in ids], [a_runs[t] for t in ids])},
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


def against_card(results: Path, model: str) -> dict[str, Any] | None:
    """One LFM3-1.7B run's pass@1 against the card: z = (score - card) / stderr; None when the run is absent."""
    path = results / f"{model}.json"
    if not path.is_file():
        return None
    provenance.verify(results, [path.name], "compare.py")
    r = json.loads(path.read_text(encoding="utf-8"))
    if r["score"] is None or not r["stderr"]:
        return {"run": model, "status": "undecidable", "card": CONTROL_CARD, "score": r["score"], "stderr": r["stderr"]}
    z = (r["score"] - CONTROL_CARD) / r["stderr"]
    return {"run": model, "status": "passed" if abs(z) <= 2 else "failed", "card": CONTROL_CARD, "score": r["score"],
            "stderr": r["stderr"], "z": z}


def control(results: Path) -> dict[str, Any]:
    """LFM3-1.7B must land within 2 SE of its card value before any hypothesis is read (PROTOCOL.md, Amendment 1).
    The run tested is the card-sampling one when it exists (Amendment 4), else `lfm3-1.7b`; when both exist the
    original is shown next to it, not tested."""
    card_run, original = against_card(results, CONTROL_RUN), against_card(results, LFM)
    tested = card_run or original
    if tested is None:
        return {"status": "not run", "run": None, "card": CONTROL_CARD}
    if card_run is not None and original is not None:
        return {**card_run, "descriptive": {k: v for k, v in original.items() if k != "status"}}
    return tested


def family(lfm: str, runs: dict) -> tuple[list[dict], dict | None, list[str]]:
    """L1-L3 of one LFM3-1.7B run against Bielik, with Holm over the three (m = 3)."""
    main = compare(lfm, BIELIK, runs[lfm], runs[BIELIK]) if runs[lfm] is not None and runs[BIELIK] is not None else None
    missing = [m for m in (lfm, BIELIK) if runs[m] is None]
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
    return rows, main, missing


def reading(rows: list[dict], other: dict | None, exploratory: dict | None = None) -> list[dict[str, Any]]:
    """Each hypothesis on the verdict run next to the card-sampling run (Amendment 4 reports both numbers when A1
    does not show the samplings equivalent). Where the protocol's rule gives another outcome on the second run, the
    hypothesis depends on the sampling settings and the question it asks is unresolved, whatever the verdict run
    says; the text never gives the verdict run's outcome alone. L1 and L3 add, as descriptive, the verdicts with the
    clustered SE and, when present, after the exploratory extraction rule F1."""
    def z(r: dict) -> str:
        return "n/a" if r["z"] is None else f"{r['z']:+.2f}"

    out = []
    for i, r in enumerate(rows):
        o = other["hypotheses"][i] if other else None
        if r["outcome"] == "not run" or o is None or o["outcome"] == "not run":
            out.append({"id": r["id"], "outcome": r["outcome"], "outcome_other_run": o and o["outcome"],
                        "depends_on_sampling": None, "text": f"{r['id']}: {r['outcome']} on {LFM} (the verdict run)"})
            continue
        depends = r["outcome"] != o["outcome"]
        if depends:
            text = (f"{r['id']}: the protocol's rule gives `{r['outcome']}` on {LFM}, the verdict run (z = {z(r)}, "
                    f"{r['verdict']}), but `{o['outcome']}` on {CONTROL_RUN} (z = {z(o)}, {o['verdict']}): "
                    f"{r['id']} depends on the sampling settings, so the question it asks is unresolved")
        else:
            text = f"{r['id']}: {r['outcome']} on both runs ({LFM} z = {z(r)}, {CONTROL_RUN} z = {z(o)})"
        pairs = ((LFM, r), (CONTROL_RUN, o))
        if r.get("clustered") and o.get("clustered"):
            text += "; descriptive, verdict with the SE clustered " + "; ".join(
                f"by {name} (k = {r['clustered'][name]['k']}): "
                + ", ".join(f"{x['clustered'][name]['verdict']} on {run}" for run, x in pairs) for name in CLUSTERS)
        f1 = {e["run"]: e.get(r["id"]) for e in exploratory["hypotheses"]} if exploratory else {}
        if all(f1.get(run) for run, _ in pairs):
            text += "; exploratory, after extraction rule F1: " + ", ".join(
                f"z = {z(f1[run])} ({f1[run]['verdict']}) on {run}" for run, _ in pairs)
        out.append({"id": r["id"], "outcome": r["outcome"], "outcome_other_run": o["outcome"],
                    "depends_on_sampling": depends, "text": text})
    return out


def analyse(results: Path) -> dict[str, Any]:
    runs = {m: load(results, m) for m in (LFM, CONTROL_RUN, BIELIK)}
    deviations = list(DEVIATIONS)
    rows, main, missing = family(LFM, runs)
    if missing:
        deviations.append("a hypothesis that is not run counts in Holm's m = 3 with p = 1 (ranked last).")
    if main is None:
        descriptive = [{"a": LFM, "b": BIELIK, "status": "not run", "missing": missing}]
    else:
        descriptive = [{"status": "ok", **main}]
    other = None
    if runs[CONTROL_RUN] is not None:  # Amendment 4: both runs reported; the verdict run stays LFM (#170)
        other_rows, other_main, _ = family(CONTROL_RUN, runs)
        other = {"run": CONTROL_RUN, "role": "reported next to the verdict run (Amendment 4), not the verdict",
                 "hypotheses": other_rows}
        if other_main is not None:
            descriptive.append({"status": "ok", **other_main})
    f1 = load_f1(results, runs)
    exploratory = exploratory_extraction(f1, runs)
    return {"benchmark": "LiveCodeBench v6", "protocol": "PROTOCOL.md", "difference": "LFM3-1.7B minus other, pp",
            "control": control(results), "verdict_run": LFM, "hypotheses": rows, "other_run": other,
            "reading": reading(rows, other, exploratory), "descriptive": descriptive,
            "extraction": {m: empty_code(r) for m, r in runs.items() if r is not None},
            "exploratory_extraction": exploratory, "exploratory_cost": exploratory_cost(runs, f1),
            "parameters": PARAMETERS, "holm_m": 3, "deviations": deviations}


def empty_code(run: dict[str, dict]) -> dict[str, int]:
    """Answered problems whose extracted code is empty (LiveCodeBench found fewer than two fence lines): a fail."""
    ok = [r for r in run.values() if r["status"] == "ok"]
    return {"answered": len(ok), "empty_code": sum(1 for r in ok if r["output"] == "")}


def load_f1(results: Path, runs: dict) -> tuple[dict, str, dict] | None:
    """results/extraction-f1.json (checked against the manifest and against the result files it was computed
    from), its sha256, and every loaded run with the F1 regrade over its official grades; None when absent."""
    path = results / EXTRACTION
    if not path.is_file():
        return None
    sha = provenance.verify(results, [EXTRACTION], "compare.py")[EXTRACTION]
    x = json.loads(path.read_text(encoding="utf-8"))
    recorded = provenance.read_manifest(results)["files"]
    loaded = [m for m, r in runs.items() if r is not None]
    for m in loaded:
        if x["runs"][m]["result"]["sha256"] != recorded[f"{m}.jsonl.gz"]["sha256"]:
            sys.exit(f"compare.py: {path} was computed from another {m}.jsonl.gz than the one in {results}; "
                     "run extraction.py again")
    regraded = {}
    for m in loaded:
        new = x["runs"][m]["regraded"]
        regraded[m] = {t: {**r, "pass": new[t]["pass"]} if t in new else r for t, r in runs[m].items()}
    return x, sha, regraded


def exploratory_extraction(f1: tuple | None, runs: dict) -> dict[str, Any] | None:
    """Exploratory, after the results: L1 and L3 with every run's answers graded under extraction rule F1
    (extraction.py, results/extraction-f1.json); None when that file is absent. The official numbers stand."""
    if f1 is None:
        return None
    x, sha, regraded = f1
    rows = []
    for lfm in (LFM, CONTROL_RUN):
        if runs[lfm] is None or runs[BIELIK] is None:
            continue
        c = compare(lfm, BIELIK, regraded[lfm], regraded[BIELIK])
        keep = ("value", "se", "z", "p", "verdict", "n")
        e = c["equal_cost"]
        rows.append({"run": lfm, "L1": {k: c["overall"][k] for k in keep},
                     "L3": {**{k: e[k] for k in keep}, "budget_a": e["budget_a"], "budget_b": e["budget_b"]}})
    counts = ("answered", "fence_lines", "empty_code", "changed", "passing_after_f1", "official_passes_lost")
    return {"file": EXTRACTION, "sha256": sha, "rule": x["rule"], "status": x["exploratory"],
            "runs": {m: {k: v[k] for k in counts} for m, v in x["runs"].items()}, "hypotheses": rows,
            "machine": {"cpu": x["provenance"]["cpu"], "platform": x["provenance"]["platform"],
                        "processes": x["evaluator"]["processes"]}}


def mean_cost(run: str, rows: list[dict], budget: int | None, prompt: bool = False) -> float:
    """Mean cost per answer at `budget`; with `prompt`, 2 x parameters x prompt tokens is added."""
    weights = 2 * PARAMETERS[WEIGHTS[run]]
    return statistics.fmean(cost(run, r, budget) + (weights * r["prompt_tokens"] if prompt else 0) for r in rows)


def exact_budget(run: str, rows: list[dict], target: float) -> int:
    """The integer output budget whose mean cost (output tokens only) is nearest `target`; the smaller one on a
    tie, the longest answer when no budget reaches it."""
    lo, hi = 0, max(r["output_tokens"] for r in rows)
    if mean_cost(run, rows, hi) <= target:
        return hi
    while lo < hi:  # the smallest budget whose mean cost reaches the target (mean cost grows with the budget)
        mid = (lo + hi) // 2
        lo, hi = (mid + 1, hi) if mean_cost(run, rows, mid) < target else (lo, mid)
    below = max(lo - 1, 0)
    return below if target - mean_cost(run, rows, below) <= mean_cost(run, rows, lo) - target else lo


def at_budgets(a: str, a_runs: dict, b_runs: dict, ids: list[str], ba: int | None, bb: int | None,
               prompt: bool) -> dict[str, Any]:
    """Pass-at-budget difference (pp) at one budget pair, with the platform-clustered t, and the pair's costs."""
    d = [int(passes_within(a_runs[t], ba)) - int(passes_within(b_runs[t], bb)) for t in ids]
    ca = mean_cost(a, [a_runs[t] for t in ids], ba, prompt)
    cb = mean_cost(BIELIK, [b_runs[t] for t in ids], bb, prompt)
    return {"budget_a": ba, "budget_b": bb, "mean_cost_a": ca, "mean_cost_b": cb, "cost_ratio": ca / cb,
            **paired(d), "platform": clustered(d, [a_runs[t] for t in ids])["platform"]}


def exploratory_cost(runs: dict, f1: tuple | None) -> list[dict[str, Any]] | None:
    """Exploratory, added after the results (the method refutation's readings of L3; not a protocol test):
    - `exact cost`: LFM3-1.7B's budget set to the integer whose mean cost equals Bielik's at its L3 budget as
      nearly as an integer allows, instead of the nearest of the three protocol budgets;
    - `prompt counted`: the protocol's nearest-pair rule over the nine budget pairs with the prompt in the cost.
    Each on both LFM3-1.7B runs, with the official grades and, when extraction-f1.json exists, after rule F1."""
    if runs[BIELIK] is None:
        return None
    out = []
    for lfm in (LFM, CONTROL_RUN):
        if runs[lfm] is None:
            continue
        ids, _ = pair(runs[lfm], runs[BIELIK])
        if not ids:
            continue
        a_rows, b_rows = [runs[lfm][t] for t in ids], [runs[BIELIK][t] for t in ids]
        bb = equal_cost(lfm, BIELIK, runs[lfm], runs[BIELIK], ids)["budget_b"]
        exact = exact_budget(lfm, a_rows, mean_cost(BIELIK, b_rows, bb))
        with_prompt = min(((ba, bp) for ba in BUDGETS for bp in BUDGETS), key=lambda x: abs(math.log(
            mean_cost(lfm, a_rows, x[0], True) / mean_cost(BIELIK, b_rows, x[1], True))))  # first on a tie
        grades = [("official", runs)] + ([("after F1", f1[2])] if f1 else [])
        for reading_, (ba, bp, prompt) in (("exact cost", (exact, bb, False)),
                                           ("prompt counted", (*with_prompt, True))):
            for name, rs in grades:
                out.append({"reading": reading_, "run": lfm, "grades": name,
                            **at_budgets(lfm, rs[lfm], rs[BIELIK], ids, ba, bp, prompt)})
    return out


def fmt(x: float | None, spec: str) -> str:
    return "" if x is None else format(x, spec)


def value_se(r: dict) -> str:
    return "" if r.get("value") is None else f"{r['value']:+.2f} ± {fmt(r['se'], '.2f')}"


def budget(b: int | None) -> str:
    return "none" if b is None else str(b)


def clustered_table(rows: list[dict]) -> list[str]:
    """L1 and L3 with the SE over problems next to the clustered ones (descriptive)."""
    lines = []
    for r in rows:
        if r["id"] not in ("L1", "L3") or not r.get("clustered"):
            continue
        if not lines:
            lines = ["", "Clustered SE (descriptive): the same difference, SE from the spread between clusters, t read "
                     "at df = k − 1:", "",
                     "| hypothesis | SE from | k (clusters) or n | value ± SE (pp) | z or t | df | p | verdict |",
                     "|---|---|---|---|---|---|---|---|"]
        lines.append(f"| {r['id']} | problems (paired) | {r['n']} | {value_se(r)} | z = {fmt(r['z'], '+.2f')} | | "
                     f"{fmt(r['p'], '.3g')} | {r['verdict']} |")
        for name, c in r["clustered"].items():
            lines.append(f"| {r['id']} | {name} | {c['k']} | {value_se(c)} | t = {fmt(c['t'], '+.2f')} | {c['df']} | "
                         f"{fmt(c['p'], '.3g')} | {c['verdict']} |")
    return lines


def hypotheses_table(rows: list[dict]) -> list[str]:
    out = ["| hypothesis | measure | value ± SE (pp) | z | Holm p | verdict | after Holm | outcome | n |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        measure = r.get("measure", "")
        if r["outcome"] == "not run":
            out.append(f"| {r['id']} | | | | | not run | not run | not run (missing: {', '.join(r['missing'])}) | |")
            continue
        if r["id"] == "L2":
            weak = r["sign_not_established"]
            measure += f": {r['signs']}" + (f" (sign not established: {', '.join(weak)})" if weak else "")
        if r["id"] == "L3" and "mean_cost_a" in r:
            measure += (f" (LFM3 B = {budget(r['budget_a'])}, Bielik B = {budget(r['budget_b'])}; "
                        f"mean cost {r['mean_cost_a']:.3g} vs {r['mean_cost_b']:.3g} FLOPs)")
        n = f"{r['n']} (excluded {r['excluded']['total']})"
        out.append(f"| {r['id']} | {measure} | {value_se(r)} | {fmt(r['z'], '+.2f')} | {fmt(r['p_holm'], '.3g')} | "
                   f"{r['verdict']} | {r['verdict_holm']} | {r['outcome']} | {n} |")
        if r["id"] == "L2":
            for lvl, x in r["per_difficulty"].items():
                note = " (sign not established)" if lvl in r["sign_not_established"] else ""
                out.append(f"| L2 {lvl} | pass@1 difference, {lvl}{note} | {value_se(x)} | {fmt(x['z'], '+.2f')} | "
                           f"| {x['verdict']} | | | {x['n']} |")
    return out


def extraction_section(a: dict) -> list[str]:
    out = ["", "Code extraction: answered problems whose extracted code is empty (LiveCodeBench takes the lines "
           "between the last two fence lines; fewer than two give empty code, graded as a fail):", "",
           "| run | answered | empty code |", "|---|---|---|"]
    out += [f"| {m} | {x['answered']} | {x['empty_code']} |" for m, x in a["extraction"].items()]
    x = a["exploratory_extraction"]
    if not x:
        return out
    m = x["machine"]
    out += ["", f"Exploratory ({x['status']}): every answer re-extracted with rule "
            f"{x['rule']}; "
            "the answers whose code changes are graded again with LiveCodeBench's evaluator on the machine that ran "
            f"extraction.py ({m['cpu']}, {m['platform']}, {m['processes']} processes, from the file's provenance), "
            "not on the machines that scored the official runs (results/<model-id>.json, provenance.scoring); "
            f"results/{x['file']}.", "",
            "| run | answered | empty code | changed by F1 | of these passing | official passes lost |",
            "|---|---|---|---|---|---|"]
    out += [f"| {m} | {r['answered']} | {r['empty_code']} | {r['changed']} | {r['passing_after_f1']} | "
            f"{r['official_passes_lost']} |" for m, r in x["runs"].items()]
    official = {(a["verdict_run"], h["id"]): h for h in a["hypotheses"]}
    if a["other_run"]:
        official |= {(a["other_run"]["run"], h["id"]): h for h in a["other_run"]["hypotheses"]}
    out += ["", "| hypothesis | LFM3-1.7B run | official value ± SE (pp) | z | verdict | after F1 value ± SE (pp) | "
            "z | verdict | n |", "|---|---|---|---|---|---|---|---|---|"]
    for r in x["hypotheses"]:
        for hid in ("L1", "L3"):
            o, f = official[(r["run"], hid)], r[hid]
            out.append(f"| {hid} | {r['run']} | {value_se(o)} | {fmt(o['z'], '+.2f')} | {o['verdict']} | "
                       f"{value_se(f)} | {fmt(f['z'], '+.2f')} | {f['verdict']} | {f['n']} |")
    return out


def cost_section(a: dict) -> list[str]:
    rows = a["exploratory_cost"]
    if not rows:
        return []
    out = ["", "Exploratory, added after the results (the method refutation's readings of L3; not a protocol test): "
           "`exact cost` sets LFM3-1.7B's budget to the integer whose mean cost (output tokens) is nearest Bielik's "
           "at its L3 budget, instead of the nearest of the protocol's three budgets; `prompt counted` applies the "
           "protocol's nearest-pair rule with the prompt tokens in the cost. L3 under PROTOCOL.md stays as in the "
           "reading line above; these rows do not change it.", "",
           "| reading | LFM3-1.7B run | grades | LFM3 B | Bielik B | mean cost LFM3 vs Bielik (FLOPs) | cost ratio "
           "LFM3/Bielik | value ± SE (pp) | z | verdict | platform t | df | p | verdict | n |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        c = r["platform"]
        out.append(f"| {r['reading']} | {r['run']} | {r['grades']} | {budget(r['budget_a'])} | {budget(r['budget_b'])} "
                   f"| {r['mean_cost_a']:.3g} vs {r['mean_cost_b']:.3g} | {r['cost_ratio']:.3f} | {value_se(r)} | "
                   f"{fmt(r['z'], '+.2f')} | {r['verdict']} | {fmt(c['t'], '+.2f')} | {c['df']} | {fmt(c['p'], '.3g')} "
                   f"| {c['verdict']} | {r['n']} |")
    return out


def report(a: dict) -> str:
    out = []
    c = a["control"]
    if c["status"] in ("passed", "failed"):
        out.append(f"control: LFM3-1.7B ({c['run']}) {c['score']:.2f} ± {c['stderr']:.2f} vs card {c['card']}, "
                   f"z = {c['z']:+.2f}: {c['status']}")
        if c["status"] == "failed":
            out.append("control failed: the setup is the suspect; no hypothesis is read until the gap is explained")
    else:
        out.append(f"control: {c['status']}")
    d = c.get("descriptive")
    if d and d.get("z") is not None:
        out.append(f"descriptive, not tested: LFM3-1.7B ({d['run']}, the verdict run of L1-L3) {d['score']:.2f} ± "
                   f"{d['stderr']:.2f} vs card {d['card']}, z = {d['z']:+.2f}")
    out += ["", f"L1-L3 on {a['verdict_run']}, the verdict run:", ""] + hypotheses_table(a["hypotheses"])
    out += clustered_table(a["hypotheses"])
    other = a["other_run"]
    if other:
        out += ["", f"L1-L3 on {other['run']}, {other['role']}:", ""] + hypotheses_table(other["hypotheses"])
        out += clustered_table(other["hypotheses"])
    out += ["", "Reading:", ""] + [f"- {r['text']}" for r in a["reading"]]
    out += ["", "Descriptive (not tested), each LFM3-1.7B run minus each model:", "",
            "| run | model | measure | value ± SE (pp) | z | verdict | n | excluded |",
            "|---|---|---|---|---|---|---|---|"]
    for d in a["descriptive"]:
        if d["status"] == "not run":
            out.append(f"| {d['a']} | {d['b']} | not run (missing: {', '.join(d['missing'])}) | | | | | |")
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
            out.append(f"| {d['a']} | {d['b']} | {name} | {value_se(r)} | {fmt(r['z'], '+.2f')} | {r['verdict']} | "
                       f"{r['n']} | {ex} |")
    out += extraction_section(a)
    out += cost_section(a)
    out.append("")
    out += [f"deviation: {x}" for x in a["deviations"]]
    return "\n".join(out)


def main(results: Path) -> None:
    a = analyse(results)
    print(report(a))
    results.mkdir(parents=True, exist_ok=True)
    (results / "hypotheses.json").write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")
    provenance.record(results, ["hypotheses.json"], "compare.py")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results")
