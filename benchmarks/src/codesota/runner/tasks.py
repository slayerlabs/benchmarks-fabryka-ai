"""lm-eval task configurations of the implemented benchmarks, ported from research/common/zadania.py.

Each configuration is the research pipeline's main variant (`space`) of the benchmark: the same prompt, answer
options, target, and pinned data source, so the same requests reach the model. The research pipeline also adds
`acc_mutual_info`, whose unconditional log-likelihoods feed a diagnostic metric (PMI) that no decision metric uses;
it is left out here, which halves the requests of a multiple-choice benchmark and changes no reported score.
Diagnostic variants (ARC-Challenge in letter format, MedMCQA as cloze) are not ported for the same reason.

`tests/test_runner.py` checks these configurations against research/common/zadania.py.
"""

import functools
import importlib.util
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from codesota.catalog import Benchmark, Dataset

Config = dict[str, Any]
Doc = dict[str, Any]

# acc and acc_norm, as research/common/zadania.py METRYKI_MC without acc_mutual_info (see the module docstring).
MC_METRICS: list[dict[str, Any]] = [
    {"metric": "acc", "aggregation": "mean", "higher_is_better": True},
    {"metric": "acc_norm", "aggregation": "mean", "higher_is_better": True},
]


def lm_eval_module(relative: str) -> ModuleType:
    """A helper module of an lm-eval task (task directories are not packages), from the installed lm-eval."""
    import lm_eval

    path = Path(lm_eval.__file__).resolve().parent / "tasks" / relative
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"lm-eval task module {relative} not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@functools.cache
def task_manager() -> Any:
    """lm-eval's index of its installed tasks, built once (it reads every task YAML)."""
    from lm_eval.tasks import TaskManager

    return TaskManager()


def lm_eval_yaml(name: str) -> Config:
    """The configuration of an lm-eval task from its installed YAML (`!function` resolved, `include` merged)."""
    config: Config = dict(task_manager()._get_config(name))
    for key in ("group", "tag"):
        config.pop(key, None)
    return config


def data_fields(dataset: Dataset) -> Config:
    """The pinned data source as lm-eval dataset fields (research/common/zadania.py `_zrodlo`).

    GOTCHA (from the research pipeline): datasets 3.6 sees only the "default" config of a refs/convert/parquet
    branch, so a named config is read from its parquet files at the pinned commit of that branch.
    """
    if dataset.source == "parquet":
        files = f"hf://datasets/{dataset.repo}@{dataset.parquet_revision}/{dataset.config}/{dataset.split}/*.parquet"
        return {
            "dataset_path": "parquet",
            "dataset_name": None,
            "dataset_kwargs": {"data_files": {"test": files}},
            "test_split": "test",
        }
    if dataset.source == "tsv":
        return {
            "dataset_path": "csv",
            "dataset_name": None,
            "dataset_kwargs": {
                "data_files": {"test": f"hf://datasets/{dataset.repo}@{dataset.revision}/{dataset.file}"},
                "delimiter": "\t",
            },
            "test_split": "test",
        }
    revision = "refs/convert/parquet" if dataset.source == "unpinned-parquet" else dataset.revision
    return {
        "dataset_path": dataset.repo,
        "dataset_name": dataset.config,
        "dataset_kwargs": {"revision": revision},
        "test_split": dataset.split,
    }


def arc_target(doc: Doc) -> int:
    return int(doc["choices"]["label"].index(doc["answerKey"]))


MULTIBLIMP_PAIRS = (("sen", "wrong_sen"), ("sentence_good", "sentence_bad"), ("good", "bad"))


def multiblimp_choices(doc: Doc) -> list[str]:
    """The minimal pair [grammatical, ungrammatical], under the column names the research pipeline accepts."""
    for good, bad in MULTIBLIMP_PAIRS:
        if good in doc and bad in doc:
            return [doc[good], doc[bad]]
    raise KeyError(f"MultiBLiMP: no minimal-pair columns, found {sorted(doc)}")


def _multiple_choice(benchmark: Benchmark, **fields: Any) -> Config:
    assert benchmark.dataset is not None
    return {
        "output_type": "multiple_choice",
        "num_fewshot": 0,
        "metric_list": MC_METRICS,
        "metadata": {"version": 1.0, "benchmark": benchmark.id},
        **data_fields(benchmark.dataset),
        **fields,
    }


def _from_lm_eval(benchmark: Benchmark, name: str) -> Config:
    """An lm-eval task as installed, with the pinned data source (research/common/zadania.py `_z_lm_eval`)."""
    assert benchmark.dataset is not None
    config = lm_eval_yaml(name)
    config.update(data_fields(benchmark.dataset))
    config.update(num_fewshot=0, metadata={**(config.get("metadata") or {}), "benchmark": benchmark.id})
    return config


def _configs() -> dict[str, Callable[[Benchmark], Config]]:
    cloze = "Question: {{question}}\nAnswer:"
    return {
        "arc-easy": lambda b: _multiple_choice(
            b, doc_to_text=cloze, doc_to_choice="{{choices.text}}", doc_to_target=arc_target
        ),
        "arc-challenge": lambda b: _multiple_choice(
            b, doc_to_text=cloze, doc_to_choice="{{choices.text}}", doc_to_target=arc_target
        ),
        "hellaswag": lambda b: _multiple_choice(
            b,
            process_docs=lm_eval_module("hellaswag/utils.py").process_docs,
            doc_to_text="{{query}}",
            doc_to_target="{{label}}",
            doc_to_choice="choices",
        ),
        "piqa": lambda b: _multiple_choice(
            b, doc_to_text="Question: {{goal}}\nAnswer:", doc_to_target="label", doc_to_choice="{{[sol1, sol2]}}"
        ),
        "mathqa": lambda b: _multiple_choice(
            b,
            doc_to_text="Question: {{Problem}}\nAnswer:",
            doc_to_target="{{['a', 'b', 'c', 'd', 'e'].index(correct)}}",
            doc_to_choice=lm_eval_module("mathqa/utils.py").doc_to_choice,
        ),
        "pubmedqa": lambda b: _multiple_choice(
            b,
            doc_to_text=lm_eval_module("pubmedqa/preprocess_pubmedqa.py").doc_to_text,
            doc_to_choice=["yes", "no", "maybe"],
            doc_to_target="final_decision",
        ),
        "medmcqa": lambda b: _multiple_choice(
            b,
            doc_to_text=lm_eval_module("medmcqa/utils_medmcqa.py").doc_to_text,
            doc_to_choice=["A", "B", "C", "D"],
            doc_to_target="cop",
        ),
        "social-iqa": lambda b: _multiple_choice(
            b,
            doc_to_text="Q: {{context}} {{question}}\nA:",
            target_delimiter=" ",
            doc_to_choice="{{[answerA, answerB, answerC]}}",
            doc_to_target="{{ (label|int) - 1 }}",
        ),
        "multiblimp-pl": lambda b: _multiple_choice(
            b, doc_to_text="", target_delimiter=" ", doc_to_choice=multiblimp_choices, doc_to_target=0
        ),
        "winogrande": lambda b: _from_lm_eval(b, "winogrande"),
        "wsc273": lambda b: _from_lm_eval(b, "wsc273"),
        "lambada": lambda b: _from_lm_eval(b, "lambada_openai"),
        "wikitext-2": _wikitext,
    }


def _wikitext(benchmark: Benchmark) -> Config:
    module = lm_eval_module("wikitext/preprocess_wikitext.py")
    config = _multiple_choice(
        benchmark,
        output_type="loglikelihood_rolling",
        doc_to_text="",
        doc_to_target=module.wikitext_detokenizer,
        process_results=module.process_results,
        metric_list=[{"metric": "word_perplexity"}, {"metric": "byte_perplexity"}, {"metric": "bits_per_byte"}],
    )
    return config


def task_config(benchmark: Benchmark, data: Config | None = None) -> Config:
    """The lm-eval configuration of an implemented benchmark, under the task name `codesota_<id>`. `data` replaces
    the pinned data source fields (tests run on local files with the same record structure)."""
    builders = _configs()
    if benchmark.id not in builders or benchmark.status == "not-implemented":
        raise KeyError(f"{benchmark.id} is not implemented in the runner")
    config = builders[benchmark.id](benchmark)
    if data is not None:
        config.update(data)
    name = "codesota_" + benchmark.id.replace("-", "_")
    # lm-eval's results table fails on an alias of None (research/common/zadania.py `konfiguracje`).
    config.update(task=name, task_alias=name)
    return config


def implemented_ids() -> frozenset[str]:
    return frozenset(_configs())
