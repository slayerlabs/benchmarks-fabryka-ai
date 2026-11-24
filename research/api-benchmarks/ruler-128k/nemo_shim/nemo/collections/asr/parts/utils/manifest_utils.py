"""The two NeMo functions RULER's scripts/eval/evaluate.py imports, without the NeMo toolkit.

A manifest is a JSON-lines file. `write_manifest` matches RULER's own copy (scripts/data/manifest_utils.py);
`read_manifest` reads one JSON object per non-empty line, as NeMo's does for a local file.
"""

import json


def read_manifest(manifest):
    with open(manifest, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_manifest(output_path, target_manifest, ensure_ascii=True):
    with open(output_path, "w", encoding="utf-8") as outfile:
        for tgt in target_manifest:
            json.dump(tgt, outfile, ensure_ascii=ensure_ascii)
            outfile.write("\n")
