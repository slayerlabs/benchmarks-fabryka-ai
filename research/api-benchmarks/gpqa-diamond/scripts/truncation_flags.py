#!/usr/bin/env python3
"""Add the truncated_<N> flag to a flag file: the tokenizer pass behind `truncated_16384` and `truncated_32768`.

usage: python scripts/truncation_flags.py SAMPLES.jsonl FLAGS.jsonl.gz MAX_GEN_TOKS TOKENIZER_PATH

Counts the generated tokens of every response in SAMPLES.jsonl with the model tokenizer
(add_special_tokens=False, trust_remote_code) and sets truncated_<MAX_GEN_TOKS> = tokens >= MAX_GEN_TOKS - 8.
The 8-token margin is the one used on the pod for the published files (the response text is re-tokenised, so the
count can differ by a few tokens from the generator's own). Checked against the pod-side token counts of the
published runs: the largest non-truncated response has 16367 tokens and the smallest truncated one 16380. FLAGS.jsonl.gz is rewritten in place.
Needs `transformers` and the LFM3 tokenizer (LiquidAI/LFM3-1.7B @ 1da06bec6a819da10b54c67e5c90972b46d81871).
"""
import gzip
import json
import sys

MARGIN = 8


def is_truncated(n_tokens, max_gen_toks):
    return n_tokens >= max_gen_toks - MARGIN


def main(samples, flags_path, max_gen_toks, tokenizer_path):
    from transformers import AutoTokenizer  # imported late: the other scripts need only the standard library

    tok = AutoTokenizer.from_pretrained(tokenizer_path, trust_remote_code=True)
    n_toks = {}
    with open(samples, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            if d["doc_id"] not in n_toks:
                n_toks[d["doc_id"]] = len(tok(d["resps"][0][0], add_special_tokens=False)["input_ids"])
    with gzip.open(flags_path, "rt", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]
    key = f"truncated_{max_gen_toks}"
    for r in rows:
        r[key] = is_truncated(n_toks[r["doc_id"]], max_gen_toks)
    with gzip.open(flags_path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"{key}: {sum(r[key] for r in rows)} of {len(rows)}")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
