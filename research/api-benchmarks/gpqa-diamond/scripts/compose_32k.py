#!/usr/bin/env python3
"""Compose the full-198 32768 file from the 16384 run and the 32768 re-run of the selected items.

usage: python scripts/compose_32k.py FLAGS_16K.jsonl.gz FLAGS_32K_SUBSET.jsonl.gz OUT.jsonl.gz [--all-rerun]

Default composition (the card's 64.65): items truncated at 16384 take their 32768 re-run result; every other item
keeps its 16384 result (truncated_32768 = false for those).
--all-rerun (the card's 62.63): every item present in the re-run file, truncated or not, takes its 32768 result.
Both compositions are reported side by side in the README; neither was fixed in a committed note before the re-run.
"""
import gzip
import json
import sys


def read(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return {r["doc_id"]: r for r in map(json.loads, f)}


def compose(full16, rerun, all_rerun=False):
    out = []
    for k in sorted(full16):
        a = full16[k]
        if k in rerun and (all_rerun or a["truncated_16384"]):
            b = rerun[k]
            out.append({"doc_id": k, "exact_match": b["exact_match"], "answer_is_present": b["answer_is_present"],
                        "truncated_32768": b["truncated_32768"]})
        else:
            out.append({"doc_id": k, "exact_match": a["exact_match"], "answer_is_present": a["answer_is_present"],
                        "truncated_32768": False})
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--all-rerun"]
    if len(args) != 3:
        raise SystemExit(__doc__)
    rows = compose(read(args[0]), read(args[1]), all_rerun="--all-rerun" in sys.argv)
    with gzip.open(args[2], "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    s = sum(r["exact_match"] for r in rows)
    print(f"{len(rows)} items: {s:g} correct = {100 * s / len(rows):.2f}%, "
          f"{sum(r['truncated_32768'] for r in rows)} still at the cap")
