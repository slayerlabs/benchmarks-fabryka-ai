"""tools/straznik_bezczynnosci.py (idle guard) and tools/kontrola_sensu.py (sanity check), on stand-ins."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KORZEN / "tools"))
import kontrola_sensu as KS  # noqa: E402
import straznik_bezczynnosci as SB  # noqa: E402


def probki(od, do, gpu=0.0, kolejka=0, krok=60):
    return [(t, gpu, kolejka) for t in range(od, do + 1, krok)]


def test_idle_only_after_full_window():
    assert not SB.bezczynny(probki(0, 540), 540)
    assert SB.bezczynny(probki(0, 600), 600)


def test_busy_gpu_or_running_evaluation_resets_idle():
    assert not SB.bezczynny(probki(0, 540) + [(600, 40.0, 0)], 600)
    assert not SB.bezczynny(probki(0, 540) + [(600, 0.0, 1)], 600)
    # activity older than the window does not count
    assert SB.bezczynny([(0, 90.0, 1)] + probki(60, 720), 720)


def test_broken_probe_counts_as_busy():
    assert SB.liczba("false") == float("inf")
    assert SB.liczba("echo 3") == 3.0


def test_loop_packs_copies_and_destroys_when_idle():
    d = Path(tempfile.mkdtemp())
    archiwum = d / "wyniki.tgz"
    znacznik = d / "zniszczona"
    kod = SB.main(["--wyjscie", str(d / "wyjscie"), "--okno", "0.05", "--interwal", "0.01",
                   "--gpu", "echo 0", "--kolejka", "echo 0", "--pakuj", f"echo x > {archiwum}",
                   "--archiwum", str(archiwum), "--zniszcz", f"touch {znacznik}"])
    assert kod == 0 and znacznik.exists() and (d / "wyjscie" / "wyniki.tgz").exists()


def test_live_work_marker_counts_and_dead_one_does_not():
    d = Path(tempfile.mkdtemp())
    assert SB.zywe_znaczniki(d / "brak") == 0
    martwy = subprocess.Popen(["true"])
    martwy.wait()
    (d / f"{martwy.pid}_slayer").write_text("x")
    assert SB.zywe_znaczniki(d) == 0  # killed run: the marker stays, the guard may still destroy
    (d / f"{os.getpid()}_slayer").write_text("x")
    assert SB.zywe_znaczniki(d) == 1


def straznik(d, praca, czas):
    """The guard loop as a process on stand-ins (idle GPU, no ewaluuj.py); True when it destroyed within `czas` s."""
    znacznik = d / "zniszczona"
    p = subprocess.Popen([sys.executable, str(KORZEN / "tools" / "straznik_bezczynnosci.py"), "--wyjscie",
                          str(d / "wyjscie"), "--okno", "0.2", "--interwal", "0.05", "--gpu", "echo 0", "--kolejka",
                          "echo 0", "--praca", str(praca), "--pakuj", "true", "--archiwum", str(d / "brak.tgz"),
                          "--zniszcz", f"touch {znacznik}"])
    try:
        p.wait(timeout=czas)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    return znacznik.exists()


def test_guard_waits_while_the_run_script_works_and_destroys_when_idle():
    d = Path(tempfile.mkdtemp())
    praca = d / "praca"
    praca.mkdir()
    pracuje = subprocess.Popen(["sleep", "30"])  # e.g. the bash of licz_model converting weights or running ewok.py
    try:
        (praca / f"{pracuje.pid}_slayer1b-1.07").write_text("x")
        assert straznik(d, praca, 2.0) is False
    finally:
        pracuje.kill()
        pracuje.wait()
    assert straznik(d, praca, 5.0) is True


def test_run_script_holds_a_live_marker_during_conversion_and_own_code_task():
    """licz_model on stand-in venvs: when konwertuj.py and ewok.py (T53) start, a live marker is in $ST/praca;
    after the model the marker is gone."""
    ws = Path(tempfile.mkdtemp())
    (ws / "logi").mkdir()
    for env in ("lock", "new"):
        py = ws / f"venv-{env}" / "bin" / "python"
        py.parent.mkdir(parents=True)
        py.write_text("#!/bin/sh\ncase \"$*\" in *konwertuj.py*|*ewok.py*)\n"
                      f"  for f in {ws}/stan/praca/*_*; do n=$(basename \"$f\"); "
                      f"kill -0 \"${{n%%_*}}\" 2>/dev/null && echo \"$1\" >> {ws}/zywe.log; done;;\nesac\nexit 0\n")
        py.chmod(0o755)
    skrypt = KORZEN / "tools" / "przebieg_centralny.sh"
    env = {**os.environ, "WS": str(ws), "K": str(KORZEN), "ZADANIA_ID": "T02 T53", "DEVICE": "cpu"}
    wynik = subprocess.run(["bash", "-c", f"source {skrypt} _funkcje; licz_kolejke - slayer1b-1.07"],
                           capture_output=True, text=True, env=env)
    assert wynik.returncode == 0, wynik.stderr
    zywe = (ws / "zywe.log").read_text().splitlines()
    assert any(z.endswith("konwertuj.py") for z in zywe) and any(z.endswith("ewok.py") for z in zywe)
    assert not list((ws / "stan" / "praca").iterdir())


def obs(task, metric, value, chance, state="ok"):
    space = {"acc": {"value": value}, "acc_norm": {"value": value}, "bazy": {"chance_value": chance}}
    return {"task_id": task, "metric": metric, "state": state, "dodatkowe": {"space": space}}


def test_sanity_flags_perfect_and_below_random():
    assert KS.bledy_obserwacji(obs("T02", "acc_norm,none", 0.5, 0.25)) == []
    assert KS.bledy_obserwacji(obs("T02", "acc_norm,none", 1.0, 0.25))
    assert KS.bledy_obserwacji(obs("T45", "acc,none", 0.19, 0.25))
    assert KS.bledy_obserwacji(obs("T45", "acc,none", 0.21, 0.25)) == []


def test_sanity_flags_one_choice_per_question_and_failed_task():
    assert any("one choice" in b for b in KS.bledy_obserwacji(obs("T01", "acc,none", 0.8, 1.0)))
    assert KS.bledy_obserwacji({"task_id": "T03", "state": "failed", "reason": "OOM"})


def test_load_test_mode_checks_only_that_the_task_finished():
    assert KS.bledy_obserwacji(obs("T02", "acc_norm,none", 1.0, 0.25), tylko_stan=True) == []
    assert KS.bledy_obserwacji(obs("T02", "acc_norm,none", 0.0, 0.25), tylko_stan=True) == []
    assert KS.bledy_obserwacji(obs("T02", "acc_norm,none", 0.0, 0.25, state="failed"), tylko_stan=True)


def test_sanity_perplexity_and_exit_code():
    d = Path(tempfile.mkdtemp())
    ok = {"task_id": "T03", "metric": "byte_perplexity,none", "state": "ok",
          "dodatkowe": {"space": {"byte_perplexity": {"value": 1.85}}}}
    (d / "results_rozszerzone.json").write_text(json.dumps({"observations": [ok]}))
    assert KS.main([str(d)]) == 0
    ok["dodatkowe"]["space"]["byte_perplexity"]["value"] = float("nan")
    (d / "results_rozszerzone.json").write_text(json.dumps({"observations": [ok]}))
    assert KS.main([str(d)]) == 1
    assert KS.main([str(d / "brak")]) == 1


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
