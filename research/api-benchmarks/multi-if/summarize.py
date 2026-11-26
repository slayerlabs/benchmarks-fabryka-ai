"""Multi-IF step CSVs -> results/<model-id>.json and results/<model-id>.jsonl.gz
(format from research/api-benchmarks/README.md).

Usage (with the Multi-IF checkout on PYTHONPATH, so that its metrics.py is importable):
  PYTHONPATH=<Multi-IF checkout> python summarize.py <results/<model> dir of the harness> <results/model-id> \
    <settings json> [--limit]

Scoring is the harness's own (metrics.MultiTurnInstructionFollowingPromptSolution.metrics_gen on
eval_result_step_{1,2,3}.csv). Per turn, `overall` = mean of prompt-level strict, instruction-level strict,
prompt-level loose and instruction-level loose over all languages; the score is the mean of the three turns' overall
(Multi-IF paper, Fig. 1: "average ... across all languages and across all turns"). One change before scoring: a turn
whose request failed (status != success) has no model answer, and the harness would score the failure text; that
turn and the later turns of the same conversation are scored with an empty answer, i.e. as failed, in the full N.
The stderr comes from a cluster bootstrap by conversation (all three turns together), 1000 resamples, fixed seed.

A run stopped before turn 3 (--stopped) gets score null; see stopped() for how its finished turns are scored.
"""

import datetime
import gzip
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from metrics import MultiTurnInstructionFollowingPromptSolution as M, parse_result

MULTIIF_COMMIT = "1cdb53ed18499ad729e0766e5d3099dd5344406f"
HARNESS = (f"https://github.com/facebookresearch/Multi-IF @ {MULTIIF_COMMIT}; api_client.py @ {MULTIIF_COMMIT} "
           "patched by patch_api_client.py")
DATA_REVISION = "0ab97ce0b45c7f57772e8ba2ac1616f4b00bd3aa"
EXPECTED_ROWS = {1: 4501, 2: 4501, 3: 4445}
BOOTSTRAP, SEED = 1000, 20261119


def main(results_dir, target, settings, limit):
    broken, turns, rows_out = set(), {}, []
    for t in (1, 2, 3):
        df = pd.read_csv(f"{results_dir}/eval_result_step_{t}.csv", keep_default_na=False)
        broken |= {str(k) for k, s in zip(df["key"], df["status"]) if s != "success"}
        forced = [str(k) in broken for k in df["key"]]
        raw = list(df["responses"])
        df["responses"] = [("" if f else r) for f, r in zip(forced, raw)]
        metrics, out_s, out_l = M.metrics_gen(df, return_outputs=True)
        keys = [str(k) for k in out_s["counter"]]
        n = len(keys)
        if not limit and n != EXPECTED_ROWS[t]:
            sys.exit(f"summarize.py: turn {t}: {n} scored rows, expected {EXPECTED_ROWS[t]}")
        if len(set(keys)) != n:
            sys.exit(f"summarize.py: turn {t}: duplicate conversation keys")
        s_rows, l_rows = out_s["all_languages"], out_l["all_languages"]
        ps, isr = parse_result(s_rows)
        pl, il = parse_result(l_rows)
        overall = (ps + isr + pl + il) / 4
        if abs(overall - metrics[f"turn_{t}_all_languages_overall"]) > 1e-12:
            sys.exit(f"summarize.py: turn {t}: overall differs from the harness")
        lang = dict(zip(df["key"].astype(str), df["language"]))
        by_key = dict(zip(df["key"].astype(str), raw))
        turns[t] = {"keys": keys, "strict": s_rows, "loose": l_rows, "overall": overall,
                    "components": {"prompt_strict": ps, "inst_strict": isr, "prompt_loose": pl, "inst_loose": il},
                    "by_language": {k[len(f"turn_{t}_"):-len("_overall")]: v for k, v in metrics.items()
                                    if k.startswith(f"turn_{t}_") and k.endswith("_overall") and "all_languages" not in k},
                    "forced": sum(1 for k in keys if k in broken)}
        for k, s, lo in zip(keys, s_rows, l_rows):
            rows_out.append({"task_id": f"{k}#turn{t}", "conversation": k, "turn": t, "language": lang[k],
                             "score": int(all(s["follow_instruction_list"])), "strict": s["follow_instruction_list"],
                             "loose": lo["follow_instruction_list"], "forced_empty": k in broken, "output": by_key[k]})

    # cluster bootstrap by conversation: per conversation and turn, the four counts of each component
    convs = sorted(set(turns[1]["keys"]))
    index = {c: i for i, c in enumerate(convs)}
    counts = {}
    for t in (1, 2, 3):
        a = np.zeros((len(convs), 8))
        for k, s, lo in zip(turns[t]["keys"], turns[t]["strict"], turns[t]["loose"]):
            i = index[k]
            fs, fl = s["follow_instruction_list"], lo["follow_instruction_list"]
            a[i] += [1, all(fs), len(fs), sum(fs), 1, all(fl), len(fl), sum(fl)]
        counts[t] = a
    rng = np.random.default_rng(SEED)
    samples = []
    for _ in range(BOOTSTRAP):
        w = np.bincount(rng.integers(0, len(convs), len(convs)), minlength=len(convs))
        per_turn = []
        for t in (1, 2, 3):
            c = w @ counts[t]
            per_turn.append((c[1] / c[0] + c[3] / c[2] + c[5] / c[4] + c[7] / c[6]) / 4)
        samples.append(sum(per_turn) / 3)
    score = sum(turns[t]["overall"] for t in (1, 2, 3)) / 3
    p1 = turns[1]["components"]["prompt_strict"]
    n1 = len(turns[1]["keys"])

    result = {
        "benchmark": "Multi-IF",
        "model": Path(target).name,
        "metric": "mean over 3 turns of all-languages overall",
        "score": round(100 * score, 2),
        "stderr": round(100 * float(np.std(samples, ddof=1)), 2),
        "n": sum(len(turns[t]["keys"]) for t in (1, 2, 3)),  # scored turns
        "n_conversations": len(convs),  # the bootstrap unit
        "date": datetime.date.today().isoformat(),
        "harness": HARNESS,
        "data": f"https://huggingface.co/datasets/facebook/Multi-IF @ {DATA_REVISION} (multiIF_20241018.csv)",
        "settings": json.loads(settings),
        "other_metrics": {
            **{f"turn_{t}_overall": round(100 * turns[t]["overall"], 2) for t in (1, 2, 3)},
            **{f"turn_{t}_{k}": round(100 * v, 2) for t in (1, 2, 3) for k, v in turns[t]["components"].items()},
            **{f"turn_{t}_{lang}_overall": round(100 * v, 2) for t in (1, 2, 3) for lang, v in turns[t]["by_language"].items()},
            "turn_1_prompt_strict_stderr": round(100 * math.sqrt(p1 * (1 - p1) / n1), 2),
            **{f"turn_{t}_forced_empty": turns[t]["forced"] for t in (1, 2, 3)},
        },
        "stderr_method": f"cluster bootstrap by conversation, {BOOTSTRAP} resamples, seed {SEED}",
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    with gzip.open(f"{target}.jsonl.gz", "wt", encoding="utf-8", newline="\n") as f:
        for r in rows_out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2))


def stopped(results_dir, target, settings, reason):
    """Record of a run stopped before turn 3: score null; the turns that finished (eval_result_step_<t>.csv) are scored
    with the harness's metrics.py. In such a run (Slayer) a request fails only when slayer_server.py rejects it because
    the turn's input plus the output limit does not fit in the model's window (HTTP 400; the harness marks the row
    `failed` after its retries). A model whose window is too short cannot run that turn, which is not a wrong answer
    (research/api-benchmarks/README.md): that turn and the later turns of the same conversation are counted as
    turn_<t>_context_exceeded and left out of the turn's N and accuracy."""
    exceeded, other = set(), {}
    for t in (1, 2, 3):
        path = Path(results_dir, f"eval_result_step_{t}.csv")
        if not path.exists():
            continue
        df = pd.read_csv(path, keep_default_na=False)
        exceeded |= {str(k) for k, s in zip(df["key"], df["status"]) if s == "failed"}
        out = df["key"].astype(str).isin(exceeded)
        metrics = M.metrics_gen(df[~out].reset_index(drop=True))
        other[f"turn_{t}_prompts_number"] = int(metrics[f"turn_{t}_prompts_number"])
        other[f"turn_{t}_context_exceeded"] = int(out.sum())
        for key, value in metrics.items():
            if key.startswith(f"turn_{t}_") and key.endswith("_overall"):
                other[key] = round(100 * float(value), 2)
    if not other:
        sys.exit("summarize.py: no eval_result_step_<t>.csv in " + str(results_dir))
    result = {
        "benchmark": "Multi-IF",
        "model": Path(target).name,
        "metric": "mean over 3 turns of all-languages overall",
        "score": None,
        "stderr": None,
        "n": 0,
        "date": datetime.date.today().isoformat(),
        "harness": HARNESS,
        "data": f"https://huggingface.co/datasets/facebook/Multi-IF @ {DATA_REVISION} (multiIF_20241018.csv)",
        "settings": json.loads(settings),
        "score_null_reason": reason,
        "other_metrics": other,
        "other_metrics_note": "turns that finished, re-scored with the harness's metrics.py; turns rejected for the "
                              "context window (turn_<t>_context_exceeded) and the later turns of their conversations "
                              "are not in turn_<t>_prompts_number",
        "deviations": "see README.md, Deviations",
    }
    Path(target).parent.mkdir(parents=True, exist_ok=True)
    Path(f"{target}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if sys.argv[1] == "--stopped":  # summarize.py --stopped <results dir> <results/model-id> <settings json> <reason>
        stopped(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3], "--limit" in sys.argv[4:])
