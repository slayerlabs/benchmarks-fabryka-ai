"""allenai/IFBench_test (Hugging Face parquet) -> JSONL in the format of the IFBench repo's data/IFBench_test.jsonl.

Usage (in the IFBench checkout): python convert_hf.py <parquet> <out jsonl>
Parquet stores integer kwargs as floats (3.0); they are turned back into ints, as in the repo file. Prints how many
prompts differ from the repo's bundled data/IFBench_test.jsonl (2 of 300 at the pinned revisions: keys 13 and 19).
"""
import json
import sys

import pyarrow.parquet as pq

COLS = ["key", "prompt", "instruction_id_list", "kwargs"]


def ints(x):
    if isinstance(x, float) and x.is_integer():
        return int(x)
    if isinstance(x, dict):
        return {k: ints(v) for k, v in x.items()}
    if isinstance(x, list):
        return [ints(v) for v in x]
    return x


rows = [ints({c: r[c] for c in COLS}) for r in pq.read_table(sys.argv[1]).to_pylist()]
if len(rows) != 300:
    sys.exit(f"convert_hf.py: {len(rows)} prompts, expected 300")
with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("data/IFBench_test.jsonl", encoding="utf-8") as f:
    bundled = {str(r["key"]): ints({c: r[c] for c in COLS}) for r in map(json.loads, f)}
diff = [r["key"] for r in rows if bundled.get(str(r["key"])) != r]
print(f"convert_hf.py: {len(rows)} prompts, {len(diff)} differ from data/IFBench_test.jsonl: {diff}")
