"""tau3-bench: turn the saved simulations into results/*.json and per-item results/*.jsonl.gz, and recount them.

  python summarize.py            build results/ from out/tau2-bench/data/simulations (and the usage logs in out/)
  python summarize.py --check    recount results/bielik-11b-v3.1.json and results/simulator-comparison.json from the
                                 per-item results/*.jsonl.gz alone (all but the cost and empty-completion counts,
                                 which come from logs in out/), exit 1 on a mismatch

Runs read (explicit list, not a glob; other directories there are smoke tests or an aborted start):
  Haiku 5.5 simulator, main result:  bielik-11b-v3.1_haiku_<domain> and, for tasks that ended without a reward there,
                                     bielik-11b-v3.1_haiku_retry_<domain> (run by retry_infra.sh)
  Sonnet 5.5 simulator, comparison:  bielik-11b-v3.1_sonnet_<domain> for airline, retail, telecom
                                     (bielik-11b-v3.1_sonnet_banking_knowledge holds 3 simulations of an aborted start
                                     and is not used)
  probe: probe_{haiku,sonnet}_<domain>, probe3_haiku_<domain> (PROTOCOL.md), probe_fault_readings.csv

Headline: mean of the 4 domain pass rates (percent); stderr = sqrt(sum of the 4 domain SE^2) / 4, each domain SE
sqrt(p (1 - p) / n) as in METHODOLOGY.md. A task without a reward is outside n and is never scored 0; the bounds put
it at 0 (lower) and 1 (upper). Simulator comparison: paired difference Sonnet - Haiku per task, SE = sd / sqrt(n),
z = d / SE, verdict and Holm from research/tools/statystyka.py (verdict words: pewne = clear, prawdopodobne =
borderline, szum = noise).
"""
import csv
import gzip
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools"))
import statystyka as st  # noqa: E402

MODEL = "bielik-11b-v3.1"
DOMAINS = ["airline", "retail", "telecom", "banking_knowledge"]
SONNET_DOMAINS = ["airline", "retail", "telecom"]
HAIKU, SONNET = "claude-haiku-5-5", "claude-sonnet-5-5"
PRICES = {HAIKU: (0.10, 0.50), SONNET: (2.0, 10.0)}  # USD per million input / output tokens
HARNESS = ("https://github.com/sierra-research/tau2-bench @ fc0055dc4e0a316c3f83133267fbd6faaa770992 "
           "(tag v1.0.1, the tau3-bench release line)")
SIMS = HERE / "out" / "tau2-bench" / "data" / "simulations"
RES = HERE / "results"
VERDICT_EN = {"pewne": "clear", "prawdopodobne": "borderline", "szum": "noise", st.NIEROZSTRZYGALNE: "undetermined"}
STAT_KEYS = ["agent_messages", "agent_messages_polish", "agent_short_replies", "user_messages", "user_words",
            "user_bold_messages"]
PL_WORDS = {"jest", "nie", "się", "dla", "proszę", "dziękuję", "czy", "przez", "mogę", "pani", "pana", "numer",
            "dzień", "dobry", "zamówienie", "rezerwacji", "który", "którą", "możemy", "witam"}


def error_class(info):
    """Why a simulation has no reward: 503 (API capacity), judge_json (the NL judge's answer is not JSON),
    empty_message (empty assistant message after the repeats of tau3_run.py), other."""
    t, e = (info or {}).get("error_type") or "", (info or {}).get("error") or ""
    tb = (info or {}).get("error_traceback") or ""
    if t == "ServiceUnavailableError":
        return "503"
    if t == "JSONDecodeError" and "evaluator_nl_assertions" in tb:  # json.loads of the judge's answer
        return "judge_json"
    if t == "ValueError" and "AssistantMessage" in e:
        return "empty_message"
    return "other"


def is_polish(text):
    """Heuristic: a Polish letter, or at least two common Polish words."""
    words = re.findall(r"[^\W\d_]+", text.lower())
    return bool(re.search("[ąćęłńóśźż]", text.lower())) or sum(w in PL_WORDS for w in words) >= 2


def load(name):
    p = SIMS / name / "results.json"
    return {s["task_id"]: s for s in json.loads(p.read_text())["simulations"]} if p.exists() else {}


def msg_stats(sim):
    """Counts over the saved messages: agent text replies (and Polish ones, and replies of at most 5 words), customer
    (simulator) messages, their words and the ones with markdown bold."""
    a = [m["content"] for m in sim["messages"] if m.get("role") == "assistant" and (m.get("content") or "").strip()
         and not m.get("tool_calls")]
    u = [m["content"] for m in sim["messages"] if m.get("role") == "user" and (m.get("content") or "").strip()]
    return {"agent_messages": len(a), "agent_messages_polish": sum(is_polish(m) for m in a),
            "agent_short_replies": sum(len(m.split()) <= 5 for m in a),
            "user_messages": len(u), "user_words": sum(len(m.split()) for m in u),
            "user_bold_messages": sum("**" in m for m in u)}


def item(domain, task, main, retry, simulator):
    """One row: the retry run replaces the main run only where the main run ended without a reward."""
    s, src, first_error = main, "main", None
    if main["reward_info"] is None and retry is not None:
        first_error, s, src = error_class(main.get("info")), retry, "retry"
    r = (s["reward_info"] or {}).get("reward")
    return {"task_id": task, "domain": domain, "simulator": simulator, "reward": r, "termination": s["termination_reason"],
            "source": src, "first_attempt_error": first_error,
            "error": None if r is not None else error_class(s.get("info")), **msg_stats(s)}


def rate(rewards):
    n = len(rewards)
    p = sum(rewards) / n if n else None
    return {"n": n, "passed": int(sum(rewards)), "p": p, "se": math.sqrt(p * (1 - p) / n) if n else None}


def headline(items):
    """Per-domain rates over assessed tasks, the 4-domain mean and its SE, and the lower and upper bounds."""
    per, lo, hi = {}, [], []
    for d in DOMAINS:
        rows = [i for i in items if i["domain"] == d]
        got = [i["reward"] for i in rows if i["reward"] is not None]
        per[d] = {**rate(got), "tasks": len(rows), "unassessed": len(rows) - len(got)}
        lo.append(rate(got + [0] * (len(rows) - len(got)))["p"])
        hi.append(rate(got + [1] * (len(rows) - len(got)))["p"])
    ps = [per[d]["p"] for d in DOMAINS]
    se = math.sqrt(sum(per[d]["se"] ** 2 for d in DOMAINS)) / 4
    return {"score": 100 * sum(ps) / 4, "stderr": 100 * se, "n": sum(per[d]["n"] for d in DOMAINS),
            "tasks": sum(per[d]["tasks"] for d in DOMAINS), "per_domain": per,
            "unassessed_as_0": 100 * sum(lo) / 4, "unassessed_as_1": 100 * sum(hi) / 4}


def compare(rows, key_h):
    """Paired Sonnet - Haiku per domain over tasks with a reward in both arms; key_h picks the Haiku reward column.
    The Holm family is the 3 domain tests."""
    out = []
    for d in SONNET_DOMAINS:
        pr = [(r[key_h], r["sonnet_reward"]) for r in rows if r["domain"] == d
              and r[key_h] is not None and r["sonnet_reward"] is not None]
        n = len(pr)
        x = [b - a for a, b in pr]
        m = sum(x) / n
        se = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1)) / math.sqrt(n)
        z = m / se if se > 0 else None
        out.append({"domain": d, "n": n, "haiku": sum(a for a, _ in pr) / n, "sonnet": sum(b for _, b in pr) / n,
                    "diff": m, "se": se, "z": z, "p": st.p_z(z), "verdict": VERDICT_EN[st.werdykt(z) or st.NIEROZSTRZYGALNE],
                    "sonnet_only": sum(1 for a, b in pr if b > a), "haiku_only": sum(1 for a, b in pr if a > b)})
    for r, h in zip(out, st.po_holmie([r["p"] for r in out], m=len(out))):
        r.update({"p_holm": h["p_holm"], "verdict_holm": VERDICT_EN[h["werdykt_holm"]], "after_holm": {"tak": "yes", "nie": "no"}[h["po_holmie"]]})
    return out


def build_main_items():
    items = []
    for d in DOMAINS:
        main, retry = load(f"{MODEL}_haiku_{d}"), load(f"{MODEL}_haiku_retry_{d}")
        items += [item(d, t, s, retry.get(t), HAIKU) for t, s in main.items()]
    return items


def build_comparison_rows(main_items):
    hm = {(i["domain"], i["task_id"]): i for i in main_items}
    rows = []
    for d in SONNET_DOMAINS:
        for t, s in load(f"{MODEL}_sonnet_{d}").items():
            h = hm[(d, t)]
            r = (s["reward_info"] or {}).get("reward")
            rows.append({"task_id": t, "domain": d, "haiku_reward": h["reward"], "haiku_source": h["source"],
                         "haiku_first_attempt_reward": h["reward"] if h["source"] == "main" else None,
                         "sonnet_reward": r, "sonnet_termination": s["termination_reason"],
                         "sonnet_error": None if r is not None else error_class(s.get("info")),
                         **{f"haiku_{k}": h[k] for k in STAT_KEYS}, **{f"sonnet_{k}": v for k, v in msg_stats(s).items()}})
    return rows


def lang_stats(items):
    pl = [i for i in items if i["agent_messages_polish"] > 0]
    got = [i["reward"] for i in pl if i["reward"] is not None]
    rest = [i["reward"] for i in items if i["agent_messages_polish"] == 0 and i["reward"] is not None]
    return {"simulations": len(items), "with_polish_agent_message": len(pl),
            "agent_messages": sum(i["agent_messages"] for i in items),
            "agent_messages_polish": sum(i["agent_messages_polish"] for i in items),
            "n_polish_assessed": len(got), "pass_rate_polish": rate(got)["p"] if got else None,
            "n_other_assessed": len(rest), "pass_rate_other": rate(rest)["p"]}


def style_stats(rows):
    """Conversation style per simulator arm over the simulations with at least one message, same 3 domains."""
    out = {}
    for arm in ("haiku", "sonnet"):
        r = [x for x in rows if x[f"{arm}_user_messages"] > 0]
        um = sum(x[f"{arm}_user_messages"] for x in r)
        am = sum(x[f"{arm}_agent_messages"] for x in r)
        out[arm] = {"simulations": len(r), "customer_messages_per_simulation": um / len(r),
                    "words_per_customer_message": sum(x[f"{arm}_user_words"] for x in r) / um,
                    "customer_messages_with_bold": sum(x[f"{arm}_user_bold_messages"] for x in r), "customer_messages": um,
                    "simulations_with_polish_agent_message": sum(x[f"{arm}_agent_messages_polish"] > 0 for x in r),
                    "agent_messages": am, "agent_messages_polish": sum(x[f"{arm}_agent_messages_polish"] for x in r),
                    "agent_replies_of_5_words_or_less": sum(x[f"{arm}_agent_short_replies"] for x in r),
                    "simulations_with_short_agent_reply": sum(x[f"{arm}_agent_short_replies"] > 0 for x in r)}
    return out


def cost(path, model):
    p = Path(path)
    n = a = b = 0
    if p.exists():
        for line in p.read_text().splitlines():
            r = json.loads(line)
            if (r["model"] or "").split("/", 1)[-1].startswith(model):
                n, a, b = n + 1, a + r["prompt_tokens"], b + r["completion_tokens"]
    pi, po = PRICES[model]
    return {"calls": n, "prompt_tokens": a, "completion_tokens": b, "cost_usd": round(a * pi / 1e6 + b * po / 1e6, 2)}


def empty_stats(path):
    if not Path(path).exists():
        return None
    """Repeated empty completions per model across every run that wrote to out/empty_calls.jsonl (smoke tests, probes,
    full runs, retries; the log has no run id). An episode is a call whose first completion was empty."""
    c, e = Counter(), Counter()
    for line in Path(path).read_text().splitlines():
        r = json.loads(line)
        m = r["model"].split("/", 1)[-1]
        c[m] += 1
        e[m] += r["attempt"] == 1
    return {"repeated_empty_completions": dict(c), "episodes": dict(e)}


def probe_stats():
    """Probe (20 tasks x 2 simulators, PROTOCOL.md) and the 3-repeat Haiku run, from the saved simulations."""
    arms = {}
    for a in ("haiku", "sonnet"):
        rows = []
        for d in DOMAINS:
            for t, s in load(f"probe_{a}_{d}").items():
                rows.append({"domain": d, "task_id": t, "reward": (s["reward_info"] or {}).get("reward"),
                             "termination": s["termination_reason"],
                             "error": None if s["reward_info"] else error_class(s.get("info"))})
        arms[a] = rows
    rd = list(csv.DictReader(open(HERE / "probe_fault_readings.csv")))
    faults = {}
    for a in ("haiku", "sonnet"):
        ra = [r for r in rd if r["arm"] == a]
        rr = [r for r in ra if r["final_fault"] != "not_assessable"]
        faults[a] = {"assessable": len(rr), "faults": sum(r["final_fault"] == "yes" for r in rr),
                     "reader1": sum(r["reader1_fault"] == "yes" for r in rr),
                     "reader2": sum(r["reader2_fault"] == "yes" for r in rr),
                     "not_assessable": len(ra) - len(rr)}
    reps = {}
    for d in DOMAINS:
        for s in json.loads((SIMS / f"probe3_haiku_{d}" / "results.json").read_text())["simulations"]:
            reps.setdefault((d, s["task_id"]), []).append((s["reward_info"] or {}).get("reward"))
    full = [v for v in reps.values() if len(v) == 3 and None not in v]
    return {"arms": arms, "fault_readings": faults,
            "repeats": {"tasks": len(reps), "tasks_with_3_rewards": len(full),
                        "tasks_same_in_all_3": sum(len(set(v)) == 1 for v in full),
                        "tasks_mixed": sum(len(set(v)) > 1 for v in full),
                        "per_task": {f"{d}/{t}": v for (d, t), v in sorted(reps.items())}}}


def write_gz(path, rows):
    with open(path, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, compresslevel=9) as f:
        for r in rows:
            f.write((json.dumps(r, ensure_ascii=False) + "\n").encode())


def read_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def result_json(items, extra):
    h = headline(items)
    retried = [i for i in items if i["source"] == "retry"]
    unassessed = [i for i in items if i["reward"] is None]
    return {
        "benchmark": "tau3-bench",
        "model": MODEL,
        "metric": "mean of the 4 domain pass rates (airline, retail, telecom, banking_knowledge), 1 trial, percent",
        "score": round(h["score"], 2), "stderr": round(h["stderr"], 2), "n": h["n"],
        "date": "2026-11-24",
        "harness": HARNESS,
        "data": "bundled with the harness at the same commit: airline 50, retail 114, telecom 114 (split base), banking_knowledge 97",
        "settings": {"agent": "openai/bielik-11b-v3.1 through the Fabryka AI API, temperature 0.6, top_p 0.95, 2 requests at a time",
                     "user_simulator": f"anthropic/{HAIKU}, litellm, LLM args {{}} (Claude 5.5 rejects temperature)",
                     "nl_judge": "openai/bielik-11b-v3.1, temperature 0.0 (harness default: gpt-4.1-2025-04-14)",
                     "retrieval_banking_knowledge": "bm25", "max_steps": 200, "max_errors": 10, "seed": 300,
                     "stderr_method": "sqrt(sum of the 4 domain SE^2) / 4, domain SE = sqrt(p (1 - p) / n)"},
        "other_metrics": {
            "per_domain": {d: {"score": round(100 * v["p"], 2), "stderr": round(100 * v["se"], 2), "n": v["n"],
                               "passed": v["passed"], "tasks": v["tasks"], "unassessed": v["unassessed"]}
                           for d, v in h["per_domain"].items()},
            "tasks": h["tasks"], "unassessed": len(unassessed),
            "unassessed_by_error": dict(Counter(i["error"] for i in unassessed)),
            "unassessed_as_0": round(h["unassessed_as_0"], 2), "unassessed_as_1": round(h["unassessed_as_1"], 2),
            "retried_tasks": len(retried),
            "retried_by_first_attempt_error": dict(Counter(i["first_attempt_error"] for i in retried)),
            "retried_with_reward": sum(i["reward"] is not None for i in retried),
            "agent_language": lang_stats(items), **extra},
        "deviations": "simulator Claude Haiku 5.5 instead of gpt-4.1-2025-04-14; NL-assertion judge Bielik 11B v3.1 instead "
                      "of gpt-4.1-2025-04-14; hidden Polish provider system prompt of the Fabryka API (#277); tasks that ended "
                      "without a reward were run once more (74 tasks); see README.md",
    }


def comparison_json(rows):
    return {
        "benchmark": "tau3-bench", "model": MODEL,
        "metric": "paired difference of the per-task reward (fraction), Sonnet 5.5 simulator minus Haiku 5.5 simulator, same agent and judge",
        "date": "2026-11-24", "harness": HARNESS,
        "settings": {"family": "3 tests (airline, retail, telecom), Holm over the 3; not pre-registered, see the PROTOCOL.md amendment",
                     "se_method": "sd of the per-task differences / sqrt(n); z = difference / SE",
                     "verdict_rule": "research/tools/statystyka.py: |z| >= 3 clear, 2-3 borderline, < 2 noise",
                     "banking_knowledge": "not run with the Sonnet simulator (cost); planned"},
        "tasks": {d: sum(r["domain"] == d for r in rows) for d in SONNET_DOMAINS},
        "paired_final": compare(rows, "haiku_reward"),
        "paired_first_attempt_only": compare(rows, "haiku_first_attempt_reward"),
        "sonnet_arm": {d: {"assessed": sum(r["sonnet_reward"] is not None for r in rows if r["domain"] == d),
                           "unassessed_by_error": dict(Counter(r["sonnet_error"] for r in rows
                                                               if r["domain"] == d and r["sonnet_reward"] is None)),
                           "pass_rate": rate([r["sonnet_reward"] for r in rows
                                              if r["domain"] == d and r["sonnet_reward"] is not None])["p"]}
                       for d in SONNET_DOMAINS},
        "style": style_stats(rows),
        "deviations": "none from the main run except the simulator; the Sonnet arm was not retried after infrastructure errors",
    }


def build():
    RES.mkdir(exist_ok=True)
    items = build_main_items()
    out = HERE / "out"
    extra = {"cost_usd": {"haiku_simulator_full_run": cost(out / f"usage_{MODEL}_haiku.jsonl", HAIKU),
                          "haiku_simulator_retry": cost(out / "usage_haiku_retry.jsonl", HAIKU),
                          "sonnet_simulator_3_domains_and_aborted_banking_start": cost(out / f"usage_{MODEL}_sonnet.jsonl", SONNET),
                          "prices_usd_per_mtok_in_out": {k: list(v) for k, v in PRICES.items()}},
             "empty_completions_all_runs_in_out": empty_stats(out / "empty_calls.jsonl")}
    write_gz(RES / f"{MODEL}.jsonl.gz", items)
    (RES / f"{MODEL}.json").write_text(json.dumps(result_json(items, extra), indent=2, ensure_ascii=False) + "\n")
    rows = build_comparison_rows(items)
    write_gz(RES / "simulator-comparison.jsonl.gz", rows)
    (RES / "simulator-comparison.json").write_text(json.dumps(comparison_json(rows), indent=2, ensure_ascii=False) + "\n")
    (RES / "simulator-probe.json").write_text(json.dumps(probe_stats(), indent=2, ensure_ascii=False) + "\n")


LOGS_ONLY = ("cost_usd", "empty_completions_all_runs_in_out")  # from uncommitted logs in out/, not recountable


def check():
    """Recount everything derivable from the committed per-item files and compare it with the JSON files, key by key.
    Only the cost and the empty-completion counts come from logs outside results/ and are not recounted."""
    bad = []
    items = read_gz(RES / f"{MODEL}.jsonl.gz")
    got = json.loads((RES / f"{MODEL}.json").read_text())
    exp = json.loads(json.dumps(result_json(items, {})))
    for k in exp:
        if k != "other_metrics" and got.get(k) != exp[k]:
            bad.append((k, got.get(k), exp[k]))
    for k in exp["other_metrics"]:
        if got["other_metrics"].get(k) != exp["other_metrics"][k]:
            bad.append(("other_metrics." + k, got["other_metrics"].get(k), exp["other_metrics"][k]))
    extra = set(got["other_metrics"]) - set(exp["other_metrics"]) - set(LOGS_ONLY)
    if extra:
        bad.append(("unexpected keys", sorted(extra)))
    rows = read_gz(RES / "simulator-comparison.jsonl.gz")
    exp_c = json.loads(json.dumps(comparison_json(rows)))
    if json.loads((RES / "simulator-comparison.json").read_text()) != exp_c:
        bad.append(("simulator-comparison.json", "differs from the recount"))
    return bad


if __name__ == "__main__":
    if "--check" in sys.argv:
        problems = check()
        for p in problems:
            print("MISMATCH", p)
        print("ok" if not problems else f"{len(problems)} mismatches")
        sys.exit(1 if problems else 0)
    build()
