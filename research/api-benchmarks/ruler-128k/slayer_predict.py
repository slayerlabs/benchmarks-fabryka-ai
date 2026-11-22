"""RULER at one length for Slayer, a base model: RULER's raw prompt, greedy, RULER's per-task answer budget.

Usage: python slayer_predict.py --weights DIR --length-dir out/slayer1b-1.09-k70000/4096 --tasks t1 t2 ... --ruler-dir DIR

The model is loaded through research/common/slayer_lm.py (`SlayerLM`, the lm-eval wrapper used by the IFEval
benchmark) and decoded with its greedy `generate`. The prompt is what RULER's call_api.py sends for a base model:
`input + answer_prefix`, no chat template, with the one BOS Slayer gets in lm-eval (`SlayerLM.tok_batch_encode`).
RULER's base template adds no stop words, so a sample ends at end of text or at the answer budget.

Position budget: RULER makes input + answer budget <= max_seq_length tokens (counted without BOS). With BOS the
prompt is input + 1 tokens and the last generated token is never fed back, so the forward needs at most
input + budget <= 4096 positions: every RULER sample at 4096 fits Slayer's block without truncation. The script
checks this per sample and stops instead of truncating.

Raw records: the same format as predict.py ("finish_reason" is "stop" at end of text, else "length").
"""

import argparse
import json
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
COMMON_DIR = HERE.parents[1] / "common"
sys.path.insert(0, str(COMMON_DIR))

import slayer_lm  # noqa: E402  research/common: loads Slayer weights and tokenizer, greedy generate
from ruler import answer_budgets, latest_records, read_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True, help="converted Slayer directory (model.safetensors, config.json, "
                    "tokenizer.json), e.g. .cache/slayer1b-1.09-k70000 from run.sh")
    ap.add_argument("--length-dir", type=Path, required=True)
    ap.add_argument("--tasks", nargs="+", required=True)
    ap.add_argument("--ruler-dir", type=Path, required=True)
    ap.add_argument("--dtype", default="bfloat16")
    args = ap.parse_args()

    budgets = answer_budgets(args.ruler_dir)
    lm = slayer_lm.SlayerLM(pretrained=args.weights, dtype=args.dtype, device="cuda")
    tokenizer, model = lm.tokenizer, lm.model
    block, bos = model.slayer.blok, model.slayer.bos
    raw_dir = args.length_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    for task in args.tasks:
        samples = read_jsonl(args.length_dir / "data" / task / "validation.jsonl")
        if not samples:
            sys.exit(f"slayer_predict.py: no data for {task}")
        raw_file = raw_dir / f"{task}.jsonl"
        done = {i for i, r in latest_records(raw_file).items() if "output" in r}
        todo = [s for s in samples if s["index"] not in done]
        print(f"slayer_predict.py: {task}: {len(samples) - len(todo)} done, {len(todo)} to generate")
        with open(raw_file, "a", encoding="utf-8", buffering=1) as f:
            for sample in todo:
                ids = [lm.prefix_token_id] + tokenizer.encode(sample["input"] + sample["answer_prefix"],
                                                              add_special_tokens=False)
                if len(ids) - 1 + budgets[task] > block:
                    sys.exit(f"slayer_predict.py: {task} #{sample['index']}: {len(ids) - 1} input tokens + "
                             f"budget {budgets[task]} > block {block}; RULER data and Slayer tokenizer disagree")
                prompt = torch.tensor([ids], device="cuda")
                out = model.generate(prompt, max_length=len(ids) + budgets[task])[0, len(ids):].tolist()
                stopped = bos in out
                if stopped:
                    out = out[:out.index(bos)]
                record = {"index": sample["index"], "output": tokenizer.decode(out, skip_special_tokens=True),
                          "finish_reason": "stop" if stopped else "length", "prompt_tokens": len(ids),
                          "output_tokens": len(out)}
                f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
