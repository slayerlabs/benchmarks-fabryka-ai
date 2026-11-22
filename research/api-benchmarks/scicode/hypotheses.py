"""PROTOCOL.md control K1 and hypotheses K2, K3, on the primary setting (with background).

Usage: python3 hypotheses.py [results-dir] [--group <other hypotheses.json>]
Reads <results-dir>/<model-id>.jsonl.gz of lfm3-1.7b, lfm3-1.7b-nothink and bielik-11b-v3.1 (sha256 checked
against <results-dir>/manifest.json), prints a Markdown table and writes <results-dir>/hypotheses.json.

Items are the 288 scored subproblems, y_i = 1 when the scorer passed it; all three models must have the same items.
Every SE is clustered by problem (summarize.clustered_se: CR1, 65 clusters on the test split).

- K1: z = (p_LFM3 - 0.2847) / SE_cl(p_LFM3); passed when |z| <= 2. When it fails, K2 and K3 are computed but
  marked `read: false` (PROTOCOL.md: no hypothesis is read until the gap is explained in an amendment).
- K2: z = (p_Bielik - 0.1632) / max(SE_cl(p_Bielik), sqrt(0.1632 * 0.8368 / 288)).
- K3: d_i = off_i - on_i / 2 - B_i / 2, D = mean(d), z = D / SE_cl(d). Read only when the lead is clear:
  on_i - B_i has mean > 0 and z = mean / SE_cl >= 3; otherwise "precondition not met" and no p.
- Raw outcome from z: supported when z <= -2, refuted when z >= 2, otherwise undetermined.
- Holm over the four tests of the Coding group (K2, K3 here and in livecodebench-pro-25q2), m = 4 always: each test
  has p_support = Phi(z) and p_refute = 1 - Phi(z) (one-sided); Holm runs separately over the four p_support and
  the four p_refute; a test without p (not run, precondition not met, or the other benchmark's file not given)
  enters with p = 1. Verdict: supported (refuted) "clear" when its Holm p_support (p_refute) <= Phi(-3), "likely"
  when <= Phi(-2), otherwise undetermined. `--group` reads the other benchmark's `group_tests` (same keys as ours:
  benchmark, id, z, p_support, p_refute, outcome_raw), agreed with the LiveCodeBench Pro 25Q2 harness.
The same statistics without background are printed as descriptive rows, not tested.
"""

import gzip
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any

import provenance
from summarize import clustered_se

HERE = Path(__file__).parent
BENCHMARK = "scicode"
LFM, NOTHINK, BIELIK = "lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1"
CARD_LFM = 0.2847  # PROTOCOL.md, K1: LFM3-1.7B on its card
WEAKEST_CARD = 0.1632  # PROTOCOL.md, K2: LFM2.5-2.6B, the weakest model on the card
N_STEPS = 288
GROUP_M = 4  # PROTOCOL.md: K2 and K3 here and in LiveCodeBench Pro 25Q2
PRIMARY, SECONDARY = "with_background", "without_background"


def phi(z: float) -> float:
    return 0.5 * math.erfc(-z / math.sqrt(2))


P_CLEAR, P_LIKELY = phi(-3), phi(-2)


def load(results: Path, model: str) -> dict[str, dict[str, Any]] | None:
    path = results / f"{model}.jsonl.gz"
    if not path.is_file():
        return None
    provenance.verify(results, [path.name], "hypotheses.py")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def items(runs: dict[str, dict | None], setting: str) -> tuple[list[str], list[str]] | None:
    """Task ids of `setting` (sorted by problem and step) and their problems; None when a model is missing.
    Every present model must have exactly the same items."""
    present = {m: r for m, r in runs.items() if r is not None}
    if len(present) != len(runs):
        return None
    sets = {m: {t for t, x in r.items() if x["setting"] == setting} for m, r in present.items()}
    first = next(iter(sets.values()))
    if any(s != first for s in sets.values()):
        sys.exit(f"hypotheses.py: the models do not have the same {setting} items: "
                 f"{ {m: len(s) for m, s in sets.items()} }")
    any_run = next(iter(present.values()))
    ids = sorted(first, key=lambda t: (int(any_run[t]["problem_id"]), int(any_run[t]["step"])))
    return ids, [any_run[t]["problem_id"] for t in ids]


def y(run: dict[str, dict], ids: list[str]) -> list[float]:
    return [float(run[t]["score"]) for t in ids]


def mean_z(d: list[float], clusters: list[str], null: float = 0.0, se_floor: float = 0.0) -> dict[str, Any]:
    """Mean of d, its clustered SE (floored at `se_floor`), and z against `null`."""
    mean = statistics.fmean(d)
    se_cl = clustered_se(d, clusters)
    se = None if se_cl is None else max(se_cl, se_floor)
    z = None if not se else (mean - null) / se
    return {"value": mean, "se_clustered": se_cl, "se": se, "z": z, "n": len(d), "clusters": len(set(clusters))}


def raw_outcome(z: float | None) -> str:
    if z is None:
        return "undetermined"
    return "supported" if z <= -2 else "refuted" if z >= 2 else "undetermined"


def one_sided(z: float | None) -> tuple[float | None, float | None]:
    return (None, None) if z is None else (phi(z), 1 - phi(z))


def control(runs: dict, ids_clusters: tuple | None) -> dict[str, Any]:
    if runs[LFM] is None:
        return {"id": "K1", "status": "not run", "card": 100 * CARD_LFM}
    ids, clusters = ids_clusters if ids_clusters else items({LFM: runs[LFM]}, PRIMARY)
    s = mean_z(y(runs[LFM], ids), clusters, null=CARD_LFM)
    status = "undetermined" if s["z"] is None else "passed" if abs(s["z"]) <= 2 else "failed"
    return {"id": "K1", "status": status, "card": 100 * CARD_LFM, "score": 100 * s["value"],
            "se_clustered": None if s["se"] is None else 100 * s["se"], "z": s["z"], "n": s["n"],
            "clusters": s["clusters"]}


def k2(runs: dict, ids: list[str], clusters: list[str]) -> dict[str, Any]:
    floor = math.sqrt(WEAKEST_CARD * (1 - WEAKEST_CARD) / N_STEPS)
    s = mean_z(y(runs[BIELIK], ids), clusters, null=WEAKEST_CARD, se_floor=floor)
    return {"measure": "Bielik pass rate minus 16.32", "value": 100 * (s["value"] - WEAKEST_CARD),
            "score": 100 * s["value"], "se": None if s["se"] is None else 100 * s["se"],
            "se_clustered": None if s["se_clustered"] is None else 100 * s["se_clustered"],
            "se_binomial_floor": 100 * floor, "z": s["z"], "n": s["n"]}


def k3(runs: dict, ids: list[str], clusters: list[str]) -> dict[str, Any]:
    on, off, b = y(runs[LFM], ids), y(runs[NOTHINK], ids), y(runs[BIELIK], ids)
    lead = mean_z([a - c for a, c in zip(on, b)], clusters)
    d = mean_z([o - a / 2 - c / 2 for o, a, c in zip(off, on, b)], clusters)
    met = lead["z"] is not None and lead["value"] > 0 and lead["z"] >= 3
    return {"measure": "D = (off - B) - (on - B) / 2, paired by subproblem",
            "value": 100 * d["value"], "se": None if d["se"] is None else 100 * d["se"],
            "z": d["z"] if met else None, "z_computed": d["z"], "n": d["n"],
            "precondition": {"lead_on_minus_bielik": 100 * lead["value"],
                             "se": None if lead["se"] is None else 100 * lead["se"], "z": lead["z"], "met": met}}


def holm(ps: list[float | None], m: int = GROUP_M) -> list[float]:
    """Holm step-down adjusted p over a family of m; a missing p counts as 1."""
    filled = [1.0 if p is None else p for p in ps] + [1.0] * (m - len(ps))
    order = sorted(range(len(filled)), key=lambda i: filled[i])
    adjusted, running = [0.0] * len(filled), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * filled[i]))
        adjusted[i] = running
    return adjusted[:len(ps)]


def verdict(p_support: float, p_refute: float) -> str:
    for p, side in ((p_support, "supported"), (p_refute, "refuted")):
        if p <= P_CLEAR:
            return f"{side} (clear)"
        if p <= P_LIKELY:
            return f"{side} (likely)"
    return "undetermined"


def group_tests_from(path: Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    other = json.loads(path.read_text(encoding="utf-8"))["group_tests"]
    tests = [t for t in other if t["benchmark"] != BENCHMARK]
    if len(tests) != GROUP_M - 2 or {t["id"] for t in tests} != {"K2", "K3"}:
        sys.exit(f"hypotheses.py: {path} must hold K2 and K3 of one other benchmark in group_tests, has {tests}")
    return tests


def analyse(results: Path, group: Path | None = None) -> dict[str, Any]:
    runs = {m: load(results, m) for m in (LFM, NOTHINK, BIELIK)}
    primary = items(runs, PRIMARY)
    k1 = control(runs, primary)
    rows = []
    for hid, fn in (("K2", k2), ("K3", k3)):
        if primary is None:
            rows.append({"id": hid, "status": "not run", "missing": [m for m, r in runs.items() if r is None],
                         "z": None})
            continue
        row = {"id": hid, "status": "computed", **fn(runs, *primary)}
        if hid == "K3" and not row["precondition"]["met"]:
            row["status"] = "precondition not met"
        rows.append(row)
    own = []
    for row in rows:
        p_sup, p_ref = one_sided(row["z"])
        row["p_support"], row["p_refute"] = p_sup, p_ref
        row["outcome_raw"] = row["status"] if row["status"] != "computed" else raw_outcome(row["z"])
        own.append({"benchmark": BENCHMARK, "id": row["id"], "z": row["z"], "p_support": p_sup, "p_refute": p_ref,
                    "outcome_raw": row["outcome_raw"]})
    others = group_tests_from(group)
    family = own + others
    adj_sup = holm([t["p_support"] for t in family])
    adj_ref = holm([t["p_refute"] for t in family])
    for row, ps, pr in zip(rows, adj_sup, adj_ref):
        row["p_support_holm"], row["p_refute_holm"] = ps, pr
        row["verdict_holm"] = row["status"] if row["status"] != "computed" else verdict(ps, pr)
        row["read"] = k1["status"] == "passed"
    descriptive = None
    secondary = items(runs, SECONDARY)
    if secondary is not None:
        ids, clusters = secondary
        descriptive = {"setting": SECONDARY, "note": "descriptive, not tested",
                       "K1_form": {k: v for k, v in control({LFM: runs[LFM]}, secondary).items() if k != "id"},
                       "K2_form": k2(runs, ids, clusters), "K3_form": k3(runs, ids, clusters)}
    return {"benchmark": BENCHMARK, "protocol": "PROTOCOL.md", "setting": PRIMARY, "control": k1,
            "hypotheses": rows, "group_tests": own,
            "holm": {"m": GROUP_M, "family": [{k: t[k] for k in ("benchmark", "id", "p_support", "p_refute")}
                                              for t in family],
                     "other_benchmark_file": str(group) if group else None,
                     "missing_counted_as_p_1": GROUP_M - len(family) + sum(1 for t in family if t["p_support"] is None)},
            "descriptive": descriptive}


def fmt(x: float | None, spec: str) -> str:
    return "" if x is None else format(x, spec)


def report(a: dict) -> str:
    c = a["control"]
    out = [f"K1 control: LFM3-1.7B {fmt(c.get('score'), '.2f')} ± {fmt(c.get('se_clustered'), '.2f')} (clustered) "
           f"vs card {c['card']:.2f}, z = {fmt(c.get('z'), '+.2f')}: {c['status']}", "",
           "| test | value (pp) | SE (pp) | z | Holm p support | Holm p refute | raw | verdict after Holm | read |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in a["hypotheses"]:
        out.append(f"| {r['id']} | {fmt(r.get('value'), '+.2f')} | {fmt(r.get('se'), '.2f')} | "
                   f"{fmt(r.get('z'), '+.2f')} | {fmt(r.get('p_support_holm'), '.3g')} | "
                   f"{fmt(r.get('p_refute_holm'), '.3g')} | {r['outcome_raw']} | {r['verdict_holm']} | {r['read']} |")
    out.append(f"Holm m = {a['holm']['m']}, family: " + ", ".join(f"{t['benchmark']} {t['id']}"
                                                                    for t in a["holm"]["family"]))
    return "\n".join(out)


def main(argv: list[str]) -> None:
    group = None
    if "--group" in argv:
        i = argv.index("--group")
        group = Path(argv[i + 1])
        del argv[i:i + 2]
    results = Path(argv[0]) if argv else HERE / "results"
    a = analyse(results, group)
    print(report(a))
    (results / "hypotheses.json").write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
