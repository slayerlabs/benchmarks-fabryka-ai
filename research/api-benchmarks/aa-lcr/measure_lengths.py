"""Token length of every AA-LCR prompt with the tokenizers of the two models and cl100k_base (the dataset's own count).

Writes results/lengths.json: per question counts, the distribution, and how many prompts fit each window.
No model and no API is used. Run: python measure_lengths.py   (needs transformers, huggingface_hub, tiktoken)
"""
import json
import statistics as st
import sys
from pathlib import Path

import common

OUT = common.HERE / "results" / "lengths.json"
# The API's window comes from `probe_window.py` (results/api-window.json) and the /v1/models listing: 32768.
WINDOWS = {"bielik-11b-v3.1 (Fabryka API)": 32768, "slayer1b (block)": 4096}
# What the API adds on top of the prompt: the chat template with its provider system prompt (about 1057 tokens, RULER
# README) is counted in `bielik_templated`; the answer needs at least 1 more token.


def summary(values):
    v = sorted(values)
    return {"min": v[0], "median": st.median(v), "max": v[-1], "mean": round(st.mean(v), 1)}


def main():
    from transformers import AutoTokenizer, PreTrainedTokenizerFast
    from huggingface_hub import snapshot_download
    import tiktoken
    rows, lcr, data_sha = common.fetch_data()
    bdir = snapshot_download(common.BIELIK_REPO, revision=common.BIELIK_REVISION,
                             allow_patterns=["tokenizer*", "special_tokens_map.json", "chat_template*", "config.json"])
    sdir = snapshot_download(common.SLAYER_REPO, revision=common.SLAYER_REVISION,
                             allow_patterns=["tokenizer.json", "config.json"])
    bt = AutoTokenizer.from_pretrained(bdir)
    sl = PreTrainedTokenizerFast(tokenizer_file=str(Path(sdir) / "tokenizer.json"))
    enc = tiktoken.get_encoding("cl100k_base")
    per_q = []
    for r in rows:
        p = common.build_prompt(r, lcr)
        templ = bt.apply_chat_template([{"role": "user", "content": p}], tokenize=True, add_generation_prompt=True,
                                       return_dict=True)["input_ids"]
        per_q.append({
            "question_id": int(r["question_id"]),
            "published_input_tokens": int(r["input_tokens"]),
            "cl100k": len(enc.encode(p, disallowed_special=())),
            "bielik_raw": len(bt(p, add_special_tokens=False)["input_ids"]),
            "bielik_templated": len(templ),
            "slayer_raw": len(sl(p, add_special_tokens=False)["input_ids"]) + 1,   # + BOS, as in ruler-128k
        })
    dist = {k: summary([q[k] for q in per_q])
            for k in ["published_input_tokens", "cl100k", "bielik_raw", "bielik_templated", "slayer_raw"]}
    fit = {"bielik-11b-v3.1 (Fabryka API)": sum(q["bielik_templated"] < 32768 for q in per_q),
           "slayer1b (block)": sum(q["slayer_raw"] < 4096 for q in per_q)}
    res = {
        "dataset": {"repo": common.REPO, "revision": common.REVISION, "sha256": data_sha, "n": len(rows)},
        "tokenizers": {"bielik": f"{common.BIELIK_REPO} @ {common.BIELIK_REVISION} (chat template, defaults)",
                       "slayer": f"{common.SLAYER_REPO} @ {common.SLAYER_REVISION} tokenizer.json",
                       "cl100k": "tiktoken cl100k_base"},
        "cl100k_equals_published": sum(q["cl100k"] == q["published_input_tokens"] for q in per_q),
        "distribution": dist, "windows": WINDOWS, "prompts_that_fit": fit, "per_question": per_q,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in ["cl100k_equals_published", "distribution", "prompts_that_fit"]}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
