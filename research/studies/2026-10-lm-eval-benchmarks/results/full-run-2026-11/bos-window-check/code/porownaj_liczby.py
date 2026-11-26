"""Wypisuje rozjazd dwoch LICZBY.json: python porownaj_liczby.py <stary> <nowy>. Kod 0, gdy zadna wspolna wartosc sie nie zmienila."""
import json
import sys


def plaskie(x, p=""):
    if isinstance(x, dict):
        d = {}
        for k, v in x.items():
            d.update(plaskie(v, f"{p}/{k}"))
        return d
    if isinstance(x, list):
        return {f"{p}[{i}]": v for i, v in enumerate(x)}
    return {p: x}


a, b = (plaskie(json.load(open(f, encoding="utf-8"))) for f in sys.argv[1:3])
zm = sorted(k for k in set(a) & set(b) if a[k] != b[k])
print(f"wspolne klucze {len(set(a) & set(b))}, zmienione {len(zm)}, usuniete {len(set(a) - set(b))}, dodane {len(set(b) - set(a))}")
for k in zm:
    print("ZMIENIONE", k, a[k], "->", b[k])
for k in sorted(set(a) - set(b)):
    print("USUNIETE", k, a[k])
for k in sorted(set(b) - set(a)):
    print("DODANE", k)
sys.exit(1 if zm else 0)
