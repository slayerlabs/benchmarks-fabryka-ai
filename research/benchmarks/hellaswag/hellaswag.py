"""HellaSwag scoring without a model, plus the commands that fetch data and score.

The prompt is lm-eval ``hellaswag/utils.py`` at tag ``v0.4.9.1``. That file is
the same as the Space commit named in ``ORIGINAL.md``. ``acc`` takes the
higher log-likelihood. ``acc_norm`` divides it by the number of characters in
the choice, without the leading space lm-eval adds when it scores the choice.

    python benchmarks/hellaswag/hellaswag.py show
        print the smoke-test rows from RECIPE.md (needs network, no weights)
    python benchmarks/hellaswag/hellaswag.py fetch --out DIR
        download the pinned validation parquet and write DIR/data.json
    python benchmarks/hellaswag/hellaswag.py score ...
        full validation with lm-eval; used by instance.sh on a GPU

lm-eval and pyarrow are imported only inside ``fetch`` and ``score``. The
offline test imports this file and does not have those packages.
"""

import argparse
import gzip
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


def preprocess(text):
    """WikiHow bracket cleanup from lm-eval.

    ``str.replace`` collapses every non-overlapping pair of spaces once. It does
    not repeat, so three spaces become two. The leading space left by a removed
    bracket stays, and it counts in ``acc_norm``.
    """
    text = text.strip()
    text = text.replace(" [title]", ". ")
    text = re.sub(r"\[.*?\]", "", text)
    text = text.replace("  ", " ")
    return text


def query_and_choices(doc):
    """Return the context string and the four cleaned endings."""
    ctx = doc["ctx_a"] + " " + doc["ctx_b"].capitalize()
    query = preprocess(doc["activity_label"] + ": " + ctx)
    choices = [preprocess(ending) for ending in doc["endings"]]
    return query, choices


def gold(doc):
    """Dataset ``label`` is the index of the correct ending, as a string or an int."""
    return int(doc["label"])


def choice_lengths(choices):
    """Character lengths used by ``acc_norm``. An empty choice counts as 1, so we never divide by zero."""
    return [max(len(choice), 1) for choice in choices]


def predict(logliki, lengths=None):
    """Index of the best score. A tie keeps the earlier ending, as ``max`` does."""
    if lengths is None:
        return max(range(len(logliki)), key=lambda i: logliki[i])
    return max(range(len(logliki)), key=lambda i: logliki[i] / lengths[i])


def score_question(doc, logliki):
    """One question: gold, both picks, and both accuracies. ``logliki`` has one value per ending."""
    _, choices = query_and_choices(doc)
    lengths = choice_lengths(choices)
    if len(logliki) != len(choices):
        raise ValueError(f"{len(logliki)} log-likelihoods for {len(choices)} endings")
    picked = predict(logliki)
    picked_norm = predict(logliki, lengths)
    correct = gold(doc)
    return {
        "gold": correct,
        "lengths": lengths,
        "pred": picked,
        "pred_norm": picked_norm,
        "acc": float(picked == correct),
        "acc_norm": float(picked_norm == correct),
    }


def summarize(rows):
    """Random baseline, majority baseline, and the share of the most common ``acc_norm`` pick.

    HellaSwag has four endings, so the random baseline is 1/4. The majority baseline is the
    share of the most common correct index on these rows. A tie between indexes keeps the earlier one.
    """
    if not rows:
        raise ValueError("no rows")
    n = len(rows)
    golds = [row["gold"] for row in rows]
    preds = [row["pred_norm"] for row in rows]
    majority_index = max(range(4), key=lambda i: golds.count(i))
    return {
        "n": n,
        "acc_norm": sum(row["acc_norm"] for row in rows) / n,
        "random": 0.25,
        "majority": golds.count(majority_index) / n,
        "majority_index": majority_index,
        "most_frequent_prediction": max(preds.count(i) for i in range(4)) / n,
    }


# Pinned in issue #24 and checked in RECIPE.md. The file is not stored in the repo.
DATA_REPO = "Rowan/hellaswag"
DATA_REVISION = "218ec52e09a7e7462a5400043bb9a69a41d06b76"
PARQUET_NAME = "data/validation-00000-of-00001.parquet"
PARQUET_SHA256 = "899813071e1e95efafec90f856e1987d2150fa4d020fc005df6962c259f660cd"
TRAIN_PARQUET_NAME = "data/train-00000-of-00001.parquet"
TRAIN_SHA256 = "cacb12587faa63d7f723a72d61d12bfa94b140446f5a6a0a2e1c6906ab88bf02"
# Row index in the validation split. These are the rows read for the smoke test.
SMOKE_ROWS = [0, 1, 3243, 5000, 7500, 10000, 10041]
EUROLLM_REPO = "utter-project/EuroLLM-1.7B"
EUROLLM_REVISION = "c730cd9b616799ace3c65e927d63191446f59374"
SLAYER_REPO = "SlayerLab/Slayer1B-1.06"
SLAYER_REVISION = "ef81be58742544ad32e1afab38db011fec209609"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def dataset_row(offset):
    """One validation row from the Hub viewer. ``offset`` is the row index, not ``ind``."""
    query = urllib.parse.urlencode({
        "dataset": DATA_REPO,
        "config": "default",
        "split": "validation",
        "offset": offset,
        "length": 1,
    })
    url = "https://datasets-server.huggingface.co/rows?" + query
    request = urllib.request.Request(url, headers={"User-Agent": "hellaswag-show"})
    with urllib.request.urlopen(request, timeout=90) as response:
        payload = json.load(response)
    row = payload["rows"][0]
    if row["row_idx"] != offset:
        raise ValueError(f"viewer returned row {row['row_idx']} for offset {offset}")
    return row["row"]


def format_row(offset, row):
    """Full prompt and the four endings. The correct ending is the dataset label, not a model pick."""
    query, choices = query_and_choices(row)
    correct = gold(row)
    lines = [
        f"wiersz {offset}  ind {row['ind']}  źródło {row['source_id']}  split_type {row['split_type']}",
        "split_type opisuje zbiór: indomain = czynność była w treningu autorów, zeroshot = nie była.",
        "To nie jest wynik modelu.",
        "prompt:",
        query,
        f"poprawne zakończenie: numer {correct} (pole label w zbiorze)",
    ]
    for index, choice in enumerate(choices):
        mark = "  <-- poprawne" if index == correct else ""
        lines.append(f"zakończenie {index}:{mark}")
        lines.append(choice)
    return "\n".join(lines)


def show(_args):
    for offset in SMOKE_ROWS:
        print(format_row(offset, dataset_row(offset)))
        print()


def _download_checked(out, filename, remote_name, expected_sha):
    target = out / filename
    url = f"https://huggingface.co/datasets/{DATA_REPO}/resolve/{DATA_REVISION}/{remote_name}"
    request = urllib.request.Request(url, headers={"User-Agent": "hellaswag-fetch"})
    with urllib.request.urlopen(request, timeout=300) as response, open(target, "wb") as handle:
        handle.write(response.read())
    digest = sha256_file(target)
    if digest != expected_sha:
        raise SystemExit(f"sha256 mismatch for {filename}: {digest}")
    return target, digest


def fetch(args):
    """Download the pinned train and validation parquets. pyarrow is imported here so tests can load this file."""
    import pyarrow.parquet as pq

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    validation, validation_sha = _download_checked(out, "validation.parquet", PARQUET_NAME, PARQUET_SHA256)
    train, train_sha = _download_checked(out, "train.parquet", TRAIN_PARQUET_NAME, TRAIN_SHA256)
    manifest = {
        "repo": DATA_REPO,
        "revision": DATA_REVISION,
        "validation": {"path": PARQUET_NAME, "sha256": validation_sha, "n_rows": pq.read_metadata(validation).num_rows,
                       "local": str(validation.resolve())},
        "train": {"path": TRAIN_PARQUET_NAME, "sha256": train_sha, "n_rows": pq.read_metadata(train).num_rows,
                  "local": str(train.resolve())},
    }
    (out / "data.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


def build_lm(args):
    if args.model == "slayer":
        import slayer_lm
        return slayer_lm.SlayerLM(pretrained=args.pretrained, dtype="float32", batch_size=args.batch,
                                   device=args.device)
    from lm_eval.models.huggingface import HFLM
    return HFLM(pretrained=args.pretrained, revision=args.revision, dtype="float32", batch_size=args.batch,
                device=args.device)


def score(args):
    """Run the lm-eval ``hellaswag`` task on the local parquet. Heavy imports stay inside this function."""
    import lm_eval
    import pyarrow.parquet as pq
    import torch
    import transformers
    from lm_eval import simple_evaluate
    from lm_eval.tasks import TaskManager, get_task_dict

    manifest = json.loads((Path(args.data) / "data.json").read_text())
    validation = manifest["validation"]["local"]
    train = manifest["train"]["local"]
    if sha256_file(validation) != manifest["validation"]["sha256"]:
        raise SystemExit(f"sha256 mismatch: {validation}")
    if sha256_file(train) != manifest["train"]["sha256"]:
        raise SystemExit(f"sha256 mismatch: {train}")
    rows = pq.read_table(validation).to_pylist()
    fewshot = int(args.fewshot)
    lm = build_lm(args)
    task = get_task_dict(["hellaswag"], TaskManager())["hellaswag"]
    task.config.dataset_path = "parquet"
    task.config.dataset_name = None
    task.config.dataset_kwargs = {"data_files": {"train": train, "validation": validation}}
    task.config.num_fewshot = fewshot
    result = simple_evaluate(model=lm, tasks=[task], num_fewshot=fewshot, log_samples=True, bootstrap_iters=0,
                             limit=None if args.limit is None else int(args.limit),
                             random_seed=0, numpy_random_seed=1234, torch_random_seed=1234, fewshot_random_seed=1234)
    samples = sorted(result["samples"]["hellaswag"], key=lambda sample: sample["doc_id"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out, "wt", encoding="utf-8") as handle:
        for sample in samples:
            row = rows[sample["doc_id"]]
            if int(sample["doc"]["gold"]) != int(row["label"]):
                raise SystemExit(f"doc {sample['doc_id']} gold does not match parquet label")
            scored = score_question(row, [float(item[0]) for item in sample["filtered_resps"][:4]])
            scored.update({"idx": sample["doc_id"], "ind": row["ind"], "source_id": row["source_id"],
                           "split_type": row["split_type"],
                           "lm_eval_acc": sample.get("acc"), "lm_eval_acc_norm": sample.get("acc_norm")})
            handle.write(json.dumps(scored) + "\n")
    meta = {
        "model": args.repo, "revision": args.revision, "wrapper": args.model, "pretrained": args.pretrained,
        "fewshot": fewshot, "n": len(samples), "lm_eval": lm_eval.__version__, "torch": torch.__version__,
        "transformers": transformers.__version__,
        "device": torch.cuda.get_device_name(0) if str(args.device).startswith("cuda") else args.device,
        "batch": args.batch, "dtype": "float32",
        "validation_sha256": manifest["validation"]["sha256"], "train_sha256": manifest["train"]["sha256"],
        "date": time.strftime("%Y-%m-%d", time.gmtime()),
    }
    Path(str(out).replace(".jsonl.gz", ".meta.json")).write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    fetch_parser = sub.add_parser("fetch")
    fetch_parser.add_argument("--out", required=True)
    score_parser = sub.add_parser("score")
    score_parser.add_argument("--model", choices=["hf", "slayer"], required=True)
    score_parser.add_argument("--pretrained", required=True)
    score_parser.add_argument("--repo", required=True)
    score_parser.add_argument("--revision", required=True)
    score_parser.add_argument("--data", required=True)
    score_parser.add_argument("--out", required=True)
    score_parser.add_argument("--fewshot", required=True)
    score_parser.add_argument("--device", default="cuda")
    score_parser.add_argument("--batch", default="1")
    score_parser.add_argument("--limit")
    args = parser.parse_args()
    {"show": show, "fetch": fetch, "score": score}[args.cmd](args)


if __name__ == "__main__":
    main()
