"""judge.py - grades AA-Omniscience answers with the official grader template on an OpenAI-compatible chat endpoint.

Usage: python judge.py <prepare dir> <answers.json from generate.py> <out grades.json>
Judge endpoint from the environment: JUDGE_BASE_URL, JUDGE_MODEL, JUDGE_API_KEY.

Protocol (as in the AA-Omniscience README):
- prompt = OMNISCIENCE_GRADER_TEMPLATE with {question}, {target}, {predicted_answer} filled by plain replacement, sent
  as one user message;
- the judge's reply must be exactly one letter A/B/C/D (spaces, ** and quotes stripped): A correct, B incorrect,
  C partially correct, D not attempted; anything else is a judge error (not a grade) and only then is the request
  repeated, at most 30 repeats in total;
- controls before grading, 4 questions (idx 0, 150, 300, 450) x 3: answer = gold target -> A, the gold target of
  question idx+300 -> B, "I don't know." -> D; any mismatch stops the run;
- one pass over the 600 answers in key order, no repeats of graded items; an answer that is missing (a transport
  error during generation) is not sent to the judge and the report is marked incomplete.
"""
import concurrent.futures as cf
import json
import os
import sys
import threading

import httpx

CONTROL_IDX, IDK = (0, 150, 300, 450), "I don't know."
CLASSES = {"A": "correct", "B": "incorrect", "C": "partial", "D": "not_attempted"}
MAX_REPEATS, CONCURRENCY = 30, 4


def parse(t):
    s = (t or "").strip().replace("**", "").strip().strip("\"'").strip()
    if s not in CLASSES:
        raise ValueError(f"not a letter A-D ({len(t or '')} chars)")
    return s


def main(prep, answers_path, out):
    base, model, key = os.environ["JUDGE_BASE_URL"], os.environ["JUDGE_MODEL"], os.environ.get("JUDGE_API_KEY", "EMPTY")
    template = json.load(open(os.path.join(prep, "templates.json"), encoding="utf-8"))["grader_template"]
    keys = [json.loads(l) for l in open(os.path.join(prep, "key.jsonl"), encoding="utf-8").read().split("\n") if l.strip()]
    answers = json.load(open(answers_path, encoding="utf-8"))["answers"]
    if not set(answers) <= {str(i) for i in range(len(keys))} or any(answers[str(k["idx"])]["id"] != k["id"]
                                                                     for k in keys if str(k["idx"]) in answers):
        sys.exit("judge.py: answers do not match the key (idx and ids)")
    asked = [k for k in keys if str(k["idx"]) in answers]  # all 600, or the first N with run.sh --limit N
    client = httpx.Client(timeout=900, headers={"Authorization": f"Bearer {key}"})
    lock, repeats = threading.Lock(), [0]

    def grade(question, target, predicted):
        prompt = template.replace("{question}", question).replace("{target}", target).replace("{predicted_answer}", predicted)
        while True:
            r = client.post(f"{base}/chat/completions", json={"model": model, "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            try:
                return parse(r.json()["choices"][0]["message"].get("content"))
            except ValueError:
                with lock:
                    repeats[0] += 1
                    if repeats[0] > MAX_REPEATS:
                        raise SystemExit("judge.py: more than 30 judge replies that are not a letter")

    for i in CONTROL_IDX:
        k, other = keys[i], keys[(i + 300) % len(keys)]
        for predicted, want in ((k["answer"], "A"), (other["answer"], "B"), (IDK, "D")):
            got = grade(k["question"], k["answer"], predicted)
            if got != want:
                sys.exit(f"judge.py: control idx {i} expected {want}, judge said {got}")
    todo = [k for k in asked if answers[str(k["idx"])]["response"] is not None]
    with cf.ThreadPoolExecutor(CONCURRENCY) as ex:
        letters = dict(zip([k["id"] for k in todo],
                           ex.map(lambda k: grade(k["question"], k["answer"], answers[str(k["idx"])]["response"]), todo)))
    result = {"judge": {"base_url": base, "model": model}, "controls": "12/12", "repeats": repeats[0],
              "missing_answers": [k["id"] for k in asked if answers[str(k["idx"])]["response"] is None],
              "grades": {k["id"]: letters.get(k["id"]) for k in asked}}
    json.dump(result, open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print(f"judge.py: {len(letters)} graded, {len(result['missing_answers'])} without an answer, {repeats[0]} repeats")


if __name__ == "__main__":
    main(*sys.argv[1:4])
