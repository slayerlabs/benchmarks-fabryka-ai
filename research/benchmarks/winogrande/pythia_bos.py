"""Pythia-1B v0 on WinoGrande with the same leading BOS the Slayer overlay adds.

Does not replace the no-BOS reproduction in RECIPE.md result 1. `add_bos_token=True`
does not prepend a token for this tokenizer, so the token is inserted in `_encode_pair`,
the same place as `common/slayer_lm.py`.
"""

import json
import sys
from pathlib import Path

from lm_eval import simple_evaluate
from lm_eval.models.huggingface import HFLM
from lm_eval.tasks import TaskManager

MODEL = "D:/models/pythia-1b-v0"
OUT = Path("benchmarks/winogrande/results/pythia-1b-v0-bos")


class HFLMWithLeadingBos(HFLM):
    def _encode_pair(self, context, continuation):
        context_enc, continuation_enc = super()._encode_pair(context, continuation)
        return [self.prefix_token_id] + context_enc, continuation_enc


def main():
    lm = HFLMWithLeadingBos(pretrained=MODEL, dtype="float32", batch_size=1, device="cuda")
    ctx, cont = lm._encode_pair(
        "Sarah was a much better surgeon than Maria so Maria",
        " always got the easier cases.",
    )
    if ctx[0] != lm.prefix_token_id:
        sys.exit(f"BOS not prepended: {ctx[:4]}")
    print(f"bos_id {lm.prefix_token_id} ctx_len {len(ctx)} cont_len {len(cont)}", flush=True)
    if "--check" in sys.argv:
        return

    tm = TaskManager(include_path="benchmarks/winogrande/lm_eval_tasks")
    result = simple_evaluate(
        model=lm,
        tasks=["winogrande"],
        num_fewshot=0,
        batch_size=1,
        log_samples=True,
        task_manager=tm,
        random_seed=0,
        numpy_random_seed=1234,
        torch_random_seed=1234,
        fewshot_random_seed=1234,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    samples = result.pop("samples", {})
    (OUT / "results.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    for name, rows in samples.items():
        path = OUT / f"samples_{name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, default=str) + "\n")
        print(f"wrote {path} n={len(rows)}", flush=True)
    acc = result["results"]["winogrande"]["acc,none"]
    se = result["results"]["winogrande"]["acc_stderr,none"]
    print(f"acc {acc} se {se}", flush=True)


if __name__ == "__main__":
    main()
