"""Re-scores official step files with the unchanged scorer and compares the verdicts with the ones in the results
(PROTOCOL.md Amendment 2: the steps whose verdicts were written around the scoring VM's disk-full window).

Usage, in the scoring container (as run.sh --score, without network), from this directory:
    python window_rescore.py <out-dir> <setting> <work-dir> <step> [<step> ...]
Writes <work-dir>/compare.json.

Inputs are checked before anything runs: `<out-dir>/graded.jsonl` must have the sha256 `scicode_runner.py score`
recorded in `<out-dir>/manifest.json` (its verdicts are the kept ones), and each step's official file
`<out-dir>/generated_code/<model>/<setting>/<step>.py` must end with that step's extracted code in graded.jsonl, as
save_response_with_steps writes it; otherwise nothing is scored. The sha256 of graded.jsonl and of every file
scored go into compare.json.
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

import provenance
import scicode_runner as sr

Scorer = Callable[..., dict[str, Any]]


def kept_verdicts(out: Path, setting: str, steps: list[str]) -> tuple[dict[str, dict[str, Any]], str]:
    sha = provenance.verify(out, ["graded.jsonl"], "window_rescore.py")["graded.jsonl"]
    graded = {f"{r['problem_id']}.{r['step']}": r for r in sr.read_jsonl(out / "graded.jsonl") if r["setting"] == setting}
    missing = [s for s in steps if s not in graded]
    if missing:
        sys.exit(f"window_rescore.py: {out / 'graded.jsonl'} has no {setting} step {missing[0]}")
    return {s: graded[s] for s in steps}, sha


def compare(out: Path, model: str, setting: str, steps: list[str], work: Path, root: Path | None, env: dict[str, str],
            scorer: Scorer) -> dict[str, Any]:
    kept, graded_sha = kept_verdicts(out, setting, steps)
    official = out / "generated_code" / model / setting
    files = {}
    for s in steps:
        text = (official / f"{s}.py").read_text(encoding="utf-8")
        if not text.endswith("\n" + (kept[s]["code"] or "")):
            sys.exit(f"window_rescore.py: {official / (s + '.py')} does not end with step {s}'s code in graded.jsonl")
        files[s] = provenance.sha256_file(official / f"{s}.py")
    code = work / "code" / model / setting
    code.mkdir(parents=True)
    for s in steps:
        shutil.copyfile(official / f"{s}.py", code / f"{s}.py")
    run = scorer(root, env, argparse.Namespace(model_id=model, split="test"), setting, work / "code", work, "logs",
                 "rescore")
    rows = []
    for s in steps:
        again = (work / "logs" / model / setting / f"{s}.txt").read_text(encoding="utf-8").splitlines()[0]
        rows.append({"step": s, "kept": kept[s]["verdict"], "rescored": again, "same": kept[s]["verdict"] == again})
    return {"model": model, "setting": setting, "steps": len(steps), "same": sum(r["same"] for r in rows),
            "differ": [r for r in rows if not r["same"]], "rows": rows, "scorer_seconds": run["seconds"],
            "graded_sha256": graded_sha, "files_sha256": files}


def main(argv: list[str]) -> None:
    out, setting, work, steps = Path(argv[0]).resolve(), argv[1], Path(argv[2]).resolve(), argv[3:]
    model = out.name
    sr.scoring_environment("window_rescore.py")
    with tempfile.TemporaryDirectory() as tmp:
        root = sr.scratch_copy(Path(tmp), sr.H5_PATH)
        env = {**os.environ, **sr.BLAS_THREADS, "PYTHONPATH": str(root / "src"), "PYTHONUNBUFFERED": "1"}
        result = compare(out, model, setting, steps, work, root, env, sr.run_scorer)
    (work / "compare.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in ("rows", "files_sha256")}))


if __name__ == "__main__":
    main(sys.argv[1:])
