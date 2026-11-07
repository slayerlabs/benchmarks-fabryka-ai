"""Zbiera wyniki T44 z przebiegu centralnego w jeden plik liczb: `results/pubmedqa.json`.

Użycie:
    python benchmarks/pubmedqa/zbierz_wyniki.py [katalog przebiegu] [plik wyjściowy]

Katalog przebiegu to `results/central-run/pubmedqa/` (domyślny): po jednym podkatalogu na model, każdy z
`results_rozszerzone.json` i `probki/T44_space.jsonl` albo `.jsonl.gz`. Domyślny plik wyjściowy to
`results/pubmedqa.json` w katalogu benchmarku.

Skrypt nie liczy metryk od nowa: wartości, SE i CI95 przepisuje z `ewaluuj.py` (`dodatkowe.space`), a bazy
z pola `bazy` tego samego pliku (`klasy_stale=True` w `common/zadania.py`, więc `ewaluuj.py` je wypełnia).
Z próbek liczy tylko to, czego w plikach przebiegu nie ma: rozkład celu, rozkład predykcji i porównanie z b
parowane po pytaniach (SE A z odchylenia różnic, ddof = 1, jak `ewaluuj.py` liczy SE wyniku).
"""
import gzip
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

KORZEN = Path(__file__).resolve().parent
PRZEBIEG = KORZEN.parent.parent / "results" / "central-run" / "pubmedqa"
METRYKI = ("acc", "acc_norm", "acc_pmi", "bpb_poprawnej")
OPCJE = ("yes", "no", "maybe")  # kolejność `doc_to_choice` wpisu T44 w common/zadania.py
ZBIOR = {
    "repo": "bigbio/pubmed_qa",
    "rewizja": "15578e80ef02c2c9636d33fdd7eb6b05b987ba60",
    "nazwa_hf": "pubmed_qa_labeled_fold0_source",
    "rewizja_parquet": "13a7d15476092370cbabb6475390e7e69b74d2f2",
    "split": "test",
    "n_population": 500,
    "test": "T44",
}


def probki(katalog):
    """[(acc per pytanie, cel, predykcja, [log P opcji])] z probki/T44_space.jsonl(.gz)."""
    plik = katalog / "probki" / "T44_space.jsonl"
    linie = (gzip.decompress(plik.with_suffix(".jsonl.gz").read_bytes()).decode("utf-8")
             if not plik.exists() else plik.read_text(encoding="utf-8")).splitlines()
    wiersze = []
    for linia in linie:
        if not linia.strip():
            continue
        d = json.loads(linia)
        # 6 argumentów: 3 opcje z kontekstem, potem 3 bez kontekstu (dla PMI); liczy się pierwsza trójka
        logp = [r[0] for r in d["filtered_resps"]][:len(OPCJE)]
        wiersze.append((float(d["acc"]), d["target"], OPCJE[logp.index(max(logp))], logp))
    return wiersze


def wobec_b(wiersze, klasa_b):
    """Porównanie z bazą większościową, parowane po pytaniach (METODOLOGIA, „Wspólny rdzeń”, punkt 4)."""
    roznice = [acc - (1.0 if cel == klasa_b else 0.0) for acc, cel, _, _ in wiersze]
    se = st.stdev(roznice) / len(roznice) ** 0.5
    return {"roznica": st.mean(roznice), "se_parowane": se, "z": st.mean(roznice) / se}


def logp_opcji(wiersze):
    """Średnie log P każdej kontynuacji i liczba pytań, w których ` maybe` ma najniższe log P.

    `acc` sumuje log-prawdopodobieństwo kontynuacji bez normalizacji długości, więc te średnie mówią,
    czy brak predykcji `maybe` jest własnością metryki i zestawu opcji, czy śladem błędu w prompcie.
    """
    srednie = {o: st.mean(w[3][i] for w in wiersze) for i, o in enumerate(OPCJE)}
    najnizsze = Counter(OPCJE[w[3].index(min(w[3]))] for w in wiersze)
    return {"srednie_log_p": srednie, "najnizsze_log_p": {k: najnizsze.get(k, 0) for k in OPCJE}}


def wczytaj(katalog):
    d = json.loads((katalog / "results_rozszerzone.json").read_text(encoding="utf-8"))
    o = d["observations"][0]
    sp = o["dodatkowe"]["space"]
    wiersze = probki(katalog)
    cele, predykcje = Counter(w[1] for w in wiersze), Counter(w[2] for w in wiersze)
    klasa_b = cele.most_common(1)[0][0]
    wyjscie = {"model": o["model_id"], "n": o["n_scored"], "n_population": o["n_population"]}
    for m in METRYKI:
        wyjscie[m] = {"value": sp[m]["value"], "se": sp[m]["se"], "ci95": sp[m]["ci95"]}
    wyjscie["bazy"] = {
        "losowa": sp["bazy"]["chance_value"],
        "stala_odpowiedz": sp["bazy"]["majority_value"],
        "klasa_stalej_odpowiedzi": klasa_b,
        "rozklad_celu": {k: cele.get(k, 0) for k in OPCJE},
    }
    wyjscie["udzial_najczestszej_predykcji"] = sp["udzial_najczestszej_predykcji"]
    wyjscie["najczestsza_predykcja"] = predykcje.most_common(1)[0][0]
    wyjscie["rozklad_predykcji"] = {k: predykcje.get(k, 0) for k in OPCJE}
    wyjscie["acc_wobec_b"] = wobec_b(wiersze, klasa_b)
    wyjscie["opcje"] = logp_opcji(wiersze)
    wyjscie["source_id_digest"] = o["source_id_digest"]
    wyjscie["results_sha256"] = o["results_sha256"]
    return wyjscie


def zbuduj(katalog_przebiegu=PRZEBIEG):
    """Cały plik liczb: zbiór i pełny split każdego modelu przebiegu centralnego."""
    katalogi = sorted(k for k in Path(katalog_przebiegu).iterdir()
                      if (k / "results_rozszerzone.json").is_file())
    if not katalogi:
        raise SystemExit(f"brak wyników w {katalog_przebiegu}")
    return {"zbior": dict(ZBIOR), "pelny_split": {k.name: wczytaj(k) for k in katalogi}}


def main():
    if len(sys.argv) > 3:
        raise SystemExit(__doc__)
    wynik = zbuduj(sys.argv[1] if len(sys.argv) > 1 else PRZEBIEG)
    cel = Path(sys.argv[2]) if len(sys.argv) == 3 else KORZEN / "results" / "pubmedqa.json"
    cel.parent.mkdir(parents=True, exist_ok=True)
    cel.write_text(json.dumps(wynik, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"zapisano {cel}")
    for nazwa, d in wynik["pelny_split"].items():
        print(f"  {nazwa}: acc {d['acc']['value']:.4f} ±{d['acc']['se']:.4f} n={d['n']} "
              f"wobec b {100 * d['acc_wobec_b']['roznica']:+.2f} pkt z {d['acc_wobec_b']['z']:+.2f}")


if __name__ == "__main__":
    main()
