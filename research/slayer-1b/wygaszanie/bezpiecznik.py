"""Samozniszczenie instancji vast.ai kluczem instancji (CONTAINER_API_KEY), niezależnie od operatora.

python gpu/bezpiecznik.py sprawdz              # GET własnej instancji: czy klucz instancji działa (kod 0 = tak)
python gpu/bezpiecznik.py po 25200 [KOMENDA]   # zniszcz po 25 200 s (7 h) od teraz; KOMENDA (np. pakowanie) przed
python gpu/bezpiecznik.py po_pliku PLIK 1200   # zniszcz 1200 s po pojawieniu się PLIK (koniec skryptu treningu)
Zmienne CONTAINER_ID i CONTAINER_API_KEY daje vast.ai; gdy sesja ssh ich nie ma, czytane z /proc/1/environ.
`zatrzymaj` (strażnik bezczynności przebiegu centralnego): PUT {"state": "stopped"} na ten sam adres, jak
`stop_instance` w pakiecie vastai 1.11.0 (vastai/api/instances.py); dysk zostaje, wznowienie `vastai start instance ID`.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# BEZPIECZNIK_API: a stand-in server in tests only
API = os.environ.get("BEZPIECZNIK_API", "https://console.vast.ai/api/v0/instances/")


def env():
    e = dict(os.environ)
    if "CONTAINER_API_KEY" not in e:
        try:
            for kv in Path("/proc/1/environ").read_bytes().split(b"\0"):
                if b"=" in kv:
                    k, v = kv.decode(errors="replace").split("=", 1)
                    e.setdefault(k, v)
        except OSError:
            pass
    return e["CONTAINER_ID"], e["CONTAINER_API_KEY"]


def wywolaj(metoda, dane=None):
    cid, klucz = env()
    naglowki = {"Authorization": f"Bearer {klucz}"}
    if dane is not None:
        naglowki["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{API}{cid}/", method=metoda, headers=naglowki,
                                 data=None if dane is None else json.dumps(dane).encode())
    with urllib.request.urlopen(req, timeout=60) as r:
        status, tresc = r.status, r.read()
    try:
        odp = json.loads(tresc)
    except ValueError:
        odp = None
    # vast.ai answers some refusals with 2xx and {"success": false, "msg": ...}
    if isinstance(odp, dict) and odp.get("success") is False:
        raise RuntimeError(f"{metoda} {status}: success false: {tresc[:300]!r}")
    return status, tresc[:300]


def _ponawiaj(nazwa, powod, metoda, dane=None, pauza=float(os.environ.get("BEZPIECZNIK_PAUZA", 30))):
    for proba in range(20):
        try:
            print(time.strftime("%H:%M:%S"), f"{nazwa}:", powod, wywolaj(metoda, dane), flush=True)
            return True
        except Exception as e:  # noqa: BLE001
            print(time.strftime("%H:%M:%S"), f"{nazwa} nieudany, ponawiam:", e, flush=True)
            time.sleep(pauza)
    print(time.strftime("%H:%M:%S"), f"{nazwa}: wszystkie proby nieudane", flush=True)
    return False


def zniszcz(powod):
    """DELETE: instance and its disk are gone."""
    return _ponawiaj("destroy", powod, "DELETE")


def zatrzymaj(powod):
    """Stop: the GPU is released, the disk (results) stays and is billed until a manual destroy."""
    return _ponawiaj("stop", powod, "PUT", {"state": "stopped"})


def main():
    tryb = sys.argv[1]
    if tryb == "sprawdz":
        status, tresc = wywolaj("GET")
        ok = status == 200 and b"instances" in tresc
        print("klucz instancji:", status, "OK" if ok else tresc)
        sys.exit(0 if ok else 1)
    if tryb == "po":
        s = int(sys.argv[2])
        print(time.strftime("%H:%M:%S"), f"uzbrojony: destroy za {s} s", flush=True)
        time.sleep(s)
        if len(sys.argv) > 3:  # e.g. pack the results first (central run)
            subprocess.run(sys.argv[3], shell=True)
        zniszcz(f"limit {s} s")
    elif tryb == "po_pliku":
        plik, s = Path(sys.argv[2]), int(sys.argv[3])
        print(time.strftime("%H:%M:%S"), f"uzbrojony: destroy {s} s po {plik}", flush=True)
        while not plik.exists():
            time.sleep(30)
        time.sleep(s)
        zniszcz(f"{plik} + {s} s")


if __name__ == "__main__":
    main()
