"""LiquidAI/ifstruct-v1.0 (Hugging Face parquet) -> JSONL in the format of the IFStruct loader (data/test.jsonl).

Usage (in the ifstruct checkout): python convert_hf.py <parquet> <out jsonl>
json_schema and top_level_count are stored as JSON strings in the parquet and parsed back; doc_id becomes seed.
Prints how many samples differ from the repo's bundled data/test.jsonl (0 of 2000 at the pinned revisions).
"""
import json
import sys

import pyarrow.parquet as pq

rows = []
for r in pq.read_table(sys.argv[1]).to_pylist():
    rows.append({"seed": r["doc_id"], "entity_type": r["entity_type"], "prompt": r["prompt"],
                 "json_schema": json.loads(r["json_schema"]), "top_level_count": json.loads(r["top_level_count"]),
                 "top_level_key": r["top_level_key"], "require_wrapper_key": r["require_wrapper_key"],
                 "require_code_block": r["require_code_block"], "require_no_commentary": r["require_no_commentary"],
                 "output_format": r["output_format"]})
if len(rows) != 2000:
    sys.exit(f"convert_hf.py: {len(rows)} samples, expected 2000")
with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as f:
    for r in rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open("data/test.jsonl", encoding="utf-8") as f:
    bundled = {r["seed"]: r for r in map(json.loads, f)}
diff = [r["seed"] for r in rows if bundled.get(r["seed"]) != r]
print(f"convert_hf.py: {len(rows)} samples, {len(diff)} differ from data/test.jsonl: {diff[:10]}")
