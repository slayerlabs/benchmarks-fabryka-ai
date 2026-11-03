"""Our EWoK code (benchmarks/ewok/ewok.py) in the settings of the authors' code: no BOS before the context, bf16, batch 1.

Does not change ewok.py: builds its model, casts the weights to bf16 and calls its `score`. The output has the format
of `score` (<out>/ewok.jsonl), so compare.py reads it like any other run.

  python benchmarks/ewok/reference/ours_bf16.py --model <gpt2-xl dir> --out benchmarks/ewok/results/gpt2-xl-bf16
"""
import argparse
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ewok as E  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--batch", type=int, default=1)  # the authors' code: Evaluator(batch_size=1)
    a = p.parse_args()
    model = E.build_model(a.model, "cuda" if torch.cuda.is_available() else "cpu")
    model.m = model.m.to(torch.bfloat16)  # the authors' default hf_precision="bf16"
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    E.score(model, E.load_records(), out / "ewok.jsonl", batch=a.batch)


if __name__ == "__main__":
    main()
