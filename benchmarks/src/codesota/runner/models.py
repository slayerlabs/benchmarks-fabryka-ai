"""Which model a run evaluates, and how it is loaded.

A model comes from the Hugging Face Hub (public, or private with a token in the `HF_TOKEN` environment variable, which
is never recorded) at a pinned commit, or from a local directory. It is loaded through lm-eval's `HFLM`; a model
architecture that `HFLM` cannot load needs its own lm-eval model class, which plugs in at `load`.

Code shipped with a model (`trust_remote_code`) runs only when the caller asks for it, and the run records that it
did. The BOS policy is part of the protocol: `one` puts exactly one leading BOS token of the model's tokenizer before
every request with a context (research/METODOLOGIA.md, section on the model input; a port of
research/common/jeden_bos.py), and `none` keeps lm-eval 0.4.9.1's default, which encodes text without special tokens.
"""

import dataclasses
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Bos = Literal["one", "none"]
COMMIT = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class ModelSpec:
    id: str | None
    """The model's name in results: `--model-id`, else the Hub repository. A local directory without `--model-id`
    gets `local/<directory name>@<12 hex>` from the digest of its weights (see `prepare`), because two different
    models can share a directory name."""
    repo: str | None
    revision: str | None
    path: Path | None
    dtype: str = "float32"
    device: str = "cuda"
    batch_size: int = 1
    max_length: int | None = None
    trust_remote_code: bool = False
    bos: Bos = "one"

    @staticmethod
    def from_args(
        model: str,
        revision: str | None,
        *,
        dtype: str = "float32",
        device: str = "cuda",
        batch_size: int = 1,
        max_length: int | None = None,
        trust_remote_code: bool = False,
        bos: Bos = "one",
        model_id: str | None = None,
    ) -> "ModelSpec":
        """A local directory when `model` is an existing directory, else a Hub repository, which needs a revision
        that is a full commit SHA: a branch or tag can move, and the run would not say what it measured."""
        path = Path(model)
        settings: dict[str, Any] = {
            "dtype": dtype,
            "device": device,
            "batch_size": batch_size,
            "max_length": max_length,
            "trust_remote_code": trust_remote_code,
            "bos": bos,
        }
        if path.is_dir():
            if revision is not None and not COMMIT.match(revision):
                raise ValueError(f"--revision {revision!r}: a 40-character commit SHA of the model's source, or none")
            return ModelSpec(id=model_id, repo=None, revision=revision, path=path.resolve(), **settings)
        if revision is None or not COMMIT.match(revision):
            raise ValueError(
                f"{model}: not a local directory, so a Hub repository; --revision must be a 40-character commit SHA "
                f"(got {revision!r})"
            )
        return ModelSpec(id=model_id or model, repo=model, revision=revision, path=None, **settings)

    @property
    def label(self) -> str:
        """The ID, or for a local model whose weights were not read yet, its directory name."""
        if self.id:
            return self.id
        assert self.path is not None
        return f"local/{self.path.name}"


def load(spec: ModelSpec) -> Any:
    """The lm-eval model object for `spec`."""
    from lm_eval.models.huggingface import HFLM

    cls = one_bos_class() if spec.bos == "one" else HFLM
    return cls(
        pretrained=str(spec.path) if spec.path else spec.repo,
        revision=None if spec.path else spec.revision,
        dtype=spec.dtype,
        batch_size=spec.batch_size,
        device=spec.device,
        trust_remote_code=spec.trust_remote_code,
        max_length=spec.max_length,
    )


def one_bos_class() -> Any:
    """`HFLM` with exactly one leading BOS in every request with a non-empty context (research/common/jeden_bos.py).

    Text is always encoded without special tokens, and the tokenizer's `bos_token_id` is put before the context of
    every log-likelihood pair and before every generation prompt. An empty context and rolling windows start with
    `prefix_token_id`, as in `HFLM`. A tokenizer without `bos_token` gives requests without BOS.
    """
    import torch
    from lm_eval.models.huggingface import HFLM

    class OneBosHFLM(HFLM):  # type: ignore[misc]  # HFLM is untyped (lm-eval ships no type information)
        @property
        def add_bos_token(self) -> bool:
            return False

        @add_bos_token.setter
        def add_bos_token(self, _: object) -> None:
            pass

        @property
        def leading_bos(self) -> int | None:
            return getattr(self.tokenizer, "bos_token_id", None)

        def _encode_pair(self, context: str, continuation: str) -> tuple[list[int], list[int]]:
            context_enc, continuation_enc = super()._encode_pair(context, continuation)
            bos = self.leading_bos
            if bos is not None and list(context_enc[:1]) != [bos]:
                context_enc = [bos, *context_enc]
            return list(context_enc), list(continuation_enc)

        def tok_batch_encode(
            self,
            strings: list[str],
            padding_side: str = "left",
            left_truncate_len: int | None = None,
            truncation: bool = False,
        ) -> tuple[Any, Any]:
            bos = self.leading_bos
            if bos is None:
                return super().tok_batch_encode(  # type: ignore[no-any-return]  # untyped base class
                    strings, padding_side=padding_side, left_truncate_len=left_truncate_len, truncation=truncation
                )
            if padding_side != "left":
                raise ValueError(f"one-BOS encoding supports left padding only, got {padding_side!r}")
            ids, mask = super().tok_batch_encode(
                strings,
                padding_side=padding_side,
                left_truncate_len=left_truncate_len - 1 if left_truncate_len else None,
                truncation=truncation,
            )
            first = mask.long().argmax(dim=1)
            if bool((ids.gather(1, first.view(-1, 1)) == bos).all()):
                return ids, mask
            # Left padding: the BOS column goes before the padding, which `generate` skips through the mask.
            return (
                torch.cat([ids.new_full((ids.shape[0], 1), bos), ids], dim=1),
                torch.cat([mask.new_ones((mask.shape[0], 1)), mask], dim=1),
            )

    return OneBosHFLM


def leading_bos_count(ids: list[int], bos: int | None) -> int:
    """How many `bos` tokens start `ids` (0 for a model without BOS)."""
    if bos is None:
        return 0
    n = 0
    for t in ids:
        if t != bos:
            break
        n += 1
    return n


def bos_probe(lm: Any) -> dict[str, Any]:
    """The model's BOS token and how many leading BOS tokens a probe log-likelihood request gets, with the encoding
    the run uses: recorded with every run, so a wrong policy is visible in the results."""
    bos = getattr(lm.tokenizer, "bos_token_id", None)
    context, _ = lm._encode_pair("Question: 2 + 2 =\nAnswer:", " 4")
    return {
        "bos_token": getattr(lm.tokenizer, "bos_token", None) if bos is not None else None,
        "bos_token_id": bos,
        "prefix_token_id": lm.prefix_token_id,
        "leading_bos_in_probe_request": leading_bos_count(list(context), bos),
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


class IncompleteWeights(FileNotFoundError):
    """The model directory has no weights, or lacks files its weight index lists."""


def weights_files(root: Path) -> list[Path]:
    """The weight files of a model directory, in the order `transformers` prefers them (safetensors, then
    PyTorch). A sharded checkpoint is read from its index (`*.index.json`), and every shard it lists must exist."""
    for suffix, pattern in (("safetensors", "*.safetensors"), ("bin", "pytorch_model*.bin")):
        indexes = sorted(root.glob(f"*.{suffix}.index.json"))
        if indexes:
            shards = sorted(
                {str(v) for i in indexes for v in json.loads(i.read_text(encoding="utf-8"))["weight_map"].values()}
            )
            missing = [s for s in shards if not (root / s).is_file()]
            if missing:
                raise IncompleteWeights(f"{root}: weight index lists missing files: {', '.join(missing)}")
            return [root / s for s in shards]
        files = sorted(root.glob(pattern))
        if files:
            return files
    raise IncompleteWeights(f"{root}: no weight files (*.safetensors or pytorch_model*.bin)")


def model_root(spec: ModelSpec) -> Path:
    """The model's directory: the local one, or its snapshot in the local Hub cache (after loading)."""
    if spec.path is not None:
        return spec.path
    from huggingface_hub import snapshot_download

    assert spec.repo is not None
    return Path(snapshot_download(spec.repo, revision=spec.revision, local_files_only=True))


def weights_digests(spec: ModelSpec) -> dict[str, str]:
    """SHA-256 of every weight file, by file name."""
    return {f.name: sha256_file(f) for f in weights_files(model_root(spec))}


def identified(spec: ModelSpec, digests: dict[str, str]) -> ModelSpec:
    """`spec` with its ID: unchanged when it has one, else `local/<directory>@<first 12 hex of the digest of its
    weight files>`, so different weights under the same directory name get different IDs."""
    if spec.id is not None:
        return spec
    lines = "".join(f"{name}:{digest}\n" for name, digest in sorted(digests.items()))
    return dataclasses.replace(spec, id=f"{spec.label}@{hashlib.sha256(lines.encode()).hexdigest()[:12]}")


def prepare(spec: ModelSpec) -> tuple[ModelSpec, Any, dict[str, Any]]:
    """Load the model and identify it: (spec with its final ID, lm-eval model, record for the manifests). Raises
    when the model does not load or its weights are incomplete."""
    lm = load(spec)
    digests = weights_digests(spec)
    spec = identified(spec, digests)
    record = {
        "bos": bos_probe(lm),
        "weights_files": digests,
        "weights_sha256": next(iter(digests.values()))
        if len(digests) == 1
        else {"unknown": f"{len(digests)} weight files; per-file SHA-256 in execution.environment.weights_files"},
        "max_length": getattr(lm, "max_length", None),
    }
    return spec, lm, record


# What a manifest records about a model that did not load.
NOT_LOADED: dict[str, Any] = {
    "bos": None,
    "weights_files": {},
    "weights_sha256": {"unknown": "the model did not load"},
    "max_length": None,
}
