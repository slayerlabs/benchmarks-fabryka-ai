"""Generate HLE predictions through an OpenAI-compatible API.

Based on centerforaisafety/hle hle_eval/run_model_predictions.py (pinned in run.sh).
Deviation from upstream: sends temperature and top_p (LFM3-1.7B card settings),
supports OPENAI_BASE_URL, and writes to --output.
"""

import argparse
import asyncio
import json
import os
import random

from datasets import load_dataset
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

SYSTEM_PROMPT = (
    "Your response should be in the following format:\n"
    "Explanation: {your explanation for your answer choice}\n"
    "Answer: {your chosen answer}\n"
    "Confidence: {your confidence score between 0% and 100% for your answer}"
)


def build_client():
    kwargs = {"timeout": 600.0, "max_retries": 1}
    base_url = os.environ.get("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def format_message(question, model):
    question_text = question["question"]
    text_content = {"type": "text", "text": question_text}
    if question.get("image"):
        image_content = {"type": "image_url", "image_url": {"url": question["image"]}}
        content = [text_content, image_content]
    else:
        content = [text_content]

    system_role = "user" if "o1" in model else "system"
    return [
        {"role": system_role, "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]


RETRYABLE_STATUS = {429, 503}
MAX_ATTEMPTS = 10
BACKOFF_START_S = 5.0
BACKOFF_MAX_S = 300.0


def _is_retryable(exc: Exception) -> bool:
    import openai

    if isinstance(exc, (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError,
                        openai.InternalServerError)):
        return True
    if isinstance(exc, openai.APIStatusError):
        return exc.status_code in RETRYABLE_STATUS
    return False


async def attempt_question(client, question, args):
    messages = format_message(question, args.model)
    params = {
        "model": args.model,
        "max_completion_tokens": args.max_completion_tokens,
        "messages": messages,
        "stream": False,
    }
    # LFM3 card reference settings: temperature 0.6, top_p 0.95.
    # Official upstream script has temperature commented out; we record this deviation.
    if "o1" not in args.model:
        params["temperature"] = args.temperature
        params["top_p"] = args.top_p

    retries = 0
    delay = BACKOFF_START_S
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = await client.chat.completions.create(**params)
            content = response.choices[0].message.content
            tokens = json.loads(response.usage.model_dump_json())
            if content is None:
                raise ValueError("empty content")
            if retries:
                print(f"retries {question.get('id','?')}: {retries}")
            return question["id"], content, tokens, retries
        except Exception as e:
            if attempt < MAX_ATTEMPTS and _is_retryable(e):
                retries += 1
                jitter = random.uniform(0, delay * 0.25)
                sleep_s = min(delay + jitter, BACKOFF_MAX_S)
                print(f"retry {attempt}/{MAX_ATTEMPTS} {question.get('id','?')}: {type(e).__name__} status={getattr(e, 'status_code', None)} sleep={sleep_s:.1f}s")
                await asyncio.sleep(sleep_s)
                delay = min(delay * 2, BACKOFF_MAX_S)
                continue
            print(f"failed {question.get('id','?')} after {attempt} attempts: {e}")
            return None
    return None


async def attempt_all(client, questions, args):
    semaphore = asyncio.Semaphore(args.num_workers)

    async def bound_func(question):
        async with semaphore:
            return await attempt_question(client, question, args)

    return await tqdm_asyncio.gather(*[bound_func(q) for q in questions])


def is_text_only(question):
    image = question.get("image")
    return not image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--max_completion_tokens", type=int, default=8192)
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--top_p", type=float, default=0.95)
    parser.add_argument("--num_workers", type=int, default=10)
    parser.add_argument("--max_samples", type=int, default=None)
    parser.add_argument("--subset", type=str, default="text-only", choices=["text-only", "full"])
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    assert args.num_workers > 1, "num_workers must be 2 or greater"
    client = build_client()
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

    results = asyncio.run(attempt_all(client, questions, args))
    failed = []
    for result in results:
        if result is None:
            # attempt_question already logged the ID
            continue
        unique_id, response, usage, retries = result
        predictions[unique_id] = {
            "model": args.model,
            "response": response,
            "usage": usage,
        }

    # Reconstruct failed IDs from this batch (None results)
    failed = [q["id"] for q, r in zip(questions, results) if r is None]
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=4)
    print(f"wrote {len(predictions)} predictions to {args.output}")
    if failed:
        print(f"failed_after_retries={len(failed)} ids={failed}")


if __name__ == "__main__":
    main()
