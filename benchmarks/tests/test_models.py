"""Model identity and weight files: what a run records about the model. No evaluation stack needed."""

import json
from pathlib import Path

import pytest

from codesota.runner import models

SHA = "f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0"


def test_a_hub_model_needs_a_commit_sha() -> None:
    assert models.ModelSpec.from_args("org/model", SHA).id == "org/model"
    assert models.ModelSpec.from_args("org/model", SHA, model_id="my-name").id == "my-name"
    for revision in (None, "main", "v1.0", SHA[:12]):
        with pytest.raises(ValueError, match="40-character commit SHA"):
            models.ModelSpec.from_args("org/model", revision)


def test_a_local_model_is_identified_by_its_weights(tmp_path: Path) -> None:
    a, b = tmp_path / "a" / "final", tmp_path / "b" / "final"
    for d in (a, b):
        d.mkdir(parents=True)
    spec_a, spec_b = models.ModelSpec.from_args(str(a), None), models.ModelSpec.from_args(str(b), None)
    assert spec_a.id is None and spec_a.label == "local/final"
    id_a = models.identified(spec_a, {"model.safetensors": "1" * 64}).id
    id_b = models.identified(spec_b, {"model.safetensors": "2" * 64}).id
    assert id_a != id_b and id_a is not None and id_a.startswith("local/final@")
    assert models.identified(spec_a, {"model.safetensors": "1" * 64}).id == id_a  # same weights, same ID
    named = models.ModelSpec.from_args(str(a), None, model_id="team/final-v2")
    assert models.identified(named, {"model.safetensors": "1" * 64}).id == "team/final-v2"


def test_weights_must_be_present(tmp_path: Path) -> None:
    with pytest.raises(models.IncompleteWeights, match="no weight files"):
        models.weights_files(tmp_path)
    (tmp_path / "pytorch_model.bin").write_bytes(b"b")
    assert [p.name for p in models.weights_files(tmp_path)] == ["pytorch_model.bin"]
    (tmp_path / "model.safetensors").write_bytes(b"s")  # transformers prefers safetensors
    assert [p.name for p in models.weights_files(tmp_path)] == ["model.safetensors"]


def test_a_sharded_checkpoint_needs_every_shard_of_its_index(tmp_path: Path) -> None:
    shards = ["model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors"]
    index = {"weight_map": {"a.weight": shards[0], "b.weight": shards[1], "c.weight": shards[1]}}
    (tmp_path / "model.safetensors.index.json").write_text(json.dumps(index), encoding="utf-8")
    (tmp_path / shards[0]).write_bytes(b"1")
    with pytest.raises(models.IncompleteWeights, match=shards[1]):
        models.weights_files(tmp_path)
    (tmp_path / shards[1]).write_bytes(b"2")
    (tmp_path / "stray.safetensors").write_bytes(b"x")  # not in the index: not a weight of this model
    assert [p.name for p in models.weights_files(tmp_path)] == shards
