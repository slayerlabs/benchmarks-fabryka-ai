"""Cost of the model calls in a usage log written by tau3_run.py (TAU3_USAGE_LOG).

Usage: python cost.py <usage.jsonl> <model-prefix> <input-usd-per-mtok> <output-usd-per-mtok>
Counts every logged call whose model starts with the prefix (e.g. anthropic/claude-haiku), including calls of task
attempts that the harness discarded and retried. The harness's own cost field reads 0 for models litellm has no price
for, so it is not used. Prints JSON.
"""
import json
import sys

path, prefix, p_in, p_out = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4])
n = tin = tout = 0
try:
    lines = open(path).read().splitlines()
except FileNotFoundError:
    lines = []
for line in lines:
    r = json.loads(line)
    if (r["model"] or "").startswith(prefix):
        n += 1
        tin += r["prompt_tokens"]
        tout += r["completion_tokens"]
print(json.dumps({"calls": n, "prompt_tokens": tin, "completion_tokens": tout,
                  "cost_usd": round(tin / 1e6 * p_in + tout / 1e6 * p_out, 4)}))
