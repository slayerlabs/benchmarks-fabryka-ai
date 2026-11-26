"""Fit check of AA-LCR prompts against a model's window (PROTOCOL.md) and the null result when nothing fits.

Usage: python fit_check.py <model-id> [--limit N] [--out-dir DIR]
With --limit the check covers the first N questions and writes to out/ (a smoke test, not a result); without it the
whole set is checked and results/<model-id>.json is written.
"""
import argparse
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

import common

MODELS = {
    "bielik-11b-v3.1": {
        "window": 32768, "tokenizer": (common.BIELIK_REPO, common.BIELIK_REVISION), "templated": True,
        "serving": "Fabryka AI API, https://fabryka.ai/v1/chat/completions, model bielik-11b-v3.1",
        "weights": f"{common.BIELIK_REPO} @ {common.BIELIK_REVISION}",
        "window_source": "GET /v1/models lists context_length 32768; probe_window.py: a templated prompt of 32767 "
                         "tokens plus 1 output token is accepted, 32768 is rejected (results/api-window.json)",
        "reserve": 1,   # the model must be able to emit at least one token
    },
    "slayer1b-1.09-k70000": {
        "window": 4096, "tokenizer": (common.SLAYER_REPO, common.SLAYER_REVISION), "templated": False,
        "serving": "research/common/slayer_lm.py (not run: nothing fits)",
        "weights": "SlayerLab/Slayer1B-1.09-checkpoints @ adfaf3fd5402bc7f3adbfe077798f20262979433 wagi_70000.pt, "
                   "tokenizer of SlayerLab/Slayer1B-1.08 @ 5f854a0cc7160594d54d1788d37a44e8ebabe16c "
                   "(sha256 0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd)",
        "window_source": "block 4096 in the config.json of SlayerLab/Slayer1B-1.08 (RoPE, trained at 4096; "
                         "the same window ruler-128k uses)",
        "reserve": 1,
    },
}


def count_tokens(model_id, texts):
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer, PreTrainedTokenizerFast
    repo, rev = MODELS[model_id]["tokenizer"]
    if MODELS[model_id]["templated"]:
        tok = AutoTokenizer.from_pretrained(snapshot_download(
            repo, revision=rev, allow_patterns=["tokenizer*", "special_tokens_map.json", "chat_template*", "config.json"]))
        return [len(tok.apply_chat_template([{"role": "user", "content": t}], tokenize=True,
                                            add_generation_prompt=True, return_dict=True)["input_ids"]) for t in texts]
    tok = PreTrainedTokenizerFast(tokenizer_file=str(Path(snapshot_download(
        repo, revision=rev, allow_patterns=["tokenizer.json", "config.json"])) / "tokenizer.json"))
    return [len(tok(t, add_special_tokens=False)["input_ids"]) + 1 for t in texts]   # + BOS


def null_result(model_id, counts, n_total, fitting, full):
    m = MODELS[model_id]
    lo, hi = min(counts), max(counts)
    reason = (f"the {m['window']}-token context window does not hold any AA-LCR prompt: the shortest of "
              f"{len(counts)} prompts has {lo} tokens, the longest {hi}; the benchmark is not cut down "
              f"(no truncation, chunking or retrieval)")
    return {
        "benchmark": "AA-LCR", "model": model_id,
        "metric": "accuracy over the 100 AA-LCR questions, judged by an LLM equality checker (percent)",
        "score": None, "stderr": None, "n": None, "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "harness": "AA-LCR dataset card prompt template and judge prompts, "
                   f"{common.REPO} @ {common.REVISION} (v1.1); no official harness repository",
        "data": f"{common.REPO} @ {common.REVISION}: AA-LCR_Dataset.csv and extracted_text/AA-LCR_extracted-text.zip",
        "settings": {"weights": m["weights"], "context_window": m["window"], "window_source": m["window_source"],
                     "serving": m["serving"], "prompt": "dataset card template, documents in the order of "
                     "data_source_filenames, " + ("one user message through the chat template with its defaults"
                                                  if m["templated"] else "raw prompt without a chat template, BOS"),
                     "judge": "GPT-5.6 Luna (medium) with the v1.1 system and user prompts: required by AA-LCR, "
                              "paid API, not run",
                     "generation": "none: no request was sent for scoring"},
        "other_metrics": {"prompts_counted": len(counts), "prompts_total": n_total, "prompts_that_fit": fitting,
                          "tokens_min": lo, "tokens_median": statistics.median(counts), "tokens_max": hi,
                          "reason": reason, "full_set": full},
        "deviations": "none (not run: " + reason + ")",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out-dir", type=Path, default=None)
    a = ap.parse_args()
    if a.model not in MODELS:
        sys.exit(f"unknown model-id {a.model}: {' | '.join(MODELS)}")
    rows, lcr, _ = common.fetch_data()
    n_total = len(rows)
    if a.limit:
        rows = rows[:a.limit]
    counts = count_tokens(a.model, [common.build_prompt(r, lcr) for r in rows])
    m = MODELS[a.model]
    fitting = sum(c + m["reserve"] <= m["window"] for c in counts)
    print(f"{a.model}: {len(counts)} prompts, tokens min {min(counts)} median {statistics.median(counts)} "
          f"max {max(counts)}, window {m['window']}, fit {fitting}")
    if fitting:
        sys.exit(f"{fitting} prompt(s) fit the window: PROTOCOL.md leaves this case to Dario; nothing was run")
    res = null_result(a.model, counts, n_total, fitting, full=a.limit is None)
    out = (a.out_dir or (common.HERE / ("results" if not a.limit else "out"))) / f"{a.model}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"null result written to {out}")


if __name__ == "__main__":
    main()
