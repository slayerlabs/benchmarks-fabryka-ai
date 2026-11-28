"""Does summarize.py at this commit reproduce a published result? -> results/reproduction.json

Usage: python reproduction.py <commit> <model-id> [<model-id> ...]

The first LFM3-1.7B and Slayer results were written by a summarize.py (sha256 d80f85f1...) that is in no commit. After
summarize.py at this commit rewrote results/<model-id>.json and .jsonl.gz, this compares them with the files of
<commit> (git show): every JSON field that differs, outside `provenance` and `warnings` (time, machine and code of
the summary; the declared generation provenance and its warning are new), and the .jsonl.gz rows (decompressed; the
gzip header holds a time).
"""
import gzip
import json
import subprocess
import sys
from pathlib import Path

import provenance

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
IGNORED = ("provenance", "warnings")


def published(commit, name):
    """The file as <commit> has it (`./` is relative to this directory)."""
    return subprocess.run(["git", "-C", str(HERE), "show", f"{commit}:./results/{name}"], capture_output=True,
                          check=True).stdout


def differences(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in sorted(set(a) | set(b)) for d in differences(a.get(k, "<missing>"), b.get(k, "<missing>"),
                                                                       f"{path}.{k}")]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, f"{path}[{i}]")]
    return [] if a == b else [path]


def compare(commit, model):
    old = json.loads(published(commit, f"{model}.json"))
    new = json.loads((RESULTS / f"{model}.json").read_text(encoding="utf-8"))
    fields = differences({k: v for k, v in old.items() if k not in IGNORED},
                         {k: v for k, v in new.items() if k not in IGNORED})
    old_rows = gzip.decompress(published(commit, f"{model}.jsonl.gz")).decode("utf-8").splitlines()
    new_rows = gzip.decompress((RESULTS / f"{model}.jsonl.gz").read_bytes()).decode("utf-8").splitlines()
    return {"published": {"commit": commit, "summarize.py sha256": old["provenance"]["summarize"]["runner_sha256"]
                          ["summarize.py"], "code": old["provenance"]["summarize"]["code"]},
            "rerun": {"code": new["provenance"]["summarize"]["code"],
                      "summarize.py sha256": new["provenance"]["summarize"]["runner_sha256"]["summarize.py"]},
            "fields_compared": "all except " + ", ".join(IGNORED), "fields_differing": fields,
            "provenance_fields_differing": differences(old["provenance"], new["provenance"], "provenance"),
            "jsonl_rows": {"published": len(old_rows), "rerun": len(new_rows), "identical": old_rows == new_rows}}


def main():
    commit, models = sys.argv[1], sys.argv[2:]
    out = {"what": __doc__.split("\n\n")[1].replace("\n", " "), **{m: compare(commit, m) for m in models}}
    (RESULTS / "reproduction.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    provenance.write_manifest(RESULTS, ["reproduction.json"], provenance.RESULTS)
    print(json.dumps({m: {k: out[m][k] for k in ("fields_differing", "jsonl_rows")} for m in models}, indent=1))


if __name__ == "__main__":
    main()
