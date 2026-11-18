"""Warunek 'Pomiar wazny' z PROTOKOL.md: KONTROLA T06 daje 0,7095 po zaokragleniu do 4 miejsc. Wypisuje tak|nie."""
import json
import sys

try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    obs = d["observations"][0]
    print("tak" if obs["state"] == "ok" and round(obs["value"], 4) == 0.7095 else "nie")
except Exception:  # brak pliku po bledzie pary to tez niespelniony warunek
    print("nie")
