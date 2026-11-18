"""SNR of one test on the central-run panel (METODOLOGIA, "Panel SNR").

Panel: models of MODELE in tools/przebieg_centralny.sh except the SlayerLab row, that have per-question samples of the
test in results/central-run/<benchmark>/<model>/probki/. Spread = standard deviation (n - 1) of the panel scores,
SE = mean over the panel of the SE of one score from the per-question values (clustered with --klaster),
SNR = spread / SE. Uncertainty: 95% basic interval from a paired bootstrap over questions (or clusters), the same
draws for every model, and SNR without each single panel model (the smallest of them decides with the interval).
Fewer than 4 panel models: SNR "nieustalony".

Run: python tools/snr_panelu.py results/central-run/arc-challenge --probki T02_space --metryka acc_norm
"""
import argparse
import gzip
import json
import math
import random
import re
import statistics
import sys
from pathlib import Path

MIN_PANEL = 4
POWTORZENIA = 2000
ZIARNO = 20261107
SKRYPT = Path(__file__).resolve().parent / "przebieg_centralny.sh"


def panel_z_modele(skrypt=SKRYPT):
    """Labels of MODELE without the SlayerLab row(s), in script order."""
    blok = skrypt.read_text(encoding="utf-8").split("\nMODELE=(", 1)[1].split("\n)", 1)[0]
    wiersze = re.findall(r'^\s*"([^"|]+)\|([^"|]+)\|', blok, re.MULTILINE)
    return [l for l, repo in wiersze if not repo.startswith("SlayerLab/")]


def wczytaj(katalog, model, probki, metryka, klaster=None):
    """{doc_id: (value, cluster)} of one model, or None when the samples file is missing."""
    f = Path(katalog) / model / "probki" / f"{probki}.jsonl.gz"
    if not f.exists():
        return None
    out = {}
    with gzip.open(f, "rt", encoding="utf-8") as fh:
        for linia in fh:
            r = json.loads(linia)
            out[r["doc_id"]] = (float(r[metryka]), r["doc"][klaster] if klaster else r["doc_id"])
    return out


def _wynik_i_se(sumy, liczby):
    """Score and SE from per-cluster sums and counts: mean = ΣS/N, SE = √(k/(k−1) · Σ (S_c − n_c·mean)²) / N
    (statystyka.se_k; with clusters of one question it is stdev/√n)."""
    N, k = sum(liczby), len(liczby)
    m = sum(sumy) / N
    return m, math.sqrt(sum((s - n * m) ** 2 for s, n in zip(sumy, liczby)) * k / (k - 1)) / N


def snr(klastry_modeli, wybor=None):
    """klastry_modeli: {model: [(sum, count) per cluster]}, clusters in the same order for every model.
    wybor: indices of the clusters to use (bootstrap draw), default all. Returns (spread, SE, SNR)."""
    wyniki, se = [], []
    for kl in klastry_modeli.values():
        uzyte = kl if wybor is None else [kl[i] for i in wybor]
        m, s = _wynik_i_se([a for a, _ in uzyte], [b for _, b in uzyte])
        wyniki.append(m)
        se.append(s)
    rozrzut, sr_se = statistics.stdev(wyniki), statistics.fmean(se)
    return rozrzut, sr_se, (rozrzut / sr_se if sr_se else math.inf)


def kwantyle(proby, alfa=0.05):
    """[q_{α/2}, q_{1−α/2}] of sorted bootstrap SNRs."""
    n = len(proby)
    return [proby[int(alfa / 2 * n)], proby[int(math.ceil((1 - alfa / 2) * n)) - 1]]


def przedzial_basic(theta, proby, alfa=0.05):
    """Basic bootstrap interval [2θ̂ − q_{1−α/2}, 2θ̂ − q_{α/2}]. Resampling questions adds their noise to the spread,
    so bootstrap SNRs sit above θ̂ and the percentile interval would be shifted up; the basic one reflects it back."""
    q_lo, q_hi = kwantyle(proby, alfa)
    return [2 * theta - q_hi, 2 * theta - q_lo]


def policz(dane, powtorzenia=POWTORZENIA, ziarno=ZIARNO):
    """dane: {model: {doc_id: (value, cluster)}} of the panel. Returns the result dict of the CLI."""
    modele = sorted(dane)
    wynik = {"panel": modele, "min_panel": MIN_PANEL}
    if len(modele) < MIN_PANEL:
        return {**wynik, "status": "nieustalony", "powod": f"panel {len(modele)} < {MIN_PANEL}"}
    pytania = set(dane[modele[0]])
    if any(set(dane[m]) != pytania for m in modele):
        raise ValueError("models of the panel scored different questions")
    pytania = sorted(pytania)
    klaster = {d: dane[modele[0]][d][1] for d in pytania}
    nazwy = sorted(set(klaster.values()), key=str)
    klastry_modeli = {}
    for m in modele:
        sumy, liczby = dict.fromkeys(nazwy, 0.0), dict.fromkeys(nazwy, 0)
        for d in pytania:
            sumy[klaster[d]] += dane[m][d][0]
            liczby[klaster[d]] += 1
        klastry_modeli[m] = [(sumy[c], liczby[c]) for c in nazwy]
    rozrzut, se, s = snr(klastry_modeli)
    rng = random.Random(ziarno)
    k = len(nazwy)
    proby = sorted(snr(klastry_modeli, [rng.randrange(k) for _ in range(k)])[2] for _ in range(powtorzenia))
    bez = {m: snr({x: v for x, v in klastry_modeli.items() if x != m})[2] for m in modele}
    return {**wynik, "status": "ustalony", "n": len(pytania), "klastry": k,
            "wyniki": {m: _wynik_i_se([a for a, _ in klastry_modeli[m]], [b for _, b in klastry_modeli[m]])[0]
                       for m in modele},
            "rozrzut": rozrzut, "se": se, "snr": s,
            "przedzial95": przedzial_basic(s, proby), "kwantyle_bootstrap": kwantyle(proby),
            "powtorzenia": powtorzenia, "ziarno": ziarno,
            "bez_jednego": bez, "snr_min_bez_jednego": min(bez.values())}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("katalog", help="results/central-run/<benchmark>")
    p.add_argument("--probki", required=True, help="samples file without .jsonl.gz, e.g. T02_space")
    p.add_argument("--metryka", required=True, help="per-question field of the decision metric, e.g. acc_norm")
    p.add_argument("--klaster", help="doc field of the cluster when the test type has a clustered SE, e.g. UID")
    p.add_argument("--modele", help="comma-separated panel instead of MODELE (only for checks)")
    p.add_argument("--skrypt", type=Path, default=SKRYPT, help="central-run script with MODELE")
    p.add_argument("--powtorzenia", type=int, default=POWTORZENIA)
    p.add_argument("--ziarno", type=int, default=ZIARNO)
    a = p.parse_args(argv)
    panel = a.modele.split(",") if a.modele else panel_z_modele(a.skrypt)
    dane = {m: w for m in panel if (w := wczytaj(a.katalog, m, a.probki, a.metryka, a.klaster)) is not None}
    wynik = policz(dane, a.powtorzenia, a.ziarno)
    wynik["bez_probek"] = [m for m in panel if m not in dane]
    print(json.dumps(wynik, ensure_ascii=False, indent=1))
    return 0 if wynik["status"] == "ustalony" else 3


if __name__ == "__main__":
    sys.exit(main())
