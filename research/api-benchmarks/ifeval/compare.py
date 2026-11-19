"""Compare IFEval runs prompt by prompt: score, paired difference with its SE, and the share of Polish answers.

Usage: python compare.py <model-id> <model-id> [...]   (reads results/<model-id>.jsonl.gz)
The first model id is the baseline for the paired differences.

The Polish check is a rough heuristic: an answer counts as Polish when over 5% of its words are common Polish
function words or over 0.5% of its characters are Polish-only letters (ą, ć, ę, ł, ń, ś, ź, ż).
"""

import gzip
import json
import math
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
# No words that also occur in English text ("to", "do", "w", "na", "tak"): they made English answers count as Polish.
PL_WORDS = set("się nie jest jak oraz że dla są być który która może".split())


def load(model_id: str) -> dict[str, dict]:
    with gzip.open(HERE / "results" / f"{model_id}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["task_id"]: r for r in map(json.loads, f)}


def is_polish(text: str) -> bool:
    words = re.findall(r"[a-ząćęłńóśźż]+", text.lower())
    if not words:
        return False
    word_share = sum(w in PL_WORDS for w in words) / len(words)
    letter_share = len(re.findall("[ąćęłńśźż]", text.lower())) / len(text)
    return word_share > 0.05 or letter_share > 0.005


def main(ids: list[str]) -> None:
    runs = {i: load(i) for i in ids}
    for i, r in runs.items():
        acc = sum(x["prompt_level_strict_acc"] for x in r.values()) / len(r)
        pl = [x["prompt_level_strict_acc"] for x in r.values() if is_polish(x["scored_output"])]
        rest = [x["prompt_level_strict_acc"] for x in r.values() if not is_polish(x["scored_output"])]
        by_lang = ", ".join(f"{name} {100 * sum(s) / len(s):.1f}" for name, s in (("Polish", pl), ("other", rest)) if s)
        print(f"{i}: n={len(r)} prompt_level_strict_acc={100 * acc:.2f} polish={100 * len(pl) / len(r):.1f}% "
              f"(score: {by_lang})")
    base = ids[0]
    for other in ids[1:]:
        common = sorted(set(runs[base]) & set(runs[other]))
        d = [runs[other][t]["prompt_level_strict_acc"] - runs[base][t]["prompt_level_strict_acc"] for t in common]
        n = len(d)
        mean = sum(d) / n
        se = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1) / n)
        print(f"{other} - {base}: {100 * mean:+.2f} +- {100 * se:.2f} (paired SE, n={n}); "
              f"passes only in {other}: {d.count(1)}, only in {base}: {d.count(-1)}")


if __name__ == "__main__":
    main(sys.argv[1:])
