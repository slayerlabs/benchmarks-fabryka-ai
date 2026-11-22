"""PROTOCOL.md Amendment 4, thesis A1: is LFM3-1.7B's pass@1 with vLLM's sampling defaults from
generation_config.json (`lfm3-1.7b`: repetition_penalty 1.1, top_k 50) equivalent within 2 pt to the card's sampling
(`lfm3-1.7b-cardsampling`: repetition_penalty 1.0, no top-k limit)?

Usage: python3 ablation.py [results-dir]   (default: results/ next to this file)
Reads <results-dir>/<model-id>.json and .jsonl.gz of both runs (each must have the sha256 summarize.py recorded in
<results-dir>/manifest.json), prints a Markdown table and writes <results-dir>/ablation-a1.json and ablation-a1.md,
recording their sha256 in <results-dir>/manifest.json.

Δ = original minus ablation in percentage points, paired by problem over the problems both runs answered
(`status: ok`; the rest are counted). Per problem d = pass(original) - pass(ablation); Δ = mean(d), paired SE =
sd(d) / sqrt(n) (sample sd). Equivalent when the 90% CI Δ ± z(0.95) × SE lies inside (-2, +2) pt: two one-sided
tests at α = 0.05, normal approximation. McNemar's exact two-sided test on the discordant problems is descriptive.
Both runs must have the same protocol settings and differ only in repetition_penalty and top_k, as Amendment 4 says.
"""

import gzip
import json
import math
import statistics
import sys
from pathlib import Path
from statistics import NormalDist
from typing import Any

import provenance

HERE = Path(__file__).parent
ORIGINAL = "lfm3-1.7b"
ABLATION = "lfm3-1.7b-cardsampling"
MARGIN_PT = 2.0  # equivalence margin, percentage points
ALPHA = 0.05
Z = NormalDist().inv_cdf(1 - ALPHA)  # 1.645: the 90% CI of two one-sided tests at α = 0.05
CARD_SAMPLING_KEYS = ("repetition_penalty", "top_k")
EXPECTED_SAMPLING = {ORIGINAL: {"repetition_penalty": 1.1, "top_k": 50},
                     ABLATION: {"repetition_penalty": 1.0, "top_k": 0}}
SAME_SETTINGS = ("prompt_style", "temperature", "top_p", "seed", "max_tokens", "context", "trials", "scored_text",
                 "eval_timeout_s", "eval_processes")
CARD = 73.46  # PROTOCOL.md, Amendment 1


def load(results: Path, model: str) -> tuple[dict[str, Any], dict[str, dict]]:
    names = [f"{model}.json", f"{model}.jsonl.gz"]
    missing = [n for n in names if not (results / n).is_file()]
    if missing:
        sys.exit(f"ablation.py: {', '.join(missing)} not in {results}; run run.sh {model} (or copy its results)")
    provenance.verify(results, names, "ablation.py")
    with gzip.open(results / names[1], "rt", encoding="utf-8") as f:
        rows = {r["task_id"]: r for r in map(json.loads, f)}
    return json.loads((results / names[0]).read_text(encoding="utf-8")), rows


def effective_sampling(settings: dict[str, Any]) -> dict[str, Any]:
    """The request's sampling over the server's defaults (a value in the request wins)."""
    defaults = settings.get("server_defaults")
    return {**(defaults if isinstance(defaults, dict) else {}), **settings.get("request_sampling", {})}


def check_settings(original: dict[str, Any], ablation: dict[str, Any]) -> None:
    """Stops unless the two runs differ only in the two sampling settings Amendment 4 changes."""
    so, sa = original["settings"], ablation["settings"]
    differ = [k for k in SAME_SETTINGS if so.get(k) != sa.get(k)]
    if differ:
        sys.exit(f"ablation.py: the runs differ in {differ}, which Amendment 4 keeps the same")
    eo, ea = effective_sampling(so), effective_sampling(sa)
    for model, eff in ((ORIGINAL, eo), (ABLATION, ea)):
        got = {k: eff.get(k) for k in CARD_SAMPLING_KEYS}
        if got != EXPECTED_SAMPLING[model]:
            sys.exit(f"ablation.py: {model} ran with {got}, Amendment 4 says {EXPECTED_SAMPLING[model]}")
    rest_o = {k: v for k, v in eo.items() if k not in CARD_SAMPLING_KEYS}
    rest_a = {k: v for k, v in ea.items() if k not in CARD_SAMPLING_KEYS}
    if rest_o != rest_a:
        sys.exit(f"ablation.py: the sampling differs beyond {CARD_SAMPLING_KEYS}: {rest_o} vs {rest_a}")


def paired_equivalence(d: list[int]) -> dict[str, Any]:
    """Δ = mean(d) in pp, paired SE, 90% CI and the two one-sided p values against the ±2 pt margin."""
    n = len(d)
    if n < 2:
        return {"n": n, "delta": None, "se": None, "ci90": None, "p_lower": None, "p_upper": None, "p_tost": None,
                "verdict": "undecidable"}
    delta = 100 * statistics.fmean(d)
    se = 100 * statistics.stdev(d) / math.sqrt(n)
    lo, hi = delta - Z * se, delta + Z * se
    if se > 0:
        p_lower = 1 - NormalDist().cdf((delta + MARGIN_PT) / se)  # H0: Δ <= -2
        p_upper = NormalDist().cdf((delta - MARGIN_PT) / se)  # H0: Δ >= +2
    else:
        p_lower, p_upper = float(delta <= -MARGIN_PT), float(delta >= MARGIN_PT)
    equivalent = -MARGIN_PT < lo and hi < MARGIN_PT
    return {"n": n, "delta": delta, "se": se, "ci90": [lo, hi], "p_lower": p_lower, "p_upper": p_upper,
            "p_tost": max(p_lower, p_upper), "verdict": "equivalent" if equivalent else "not shown equivalent"}


def mcnemar(b: int, c: int) -> float:
    """Exact two-sided McNemar p: 2 × P(X <= min(b, c)), X ~ Binomial(b + c, 1/2), at most 1."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def analyse(results: Path) -> dict[str, Any]:
    original, o_rows = load(results, ORIGINAL)
    ablation, a_rows = load(results, ABLATION)
    check_settings(original, ablation)

    def ok(r: dict) -> bool:
        return r["status"] == "ok" and r["pass"] is not None

    ids = sorted(set(o_rows) | set(a_rows))
    keep = [t for t in ids if t in o_rows and t in a_rows and ok(o_rows[t]) and ok(a_rows[t])]
    excluded = {"not_scored_original": sum(1 for t in ids if t in o_rows and not ok(o_rows[t])),
                "not_scored_ablation": sum(1 for t in ids if t in a_rows and not ok(a_rows[t])),
                "missing_original": sum(1 for t in ids if t not in o_rows),
                "missing_ablation": sum(1 for t in ids if t not in a_rows), "total": len(ids) - len(keep)}
    po = [bool(o_rows[t]["pass"]) for t in keep]
    pa = [bool(a_rows[t]["pass"]) for t in keep]
    b = sum(1 for x, y in zip(po, pa) if x and not y)  # passed only with the generation_config defaults
    c = sum(1 for x, y in zip(po, pa) if y and not x)  # passed only with the card's sampling
    eq = paired_equivalence([int(x) - int(y) for x, y in zip(po, pa)])
    if eq["verdict"] == "equivalent":
        consequence = (f"A1 holds: the original pass@1 {original['score']} stands and the gap named in Amendment 3 "
                       "is closed")
    elif eq["verdict"] == "undecidable":
        consequence = "A1 undecidable: fewer than 2 problems answered by both runs"
    else:
        consequence = (f"A1 not shown equivalent: both numbers are reported ({ORIGINAL} {original['score']}, "
                       f"{ABLATION} {ablation['score']}); the card-sampling one is the headline for comparisons "
                       f"with the card's {CARD}")
    return {
        "thesis": "A1 (PROTOCOL.md, Amendment 4): |pass@1(original) - pass@1(card sampling)| < 2 pt",
        "original": ORIGINAL, "ablation": ABLATION, "margin_pt": MARGIN_PT, "alpha": ALPHA, "z": Z,
        "sampling": {ORIGINAL: EXPECTED_SAMPLING[ORIGINAL], ABLATION: EXPECTED_SAMPLING[ABLATION]},
        "score": {ORIGINAL: original["score"], ABLATION: ablation["score"]},
        "paired_pass_at_1": {ORIGINAL: 100 * statistics.fmean(po) if po else None,
                             ABLATION: 100 * statistics.fmean(pa) if pa else None},
        "difference": "original minus ablation, pp",
        **eq,
        "mcnemar": {"only_original": b, "only_ablation": c, "p_exact": mcnemar(b, c), "descriptive": True},
        "excluded": excluded,
        "consequence": consequence,
        "inputs_sha256": {n: f["sha256"] for n, f in provenance.read_manifest(results)["files"].items()
                          if n.startswith((f"{ORIGINAL}.", f"{ABLATION}."))},
    }


def fmt(x: float | None, spec: str) -> str:
    return "" if x is None else format(x, spec)


def report(a: dict[str, Any]) -> str:
    ci = a["ci90"] or [None, None]
    m = a["mcnemar"]
    return "\n".join([
        "| run | repetition_penalty | top_k | pass@1 (file) | pass@1 (paired) |", "|---|---|---|---|---|",
        *(f"| {k} | {a['sampling'][k]['repetition_penalty']} | {a['sampling'][k]['top_k']} | {a['score'][k]} | "
          f"{fmt(a['paired_pass_at_1'][k], '.2f')} |" for k in (a["original"], a["ablation"])),
        "",
        "| Δ (original − ablation), pp | paired SE | 90% CI | TOST p | verdict | n | excluded |",
        "|---|---|---|---|---|---|---|",
        f"| {fmt(a['delta'], '+.2f')} | {fmt(a['se'], '.2f')} | [{fmt(ci[0], '+.2f')}, {fmt(ci[1], '+.2f')}] | "
        f"{fmt(a['p_tost'], '.3g')} | {a['verdict']} (margin ±{a['margin_pt']:g} pt) | {a['n']} | "
        f"{a['excluded']['total']} |",
        "",
        f"McNemar (descriptive): passed only with repetition_penalty 1.1 / top_k 50: {m['only_original']}; only with "
        f"the card's sampling: {m['only_ablation']}; exact two-sided p = {m['p_exact']:.3g}",
        "",
        a["consequence"],
    ])


def main(results: Path) -> None:
    a = analyse(results)
    text = report(a)
    print(text)
    (results / "ablation-a1.json").write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")
    (results / "ablation-a1.md").write_text(text + "\n", encoding="utf-8")
    provenance.record(results, ["ablation-a1.json", "ablation-a1.md"], "ablation.py")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results")
