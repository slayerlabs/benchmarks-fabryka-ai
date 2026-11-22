"""Writes the generated blocks of README.md from results/, so no number in them is typed by hand.

Usage: python3 readme.py [results-dir] [--check]   (default: results/ next to this file)

Blocks, each between `<!-- readme.py: NAME ... -->` and `<!-- readme.py: end NAME -->`:
- `results`: one row per run from results/<model-id>.json (score, stderr, n, mean output tokens, date) with each
  row's thinking mode, serving and output limit; the secondary score; accepted/n per difficulty; the judge
  categories; output tokens, unfinished answers, length stops and answers containing `<think>`; baselines; the
  judge machine; where the raw outputs are (results/raw-outputs.json) and why answers had no code;
- `hypotheses`: compare.py's report of results/hypotheses.json, verbatim, and what K2 and K3 compare;
- `exploratory`: results/exploratory.json (explore.py), labelled as added after the results were seen.
Every file read must have the sha256 its writer recorded in results/manifest.json. `--check` writes nothing and
exits 1 when README.md differs from what this would write; the tests make the same comparison byte for byte.
"""

import json
import sys
from pathlib import Path
from typing import Any

import compare
import explore
import provenance

HERE = Path(__file__).resolve().parent
README = HERE / "README.md"
RUNS = {
    "lfm3-1.7b": ("LFM3-1.7B (`lfm3-1.7b`)", "on (template default)", "vLLM 0.34.0, bf16, H100"),
    "lfm3-1.7b-nothink": ("LFM3-1.7B (`lfm3-1.7b-nothink`)", "off requested (`enable_thinking: false`)",
                          "the same vLLM server"),
    "bielik-11b-v3.1": ("Bielik 11B v3.1 (`bielik-11b-v3.1`)", "none (the API has no switch)",
                        "Fabryka AI API, with the API's provider system prompt"),
}
NOT_RUN = ("Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`)", "slayer1b-1.09-k70000")
CATEGORY_LABELS = {"accepted": "AC", "wrong_answer": "WA", "time_limit": "TLE", "memory_limit": "MLE",
                   "runtime_error": "RE", "output_limit": "OLE", "compile_error": "CE", "no_code": "no code",
                   "unfinished": "unfinished", "no_tests": "no tests", "judge_error": "judge error",
                   "request_error": "request error", "unsupported": "over context"}
NO_CODE_LABELS = {"python_fence": "a ```python block instead of C++", "tool_call": "a `<tool_call>` instead of an answer",
                  "length_stop": "cut by the output limit inside the code", "other": "other"}
CAUSE_LABELS = {"compiler_says_missing_include": "g++ names the missing header",
                "undeclared_std_name": "a standard-library name used without its header",
                "other": "other (syntax, types, undefined own names)"}


def markers(name: str) -> tuple[str, str]:
    return (f"<!-- readme.py: {name} (generated from results/ by readme.py; edit readme.py, not this block) -->",
            f"<!-- readme.py: end {name} -->")


def read_json(results: Path, name: str) -> dict[str, Any]:
    provenance.verify(results, [name], "readme.py")
    return json.loads((results / name).read_text(encoding="utf-8"))


def cell(x: dict[str, Any]) -> str:
    return f"{x['score']:.2f} ± {x['stderr']:.2f} ({x['accepted']}/{x['n']})"


def results_block(results: Path) -> str:
    files = {m: read_json(results, f"{m}.json") for m in RUNS}
    raw = read_json(results, "raw-outputs.json")
    slayer = read_json(results, f"{NOT_RUN[1]}.json")
    out = ["| model | thinking | serving | output limit | accepted (%) | stderr | n | mean output tokens | date |",
           "|---|---|---|---|---|---|---|---|---|"]
    for m, (name, thinking, serving) in RUNS.items():
        r = files[m]
        limit = f"{r['settings']['max_tokens']} (context {r['settings']['context']})"
        out.append(f"| {name} | {thinking} | {serving} | {limit} | {r['score']:.2f} | {r['stderr']:.2f} | {r['n']} | "
                   f"{r['other_metrics']['output_tokens']['mean']:.1f} | {r['date']} |")
    out.append(f"| {NOT_RUN[0]} | | | | null ({slayer['reason']}) | | | | |")
    out += ["", "Accepted (%) ± stderr (accepted/n): all problems (headline), without the problems whose test zip is "
            "missing or whose judging or request failed (secondary), and per difficulty:", "",
            "| run | all | secondary | left out of secondary | easy | medium | hard |", "|---|---|---|---|---|---|---|"]
    for m, r in files.items():
        o = r["other_metrics"]
        left = ", ".join(f"{k} {v}" for k, v in o["secondary"]["left_out"].items() if v) or "none"
        out.append(f"| {m} | {cell({**o, 'score': r['score'], 'stderr': r['stderr'], 'n': r['n']})} | "
                   f"{cell(o['secondary'])} | {left} | "
                   + " | ".join(cell(o["per_difficulty"][d]) for d in ("easy", "medium", "hard")) + " |")
    out += ["", "Judge categories (problems):", "",
            "| run | " + " | ".join(CATEGORY_LABELS.values()) + " |", "|---|" + "---|" * len(CATEGORY_LABELS)]
    for m, r in files.items():
        c = r["other_metrics"]["categories"]
        out.append(f"| {m} | " + " | ".join(str(c[k]) for k in CATEGORY_LABELS) + " |")
    out += ["", "| run | output tokens mean / median / max | unfinished (thinking on) | stopped by the length limit | "
            "answers containing `<think>` |", "|---|---|---|---|---|"]
    for m, r in files.items():
        o = r["other_metrics"]
        t, th = o["output_tokens"], o["think_in_output"]
        out.append(f"| {m} | {t['mean']:.1f} / {t['median']} / {t['max']} | {o['unfinished']} | {o['length_stops']} | "
                   f"{th['answers']} of {th['of']} ({100 * th['share']:.1f}%) |")
    judges = {json.dumps(r["settings"]["judge"], sort_keys=True) for r in files.values()}
    machines = {json.dumps(r["settings"]["judge_machine"], sort_keys=True) for r in files.values()}
    if len(judges) != 1 or len(machines) != 1:
        sys.exit("readme.py: the runs were judged with different images or on different machines")
    j, mach = files["lfm3-1.7b"]["settings"]["judge"], files["lfm3-1.7b"]["settings"]["judge_machine"]
    out += ["", "Baselines: 0 for random and majority answers (no fixed output passes a problem's hidden tests). "
            f"The LFM3-1.7B card reports {100 * compare.CARD_LFM3:.2f}; the control is in Hypotheses.",
            "", f"Judge: all three runs on one machine, one after another: {mach['cpu']}, {mach['cpu_count']} vCPUs, "
            f"{j['workers']} judge workers, image `{j['image_id']}`, go-judge {j['go_judge_version']}.",
            "", f"Raw outputs (with thinking, not committed): the LFM3-1.7B runs in `{raw['archive']['file']}`, "
            f"sha256 `{raw['archive']['sha256']}`; Bielik's in `{raw['runs']['bielik-11b-v3.1']['file']}`. Each "
            "run's generations.jsonl sha256 equals its result file's `raw_outputs.sha256` (results/raw-outputs.json)."]
    for m in RUNS:
        causes = raw["runs"][m]["no_code"]
        if causes:
            parts = "; ".join(f"{NO_CODE_LABELS[c]}: {len(ids)} ({', '.join(ids)})" for c, ids in causes.items())
            out += ["", f"No code extracted, `{m}`: {parts}."]
    return "\n".join(out)


def hypotheses_block(results: Path) -> str:
    h = read_json(results, "hypotheses.json")
    on = read_json(results, "lfm3-1.7b-nothink.json")["other_metrics"]
    th, tok = on["think_in_output"], on["output_tokens"]
    k3 = next(x for x in h["hypotheses"] if x["id"] == "K3")
    return "\n".join([
        compare.report(h), "",
        "What K2 and K3 compare:", "",
        "- **K2 compares Bielik through the API with a number on the card**, not with a model run here: LFM2.5-2.6B's "
        f"{100 * compare.CARD_WEAKEST:.2f}, with the SE floor of PROTOCOL.md.",
        "- **K3 compares thinking modes of one model, not models.** \"Off\" is `enable_thinking: false`; "
        f"`lfm3-1.7b-nothink` still wrote {tok['mean']:.0f} output tokens per answer on average (median "
        f"{tok['median']}), and {th['answers']} of its {th['of']} answers contain `<think>`, so \"off\" is not "
        f"\"no reasoning\". K3's D is {k3['value']:+.2f} ± {k3['se']:.2f} pp, from accepted shares of "
        f"{k3['on']:.2f}% (on), {k3['off']:.2f}% (off) and {k3['bielik']:.2f}% (Bielik).",
        "- **Holm over the Coding group** needs SciCode's K2 and K3 (`python3 compare.py results --group "
        "<SciCode hypotheses.json>`); until then they count with p = 1, which can only make the adjusted p larger.",
    ])


def exploratory_block(results: Path) -> str:
    e = read_json(results, "exploratory.json")
    b = e["budgets"]
    out = ["**EXPLORATORY: added after the results were seen; not in PROTOCOL.md, no verdict reads it.**", "",
           "Accepted within an output budget (a problem counts only if it was accepted and its answer used at most B "
           "output tokens, thinking included):", "",
           "| run | " + " | ".join(f"B = {t}" for t in b["tokens"]) + " | no limit | n |",
           "|---|" + "---|" * (len(b["tokens"]) + 2)]
    for m in explore.RUNS:
        r = read_json(results, f"{m}.json")
        out.append(f"| {m} | " + " | ".join(str(b["accepted"][m][str(t)]) for t in b["tokens"]) +
                   f" | {r['other_metrics']['accepted']} | {b['n'][m]} |")
    out += ["", "Compile errors by cause, from the judge's compiler message (explore.py: the compiler's own "
            "\"did you forget to '#include'\" note; else a first error naming an undeclared standard-library name "
            "from a fixed list; else other):", "",
            "| run | compile errors | " + " | ".join(CAUSE_LABELS.values()) + " |",
            "|---|---|" + "---|" * len(CAUSE_LABELS)]
    for m, c in e["compile_errors"].items():
        out.append(f"| {m} | {c['total']} | " + " | ".join(str(c["by_cause"][k]["count"]) for k in CAUSE_LABELS) + " |")
    return "\n".join(out)


def blocks(results: Path) -> dict[str, str]:
    return {"results": results_block(results), "hypotheses": hypotheses_block(results),
            "exploratory": exploratory_block(results)}


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
