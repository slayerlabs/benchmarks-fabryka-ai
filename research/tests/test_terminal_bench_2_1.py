"""Terminal-Bench 2.1 (research/benchmarks/terminal-bench-2-1), no network, Docker or model.

- summarize.py on small synthetic Harbor jobs: a trial with a test result counts whatever Harbor's label says, a
  trial without one needs a re-run, the re-run is counted in its place (as a failure when it has no result again),
  a model-server error event blocks the score, and long tool outputs and reasoning are cut with their start and end;
- summarize.main: it writes nothing when a trial is missing or tasks have different trial counts, and a server error
  in a re-run blocks too;
- the committed results: an independent recount of score, both stderrs and n from the .jsonl.gz, the recorded jobs, the same counted-trial
  number for every task, the file under 10 MB, and the README row.
Run: python tests/test_terminal_bench_2_1.py (or pytest).
"""
import gzip
import importlib.util
import json
import math
import statistics
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / "benchmarks" / "terminal-bench-2-1"
spec = importlib.util.spec_from_file_location("tb21_summarize", HERE / "summarize.py")
summarize = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summarize)


def trial(job: Path, name: str, reward=None, label=None, events=("stop",), log="", server_error=False):
    d = job / name
    (d / "agent").mkdir(parents=True)
    result = {
        "task_name": "terminal-bench/" + name.split("__")[0],
        "trial_name": name,
        "verifier_result": None if reward is None else {"rewards": {"reward": reward}},
        "exception_info": None if label is None else {"exception_type": label,
                                                      "exception_message": "Command failed (exit 1): opencode"},
        "agent_result": {"n_input_tokens": 10, "n_output_tokens": 2},
    }
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    (d / "trial.log").write_text(log, encoding="utf-8")
    lines = [{"type": "step_finish", "part": {"reason": r}} for r in events]
    if server_error:
        lines.insert(0, {"type": "error", "error": "500"})
    if events or server_error:
        (d / "agent" / "opencode.txt").write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")


def test_counting_rules():
    with tempfile.TemporaryDirectory() as tmp:
        main, rerun = Path(tmp) / "main", Path(tmp) / "rerun"
        trial(main, "a__1", reward=1.0, label="ApiRateLimitError")  # EPIPE exit labelled "rate limit": counts
        trial(main, "a__2", reward=0.0)
        trial(main, "b__1", reward=None, events=())  # agent never started
        trial(main, "b__2", reward=None, log="VerifierTimeoutError")
        rows = summarize.load(main)
        assert {r["trial"]: r["status"] for r in rows} == {
            "a__1": "scored", "a__2": "scored", "b__1": "agent_not_started", "b__2": "verifier_timeout"}
        assert len(summarize.count(rows, [])) == 2  # two missing trials, no re-run: blocked

        trial(rerun, "b__3", reward=1.0)
        trial(rerun, "b__4", reward=None)
        rows, extra = summarize.load(main), summarize.load(rerun)
        assert summarize.count(rows, extra) == []
        counted = [r for r in rows + extra if r["counted"]]
        assert sorted((r["trial"], r["score"]) for r in counted) == [
            ("a__1", 1.0), ("a__2", 0.0), ("b__3", 1.0), ("b__4", 0.0)]
        assert next(r for r in extra if r["trial"] == "b__4")["counted_as_failure"]
        assert {r["replaces"] for r in extra} == {"b__1", "b__2"}


def test_rerun_without_missing_trial_and_server_error_block():
    with tempfile.TemporaryDirectory() as tmp:
        main, rerun = Path(tmp) / "main", Path(tmp) / "rerun"
        trial(main, "a__1", reward=0.0, server_error=True)
        trial(rerun, "a__2", reward=1.0)
        problems = summarize.count(summarize.load(main), summarize.load(rerun))
        assert any("model-server error" in p for p in problems)
        assert any("replaces nothing" in p for p in problems)


def test_server_error_in_a_rerun_blocks():
    with tempfile.TemporaryDirectory() as tmp:
        main, rerun = Path(tmp) / "main", Path(tmp) / "rerun"
        trial(main, "a__1", reward=None, events=())
        trial(rerun, "a__2", reward=1.0, server_error=True)
        problems = summarize.count(summarize.load(main), summarize.load(rerun))
        assert problems == ["a__2: 1 model-server error events"]


def run_main(job: Path, out: Path, *rerun: Path) -> int:
    args = [str(job), "--model", "m", "--out-dir", str(out)]
    for r in rerun:
        args += ["--rerun", str(r)]
    return summarize.main(args)


def test_main_writes_nothing_when_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        main, out = Path(tmp) / "main", Path(tmp) / "out"
        trial(main, "a__1", reward=1.0)
        trial(main, "b__1", reward=None, events=())  # missing, no re-run
        assert run_main(main, out) == 1
        assert not out.exists()


def test_main_refuses_unequal_trial_counts():
    with tempfile.TemporaryDirectory() as tmp:
        main, out = Path(tmp) / "main", Path(tmp) / "out"
        trial(main, "a__1", reward=1.0)
        trial(main, "a__2", reward=0.0)
        trial(main, "b__1", reward=1.0)
        assert run_main(main, out) == 1
        assert not out.exists()


def test_main_writes_score_and_both_stderrs():
    with tempfile.TemporaryDirectory() as tmp:
        main, out = Path(tmp) / "main", Path(tmp) / "out"
        for name, reward in (("a__1", 1.0), ("a__2", 1.0), ("b__1", 0.0), ("b__2", 1.0)):
            trial(main, name, reward=reward)
        assert run_main(main, out) == 0
        result = json.loads((out / "m.json").read_text(encoding="utf-8"))
        assert result["score"] == 75.0 and result["n"] == 2
        assert result["stderr"] == round(100 * statistics.stdev([1.0, 0.5]) / math.sqrt(2), 2)
        assert result["other_metrics"]["stderr_per_trial"] == round(100 * math.sqrt(0.75 * 0.25 / 4), 2)


def test_compact_keeps_calls_and_cuts_long_text():
    long = "x" * 10_000
    traj = {"session_id": "s", "agent": {}, "final_metrics": {}, "steps": [{
        "step_id": 1, "timestamp": "t", "metrics": {}, "message": long, "reasoning_content": long,
        "tool_calls": [{"arguments": {"command": long}}],
        "observation": {"results": [{"content": long}]},
    }]}
    step = summarize.compact(traj)["steps"][0]
    assert "timestamp" not in step and "metrics" not in step
    assert step["message"] == long and step["tool_calls"][0]["arguments"]["command"] == long
    assert len(step["reasoning_content"]) < summarize.REASONING_CHARS + 100
    assert len(step["observation"]["results"][0]["content"]) < summarize.OBSERVATION_CHARS + 100
    assert summarize.cut("short", 10) == "short"


def test_committed_results_recount():
    for path in sorted((HERE / "results").glob("*.json")):
        result = json.loads(path.read_text(encoding="utf-8"))
        rows_path = path.with_suffix(".jsonl.gz")
        if result["score"] is None:
            assert result["n"] == 0 and not rows_path.exists()
            continue
        assert rows_path.stat().st_size < 10_000_000
        by_task = defaultdict(list)
        with gzip.open(rows_path, "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r["counted"]:
                    by_task[r["task"]].append(r["score"])
        assert len({len(v) for v in by_task.values()}) == 1
        per_task = [statistics.fmean(v) for v in by_task.values()]
        assert len(per_task) == result["n"] == 89
        assert round(100 * statistics.fmean(per_task), 2) == result["score"]
        assert round(100 * statistics.stdev(per_task) / math.sqrt(len(per_task)), 2) == result["stderr"]
        trials = [s for v in by_task.values() for s in v]
        p = statistics.fmean(trials)
        assert round(100 * math.sqrt(p * (1 - p) / len(trials)), 2) == result["other_metrics"]["stderr_per_trial"]
        jobs = result["settings"]["jobs"]
        assert [j["job"] for j in jobs] == [result["model"], *result["settings"]["rerun_jobs"]]
        assert jobs[0]["n_concurrent_trials"] == 8 and all(j["n_concurrent_trials"] == 4 for j in jobs[1:])
        readme = (HERE / "README.md").read_text(encoding="utf-8")
        assert f"(`{result['model']}`)" in readme and f"| {result['score']:.2f} | {result['stderr']:.2f} | 89 |" in readme


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    sys.exit(0)
