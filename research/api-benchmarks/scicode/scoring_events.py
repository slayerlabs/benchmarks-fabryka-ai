"""What happened on the scoring VM, from the files copied off it into results/scoring-vm/: results/scoring-events.json.

Usage: python3 scoring_events.py [results-dir]

Inputs (copied from coding-judge-vm after scoring; PROTOCOL.md Amendment 2):
- `score-scicode.log`: the queue log of /root/score_scicode.sh (code commit, start and end of each model, load);
- `<model-id>.<pass>.stdout.txt`: the scorer's stdout of the final --score of each model (`pass` is the setting, or
  `e1_<setting>` for the E1 pass); a step the scorer had a log for is not run again and prints nothing;
- `kernel-oom.txt`: the kernel's OOM-killer lines (`journalctl -k`, 2026-11-22 17:00 to 2026-11-23 01:00 UTC);
- `disk-full-journal.txt`: the journal's "No space left on device" lines in that period, counted (`uniq -c`);
- `window-<tag>.json`: the re-scoring of the steps whose official verdicts were written around the disk-full window
  (window_rescore.py, run on the VM by `window_rescore.sh`), each comparing the kept verdict with a fresh one;
- `reference-extraction-<model-id>.json`: the same answers extracted from the whole answer, as SciCode's gencode.py
  would, re-scored where the step files differ (reference_extraction.py, run on the VM).
Writes, per run and pass, the step files the final scorer went through (`files`: it prints "Testing function" also
for a step whose log it reuses), those it reports killed by SIGKILL (the container's 48 GB
memory limit: the OOM killer), and its printed correct steps; the kernel's OOM kills (time, container, resident
memory); the disk-full lines; the queue log entries; the re-scoring comparisons; and the sha256 of every input.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any

import provenance

HERE = Path(__file__).resolve().parent
TESTED = re.compile(r"^Testing function (\S+) \.\.\.$", re.MULTILINE)
KILLED = re.compile(r"^Error running script \S+/(\S+)\.py: .* died with <Signals\.SIGKILL: 9>\.$", re.MULTILINE)
PRINTED = re.compile(r"^correct steps: (\d+)/(\d+)$", re.MULTILINE)
OOM_KILL = re.compile(r"^(\w{3} \d+ [\d:]{8}) \S+ kernel: Memory cgroup out of memory: Killed process (\d+) \(\S+\) "
                      r"total-vm:(\d+)kB, anon-rss:(\d+)kB", re.MULTILINE)
OOM_SCOPE = re.compile(r"^(\w{3} \d+ [\d:]{8}) \S+ kernel: oom-kill:.*task_memcg=/system\.slice/docker-([0-9a-f]{12})"
                       r"[0-9a-f]*\.scope,task=\S+,pid=(\d+)", re.MULTILINE)
DISK = re.compile(r"^\s*(\d+) (\w{3} \d+ [\d:]{8}) .*No space left on device", re.MULTILINE)
QUEUE = re.compile(r"^(\S+Z) (.*)$", re.MULTILINE)


def scorer_runs(folder: Path) -> dict[str, dict[str, Any]]:
    runs: dict[str, dict[str, Any]] = {}
    for path in sorted(folder.glob("*.stdout.txt")):
        run, pas = path.name[:-len(".stdout.txt")].rsplit(".", 1)
        text = path.read_text(encoding="utf-8")
        printed = PRINTED.findall(text)
        runs.setdefault(run, {})[pas] = {
            "files": len(TESTED.findall(text)),
            "killed_sigkill": sorted(KILLED.findall(text), key=lambda s: [int(x) for x in s.split(".")]),
            "printed_correct_steps": int(printed[-1][0]) if printed else None}
    return runs


def main(results: Path) -> None:
    folder = results / "scoring-vm"
    oom = (folder / "kernel-oom.txt").read_text(encoding="utf-8")
    scopes = {pid: (t, c) for t, c, pid in OOM_SCOPE.findall(oom)}
    kills = [{"time_utc": t, "container": scopes.get(pid, (None, None))[1], "pid": int(pid),
              "anon_rss_kb": int(rss), "total_vm_kb": int(vm)} for t, pid, vm, rss in OOM_KILL.findall(oom)]
    disk = [{"time_utc": t, "lines": int(n)} for n, t in DISK.findall((folder / "disk-full-journal.txt").read_text())]
    queue = [{"time": t, "entry": e} for t, e in QUEUE.findall((folder / "score-scicode.log").read_text())]
    window = {p.stem[len("window-"):]: json.loads(p.read_text(encoding="utf-8"))
              for p in sorted(folder.glob("window-*.json"))}
    reference = {p.stem[len("reference-extraction-"):]: json.loads(p.read_text(encoding="utf-8"))
                 for p in sorted(folder.glob("reference-extraction-*.json"))}
    record = {
        "scorer_runs_final": scorer_runs(folder),
        "kernel_oom_kills": kills,
        "container_memory_limit": "48g (run.sh --score, docker --memory)",
        "disk_full_journal": disk,
        "queue_log": queue,
        "window_rescore": {tag: {k: v for k, v in w.items() if k not in ("rows", "files_sha256")}
                           for tag, w in window.items()},
        "reference_extraction": {run: {s: {"answers_with_think_end": len(x["answers_with_think_end"]),
                                           "answers_whose_code_differs": len(x["answers_whose_code_differs"]),
                                           "files_differing": len(x["files_differing"]),
                                           "passed_after_think": x["passed_after_think"],
                                           "passed_whole_answer": x["passed_whole_answer"],
                                           "verdicts_changed": len(x["verdicts_changed"]),
                                           "verdicts_of_differing_files": sorted(
                                               {f"{a} -> {b}" for a, b in x["verdicts_of_differing_files"].values()})}
                                       for s, x in r["settings"].items()}
                                 for run, r in reference.items()},
        "inputs_sha256": {p.name: provenance.sha256_file(p) for p in sorted(folder.iterdir()) if p.is_file()},
    }
    (results / "scoring-events.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    provenance.record(results, ["scoring-events.json"], "scoring_events.py")
    print(json.dumps({k: v for k, v in record.items() if k != "inputs_sha256"}, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results")
