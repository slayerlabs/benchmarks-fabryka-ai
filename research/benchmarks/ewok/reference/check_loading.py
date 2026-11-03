"""Loading check before an EWoK run (local, no EWoK data).

1. Missing and unexpected weight keys (`from_pretrained(..., output_loading_info=True)`).
2. The scorer path of ewok.py (hidden states, then the head on the target positions) gives the same logits as
   `model(ids).logits`.

  python benchmarks/ewok/reference/check_loading.py --model <dir> [--out <file.json>]
"""
import argparse
import gc
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ewok as E  # noqa: E402
from hipoteza_formatu import para  # noqa: E402

# made-up sentences, not EWoK records
SENTENCES = [("The cup is on the table.", "Anna sees the cup."), ("Tom is sleeping.", "Tom hears the alarm."),
             ("The box is heavy.", "Ola lifts the box easily."), ("It is raining.", "The street is wet.")]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--out")
    a = p.parse_args()
    from transformers import AutoModelForCausalLM
    tmp, info = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float32, trust_remote_code=True,
                                                     output_loading_info=True)
    keys = {k: sorted(v) if isinstance(v, (set, list)) else str(v) for k, v in info.items()}
    cls = type(tmp).__name__
    del tmp  # one copy of the weights in RAM at a time
    gc.collect()
    m = E.build_model(a.model, "cuda" if torch.cuda.is_available() else "cpu")
    diff = 0.0
    for c, t in SENTENCES:
        ce, co = para(m, c, " " + t)
        ids = torch.tensor([ce + co], device=m.device)
        with torch.no_grad():
            full = m.logits(ids)[0, len(ce) - 1:-1]
            path = m.glowa(m.ukryte(ids)[0, len(ce) - 1:-1])
        diff = max(diff, (full - path).abs().max().item())
    w = {"model": a.model, "class": cls, "keys": keys, "max_abs_logit_diff_path_vs_model": diff,
         "dtype": str(next(m.m.parameters()).dtype), "no_base": m.no_base}
    print(json.dumps(w, indent=1))
    if a.out:
        Path(a.out).write_text(json.dumps(w, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
