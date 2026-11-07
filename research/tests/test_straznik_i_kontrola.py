"""tools/straznik_bezczynnosci.py (idle guard) and tools/kontrola_sensu.py (sanity check), on stand-ins."""
import http.server
import json
import os
import subprocess
import sys
import threading
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


def test_loop_packs_copies_and_stops_when_idle():
    d = Path(tempfile.mkdtemp())
    archiwum = d / "wyniki.tgz"
    znacznik = d / "zatrzymana"
    kod = SB.main(["--wyjscie", str(d / "wyjscie"), "--okno", "0.05", "--interwal", "0.01",
                   "--gpu", "echo 0", "--kolejka", "echo 0", "--pakuj", f"echo x > {archiwum}",
                   "--archiwum", str(archiwum), "--zatrzymaj", f"touch {znacznik}"])
    assert kod == 0 and znacznik.exists() and (d / "wyjscie" / "wyniki.tgz").exists()


class AtrapaVast:
    """Stand-in vast.ai API on localhost: records (method, path, JSON body, Authorization) of every call."""

    def __init__(self, kod=200, odpowiedz=b'{"success": true, "instances": {}}'):
        wywolania = self.wywolania = []

        class H(http.server.BaseHTTPRequestHandler):
            def _zapisz(self):
                n = int(self.headers.get("Content-Length") or 0)
                cialo = json.loads(self.rfile.read(n)) if n else None
                wywolania.append((self.command, self.path, cialo, self.headers.get("Authorization")))
                self.send_response(kod)
                self.end_headers()
                self.wfile.write(odpowiedz)

            do_GET = do_PUT = do_DELETE = _zapisz

            def log_message(self, *a):
                pass

        self.serwer = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.serwer.serve_forever, daemon=True).start()
        self.env = {**os.environ, "BEZPIECZNIK_API": f"http://127.0.0.1:{self.serwer.server_port}/api/v0/instances/",
                    "CONTAINER_ID": "123", "CONTAINER_API_KEY": "klucz", "BEZPIECZNIK_PAUZA": "0"}

    def metody(self):
        return [(m, p, c) for m, p, c, _ in self.wywolania]

    def zamknij(self):
        self.serwer.shutdown()


def test_safety_limit_packs_then_destroys_and_idle_stop_is_put_stopped():
    api = AtrapaVast()
    try:
        d = Path(tempfile.mkdtemp())
        bez = str(KORZEN / "slayer-1b" / "wygaszanie" / "bezpiecznik.py")
        subprocess.run([sys.executable, bez, "po", "0", f"touch {d / 'spakowane'}"], env=api.env, check=True,
                       capture_output=True, timeout=30)
        assert (d / "spakowane").exists() and api.metody() == [("DELETE", "/api/v0/instances/123/", None)]
        assert api.wywolania[0][3] == "Bearer klucz"
        api.wywolania.clear()
        kod = subprocess.run([sys.executable, "-c", f"import sys; sys.path.insert(0, {str(Path(bez).parent)!r}); "
                              "import bezpiecznik; bezpiecznik.zatrzymaj('idle')"], env=api.env, timeout=30).returncode
        assert kod == 0 and api.metody() == [("PUT", "/api/v0/instances/123/", {"state": "stopped"})]
    finally:
        api.zamknij()


def test_live_work_marker_counts_and_dead_one_does_not():
    d = Path(tempfile.mkdtemp())
    assert SB.zywe_znaczniki(d / "brak") == 0
    martwy = subprocess.Popen(["true"])
    martwy.wait()
    (d / f"{martwy.pid}_slayer").write_text("x")
    assert SB.zywe_znaczniki(d) == 0  # killed run: the marker stays, the guard may still destroy
    (d / f"{os.getpid()}_slayer").write_text("x")
    assert SB.zywe_znaczniki(d) == 1


def straznik(d, praca, czas, api, wynik=None):
    """The guard loop as a process on stand-ins (idle GPU, no ewaluuj.py) with its default action against the stand-in
    vast.ai API; returns the API calls made within `czas` s (exit code and stdout into `wynik`, when given)."""
    p = subprocess.Popen([sys.executable, str(KORZEN / "tools" / "straznik_bezczynnosci.py"), "--wyjscie",
                          str(d / "wyjscie"), "--okno", "0.2", "--interwal", "0.05", "--gpu", "echo 0", "--kolejka",
                          "echo 0", "--praca", str(praca), "--pakuj", "true", "--archiwum", str(d / "brak.tgz"),
                          "--blad", str(d / "stan" / "STOP_NIEUDANY.txt")],
                         env=api.env, stdout=subprocess.PIPE, text=True)
    try:
        out, _ = p.communicate(timeout=czas)
    except subprocess.TimeoutExpired:
        p.kill()
        out, _ = p.communicate()
    if wynik is not None:
        wynik.update(kod=p.returncode, out=out)
    return api.metody()


def test_failed_stop_exits_non_zero_with_a_readable_line_and_never_destroys():
    """403 on every try, and 200 with {"success": false}: both are a failed stop, never a DELETE."""
    for kod, odp in ((403, b'{"success": false, "msg": "forbidden"}'), (200, b'{"success": false, "msg": "no"}')):
        d = Path(tempfile.mkdtemp())
        api = AtrapaVast(kod, odp)
        try:
            wynik = {}
            wywolania = straznik(d, d / "praca", 30.0, api, wynik)
        finally:
            api.zamknij()
        assert wywolania and {m for m, _, _ in wywolania} == {"PUT"}, (kod, wywolania)
        assert wynik["kod"] != 0 and "STOP NIEUDANY, instancja dalej dziala" in wynik["out"]
        assert "STOP NIEUDANY" in (d / "stan" / "STOP_NIEUDANY.txt").read_text()
        env = {**os.environ, "WS": str(d), "K": str(KORZEN)}
        stan = subprocess.run(["bash", str(KORZEN / "tools" / "przebieg_centralny.sh"), "stan"], capture_output=True,
                              text=True, env=env)
        assert "STOP NIEUDANY, instancja dalej dziala" in stan.stdout


def test_guard_waits_while_the_run_script_works_and_stops_not_destroys_when_idle():
    d = Path(tempfile.mkdtemp())
    praca = d / "praca"
    praca.mkdir()
    api = AtrapaVast()
    pracuje = subprocess.Popen(["sleep", "30"])  # e.g. the bash of licz_model converting weights or running ewok.py
    try:
        (praca / f"{pracuje.pid}_slayer1b-1.07").write_text("x")
        assert straznik(d, praca, 2.0, api) == []
        pracuje.kill()
        pracuje.wait()
        assert straznik(d, praca, 10.0, api) == [("PUT", "/api/v0/instances/123/", {"state": "stopped"})]
    finally:
        pracuje.kill()
        api.zamknij()


def test_przygotuj_holds_a_live_marker_while_the_guard_starts_and_drops_it_at_exit():
    """`przygotuj` on a stand-in python3: when the guard is started, a live `przygotuj` marker is in $ST/praca; the
    safety limit gets the pack command; the stage then fails at `bezpiecznik.py sprawdz` and the marker is gone."""
    ws = Path(tempfile.mkdtemp())
    bin_ = Path(tempfile.mkdtemp())
    (bin_ / "python3").write_text(
        "#!/bin/sh\necho \"$*\" >> " + str(ws / "wywolania.log") + "\n"
        "case \"$*\" in *straznik_bezczynnosci.py*)\n"
        f"  for f in {ws}/stan/praca/*_przygotuj; do n=$(basename \"$f\"); "
        f"kill -0 \"${{n%%_*}}\" 2>/dev/null && echo zywy >> {ws}/zywe.log; done;;\n"
        "  *sprawdz*) sleep 1; exit 1;;\nesac\nexit 0\n")
    (bin_ / "python3").chmod(0o755)
    env = {**os.environ, "WS": str(ws), "K": str(KORZEN), "PATH": f"{bin_}:{os.environ['PATH']}"}
    wynik = subprocess.run(["bash", str(KORZEN / "tools" / "przebieg_centralny.sh"), "przygotuj", "100"],
                           capture_output=True, text=True, env=env)
    assert wynik.returncode != 0  # stopped by the stand-in `sprawdz`
    assert (ws / "zywe.log").read_text().split() == ["zywy"]
    wywolania = (ws / "wywolania.log").read_text()
    assert f"bezpiecznik.py po 100 bash {KORZEN}/tools/przebieg_centralny.sh pakuj" in wywolania
    assert f"--praca {ws}/stan/praca" in wywolania
    assert not list((ws / "stan" / "praca").iterdir())


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


def obs_se(value, se, chance, majority=None, task="T45"):
    space = {"acc": {"value": value, "se": se}, "bazy": {"chance_value": chance, "majority_value": majority}}
    return {"task_id": task, "metric": "acc,none", "state": "ok", "dodatkowe": {"space": space}}


def test_baseline_control_uses_the_higher_baseline_plus_two_se():
    # MedMCQA-like: random 0.25, constant answer 0.3223; 0.316 is far above random but not above b + 2 SE
    assert "baseline level" in KS.na_poziomie_bazy(obs_se(0.316, 0.0072, 0.25, 0.3223))
    assert KS.na_poziomie_bazy(obs_se(0.34, 0.0072, 0.25, 0.3223)) is None  # 0.34 > 0.3223 + 0.0144
    assert KS.na_poziomie_bazy(obs_se(0.27, 0.01, 0.25)) is not None  # no constant answer: b = random
    assert KS.na_poziomie_bazy(obs_se(0.30, 0.01, 0.25)) is None
    assert KS.na_poziomie_bazy(obs_se(0.30, None, 0.25)) is None  # no SE: nothing to check


def test_baseline_control_reads_the_paired_comparison_when_the_run_wrote_it():
    # PubMedQA LFM3-like: 0.594 is not above 0.552 + 2 x 0.022 unpaired, but the paired difference is 4.3 SE
    o = obs_se(0.594, 0.022, 1 / 3, 0.552, task="T44")
    o["dodatkowe"]["space"]["wobec_b"] = {"b": 0.552, "baza": "stala odpowiedz", "roznica": 0.042, "se": 0.0098,
                                          "z": 4.27, "werdykt": "pewne"}
    assert KS.na_poziomie_bazy(o) is None
    o["dodatkowe"]["space"]["wobec_b"].update(roznica=-0.0062, z=-2.04, werdykt="prawdopodobne")  # under b
    assert "baseline level" in KS.na_poziomie_bazy(o)
    o["dodatkowe"]["space"]["wobec_b"].update(roznica=0.01, z=None, t=1.5, df=66, werdykt="szum")
    assert "t 1.50 df 66" in KS.na_poziomie_bazy(o)


def test_baseline_control_on_the_subset_and_skips_perplexity():
    squad = {"task_id": "T38", "metric": "f1", "state": "ok", "dodatkowe": {"space": {
        "glowna": {"value": 0.5, "se": 0.01, "metryka": "f1"}, "bazy": {"chance_value": 0.0, "majority_value": 0.5},
        "podzbior": {"glowna": {"value": 0.05, "se": 0.01}, "bazy": {"chance_value": 0.0, "majority_value": 0.0}}}}}
    assert KS.na_poziomie_bazy(squad) is None  # HasAns: 0.05 > 0 + 0.02, the empty-answer b of the full set ignored
    ppl = {"task_id": "T03", "state": "ok", "dodatkowe": {"space": {"byte_perplexity": {"value": 1.8, "se": 0.01}}}}
    assert KS.na_poziomie_bazy(ppl) is None


def test_baseline_flag_is_listed_but_does_not_fail_the_run(capsys):
    d = Path(tempfile.mkdtemp())
    (d / "results_rozszerzone.json").write_text(json.dumps({"observations": [obs_se(0.316, 0.0072, 0.25, 0.3223)]}))
    assert KS.main([str(d)]) == 0
    assert "at baseline level" in capsys.readouterr().out


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
