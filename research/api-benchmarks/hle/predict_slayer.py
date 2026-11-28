"""Generate HLE predictions locally with Slayer (base model).

Status: prepared, not run (maintainer decision 2026-11-25: cost vs expected ~0 score).

Plain prompt (no chat template), greedy batched decoding via
research/common/slayer_batch.py. BOS rule: one leading BOS per request as in
IFEval/SlayerLM (handled inside generate_batch). Tokenizer v6
(SHA 0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd).

Context overflow (prompt leaves < 256 tokens for answer in 4096 context) is
recorded as an unsupported empty response and counted in the benchmark
(no cutting, rule 8).
"""

import argparse
import json
import os
import sys
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

HERE = Path(__file__).resolve().parent
COMMON = HERE.parents[1] / "common"
if str(COMMON) not in sys.path:
    sys.path.insert(0, str(COMMON))

SYSTEM_PROMPT = (
    "Your response should be in the following format:\n"
    "Explanation: {your explanation for your answer choice}\n"
    "Answer: {your chosen answer}\n"
    "Confidence: {your confidence score between 0% and 100% for your answer}"
)

SLAYER_CONTEXT = 4096
SLAYER_MIN_ANSWER_TOKENS = 256


def load_slayer(pretrained: str, device: str, dtype: str):
    import torch
    import slayer_model

    dt = {
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
        "float16": torch.float16,
        "fp16": torch.float16,
        "float32": torch.float32,
        "fp32": torch.float32,
    }.get(dtype, torch.bfloat16)
    return slayer_model.Slayer(pretrained, device=device, dtype=dt)


def is_text_only(question):
    return not question.get("image")


def build_prompt(question_text: str) -> str:
    return SYSTEM_PROMPT + "\n\n" + question_text


def _save(path, predictions):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--slayer-pretrained", required=True)
    parser.add_argument("--slayer-device", default="cuda")
    parser.add_argument("--slayer-dtype", default="bfloat16")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--subset", type=str, default="text-only", choices=["text-only", "full"])
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    dataset = load_dataset(args.dataset, split="test").to_dict()
    questions = [dict(zip(dataset.keys(), values)) for values in zip(*dataset.values())]
    total_full = len(questions)
    text_only_questions = [q for q in questions if is_text_only(q)]
    if args.subset == "text-only":
        questions = text_only_questions
    print(
        f"subset={args.subset} selected={len(questions)} "
        f"text_only={len(text_only_questions)} full={total_full}"
    )
    if args.max_samples:
        questions = questions[: args.max_samples]

    predictions = {}
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            predictions = json.load(f)
    questions = [q for q in questions if q["id"] not in predictions]

    model = load_slayer(args.slayer_pretrained, args.slayer_device, args.slayer_dtype)
    from slayer_batch import generate_batch

    overflow = 0
    overflow_ids = []
    pending = []
    for q in tqdm(questions, desc="prepare"):
        prompt = build_prompt(q["question"])
        prompt_ids = model.encode(prompt)
        prompt_tokens = len(prompt_ids)
        max_new_tokens = SLAYER_CONTEXT - prompt_tokens
        if max_new_tokens < SLAYER_MIN_ANSWER_TOKENS:
            overflow += 1
            overflow_ids.append(q["id"])
            predictions[q["id"]] = {
                "model": args.model,
                "response": "",
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": 0,
                    "total_tokens": prompt_tokens,
                },
                "slayer_unsupported": True,
                "slayer_overflow_reason": (
                    f"prompt has {prompt_tokens} tokens, leaving {max_new_tokens} < "
                    f"{SLAYER_MIN_ANSWER_TOKENS} for answer in {SLAYER_CONTEXT}"
                ),
            }
            _save(args.output, predictions)
        else:
            pending.append((q, prompt_ids, prompt_tokens))

    bs = max(1, args.batch_size)
    for i in tqdm(range(0, len(pending), bs), desc="generate"):
        batch = pending[i : i + bs]
        prompt_ids_list = [p for _, p, _ in batch]
        outs = generate_batch(model, prompt_ids_list, max_total=SLAYER_CONTEXT, stop_id=model.bos)
        for (q, prompt_ids, prompt_tokens), out_ids in zip(batch, outs):
            finish_stop = bool(out_ids and out_ids[-1] == model.bos)
            decoded_ids = out_ids[:-1] if finish_stop else out_ids
            response = model.tok.decode(decoded_ids, skip_special_tokens=False)
            if response.startswith("<|endoftext|>"):
                response = response[len("<|endoftext|>") :]
            predictions[q["id"]] = {
                "model": args.model,
                "response": response,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": len(out_ids),
                    "total_tokens": prompt_tokens + len(out_ids),
                },
            }
        _save(args.output, predictions)

    total_overflow = sum(1 for v in predictions.values() if v.get("slayer_unsupported"))
    print(f"wrote {len(predictions)} predictions to {args.output}")
    print(f"slayer_context_overflow_new={overflow} overflow_ids={overflow_ids}")
    print(f"slayer_context_overflow_total={total_overflow}")


if __name__ == "__main__":
    main()
