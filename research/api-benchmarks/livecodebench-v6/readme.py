"""Writes the generated blocks of README.md from results/, so no number in them is typed by hand.

Usage: python3 readme.py [results-dir] [--check]   (default: results/ next to this file)

Blocks, each between `<!-- readme.py: NAME ... -->` and `<!-- readme.py: end NAME -->`:
- `results`: one row per run from results/<model-id>.json (pass@1, stderr, n, mean output tokens, date) with the
  thinking mode, serving and output limit of each row, the breakdown per difficulty, v6-only and budget, and the
  consequence of Amendment 4 from results/ablation-a1.json;
- `hypotheses`: compare.py's report of results/hypotheses.json, verbatim, then what L1-L3 compare (modes, the cost
  of the "equal cost" pair, the prompt the cost leaves out), with the numbers from the same file;
- `ablation`: results/ablation-a1.md, verbatim.
Every file read must have the sha256 its writer recorded in results/manifest.json. `--check` writes nothing and
exits 1 when README.md differs from what this would write; the tests make the same comparison byte for byte.
"""

import json
import sys
from pathlib import Path
from typing import Any

import compare
import provenance

HERE = Path(__file__).resolve().parent
README = HERE / "README.md"
BLOCKS = ("results", "hypotheses", "ablation")

# Per run: name, thinking mode and serving. Thinking: LFM3-1.7B's template thinks by default (its answers carry
# `</think>`); the Fabryka API renders Bielik's template with `reasoning_effort` none and rejects every reasoning
# switch (README, Deviations). The output limit comes from the result file's settings.
RUNS = {
    "lfm3-1.7b": ("LFM3-1.7B (`lfm3-1.7b`, the verdict run of L1-L3)",
                  "thinks (template default)",
                  "vLLM 0.34.0, bf16; `repetition_penalty` 1.1 and `top_k` 50 from `generation_config.json` "
                  "(Amendment 3)"),
    "lfm3-1.7b-cardsampling": ("LFM3-1.7B with the card's sampling (`lfm3-1.7b-cardsampling`, Amendment 4)",
                               "thinks (template default)",
                               "vLLM 0.34.0, bf16; `repetition_penalty` 1.0 and `top_k` 0 in the request"),
    "bielik-11b-v3.1": ("Bielik 11B v3.1 (`bielik-11b-v3.1`)",
                        "does not think (API default `reasoning_effort` none: empty `<think></think>`)",
                        "Fabryka AI API, with the API's hidden provider system prompt"),
}
NOT_RUN = [("Slayer 1B 1.09 at update 70 000 (`slayer1b-1.09-k70000`)", "not run, see Deviations")]


def markers(name: str) -> tuple[str, str]:
    return (f"<!-- readme.py: {name} (generated from results/ by readme.py; edit readme.py, not this block) -->",
            f"<!-- readme.py: end {name} -->")


def read_json(results: Path, name: str) -> dict[str, Any]:
    provenance.verify(results, [name], "readme.py")
    return json.loads((results / name).read_text(encoding="utf-8"))


def cell(x: dict[str, Any]) -> str:
    return f"{x['score']:.2f} ± {x['stderr']:.2f} ({x['n']})"


def results_block(results: Path) -> str:
    out = ["| model | thinking | serving | output limit | pass@1 (%) | stderr | n | mean output tokens | date |",
           "|---|---|---|---|---|---|---|---|---|"]
    files = {m: read_json(results, f"{m}.json") for m in RUNS}
    for m, (name, thinking, serving) in RUNS.items():
        r = files[m]
        limit = f"{r['settings']['max_tokens']} (context {r['settings']['context']})"
        out.append(f"| {name} | {thinking} | {serving} | {limit} | {r['score']:.2f} | {r['stderr']:.2f} | {r['n']} | "
                   f"{r['other_metrics']['output_tokens']['mean']:.1f} | {r['date']} |")
    out += [f"| {name} | | | | null ({reason}) | | | | |" for name, reason in NOT_RUN]
    out += ["", "pass@1 (%) ± stderr (n) by difficulty, on the v6-only problems, and within an output budget (an "
            "answer counts only if it passed, finished, and used at most that many tokens):", "",
            "| run | easy | medium | hard | v6-only | within 4096 tokens | within 16384 tokens |",
            "|---|---|---|---|---|---|---|"]
    for m, r in files.items():
        o = r["other_metrics"]
        out.append(f"| {m} | " + " | ".join(cell(o["per_difficulty"][lvl]) for lvl in compare.DIFFICULTIES) +
                   f" | {cell(o['v6_only'])} | {cell(o['pass_at_budget']['4096'])} | "
                   f"{cell(o['pass_at_budget']['16384'])} |")
    ablation = read_json(results, "ablation-a1.json")
    out += ["", "Baselines: 0 for random and majority answers (no fixed output passes a problem's hidden tests). "
            f"The LFM3-1.7B card reports {compare.CONTROL_CARD}; the control is in Hypotheses.",
            "", f"Amendment 4: {ablation['consequence']} (Ablation below)."]
    return "\n".join(out)


def equal_cost_lines(run: str, e: dict[str, Any]) -> list[str]:
    ratio = e["mean_cost_b"] / e["mean_cost_a"]
    with_prompt = e["mean_cost_with_prompt_b"] / e["mean_cost_with_prompt_a"]
    prompts = e["mean_prompt_tokens_b"] / e["mean_prompt_tokens_a"]
    return [
        f"- **The \"equal cost\" pair of L3 on `{run}` is not of equal cost.** It is the closest of the nine budget "
        f"pairs: LFM3-1.7B at B = {compare.budget(e['budget_a'])} and Bielik at B = {compare.budget(e['budget_b'])}, "
        f"mean costs {e['mean_cost_a']:.3g} vs {e['mean_cost_b']:.3g} FLOPs, so Bielik's mean cost is "
        f"{100 * abs(ratio - 1):.1f}% {'above' if ratio > 1 else 'below'} LFM3-1.7B's (ratio {ratio:.3f}). "
        "PROTOCOL.md takes the closest pair and sets no tolerance, "
        "so L3 is read at this pair as written, with costs this far apart.",
        f"- **The prompt is left out of that cost** (PROTOCOL.md: \"prompt tokens are shared by all models\"), but the "
        f"prompts differ: Bielik's average {e['mean_prompt_tokens_b']:.0f} tokens (its template with the API's "
        f"provider system prompt, counted locally), LFM3-1.7B's {e['mean_prompt_tokens_a']:.0f}, {prompts:.2f}×. "
        f"With the prompt counted (2 × parameters × (prompt + output tokens)) the same pair costs "
        f"{e['mean_cost_with_prompt_a']:.3g} vs {e['mean_cost_with_prompt_b']:.3g} FLOPs (ratio {with_prompt:.3f}).",
    ]


def hypotheses_block(results: Path) -> str:
    h = read_json(results, "hypotheses.json")
    out = [compare.report(h), "", "What L1-L3 compare:", "",
           "- **Modes, not model sizes.** LFM3-1.7B thinks before it answers (its template's default; the answer is "
           "the text after `</think>`); Bielik 11B v3.1 through the Fabryka API does not (the API's default "
           "`reasoning_effort` is `none`, which renders an empty `<think></think>`, and it rejects every reasoning "
           "switch), and it runs with the API's hidden provider system prompt, LFM3-1.7B on our vLLM. L1-L3 compare "
           "a thinking 1.7B model with a non-thinking 11B model served another way: a comparison of modes (and "
           "serving), not of models of two sizes, and they say nothing about size alone."]
    runs = [(h["verdict_run"], h["hypotheses"])]
    if h["other_run"]:
        runs.append((h["other_run"]["run"], h["other_run"]["hypotheses"]))
    for run, rows in runs:
        l3 = next(r for r in rows if r["id"] == "L3")
        if "mean_cost_a" in l3:
            out += equal_cost_lines(run, l3)
    return "\n".join(out)


def ablation_block(results: Path) -> str:
    provenance.verify(results, ["ablation-a1.md"], "readme.py")
    return (results / "ablation-a1.md").read_text(encoding="utf-8").rstrip("\n")


def blocks(results: Path) -> dict[str, str]:
    return {"results": results_block(results), "hypotheses": hypotheses_block(results),
            "ablation": ablation_block(results)}


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
    if new == text:
        return 0
    a, b = text.splitlines(), new.splitlines()
    line = next((i for i, (x, y) in enumerate(zip(a, b), 1) if x != y), min(len(a), len(b)) + 1)
    print(f"readme.py: README.md differs from the generated blocks (first at line {line}); run python3 readme.py")
    return 1


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--check"]
    sys.exit(main(Path(args[0]) if args else HERE / "results", "--check" in sys.argv[1:]))
