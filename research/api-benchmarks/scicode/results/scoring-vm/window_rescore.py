"""Re-score, with the unchanged scorer in the scoring container, the official step files whose verdicts were written
around the VM's disk-full window (2026-11-22 20:10-20:20 UTC) or that were running through it, and compare with the
verdicts kept in the results. Usage (in the container, cwd = benchmark dir):
  python window_rescore.py <model> <setting> <tag> <step> [<step> ...]
Writes /work/<tag>/compare.json."""
import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.getcwd())
import scicode_runner as sr  # noqa: E402

model, setting, tag, steps = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
out = Path("out") / model
work = Path("/work") / tag
code = work / "code" / model / setting
code.mkdir(parents=True)
for s in steps:
    shutil.copyfile(out / "generated_code" / model / setting / f"{s}.py", code / f"{s}.py")
os.environ["HF_HOME"] = str(sr.HF_CACHE)
os.environ["HF_HUB_OFFLINE"] = os.environ["HF_DATASETS_OFFLINE"] = "1"
args = argparse.Namespace(model_id=model, split="test")
with tempfile.TemporaryDirectory() as tmp:
    root = sr.scratch_copy(Path(tmp), sr.H5_PATH)
    env = {**os.environ, **sr.BLAS_THREADS, "PYTHONPATH": str(root / "src"), "PYTHONUNBUFFERED": "1"}
    run = sr.run_scorer(root, env, args, setting, work / "code", work, "logs", "rescore")
rows = []
for s in steps:
    kept = (out / "score" / "logs" / model / setting / f"{s}.txt").read_text().splitlines()[0]
    again = (work / "logs" / model / setting / f"{s}.txt").read_text().splitlines()[0]
    rows.append({"step": s, "kept": kept, "rescored": again, "same": kept == again})
result = {"model": model, "setting": setting, "steps": len(steps), "same": sum(r["same"] for r in rows),
          "differ": [r for r in rows if not r["same"]], "rows": rows, "scorer_seconds": run["seconds"]}
(work / "compare.json").write_text(json.dumps(result, indent=1) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "rows"}))
