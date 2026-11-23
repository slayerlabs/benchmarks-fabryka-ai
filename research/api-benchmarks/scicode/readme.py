"""Writes the generated blocks of README.md from results/, so no number in them is typed by hand.

Usage: python3 readme.py [results-dir] [--check]   (default: results/ next to this file)

Blocks, each between `<!-- readme.py: NAME ... -->` and `<!-- readme.py: end NAME -->`:
- `results`: one row per run from results/<model-id>.json (headline with background: correct steps, binomial and
  clustered SE, n, main problems, mean output tokens, date) with each row's thinking mode, serving and output limit;
  both settings with main problems and the scorer's verdicts; output tokens, unfinished answers, length stops and
  answers containing `<think>`; E1 next to the official extraction with the steps that took the official verdict
  (identical file) and those scored; baselines; the scoring machine; where the raw outputs are; the setup check;
- `hypotheses`: hypotheses.py's report of results/hypotheses.json, verbatim, the without-background forms, and what
  K2 and K3 compare;
- `exploratory`: reasoning counts and empty extractions from results/raw-outputs.json (raw_outputs.py), labelled as
  added after the results were seen;
- `scoring`: what happened on the scoring VM, from results/scoring-events.json (scoring_events.py) and the result
  files (generation and scoring commits, the E1 reuse counts).
Every file read must have the sha256 its writer recorded in its manifest.json. Where a count is 0, the cell gives the
exact (Clopper-Pearson) two-sided 95% interval instead of the SE, which is 0 there. `--check` writes nothing and
exits 1 when README.md differs from what this would write; the tests make the same comparison byte for byte.
"""

import json
import sys
from pathlib import Path
from typing import Any

import hypotheses
import provenance

HERE = Path(__file__).resolve().parent
README = HERE / "README.md"
SETTINGS = ("with_background", "without_background")
SETTING_LABEL = {"with_background": "with background", "without_background": "without background"}
RUNS = {
    "lfm3-1.7b": ("LFM3-1.7B (`lfm3-1.7b`)", "on (template default)", "vLLM 0.34.0, bf16, one H100"),
    "lfm3-1.7b-nothink": ("LFM3-1.7B (`lfm3-1.7b-nothink`)", "off requested (`enable_thinking: false`)",
                          "the same vLLM server"),
    "bielik-11b-v3.1": ("Bielik 11B v3.1 (`bielik-11b-v3.1`)", "no reasoning switch through the API",
                        "Fabryka AI API, with the API's provider system prompt"),
}
NOT_RUN = ("Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`)", "slayer1b-1.09-k70000")
STEPS, PROBLEMS = 288, 65
REPRODUCTION_TOLERANCE_PT = 2  # the reporting rules' check against a published number (zasady raportowania, §4)


def markers(name: str) -> tuple[str, str]:
    return (f"<!-- readme.py: {name} (generated from results/ by readme.py; edit readme.py, not this block) -->",
            f"<!-- readme.py: end {name} -->")


def read_json(results: Path, name: str) -> dict[str, Any]:
    provenance.verify(results, [name], "readme.py")
    return json.loads((results / name).read_text(encoding="utf-8"))


def zero_upper(n: int) -> float:
    """Upper end (percent) of the exact (Clopper-Pearson) two-sided 95% interval for 0 successes in n."""
    return 100 * (1 - 0.025 ** (1 / n))


def share(k: int, n: int, se: float | None = None, se_cl: float | None = None) -> str:
    """`p ± SE (k/n)`, the clustered SE after a semicolon when given; for k = 0 the exact 95% interval."""
    if k == 0:
        return f"0.00 (0/{n}; exact 95% CI 0 to {zero_upper(n):.2f})"
    clustered = "" if se_cl is None else f"; clustered {se_cl:.2f}"
    return f"{100 * k / n:.2f} ± {se:.2f} ({k}/{n}{clustered})"


def problems_cell(mp: dict[str, Any]) -> str:
    if mp["solved"] == 0:
        return f"0/{mp['of']} (exact 95% CI 0 to {zero_upper(mp['of']):.2f}%)"
    return f"{mp['solved']}/{mp['of']} ({100 * mp['solved'] / mp['of']:.2f}%)"


def setting_metrics(r: dict[str, Any], setting: str) -> dict[str, Any]:
    o = r["other_metrics"]
    if setting == "with_background":
        return {**o["with_background"], "score": r["score"], "stderr": r["stderr"], "n": r["n"]}
    return o[setting]


def limit_cell(r: dict[str, Any]) -> str:
    return f"{r['settings']['max_tokens']} (context {r['settings']['context']})"


def results_block(results: Path) -> str:
    files = {m: read_json(results, f"{m}.json") for m in RUNS}
    slayer = read_json(results, f"{NOT_RUN[1]}.json")
    out = ["Headline: correct subproblems with background, out of 288 (test_generated_code.py). Verdicts read the "
           "SE clustered by problem (65 clusters).", "",
           "| model | thinking | serving | output limit | correct (%) | stderr | stderr clustered | n | main problems "
           "| mean output tokens | date |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m, (name, thinking, serving) in RUNS.items():
        r = files[m]
        wb = setting_metrics(r, "with_background")
        out.append(f"| {name} | {thinking} | {serving} | {limit_cell(r)} | {r['score']:.2f} | {r['stderr']:.2f} | "
                   f"{r['stderr_clustered']:.2f} | {r['n']} | {problems_cell(wb['main_problems'])} | "
                   f"{wb['output_tokens']['mean']:.1f} | {r['date']} |")
    out.append(f"| {NOT_RUN[0]} | | | | null ({slayer['reason']}) | | | | | | |")
    out += ["", "Both prompt settings: correct (%) ± stderr (correct/288; clustered SE), main problems solved (all "
            "scored steps pass) out of 65, and the scorer's verdicts per step:", "",
            "| run | setting | correct | main problems | pass | fail | time out |", "|---|---|---|---|---|---|---|"]
    for m, r in files.items():
        for s in SETTINGS:
            x = setting_metrics(r, s)
            v = x["verdicts"]
            out.append(f"| {m} | {SETTING_LABEL[s]} | {share(x['correct'], x['n'], x['stderr'], x['stderr_clustered'])}"
                       f" | {problems_cell(x['main_problems'])} | {v.get('pass', 0)} | {v.get('fail', 0)} | "
                       f"{v.get('time out', 0)} |")
    out += ["", "| run | setting | output tokens mean / median / max | unfinished (thinking on) | stopped by the length "
            "limit | prompts over the context | answers containing `<think>` |", "|---|---|---|---|---|---|---|"]
    for m, r in files.items():
        for s in SETTINGS:
            x = setting_metrics(r, s)
            t = x["output_tokens"]
            th = x["answers_with_think_open"]
            out.append(f"| {m} | {SETTING_LABEL[s]} | {t['mean']:.1f} / {t['median']} / {t['max']} | {x['unfinished']} "
                       f"| {x['length_stops']} | {x['unsupported']} | {th['count']} of {th['of']} |")
    out += ["", "Secondary extraction E1 (PROTOCOL.md Amendment 1), the same answers: a step whose E1 file is "
            "byte-identical to its official file took the official verdict, the others were scored by the same "
            "scorer:", "",
            "| run | setting | correct, official | correct, E1 | main problems, E1 | steps with the official verdict "
            "(identical file) | steps scored under E1 |", "|---|---|---|---|---|---|---|"]
    for m, r in files.items():
        for s in SETTINGS:
            x, e = setting_metrics(r, s), r["other_metrics"]["extraction_e1"][s]
            out.append(f"| {m} | {SETTING_LABEL[s]} | {x['correct']}/{x['n']} | "
                       f"{share(e['correct'], e['n'], e['stderr'], e['stderr_clustered'])} | "
                       f"{problems_cell(e['main_problems'])} | {e['reused_identical']} | {e['scored']} |")
    api = files["bielik-11b-v3.1"]["other_metrics"]["with_background"]["api_prompt_minus_local"]
    ev = files["bielik-11b-v3.1"]["provenance"]["api_events"]
    out += ["", f"Bielik's prompt: the API's `usage.prompt_tokens` minus our local count with Bielik's own template, "
                f"with background: min {api['min']}, max {api['max']}. Its request log holds {ev['events']} events "
                f"({', '.join(f'{k} {v}' for k, v in ev['by_action'].items())}; HTTP "
                f"{', '.join(f'{k} {v}' for k, v in ev['by_status'].items())}).",
            "", "Baselines: 0 for random and majority answers (no fixed output passes a step's numerical tests). "
                f"The LFM3-1.7B card reports {100 * hypotheses.CARD_LFM:.2f}; the control is in Hypotheses."]
    s = files["lfm3-1.7b"]["provenance"]["scoring"]
    machines = {json.dumps({k: f["provenance"]["scoring"][k] for k in ("cpu", "cpu_count", "container", "packages",
                                                                       "test_data_h5", "scicode_commit")},
                           sort_keys=True) for f in files.values()}
    if len(machines) != 1:
        sys.exit("readme.py: the runs were scored on different machines, images or packages")
    seen = sorted({v["printed"]["dataset_revision_seen"] for f in files.values()
                   for v in f["provenance"]["scoring"]["runs"].values() if v["printed"]})
    pk = s["packages"]
    out += ["", f"Scoring: all three runs on one VM ({s['cpu']}, {s['cpu_count']} vCPUs), SciCode "
                f"`{s['scicode_commit'][:8]}`, container image `{s['container']['image_id']}` (network "
                f"{s['container']['network']}; python {s['python']}, numpy {pk['numpy']} with "
                f"{pk['numpy_blas']['name']} {pk['numpy_blas']['version']}, scipy {pk['scipy']}, sympy {pk['sympy']}, "
                f"h5py {pk['h5py']}), BLAS threads 1, 1800 s per step; `test_data.h5` sha256 "
                f"`{s['test_data_h5']['sha256']}` checked; dataset revision the scorer loaded: "
                f"{', '.join(f'`{x}`' for x in seen)}."]
    raw = read_json(results, "raw-outputs.json")
    out += ["", f"Raw outputs (with thinking, not committed): the LFM3-1.7B runs in `{raw['archive']['file']}`, "
                f"sha256 `{raw['archive']['sha256']}`; Bielik's in `{raw['runs']['bielik-11b-v3.1']['file']}`. Each "
                "run's generations.jsonl sha256 equals its result file's `raw_outputs.sha256` "
                "(results/raw-outputs.json)."]
    dev = read_json(results / "checks", "dev-ground-truth.json")
    dm = dev["other_metrics"]["with_background"]
    out += ["", f"Setup check (not a model): the dev split's `ground_truth_code`, fed through the same Gencode files "
                f"and scorer, passes {dm['correct']} of {dev['n']} steps and {dm['main_problems']['solved']} of "
                f"{dm['main_problems']['of']} problems (results/checks/dev-ground-truth.json); the "
                f"{dev['n'] - dm['correct']} failing steps "
                "fail with the authors' own code (SciCode issue #43)."]
    return "\n".join(out)


def hypotheses_block(results: Path) -> str:
    h = read_json(results, "hypotheses.json")
    raw = read_json(results, "raw-outputs.json")["runs"]
    off = raw["lfm3-1.7b-nothink"]["settings"]["with_background"]["reasoning"]
    on = raw["lfm3-1.7b"]["settings"]["with_background"]["reasoning"]
    tok = {m: read_json(results, f"{m}.json")["other_metrics"]["with_background"]["output_tokens"]["mean"]
           for m in ("lfm3-1.7b", "lfm3-1.7b-nothink")}
    k2, k3 = h["hypotheses"]
    t = h["t_check"]
    cf = read_json(results, "exploratory.json")["k3_without_reasoning_passes"]
    d = h["descriptive"]
    holm = h["holm"]
    group = json.loads((results / holm["other_benchmark_file"].split("results/", 1)[-1]).read_text(encoding="utf-8"))
    out = [hypotheses.report(h), "",
           "Without background (descriptive, not tested; PROTOCOL.md: the without-background run is no second "
           "chance at the control):", "",
           "| test form | value (pp) | SE (pp) | z |", "|---|---|---|---|",
           f"| K1 form: LFM3-1.7B minus the card's {d['K1_form']['card']:.2f} | "
           f"{d['K1_form']['score'] - d['K1_form']['card']:+.2f} | {d['K1_form']['se_clustered']:.2f} | "
           f"{d['K1_form']['z']:+.2f} |",
           f"| K2 form | {d['K2_form']['value']:+.2f} | {d['K2_form']['se']:.2f} | {d['K2_form']['z']:+.2f} |",
           f"| K3 form | {d['K3_form']['value']:+.2f} | {d['K3_form']['se']:.2f} | {d['K3_form']['z']:+.2f} |",
           "", "Reading:", "",
           f"- **K1** {h['control']['status']} by PROTOCOL.md's rule: LFM3-1.7B with background lands within 2 "
           f"clustered SE of its card value ({h['control']['score'] - h['control']['card']:+.2f} pt, z = "
           f"{h['control']['z']:+.2f}), so K2 and K3 are read. The reporting rules' reproduction check (within "
           f"±{REPRODUCTION_TOLERANCE_PT} pt of a published number) is not met: the gap is "
           f"{abs(h['control']['score'] - h['control']['card']):.2f} pt; at n = {h['control']['n']} that check cannot be "
           f"decided either way, since 2 clustered SE are {2 * h['control']['se_clustered']:.2f} pt.",
           f"- **K2** ({k2['verdict_holm']}) compares Bielik through the API with a number on the card, not with a "
           f"model run here: LFM2.5-2.6B's {100 * hypotheses.WEAKEST_CARD:.2f}, with the SE floor of PROTOCOL.md. "
           f"Under E1 (Amendment 1) z = {k2['e1']['z']:+.2f}, {k2['e1']['verdict_holm']}: "
           f"{k2['extraction_note']}",
           f"- **K3** {k3['verdict_holm'].split(' ')[0]} under the pre-registered switch (`enable_thinking: false`): "
           f"with the switch off LFM3 keeps more than half of its lead over Bielik (D = {k3['value']:+.2f} ± "
           f"{k3['se']:.2f}, z = {k3['z']:+.2f}; the lead itself {k3['precondition']['lead_on_minus_bielik']:+.2f}, "
           f"z = {k3['precondition']['z']:+.2f}). *Descriptive, from the raw outputs, added after the results "
           f"(Amendment 2):* the switch removes reasoning only in part: with it off "
           f"{off['closing_think']} of {off['answers']} answers with background still reason and close a "
           f"`</think>` (median {100 * off['median_share_before_last_think_end']:.1f}% of an answer's characters "
           f"before it), against {on['closing_think']} of {on['answers']} with thinking on; {off['passed_closing_think']} "
           f"of its {off['passed']} passed steps come from such answers, and it writes {tok['lfm3-1.7b-nothink']:.0f} "
           f"output tokens per answer on average against {tok['lfm3-1.7b']:.0f}. How much of the lead thinking "
           "itself buys is therefore undetermined by K3.",
           f"  - *Exploratory (explore.py):* counting those {cf['passes_removed']} passes as failed gives D = "
           f"{cf['value']:+.2f} ± {cf['se']:.2f} (z = {cf['z']:+.2f}): the lead that survives the switch sits in "
           "answers that still reason.",
           *repeat_lines(results),
           f"- **With Student's t instead of the normal** (descriptive, df = {t['df']}, our two tests; LiveCodeBench "
           f"Pro's p as recorded) the verdicts are the same: K2 Holm p {t['K2']['p_support_holm']:.3g}, "
           f"{t['K2']['verdict_holm']}; K3 Holm p {t['K3']['p_refute_holm']:.3g}, {t['K3']['verdict_holm']}, against "
           f"{hypotheses.P_CLEAR:.3g} for \"clear\" (z = 3), a small margin.",
           f"- **Holm over the Coding group** (m = {holm['m']}) used LiveCodeBench Pro 25Q2's K2 and K3 from "
           f"`{holm['other_benchmark_file']}`, copied from branch `{group['source']['branch']}` at "
           f"`{group['source']['commit'][:8]}`.",
           "", "K3 robustness (descriptive, added after the results; no verdict reads it): D without the problems "
           "that contribute most to it, with the Holm p of \"refuted\" (the other three tests unchanged):", "",
           "| problems left out | D (pp) | SE (pp) | z | Holm p | verdict after Holm |", "|---|---|---|---|---|---|"]
    rob = h["k3_robustness"]
    for x in rob["drop_top_problems"]:
        out.append(f"| {', '.join(x['dropped'])} | {x['value']:+.2f} | {x['se']:.2f} | {x['z']:+.2f} | "
                   f"{x['p_refute_holm']:.3g} | {x['verdict_holm']} |")
    st, bs = rob["sign_test_problems"], rob["cluster_bootstrap"]
    out += ["", f"Jackknife over problems: SE {rob['jackknife']['se']:.2f}, z = {rob['jackknife']['z']:+.2f}. Cluster "
                f"bootstrap over problems ({bs['draws']} draws, seed {bs['seed']}): 95% interval of D "
                f"[{bs['ci95'][0]:.2f}; {bs['ci95'][1]:.2f}] pp. Sign of each problem's contribution: {st['positive']} "
                f"positive, {st['negative']} negative, {st['zero']} zero (exact sign test p = {st['p_one_sided']:.2g} "
                f"one-sided, {st['p_two_sided']:.2g} two-sided). \"Clear\" rests on problem "
                f"{rob['drop_top_problems'][0]['dropped'][0]}: without it K3 is "
                f"{rob['drop_top_problems'][0]['verdict_holm']}."]
    return "\n".join(out)


def repeat_lines(results: Path) -> list[str]:
    """Repeated scoring of single steps whose tests are not deterministic (results/scoring-events.json)."""
    ev = read_json(results, "scoring-events.json")
    out = []
    for r in ev["repeated_steps"]:
        counts = ", ".join(f"{v} {n} times" for v, n in sorted(r["rescored"].items()))
        out.append(f"  - *Descriptive:* `{r['model']}` {SETTING_LABEL[r['setting']]} step {r['step']} (officially "
                   f"{r['kept']}; its test checks a simulation the step's code runs on random numbers without a "
                   f"seed) re-scored {r['runs']} times with the same image: {counts}. The refuter reports SciCode-Verified "
                   f"flagging problem {r['step'].split('.')[0]} (not checked here)."
                   + (" A pass there would raise D, not lower it." if r["setting"] == hypotheses.PRIMARY else ""))
    return out


def exploratory_block(results: Path) -> str:
    raw = read_json(results, "raw-outputs.json")["runs"]
    out = ["**EXPLORATORY: added after the results were seen (PROTOCOL.md, Amendment 2); no verdict reads it.** "
           "From the raw outputs (raw_outputs.py), the last answer of each step:", "",
           "| run | setting | answers closing a reasoning block with `</think>` | median share of the answer before "
           "its last `</think>` | passed steps whose answer closes `</think>` |", "|---|---|---|---|---|"]
    for m in RUNS:
        for s in SETTINGS:
            rs = raw[m]["settings"][s]["reasoning"]
            sh = rs["median_share_before_last_think_end"]
            out.append(f"| {m} | {SETTING_LABEL[s]} | {rs['closing_think']} of {rs['answers']} | "
                       f"{'none' if sh is None else f'{100 * sh:.1f}%'} | {rs['passed_closing_think']} of {rs['passed']} |")
    b = raw["bielik-11b-v3.1"]["settings"]
    out += ["", "Bielik's API template ends the prompt with an empty `<think></think>`, so each `</think>` in its "
            f"output is a stray tag it wrote: {b['with_background']['reasoning']['closing_think']} answers with "
            f"background, {b['without_background']['reasoning']['closing_think']} without. The official extraction "
            "reads only the text after it.", "",
            "Empty official extractions (no code at all) and their cause, read from the text the extraction saw "
            "(`lone fence`: exactly one fence line and no ```` ```python ````, so the official rule took the text after "
            "a fence that closes code never opened, here nothing), and over all answers how many have such a lone "
            "fence (where E1 differs) or no fence line:", "",
            "| run | setting | empty extractions | lone fence | unfinished | other | answers with a lone fence | "
            "answers without a fence line |", "|---|---|---|---|---|---|---|---|"]
    for m in RUNS:
        for s in SETTINGS:
            x = raw[m]["settings"][s]["extraction"]
            c = x["empty_by_cause"]
            out.append(f"| {m} | {SETTING_LABEL[s]} | {x['empty_official']} | {len(c.get('lone_fence', []))} | "
                       f"{len(c.get('unfinished', []))} | {len(c.get('other', []))} | {x['answers_lone_fence']} | "
                       f"{x['answers_without_fence_line']} |")
    return "\n".join(out)


def scoring_block(results: Path) -> str:
    ev = read_json(results, "scoring-events.json")
    files = {m: read_json(results, f"{m}.json") for m in RUNS}
    gens = "; ".join(f"{m}: " + ", ".join(f"`{g['code_commit'][:8]}` ({g['at']}, {g['cpu']}"
                                          f"{', ' + g['gpu'] if g['gpu'] else ''}"
                                          f"{', limit ' + str(g['limit']) if g['limit'] else ''})"
                                          for g in f["provenance"]["generation"])
                     for m, f in files.items())
    scoring = {f["provenance"]["scoring"]["code_commit"] for f in files.values()}
    kills = ev["kernel_oom_kills"]
    killed = [f"{m} {p} {step}" for m, passes in ev["scorer_runs_final"].items()
              for p, x in passes.items() for step in x["killed_sigkill"]]
    disk = ev["disk_full_journal"]
    windows = ev["window_rescore"]
    q = [e for e in ev["queue_log"] if e["entry"].startswith("parallel")]
    reuse = "; ".join(f"{m} {SETTING_LABEL[s]}: {f['other_metrics']['extraction_e1'][s]['reused_identical']} reused, "
                      f"{f['other_metrics']['extraction_e1'][s]['scored']} scored"
                      for m, f in files.items() for s in SETTINGS)
    return "\n".join([
        f"- Generation (commit at the start of each session): {gens}.",
        f"- Scoring code: {', '.join(f'`{c}`' for c in sorted(scoring))} for all three runs (final `--score`).",
        f"- Side by side: {q[0]['time'] if q else ''} {q[0]['entry'] if q else ''} — the three models were scored "
        "at the same time in three containers on one VM (results/scoring-vm/score-scicode.log, with the load "
        "average at each start and end); a step near the 1800 s limit can time out under load that it would pass "
        "on an idle machine.",
        f"- Container memory limit {ev['container_memory_limit']}; the official scorer has none. The kernel's OOM "
        f"killer ended {len(kills)} test scripts: " + "; ".join(
            f"{k['time_utc']} UTC (container `{k['container']}`, {k['anon_rss_kb'] / 2 ** 20:.1f} GiB resident)"
            for k in kills) + f". In the final scorer output the killed steps are: {', '.join(killed) or 'none'}; "
        "each counts as a failed step, as the scorer grades it.",
        f"- Disk full: the journal logged {sum(d['lines'] for d in disk)} \"No space left on device\" lines at "
        f"{', '.join(sorted({d['time_utc'] for d in disk}))} UTC. "
        + " ".join(f"Queue log, {e['time']}: {e['entry']}." for e in ev["queue_log"] if "removed" in e["entry"])
        + " The official LFM3 steps whose verdicts were written between 20:10 and 20:20 UTC, and the time-outs that "
        "ran through that window, were re-scored afterwards with the same image and compared with the kept verdicts: "
        + "; ".join(f"{w['model']} {SETTING_LABEL[w['setting']]} ({t}): {w['same']} of {w['steps']} the same"
                    for t, w in windows.items()) + ".",
        f"- E1 identity reuse: {reuse}.",
        *reference_lines(ev),
    ])


def reference_lines(ev: dict[str, Any]) -> list[str]:
    """Deviation: SciCode's gencode.py extracts from the whole answer; we cut after the last `</think>` (PROTOCOL.md)."""
    out = []
    for run, settings in ev["reference_extraction"].items():
        parts = "; ".join(
            f"{SETTING_LABEL[s]}: {x['answers_with_think_end']} answers contain `</think>`, "
            f"{x['answers_whose_code_differs']} give other code, {x['files_differing']} step files differ (with the "
            f"later steps that include that code), passed {x['passed_after_think']} after the last `</think>` and "
            f"{x['passed_whole_answer']} from the whole answer, {x['verdicts_changed']} verdicts change"
            + (f" (the differing files: {', '.join(x['verdicts_of_differing_files'])})" if x['files_differing'] else "")
            for s, x in settings.items())
        out.append(f"- **Extraction after the last `</think>` for a model without thinking.** SciCode @ "
                   "`e3158ea0` hands the whole answer to `extract_python_script` (it knows no `</think>`); PROTOCOL.md "
                   f"cuts after the last `</think>` for every model. Re-scored where it matters for `{run}` "
                   f"(reference_extraction.py on the scoring VM): {parts}. For the LFM3-1.7B runs the reference "
                   "extraction would read the reasoning too; its effect there is not measured.")
    return out


def blocks(results: Path) -> dict[str, str]:
    return {"results": results_block(results), "hypotheses": hypotheses_block(results),
            "exploratory": exploratory_block(results), "scoring": scoring_block(results)}


def render(readme: str, bodies: dict[str, str]) -> str:
    """README text with each block's body replaced; a block whose markers are missing stops the run."""
    for name, body in bodies.items():
        begin, end = markers(name)
        if readme.count(begin) != 1 or readme.count(end) != 1 or readme.index(begin) > readme.index(end):
            sys.exit(f"readme.py: README.md needs exactly one `{begin}` followed by one `{end}`")
        i, j = readme.index(begin) + len(begin), readme.index(end)
        readme = readme[:i] + "\n\n" + body + "\n\n" + readme[j:]
    return readme


def main(results: Path, check: bool) -> int:
    text = README.read_text(encoding="utf-8")
    new = render(text, blocks(results))
    if not check:
        README.write_text(new, encoding="utf-8")
        return 0
    if new != text:
        print("readme.py: README.md differs from the generated blocks; run python3 readme.py", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    argv = sys.argv[1:]
    check = "--check" in argv
    argv = [a for a in argv if a != "--check"]
    sys.exit(main(Path(argv[0]) if argv else HERE / "results", check))
