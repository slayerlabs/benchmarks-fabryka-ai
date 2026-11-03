"""tools/straznik_bezczynnosci.py (idle guard) and tools/kontrola_sensu.py (sanity check), on stand-ins."""
import json
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
