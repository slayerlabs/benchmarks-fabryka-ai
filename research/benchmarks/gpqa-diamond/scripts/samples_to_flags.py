#!/usr/bin/env python3
"""Turn an lm-eval `samples_*.jsonl` (run with --log_samples) into the per-item flag file kept in results/.

usage: python scripts/samples_to_flags.py SAMPLES.jsonl OUT.jsonl.gz

One output line per doc_id, sorted: {"doc_id", "exact_match", "answer_is_present"}.
  exact_match        the `flexible-extract` filter's score (the reported metric)
  answer_is_present  the model response contains the phrase "answer is" (case-insensitive)

The samples file holds the gated GPQA question text and the model output. Only the flags above are written, so
nothing gated reaches the repo. Run this locally on the raw output and publish only the .jsonl.gz.
Truncation flags are added by truncation_flags.py (needs the model tokenizer).
"""
import gzip
import json
import re
import sys


def flags_from_samples(path):
    rows = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            r = rows.setdefault(d["doc_id"], {"doc_id": d["doc_id"]})
            if "answer_is_present" not in r:  # the response text is the same under every filter
                r["answer_is_present"] = bool(re.search(r"answer is", d["resps"][0][0], re.I))
            if d["filter"] == "flexible-extract":
                r["exact_match"] = d["exact_match"]
    out = []
    for k in sorted(rows):
        r = rows[k]
        if "exact_match" not in r:
            raise SystemExit(f"doc_id {k}: no flexible-extract line in {path}")
        out.append({"doc_id": k, "exact_match": r["exact_match"], "answer_is_present": r["answer_is_present"]})
    return out


def write_flags(rows, out_path):
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    rows = flags_from_samples(sys.argv[1])
    write_flags(rows, sys.argv[2])
    print(f"{len(rows)} items, exact_match sum {sum(r['exact_match'] for r in rows):g}, "
          f"answer_is_present {sum(r['answer_is_present'] for r in rows)}")
