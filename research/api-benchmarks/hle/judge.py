"""Judge HLE predictions with an Anthropic Claude judge.

Based on centerforaisafety/hle hle_eval/run_judge_results.py @ 22ed3074b1e7b134bcbc09028d0ba320839b0655
(JUDGE_PROMPT, ExtractedAnswer schema, metrics and calibration error copied verbatim; provider
changed to Anthropic as a documented deviation, see README.md "Deviations").

The prompt below is copied verbatim from the pinned upstream file (hash check against the commit in
run.sh). Do not edit it.
"""

import argparse
import asyncio
import copy
import json
import math
import os
import random
import time
from pathlib import Path
from typing import Literal

import numpy as np
from anthropic import AsyncAnthropic
from datasets import load_dataset
from pydantic import BaseModel
from tqdm.asyncio import tqdm_asyncio

JUDGE_PROMPT = """Judge whether the following [response] to [question] is correct or not based on the precise and unambiguous [correct_answer] below.

[question]: {question}

[response]: {response}

Your judgement must be in the format and criteria specified below:

extracted_final_answer: The final exact answer extracted from the [response]. Put the extracted answer as 'None' if there is no exact, final answer to extract from the response.

[correct_answer]: {correct_answer}

reasoning: Explain why the extracted_final_answer is correct or incorrect based on [correct_answer], focusing only on if there are meaningful differences between [correct_answer] and the extracted_final_answer. Do not comment on any background to the problem, do not attempt to solve the problem, do not argue for any answer different than [correct_answer], focus only on whether the answers match.

correct: Answer 'yes' if extracted_final_answer matches the [correct_answer] given above, or is within a small margin of error for numerical problems. Answer 'no' otherwise, i.e. if there if there is any inconsistency, ambiguity, non-equivalency, or if the extracted answer is incorrect.


confidence: The extracted confidence score between 0|\\%| and 100|\\%| from [response]. Put 100 if there is no confidence score available."""

TOOLS = [
    {
        "name": "judge",
        "description": "Return the judgement of the model response against the correct answer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "extracted_final_answer": {"type": "string"},
                "reasoning": {"type": "string"},
                "correct": {"type": "string", "enum": ["yes", "no"]},
                "confidence": {"type": "integer"},
                "strict": {"type": "boolean", "const": True},
            },
            "required": [
                "extracted_final_answer",
                "reasoning",
                "correct",
                "confidence",
                "strict",
            ],
            "additionalProperties": False,
        },
    }
]


class ExtractedAnswer(BaseModel):
    extracted_final_answer: str
    reasoning: str
    correct: Literal["yes", "no"]
    confidence: int
    strict: Literal[True]


NO_TOOL_CALL_COUNT = 0

RETRYABLE_STATUS = {429, 500, 502, 503, 504, 529}
MAX_ATTEMPTS = 10
BACKOFF_START_S = 5.0
BACKOFF_MAX_S = 300.0


def load_dotenv():
    # research/.env (two levels up from this file) may hold ANTHROPIC_API_KEY.
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.is_file():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _is_retryable(exc: Exception) -> bool:
    import anthropic as _anthropic

    if isinstance(exc, (_anthropic.RateLimitError, _anthropic.APITimeoutError,
                        _anthropic.APIConnectionError, _anthropic.InternalServerError,
                        _anthropic.OverloadedError)):
        return True
    if isinstance(exc, _anthropic.APIStatusError):
        return getattr(exc, "status_code", None) in RETRYABLE_STATUS
    return False


def build_client():
    load_dotenv()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set (put it in research/.env or the environment)")
    return AsyncAnthropic(api_key=key, timeout=300.0, max_retries=0)


async def extract_answer(client, args, question, correct_answer, response):
    prompt = JUDGE_PROMPT.format(question=question, correct_answer=correct_answer, response=response)
    delay = BACKOFF_START_S
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            msg = await client.messages.create(
                model=args.judge,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                tools=TOOLS,
                tool_choice={"type": "auto"},
            )
            tool_use = None
            for block in msg.content:
                if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "judge":
                    tool_use = block
                    break
            if tool_use is None:
                global NO_TOOL_CALL_COUNT
                NO_TOOL_CALL_COUNT += 1
                raise ValueError("judge tool was not called")
            data = tool_use.input
            # Validate through pydantic to enforce the schema.
            parsed = ExtractedAnswer.model_validate(data)
            usage = {
                "input_tokens": getattr(msg.usage, "input_tokens", 0),
                "output_tokens": getattr(msg.usage, "output_tokens", 0),
            }
            return {
                "correct_answer": correct_answer,
                "model_answer": parsed.extracted_final_answer,
                "reasoning": parsed.reasoning,
                "correct": parsed.correct,
                "confidence": parsed.confidence,
                "_judge_usage": usage,
            }
        except Exception as e:
            if attempt < MAX_ATTEMPTS:
                jitter = random.uniform(0, delay * 0.25)
                sleep_s = min(delay + jitter, BACKOFF_MAX_S)
                print(f"retry {attempt}/{MAX_ATTEMPTS}: {type(e).__name__} sleep={sleep_s:.1f}s", flush=True)
                await asyncio.sleep(sleep_s)
                delay = min(delay * 2, BACKOFF_MAX_S)
                continue
            print(f"failed after {attempt} attempts: {e}", flush=True)
            return None
    return None


async def add_judge_response(client, args, question, predictions):
    unique_id = question["id"]
    prediction = copy.deepcopy(predictions[unique_id])
    if "judge_response" in prediction:
        return unique_id, prediction
    content = await extract_answer(client, args, question["question"], question["answer"], prediction["response"])
    if content is not None:
        # Keep the judge token usage out of the persisted judge_response (official fields only).
        usage = content.pop("_judge_usage", None)
        if usage is not None:
            prediction.setdefault("_judge_usage", usage)
        prediction["judge_response"] = content
        return unique_id, prediction
    return None, None


async def judge_all_responses(client, args, questions, predictions):
    semaphore = asyncio.Semaphore(args.num_workers)

    async def bound_func(question):
        async with semaphore:
            return await add_judge_response(client, args, question, predictions)

    return await tqdm_asyncio.gather(*[bound_func(q) for q in questions])


# source: https://github.com/hendrycks/outlier-exposure/blob/master/utils/calibration_tools.py
def calib_err(confidence, correct, p="2", beta=100):
    idxs = np.argsort(confidence)
    confidence = confidence[idxs]
    correct = correct[idxs]
    bins = [[i * beta, (i + 1) * beta] for i in range(len(confidence) // beta)]
    if bins:
        bins[-1] = [bins[-1][0], len(confidence)]
    cerr = 0
    total_examples = len(confidence)
    for i in range(len(bins) - 1):
        bin_confidence = confidence[bins[i][0]:bins[i][1]]
        bin_correct = correct[bins[i][0]:bins[i][1]]
        num_examples_in_bin = len(bin_confidence)
        if num_examples_in_bin > 0:
            difference = np.abs(np.nanmean(bin_confidence) - np.nanmean(bin_correct))
            if p == "2":
                cerr += num_examples_in_bin / total_examples * np.square(difference)
            elif p == "1":
                cerr += num_examples_in_bin / total_examples * difference
            elif p in ("infty", "infinity", "max"):
                cerr = np.maximum(cerr, difference)
            else:
                assert False, "p must be '1', '2', or 'infty'"
    if p == "2":
        cerr = np.sqrt(cerr)
    return cerr


def dump_metrics(predictions, n):
    correct = []
    confidence = []
    for k, v in predictions.items():
        if "judge_response" in v:
            jr = v["judge_response"]
            correct.append("yes" in jr["correct"])
            confidence.append(jr["confidence"])
        else:
            print(f"Missing judge response for {k}, you should rerun the judge")
    correct = np.array(correct)
    confidence = np.array(confidence) / 100
    if len(correct) != n:
        print(f"Available predictions: {len(correct)} | Total questions: {n}")
    accuracy = round(100 * sum(correct) / n, 2) if n else 0.0
    confidence_half_width = round(1.96 * math.sqrt(accuracy * (100 - accuracy) / n), 2) if n else 0.0
    calibration_error = 100 * round(calib_err(confidence, correct, p="2", beta=100), 2) if len(correct) else 0.0
    print("*** Metrics ***")
    print(f"Accuracy: {accuracy}% +/- {confidence_half_width}% | n = {n}")
    print(f"Calibration Error: {calibration_error}")
    return accuracy, confidence_half_width, calibration_error


def build_batch_requests(questions, predictions):
    requests = []
    for q in questions:
        qid = q["id"]
        if qid not in predictions:
            continue
        pred = predictions[qid]
        prompt = JUDGE_PROMPT.format(question=q["question"], correct_answer=q["answer"], response=pred["response"])
        requests.append({
            "custom_id": qid,
            "params": {
                "model": None,  # filled by caller
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}],
                "tools": TOOLS,
                "tool_choice": {"type": "auto"},
            },
        })
    return requests


def run_batch(args, questions, predictions, judged_predictions):
    import anthropic

    load_dotenv()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    client = anthropic.Anthropic(api_key=key, timeout=300.0, max_retries=0)

    # Only unjudged.
    todo = [q for q in questions if q["id"] in predictions and q["id"] not in judged_predictions]
    if args.limit and args.limit > 0:
        todo = todo[: args.limit]

    if not todo:
        print("nothing to judge")
        return judged_predictions, 0, 0

    requests = build_batch_requests(todo, predictions)
    for r in requests:
        r["params"]["model"] = args.judge

    print(f"submitting batch with {len(requests)} requests", flush=True)
    batch = client.messages.batches.create(requests=requests)
    batch_id = batch.id
    print(f"batch id: {batch_id}", flush=True)

    poll = args.poll_interval if args.poll_interval and args.poll_interval > 0 else 30
    while True:
        b = client.messages.batches.retrieve(batch_id)
        status = b.processing_status
        counts = getattr(b, "request_counts", None)
        print(f"batch {batch_id}: {status} counts={counts}", flush=True)
        if status == "ended":
            break
        time.sleep(poll)

    total_in = 0
    total_out = 0
    no_tool = 0
    retry_ids = []
    new_judged = {}

    for entry in client.messages.batches.results(batch_id):
        qid = entry.custom_id
        result = entry.result
        if result.type != "succeeded":
            print(f"batch entry {qid}: {result.type} {getattr(result, 'error', None)}", flush=True)
            continue
        msg = result.message
        tool_use = None
        for block in msg.content:
            if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "judge":
                tool_use = block
                break
        if tool_use is None:
            no_tool += 1
            retry_ids.append(qid)
            continue
        try:
            parsed = ExtractedAnswer.model_validate(tool_use.input)
        except Exception as e:
            print(f"batch entry {qid}: schema error {e}", flush=True)
            retry_ids.append(qid)
            continue
        pred = copy.deepcopy(predictions[qid])
        content = {
            "correct_answer": predictions[qid] and None,  # placeholder, fix below
        }
        # We need the correct answer from the dataset question; find it.
        # (handled after: store qid and fill correct_answer from questions map)
        usage = {
            "input_tokens": getattr(msg.usage, "input_tokens", 0),
            "output_tokens": getattr(msg.usage, "output_tokens", 0),
        }
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]

        # correct answer lookup happens in caller-provided map; store temporarily
        entry._parsed = parsed
        entry._usage = usage
        new_judged[qid] = (pred, parsed, usage)

    # Resolve correct_answer and finalize
    qmap = {q["id"]: q for q in questions}
    for qid in list(new_judged.keys()):
        pred, parsed, usage = new_judged[qid]
        q = qmap[qid]
        content = {
            "correct_answer": q["answer"],
            "model_answer": parsed.extracted_final_answer,
            "reasoning": parsed.reasoning,
            "correct": parsed.correct,
            "confidence": parsed.confidence,
        }
        pred["judge_response"] = content
        pred["_judge_usage"] = usage
        judged_predictions[qid] = pred

    # Retry items without a tool call (online, with backoff) up to 3 attempts.
    if retry_ids:
        print(f"retrying {len(retry_ids)} items without tool call", flush=True)
        async def _retry():
            client_async = build_client()
            sem = asyncio.Semaphore(args.num_workers)

            async def one(qid):
                global NO_TOOL_CALL_COUNT
                q = qmap[qid]
                for _ in range(3):
                    res = await extract_answer(client_async, args, q["question"], q["answer"], predictions[qid]["response"])
                    if res is not None:
                        usage = res.pop("_judge_usage", None)
                        pred = copy.deepcopy(predictions[qid])
                        if usage:
                            pred["_judge_usage"] = usage
                            nonlocal total_in, total_out
                            total_in += usage.get("input_tokens", 0)
                            total_out += usage.get("output_tokens", 0)
                        pred["judge_response"] = res
                        judged_predictions[qid] = pred
                        return
                print(f"retry failed for {qid}", flush=True)

            await asyncio.gather(*[one(qid) for qid in retry_ids])

        asyncio.run(_retry())

    # Strip _judge_usage from persisted judge_response? Keep usage summary separately.
    # Remove helper key from judged_predictions values? Keep for token totals but not required.
    # We'll keep _judge_usage in prediction (not in jsonl.gz) - summarize ignores it.
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(judged_predictions, f, indent=2)

    # Token totals
    for qid, pred in judged_predictions.items():
        u = pred.pop("_judge_usage", None)
        if u:
            # already counted during parse/retry; avoid double count by not re-adding
            pass

    dump_metrics(judged_predictions, n=len(judged_predictions) if args.limit else len(predictions))
    print(f"wrote judged predictions to {args.output}")
    print(f"NO_TOOL_CALLS n={no_tool}")
    print(f"JUDGE_TOKENS input={total_in} output={total_out} total={total_in + total_out} n={len(judged_predictions)}")
    # 50% batch discount note
    print("BATCH_DISCOUNT=0.5 (Message Batches API)")
    return judged_predictions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, required=True)
    parser.add_argument("--predictions", type=str, required=True)
    parser.add_argument("--num_workers", type=int, default=5)
    parser.add_argument("--judge", type=str, default="claude-opus-5-5")
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch", action="store_true", help="Use the Message Batches API (50%% discount)")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between batch status polls")
    args = parser.parse_args()
    assert args.num_workers > 1, "num_workers must be 2 or greater"

    client = build_client()
    dataset = load_dataset(args.dataset, split="test").to_dict()
    questions = [dict(zip(dataset.keys(), values)) for values in zip(*dataset.values())]
    total_questions = len(questions)

    with open(args.predictions, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    judged_predictions = {}
    if os.path.exists(args.output):
        with open(args.output, "r", encoding="utf-8") as f:
            judged_predictions = json.load(f)

    if args.batch:
        run_batch(args, questions, predictions, judged_predictions)
        return

    # text-only subset handling is done at generation time; here we only judge
    # questions that were predicted and are not already judged.
    questions = [q for q in questions if q["id"] in predictions and q["id"] not in judged_predictions]
    if args.limit and args.limit > 0:
        questions = questions[: args.limit]

    results = asyncio.run(judge_all_responses(client, args, questions, predictions))

    total_in = 0
    total_out = 0
    for unique_id, preds in results:
        if unique_id is not None:
            judged_predictions[unique_id] = preds
            usage = preds.pop("_judge_usage", None)
            if usage:
                total_in += usage.get("input_tokens", 0)
                total_out += usage.get("output_tokens", 0)

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(judged_predictions, f, indent=2)

    dump_metrics(judged_predictions, n=len(judged_predictions) if args.limit else total_questions)
    print(f"wrote judged predictions to {args.output}")
    print(f"NO_TOOL_CALLS n={NO_TOOL_CALL_COUNT}")
    print(f"JUDGE_TOKENS input={total_in} output={total_out} total={total_in + total_out} n={len(results)}")


if __name__ == "__main__":
    main()
