"""Zestawienie: ramiona C / C2 / E25 / PLHQ wobec siebie i bazy 13848, werdykt wg PROGI.md.

python testy_danych_slayer/porownaj_ramion.py --wyniki wyniki --K 100              # -> werdykt_glowny.json
python testy_danych_slayer/porownaj_ramion.py --wyniki wyniki --K 100 --szuflada   # dopiero po werdykcie głównym

Układ: wyniki/heldout_{13800,13848,C,C2,E25,PLHQ}.json, wyniki/{13848,C,C2,E25,PLHQ}/<zadanie>.jsonl + zrodla.json,
szuflada w wyniki/szuflada/{C,E25,PLHQ}/. Odmawia, gdy krok modelu w wynikach != oczekiwany (13848+K dla ramion).
BPB agregatu = średnia ważona BPB komponentów (wagi stałe); SE i przedział 95% z bootstrapu parowanego,
warstwowanego po komponentach. Benchmarki: parowany bootstrap po pytaniach. B = 10 000, seed 20261028.
Szum: Z2 = |13800 − 13848| i Zk = |C2 − C| (kolejność danych); próg bierze większy.
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "common"))
from hipoteza_formatu import wybory  # noqa: E402

LN2 = math.log(2)
B = 10000
SEED = 20261028
RAMIONA = ["C", "C2", "E25", "PLHQ"]
MIN_WZGL = 0.01       # minimalny efekt praktyczny: 1% BPB kontroli na agregacie
TOLERANCJA_PL = 0.01  # test 1: górna granica 95% CI Δ BPB PL_mix musi być < 1% BPB kontroli (PROGI.md)

AGREGATY = {
    "PL_neutralny": {"core": 0.19, "legal": 0.08},
    "PL_mix": {"web_hplt": 0.63, "core": 0.19, "legal": 0.08},
    "PL_hplt": {"web_hplt": 1.0},
    "PL_hq": {"web_hq": 1.0},
}
EN_TESTY = ["arc_e_cloze", "mmlu_cloze_5shot", "siqa_cloze"]   # decyduje BPB poprawnej
PL_TESTY_BPB = ["belebele_cloze"]                               # decyduje BPB poprawnej
PL_TESTY_ACC = ["multiblimp"]                                   # para minimalna: acc
GLOWNE = ["arc_e_cloze", "arc_c_cloze", "mmlu_cloze_5shot", "siqa_cloze", "belebele_cloze", "belebele_mc", "multiblimp"]
SZUFLADA = {"EN": ["hellaswag_cloze", "piqa_cloze"], "PL": ["gmmlu_pl_cloze_5shot", "llmzszl_cloze"]}
RAPORT_ACC = {"belebele_mc": "acc", "multiblimp": "acc"}        # pozostałe: acc_norm (tylko raport)


# ---------------------------------------------------------------- czyste funkcje (testy: test_testy_danych_slayer.py)

def wagi_en(komponenty_okna):
    en = {k: n for k, n in komponenty_okna.items() if k.startswith("en")}
    s = sum(en.values())
    return {k: n / s for k, n in en.items()} if s else {}


def bpb_agregatu(okna, wagi, idx=None):
    """okna: {komponent: (loss_suma[n], bajty[n])}; idx: {komponent: macierz [B, n]} albo None (punkt)."""
    sw = sum(wagi.values())
    tot = 0.0
    for k, w in wagi.items():
        L, by = okna[k]
        if idx is None:
            v = L.sum() / (LN2 * by.sum())
        else:
            v = L[idx[k]].sum(1) / (LN2 * by[idx[k]].sum(1))
        tot = tot + (w / sw) * v
    return tot


def werdykt_loss(d, se, szum, ref):
    """'spadek' / 'wzrost', gdy |Δ| > 2 SE i |Δ| >= max(3·szum, 1% ref); inaczej 'nierozstrzygnięte'."""
    if abs(d) > 2 * se and abs(d) >= max(3 * szum, MIN_WZGL * ref):
        return "spadek" if d < 0 else "wzrost"
    return "nierozstrzygnięte"


def ruch(delta, se, szum=0.0, lepiej_nizej=False):
    """+1 istotnie lepiej, -1 istotnie gorzej, 0 w szumie. Istotnie: |Δ| > 2 SE i |Δ| > 2·szum kolejności."""
    if abs(delta) <= 2 * se or abs(delta) <= 2 * szum:
        return 0
    lepiej = delta < 0 if lepiej_nizej else delta > 0
    return 1 if lepiej else -1


def koszt_pl(gorna_ci, ref, werdykt_pl, ruchy_pl):
    """'brak' tylko przy górnej granicy 95% CI Δ PL_mix < TOLERANCJA_PL·ref i bez testu PL w dół."""
    if werdykt_pl == "wzrost" or any(v == -1 for v in ruchy_pl.values()):
        return "jest"
    if gorna_ci < TOLERANCJA_PL * ref:
        return "brak"
    return "nierozstrzygnięty"


def werdykt_test1(en_loss, ruchy_en, koszt):
    """en_loss: werdykt BPB heldoutu EN (E25−C); ruchy_en: BPB poprawnej ARC-E/MMLU/SIQA; koszt: koszt_pl()."""
    gorzej = any(v == -1 for v in ruchy_en.values()) or en_loss == "wzrost"
    pomaga = en_loss == "spadek" and sum(v == 1 for v in ruchy_en.values()) >= 2 and not gorzej
    if pomaga:
        return {"brak": "EN pomaga bez kosztu PL", "jest": "EN pomaga kosztem PL",
                "nierozstrzygnięty": "EN pomaga, koszt PL nierozstrzygnięty"}[koszt]
    if gorzej:
        return "EN szkodzi EN"
    if koszt == "jest":
        return "szkodzi PL bez zysku EN"
    return "nierozstrzygnięte"


def werdykt_test2(pl_loss, ruchy_pl):
    gorzej = any(v == -1 for v in ruchy_pl.values())
    lepiej = any(v == 1 for v in ruchy_pl.values())
    if pl_loss == "spadek" and not gorzej:
        return "PL-HQ pomaga (loss i testy)" if lepiej else "PL-HQ obniża loss PL"
    if pl_loss == "wzrost" or (gorzej and pl_loss != "spadek"):
        return "PL-HQ szkodzi"
    return "nierozstrzygnięte"


def kierunki(t1, t2):
    """Oczekiwany kierunek szuflady per (test, język): +1 poprawa, -1 pogorszenie, 0 brak ruchu, None nie dotyczy."""
    en = {"EN pomaga bez kosztu PL": 1, "EN pomaga kosztem PL": 1, "EN pomaga, koszt PL nierozstrzygnięty": 1,
          "EN szkodzi EN": -1}.get(t1)
    pl1 = {"EN pomaga bez kosztu PL": 0, "EN pomaga kosztem PL": -1, "szkodzi PL bez zysku EN": -1}.get(t1)
    pl2 = {"PL-HQ pomaga (loss i testy)": 1, "PL-HQ obniża loss PL": 1, "PL-HQ szkodzi": -1}.get(t2)
    return {("test1", "EN"): en, ("test1", "PL"): pl1, ("test2", "PL"): pl2}


def status_szuflady(kierunek, ruchy, n_oczekiwanych):
    """Potwierdzenie wymaga ruchu w oczekiwanym kierunku; sam brak sprzeczności nie potwierdza."""
    if kierunek is None:
        return "nie dotyczy"
    if len(ruchy) < n_oczekiwanych:
        return f"brak danych szuflady ({len(ruchy)}/{n_oczekiwanych})"
    if kierunek == 0:
        return "sprzeczny" if any(v == -1 for v in ruchy.values()) else "zgodny (brak pogorszenia)"
    if any(v == -kierunek for v in ruchy.values()):
        return "sprzeczny"
    if any(v == kierunek for v in ruchy.values()):
        return "potwierdzony"
    return "niepotwierdzony (szuflada w szumie)"


# ---------------------------------------------------------------- wczytanie

def wczytaj_heldout(W, oczekiwane):
    h = {}
    for m, krok in oczekiwane.items():
        f = W / f"heldout_{m}.json"
        if not f.exists():
            raise SystemExit(f"STOP: brak {f}")
        d = json.loads(f.read_text())
        if d.get("config_step") != krok:
            raise SystemExit(f"STOP: {f.name} ma krok {d.get('config_step')}, oczekiwany {krok}")
        okna = {}
        for o in d["okna"]:
            okna.setdefault(o["komponent"], ([], []))
            okna[o["komponent"]][0].append(o["loss_suma"])
            okna[o["komponent"]][1].append(o["bajty"])
        h[m] = {k: (np.array(a), np.array(b, dtype=np.float64)) for k, (a, b) in okna.items()}
    return h


def sprawdz_krok(katalog, krok):
    z = katalog / "zrodla.json"
    if not z.exists() or json.loads(z.read_text()).get("config_step") != krok:
        got = json.loads(z.read_text()).get("config_step") if z.exists() else "brak zrodla.json"
        raise SystemExit(f"STOP: {katalog} ma krok {got}, oczekiwany {krok}")


def wiersze(katalog, zadanie):
    f = katalog / f"{zadanie}.jsonl"
    return {json.loads(x)["id"]: json.loads(x) for x in f.read_text().splitlines() if x.strip()} if f.exists() else None


def wektory(d, ids, met):
    acc = np.array([float(wybory(d[i])[met] == d[i]["gold"]) for i in ids])
    bpb = np.array([-d[i]["ll"][d[i]["gold"]] / (LN2 * max(d[i]["bajty"][d[i]["gold"]], 1)) for i in ids])
    return acc, bpb


def porownaj_benchmark(Wa, Wb, zadanie, rng, Wc2=None):
    """Δ = a − b; zk = |C2 − C| tej samej wielkości (gdy podano katalog C2, a b to C)."""
    da, db = wiersze(Wa, zadanie), wiersze(Wb, zadanie)
    if not da or not db:
        return None
    dc2 = wiersze(Wc2, zadanie) if Wc2 else None
    ids = sorted(set(da) & set(db) & (set(dc2) if dc2 else set(da)))
    met = RAPORT_ACC.get(zadanie, "acc_norm")
    aa, ba = wektory(da, ids, met)
    ab, bb = wektory(db, ids, met)
    idx = rng.integers(0, len(ids), size=(B, len(ids)))
    out = {"n": len(ids), "metryka_acc": met}
    for nazwa, x, y in (("acc", aa, ab), ("bpb_poprawnej", ba, bb)):
        d = x - y
        out[nazwa] = {"a": float(x.mean()), "b": float(y.mean()), "delta": float(d.mean()),
                      "se": float(d[idx].mean(1).std(ddof=1))}
    if dc2:
        ac, bc = wektory(dc2, ids, met)
        out["acc"]["zk"] = abs(float(ac.mean() - ab.mean()))
        out["bpb_poprawnej"]["zk"] = abs(float(bc.mean() - bb.mean()))
    return out


def ruch_zadania(r, zadanie):
    if zadanie in PL_TESTY_ACC:
        a = r["acc"]
        return ruch(a["delta"], a["se"], a.get("zk", 0.0))
    b = r["bpb_poprawnej"]
    return ruch(b["delta"], b["se"], b.get("zk", 0.0), lepiej_nizej=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--wyniki", required=True)
    p.add_argument("--K", type=int, required=True)
    p.add_argument("--szuflada", action="store_true")
    a = p.parse_args()
    W = Path(a.wyniki)
    rng = np.random.default_rng(SEED)
    koniec = 13848 + a.K

    if a.szuflada:
        wg = W / "werdykt_glowny.json"
        if not wg.exists():
            raise SystemExit("STOP: szuflada otwiera się dopiero po werdykcie głównym (werdykt_glowny.json)")
        glowny = json.loads(wg.read_text())
        S = W / "szuflada"
        for r in ("C", "E25", "PLHQ"):
            sprawdz_krok(S / r, koniec)
        out = {"sha256_werdyktu_glownego": hashlib.sha256(wg.read_bytes()).hexdigest(), "porownania": {}, "status": {}}
        for ram in ("E25", "PLHQ"):
            out["porownania"][ram] = {z: porownaj_benchmark(S / ram, S / "C", z, rng)
                                      for z in SZUFLADA["EN"] + SZUFLADA["PL"]}
        for (test, jez), kier in kierunki(glowny["test1"]["werdykt"], glowny["test2"]["werdykt"]).items():
            ram = "E25" if test == "test1" else "PLHQ"
            ruchy = {z: ruch_zadania(v, z) for z, v in out["porownania"][ram].items() if v and z in SZUFLADA[jez]}
            out["status"][f"{test}:{jez}"] = {"kierunek": kier, "ruchy": ruchy,
                                              "status": status_szuflady(kier, ruchy, len(SZUFLADA[jez]))}
        (W / "szuflada.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(json.dumps(out["status"], indent=1, ensure_ascii=False))
        return

    oczek = {"13800": 13800, "13848": 13848, **{r: koniec for r in RAMIONA}}
    h = wczytaj_heldout(W, oczek)
    for m, krok in oczek.items():
        if m != "13800":
            sprawdz_krok(W / m, krok)
    komp = h["C"]
    idx = {k: rng.integers(0, len(komp[k][0]), size=(B, len(komp[k][0]))) for k in komp}
    agregaty = dict(AGREGATY)
    agregaty["EN"] = wagi_en({k: len(v[0]) for k, v in komp.items()})
    for k in komp:
        agregaty[f"komp:{k}"] = {k: 1.0}
    held = {}
    for nazwa, wagi in agregaty.items():
        if not wagi or not all(k in komp for k in wagi):
            continue
        pkt = {m: float(bpb_agregatu(h[m], wagi)) for m in h}
        bs = {m: bpb_agregatu(h[m], wagi, idx) for m in h}
        z2, zk = abs(pkt["13800"] - pkt["13848"]), abs(pkt["C2"] - pkt["C"])
        r = {"bpb": pkt, "Z2": z2, "Zk": zk, "szum": max(z2, zk)}
        for x in ("E25", "PLHQ"):
            d = pkt[x] - pkt["C"]
            bd = bs[x] - bs["C"]
            se = float(np.std(bd, ddof=1))
            r[f"{x}-C"] = {"delta": d, "se": se, "ci95": [float(np.quantile(bd, 0.025)), float(np.quantile(bd, 0.975))],
                           "werdykt": werdykt_loss(d, se, r["szum"], pkt["C"])}
        held[nazwa] = r

    bench = {x: {z: porownaj_benchmark(W / x, W / "C", z, rng, W / "C2") for z in GLOWNE} for x in ("E25", "PLHQ")}
    bench["C-13848"] = {z: porownaj_benchmark(W / "C", W / "13848", z, rng) for z in GLOWNE}

    ruchy_en = {z: ruch_zadania(bench["E25"][z], z) for z in EN_TESTY if bench["E25"].get(z)}
    ruchy_pl1 = {z: ruch_zadania(bench["E25"][z], z) for z in PL_TESTY_BPB + PL_TESTY_ACC if bench["E25"].get(z)}
    ruchy_pl2 = {z: ruch_zadania(bench["PLHQ"][z], z) for z in PL_TESTY_BPB + PL_TESTY_ACC if bench["PLHQ"].get(z)}
    plm = held["PL_mix"]
    k1 = koszt_pl(plm["E25-C"]["ci95"][1], plm["bpb"]["C"], plm["E25-C"]["werdykt"], ruchy_pl1)
    t1 = werdykt_test1(held["EN"]["E25-C"]["werdykt"] if "EN" in held else "nierozstrzygnięte", ruchy_en, k1)
    t2 = werdykt_test2(held["PL_neutralny"]["PLHQ-C"]["werdykt"], ruchy_pl2)
    out = {"K": a.K, "heldout": held, "benchmarki": bench,
           "test1": {"werdykt": t1, "ruchy_EN_bpb_poprawnej": ruchy_en, "ruchy_PL": ruchy_pl1, "koszt_PL": k1,
                     "tolerancja_PL_bpb": TOLERANCJA_PL * plm["bpb"]["C"], "loss_PL_mix": plm["E25-C"],
                     "loss_EN": held.get("EN", {}).get("E25-C")},
           "test2": {"werdykt": t2, "ruchy_PL": ruchy_pl2, "loss_PL_neutralny": held["PL_neutralny"]["PLHQ-C"],
                     "loss_PL_hplt": held["PL_hplt"]["PLHQ-C"], "loss_PL_hq": held.get("PL_hq", {}).get("PLHQ-C")}}
    (W / "werdykt_glowny.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    md = ["| agregat | Z2 | Zk | BPB C | Δ E25−C (SE) [95% CI] | werdykt | Δ PLHQ−C (SE) | werdykt |",
          "|---|---|---|---|---|---|---|---|"]
    for n, r in held.items():
        e, q = r["E25-C"], r["PLHQ-C"]
        md.append(f"| {n} | {r['Z2']:.4f} | {r['Zk']:.4f} | {r['bpb']['C']:.4f} | {e['delta']:+.4f} ({e['se']:.4f}) "
                  f"[{e['ci95'][0]:+.4f}, {e['ci95'][1]:+.4f}] | {e['werdykt']} | {q['delta']:+.4f} ({q['se']:.4f}) | "
                  f"{q['werdykt']} |")
    md += ["", "| zadanie | n | BPB popr. Δ E25−C (SE, Zk) | Δ PLHQ−C (SE, Zk) | acc Δ E25−C (SE) | acc Δ PLHQ−C (SE) |",
           "|---|---|---|---|---|---|"]
    for z in GLOWNE:
        e, q = bench["E25"].get(z), bench["PLHQ"].get(z)
        if not (e or q):
            continue
        f = lambda r, m: (f"{r[m]['delta']:+.4f} ({r[m]['se']:.4f}" + (f", {r[m]['zk']:.4f}" if "zk" in r[m] else "")  # noqa: E731
                          + ")") if r else "—"
        md.append(f"| {z} | {(e or q)['n']} | {f(e, 'bpb_poprawnej')} | {f(q, 'bpb_poprawnej')} | {f(e, 'acc')} | {f(q, 'acc')} |")
    md += ["", f"**Test 1 (udział EN): {t1}** (koszt PL: {k1})", f"**Test 2 (jakość PL): {t2}**"]
    (W / "werdykt_glowny.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
