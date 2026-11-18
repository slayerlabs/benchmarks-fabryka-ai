"""ewaluuj.py fabryki z nadpisaną liczbą przykładów few-shot (np. kontrola HellaSwag 10-shot).

    python ewaluuj_shoty.py <N> <argumenty ewaluuj.py ...>

Jedyna zmiana: `num_fewshot` w konfiguracjach zadań z `zadania.konfiguracje` = N. Prompt, dane, rewizje, seedy
(fewshot 1234), metryki i zapis wyników są te z ewaluuj.py. Wynik dostaje `shoty` w results_rozszerzone.json.
"""
import json
import sys
from pathlib import Path

_TU = Path(__file__).resolve().parent
COMMON = (_TU.parents[1] / "common") if (_TU.parents[1] / "common" / "zadania.py").exists() else (_TU / "fabryka" / "research" / "common")
sys.path.insert(0, str(COMMON))

shoty = int(sys.argv.pop(1))
import zadania as Z  # noqa: E402

_oryginal = Z.konfiguracje


def konfiguracje(task_id, zrodlo="hf"):
    warianty = _oryginal(task_id, zrodlo)
    for _, cfg in warianty:
        cfg["num_fewshot"] = shoty
    return warianty


Z.konfiguracje = konfiguracje
sys.argv[0] = str(COMMON / "ewaluuj.py")
import ewaluuj  # noqa: E402

try:
    ewaluuj.main()
finally:
    wyj = Path(sys.argv[sys.argv.index("--wyjscie") + 1]) / "results_rozszerzone.json"
    if wyj.exists():
        d = json.loads(wyj.read_text(encoding="utf-8"))
        d["shoty"] = shoty
        wyj.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
