"""Stage B check (REPRODUCTION.md, "BOS i kodowanie"): Pythia-1b-v0 tokens of every lambada_openai request.

Compares the 2022 harness (lm-eval 0.2.0/0.3.0 `loglikelihood`: context and target encoded separately, no BOS;
gpt-neox `eval_adapter.py` @ dfc018a encodes with the bare `tokenizers` encoder) with lm-eval 0.4.9.1 HFLM
(`_encode_pair`: whole text encoded, split at the context length; `add_bos_token=False`). Prints how many contexts
start with BOS under the tokenizer defaults and how many (context, target) token pairs differ.

Run from research/ (no network when both are in the HF cache):
  python -I benchmarks/lambada/kodowanie_par.py <pythia-1b-v0 snapshot f3f1b6d5> <lambada_openai test parquet @ 900124bf>
"""
import sys

import pyarrow.parquet as pq
from transformers import AutoTokenizer


def main(model_dir, parquet):
    tok = AutoTokenizer.from_pretrained(model_dir)
    texts = pq.read_table(parquet).column("text").to_pylist()

    def enc(s):
        return tok.encode(s, add_special_tokens=False)

    bos = diff = 0
    for t in texts:
        ctx, word = t.rsplit(" ", 1)
        cont = " " + word
        c = enc(ctx)
        bos += tok.encode(ctx)[:1] == [tok.bos_token_id]
        diff += (c, enc(cont)) != (c, enc(ctx + cont)[len(c):])
    print(f"n={len(texts)} bos_id={tok.bos_token_id} contexts_with_bos={bos} pairs_differing={diff}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
