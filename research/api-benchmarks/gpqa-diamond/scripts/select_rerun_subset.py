#!/usr/bin/env python3
"""Pick the items re-run at the larger budget ("subset B") and write the lm-eval --samples file.

usage: python scripts/select_rerun_subset.py FLAGS_16K.jsonl.gz OUT.json [TASK]

Rule used for the published 32768 re-run: the doc_ids that hit the cap at 16384 (truncated_16384) OR whose
response has no "answer is" phrase (answer_is_present false). On the 16384 run that is 36 + 31 = 67 items.
The 31 items did conclude by 16384. The run brief names them only as responses with no "answer is" conclusion;
no other reason was recorded. Under greedy decoding they were expected to reproduce their 16384 result, and 4 of
them did not (see README, Results). The rule was written in the run brief before the re-run, not in a committed note.

OUT.json is the format `lm_eval --samples` takes: {"<task>": [doc_id, ...]}. The task name must match the task
that run.sh runs, `gpqa_diamond_cot_zeroshot_pinned` (the published re-run used the stock name
`gpqa_diamond_cot_zeroshot`; pass it as TASK to rebuild that file). Then:
  SAMPLES_JSON=OUT.json MAX_GEN_TOKS=32768 bash run.sh lfm3-1.7b
"""
import gzip
import json
import sys

TASK = "gpqa_diamond_cot_zeroshot_pinned"


def select(rows):
    return sorted(r["doc_id"] for r in rows if r["truncated_16384"] or not r["answer_is_present"])


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    with gzip.open(sys.argv[1], "rt", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]
    ids = select(rows)
    with open(sys.argv[2], "w") as f:
        json.dump({sys.argv[3] if len(sys.argv) == 4 else TASK: ids}, f)
    t = sum(r["truncated_16384"] for r in rows)
    print(f"{len(ids)} items: {t} truncated at 16384 + {len(ids) - t} concluded without 'answer is'")
