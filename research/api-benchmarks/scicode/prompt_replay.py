"""Replay the prompts of the committed runs through the pinned SciCode harness, and count them for Slayer 1B.

The results keep the model's answer of every subproblem, not the prompt. This rebuilds the prompt Gencode
sent for each subproblem from those answers: the code of the earlier steps goes into `previous_llm_code`,
exactly as the resume path of `scicode_runner.Generator.run` does, so a prompt here is the prompt of the run
(the harness at the pinned commit builds it; `test_scicode.py` checks that path against SciCode's own
uninterrupted flow). The model call is a stub; right after each call the recorded code is put back, so the
next prompt carries the code of the real run.

Used for three notes in README.md: five subproblems read by hand per model (rule: read tasks by hand before
trusting a run), how many prompts do not fit Slayer 1B's 4096-token context, and the pre-run
`context_overflow` counts of the Slayer run (prompts that leave fewer than 256 tokens for the answer; the
benchmark is not cut to fit).

Counts use the tokenizer of the pinned Slayer 1.08 template (v6, 32768 tokens; METODOLOGIA, "Wspólny rdzeń"),
with the one leading BOS every request carries (research/common/slayer_lm.py). `--fetch-tokenizer` downloads
just `tokenizer.json` and `config.json` of that template into `.cache/slayer-tokenizer/`.

Writes `.cache/prompt-replay/<run>/prompts/<run>/<setting>/<problem>.<step>.txt` (gitignored). Needs the
SciCode clone and the pinned dataset, both made by `run.sh`, and `.venv-gen`:

    .venv-gen/bin/python prompt_replay.py --fetch-tokenizer   # once
    .venv-gen/bin/python prompt_replay.py                     # replay, then the Slayer-context counts
    .venv-gen/bin/python prompt_replay.py --reuse             # only the counts, prompts already there
    .venv-gen/bin/python prompt_replay.py --hand 77.1 13.1 42.3 65.4 11.3
"""
import argparse
import gzip
import hashlib
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
SLAYER_DIR = BENCH / ".cache" / "slayer-tokenizer"
SLAYER_TOKENIZER = SLAYER_DIR / "tokenizer.json"
SLAYER_TEMPLATE_REPO = "SlayerLab/Slayer1B-1.08"
SLAYER_TEMPLATE_REVISION = "5f854a0cc7160594d54d1788d37a44e8ebabe16c"
SLAYER_CONTEXT = 4096
SLAYER_MIN_ANSWER_TOKENS = 256  # rule: a prompt must leave at least this much room for the answer
BOS_PER_REQUEST = 1  # research/common/slayer_lm.py: "exactly one leading BOS per request"


def load(run: str) -> dict[tuple[str, str, int], dict]:
    out = {}
    with gzip.open(BENCH / "results" / f"{run}.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[(r["setting"], r["problem_id"], int(r["step"]))] = r
    return out


def fetch_tokenizer() -> None:
    from huggingface_hub import hf_hub_download

    SLAYER_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("tokenizer.json", "config.json"):
        path = Path(hf_hub_download(SLAYER_TEMPLATE_REPO, name, revision=SLAYER_TEMPLATE_REVISION,
                                    local_dir=str(SLAYER_DIR)))
        print(f"{name}: sha256 {hashlib.sha256(path.read_bytes()).hexdigest()}, {path.stat().st_size} bytes")
    cfg = json.loads((SLAYER_DIR / "config.json").read_text(encoding="utf-8"))
    print("template config:", {k: cfg.get(k) for k in ("block", "n_layer", "n_embd", "vocab")})


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

    if not SLAYER_TOKENIZER.is_file():
        sys.exit(f"prompt_replay.py: {SLAYER_TOKENIZER} is missing; run with --fetch-tokenizer first")
    tok = Tokenizer.from_file(str(SLAYER_TOKENIZER))
    print(f"prompts of the harness, counted with the Slayer 1.08 template tokenizer "
          f"(v6, {tok.get_vocab_size()} tokens) plus one leading BOS:")
    print(f"  'over {SLAYER_CONTEXT}' is a prompt that cannot be sent at all; "
          f"'overflow' is the run's rule: fewer than {SLAYER_MIN_ANSWER_TOKENS} tokens left for the answer")
    for run in RUNS:
        for setting in SETTINGS:
            files = sorted((OUT / run / "prompts" / run / setting).glob("*.txt"))
            counts = [(f.stem, BOS_PER_REQUEST
                       + len(tok.encode(f.read_text(encoding="utf-8"), add_special_tokens=False).ids))
                      for f in files]
            over = [stem for stem, n in counts if n > SLAYER_CONTEXT]
            overflow = [stem for stem, n in counts if n > SLAYER_CONTEXT - SLAYER_MIN_ANSWER_TOKENS]
            problems = sorted({stem.rsplit(".", 1)[0] for stem in overflow})
            print(f"  {run:20} {setting:18} n={len(counts)}  over {SLAYER_CONTEXT}: {len(over)}  "
                  f"overflow (<{SLAYER_MIN_ANSWER_TOKENS} left): {len(overflow)} in {len(problems)}/65 problems  "
                  f"median {statistics.median(n for _, n in counts):.0f}  max {max(n for _, n in counts)}")
            print(f"      overflow ids: {', '.join(overflow)}")


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
    ap.add_argument("--fetch-tokenizer", action="store_true",
                    help="download tokenizer.json and config.json of the pinned Slayer 1.08 template")
    ap.add_argument("--reuse", action="store_true", help="do not replay; use the prompts already in .cache")
    ap.add_argument("--hand", nargs="+", metavar="PROBLEM.STEP",
                    help="print prompt, committed output and verdict for these subproblems")
    args = ap.parse_args()
    if args.fetch_tokenizer:
        fetch_tokenizer()
        return
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
