"""Draw the 20-task sample of the simulator probe: 5 tasks per domain, seeded.

Usage: python sample_tasks.py <tau2-bench data dir> [seed] > sample.json
Population: the `base` split of airline (50), retail (114) and telecom (114), and all 97 tasks of banking_knowledge
(the domain has no split file). `random.Random(seed).sample` over the ids sorted as strings.
"""
import json
import random
import sys
from pathlib import Path

DOMAINS = ["airline", "retail", "telecom", "banking_knowledge"]
PER_DOMAIN = 5

data = Path(sys.argv[1]) / "tau2" / "domains"
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 20261123
rng = random.Random(seed)
out = {"seed": seed, "per_domain": PER_DOMAIN, "domains": {}}
for d in DOMAINS:
    tasks = json.loads((data / d / "tasks.json").read_text())
    split = data / d / "split_tasks.json"
    if split.exists():
        base = set(json.loads(split.read_text())["base"])
        ids = [str(t["id"]) for t in tasks if str(t["id"]) in base]
    else:
        ids = [str(t["id"]) for t in tasks]
    ids = sorted(ids)
    out["domains"][d] = {"population": len(ids), "ids": sorted(rng.sample(ids, PER_DOMAIN))}
print(json.dumps(out, indent=1, ensure_ascii=False))
