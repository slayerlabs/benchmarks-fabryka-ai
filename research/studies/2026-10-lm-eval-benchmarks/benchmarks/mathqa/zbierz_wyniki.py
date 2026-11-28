"""Zbiera pomiar T19 w jeden plik liczb: `results/mathqa.json`.

Użycie (w `research/`):
    python benchmarks/mathqa/zbierz_wyniki.py [katalog modelu] [plik wyjściowy]

Katalog modelu to `benchmarks/mathqa/results/slayer-1.06/` (domyślny) z podkatalogami `panel200` i `pelna`,
każdy z `results_rozszerzone.json` i `probki/T19_space.jsonl` albo `.jsonl.gz`.

Wartości, SE i CI95 przepisuje z `ewaluuj.py` (`dodatkowe.space`). Z próbek liczy to, czego w plikach przebiegu
nie ma: rozkład celu i predykcji, bazy (wpis T19 ma `klasy_stale=False`, więc `ewaluuj.py` zostawia je puste),
porównania z bazami parowane po pytaniach, wpływ długości opcji na `acc_norm` i zgodność panelu z pełnym splitem.
"""
import gzip
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

KORZEN = Path(__file__).resolve().parent
MODEL = KORZEN / "results" / "slayer-1.06"
PRZEBIEGI = (("slayer_panel200", "panel200"), ("slayer_pelny", "pelna"))
METRYKI = ("acc", "acc_norm", "acc_pmi", "bpb_poprawnej")
LITERY = ("a", "b", "c", "d", "e")
ZBIOR = {
    "repo": "allenai/math_qa",
    "rewizja": "c4f1cc784c04c4957b50c97858f23893b633eea6",
    "nazwa_hf": "default",
    "rewizja_parquet": "fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6",
    "split": "test",
    "n_population": 2985,
    "test": "T19",
}


def werdykt(z):
    """Progi rdzenia, punkt 4."""
    a = abs(z)
    return "pewne" if a >= 3 else "prawdopodobne" if a >= 2 else "szum"


def probki(katalog):
    plik = katalog / "probki" / "T19_space.jsonl"
    tekst = (plik.read_text(encoding="utf-8") if plik.exists()
             else gzip.decompress(plik.with_suffix(".jsonl.gz").read_bytes()).decode("utf-8"))
    return [json.loads(w) for w in tekst.splitlines() if w.strip()]


def porownanie(wartosci, baza):
    """Różnica wobec bazy, parowana po pytaniach (METODOLOGIA, „Wspólny rdzeń”, punkt 4)."""
    roznice = [w - b for w, b in zip(wartosci, baza)]
    se = st.stdev(roznice) / len(roznice) ** 0.5
    z = st.mean(roznice) / se
    return {"roznica": st.mean(roznice), "se": se, "z": z, "werdykt": werdykt(z)}


def dlugosci(wiersze):
    """Czy `acc_norm` premiuje opcje dłuższe: `acc` dzieli sumę log P przez liczbę znaków kontynuacji, więc
    przy ujemnych log P krótsza opcja dostaje wartość bardziej ujemną. Liczymy to tylko na pytaniach z jedną
    najkrótszą opcją, żeby remisy nie zaciemniały obrazu."""
    wszystkie, wybrane, jedna, wybr_najkr, gold_najkr = [], [], 0, 0, 0
    for r in wiersze:
        opcje = [a[1].strip() for a in r["arguments"][:len(LITERY)]]
        logp = [x[0] for x in r["filtered_resps"][:len(LITERY)]]
        dl = [len(o) for o in opcje]
        i = max(range(len(opcje)), key=lambda j: logp[j] / dl[j])
        wszystkie.extend(dl)
        wybrane.append(dl[i])
        if dl.count(min(dl)) == 1:
            jedna += 1
            wybr_najkr += dl[i] == min(dl)
            gold_najkr += dl[r["target"]] == min(dl)
    return {"srednia_dlugosc_opcji": st.mean(wszystkie), "srednia_dlugosc_wybranej": st.mean(wybrane),
            "pytan_z_jedna_najkrotsza": jedna, "wybrana_najkrotsza": wybr_najkr,
            "udzial_wybranej_najkrotszej": wybr_najkr / jedna, "gold_najkrotsza": gold_najkr,
            "udzial_gold_najkrotszej": gold_najkr / jedna}


def wczytaj(katalog):
    sp = json.loads((katalog / "results_rozszerzone.json").read_text(encoding="utf-8"))["observations"][0]
    space = sp["dodatkowe"]["space"]
    wiersze = probki(katalog)
    n = len(wiersze)
    accn = [r["acc_norm"] for r in wiersze]
    cele = Counter(r["doc"]["correct"] for r in wiersze)
    klasa_b, ile_b = cele.most_common(1)[0]
    predykcje = Counter()
    for r in wiersze:
        opcje = [a[1].strip() for a in r["arguments"][:len(LITERY)]]
        logp = [x[0] for x in r["filtered_resps"][:len(LITERY)]]
        predykcje[LITERY[max(range(len(opcje)), key=lambda j: logp[j] / len(opcje[j]))]] += 1
    wyjscie = {m: {"value": space[m]["value"], "se": space[m]["se"], "ci95": space[m]["ci95"]} for m in METRYKI}
    wyjscie["n"] = n
    wyjscie["n_population"] = sp["n_population"]
    wyjscie["bazy"] = {
        "losowa": 1 / len(LITERY),
        "wiekszosciowa_tego_przebiegu": ile_b / n,
        "klasa_wiekszosciowa": klasa_b,
        "rozklad_celu": {k: cele.get(k, 0) for k in LITERY},
    }
    wyjscie["rozklad_predykcji"] = {k: predykcje.get(k, 0) for k in LITERY}
    wyjscie["udzial_najczestszej_predykcji"] = predykcje.most_common(1)[0][1] / n
    wyjscie["acc_norm_wobec_losowej"] = porownanie(accn, [1 / len(LITERY)] * n)
    wyjscie["acc_norm_wobec_wiekszosciowej"] = porownanie(
        accn, [1.0 if r["doc"]["correct"] == klasa_b else 0.0 for r in wiersze])
    wyjscie["dlugosc_opcji"] = dlugosci(wiersze)
    wyjscie["source_id_digest"] = sp["source_id_digest"]
    wyjscie["results_sha256"] = sp["results_sha256"]
    return wyjscie, wiersze


def zgodnosc(panel, pelny):
    """Panel ma być podzbiorem pełnego przebiegu: te same logliki na tych samych pytaniach."""
    p = {r["doc_id"]: r for r in panel}
    f = {r["doc_id"]: r for r in pelny}
    wspolne = sorted(set(p) & set(f))
    maks = max((abs(a[0] - b[0]) for i in wspolne
                for a, b in zip(p[i]["filtered_resps"], f[i]["filtered_resps"])), default=0.0)
    return {"panel_jest_podzbiorem": set(p) <= set(f), "wspolnych_pytan": len(wspolne),
            "max_roznica_loglik": maks,
            "rozne_acc_norm": sum(1 for i in wspolne if p[i]["acc_norm"] != f[i]["acc_norm"]),
            "acc_norm_panelu_w_przebiegu_pelnym": st.mean(f[i]["acc_norm"] for i in wspolne)}


def zbuduj(katalog_modelu=MODEL):
    katalog_modelu = Path(katalog_modelu)
    wynik, wiersze = {"zbior": dict(ZBIOR)}, {}
    for klucz, podkatalog in PRZEBIEGI:
        wynik[klucz], wiersze[klucz] = wczytaj(katalog_modelu / podkatalog)
    wynik["zgodnosc_panel_pelny"] = zgodnosc(wiersze["slayer_panel200"], wiersze["slayer_pelny"])
    return wynik


def main():
    wynik = zbuduj(sys.argv[1] if len(sys.argv) > 1 else MODEL)
    cel = Path(sys.argv[2]) if len(sys.argv) == 3 else KORZEN / "results" / "mathqa.json"
    cel.write_text(json.dumps(wynik, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"zapisano {cel}")
    for klucz, _ in PRZEBIEGI:
        d = wynik[klucz]
        print(f"  {klucz}: acc_norm {d['acc_norm']['value']:.4f} ±{d['acc_norm']['se']:.4f} n={d['n']}"
              f" | wobec losowej z {d['acc_norm_wobec_losowej']['z']:+.2f}"
              f" | wobec większościowej z {d['acc_norm_wobec_wiekszosciowej']['z']:+.2f}")


if __name__ == "__main__":
    main()
