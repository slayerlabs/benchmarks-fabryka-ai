"""PROTOCOL.md control K1 and hypotheses K2, K3, with Holm over the Coding group's four tests.

Usage: python3 compare.py [results-dir] [--group <other benchmark's hypotheses.json>]
Reads <results-dir>/<model-id>.jsonl.gz of lfm3-1.7b, lfm3-1.7b-nothink and bielik-11b-v3.1, prints a Markdown
summary and writes <results-dir>/hypotheses.json. Every file read must have the sha256 summarize.py recorded in
<results-dir>/manifest.json.

All three use the headline scoring: x_i = 1 when problem i is accepted, else 0 (a missing test zip or a persistent
error counts as 0), over all n = 167 problems; the three runs must cover the same problems.
- K1: p_on = mean(x_on), SE = sqrt(p(1-p)/n); z = (p_on - 0.3174) / SE; passed when |z| <= 2. Until it passes, the
  hypotheses are computed but marked not read.
- K2: z = (p_B - 0.1916) / SE, SE = max(sqrt(p_B(1-p_B)/n), sqrt(0.1916 * 0.8084 / n)).
- K3: d_i = off_i - on_i/2 - B_i/2, D = mean(d), SE = sd(d)/sqrt(n) (sd with n - 1), z = D / SE. Read only if the
  lead on - B is clear: paired l_i = on_i - B_i, z_lead = mean(l) / (sd(l)/sqrt(n)) >= 3 and mean(l) > 0;
  otherwise "precondition not met" and no p.
- Raw outcome: supported when z <= -2, refuted when z >= 2, otherwise undetermined; raw strength |z| >= 3 clear,
  2-3 likely, < 2 noise.
- One-sided p from z: p_support = Phi(z) (toward supported), p_refute = 1 - Phi(z). Holm with m = 4 over the
  group (K2 and K3 here and in SciCode, read from `--group`), separately for the p_support and the p_refute family;
  a test without a p (not run, precondition not met, or the other benchmark's file absent) counts in m with p = 1.
  After Holm: supported (clear when Holm p_support <= Phi(-3), likely when <= Phi(-2)), refuted the same way with
  p_refute, else undetermined.
`group_tests` in hypotheses.json carries this benchmark's K2 and K3 (z, p_support, p_refute, raw outcome) for the
other benchmark's script.
"""

import gzip
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Any

import provenance

HERE = Path(__file__).parent
BENCHMARK_ID = "livecodebench-pro-25q2"
ON, OFF, BIELIK = "lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1"
CARD_LFM3 = 0.3174  # PROTOCOL.md, Sources: LFM3-1.7B card, 31.74
CARD_WEAKEST = 0.1916  # LFM2.5-2.6B, the weakest model on the card, 19.16
GROUP_SIZE = 4  # K2 and K3 here and in SciCode (#297)


def phi(z: float) -> float:
    return 0.5 * math.erfc(-z / math.sqrt(2))


P_CLEAR, P_LIKELY = phi(-3), phi(-2)


def load(results: Path, model: str) -> dict[str, int] | None:
    """problem -> 1 if accepted else 0, from <model>.jsonl.gz; None when the file is absent."""
    path = results / f"{model}.jsonl.gz"
    if not path.is_file():
        return None
    provenance.verify(results, [path.name], "compare.py")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {r["task_id"]: int(bool(r["accepted"])) for r in map(json.loads, f)}


def difficulties(results: Path, model: str) -> dict[str, str]:
    with gzip.open(results / f"{model}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["task_id"]: r["difficulty"] for r in map(json.loads, f)}


def raw_outcome(z: float | None) -> str:
    if z is None:
        return "undetermined"
    return "supported" if z <= -2 else "refuted" if z >= 2 else "undetermined"


def strength(z: float | None) -> str:
    if z is None:
        return "undecidable"
    return "clear" if abs(z) >= 3 else "likely" if abs(z) >= 2 else "noise"


def ps(z: float | None) -> tuple[float | None, float | None]:
    return (None, None) if z is None else (phi(z), 1 - phi(z))


def control(on: dict[str, int] | None) -> dict[str, Any]:
    if on is None:
        return {"status": "not run", "card": 100 * CARD_LFM3}
    n = len(on)
    p = sum(on.values()) / n
    se = math.sqrt(p * (1 - p) / n)
    z = (p - CARD_LFM3) / se if se > 0 else None
    status = "undecidable" if z is None else "passed" if abs(z) <= 2 else "failed"
    return {"status": status, "card": 100 * CARD_LFM3, "score": 100 * p, "stderr": 100 * se, "z": z, "n": n}


def k2(bielik: dict[str, int] | None) -> dict[str, Any]:
    if bielik is None:
        return {"id": "K2", "status": "not run", "z": None}
    n = len(bielik)
    p = sum(bielik.values()) / n
    se = max(math.sqrt(p * (1 - p) / n), math.sqrt(CARD_WEAKEST * (1 - CARD_WEAKEST) / n))
    z = (p - CARD_WEAKEST) / se
    return {"id": "K2", "status": "ok", "value": 100 * p, "reference": 100 * CARD_WEAKEST, "se": 100 * se, "z": z,
            "n": n}


def paired_z(d: list[float]) -> tuple[float, float, float | None]:
    """mean, SE = sd/sqrt(n) and z (None when SE is 0)."""
    mean = statistics.fmean(d)
    se = statistics.stdev(d) / math.sqrt(len(d))
    return mean, se, (mean / se if se > 0 else None)


def k3(on: dict[str, int] | None, off: dict[str, int] | None, bielik: dict[str, int] | None) -> dict[str, Any]:
    if on is None or off is None or bielik is None:
        return {"id": "K3", "status": "not run", "z": None,
                "missing": [m for m, r in ((ON, on), (OFF, off), (BIELIK, bielik)) if r is None]}
    if not (set(on) == set(off) == set(bielik)):
        sys.exit("compare.py: the three runs cover different problems; K3 pairs them by problem")
    ids = sorted(on)
    lead_mean, lead_se, lead_z = paired_z([on[t] - bielik[t] for t in ids])
    lead = {"value": 100 * lead_mean, "se": 100 * lead_se, "z": lead_z}
    mean, se, z = paired_z([off[t] - on[t] / 2 - bielik[t] / 2 for t in ids])
    record = {"id": "K3", "value": 100 * mean, "se": 100 * se, "n": len(ids), "lead": lead,
              "on": 100 * statistics.fmean(on[t] for t in ids), "off": 100 * statistics.fmean(off[t] for t in ids),
              "bielik": 100 * statistics.fmean(bielik[t] for t in ids)}
    if lead_z is None or lead_mean <= 0 or lead_z < 3:
        return {**record, "status": "precondition not met", "z_descriptive": z, "z": None}
    return {**record, "status": "ok", "z": z}


def contest(problem_id: str) -> str:
    """Codeforces contest of a problem id ("2084" of "2084G1")."""
    return re.match(r"\d+", problem_id).group(0)


def binom_cdf(k: int, n: int) -> float:
    """P(X <= k) for X ~ Binomial(n, 1/2)."""
    return sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n


def k3_robustness(on: dict[str, int], off: dict[str, int], bielik: dict[str, int],
                  difficulty: dict[str, str]) -> dict[str, Any]:
    """DESCRIPTIVE, added after the results (PROTOCOL.md Amendment 1); no verdict reads it. K3's d_i
    (off - on/2 - B/2) with problems of one contest treated as one cluster: SE clustered by contest
    sqrt(G/(G-1) * sum_g (sum_{i in g} (d_i - D))^2) / n and z = D / SE; a sign test over contests (contests with
    sum d > 0 against sum d < 0, one-sided binomial p in the direction of D's sign); D, SE and z per difficulty."""
    ids = sorted(on)
    d = {t: off[t] - on[t] / 2 - bielik[t] / 2 for t in ids}
    mean = statistics.fmean(d.values())
    sums: dict[str, float] = {}
    resid: dict[str, float] = {}
    for t in ids:
        sums[contest(t)] = sums.get(contest(t), 0.0) + d[t]
        resid[contest(t)] = resid.get(contest(t), 0.0) + d[t] - mean
    g = len(resid)
    se = math.sqrt(g / (g - 1) * sum(r * r for r in resid.values())) / len(ids)
    pos, neg = sum(1 for s in sums.values() if s > 0), sum(1 for s in sums.values() if s < 0)
    levels = {}
    order = ("easy", "medium", "hard")
    for level in sorted(set(difficulty.values()), key=lambda x: (order.index(x) if x in order else len(order), x)):
        sub = [d[t] for t in ids if difficulty[t] == level]
        m, s, z = paired_z(sub) if len(sub) > 1 else (statistics.fmean(sub), 0.0, None)
        levels[level] = {"value": 100 * m, "se": 100 * s, "z": z, "n": len(sub),
                         "accepted": {"on": sum(on[t] for t in ids if difficulty[t] == level),
                                      "off": sum(off[t] for t in ids if difficulty[t] == level),
                                      "bielik": sum(bielik[t] for t in ids if difficulty[t] == level)}}
    return {"descriptive": True,
            "clustered_by_contest": {"contests": g, "se": 100 * se, "z": mean / se if se > 0 else None},
            "sign_test_contests": {"positive": pos, "negative": neg, "zero": g - pos - neg,
                                   "p_one_sided": binom_cdf(min(pos, neg), pos + neg)},
            "per_difficulty": levels}


def holm(p: list[float | None], m: int) -> list[float | None]:
    """Holm step-down adjusted p over a family of m; a missing p counts as p = 1 (ranked last)."""
    filled = [1.0 if x is None else x for x in p] + [1.0] * (m - len(p))
    if len(filled) != m:
        raise ValueError(f"{len(p)} tests in a family of {m}")
    order = sorted(range(m), key=lambda i: filled[i])
    adjusted, running = [0.0] * m, 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * filled[i]))
        adjusted[i] = running
    return [None if x is None else adjusted[i] for i, x in enumerate(p)]


def holm_verdict(p_support: float | None, p_refute: float | None) -> str:
    for p, word in ((p_support, "supported"), (p_refute, "refuted")):
        if p is not None and p <= P_LIKELY:
            return f"{word} ({'clear' if p <= P_CLEAR else 'likely'})"
    return "undetermined"


def group_test(h: dict[str, Any]) -> dict[str, Any]:
    p_support, p_refute = ps(h["z"])
    outcome = h["status"] if h["status"] != "ok" else raw_outcome(h["z"])
    return {"benchmark": BENCHMARK_ID, "id": h["id"], "z": h["z"], "p_support": p_support, "p_refute": p_refute,
            "outcome_raw": outcome}


def other_tests(group_file: Path | None) -> tuple[list[dict[str, Any]], str | None]:
    """The other benchmark's K2 and K3 from its hypotheses.json (`group_tests`), or two placeholders with p = 1."""
    if group_file is None or not group_file.is_file():
        note = (f"{group_file} not found; " if group_file else "") + \
            "the other benchmark's two tests count in Holm's m = 4 with p = 1"
        return [{"benchmark": "scicode", "id": i, "z": None, "p_support": None, "p_refute": None,
                 "outcome_raw": "not available"} for i in ("K2", "K3")], note
    tests = [t for t in json.loads(group_file.read_text(encoding="utf-8"))["group_tests"]
             if t["benchmark"] != BENCHMARK_ID]
    if len(tests) != GROUP_SIZE - 2:
        sys.exit(f"compare.py: {group_file} has {len(tests)} group tests of another benchmark, expected "
                 f"{GROUP_SIZE - 2}")
    return tests, None


def analyse(results: Path, group_file: Path | None = None) -> dict[str, Any]:
    on, off, bielik = load(results, ON), load(results, OFF), load(results, BIELIK)
    c = control(on)
    ours = [k2(bielik), k3(on, off, bielik)]
    mine = [group_test(h) for h in ours]
    others, note = other_tests(group_file)
    family = mine + others
    adj_support = holm([t["p_support"] for t in family], GROUP_SIZE)
    adj_refute = holm([t["p_refute"] for t in family], GROUP_SIZE)
    holm_rows = [{**t, "p_support_holm": s, "p_refute_holm": r, "verdict_holm": holm_verdict(s, r)}
                 for t, s, r in zip(family, adj_support, adj_refute)]
    readable = c["status"] == "passed"
    hypotheses = []
    for h, row in zip(ours, holm_rows):
        verdict = row["verdict_holm"] if h["status"] == "ok" else h["status"]
        hypotheses.append({**h, "outcome_raw": row["outcome_raw"], "strength_raw": strength(h["z"]),
                           "p_support": row["p_support"], "p_refute": row["p_refute"],
                           "p_support_holm": row["p_support_holm"], "p_refute_holm": row["p_refute_holm"],
                           "verdict_holm": verdict,
                           "read": readable and h["status"] == "ok"})
    notes = [note] if note else []
    if not readable:
        notes.append(f"control K1 {c['status']}: no hypothesis is read until it passes (PROTOCOL.md, Control)")
    robustness = (k3_robustness(on, off, bielik, difficulties(results, ON))
                  if on is not None and off is not None and bielik is not None else None)
    return {"benchmark": BENCHMARK_ID, "protocol": "PROTOCOL.md", "control": c, "hypotheses": hypotheses,
            "group_tests": mine, "holm": {"m": GROUP_SIZE, "family": holm_rows}, "notes": notes,
            "k3_robustness": robustness,
            "group_file": None if note else {"file": f"{group_file.parent.parent.name}/results/{group_file.name}",
                                             "sha256": provenance.sha256_file(group_file)}}


def fmt(x: float | None, spec: str) -> str:
    return "" if x is None else format(x, spec)


def report(a: dict[str, Any]) -> str:
    c = a["control"]
    lines = [f"K1 control: {c['status']}" + ("" if "z" not in c or c["z"] is None else
             f": LFM3-1.7B {c['score']:.2f} ± {c['stderr']:.2f} vs card {c['card']:.2f}, z = {c['z']:+.2f}"), "",
             "| test | value ± SE (pp) | z | raw | Holm p (support / refute) | after Holm (m = 4) | read |",
             "|---|---|---|---|---|---|---|"]
    for h in a["hypotheses"]:
        value = "" if h.get("value") is None else f"{h['value']:+.2f} ± {h['se']:.2f}"
        lines.append(f"| {h['id']} | {value} | {fmt(h['z'], '+.2f')} | {h['outcome_raw']} ({h['strength_raw']}) | "
                     f"{fmt(h['p_support_holm'], '.3g')} / {fmt(h['p_refute_holm'], '.3g')} | {h['verdict_holm']} | "
                     f"{'yes' if h['read'] else 'no'} |")
        if h["id"] == "K3" and "lead" in h:
            lead = h["lead"]
            lines.append(f"| K3 lead on − B (precondition z ≥ 3) | {lead['value']:+.2f} ± {lead['se']:.2f} | "
                         f"{fmt(lead['z'], '+.2f')} | | | | |")
    lines += ["", "Holm family:", ""]
    lines += [f"- {t['benchmark']} {t['id']}: " + (f"z {t['z']:+.2f}, {t['verdict_holm']}" if t["z"] is not None
                                                   else f"{t['outcome_raw']} (p = 1 in Holm)")
              for t in a["holm"]["family"]]
    lines += [f"note: {n}" for n in a["notes"]]
    r = a.get("k3_robustness")
    if r:
        cl, sign = r["clustered_by_contest"], r["sign_test_contests"]
        lines += ["", "K3 robustness (DESCRIPTIVE, added after the results; PROTOCOL.md Amendment 1):", "",
                  "| view | D ± SE (pp) | z | n |", "|---|---|---|---|",
                  f"| SE clustered by contest | {a['hypotheses'][1]['value']:+.2f} ± {cl['se']:.2f} | "
                  f"{fmt(cl['z'], '+.2f')} | {cl['contests']} contests |"]
        for level, x in r["per_difficulty"].items():
            acc = x["accepted"]
            lines.append(f"| {level} only (accepted on / off / Bielik: {acc['on']} / {acc['off']} / {acc['bielik']}) "
                         f"| {x['value']:+.2f} ± {x['se']:.2f} | {fmt(x['z'], '+.2f')} | {x['n']} |")
        lines += ["", f"Sign test over contests: {sign['positive']} with D > 0, {sign['negative']} with D < 0, "
                      f"{sign['zero']} with D = 0; one-sided binomial p = {sign['p_one_sided']:.2g}."]
    return "\n".join(lines)


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
    provenance.record(results, ["hypotheses.json"], "compare.py")


if __name__ == "__main__":
    main(sys.argv[1:])
