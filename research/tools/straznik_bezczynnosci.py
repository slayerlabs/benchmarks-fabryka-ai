"""Idle guard for a vast.ai instance, next to the time limit of slayer-1b/wygaszanie/bezpiecznik.py.

GPU utilisation below PROG % with no ewaluuj.py running, for OKNO seconds in a row: pack the results,
copy them to the output directory and destroy the instance.
  python tools/straznik_bezczynnosci.py --wyjscie /workspace/wyjscie
Commands are arguments, so tests run the loop on stand-ins (no GPU, no vast.ai).
"""
import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

KORZEN = Path(__file__).resolve().parent.parent


def bezczynny(probki, teraz, okno=600.0, prog=5.0):
    """probki: [(time, gpu %, running evaluations)]. True when the last `okno` seconds are fully covered and idle."""
    if not probki or teraz - probki[0][0] < okno:
        return False
    od = teraz - okno
    ostatnie = [p for p in probki if p[0] >= od]
    return bool(ostatnie) and all(gpu < prog and kolejka == 0 for _, gpu, kolejka in ostatnie)


def liczba(komenda):
    """First number printed by a shell command; a command that fails counts as busy (no destroy on a broken probe)."""
    try:
        wynik = subprocess.run(komenda, shell=True, capture_output=True, text=True, timeout=30)
        return float(wynik.stdout.split()[0])
    except (subprocess.SubprocessError, ValueError, IndexError):
        return float("inf")


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--wyjscie", required=True, help="directory the packed results are copied to")
    p.add_argument("--okno", type=float, default=600.0)
    p.add_argument("--prog", type=float, default=5.0)
    p.add_argument("--interwal", type=float, default=30.0)
    p.add_argument("--gpu", default="nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | head -1")
    # GOTCHA: "[c]" keeps the probe's own `sh -c` command line out of the count
    p.add_argument("--kolejka", default="pgrep -fc '[c]ommon/ewaluuj.py' || true")
    p.add_argument("--pakuj", default=f"bash {KORZEN}/tools/przebieg_centralny.sh pakuj")
    p.add_argument("--archiwum", default="/workspace/wyniki.tgz")
    p.add_argument("--zniszcz", default=f"{sys.executable} -c \"import sys; sys.path.insert(0, '{KORZEN}/slayer-1b/wygaszanie'); "
                                        f"import bezpiecznik; bezpiecznik.zniszcz('idle')\"")
    a = p.parse_args(argv)
    probki = []
    while True:
        teraz = time.time()
        probki.append((teraz, liczba(a.gpu), liczba(a.kolejka)))
        probki = [x for x in probki if x[0] >= teraz - 2 * a.okno]
        if bezczynny(probki, teraz, a.okno, a.prog):
            print(time.strftime("%H:%M:%S"), f"idle for {a.okno:.0f} s: pack, copy, destroy", flush=True)
            subprocess.run(a.pakuj, shell=True)
            Path(a.wyjscie).mkdir(parents=True, exist_ok=True)
            if Path(a.archiwum).exists():
                shutil.copy(a.archiwum, a.wyjscie)
            subprocess.run(a.zniszcz, shell=True)
            return 0
        time.sleep(a.interwal)


if __name__ == "__main__":
    sys.exit(main())
