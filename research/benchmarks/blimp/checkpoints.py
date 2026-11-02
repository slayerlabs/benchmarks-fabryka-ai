"""BLiMP over training checkpoints and weight averaging: statistics (results/CHECKPOINTS_THRESHOLDS.md).

  python benchmarks/blimp/checkpoints.py zbierz --surowe benchmarks/blimp/results/checkpoints \
      --wyjscie benchmarks/blimp/results/checkpoints.json
  python benchmarks/blimp/checkpoints.py raport   # results/LICZBY.json -> results/CHECKPOINTS.md + blimp_curve.svg

Reads per-pair results <surowe>/<label>.jsonl.gz (labels k<step>, avg3/5/10), Pythia-1B and the MPS 1.06
run from benchmarks/blimp/results/<model>/blimp.jsonl.gz, held-out losses <surowe>/heldout_<model>.json.
Pure functions are tested in tests/test_blimp_checkpoints.py on dummy data.
"""

import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

import blimp
from blimp_analiza import P_PRAWDOPODOBNE, holm, p_t, p_z, werdykt_p

KORZEN = Path(__file__).resolve().parents[2]  # research/
WYNIKI = KORZEN / "benchmarks/blimp/results"
WYGASZANIE = KORZEN / "slayer-1b/wygaszanie/wyniki"
TOKENY_NA_KROK = 2 ** 20  # batch 256 x block 4096
PUNKTY = [("1.00", 1430), ("1.01", 2860), ("1.02", 5720), ("1.03", 7150), ("1.04", 8600), ("1.04", 10010),
          ("1.04", 11450), ("1.05", 12870), ("1.06", 13848)]
# Protocol constants (CHECKPOINTS_THRESHOLDS.md, committed before the measurement); tests pin them.
# final run: primary slope. Amendment 1: 11450 and 12870 not measured (scope cut)
GLOWNE = [7150, 8600, 10010, 13848]
# the composition the protocol prescribes; the built composition is read from results/checkpoints/averages.jsonl
SREDNIE = {"avg3": [13750, 13800, 13848], "avg5": [13650, 13700, 13750, 13800, 13848],
           "avg10": list(range(13400, 13848, 50)) + [13848]}
SREDNIE_Q2 = ("avg3", "avg5")  # amendment 1: the question 2 verdict rests on these; avg10 is reported beside it
PROG_URZADZENIE = 30  # max changed pair outcomes between devices
BOOT = 2000
# protocol thresholds: share >= 0.5 of the annealing gain, written as 0.5 x (-0.0504); the measured references
# themselves are read from slayer-1b/wygaszanie/wyniki/heldout_*.json (odniesienie_wygaszania)
HELDOUT_1_06 = 2.33104
HELDOUT_TOL = 0.0005
WYGASZANIE_VS_106 = -0.0504
PROG_SREDNIA = -0.01
VAL_SHA = "86ebed396365110cfce1305d0647dbc0122031239af13e17c08ef62ba173b2d3"
LN2 = math.log(2)
EPS = 1e-12
MOCNE = ("pewne", "prawdopodobne")


def mld(krok):
    return krok * TOKENY_NA_KROK / 1e9


def wagi_ols(x):
    """OLS slope = sum_c w_c y_c with w_c = (x_c - mean) / sum (x - mean)^2."""
    m = sum(x) / len(x)
    s = sum((v - m) ** 2 for v in x)
    return [(v - m) / s for v in x]


def nachylenie(x, y):
    return sum(w * v for w, v in zip(wagi_ols(x), y))


def macierz_trafien(docs, wyniki):
    """{paradigm: [[hit of pair i for model c] for c]} in doc order; `wyniki` = list of {id: row} per model."""
    out = {}
    for d in docs:
        out.setdefault(d["grupa"], [[] for _ in wyniki])
        for c, w in enumerate(wyniki):
            out[d["grupa"]][c].append(blimp.trafienie_pary(d, w[d["id"]]))
    return out


def nachylenie_statystyki(x, H, boot=BOOT, seed=blimp.SEED, grupy=None):
    """Slope of the equal-paradigm-weight accuracy on x. H = macierz_trafien (models in the order of x).
    pairs: bootstrap of pairs within paradigms, the same pairs for every model; paradigms: t over per-paradigm slopes."""
    import numpy as np
    w = np.array(wagi_ols(x))
    gr = sorted(H) if grupy is None else grupy
    per_g = []
    rng = np.random.default_rng(seed)
    boot_acc = np.zeros((boot, len(x)))
    for g in gr:
        h = np.array(H[g], dtype=float)  # [models, pairs]
        n = h.shape[1]
        per_g.append(float(w @ h.mean(axis=1)))
        idx = rng.integers(0, n, size=(boot, n))
        boot_acc += h[:, idx].mean(axis=2).T
    boot_acc /= len(gr)
    b_boot = (boot_acc * w).sum(axis=1)  # not `@`: macOS Accelerate matmul raises spurious FP warnings
    b = sum(per_g) / len(per_g)
    se = float(b_boot.std(ddof=1))
    lo, hi = (float(v) for v in np.percentile(b_boot, [2.5, 97.5]))
    z = b / se if se > 0 else None
    k = len(per_g)
    sd = math.sqrt(sum((v - b) ** 2 for v in per_g) / (k - 1)) if k > 1 else 0.0
    se_k = sd / math.sqrt(k) if k > 1 else None
    t = b / se_k if se_k and se_k > EPS else None  # float residue of equal slopes is no variance
    p = p_t(t, k - 1) if t is not None else None
    return {"nachylenie": b, "se": se, "ci95": [lo, hi], "z": z, "p": p_z(z) if z is not None else None,
            "werdykt": blimp.werdykt(z), "k": k, "se_klastr": se_k, "t": t, "df": k - 1,
            "p_klastr": p, "werdykt_klastr": (werdykt_p(p) if k >= 3 else "nierozstrzygalne") if p is not None else None,
            "_boot": b_boot}


def werdykt_luki(st):
    """CHECKPOINTS_THRESHOLDS.md question 1: the gap shrinks / no detectable shrinking / not determined."""
    mocne = ("pewne", "prawdopodobne")
    if st["nachylenie"] > 0 and st["werdykt"] in mocne and st["werdykt_klastr"] in mocne:
        return "potwierdzone"
    if st["ci95"][0] <= 0:
        return "obalone"
    return "nierozstrzygniete"


def rosnie(r):
    """Question 1, item 4: a phenomenon grows when its slope is > 0, Holm-significant on pairs AND certain or
    probable over its paradigms (noise, undetermined and no variance do not count)."""
    return bool(r["nachylenie"] > 0 and r["holm"] and r["werdykt_klastr"] in MOCNE)


def nachylenie_reszty(x, y):
    """OLS slope of y on x with the classical SE from the residuals between the points (df = n - 2): how well a
    straight line fits the checkpoints themselves, as opposed to the sampling noise of the pairs."""
    n = len(x)
    b = nachylenie(x, y)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((v - mx) ** 2 for v in x)
    reszty = [yi - (my + b * (xi - mx)) for xi, yi in zip(x, y)]
    df = n - 2
    se = math.sqrt(sum(r * r for r in reszty) / df / sxx) if df > 0 else None
    t = b / se if se and se > EPS else None
    p = p_t(t, df) if t is not None else None
    return {"nachylenie": b, "se_reszty": se, "t": t, "df": df, "p": p, "reszty": reszty,
            "werdykt": werdykt_p(p) if p is not None else None}


def zastrzezenia_luki(bez_ostatniego, reszty):
    """Reasons the protocol verdict of question 1 does not read as a steady trend (empty = none)."""
    out = []
    if not (bez_ostatniego["nachylenie"] > 0 and bez_ostatniego["werdykt"] in MOCNE
            and bez_ostatniego["werdykt_klastr"] in MOCNE):
        out.append("bez_ostatniego_punktu_brak_wzrostu")
    if reszty["werdykt"] not in MOCNE:
        out.append("trend_nieodroznialny_od_wahan_miedzy_checkpointami")
    return out


def wklad_paradygmatow(Ha, Hb, ile=5):
    """Contribution of each paradigm to the equal-weight difference a - b (difference / k), the `ile` largest
    in the direction of the change (most negative for a fall), and the difference left without them."""
    gr = sorted(Ha)
    k = len(gr)
    w = {g: (sum(Ha[g]) / len(Ha[g]) - sum(Hb[g]) / len(Hb[g])) / k for g in gr}
    znak = 1 if sum(w.values()) >= 0 else -1
    top = sorted(gr, key=lambda g: (-znak * w[g], g))[:ile]
    return {"top": [{"grupa": g, "wklad": w[g]} for g in top], "suma_top": sum(w[g] for g in top),
            "bez_top": sum(w.values()) - sum(w[g] for g in top)}


def porownanie_klastrowe(H_a, H_b, grupy=None):
    """Paired a - b with SE over paradigm differences (t, df = k - 1)."""
    gr = sorted(H_a) if grupy is None else grupy
    r = [sum(H_a[g]) / len(H_a[g]) - sum(H_b[g]) / len(H_b[g]) for g in gr]
    k = len(r)
    m = sum(r) / k
    se = math.sqrt(sum((v - m) ** 2 for v in r) / (k - 1)) / math.sqrt(k) if k > 1 else None
    t = m / se if se and se > EPS else None
    p = p_t(t, k - 1) if t is not None else None
    return {"roznica": m, "k": k, "se_klastr": se, "t": t, "df": k - 1, "p_klastr": p,
            "werdykt_klastr": (werdykt_p(p) if k >= 3 else "nierozstrzygalne") if p is not None else None}


def zmiany_wynikow(docs, wa, wb):
    """Pairs whose outcome differs between two runs of the same model, and the max |ll difference|."""
    zm, mx = 0, 0.0
    for d in docs:
        ra, rb = wa[d["id"]], wb[d["id"]]
        zm += blimp.trafienie_pary(d, ra) != blimp.trafienie_pary(d, rb)
        mx = max(mx, max(abs(x - y) for x, y in zip(ra["ll"], rb["ll"])))
    return {"zmienione_pary": zm, "max_abs_ll": mx, "w_progu": zm <= PROG_URZADZENIE}


def kontrola_gpu(docs, katalog):
    """The same model scored on different GPU types: <katalog>/<gpu>/<label>.jsonl.gz, every pair of GPUs."""
    out = []
    katalog = Path(katalog)
    if not katalog.exists():
        return out
    for model in ("k13848", "avg3"):
        pliki = sorted(katalog.glob(f"*/{model}.jsonl.gz"))
        wyn = [(p.parent.name, blimp.wczytaj_wyniki(p)) for p in pliki]
        for i in range(len(wyn)):
            for j in range(i + 1, len(wyn)):
                out.append({"model": model, "a": wyn[i][0], "b": wyn[j][0], **zmiany_wynikow(docs, wyn[i][1], wyn[j][1])})
    return out


def heldout_porownanie(a, b):
    """Paired per-window loss difference a - b (same windows required)."""
    oa, ob = a["okna"], b["okna"]
    if [(o["komponent"], o["start"]) for o in oa] != [(o["komponent"], o["start"]) for o in ob]:
        raise ValueError("held-out windows differ")
    r = [x["loss"] - y["loss"] for x, y in zip(oa, ob)]
    n = len(r)
    m = sum(r) / n
    se = math.sqrt(sum((v - m) ** 2 for v in r) / (n - 1)) / math.sqrt(n)
    z = m / se if se > 0 else None
    # bits per TOKEN, not BPB: the byte length of the held-out windows was not saved, so bits per byte is not computed
    return {"roznica": m, "se": se, "z": z, "werdykt": blimp.werdykt(z), "n_okien": n,
            "roznica_bity_na_token": m / LN2}


def heldout_komponenty(a, b):
    """Mean per-window loss difference a - b per data component (web, core, legal, en), same windows required."""
    if [(o["komponent"], o["start"]) for o in a["okna"]] != [(o["komponent"], o["start"]) for o in b["okna"]]:
        raise ValueError("held-out windows differ")
    po = {}
    for x, y in zip(a["okna"], b["okna"]):
        po.setdefault(x["komponent"], []).append(x["loss"] - y["loss"])
    return {k: {"roznica": sum(v) / len(v), "n_okien": len(v)} for k, v in po.items()}


def odniesienie_wygaszania(katalog):
    """Measured annealing references from the annealing run's held-out files (same windows): Slayer 1.06 loss,
    annealed arm A - 1.06 and A - constant-LR arm B. None when a file is missing."""
    katalog = Path(katalog)
    pl = {n: katalog / f"heldout_{n}.json" for n in ("1.06", "A", "B")}
    if not all(p.exists() for p in pl.values()):
        return None
    h = {n: json.loads(p.read_text()) for n, p in pl.items()}
    return {"loss_1.06": h["1.06"]["loss"], "A_vs_1.06": heldout_porownanie(h["A"], h["1.06"]),
            "A_vs_B": heldout_porownanie(h["A"], h["B"]), "_okna": h}


def werdykt_sredniej(por_heldout, modele=None):
    """Question 2: substitute for annealing confirmed / refuted (per THRESHOLDS), over `modele` (default all)."""
    ok = [k for k, r in por_heldout.items() if (modele is None or k in modele)
          and r["roznica"] <= 0.5 * WYGASZANIE_VS_106 and r["z"] is not None and abs(r["z"]) >= 3]
    return "potwierdzone" if ok else "obalone"


def kontrole(out):
    """Controls of the protocol that block a verdict when they fail or are missing: {name: True/False/None}
    for question 1 (BLiMP of checkpoints) and question 2 (averages, held-out)."""
    ku = out.get("kontrola_urzadzenia")
    kg = out.get("kontrola_gpu") or []
    q1 = {"urzadzenie": ku["w_progu"] if ku else None,
          "gpu": all(g["w_progu"] for g in kg) if kg else None,  # no copies on other GPUs = no control
          "konwersja": out.get("konwersja_13848_max_abs") == 0 if out.get("konwersja_13848_max_abs") is not None else None,
          "sha_ckpt": out.get("sha_ckpt_zgodne")}
    ho = out.get("heldout", {})
    q2 = {**q1, "heldout_1.06": ho.get("kontrola_1.06"), "val_sha": ho.get("val_sha256_zgodne"),
          "odniesienia": ho.get("odniesienia_zgodne_z_protokolem"),
          "sklad_srednich": all(s.get("sklad_zgodny_z_protokolem") is True for s in out.get("srednie", {}).values())
          if out.get("srednie") else None,
          "sha_ckpt_srednich": all(s.get("sha_ckpt_zgodne") is True for s in out.get("srednie", {}).values())
          if out.get("srednie") else None}
    return {"q1": q1, "q2": q2, "q1_ok": all(v is True for v in q1.values()), "q2_ok": all(v is True for v in q2.values())}


def zastosuj_kontrole(out):
    """A failed or missing control turns the verdict into 'nieustalone' (kept as werdykt_przed_kontrola)."""
    k = kontrole(out)
    out["kontrole"] = k
    if "nachylenie" in out and not k["q1_ok"]:
        out["nachylenie"]["werdykt_przed_kontrola"] = out["nachylenie"]["werdykt_luki"]
        out["nachylenie"]["werdykt_luki"] = "nieustalone"
    ho = out.get("heldout", {})
    if "werdykt_substytut" in ho and not k["q2_ok"]:
        ho["werdykt_przed_kontrola"] = ho["werdykt_substytut"]
        ho["werdykt_substytut"] = "nieustalone"
    return out


def sha_pliku(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def wczytaj_surowy(katalog, etykieta):
    for p in (Path(katalog) / f"{etykieta}.jsonl.gz", Path(katalog) / etykieta / "blimp.jsonl"):
        if p.exists():
            return blimp.wczytaj_wyniki(p), p
    return None, None


def sklad_srednich(surowe, pobrania):
    """Composition of each average from results/checkpoints/averages.jsonl (average_weights.py output: steps read
    from the checkpoint files), compared with the protocol and with the SHA check of the downloads of those steps."""
    p = Path(surowe) / "averages.jsonl"
    if not p.exists():
        return {}
    ok_sha = {r["krok"]: r["zgodny_z_lfs"] for r in pobrania if r.get("repo", "").endswith("1.06-checkpoints")}
    out = {}
    for l in p.read_text().splitlines():
        if not l.strip():
            continue
        r = json.loads(l)
        kroki = sorted(r["kroki"])
        out[r["model"]] = {"kroki": kroki, "sha256_safetensors": r.get("sha256_safetensors"), "zrodlo": r.get("zrodlo"),
                           "sklad_zgodny_z_protokolem": kroki == sorted(SREDNIE.get(r["model"], [])),
                           "sha_ckpt_zgodne": all(ok_sha.get(s) is True for s in kroki)}
    return out


def przerwane_przebiegi(tekst):
    """From an instance's logi/punkty.log: the BLiMP runs that did not reach all pairs. A conversion line
    {"step": S, ...} opens the run of checkpoint S; progress lines read '[blimp] done/total'."""
    krok, stan = None, {}
    for l in tekst.replace("\r", "\n").splitlines():
        l = l.strip()
        if l.startswith('{"step"'):
            krok = json.loads(l)["step"]
        elif l.startswith("[blimp]") and krok is not None:
            zrob, wsz = l.split()[1].split("/")
            stan[krok] = (int(zrob), int(wsz))
    return [{"krok": s, "pary": z, "wszystkie": w, "udzial": z / w} for s, (z, w) in stan.items() if z < w]


def zbierz(surowe, dane=None, gpu=None, wygaszanie=None, kontrola_gpu_zapas=None):
    docs = blimp.wczytaj(dane)
    pythia = blimp.wczytaj_wyniki(WYNIKI / "pythia-1b/blimp.jsonl.gz")
    mps106 = blimp.wczytaj_wyniki(WYNIKI / "1.06/blimp.jsonl.gz")
    modele, pliki = {}, {}
    for e in [f"k{s}" for _, s in PUNKTY] + list(SREDNIE):
        w, p = wczytaj_surowy(surowe, e)
        if w is None:
            continue
        brak = [d["id"] for d in docs if d["id"] not in w]
        if brak:
            raise SystemExit(f"{e}: {len(brak)} pairs without a result")
        modele[e], pliki[e] = w, p
    out = {"protokol": "benchmarks/blimp/results/CHECKPOINTS_THRESHOLDS.md", "n": len(docs),
           "sha256_surowych": {e: sha_pliku(p) for e, p in pliki.items()},
           "kontrola_urzadzenia": zmiany_wynikow(docs, modele["k13848"], mps106) if "k13848" in modele else None,
           "pythia_acc": blimp.statystyki_modelu(pythia, docs, bootstrap=False)["acc"]}
    # per-GPU copies of the same model (not in the repo: 6 x 1.9 MB); the result is kept in checkpoints.json
    out["kontrola_gpu"] = kontrola_gpu(docs, Path(gpu) if gpu else Path(surowe) / "gpu") or (kontrola_gpu_zapas or [])
    konw = Path(surowe) / "conversions.jsonl"
    if konw.exists():
        wart = [json.loads(l).get("max_abs_roznica_vs_wzorzec") for l in konw.read_text().splitlines() if l.strip()]
        wart = [v for v in wart if v is not None]
        if wart:
            out["konwersja_13848_max_abs"] = max(wart)
    pobrania = [json.loads(l) for p in sorted(Path(surowe).glob("times_*.jsonl")) for l in p.read_text().splitlines()
                if l.strip() and json.loads(l).get("etap") == "pobranie"]
    if pobrania:
        out["sha_ckpt_zgodne"] = all(p["zgodny_z_lfs"] for p in pobrania)
        out["n_pobran"] = len(pobrania)
    out["przerwane"] = sorted(({"gpu": p.stem.removeprefix("points_"), **r} for p in Path(surowe).glob("points_*.log")
                               for r in przerwane_przebiegi(p.read_text())), key=lambda r: r["krok"])
    out["punkty"] = []
    for r, s in PUNKTY:
        e = f"k{s}"
        if e not in modele:
            continue
        st = blimp.statystyki_modelu(modele[e], docs)
        por = blimp.porownanie_parowane(modele[e], pythia, docs)
        out["punkty"].append({"etykieta": e, "repo": f"SlayerLab/Slayer1B-{r}-checkpoints", "krok": s, "mld": mld(s),
                              "glowny_bieg": s in GLOWNE, **st, "luka_pythia": por["ogolem"],
                              "luka_pythia_zjawiska": por["zjawiska"]})
    gl = [s for s in GLOWNE if f"k{s}" in modele]
    zj = sorted({d["zjawisko"] for d in docs})
    gr_zj = {z: sorted({d["grupa"] for d in docs if d["zjawisko"] == z}) for z in zj}
    if len(gl) == len(GLOWNE):
        H = macierz_trafien(docs, [modele[f"k{s}"] for s in gl])
        x = [mld(s) for s in gl]
        st = nachylenie_statystyki(x, H)
        st.pop("_boot")
        st["werdykt_luki"] = werdykt_luki(st)
        out["nachylenie"] = st
        # robustness of question 1 (not a protocol rule): the slope without the last point, and the SE from the
        # residuals of the checkpoint accuracies around the line (df = points - 2)
        H3 = {g: v[:-1] for g, v in H.items()}
        b3 = nachylenie_statystyki(x[:-1], H3)
        b3.pop("_boot")
        out["nachylenie_bez_ostatniego"] = {"kroki": gl[:-1], **b3}
        acc_gl = [next(p["acc"] for p in out["punkty"] if p["krok"] == s) for s in gl]
        out["nachylenie_reszty"] = nachylenie_reszty(x, acc_gl)
        st["zastrzezenia"] = zastrzezenia_luki(b3, out["nachylenie_reszty"])
        zjs = {}
        for z in zj:
            s_ = nachylenie_statystyki(x, H, grupy=gr_zj[z])
            s_.pop("_boot")
            zjs[z] = s_
        hz = holm({z: r["p"] for z, r in zjs.items()}, alfa=P_PRAWDOPODOBNE)
        for z, r in zjs.items():
            r["holm"] = hz[z]
            r["rosnie"] = rosnie(r)
            # robustness (not a protocol rule): residual SE of the phenomenon's checkpoint accuracies, and the
            # changes between adjacent points
            acc_z = [sum(sum(H[g][c]) / len(H[g][c]) for g in gr_zj[z]) / len(gr_zj[z]) for c in range(len(gl))]
            r["reszty"] = nachylenie_reszty(x, acc_z)
            r["kroki_sasiednie"] = [{"od": a, "do": b, "roznica": acc_z[i + 1] - acc_z[i]}
                                    for i, (a, b) in enumerate(zip(gl, gl[1:]))]
        out["nachylenie_zjawiska"] = zjs
        out["kroki"] = []
        for a, b in itertools.combinations(gl, 2):
            por = blimp.porownanie_parowane(modele[f"k{b}"], modele[f"k{a}"], docs)["ogolem"]
            Ha = {g: H[g][gl.index(b)] for g in H}
            Hb = {g: H[g][gl.index(a)] for g in H}
            out["kroki"].append({"od": a, "do": b, **por, **{k: v for k, v in porownanie_klastrowe(Ha, Hb).items() if k != "roznica"},
                                 "wklad_paradygmatow": wklad_paradygmatow(Ha, Hb)})
    wsz = [s for _, s in PUNKTY if f"k{s}" in modele]
    if len(wsz) >= 3:
        H = macierz_trafien(docs, [modele[f"k{s}"] for s in wsz])
        st = nachylenie_statystyki([math.log(mld(s)) for s in wsz], H)
        st.pop("_boot")
        out["nachylenie_ln_D"] = st
    out["srednie"] = {}
    sklad = sklad_srednich(surowe, pobrania)
    if "k13848" in modele:
        H106 = macierz_trafien(docs, [modele["k13848"]])
        H106 = {g: v[0] for g, v in H106.items()}
        for e in SREDNIE:
            if e not in modele:
                continue
            por = blimp.porownanie_parowane(modele[e], modele["k13848"], docs)
            Ha = {g: v[0] for g, v in macierz_trafien(docs, [modele[e]]).items()}
            sk = sklad.get(e, {"kroki": None, "sklad_zgodny_z_protokolem": None, "sha_ckpt_zgodne": None})
            out["srednie"][e] = {**sk, "acc": blimp.statystyki_modelu(modele[e], docs, bootstrap=False)["acc"],
                                 "blimp": {**por["ogolem"], **{k: v for k, v in porownanie_klastrowe(Ha, H106).items() if k != "roznica"}},
                                 "blimp_zjawiska": por["zjawiska"]}
        ps = {f"{e}/{z}": r["p_z"] for e in out["srednie"] for z, r in
              ((z, {"p_z": p_z(r["z"]) if r["z"] is not None else 1.0}) for z, r in out["srednie"][e]["blimp_zjawiska"].items())}
        hz = holm(ps, alfa=P_PRAWDOPODOBNE)
        for e in out["srednie"]:
            Ha = {g: v[0] for g, v in macierz_trafien(docs, [modele[e]]).items()}
            for z, r in out["srednie"][e]["blimp_zjawiska"].items():
                r["holm"] = hz[f"{e}/{z}"]
                kl = porownanie_klastrowe(Ha, H106, grupy=gr_zj[z])
                r.update({k: v for k, v in kl.items() if k != "roznica"})
    ho = {}
    for p in sorted(Path(surowe).glob("heldout_*.json")):
        if p.name == "heldout_stats.json":
            continue
        ho[p.stem.removeprefix("heldout_")] = json.loads(p.read_text())
    ref = odniesienie_wygaszania(Path(wygaszanie) if wygaszanie else WYGASZANIE)
    if "m106" in ho:
        out["heldout"] = {"loss_1.06": ho["m106"]["loss"], "se_1.06": ho["m106"]["se"], "n_okien": ho["m106"]["n_okien"],
                          "odniesienie_wygaszania": ref["loss_1.06"] if ref else None,
                          "kontrola_1.06": abs(ho["m106"]["loss"] - ref["loss_1.06"]) <= HELDOUT_TOL if ref else None}
        st = Path(surowe) / "heldout_stats.json"
        if st.exists():
            out["heldout"]["val_sha256_zgodne"] = json.loads(st.read_text())["sha256"]["val.bin"] == VAL_SHA
        if ref:
            av, ab = ref["A_vs_1.06"]["roznica"], ref["A_vs_B"]["roznica"]
            out["heldout"]["wygaszanie_vs_1.06"] = av
            out["heldout"]["wygaszanie_vs_staly"] = ab
            # the protocol wrote the references rounded; the measured ones must round to them
            out["heldout"]["odniesienia_zgodne_z_protokolem"] = (round(av, 4) == WYGASZANIE_VS_106
                                                                and round(ref["loss_1.06"], 5) == HELDOUT_1_06)
            out["heldout"]["komponenty"] = {n: heldout_komponenty(ref["_okna"][n], ho["m106"]) for n in ("A", "B")}
        por = {}
        for e in SREDNIE:
            if e in ho:
                r = heldout_porownanie(ho[e], ho["m106"])
                r["loss"] = ho[e]["loss"]
                r["pomaga"] = r["roznica"] <= PROG_SREDNIA and r["z"] is not None and abs(r["z"]) >= 3
                if ref:
                    r["udzial_wygaszania"] = r["roznica"] / av
                    r["udzial_vs_staly"] = r["roznica"] / ab
                    r["vs_wygaszanie"] = heldout_porownanie(ho[e], ref["_okna"]["A"])
                    out["heldout"]["komponenty"][e] = heldout_komponenty(ho[e], ho["m106"])
                por[e] = r
        out["heldout"]["srednie"] = por
        if por:
            q2 = {e: r for e, r in por.items() if e in SREDNIE_Q2}
            out["heldout"]["srednie_werdyktu"] = list(q2)
            out["heldout"]["werdykt_substytut"] = werdykt_sredniej(q2)
            out["heldout"]["werdykt_substytut_avg10"] = werdykt_sredniej(por, ("avg10",)) if "avg10" in por else None
    return zastosuj_kontrole(out)


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zbierz")
    z.add_argument("--surowe", default=str(WYNIKI / "checkpoints"))
    z.add_argument("--dane")
    z.add_argument("--gpu", help="dir with <gpu>/<label>.jsonl.gz copies for the cross-GPU control")
    z.add_argument("--wygaszanie", help="dir with the annealing run's held-out files (default slayer-1b/wygaszanie/wyniki)")
    z.add_argument("--wyjscie", default=str(WYNIKI / "checkpoints.json"))
    r = sub.add_parser("raport")
    r.add_argument("--liczby", default=str(KORZEN / "results/LICZBY.json"))
    r.add_argument("--katalog", default=str(WYNIKI))
    a = p.parse_args(argv)
    if a.cmd == "zbierz":
        stare = Path(a.wyjscie)
        # rebuilt without the GPU copies (not in the repo): keep the recorded cross-GPU control
        zapas = json.loads(stare.read_text()).get("kontrola_gpu", []) if stare.exists() else []
        out = zbierz(a.surowe, a.dane, a.gpu, a.wygaszanie, kontrola_gpu_zapas=zapas)
        Path(a.wyjscie).write_text(json.dumps(out, indent=1) + "\n")
        print(json.dumps({k: out.get(k) for k in ("kontrola_urzadzenia", "nachylenie")}, default=str)[:2000])
    else:
        from checkpoints_report import raport
        raport(Path(a.liczby), Path(a.katalog))
    return 0


if __name__ == "__main__":
    sys.exit(main())
