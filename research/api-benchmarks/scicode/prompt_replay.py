"""Replay the prompts of the committed runs through the pinned SciCode harness.

The results keep the model's answer of every subproblem, not the prompt. This rebuilds the prompt Gencode
sent for each subproblem from those answers: the code of the earlier steps goes into `previous_llm_code`,
exactly as the resume path of `scicode_runner.Generator.run` does, so a prompt here is the prompt of the
run (the harness at the pinned commit builds it; `test_scicode.py` checks that path against SciCode's own
uninterrupted flow). The model call is a stub; right after each call the recorded code is put back, so the
next prompt carries the code of the real run.

Used for two notes in README.md: five subproblems read by hand per model (rule: read tasks by hand before
trusting a run) and how many prompts do not fit Slayer 1B's 4096-token context (the benchmark is not cut
to fit).

Writes `.cache/prompt-replay/<run>/prompts/<run>/<setting>/<problem>.<step>.txt` (gitignored). Needs the
SciCode clone and the pinned dataset, both made by `run.sh`, and `.venv-gen`:

    .venv-gen/bin/python prompt_replay.py                 # replay, then the Slayer-context counts
    .venv-gen/bin/python prompt_replay.py --reuse         # only the counts, prompts already there
    .venv-gen/bin/python prompt_replay.py --hand 77.1 13.1 42.3 65.4 11.3
"""
import argparse
import gzip
import json
import os
import shutil
import statistics
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

import scicode_runner as sr  # noqa: E402

RUNS = ("lfm3-1.7b", "lfm3-1.7b-nothink", "bielik-11b-v3.1")
SETTINGS = ("with_background", "without_background")
OUT = BENCH / ".cache" / "prompt-replay"
SLAYER_TOKENIZER = BENCH.parent.parent / "slayer-1b" / "tokenizer" / "tokenizer.json"
SLAYER_CONTEXT = 4096


def load(run: str) -> dict[tuple[str, str, int], dict]:
    out = {}
    with gzip.open(BENCH / "results" / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[(r["setting"], r["problem_id"], int(r["step"]))] = r
    return out


def replay() -> None:
    os.environ.setdefault("HF_HOME", str(sr.HF_CACHE))
    h = sr.harness()
    problems = sr.load_split("test", None)
    shutil.rmtree(OUT, ignore_errors=True)
    for run in RUNS:
        answers = load(run)
        captured: dict[str, str] = {}

        def respond(prompt: str, ctx: dict, _cap: dict = captured) -> dict:
            _cap[f"{ctx['setting']}/{ctx['problem_id']}.{ctx['step']}"] = prompt
            return {"status": "ok", "output": "```python\n# prompt replay placeholder\n```\n",
                    "finish_reason": "stop", "unfinished": False, "output_tokens": None,
                    "prompt_tokens": None}

        gen = sr.Generator(h, OUT / run, run, respond, thinking=True)
        total = 0
        for setting in SETTINGS:
            with_background = setting == "with_background"
            template = (h.gencode.BACKGOUND_PROMPT_TEMPLATE if with_background
                        else h.gencode.DEFAULT_PROMPT_TEMPLATE)
            for prob in problems:
                pid, steps = prob["problem_id"], len(prob["sub_steps"])
                gcode = h.gencode.Gencode(model=run, output_dir=OUT / run / "generated_code",
                                          prompt_dir=OUT / run / "prompts",
                                          with_background=with_background, temperature=sr.TEMPERATURE)
                gcode.previous_llm_code = [None] * steps
                for i in range(steps):
                    step = i + 1
                    if (pid, step) in sr.HARNESS_STEPS:
                        continue
                    gen.local.ctx = {"setting": setting, "problem_id": pid, "step": step,
                                     "sub_step": prob["sub_steps"][i]}
                    h.gencode.Gencode.generate_response_with_steps(gcode, prob, step, steps, run, template)
                    gcode.previous_llm_code[i] = answers[(setting, pid, step)]["output"]  # the run's code
                    text = captured[f"{setting}/{pid}.{step}"]
                    path = OUT / run / "prompts" / run / setting / f"{pid}.{step}.txt"
                    assert path.read_text(encoding="utf-8") == text, f"prompt file differs: {path}"
                    total += 1
        print(f"{run}: {total} prompts replayed", flush=True)


def context_counts() -> None:
    from tokenizers import Tokenizer

    tok = Tokenizer.from_file(str(SLAYER_TOKENIZER))
    print(f"prompts over Slayer 1B's {SLAYER_CONTEXT} tokens, counted with Slayer's own tokenizer "
          f"({tok.get_vocab_size()} tokens):")
    for run in RUNS:
        for setting in SETTINGS:
            files = sorted((OUT / run / "prompts" / run / setting).glob("*.txt"))
            counts = [(f.stem, len(tok.encode(f.read_text(encoding="utf-8"), add_special_tokens=False).ids))
                      for f in files]
            over = [(stem, n) for stem, n in counts if n > SLAYER_CONTEXT]
            problems = sorted({stem.rsplit(".", 1)[0] for stem, _ in over})
            print(f"  {run:20} {setting:18} over {SLAYER_CONTEXT}: {len(over)}/{len(counts)} steps, "
                  f"{len(problems)}/65 problems, median {statistics.median(n for _, n in counts):.0f}, "
                  f"max {max(n for _, n in counts)}")


def hand(picks: list[str]) -> None:
    for run in RUNS:
        rows = {r["task_id"].split("/", 1)[1]: r for r in load(run).values()
                if r["setting"] == "with_background"}
        print("=" * 15, run, "with background")
        for p in picks:
            r = rows.get(p)
            if r is None:
                print(f"  {p}: not in this run")
                continue
            txt = (OUT / run / "prompts" / run / "with_background" / f"{p}.txt").read_text(encoding="utf-8")
            heads = [line for line in txt.splitlines() if line.isupper() and len(line) > 8]
            print(f"  {p}: score={r['score']} verdict={r['verdict']} prompt_chars={len(txt)} "
                  f"prompt_tokens={r['prompt_tokens']} out_tokens={r['output_tokens']} sections={heads}")
            print("    prompt tail:", repr(txt[-300:]))
            print("    output head:", repr((r["output"] or "")[:200]))
        passed = sorted(k for k, v in rows.items() if v["score"] == 1)
        print(f"  passes with background: {len(passed)}/288, first: {passed[:8]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reuse", action="store_true", help="do not replay; use the prompts already in .cache")
    ap.add_argument("--hand", nargs="+", metavar="PROBLEM.STEP",
                    help="print prompt, committed output and verdict for these subproblems")
    args = ap.parse_args()
    if not args.reuse:
        replay()
    elif not (OUT / RUNS[0]).is_dir():
        sys.exit("prompt_replay.py: no prompts in .cache/prompt-replay; run without --reuse")
    if args.hand:
        hand(args.hand)
    else:
        context_counts()


if __name__ == "__main__":
    main()
