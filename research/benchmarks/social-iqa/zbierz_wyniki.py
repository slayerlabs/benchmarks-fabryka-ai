"""Zbiera przebiegi T46 (panel Space 200 i pełny split) w jeden plik liczb: `results/social_iqa.json`.

Użycie:
    python benchmarks/social-iqa/zbierz_wyniki.py <katalog panelu> <katalog pełnego splitu> [plik wyjściowy]

Katalogi to wyjścia `common/ewaluuj.py` (muszą zawierać `results_rozszerzone.json` i `probki/T46_space.jsonl`).
Domyślny plik wyjściowy to `results/social_iqa.json` w katalogu benchmarku.
Skrypt nie liczy metryk od nowa: przepisuje wartości, SE i CI95 z `ewaluuj.py`, a bazy liczy z goldów
(`label` zbioru), bo `ewaluuj.py` zostawia je puste (`klasy_stale=False` w `common/zadania.py`).
"""
import json
import sys
from collections import Counter
from pathlib import Path

KORZEN = Path(__file__).resolve().parent
METRYKI = ("acc", "acc_norm", "acc_pmi", "bpb_poprawnej")
ZBIOR = {
    "repo": "allenai/social_i_qa",
    "rewizja": "8835ceb9141d7896d9d968634a9b21ae440e3ec5",
    "rewizja_parquet": "refs/convert/parquet",
    "split": "validation",
    "n_population": 1954,
    "test": "T46",
}
MODEL = {
    "nazwa": "slayer-1.06",
    "repo": "SlayerLab/Slayer1B-1.06",
    "rewizja": "ef81be58742544ad32e1afab38db011fec209609",
}


def wczytaj(katalog):
    d = json.loads((katalog / "results_rozszerzone.json").read_text(encoding="utf-8"))
    o = d["observations"][0]
    sp = o["dodatkowe"]["space"]
    linie = (katalog / "probki" / "T46_space.jsonl").read_text(encoding="utf-8").splitlines()
    gold = [int(json.loads(l)["target"]) for l in linie if l.strip()]
    wyjscie = {"n": o["n_scored"], "n_population": o["n_population"]}
    for m in METRYKI:
        wyjscie[m] = {"value": sp[m]["value"], "se": sp[m]["se"], "ci95": sp[m]["ci95"]}
    wyjscie["bazy"] = {
        "losowa": sp["bazy"]["chance_value"],
        # lm-eval punktuje indeks, więc stała odpowiedź to udział najczęstszego indeksu poprawnego
        "stala_odpowiedz": max(Counter(gold).values()) / len(gold),
        "rozklad_gold": dict(sorted(Counter(gold).items())),
    }
    wyjscie["udzial_najczestszej_predykcji"] = sp["udzial_najczestszej_predykcji"]
    wyjscie["source_id_digest"] = o["source_id_digest"]
    wyjscie["results_sha256"] = o["results_sha256"]
    return wyjscie


def zbuduj(katalog_panelu, katalog_pelny):
    """Cały plik liczb: zbiór, model, panel Space i pełny split."""
    return {
        "zbior": dict(ZBIOR),
        "model": dict(MODEL),
        "panel_space": wczytaj(Path(katalog_panelu)),
        "pelny_split": wczytaj(Path(katalog_pelny)),
    }


def main():
    if len(sys.argv) not in (3, 4):
        raise SystemExit(__doc__)
    wynik = zbuduj(sys.argv[1], sys.argv[2])
    cel = Path(sys.argv[3]) if len(sys.argv) == 4 else KORZEN / "results" / "social_iqa.json"
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_text(json.dumps(wynik, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"zapisano {cel}")
    for nazwa in ("panel_space", "pelny_split"):
        d = wynik[nazwa]
        print(f"  {nazwa}: acc {d['acc']['value']:.4f} ±{d['acc']['se']:.4f} n={d['n']} "
              f"ci95 {d['acc']['ci95']}")


if __name__ == "__main__":
    main()
