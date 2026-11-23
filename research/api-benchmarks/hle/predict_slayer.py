"""Generate HLE predictions locally with Slayer (base model).

Plain prompt (no chat template), greedy decoding via research/common/slayer_model.Slayer.
Context overflow (prompt leaves < 256 tokens for answer in 4096 context) is recorded as
an unsupported response and counted in the benchmark (no cutting, rule 8).
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


def slayer_generate(model, prompt_ids, max_new_tokens):
    import torch

    cache = []
    ids = torch.tensor([prompt_ids], dtype=torch.long, device=model.device)
    logits = model.krok(ids, cache)[0]
    out = []
    for _ in range(max_new_tokens):
        nxt = int(logits.argmax().item())
        out.append(nxt)
        if nxt == model.bos:
            break
        logits = model.krok(torch.tensor([[nxt]], dtype=torch.long, device=model.device), cache)[0]
    return out


def is_text_only(question):
    return not question.get("image")


def build_prompt(question_text: str) -> str:
    return SYSTEM_PROMPT + "\n\n" + question_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--slayer-pretrained", required=True)
    parser.add_argument("--slayer-device", default="cuda")
    parser.add_argument("--slayer-dtype", default="bfloat16")
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
    print(f"subset={args.subset} selected={len(questions)} text_only={len(text_only_questions)} full={total_full}")
    if args.max_samples:
        questions = questions[: args.max_samples]

    predictions = {}
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            predictions = json.load(f)
    questions = [q for q in questions if q["id"] not in predictions]

    model = load_slayer(args.slayer_pretrained, args.slayer_device, args.slayer_dtype)
    overflow = 0
    for q in tqdm(questions):
        prompt = build_prompt(q["question"])
        ids = model.encode(prompt)
        prompt_tokens = len(ids)
        max_new_tokens = SLAYER_CONTEXT - prompt_tokens
        if max_new_tokens < SLAYER_MIN_ANSWER_TOKENS:
            overflow += 1
            predictions[q["id"]] = {
                "model": args.model,
                "response": "",
                "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": 0, "total_tokens": prompt_tokens},
                "slayer_unsupported": True,
                "slayer_overflow_reason": f"prompt has {prompt_tokens} tokens, leaving {max_new_tokens} < {SLAYER_MIN_ANSWER_TOKENS} for answer in {SLAYER_CONTEXT}",
            }
        else:
            out_ids = slayer_generate(model, ids, max_new_tokens)
            finish_stop = bool(out_ids and out_ids[-1] == model.bos)
            decoded_ids = out_ids[:-1] if finish_stop else out_ids
            response = model.tok.decode(decoded_ids, skip_special_tokens=False)
            if response.startswith("<|endoftext|>"):
                response = response[len("<|endoftext|>"):]
            predictions[q["id"]] = {
                "model": args.model,
                "response": response,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": len(out_ids),
                    "total_tokens": prompt_tokens + len(out_ids),
                },
            }
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(predictions, f, ensure_ascii=False, indent=2)

    print(f"wrote {len(predictions)} predictions to {args.output}")
    print(f"slayer_context_overflow={overflow} of {len(questions) + len([k for k in predictions if predictions[k].get('slayer_unsupported')]) - overflow} newly processed; total_overflow_in_file={sum(1 for v in predictions.values() if v.get('slayer_unsupported'))}")


if __name__ == "__main__":
    main()
