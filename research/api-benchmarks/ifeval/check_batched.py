"""Compares batched generation (lm_eval_slayer.py) with the per-row one (slayer_lm) on IFEval prompts.

Usage: python check_batched.py <weights dir> [n_prompts] [max_new_tokens] [dtype]
Prints, per prompt, whether the greedy tokens match and from which token they differ, and the time of each.
"""

import sys
import time

import torch
from datasets import load_dataset

import lm_eval_slayer
import slayer_lm
import slayer_model

REVISION = "966cd89545d6b6acfd7638bc708b98261ca58e84"


def main():
    weights = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    new = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    dtype = getattr(torch, sys.argv[4]) if len(sys.argv) > 4 else torch.bfloat16
    module = slayer_lm._SlayerModule(slayer_model.Slayer(weights, device="cuda", dtype=dtype))
    prompts = load_dataset("google/IFEval", revision=REVISION, split="train")["prompt"][:n]
    rows = [module.slayer.encode(p) for p in prompts]
    width = max(map(len, rows)) + 1
    # The layout SlayerLM.tok_batch_encode gives lm-eval: BOS first, then the left padding, then the prompt.
    ids = torch.tensor([[module.slayer.bos] + [0] * (width - 1 - len(r)) + r for r in rows], device="cuda")
    mask = torch.tensor([[1] + [0] * (width - 1 - len(r)) + [1] * len(r) for r in rows], device="cuda")
    out = {}
    for name, fn in (("per-row", lm_eval_slayer._per_row_generate), ("batched", lm_eval_slayer.generate)):
        torch.cuda.synchronize()
        t = time.perf_counter()
        out[name] = fn(module, ids, attention_mask=mask, max_length=width + new)[:, width:]
        torch.cuda.synchronize()
        print(f"{name}: {time.perf_counter() - t:.1f} s for {n} prompts x up to {new} tokens")
    a, b = out["per-row"], out["batched"]
    cols = max(a.shape[1], b.shape[1])  # the loops may stop at different steps once outputs diverge
    a, b = (torch.nn.functional.pad(x, (0, cols - x.shape[1]), value=-1) for x in (a, b))
    for i in range(n):
        diff = (a[i] != b[i]).nonzero()
        where = "same" if not len(diff) else f"differs from token {int(diff[0])}"
        print(f"prompt {i} (len {len(rows[i]) + 1}): {where}")


if __name__ == "__main__":
    main()
