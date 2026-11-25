"""AA-Omniscience-Public: question file for generate.py and answer key for judge.py, from the pinned Hugging Face revision.

Usage: python prepare.py <out dir>

Downloads AA-Omniscience_dataset_public.csv and README.md of ArtificialAnalysis/AA-Omniscience-Public at the pinned
revision (sha256 checked) and cuts the two prompt templates (OMNISCIENCE_ANSWER_PROMPT, OMNISCIENCE_GRADER_TEMPLATE)
out of the README verbatim. Writes:
  questions.jsonl  {idx, id, domain, topic, subtopic, system, user}   -> generate.py (no answers)
  key.jsonl        {idx, id, question, answer}                         -> judge.py only
  templates.json   {answer_prompt, grader_template}
"""

import csv
import hashlib
import json
import os
import re
import sys

from huggingface_hub import hf_hub_download

REPO = "ArtificialAnalysis/AA-Omniscience-Public"
REVISION = "e4883edbb9f5ccf2b2a8fdc6fb65e01a58e99849"
FILES = {
    "AA-Omniscience_dataset_public.csv": "1e04603dafa3bd0d16d8151f07a5eb74c43d90c3a85d2fca120da2359174d02f",
    "README.md": "e75f912ebd1c5ea40b47692a98bc684e13da32af226694024f4a94eab7327481",
}


def fetch(name):
    path = hf_hub_download(REPO, name, revision=REVISION, repo_type="dataset")
    data = open(path, "rb").read()
    if hashlib.sha256(data).hexdigest() != FILES[name]:
        sys.exit(f"prepare.py: {name} @ {REVISION[:8]} has another sha256")
    return data.decode("utf-8")


def block(readme, name):
    found = re.findall(name + r' = """\n(.*?)"""', readme, flags=re.S)
    if len(found) != 1:
        sys.exit(f"prepare.py: {name} found {len(found)} times in README.md")
    return found[0]


def main(out):
    readme = fetch("README.md")
    answer_prompt = block(readme, "OMNISCIENCE_ANSWER_PROMPT")
    grader = block(readme, "OMNISCIENCE_GRADER_TEMPLATE").strip()  # the README applies .strip()
    for field in ("{domain}", "{subtopic}"):
        if field not in answer_prompt:
            sys.exit(f"prepare.py: {field} missing in the answer prompt")
    for field in ("{question}", "{target}", "{predicted_answer}"):
        if field not in grader:
            sys.exit(f"prepare.py: {field} missing in the grader template")
    rows = list(csv.DictReader(fetch("AA-Omniscience_dataset_public.csv").splitlines(keepends=True)))
    if len(rows) != 600 or len({w["question_id"] for w in rows}) != 600:
        sys.exit(f"prepare.py: {len(rows)} rows or duplicate question_id, expected 600 distinct")
    os.makedirs(out, exist_ok=True)
    with (
        open(os.path.join(out, "questions.jsonl"), "w", encoding="utf-8", newline="\n") as q,
        open(os.path.join(out, "key.jsonl"), "w", encoding="utf-8", newline="\n") as k,
    ):
        for i, w in enumerate(rows):
            q.write(
                json.dumps(
                    {
                        "idx": i,
                        "id": w["question_id"],
                        "domain": w["domain"],
                        "topic": w["topic"],
                        "subtopic": w["subtopic"],
                        "system": answer_prompt.format(domain=w["domain"], subtopic=w["subtopic"]),
                        "user": w["question"],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            k.write(
                json.dumps(
                    {"idx": i, "id": w["question_id"], "question": w["question"], "answer": w["answer"]},
                    ensure_ascii=False,
                )
                + "\n"
            )
    with open(os.path.join(out, "templates.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"answer_prompt": answer_prompt, "grader_template": grader}, f, ensure_ascii=False, indent=1)
    print(f"prepare.py: 600 questions in {out}")


if __name__ == "__main__":
    main(sys.argv[1])
