"""Tryb „po checkpointach": ta sama lista pytań na kilku wersjach i diff przejść.

  python common/porownaj_checkpointy.py --zadanie T02_space --wyjscie results/arc_diff \
      results/1.00 results/1.01 ... results/1.06

Każdy katalog to wyjście `ewaluuj.py` (podkatalog trace/). Kolejność argumentów = kolejność
treningu; etykieta wersji = nazwa katalogu. Dla każdej reguły (acc, acc_norm, bpb, pmi) zapisuje
przejścia błędne→dobre i dobre→błędne między kolejnymi wersjami (z id pytań i p McNemara).
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import trace_pytan as T  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("katalogi", nargs="+")
    p.add_argument("--zadanie", default="T02_space", help="plik trace bez .jsonl, np. T02_space albo T02_mc")
    p.add_argument("--wyjscie", required=True)
    a = p.parse_args()

    traces = [(Path(k).name, T.wczytaj_trace(Path(k) / "trace" / f"{a.zadanie}.jsonl")) for k in a.katalogi]
    reguly = sorted(set.intersection(*({m for w in ws for m in w["wybor"]} for _, ws in traces)))
    wynik = {"zadanie": a.zadanie,
             "porownania": {r: T.porownaj_checkpointy(traces, r) for r in reguly},
             "rozklady": {et: T.rozklad_wyborow(ws) for et, ws in traces}}
    wyj = Path(a.wyjscie)
    wyj.mkdir(parents=True, exist_ok=True)
    (wyj / f"diff_{a.zadanie}.json").write_text(json.dumps(wynik, ensure_ascii=False, indent=1))

    linie = [f"# {a.zadanie}: przejścia między checkpointami", "",
             "| reguła | z → do | n | trafność z | trafność do | źle→dobrze | dobrze→źle | zmiana wyboru | p McNemara |",
             "|---|---|---|---|---|---|---|---|---|"]
    for r, por in wynik["porownania"].items():
        traf = {w["wersja"]: w["trafnosc"] for w in por["wersje"]}
        n = por["wersje"][0]["n"]
        for prz in por["przejscia"]:
            linie.append(f"| {r} | {prz['z']} → {prz['do']} | {n} | {traf[prz['z']]:.3f} | {traf[prz['do']]:.3f} | "
                         f"{prz['zle_na_dobre']} | {prz['dobre_na_zle']} | {prz['zmiana_wyboru']} | {prz['p_mcnemar']:.3f} |")
    linie += ["", "| wersja | reguła | trafność | pozycje wyborów | najkrótsza | najdłuższa |", "|---|---|---|---|---|---|"]
    for et, rk in wynik["rozklady"].items():
        for r, d in rk["reguly"].items():
            linie.append(f"| {et} | {r} | {d['trafnosc']:.3f} | {d['pozycje']} | {d['najkrotsza']:.2f} | {d['najdluzsza']:.2f} |")
    (wyj / f"diff_{a.zadanie}.md").write_text("\n".join(linie) + "\n")
    print("\n".join(linie))


if __name__ == "__main__":
    main()
