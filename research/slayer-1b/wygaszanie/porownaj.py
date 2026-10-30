"""Zestawienie: baza 1.06 / A (wygaszenie) / B (stały LR), werdykt wg PROGI.md.

python wygaszanie/porownaj.py --wyniki wyniki   (katalogi wyniki/{1.06,A,B}, pliki wyniki/heldout_*.json)

Na pytanie: acc (max loglik), acc_norm (loglik/znak), pmi (loglik - bezwarunkowy), bpb_wybor (loglik/bajt),
bpb_poprawnej (−loglik poprawnej / (ln2·bajty), niżej = lepiej). SE = sd/√n; Δ i SE(Δ) z parowanego
bootstrapu po pytaniach (10 000, seed 20261028). Bazy: losowa = średnie 1/k, większościowa = udział
najczęstszej poprawnej pozycji. Dla formatu literowego rozkład wybranych liter.
"""

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "slayer_eval"))
from hipoteza_formatu import LITERY, wybory  # noqa: E402

LN2 = math.log(2)
B = 10000
SEED = 20261028
MODELE = ["1.06", "A", "B"]


def wczytaj(plik):
    return {json.loads(l)["id"]: json.loads(l) for l in plik.read_text().splitlines() if l.strip()}


def wektory(wiersze, ids):
    out = {}
    for i in ids:
        w = wiersze[i]
        wyb = wybory(w)
        for m, v in wyb.items():
            out.setdefault(m, []).append(float(v == w["gold"]))
        g = w["gold"]
        out.setdefault("bpb_poprawnej", []).append(-w["ll"][g] / (LN2 * max(w["bajty"][g], 1)))
    return {k: np.array(v) for k, v in out.items()}


def boot_delta(x, y, rng_idx):
    d = x - y
    bs = d[rng_idx].mean(1)
    return float(d.mean()), float(bs.std(ddof=1))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--wyniki", required=True)
    a = p.parse_args()
    W = Path(a.wyniki)
    rng = np.random.default_rng(SEED)
    raport = {"zadania": {}, "heldout": None, "wikitext": {}}
    md = ["| zadanie | metryka | n | 1.06 (SE) | A (SE) | B (SE) | Δ A−B (SE) | |Δ|>2SE | Δ A−1.06 (SE) |",
          "|---|---|---|---|---|---|---|---|---|"]
    zadania = sorted({f.stem for f in (W / "1.06").glob("*.jsonl")})
    for z in zadania:
        dane = {m: wczytaj(W / m / f"{z}.jsonl") for m in MODELE if (W / m / f"{z}.jsonl").exists()}
        if len(dane) < 3:
            continue
        ids = sorted(set.intersection(*(set(d) for d in dane.values())))
        n = len(ids)
        idx = rng.integers(0, n, size=(B, n))
        wek = {m: wektory(dane[m], ids) for m in MODELE}
        ref = dane["1.06"]
        k_sr = float(np.mean([ref[i]["k"] for i in ids]))
        losowa = float(np.mean([1 / ref[i]["k"] for i in ids]))
        golds = Counter(ref[i]["gold"] for i in ids)
        wiekszosc = golds.most_common(1)[0][1] / n
        wz = {"n": n, "k_srednie": k_sr, "losowa": losowa, "wiekszosciowa": wiekszosc,
              "rozklad_poprawnych": {LITERY[g]: c / n for g, c in sorted(golds.items())}, "metryki": {}}
        for met in wek["1.06"]:
            r = {}
            for m in MODELE:
                v = wek[m][met]
                r[m] = {"wartosc": float(v.mean()), "se": float(v.std(ddof=1) / math.sqrt(n))}
            r["delta_A_B"], r["se_delta_A_B"] = boot_delta(wek["A"][met], wek["B"][met], idx)
            r["delta_A_baza"], r["se_delta_A_baza"] = boot_delta(wek["A"][met], wek["1.06"][met], idx)
            r["delta_B_baza"], r["se_delta_B_baza"] = boot_delta(wek["B"][met], wek["1.06"][met], idx)
            r["istotne_A_B"] = abs(r["delta_A_B"]) > 2 * r["se_delta_A_B"]
            wz["metryki"][met] = r
            f = lambda m: f"{r[m]['wartosc']:.4f} ({r[m]['se']:.4f})"  # noqa: E731
            md.append(f"| {z} | {met} | {n} | {f('1.06')} | {f('A')} | {f('B')} | {r['delta_A_B']:+.4f} "
                      f"({r['se_delta_A_B']:.4f}) | {'TAK' if r['istotne_A_B'] else 'nie'} | "
                      f"{r['delta_A_baza']:+.4f} ({r['se_delta_A_baza']:.4f}) |")
        if z.endswith("_mc"):
            wz["rozklad_wyborow_acc"] = {m: {LITERY[c]: v / n for c, v in sorted(Counter(
                wybory(dane[m][i])["acc"] for i in ids).items())} for m in MODELE}
        raport["zadania"][z] = wz
    for m in MODELE:
        f = W / m / "wikitext.json"
        if f.exists():
            raport["wikitext"][m] = json.loads(f.read_text())
    if raport["wikitext"]:
        md += ["", "| WikiText-2 | " + " | ".join(raport["wikitext"]) + " |",
               "|---|" + "---|" * len(raport["wikitext"])]
        for k in ("byte_perplexity", "bits_per_byte", "word_perplexity"):
            md.append(f"| {k} | " + " | ".join(f"{v[k]:.4f}" for v in raport["wikitext"].values()) + " |")

    # ---- loss na odłożonych danych i werdykt
    h = {f.stem.replace("heldout_", ""): json.loads(f.read_text()) for f in W.glob("heldout_*.json")}
    if {"A", "B", "1.06"} <= set(h):
        st = {m: np.array([o["loss"] for o in h[m]["okna"]]) for m in h}
        nwin = len(st["A"])
        idx = rng.integers(0, nwin, size=(B, nwin))
        d, se = boot_delta(st["A"], st["B"], idx)
        z1 = abs(float(st["1.03"].mean() - st["1.06"].mean())) if "1.03" in st else None
        z2 = abs(float(st["13800"].mean() - st["1.06"].mean())) if "13800" in st else None
        szum = abs(d) > 2 * se
        # PROGI.md, zmiana 30.10: główną miarą szumu jest Z2, Z1 tylko jako kontekst.
        ponad_z2 = z2 is not None and abs(d) >= 3 * z2 and szum
        ponad_z1 = z1 is not None and abs(d) >= 3 * z1
        if d <= -0.03 and ponad_z2:
            werdykt = "działa" + (" (także wg Z1)" if ponad_z1 else " (nie wg Z1: 1.03/1.06)")
        elif d >= 0.03 and ponad_z2:
            werdykt = "szkodzi"
        else:
            werdykt = "nierozstrzygnięte"
        raport["heldout"] = {
            "loss": {m: float(v.mean()) for m, v in st.items()},
            "se": {m: float(v.std(ddof=1) / math.sqrt(len(v))) for m, v in st.items()},
            "per_komponent": {m: h[m]["per_komponent"] for m in h},
            "n_okien": nwin, "delta_A_B": d, "se_delta_A_B": se,
            "delta_A_baza": boot_delta(st["A"], st["1.06"], idx), "delta_B_baza": boot_delta(st["B"], st["1.06"], idx),
            "Z1_103_106": z1, "Z2_13800_13848": z2, "werdykt": werdykt}
        hh = raport["heldout"]
        md += ["", "| loss heldout (nat/token) | " + " | ".join(hh["loss"]) + " |", "|---|" + "---|" * len(hh["loss"]),
               "| średnia | " + " | ".join(f"{v:.4f}" for v in hh["loss"].values()) + " |",
               "| SE | " + " | ".join(f"{v:.4f}" for v in hh["se"].values()) + " |"]
        for k in next(iter(hh["per_komponent"].values())):
            md.append(f"| {k} | " + " | ".join(f"{hh['per_komponent'][m][k]:.4f}" for m in hh["loss"]) + " |")
        md += ["", f"Δ loss A−B = {d:+.4f} nat (SE {se:.4f}, n okien {nwin}); Z1 = {z1}; Z2 = {z2}; "
                   f"Δ A−1.06 = {hh['delta_A_baza'][0]:+.4f} ({hh['delta_A_baza'][1]:.4f}); "
                   f"Δ B−1.06 = {hh['delta_B_baza'][0]:+.4f} ({hh['delta_B_baza'][1]:.4f})",
               f"**Werdykt (loss): {werdykt}**"]
    (W / "porownanie.json").write_text(json.dumps(raport, indent=1, ensure_ascii=False))
    (W / "porownanie.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
