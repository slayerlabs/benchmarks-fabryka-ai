"""Deterministic synthetic runs for the validator tests. No model, network, or real benchmark data.

These are synthetic validation data, not model evaluations. `local_bf16` has complete provenance only in the sense
the validator checks (every required field is recorded); its model, dataset, scorer, and scores are invented.

The benchmark is a made-up six-prompt instruction task with three metrics: strict and loose prompt-level accuracy
(one boolean per prompt) and strict instruction-level accuracy (one boolean per instruction, `micro_mean`). The
committed fixtures in tests/fixtures/runs/ are exactly what `write_run` produces (test_fixtures_are_reproducible).
"""

import copy
import json
from pathlib import Path
from typing import Any

from codesota.results import schema, sha256_file, source_id_digest

FIXTURES = Path(__file__).parent / "fixtures" / "runs"
COMMIT = "0" * 39 + "1"

# sample_id, strict, loose, per-instruction strict, raw output
SAMPLES: list[tuple[str, bool, bool, list[bool], str]] = [
    ("toy-001", True, True, [True], "A short answer without commas."),
    ("toy-002", False, True, [False, True], "*Title*\nAnother answer, with a comma."),
    ("toy-003", True, True, [True, True], "ALL CAPS ANSWER"),
    ("toy-004", False, False, [False], "an answer that ignores the instruction"),
    ("toy-005", True, True, [True, True, True], "Three rules, all followed."),
    ("toy-006", False, False, [False, True], "Half of it."),
]

METRICS = [
    {
        "id": "prompt_level_strict_acc",
        "sample_key": "prompt_level_strict_acc",
        "unit": "percent",
        "higher_is_better": True,
        "aggregation": "mean",
        "kind": "quality",
    },
    {
        "id": "prompt_level_loose_acc",
        "sample_key": "prompt_level_loose_acc",
        "unit": "percent",
        "higher_is_better": True,
        "aggregation": "mean",
        "kind": "quality",
    },
    {
        "id": "inst_level_strict_acc",
        "sample_key": "inst_level_strict_acc",
        "unit": "percent",
        "higher_is_better": True,
        "aggregation": "micro_mean",
        "kind": "quality",
    },
]


def base_manifest(run_id: str) -> dict[str, Any]:
    return {
        "format": schema.MANIFEST_FORMAT,
        "run_id": run_id,
        "provenance_claim": "complete",
        "analysis": {"kind": "primary"},
        "benchmark": {"id": "synthetic-toy-instructions", "definition": "tests/runs.py (synthetic validation data)"},
        "protocol": {
            "id": "synthetic-toy-chat-greedy",
            "dataset": {
                "repo": "synthetic/toy-instructions (not a real dataset)",
                "revision": "fixture-1",
                "split": "test",
                "n_population": len(SAMPLES),
            },
            "scorer": {
                "name": "synthetic rules",
                "version": "fixture-1",
                "randomness": {
                    "controlled": True,
                    "policy": "the synthetic scorer is deterministic",
                    "limitations": None,
                },
            },
            "output_preprocessing": "none",
        },
        "model": {
            "id": "example/model-1b",
            "repo": "example/model-1b",
            "revision": "a" * 40,
            "weights_sha256": "b" * 64,
        },
        "inference": {
            "backend": {"name": "vllm", "version": "0.0.0-fixture"},
            "dtype": "bfloat16",
            "quantization": None,
            "temperature": 0.0,
            "top_p": None,
            "max_output_tokens": 1280,
            "context_length": 4096,
            "chat_template": "model default",
            "system_prompt": "none",
            "thinking": "not_applicable",
            "batch_size": 1,
            "concurrency": 1,
            "seed": 1234,
        },
        "execution": {
            "started_at": "2026-11-19T10:00:00Z",
            "finished_at": "2026-11-19T10:05:00Z",
            "source_commit": COMMIT,
            "environment": {"python": "3.12", "gpu": "synthetic"},
        },
        "publication": {"outputs": "included", "license": "CC0-1.0 (synthetic)"},
        "metrics": copy.deepcopy(METRICS),
    }


def records(failed: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for sample_id, strict, loose, inst, raw in SAMPLES:
        if sample_id in failed:
            out.append(
                {
                    "sample_id": sample_id,
                    "state": "failed",
                    "scores": None,
                    "raw_output": None,
                    "scored_output": None,
                    "error": "HTTP 503 after 3 attempts",
                }
            )
        else:
            out.append(
                {
                    "sample_id": sample_id,
                    "state": "ok",
                    "scores": {
                        "prompt_level_strict_acc": strict,
                        "prompt_level_loose_acc": loose,
                        "inst_level_strict_acc": inst,
                    },
                    "raw_output": raw,
                    "scored_output": raw,
                    "error": None,
                }
            )
    return out


def observations(manifest: dict[str, Any], recs: list[dict[str, Any]], samples_sha: str) -> list[dict[str, Any]]:
    scored = [r for r in recs if r["state"] == "ok"]
    out = []
    for m in manifest["metrics"]:
        values = [r["scores"][m["sample_key"]] for r in scored]
        flat = [v for vs in values for v in vs] if m["aggregation"] == "micro_mean" else values
        value = 100 * sum(flat) / len(flat)
        out.append(
            {
                "task_id": manifest["benchmark"]["id"],
                "model_id": manifest["model"]["id"],
                "protocol_id": manifest["protocol"]["id"],
                "metric": m["id"],
                "unit": m["unit"],
                "higher_is_better": m["higher_is_better"],
                "n_population": manifest["protocol"]["dataset"]["n_population"],
                "n_selected": len(recs),
                "n_scored": len(scored),
                "state": "ok",
                "value": value,
                "ci95": None,
                "source_id_digest": source_id_digest(r["sample_id"] for r in recs),
                "results_sha256": samples_sha,
                "runner_sha256": "c" * 64,
                "contamination": "unscanned",
                "contamination_receipt_sha256": None,
            }
        )
    return out


def write_run(run_dir: Path, manifest: dict[str, Any], recs: list[dict[str, Any]]) -> Path:
    """Write samples.jsonl and a manifest whose checksums and aggregates match it."""
    run_dir.mkdir(parents=True, exist_ok=True)
    samples = run_dir / "samples.jsonl"
    samples.write_bytes(b"".join(json.dumps(r, sort_keys=True).encode("utf-8") + b"\n" for r in recs))
    sha = sha256_file(samples)
    manifest = {
        **manifest,
        "artifacts": [{"path": "samples.jsonl", "role": "samples", "sha256": sha, "bytes": samples.stat().st_size}],
        "observations": observations(manifest, recs, sha),
    }
    (run_dir / "manifest.json").write_bytes((json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return run_dir


def local_bf16(run_dir: Path) -> Path:
    """Synthetic run with complete provenance fields: local engine, bf16, greedy. Not a real evaluation."""
    return write_run(run_dir, base_manifest("synthetic.toy.example-model-1b.local-bf16.20261119T100000Z"), records())


def provider_api(run_dir: Path) -> Path:
    """Synthetic run of the same model through an API: another protocol, an unknown served revision, and one failed
    request. Not a real evaluation."""
    m = base_manifest("synthetic.toy.example-model-1b.provider-api.20261119T110000Z")
    m["provenance_claim"] = "partial"
    m["protocol"]["id"] = "synthetic-toy-chat-sampled-api"
    m["model"]["revision"] = {"unknown": "the provider does not expose the served model revision"}
    m["model"]["weights_sha256"] = {"unknown": "weights are served by the provider"}
    m["inference"].update(
        {
            "backend": {"name": "example-provider-api", "version": {"unknown": "not exposed by the provider"}},
            "dtype": {"unknown": "not exposed by the provider"},
            "quantization": {"unknown": "not exposed by the provider"},
            "temperature": 0.6,
            "top_p": 0.95,
            "system_prompt": "provider default (injected by the provider, text not recorded)",
            "batch_size": None,
            "concurrency": 2,
        }
    )
    return write_run(run_dir, m, records(failed=("toy-004",)))
