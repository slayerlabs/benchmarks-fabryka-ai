"""Samozniszczenie instancji vast.ai kluczem instancji (CONTAINER_API_KEY), niezależnie od operatora.

python gpu/bezpiecznik.py sprawdz              # GET własnej instancji: czy klucz instancji działa (kod 0 = tak)
python gpu/bezpiecznik.py po 25200             # zniszcz po 25 200 s (7 h) od teraz
python gpu/bezpiecznik.py po_pliku PLIK 1200   # zniszcz 1200 s po pojawieniu się PLIK (koniec skryptu treningu)
Zmienne CONTAINER_ID i CONTAINER_API_KEY daje vast.ai; gdy sesja ssh ich nie ma, czytane z /proc/1/environ.
"""
import os
import sys
import time
import urllib.request
from pathlib import Path

API = "https://console.vast.ai/api/v0/instances/"


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


def wywolaj(metoda):
    cid, klucz = env()
    req = urllib.request.Request(f"{API}{cid}/", method=metoda, headers={"Authorization": f"Bearer {klucz}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()[:300]


def zniszcz(powod):
    for proba in range(20):
        try:
            print(time.strftime("%H:%M:%S"), "destroy:", powod, wywolaj("DELETE"), flush=True)
            return
        except Exception as e:  # noqa: BLE001
            print(time.strftime("%H:%M:%S"), "destroy nieudany, ponawiam:", e, flush=True)
            time.sleep(30)


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
