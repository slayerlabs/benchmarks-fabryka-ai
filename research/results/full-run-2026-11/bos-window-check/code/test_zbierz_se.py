"""Zgodnosc odczytu `obserwacja` z manifestem przebiegu: value i se dla Pythii i Slayera na 7 zadaniach."""
import importlib.util
import json
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("zbierz", Path(__file__).parent / "zbierz.py")
Z = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Z)

fr = Path(sys.argv[1])
zle = 0
for l in open(fr / "manifest.jsonl", encoding="utf-8"):
    r = json.loads(l)
    if r["model"] in ("pythia-1b-v0", "slayer1b-1.07-hf") and r["zadanie"] in Z.KATALOG and r["stan"] == "ok":
        o = Z.obserwacja(fr / Z.KATALOG[r["zadanie"]] / r["model"])
        ok = o and abs(o["value"] - r["wartosc"]) < 1e-12 and abs(o["se"] - r["se"]) < 1e-12 and o["n"] == r["n"]
        print(r["model"], r["zadanie"], "OK" if ok else f"ROZNE {o and (o['value'], o['se'], o['n'])} vs {r['wartosc'], r['se'], r['n']}")
        zle += 0 if ok else 1
sys.exit(1 if zle else 0)
