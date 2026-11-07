"""tools/start.sh and the GOTOWE list of tools/przebieg_centralny.sh: GOTOWE equals the task ids of the "✅ Gotowe"
section of STATUS.md; start.sh finds the code from its own location and, with START_SUCHO=1, prints the commands
it would run (no GPU, no network). Run: python -m pytest tests/test_start.py"""
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent
SKRYPT = KORZEN / "tools" / "przebieg_centralny.sh"


def env_bez_k(**dodatkowe):
    env = {k: v for k, v in os.environ.items() if k not in ("K", "HF_TOKEN", "START_SUCHO")}
    return {**env, "WS": tempfile.mkdtemp(), **dodatkowe}


def gotowe_skryptu():
    return subprocess.run(["bash", str(SKRYPT), "gotowe"], capture_output=True, text=True, check=True,
                          env=env_bez_k()).stdout.split()


def gotowe_statusu(tekst):
    """(task ids in table order, the count from the heading) of the "✅ Gotowe" section."""
    naglowek, reszta = re.search(r"^## ✅ Gotowe · (\d+)\n(.*?)(?=^## )", tekst, re.MULTILINE | re.DOTALL).groups()
    return re.findall(r"^\|[^|\n]*\| (T\d\d) \|", reszta, re.MULTILINE), int(naglowek)


def test_gotowe_equals_the_gotowe_section_of_status():
    ids, liczba = gotowe_statusu((KORZEN / "STATUS.md").read_text(encoding="utf-8"))
    assert len(ids) == liczba
    assert gotowe_skryptu() == ids


def test_gotowe_are_tasks_of_the_run():
    katalogi = subprocess.run(["bash", str(SKRYPT), "katalogi"], capture_output=True, text=True, check=True,
                              env=env_bez_k()).stdout
    assert set(gotowe_skryptu()) <= {l.split()[0] for l in katalogi.splitlines()}


def test_start_dry_run_from_a_copy_elsewhere_finds_its_code_and_the_gotowe_list():
    kopia = Path(tempfile.mkdtemp()) / "klon" / "research"
    shutil.copytree(KORZEN / "tools", kopia / "tools")
    wynik = subprocess.run(["bash", str(kopia / "tools" / "start.sh"), "slayer1b-1.07"], capture_output=True,
                           text=True, cwd=tempfile.mkdtemp(), env=env_bez_k(HF_TOKEN="x", START_SUCHO="1"))
    assert wynik.returncode == 0, wynik.stderr
    assert f"kod (K): {kopia}" in wynik.stdout
    licz = f'bash {kopia}/tools/przebieg_centralny.sh licz "slayer1b-1.07:{",".join(gotowe_skryptu())}"'
    assert licz in wynik.stdout.splitlines()
    assert f"bash {kopia}/tools/przebieg_centralny.sh przygotuj 172800" in wynik.stdout.splitlines()


def test_start_wszystkie_counts_the_whole_model():
    wynik = subprocess.run(["bash", str(KORZEN / "tools" / "start.sh"), "slayer1b-1.07", "wszystkie"],
                           capture_output=True, text=True, check=True,
                           env=env_bez_k(HF_TOKEN="x", START_SUCHO="1", LIMIT_S="60"))
    assert f'bash {SKRYPT} licz "slayer1b-1.07"' in wynik.stdout.splitlines()
    assert f"bash {SKRYPT} przygotuj 60" in wynik.stdout.splitlines()


def test_start_without_hf_token_stops_before_anything_runs():
    wynik = subprocess.run(["bash", str(KORZEN / "tools" / "start.sh"), "slayer1b-1.07"], capture_output=True,
                           text=True, env=env_bez_k(START_SUCHO="1"))
    assert wynik.returncode == 3 and "HF_TOKEN" in wynik.stderr and "przygotuj" not in wynik.stdout


def test_start_unknown_model_or_scope_is_a_usage_error():
    for args in (["slayer9"], ["slayer1b-1.07", "polowa"], []):
        wynik = subprocess.run(["bash", str(KORZEN / "tools" / "start.sh"), *args], capture_output=True, text=True,
                               env=env_bez_k(HF_TOKEN="x", START_SUCHO="1"))
        assert wynik.returncode == 2, args


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__]))
