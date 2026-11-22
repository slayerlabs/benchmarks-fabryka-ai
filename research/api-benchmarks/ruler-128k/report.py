"""README.md's Results and Hypotheses sections, generated from the results files: no number in them is typed by hand.

Usage: python3 report.py           rewrite the block between the markers in README.md
       python3 report.py --check   exit 1 when README.md's block differs from what the results files give

Reads results/<model-id>.json and .jsonl.gz, hypotheses.json (compare.py), diagnostics.json (diagnostics.py) and
reproduction.json (reproduction.py), each checked first against results/results.sha256.json. Every row of the results
table names the thinking mode, the serving path, the output limit and the tasks measured (team rule from the
LiveCodeBench v6 verification). RULER is generative: answers are free text scored by string match, so random and
majority baselines are 0; a rule that echoes the input scores near 100 with this scorer (diagnostics.json).
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

import provenance

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
README = HERE / "README.md"
BEGIN = "<!-- report.py: generated from results/ by `python3 report.py`; edit report.py, not this block -->"
END = "<!-- /report.py -->"
MODELS = {"lfm3-1.7b": "LFM3-1.7B", "bielik-11b-v3.1": "Bielik 11B v3.1",
          "slayer1b-1.09-k70000": "Slayer 1B 1.09, update 70 000"}
LENGTHS = [4096, 8192, 16384, 32768, 65536, 131072]
# Bielik's template with its defaults on a one-sentence message, counted locally (run.sh, API_MARGIN comment; the API
# billed about 1065 in ../ifeval): the provider system prompt each Bielik request carries
PROVIDER_PROMPT_TOKENS = 1057
TASKS = 13
FILES = [f"{m}{ext}" for m in MODELS for ext in (".json", ".jsonl.gz")] + [
    "hypotheses.json", "diagnostics.json", "reproduction.json"]


def f2(x):
    return "null" if x is None else f"{x:.2f}"


def fp(p):
    return "-" if p is None else f"{p:.2g}" if p < 1e-3 else f"{p:.2f}"


def load(results_dir):
    provenance.check(results_dir, FILES, provenance.RESULTS, "report.py", add_unrecorded=False)
    data = {name: json.loads((results_dir / name).read_text(encoding="utf-8")) for name in FILES if name.endswith(".json")}
    rows = {}
    for m in MODELS:
        with gzip.open(results_dir / f"{m}.jsonl.gz", "rt", encoding="utf-8") as f:
            rows[m] = [json.loads(line) for line in f]
    return data, rows


def thinking(result):
    strict = result["other_metrics"]["strict"]
    if strict.get("applies"):
        return "reasons first: the generation prompt opens `<think>`"
    reason = strict["reason"]
    return "no reasoning: the template closes `<think></think>`" if "closes" in reason else "none: " + reason


def serving(result):
    """The serving path and the weights (or, for the API, the tokenizer the prompts were counted with)."""
    s = result["settings"]
    repo, _, revision = s["weights"].split()[:3]
    weights = f"`{repo}` @ `{revision[:8]}`"
    if s["serving"].startswith("Fabryka"):
        return f"Fabryka AI API, hidden provider system prompt (#277); prompts counted with {weights}"
    if s["serving"].startswith("vLLM"):
        return f"{s['serving']}, {weights}"
    return f"{s['serving']}, greedy, {weights} `wagi_70000.pt`, converted"


def tasks_of(entry):
    return TASKS - len(entry.get("skipped_tasks") or {})


def lengths_measured(result):
    measured = [(int(k), v) for k, v in result["other_metrics"]["per_length"].items() if v["score"] is not None]
    return ", ".join(f"{k} ({tasks_of(v)})" for k, v in measured) or "none"


def cell(entry):
    if entry is None or entry["score"] is None:
        return "null"
    partial = f" ({tasks_of(entry)} tasks)" if entry.get("partial") else ""
    return f"{f2(entry['score'])} ± {f2(entry['stderr'])}{partial}"


def results_section(data, rows):
    out = ["## Results", "",
           "| model | thinking mode | serving | output limit | score at 131072 | strict | n | lengths measured (tasks) "
           "| date |", "|---|---|---|---|---|---|---|---|---|"]
    for m, label in MODELS.items():
        r = data[f"{m}.json"]
        score = f"{f2(r['score'])} ± {f2(r['stderr'])}" if r["score"] is not None else f"null: {r['reason']}"
        strict = f2(r["strict"]["score"]) if r["strict"]["score"] is not None else "null"
        out.append(f"| {label} (`{m}`) | {thinking(r)} | {serving(r)} | {r['settings']['max_tokens']} "
                   f"({r['settings']['context_window']}-token window) | {score} | {strict} | {r['n'] or '-'} | "
                   f"{lengths_measured(r)} | {r['date']} |")
    echo = data["diagnostics.json"]["lfm3-1.7b"]["echo_baseline"]["per_length"]
    out += ["", "Baselines: random and majority 0 (RULER is generative: free-text answers scored by string match against "
                "the references, with no options to guess from). A rule baseline scores high: an output that echoes the "
                "input (LFM3-1.7B's samples) scores " + ", ".join(f"{f2(v['mean'])} at {x}" for x, v in echo.items())
            + ", because the scorer is a case-insensitive substring match with no cap on the answer's length and the "
              "input contains the references (`diagnostics.json`, Amendment 8). The output limit here is the rest of the "
              "window, so a long answer is not cut down.", "",
            "Mean of the task scores per length (± bootstrap SE over samples within tasks; a length with fewer than "
            "13 tasks is partial: RULER's generator could not produce the task named in the result file). Strict "
            "(Amendment 4): an output without `</think>` scores 0, only where the generation prompt opens a "
            "reasoning block.", "",
            "| model | scoring | " + " | ".join(map(str, LENGTHS)) + " |", "|---" * (len(LENGTHS) + 2) + "|"]
    for m in MODELS:
        metrics = data[f"{m}.json"]["other_metrics"]
        out.append(f"| {m} | pre-registered | " + " | ".join(cell(metrics["per_length"].get(str(x))) for x in LENGTHS)
                   + " |")
        if metrics["strict"].get("applies"):
            out.append(f"| {m} | strict | " + " | ".join(cell(metrics["strict"]["per_length"].get(str(x)))
                                                       for x in LENGTHS) + " |")
    requests = {m: sum(r["score"] is not None for r in rows[m]) for m in MODELS}
    out += ["", "| model | requests scored (rows in `.jsonl.gz`) | errors |", "|---|---|---|"]
    out += [f"| {m} | {requests[m]} | {sum(r['score'] is None for r in rows[m])} |" for m in MODELS]
    out += ["", f"Each of Bielik's {requests['bielik-11b-v3.1']} requests carries the provider system prompt, about "
                f"{PROVIDER_PROMPT_TOKENS} tokens by the local count: about "
                f"{requests['bielik-11b-v3.1'] * PROVIDER_PROMPT_TOKENS / 1e6:.1f}M prompt tokens on top of RULER's input."]
    return out


def control_block(h, diag):
    c = h["control"]
    s = c["strict"]
    out = [f"**Control: {c['status']}, z = {f2(c['z'])}.** LFM3-1.7B at 131072: {f2(c['mean'])} ± {f2(c['se'])} "
           f"against the card's {c['card']}, z = {f2(c['z'])} (strict {f2(s['mean'])} ± {f2(s['se'])}, "
           f"z = {f2(s['z'])}). {c['reading']}; the control's z = {f2(c['z'])}. {c['amendment_4']}.", ""]
    v = diag["lfm3-1.7b"]["control_variants"]
    near = [name for name, x in v["variants"].items() if x["within_2_se"]]
    out += [f"Exploratory, not a fix of the control: after the failure the refuter rescored the 131072 outputs in "
            f"{v['variants_tried']} ways (`diagnostics.json`); {len(near)} of them land within 2 SE of the card. With "
            f"{v['variants_tried']} variants tried, landing near the card says which unstated choices could explain "
            f"the difference, not which one the card used. The SEs come from diagnostics.py's own bootstrap, so the "
            f"pre-registered row's z differs from the control's in the second decimal.", "",
            "| scoring of LFM3-1.7B at 131072 | mean ± SE | z against 65.56 | within 2 SE |", "|---|---|---|---|"]
    out += [f"| {name} | {f2(x['mean'])} ± {f2(x['se'])} | {f2(x['z_vs_card'])} | {'yes' if x['within_2_se'] else 'no'} |"
            for name, x in v["variants"].items()]
    return out


def zt(h):
    return f"z = {f2(h['z'])}" if h.get("z") is not None else f"t = {f2(h['t'])} (df {h['df']})" if h.get("t") is not None else "-"


def hypotheses_table(h):
    rules = {"R1": "mean at 131072 below 85.6 with z <= -3 (sample-level SE)",
             "R2": "slope difference, LFM3-1.7B minus Bielik (Amendment 1)",
             "R3": "drops 4096 to 131072: refuted when retrieval's is not smaller than tracing's and aggregation's; "
                   "strength with the SE clustered by task"}
    out = ["| hypothesis | pre-registered measure | value ± SE | z or t | Holm p (m = 3) | verdict | outcome | n | strict "
           "verdict |", "|---|---|---|---|---|---|---|---|---|"]
    for name, x in h["hypotheses"].items():
        if "status" in x:
            out.append(f"| {name} | {rules[name]} | - | - | - | {x['status']} | {x['outcome']} | - | "
                       f"{x['strict']['verdict']} |")
            continue
        out.append(f"| {name} | {rules[name]} | {f2(x['value'])} ± {f2(x['se'])} | {zt(x)} | {fp(x['p_holm'])} | "
                   f"{x['verdict']} | {x['outcome']} | {x['n']} | {x['strict']['verdict']} |")
    return out


def r1_block(h):
    r1 = h["hypotheses"]["R1"]
    s, e, st = r1["sensitivity"], r1["effective_length"], r1["strict"]["effective_length"]
    c, g, w = s["clustered"], s["sign_test"], s["without_lowest"]
    point = str(e["point"])
    return [f"**R1: {r1['outcome']} by the pre-registered rule, {r1['verdict']}.** LFM3-1.7B at 131072: "
            f"{f2(r1['value'])} ± {f2(r1['se'])}, {f2(r1['comparisons'][0]['value'])} against 85.6, z = {f2(r1['z'])} "
            f"(strict: z = {f2(r1['strict']['z'])}, {r1['strict']['verdict']}). The rule's SE treats the 13 tasks as "
            f"fixed. Next to it, not replacing it: with the SE clustered by task t = {f2(c['t'])} (df {c['df']}, "
            f"p {fp(c['p'])}, {c['verdict']}); {g['below']} of {g['tasks']} tasks are below 85.6 (sign test p "
            f"{fp(g['p'])}); without the 2 lowest tasks at 131072 ({', '.join(w['tasks_dropped'])}) the mean is "
            f"{f2(w['mean'])} ± {f2(w['se'])}, z = {f2(w['z'])} against 85.6 ({w['verdict']}). Protocol rule met; "
            f"whether the context loss holds across tasks rather than in two of them is undetermined.", "",
            f"Effective length (longest length with a mean of at least 85.6), with the 13 tasks as fixed: "
            f"{e['above_2_se']} or {point}. {point} has {f2(e['per_length'][point]['mean'])}, only z = {f2(e['z'])} "
            f"above 85.6 (strict {f2(st['per_length'][point]['mean'])}, z = {f2(st['z'])}); {e['above_2_se']} is the "
            f"longest length at least 2 SE above it. Across tasks (t of the task means against 85.6, df 12; Amendment 8) "
            + (f"no length beyond {e['above_across_tasks']} can be named"
               if e["above_across_tasks"] else "no length can be named")
            + f" ({e['above_across_tasks'] or 'none'} is the longest above 85.6 at p ≤ 0.0455, the p of |z| = 2; strict: "
            f"{st['above_across_tasks'] or 'none'}); {len(e['tasks_below_at_shortest'])} tasks "
            f"({', '.join(e['tasks_below_at_shortest'])}) are below 85.6 already at {min(map(int, e['per_length']))}. "
            f"SEs below come from compare.py's bootstrap (seeded per model), the per-length table in Results from "
            f"summarize.py's; they differ in the second decimal.", "",
            "| length | mean ± SE | z against 85.6 | across tasks t (df), p | strict mean ± SE | strict z | strict "
            "across tasks t, p |", "|---|---|---|---|---|---|---|"] + [
            f"| {x} | {f2(v['mean'])} ± {f2(v['se'])} | {f2(v['z'])} | {f2(v['across_tasks']['t'])} "
            f"({v['across_tasks']['df']}), p {fp(v['across_tasks']['p'])} | {f2(st['per_length'][x]['mean'])} ± "
            f"{f2(st['per_length'][x]['se'])} | {f2(st['per_length'][x]['z'])} | "
            f"{f2(st['per_length'][x]['across_tasks']['t'])}, p {fp(st['per_length'][x]['across_tasks']['p'])} |"
            for x, v in e["per_length"].items()]


def r2_block(h, diag):
    r2 = h["hypotheses"]["R2"]
    lfm3, bielik = "lfm3-1.7b", "bielik-11b-v3.1"
    ratio = diag["input_text"]["bielik_over_lfm3"]
    out = [f"**R2: {r2['status']}.** Complete lengths both models measured: {', '.join(map(str, r2['lengths']))}. "
           "Per-length means, descriptive only, not a test of R2 (Amendments 6 and 8). The difference is on the same "
           "tasks; its SE combines the two models' bootstraps (independent: RULER generated each model's data with its "
           "own tokenizer); the t is across tasks (each task's difference, df = tasks - 1).", "",
           f"| length | {MODELS[lfm3]} | {MODELS[bielik]} | Bielik minus LFM3-1.7B, same tasks: value ± SE, z | across "
           "tasks: t (df), p | without the task of the largest gap | Bielik input text (median characters, share of "
           "LFM3-1.7B's) |", "|---|---|---|---|---|---|---|"]
    for length, d in r2["descriptive"].items():
        a, b, g = d[lfm3], d[bielik], d["bielik_minus_lfm3"]
        at, w = g["across_tasks"], g["without_largest_gap"]
        note_a = f"{f2(a['mean'])}" + (f"; {f2(a['mean_on_shared_tasks'])} on the same {a['shared_tasks']} tasks"
                                       if "mean_on_shared_tasks" in a else "")
        note_b = f"{f2(b['mean'])}" + (f" ({b['tasks']} tasks, no {', '.join(b['skipped_tasks'])})"
                                       if "skipped_tasks" in b else "")
        diff = f"{f2(g['value'])} ± {f2(g['se'])}, z = {f2(g['z'])}" + (
            f" ({f2(b['mean'] - a['mean'])} on unequal task sets)" if "mean_on_shared_tasks" in a else "")
        out.append(f"| {length} | {note_a} | {note_b} | {diff} | t = {f2(at['t'])} ({at['df']}), p {fp(at['p'])} | "
                   f"without {w['task']} ({f2(w['gap'])}): {f2(w['value'])} ± {f2(w['se'])}, z = {f2(w['z'])} | "
                   f"{diag['input_text']['median_chars'][bielik][length]:.0f} ({f2(ratio[length])}) |")
    out += [""] + [f"- {c[0].upper()}{c[1:]}." for c in r2["caveats"]]
    return out


def r3_block(h):
    r3 = h["hypotheses"]["R3"]
    tr, ag = r3["comparisons"]
    d = r3["descriptive_sample"]
    w = r3["without_largest_retrieval_drops"]
    wt = w["tracing_minus_retrieval"]
    drops = r3["drops"]
    out = [f"**R3: {r3['outcome']} by the pre-registered point rule as coded before the results** (tracing drop "
           f"{f2(drops['tracing']['drop'])} against retrieval {f2(drops['retrieval']['drop'])}; aggregation "
           f"{f2(drops['aggregation']['drop'])}). **Across tasks the strength is {r3['verdict']}**: "
           f"{r3['undetermined_reason']} (Amendments 7 and 8). Tracing - retrieval {f2(tr['value'])} ± "
           f"{f2(tr['se_clustered'])} (t = {f2(tr['t'])}, df {tr['df']}, p {fp(tr['p_t'])}; tracing's one task has no "
           f"between-task SE, taken as 0), aggregation - retrieval {f2(ag['value'])} ± {f2(ag['se_clustered'])} "
           f"(t = {f2(ag['t'])}, df {ag['df']}). The retrieval drop rests on {len(w['tasks_dropped'])} of {w['of']} "
           f"retrieval tasks ({', '.join(w['tasks_dropped'])}: {w['share_of_retrieval_drop'] * 100:.0f}% of it); "
           f"without them retrieval drops {f2(w['retrieval_drop'])} and tracing - retrieval is {f2(wt['value'])} ± "
           f"{f2(wt['se_sample'])} (sample-level SE). Descriptive, with the sample-level SE (tasks fixed, not the "
           f"protocol's SE): tracing - retrieval {f2(d['value'])} ± {f2(d['se'])}, z = {f2(d['z'])}.", "",
           "| LFM3-1.7B category | tasks | drop 4096 to 131072 | SE clustered by task | SE sample-level |",
           "|---|---|---|---|---|"]
    out += [f"| {c} | {x['tasks']} | {f2(x['drop'])} | {f2(x['se_clustered']) if x['se_clustered'] is not None else '-'}"
            f" | {f2(x['se_sample'])} |" for c, x in r3["drops"].items()]
    return out


def notes_block(diag):
    l3 = diag["lfm3-1.7b"]
    te, dup = l3["think_end"], l3["duplicates"]
    stopped = te["stopped_without_think_end"]
    by_length = "; ".join(f"{x}: " + ", ".join(f"{n} `{k}`" for k, n in v.items())
                          for x, v in te["without_think_end_by_finish_reason"].items())
    out = ["**Strict scoring and outputs that stopped without `</think>`.** Amendment 4's reason for strict scoring "
           f"was outputs looping to the length limit. LFM3-1.7B outputs without `</think>` per length and finish "
           f"reason: {by_length}. {len(stopped)} stopped on its own without closing its reasoning: "
           + "; ".join(f"{s['length']} {s['task']} #{s['index']} ({s['output_tokens']} output tokens, pre-registered "
                       f"score {f2(s['pre_registered_score'])}, strict {f2(s['strict_score'])})" for s in stopped)
           + ". Strict scoring gives such an output 0 although it did not loop to the limit.", ""]
    for length, x in dup["per_length"].items():
        r3 = dup["r3_comparisons_at_4096"]
        out.append(
            f"**Samples with two raw records (LFM3-1.7B, {length}).** {sum(x['samples_with_more_than_one_record'].values())} "
            f"samples have {', '.join(map(str, x['records_per_sample']))} records (a rerun appended: "
            + ", ".join(f"{t} {n}" for t, n in x["samples_with_more_than_one_record"].items())
            + f"); every replaced record ended `{', '.join(x['finish_reason_of_replaced'])}`, "
            f"{x['identical_outputs']} are identical to the last. The last record is scored (`ruler.latest_records`). With "
            f"the first record instead the mean at {length} is {f2(x['mean']['first'])} (scored: "
            f"{f2(x['mean']['last (scored)'])}), strict {f2(x['strict_mean']['first'])} "
            f"({f2(x['strict_mean']['last (scored)'])}); R3's tracing - retrieval "
            f"{f2(r3['first']['drop tracing - drop retrieval'])} ({f2(r3['last (scored)']['drop tracing - drop retrieval'])})"
            f" and aggregation - retrieval {f2(r3['first']['drop aggregation - drop retrieval'])} "
            f"({f2(r3['last (scored)']['drop aggregation - drop retrieval'])}). The scored record is not the longer "
            f"one: median {x['output_tokens_median']['last']:.0f} output tokens against "
            f"{x['output_tokens_median']['first']:.0f} for the replaced, longer in {x['last_longer_than_first']} of "
            f"{sum(x['samples_with_more_than_one_record'].values())}.")
    return out


def provenance_block(data):
    out = ["**Provenance.**", ""]
    rep = data["reproduction.json"]
    for m in MODELS:
        p = data[f"{m}.json"]["provenance"]
        code = p["summarize"]["code"]
        if p.get("generation"):
            g = p["generation"][0]["code"]
            gen = f"recorded by run.sh (`generation.jsonl`): commit `{g['commit'][:8]}`, dirty {g['dirty']}"
        elif p.get("generation_declared"):
            g = p["generation_declared"]
            c = g["code"]
            gen = (f"{g['status']}: commit `{c['commit'][:8]}`"
                   + (f", {c['relation']}" if c.get("relation") else "")
                   + ("; runner sha256 " + ", ".join(f"{k} `{v[:8]}`" for k, v in c["runner_sha256"].items())
                      if c.get("runner_sha256") else "")
                   + f" ({g['source']})" + (f"; requests: {g['requests']}" if g.get("requests") else "")
                   + "; archives " + ", ".join(f"`{k}` sha256 `{v[:12]}…`" for k, v in g["archives_sha256"].items()))
        else:
            gen = p["generation_reason"]
        out.append(f"- {MODELS[m]}: generation {gen}. Summary: commit `{code['commit'][:8]}`"
                   + (f", runner files differing from it: {code['uncommitted_runner_files'] or 'none'}"
                      if "uncommitted_runner_files" in code else f", dirty {code['dirty']} (runner files not listed)")
                   + ".")
        if m in rep:
            r = rep[m]
            out.append(f"  The first summary was written by a summarize.py in no commit (sha256 "
                       f"`{r['published']['summarize.py sha256'][:8]}…`, tree at `{r['published']['code']['commit'][:8]}`, "
                       f"dirty {r['published']['code']['dirty']}); summarize.py at `{r['rerun']['code']['commit'][:8]}` "
                       f"reproduces it: {len(r['fields_differing'])} fields differ outside provenance and warnings, "
                       f"rows identical: {r['jsonl_rows']['identical']} ({r['jsonl_rows']['rerun']}).")
    return out


def manifest_block(results_dir):
    recorded = json.loads((results_dir / provenance.RESULTS).read_text(encoding="utf-8"))
    return ["Results files and their sha256 (`results/results.sha256.json`):", "", "| file | sha256 |", "|---|---|"] + [
        f"| `results/{name}` | `{sha}` |" for name, sha in recorded.items()]


def render(results_dir=RESULTS):
    data, rows = load(Path(results_dir))
    h, diag = data["hypotheses.json"], data["diagnostics.json"]
    lines = [BEGIN, *results_section(data, rows), "", "## Hypotheses", "",
             "`python3 compare.py` evaluates PROTOCOL.md as amended and writes `results/hypotheses.json`; "
             "`python3 diagnostics.py` the exploratory checks in `results/diagnostics.json`. Holm runs over the three "
             "hypotheses (m = 3) whether or not they could be decided.", "",
             *control_block(h, diag), "", *hypotheses_table(h), "", *r1_block(h), "", *r2_block(h, diag), "",
             *r3_block(h), "", *notes_block(diag), "", *provenance_block(data), "", *manifest_block(Path(results_dir)),
             END]
    return "\n".join(lines) + "\n"


def block_of(text):
    start, end = text.index(BEGIN), text.index(END) + len(END) + 1
    return text[start:end]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    text, block = README.read_text(encoding="utf-8"), render()
    if args.check:
        same = block_of(text) == block
        print("report.py: README.md block matches the results files" if same else
              "report.py: README.md block differs from the results files; run python3 report.py")
        sys.exit(0 if same else 1)
    README.write_text(text.replace(block_of(text), block), encoding="utf-8")


if __name__ == "__main__":
    main()
