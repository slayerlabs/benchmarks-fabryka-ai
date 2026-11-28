"""The effect of extracting code from the text after the last `</think>` (PROTOCOL.md, "Settings") instead of from the
whole answer, as SciCode @ e3158ea0 does (gencode.py hands the whole response to extract_python_script; it knows no
`</think>`). For a model whose answers contain `</think>` the step files differ: this rebuilds them from the recorded
answers with the official extraction on the whole answer (Gencode assembles them with the earlier steps' code, as
the E1 files), scores only the files that differ from the official ones with the unchanged scorer, and keeps the
official verdict for the rest. Descriptive (README, Deviations); no verdict reads it.

Usage, in the scoring container (as run.sh --score, without network), from this directory:
    python reference_extraction.py <out-dir> <work-dir>
Writes <work-dir>/reference-extraction.json. `<out-dir>/generations.jsonl` and `graded.jsonl` must have the sha256
their writers recorded in `<out-dir>/manifest.json`; both sha256 go into the output.
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


def whole_answer_code(h: Any) -> Callable[[dict[str, Any]], str]:
    """What gencode.py would extract: the whole response (a prompt over the context gave no response: empty)."""
    return lambda a: h.models.extract_python_script(a["output"]) if a["status"] == "ok" else ""


def compare(out: Path, model: str, work: Path, h: Any, rows: list[dict[str, Any]],
            score_subset: Callable[[str, Path], dict[str, str]]) -> dict[str, Any]:
    hashes = provenance.verify(out, ["generations.jsonl", "graded.jsonl"], "reference_extraction.py")
    answers = sr.latest(sr.read_jsonl(out / "generations.jsonl"))
    graded = {(r["setting"], r["problem_id"], int(r["step"])): r for r in sr.read_jsonl(out / "graded.jsonl")}
    settings = sorted({k[0] for k in graded}, key=sr.SETTINGS.index)
    expected = sr.expected_steps(rows)
    code_dir = work / "generated_code"
    sr.build_step_files(h, rows, answers, settings, model, code_dir, whole_answer_code(h))
    result: dict[str, Any] = {"model": model, "inputs_sha256": hashes, "settings": {}}
    for setting in settings:
        official, rebuilt = out / "generated_code" / model / setting, code_dir / model / setting
        differ = [f"{p}.{s}" for p, s in expected
                  if (rebuilt / f"{p}.{s}.py").read_bytes() != (official / f"{p}.{s}.py").read_bytes()]
        scored = work / "scored" / model / setting
        scored.mkdir(parents=True)
        for name in differ:
            shutil.copyfile(rebuilt / f"{name}.py", scored / f"{name}.py")
        again = score_subset(setting, work / "scored") if differ else {}
        kept = {f"{p}.{s}": graded[(setting, p, s)]["verdict"] for p, s in expected}
        whole = {name: again.get(name, kept[name]) for name in kept}
        think_end = sorted((f"{p}.{s}" for p, s in expected if "</think>" in answers[(setting, p, s)].get("output", "")),
                           key=lambda x: [int(y) for y in x.split(".")])
        result["settings"][setting] = {
            "answers_with_think_end": think_end,
            "answers_whose_code_differs": [n for n in think_end
                                           if whole_answer_code(h)(answers[(setting, *_split(n))]) !=
                                           graded[(setting, *_split(n))]["code"]],
            "files_differing": differ,
            "passed_after_think": sum(v == "pass" for v in kept.values()),
            "passed_whole_answer": sum(v == "pass" for v in whole.values()),
            "verdicts_changed": {n: [kept[n], whole[n]] for n in kept if kept[n] != whole[n]},
            "verdicts_of_differing_files": {n: [kept[n], whole[n]] for n in differ},
        }
    return result


def _split(name: str) -> tuple[str, int]:
    p, s = name.split(".")
    return p, int(s)


def main(argv: list[str]) -> None:
    out, work = Path(argv[0]).resolve(), Path(argv[1]).resolve()
    model = out.name
    sr.scoring_environment("reference_extraction.py")
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))["scoring"]
    rows = sr.load_split(run["split"], run["limit"])
    h = sr.harness()
    with tempfile.TemporaryDirectory() as tmp:
        root = sr.scratch_copy(Path(tmp), sr.H5_PATH)
        env = {**os.environ, **sr.BLAS_THREADS, "PYTHONPATH": str(root / "src"), "PYTHONUNBUFFERED": "1"}

        def score_subset(setting: str, code_dir: Path) -> dict[str, str]:
            args = argparse.Namespace(model_id=model, split=run["split"])
            sr.run_scorer(root, env, args, setting, code_dir, work, "logs", f"reference_{setting}")
            logs = work / "logs" / model / setting
            return {p.stem: p.read_text(encoding="utf-8").splitlines()[0] for p in logs.glob("*.txt")}

        result = compare(out, model, work, h, rows, score_subset)
    (work / "reference-extraction.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({s: {k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in x.items()}
                      for s, x in result["settings"].items()}))


if __name__ == "__main__":
    main(sys.argv[1:])
