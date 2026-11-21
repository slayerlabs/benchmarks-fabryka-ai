"""Run one benchmark on one model and write its run directory.

The flow follows research/common/ewaluuj.py `ocen_zadanie` for the full split: build the lm-eval task, check that
every request fits the model's context, evaluate with the research pipeline's seeds, and score the per-question
log-likelihoods with `scoring`. A failure is recorded as a state with its reason, never as a score:

- `unsupported`: a prompt does not fit the model's context window (the evaluation is not shrunk to fit);
- `blocked_access`: the dataset or model needs access the run does not have;
- `failed`: anything else, including a dataset whose size differs from the pinned split.
"""

import json
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from codesota.catalog import Benchmark
from codesota.results import source_id_digest
from codesota.runner import artifact, models, scoring, tasks

CONTEXT_LIMIT = 4096  # research/METODOLOGIA.md: longer inputs are rejected, never truncated
LM_EVAL_SEEDS = {"random_seed": 0, "numpy_random_seed": 1234, "torch_random_seed": 1234, "fewshot_random_seed": 1234}
STATE_OF = {
    "ContextTooLong": "unsupported",
    "GatedRepoError": "blocked_access",
    "RepositoryNotFoundError": "blocked_access",
}


def state_of(error: BaseException) -> str:
    """The state of a benchmark that raised `error`, from the exception or one it was raised from (transformers wraps
    a Hub access error in an OSError)."""
    seen: BaseException | None = error
    visited: set[int] = set()
    while seen is not None and id(seen) not in visited:
        visited.add(id(seen))
        if type(seen).__name__ in STATE_OF:
            return STATE_OF[type(seen).__name__]
        seen = seen.__cause__ or seen.__context__
    return "failed"


class ContextTooLong(ValueError):
    """A prompt and its continuation do not fit the model's context window."""


class DatasetMismatch(ValueError):
    """The loaded split does not have the pinned number of documents, or its sample IDs are not unique."""


@dataclass(frozen=True)
class Outcome:
    benchmark: str
    state: str
    run_dir: Path | None
    value: float | None
    reason: str | None
    seconds: float


def protocol_id(benchmark: Benchmark, bos: models.Bos) -> str:
    return f"codesota.{benchmark.id}.0shot.{bos}-bos.v1"


def build_task(config: dict[str, Any]) -> Any:
    """The lm-eval task object of a configuration. lm-eval 0.4.9.1 drops the `task` key of a dict configuration
    (research/common/ewaluuj.py `zbuduj_zadania`), so the name is written back."""
    import copy

    from lm_eval.tasks import get_task_dict

    task = next(iter(get_task_dict([copy.deepcopy(config)], tasks.task_manager()).values()))
    task.config.task = config["task"]
    return task


def request_pairs(task: Any, doc: dict[str, Any], context: Any) -> list[tuple[str, str]]:
    """(context, continuation) of every log-likelihood request of a document, as lm-eval's `construct_requests`
    builds them: multiple choice = context and delimiter + option; multiple input (WinoGrande) = context + option and
    delimiter + target; log-likelihood = context and target."""
    delimiter = task.config.target_delimiter
    contexts = context if isinstance(context, list) else [context]
    if task.OUTPUT_TYPE != "multiple_choice":
        return [(c, str(task.doc_to_target(doc))) for c in contexts]
    if getattr(task, "multiple_input", 0):
        target = delimiter + str(task.doc_to_target(doc))
        if isinstance(context, list):
            return [(c, target) for c in context]
        return [(context + str(o), target) for o in task.doc_to_choice(doc)]
    return [(c, delimiter + str(o)) for c in contexts for o in task.doc_to_choice(doc)]


def request_tokens(lm: Any, context: str, continuation: str) -> int:
    """How many tokens the model gets for one log-likelihood request, encoded as lm-eval 0.4.9.1 `HFLM.loglikelihood`
    encodes it, with the model class's BOS policy: an empty context is `[prefix_token_id]`, any other pair goes
    through the model's `_encode_pair`. `HFLM` truncates when context + continuation exceeds `max_length` + 1 tokens
    (it feeds `(context + continuation)[:-1]`)."""
    if context == "":
        return 1 + len(lm.tok_encode(continuation))
    context_enc, continuation_enc = lm._encode_pair(context, continuation)
    return len(context_enc) + len(continuation_enc)


def enforce_context_limit(task: Any, lm: Any, limit: int) -> None:
    """Fail a request that would be truncated, counting exactly the tokens the model gets (`request_tokens`). 0-shot
    prompts have no demonstrations to drop, so a prompt that does not fit ends the benchmark as unsupported."""
    original = task.fewshot_context

    def fewshot_context(doc: dict[str, Any], num_fewshot: int, **kwargs: Any) -> Any:
        context = original(doc, num_fewshot=num_fewshot, **kwargs)
        if max(request_tokens(lm, c, x) for c, x in request_pairs(task, doc, context)) > limit + 1:
            raise ContextTooLong(f"{task.config.task}: a prompt exceeds the context limit of {limit} tokens")
        return context

    task.fewshot_context = fewshot_context


def evaluate(
    benchmark: Benchmark, lm: Any, data: dict[str, Any] | None = None
) -> tuple[Any, list[dict[str, Any]], list[Any]]:
    """(task, lm-eval samples in split order, sample IDs in split order). `data`: see `tasks.task_config`."""
    from lm_eval import simple_evaluate

    assert benchmark.dataset is not None and benchmark.scoring is not None
    config = tasks.task_config(benchmark, data)
    task = build_task(config)
    docs = list(task.eval_docs)
    if len(docs) != benchmark.dataset.n_population:
        raise DatasetMismatch(
            f"{benchmark.id}: the split has {len(docs)} documents, the pinned dataset {benchmark.dataset.n_population}"
        )
    field = benchmark.dataset.id_field
    ids = [d.get(field, i) if field else i for i, d in enumerate(docs)]
    if len(set(map(str, ids))) != len(ids):
        raise DatasetMismatch(f"{benchmark.id}: the sample IDs (field {field!r}) are not unique")
    if benchmark.scoring.kind != "rolling":  # rolling windows are cut by the model, there is no prompt to reject
        enforce_context_limit(task, lm, min(CONTEXT_LIMIT, getattr(lm, "max_length", None) or CONTEXT_LIMIT))
    result = simple_evaluate(model=lm, tasks=[task], log_samples=True, bootstrap_iters=0, **LM_EVAL_SEEDS)
    samples = sorted(result["samples"][config["task"]], key=lambda s: s["doc_id"])
    if [s["doc_id"] for s in samples] != list(range(len(docs))):
        raise RuntimeError(f"{benchmark.id}: lm-eval returned samples for documents other than the full split")
    if getattr(task, "multiple_input", 0):  # WinoGrande, WSC273: the gold index comes from doc_to_text
        for s in samples:
            s["gold"] = int(task.doc_to_text(s["doc"]))
    return task, samples, ids


def research_digest(benchmark: Benchmark, samples: list[dict[str, Any]]) -> str | None:
    """`source_id_digest` as the research pipeline computes it, when it used a field other than the sample ID."""
    assert benchmark.dataset is not None
    field = benchmark.dataset.research_id_field
    return source_id_digest(s["doc"][field] for s in samples) if field else None


def score(benchmark: Benchmark, task: Any, samples: list[dict[str, Any]], ids: list[Any]) -> dict[str, Any]:
    """Per-sample records, one summary per metric, baselines, and the comparison with b."""
    assert benchmark.scoring is not None
    s = benchmark.scoring
    if s.kind == "rolling":
        process = task.config.process_results
        lls, words, nbytes = [], [], []
        records = []
        for sample_id, sample in zip(ids, samples, strict=True):
            ll = float(sample["filtered_resps"][0])
            r = process(sample["doc"], [ll])
            lls.append(r["word_perplexity"][0])
            words.append(r["word_perplexity"][1])
            nbytes.append(r["byte_perplexity"][1])
            records.append(_record(sample_id, {"loglikelihood": ll, "words": words[-1], "bytes": nbytes[-1]}, [ll]))
        return {"records": records, "metrics": scoring.perplexity(lls, words, nbytes), "baselines": None, "b": None}

    clusters = scoring.CLUSTER_RULES[s.clusters]([sample["doc"] for sample in samples]) if s.clusters else None
    summarize = (lambda v: scoring.clustered_mean(v, clusters)) if clusters else scoring.mean_with_uncertainty
    if s.kind == "multiple_choice":
        outcomes = [scoring.multiple_choice_outcome(x, x.get("gold")) for x in samples]
        records = [
            _record(
                sample_id,
                {"acc": o["acc"], "acc_norm": o["acc_norm"]},
                o["loglikelihoods"],
                gold=o["gold"],
                prediction={"acc": o["pred_acc"], "acc_norm": o["pred_acc_norm"]},
            )
            for sample_id, o in zip(ids, outcomes, strict=True)
        ]
        metrics = {m: summarize([o[m] for o in outcomes]) for m in ("acc", "acc_norm")}
        baselines = scoring.choice_baselines(outcomes, s.fixed_classes, s.decision_metric)
        golds: list[Any] = [o["gold"] for o in outcomes]
        values = [o[s.decision_metric] for o in outcomes]
    else:  # loglikelihood: lm-eval's per-sample `acc` (is the target the greedy continuation)
        values = [float(x["acc"]) for x in samples]
        records = [
            _record(sample_id, {"acc": v}, [float(x["filtered_resps"][0][0]), bool(x["filtered_resps"][0][1])])
            for sample_id, x, v in zip(ids, samples, values, strict=True)
        ]
        metrics = {"acc": summarize(values)}
        golds = [str(task.doc_to_target(x["doc"])).strip() for x in samples]
        baselines = scoring.cloze_baseline(golds)
    b = scoring.against_baseline(values, golds, metrics[s.decision_metric], baselines, clusters)
    return {"records": records, "metrics": metrics, "baselines": baselines, "b": b}


def _record(sample_id: Any, scores: dict[str, Any], raw: list[Any], **extra: Any) -> dict[str, Any]:
    """One sample: the model's output is its log-likelihoods (one per option), which is also what the scorer saw."""
    output = json.dumps(raw)
    return {
        "sample_id": sample_id,
        "state": "ok",
        "scores": scores,
        "raw_output": output,
        "scored_output": output,
        "error": None,
        **extra,
    }


def run_benchmark(
    benchmark: Benchmark,
    lm: Any,
    spec: models.ModelSpec,
    model_record: dict[str, Any],
    out: Path,
    data: dict[str, Any] | None = None,
    load_error: BaseException | None = None,
) -> Outcome:
    """Evaluate `benchmark` and write its run directory under `out`. Never raises for a failure of the evaluation
    itself: it is recorded in the run as a state with its reason, and returned."""
    assert benchmark.dataset is not None and benchmark.scoring is not None
    started, clock = artifact.now(), time.monotonic()
    protocol = protocol_id(benchmark, spec.bos)
    stamp = started.replace("-", "").replace(":", "")
    model = spec.label.replace("/", "--").replace("@", "-")
    run_id = f"{benchmark.id}.{model}.{spec.bos}-bos.{stamp}.{uuid.uuid4().hex[:8]}"
    try:
        if load_error is not None:  # the model did not load: every selected benchmark records why
            raise load_error
        task, samples, ids = evaluate(benchmark, lm, data)
        scored = score(benchmark, task, samples, ids)
        scored["research_digest"] = research_digest(benchmark, samples)
        state, reason, log = "ok", None, None
        config = json.dumps(task.dump_config(), indent=2, sort_keys=True, default=str).encode("utf-8")
    # The boundary of one benchmark in a run of several: every exception becomes the benchmark's recorded state,
    # with its traceback in the run, and the command exits non-zero. Nothing is turned into a score.
    except Exception as e:
        state = state_of(e)
        reason = f"{type(e).__name__}: {e}"[:500]
        log = traceback.format_exc().encode("utf-8")
        samples, ids, scored, config = [], [], None, None
    finished, seconds = artifact.now(), time.monotonic() - clock
    timing = {
        "seconds": round(seconds, 1),
        "requests": sum(len(s["arguments"]) for s in samples),
        "requests_per_second": round(sum(len(s["arguments"]) for s in samples) / seconds, 2) if seconds else None,
        "note": "wall-clock time of loading the data, evaluating, and scoring; model loading not included",
    }
    manifest = _manifest(benchmark, spec, model_record, protocol, run_id, started, finished, scored)
    manifest["execution"]["timing"] = timing
    observations = _observations(benchmark, spec, protocol, ids, scored, state, reason)
    extra: dict[str, tuple[str, bytes]] = {}
    if config is not None:
        extra["task-config.json"] = ("config", config)
    if log is not None:
        extra["error.log"] = ("log", log)
    records = scored["records"] if scored else []
    run_dir = artifact.write_run(out / run_id, manifest, records, observations, extra)
    value = next((o["value"] for o in observations if o["metric"] == benchmark.scoring.decision_metric), None)
    return Outcome(benchmark.id, state, run_dir, value, reason, round(seconds, 1))


def _metric_definitions(benchmark: Benchmark) -> list[dict[str, Any]]:
    assert benchmark.scoring is not None
    s = benchmark.scoring
    if s.kind == "rolling":
        names = ["byte_perplexity", "word_perplexity", "bits_per_byte"]
        # Perplexity is a ratio of sums over documents, not a mean of per-document scores: not recomputed.
        return [
            {
                "id": n,
                "sample_key": n,
                "unit": s.unit if n == "byte_perplexity" else "score",
                "higher_is_better": False,
                "aggregation": "external",
                "kind": "quality",
            }
            for n in names
        ]
    names = ["acc", "acc_norm"] if s.kind == "multiple_choice" else ["acc"]
    return [
        {"id": n, "sample_key": n, "unit": s.unit, "higher_is_better": True, "aggregation": "mean", "kind": "quality"}
        for n in names
    ]


def _observations(
    benchmark: Benchmark,
    spec: models.ModelSpec,
    protocol: str,
    ids: list[Any],
    scored: dict[str, Any] | None,
    state: str,
    reason: str | None,
) -> list[dict[str, Any]]:
    """One observation per metric in the results contract's shape (research/common/metryki.py `obserwacja`)."""
    assert benchmark.dataset is not None and benchmark.scoring is not None
    out = []
    for m in _metric_definitions(benchmark):
        scale = 100.0 if m["unit"] == "percent" else 1.0
        obs: dict[str, Any] = {
            "task_id": benchmark.id,
            "model_id": spec.label,
            "protocol_id": protocol,
            "metric": m["id"],
            "unit": m["unit"],
            "higher_is_better": m["higher_is_better"],
            "n_population": benchmark.dataset.n_population if scored else None,
            "n_selected": len(ids) if scored else None,
            "n_scored": len(ids) if scored else 0,
            "state": state,
            "value": None,
            "ci95": None,
            "source_id_digest": None,
            "results_sha256": None,
            "runner_sha256": None,
            "contamination": "unscanned",
            "contamination_receipt_sha256": None,
            "reference": None,
        }
        if scored:
            summary = scored["metrics"][m["id"]]
            baselines = scored["baselines"]
            obs.update(
                value=summary["value"] * scale,
                ci95={
                    "lower": summary["ci95"][0] * scale,
                    "upper": summary["ci95"][1] * scale,
                    "level": 0.95,
                    "method": "percentile_bootstrap" if summary["se_method"] != "clustered" else "cluster_bootstrap",
                    "replicates": scoring.REPLICATES,
                    "seed": scoring.SEED,
                },
                source_id_digest=source_id_digest(ids),
                runner_sha256=artifact.runner_sha256(),
                reference=None
                if baselines is None or m["id"] != benchmark.scoring.decision_metric
                else {
                    k: (v * scale if k in ("chance_value", "majority_value") and v is not None else v)
                    for k, v in baselines.items()
                },
            )
        else:
            obs["reason"] = reason
        out.append(obs)
    return out


def _manifest(
    benchmark: Benchmark,
    spec: models.ModelSpec,
    model_record: dict[str, Any],
    protocol: str,
    run_id: str,
    started: str,
    finished: str,
    scored: dict[str, Any] | None,
) -> dict[str, Any]:
    assert benchmark.dataset is not None and benchmark.scoring is not None
    import lm_eval

    commit, dirty = artifact.source_state()
    d = benchmark.dataset
    revision = d.revision if d.source != "parquet" else f"{d.revision} (parquet conversion @ {d.parquet_revision})"
    if d.source == "unpinned-parquet":
        revision = f"{d.revision} (read from refs/convert/parquet, not pinned)"
    env = artifact.environment(spec.device)
    env.update(source_dirty=dirty, bos=model_record["bos"], weights_files=model_record["weights_files"])
    na = {"unknown": "not applicable: log-likelihood scoring, nothing is generated"}
    complete = not dirty and isinstance(commit, str) and spec.revision is not None and d.source != "unpinned-parquet"
    return {
        "format": "urn:codesota:run-manifest:1",
        "run_id": run_id,
        "provenance_claim": "complete" if complete else "partial",
        "analysis": {"kind": "primary"},
        "benchmark": {
            "id": benchmark.id,
            "definition": f"benchmarks/src/codesota/catalog.py and runner/tasks.py; card {benchmark.definition}",
            "name": benchmark.name,
            "legacy_id": benchmark.legacy_id,
        },
        "protocol": {
            "id": protocol,
            "dataset": {"repo": d.repo, "revision": revision, "split": d.split, "n_population": d.n_population},
            "scorer": {
                "name": f"lm-evaluation-harness {benchmark.scoring.kind} log-likelihoods, scored by codesota.runner",
                "version": f"lm-eval {lm_eval.__version__}",
                "randomness": {
                    "controlled": True,
                    "policy": "deterministic: scores are argmax or sums of log-likelihoods; bootstrap seed "
                    f"{scoring.SEED}, lm-eval seeds {LM_EVAL_SEEDS}",
                    "limitations": None,
                },
            },
            "output_preprocessing": "none",
            "bos": spec.bos,
            "num_fewshot": 0,
        },
        "model": {
            "id": spec.label,
            "repo": spec.repo if spec.repo else {"unknown": f"local directory {spec.path}"},
            "revision": spec.revision if spec.revision else {"unknown": "local directory without a recorded revision"},
            "weights_sha256": model_record["weights_sha256"],
            "trust_remote_code": spec.trust_remote_code,
        },
        "inference": {
            "backend": {"name": "lm-evaluation-harness HFLM", "version": lm_eval.__version__},
            "dtype": spec.dtype,
            "quantization": None,
            "temperature": na,
            "top_p": None,
            "max_output_tokens": na,
            "context_length": model_record["max_length"],
            "chat_template": None,
            "system_prompt": "none",
            "thinking": "not_applicable",
            "batch_size": spec.batch_size,
            "concurrency": 1,
            "seed": LM_EVAL_SEEDS["torch_random_seed"],
        },
        "execution": {"started_at": started, "finished_at": finished, "source_commit": commit, "environment": env},
        "publication": {
            "outputs": "included",
            "license": "per-option log-likelihoods only, no dataset text; dataset terms: "
            f"{benchmark.definition}ORIGINAL.md",
        },
        "metrics": _metric_definitions(benchmark),
        "assessment": {
            "status": benchmark.status,
            "evidence": benchmark.evidence,
            "limitations": list(benchmark.limitations),
            "decision_metric": benchmark.scoring.decision_metric,
            "research_source_id_digest": None if scored is None else scored.get("research_digest"),
            "uncertainty": None if scored is None else scored["metrics"][benchmark.scoring.decision_metric],
            "baselines": None if scored is None else scored["baselines"],
            "against_b": None if scored is None else scored["b"],
        },
    }
