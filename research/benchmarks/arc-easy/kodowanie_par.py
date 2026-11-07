"""Stage B check (REPRODUCTION.md, "BOS i kodowanie"): Pythia-1b-v0 tokens of every ARC-Easy test request.

Compares the 2022 harness (lm-eval 0.2.0/0.3.0 `arc.py`: gold = num_to_letter + index in A-E; `loglikelihood`:
context and continuation encoded separately, no BOS) with lm-eval 0.4.9.1 (gold = `choices.label.index(answerKey)`;
HFLM `_encode_pair`: whole text encoded, split at the context length; `add_bos_token=False`). Prints how many golds
differ, how many contexts start with BOS under the tokenizer defaults and how many token pairs differ.

Run from research/ (no network when both are in the HF cache):
  python -I benchmarks/arc-easy/kodowanie_par.py <pythia-1b-v0 snapshot f3f1b6d5> <ARC-Easy test parquet @ 210d026>
"""
import sys

import pyarrow.parquet as pq
from transformers import AutoTokenizer

NUM_TO_LETTER = {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E"}


def main(model_dir, parquet):
    tok = AutoTokenizer.from_pretrained(model_dir)
    rows = pq.read_table(parquet).to_pylist()

    def enc(s):
        return tok.encode(s, add_special_tokens=False)

    gold = bos = diff = pairs = 0
    for d in rows:
        old = ["A", "B", "C", "D", "E"].index(NUM_TO_LETTER.get(d["answerKey"], d["answerKey"]))
        gold += old != list(d["choices"]["label"]).index(d["answerKey"])
        ctx = "Question: " + d["question"] + "\nAnswer:"
        c = enc(ctx)
        bos += tok.encode(ctx)[:1] == [tok.bos_token_id]
        for o in d["choices"]["text"]:
            cont = " " + o
            diff += (c, enc(cont)) != (c, enc(ctx + cont)[len(c):])
            pairs += 1
    print(f"n={len(rows)} pairs={pairs} golds_differing={gold} contexts_with_bos={bos} pairs_differing={diff}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
