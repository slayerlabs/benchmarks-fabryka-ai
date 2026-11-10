"""Parameter count of the models of a full run, computed from the weights rather than taken from a model card.

    python tools/ewaluacja/count_params.py results/<run>

Reads `manifest.jsonl` and, for every (repo, revision), sums the products of tensor shapes over all `*.safetensors`
shards, reading only each file's header through an HTTP range request. Tensors that share a byte range (tied weights
stored once) count once. A repo with `pytorch_model.bin` only is read the same way: the zip directory and the pickle
with the tensor shapes, through range requests, with a whitelist of the classes a weights pickle needs. A gated repo
falls back to the `safetensors` block of the HF API, which HF computes from the same headers. A repo without either
format gets `params: null` with a reason: a declared size is never substituted. Writes `sizes.json` into the run
directory.
"""
import io
import json
import pickle
import re
import struct
import subprocess
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path

HF = "https://huggingface.co"
AGENT = "benchmarks-fabryka-ai/count-params"


def count_tensors(header: dict) -> int:
    """Sum of tensor-shape products of one safetensors header; a shared byte range counts once."""
    seen, total = set(), 0
    for name, info in header.items():
        if name == "__metadata__":
            continue
        span = tuple(info["data_offsets"])
        if span in seen:
            continue
        seen.add(span)
        n = 1
        for dim in info["shape"]:
            n *= dim
        total += n
    return total


def _get(url: str, byte_range: str | None = None) -> bytes:
    """curl, because it uses the system certificate store also where this Python has none."""
    cmd = ["curl", "-sSfL", "-m", "60", "-A", AGENT] + (["-r", byte_range] if byte_range else []) + [url]
    return subprocess.run(cmd, capture_output=True, check=True).stdout


def safetensors_header(repo: str, revision: str, path: str) -> dict:
    url = f"{HF}/{repo}/resolve/{revision}/{path}"
    length = struct.unpack("<Q", _get(url, "0-7"))[0]
    return json.loads(_get(url, f"8-{8 + length - 1}"))


def repo_files(repo: str, revision: str) -> list[str]:
    return [p["path"] for p in json.loads(_get(f"{HF}/api/models/{repo}/tree/{revision}?recursive=true"))
            if p.get("type") == "file"]


def api_total(repo: str, revision: str) -> int | None:
    meta = json.loads(_get(f"{HF}/api/models/{repo}/revision/{revision}?expand[]=safetensors"))
    return (meta.get("safetensors") or {}).get("total")


class _RangeFile(io.RawIOBase):
    """Seekable read-only view of a remote file, so `zipfile` reads only the zip directory and `data.pkl`."""

    def __init__(self, url: str):
        self.url, self.pos = url, 0
        head = subprocess.run(["curl", "-sSIfL", "-m", "60", "-A", AGENT, url], capture_output=True, check=True, text=True)
        self.size = int(re.findall(r"(?im)^content-length:\s*(\d+)", head.stdout)[-1])

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.pos, io.SEEK_END: self.size}[whence]
        self.pos = base + offset
        return self.pos

    def readinto(self, buf):
        if self.pos >= self.size or not len(buf):
            return 0
        data = _get(self.url, f"{self.pos}-{min(self.pos + len(buf), self.size) - 1}")
        buf[:len(data)] = data
        self.pos += len(data)
        return len(data)


class _TensorRef:
    def __init__(self, storage_key, offset, shape):
        self.key = (storage_key, offset, tuple(shape))
        self.shape = tuple(shape)


class _ShapeUnpickler(pickle.Unpickler):
    """Reads tensor shapes from a `torch.save` pickle; every class outside this whitelist is refused."""

    def persistent_load(self, pid):
        return pid[2]  # ('storage', class, key, location, size): the storage key identifies shared tensors

    def find_class(self, module, name):
        if module == "collections" and name == "OrderedDict":
            return OrderedDict
        if module == "torch._utils" and name in ("_rebuild_tensor", "_rebuild_tensor_v2"):
            return lambda storage, offset, size, *rest: _TensorRef(storage, offset, size)
        if module == "torch" and name.endswith("Storage"):
            return name
        raise pickle.UnpicklingError(f"not allowed in a weights file: {module}.{name}")


def count_state_dict(state: dict) -> int:
    seen, total = set(), 0
    for ref in state.values():
        if not isinstance(ref, _TensorRef) or ref.key in seen:
            continue
        seen.add(ref.key)
        n = 1
        for dim in ref.shape:
            n *= dim
        total += n
    return total


def bin_params(repo: str, revision: str, path: str) -> int:
    url = f"{HF}/{repo}/resolve/{revision}/{path}"
    with zipfile.ZipFile(io.BufferedReader(_RangeFile(url), buffer_size=1 << 20)) as archive:
        name = next(n for n in archive.namelist() if n.endswith("data.pkl"))
        return count_state_dict(_ShapeUnpickler(io.BytesIO(archive.read(name))).load())


def repo_params(repo: str, revision: str) -> dict:
    files = repo_files(repo, revision)
    shards = sorted(p for p in files if p.endswith(".safetensors"))
    base = {"repo": repo, "revision": revision, "files": shards}
    if not shards:
        bins = sorted(p for p in files if p.endswith(".bin") and "training_args" not in p)
        if not bins:
            return {**base, "params": None, "reason": "no safetensors or pytorch_model.bin files in the repo"}
        return {**base, "files": bins, "params": sum(bin_params(repo, revision, p) for p in bins),
                "method": "sum of tensor-shape products from the pickle of pytorch_model.bin"}
    try:
        return {**base, "params": sum(count_tensors(safetensors_header(repo, revision, p)) for p in shards),
                "method": "sum of tensor-shape products from the safetensors headers"}
    except subprocess.CalledProcessError:
        return {**base, "params": api_total(repo, revision),
                "method": "safetensors block of the HF API (gated repo, headers not readable without a token)"}


def main():
    run_dir = Path(sys.argv[1])
    models = {}
    for row in map(json.loads, (run_dir / "manifest.jsonl").read_text(encoding="utf-8").splitlines()):
        models.setdefault(row["model"], (row["repo"], row["rewizja"]))
    result = {m: repo_params(r, rev) for m, (r, rev) in sorted(models.items())}
    (run_dir / "sizes.json").write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for m, r in result.items():
        print(m, r["params"], r.get("reason", ""))


if __name__ == "__main__":
    main()
