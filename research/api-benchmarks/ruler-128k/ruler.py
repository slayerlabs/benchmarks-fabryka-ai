"""The pinned RULER checkout as a library, plus the record helpers the scripts of this benchmark share.

Nothing here reimplements RULER. `answer_budgets` reads `scripts/synthetic.yaml` and the data constants, as
`scripts/data/prepare.py` does; `scorer` returns RULER's own `postprocess_pred` (scripts/eval/evaluate.py) and
metric functions (scripts/eval/synthetic/constants.py), so that each sample can be scored on its own.
`evaluate.py` imports NeMo only for `read_manifest`; `nemo_shim/` provides that one function (JSON lines), so the
NeMo toolkit is not installed.
"""

import importlib.util
import json
import sys
from pathlib import Path

SHIM = Path(__file__).resolve().parent / "nemo_shim"
THINK_END = "</think>"


def read_jsonl(path):
    path = Path(path)
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_records(raw_file):
    """index -> the last record written for it (a rerun appends; the newest attempt wins)."""
    return {r["index"]: r for r in read_jsonl(raw_file)}


def answer_text(output):
    """The scored text: everything after the last `</think>`, or the whole output when there is none."""
    return output.rsplit(THINK_END, 1)[-1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _task_bases(ruler_dir):
    import yaml  # only where the RULER checkout is used; the offline test does not need it
    config = yaml.safe_load((Path(ruler_dir) / "scripts" / "synthetic.yaml").read_text(encoding="utf-8"))
    return {task: c["task"] for task, c in config.items()}


def answer_budgets(ruler_dir):
    """task -> RULER's tokens_to_generate."""
    constants = _load("ruler_data_constants", Path(ruler_dir) / "scripts" / "data" / "synthetic" / "constants.py")
    return {task: constants.TASKS[base]["tokens_to_generate"] for task, base in _task_bases(ruler_dir).items()}


def scorer(ruler_dir):
    """(postprocess_pred, {task: metric_fn}) from the pinned RULER evaluator."""
    eval_dir = Path(ruler_dir) / "scripts" / "eval"
    constants = _load("ruler_eval_constants", eval_dir / "synthetic" / "constants.py")
    # evaluate.py parses sys.argv at import time; give it the one required argument.
    argv, sys.argv = sys.argv, ["evaluate.py", "--data_dir", "."]
    sys.path.insert(0, str(SHIM))
    try:
        evaluate = _load("ruler_evaluate", eval_dir / "evaluate.py")
    finally:
        sys.argv = argv
        sys.path.remove(str(SHIM))
    metrics = {task: constants.TASKS[base]["metric_fn"] for task, base in _task_bases(ruler_dir).items()}
    return evaluate.postprocess_pred, metrics
