"""Independent recomputation of the key numbers of benchmarks/blimp/results/checkpoints.json and LICZBY.json
from the raw files.

Gate (g) of sprawdz_raporty.py regenerates the report with the same generator, so it cannot catch an error in
benchmarks/blimp/checkpoints.py itself. This file does NOT import checkpoints or blimp: it re-reads the per-pair
files (benchmarks/blimp/results/checkpoints, benchmarks/blimp/results/<model>), the held-out windows and the
annealing references, recomputes with numpy and its own constants, and compares with tolerance 1e-9
(z and t: 1e-6 relative).
Run: python tests/test_blimp_checkpoints_independent.py (or pytest).
"""
import gzip
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pytest

KORZEN = Path(__file__).resolve().parent.parent
RAW = KORZEN / "benchmarks/blimp/results/checkpoints"
KRZYWA = KORZEN / "benchmarks/blimp/results/checkpoints.json"
WYG = KORZEN / "slayer-1b/wygaszanie/wyniki"
# written here again on purpose (not imported): CHECKPOINTS_THRESHOLDS.md and amendment 1
GLOWNE = [7150, 8600, 10010, 13848]
TOKENY_NA_KROK = 256 * 4096
TOL = 1e-9
# the 7 BLiMP pairs whose two sentences are identical (nyu-mll/blimp @ 877fba08, read from the parquet files);
# they count as correct even when batching makes the two log-likelihoods differ in the last bits
IDENTYCZNE = {"blimp_passive_1/324", "blimp_passive_1/810", "blimp_principle_A_case_2/105",
              "blimp_principle_A_case_2/287", "blimp_principle_A_case_2/372", "blimp_principle_A_case_2/816",
              "blimp_principle_A_case_2/967"}

pytestmark = pytest.mark.skipif(not KRZYWA.exists(), reason="no benchmarks/blimp/results/checkpoints.json")


def wczytaj(p):
    """{paradigm: {pair id: hit}}; hit = ll(gold) >= ll(other): a tie and identical sentences count as correct."""
    out = {}
    with gzip.open(p, "rt") as f:
        for l in f:
            d = json.loads(l)
            g, ll = d["gold"], d["ll"]
            out.setdefault(d["grupa"], {})[d["id"]] = 1.0 if d["id"] in IDENTYCZNE or ll[g] >= ll[1 - g] else 0.0
    return out


_cache = {}


def model(e):
    if e not in _cache:
        p = KORZEN / "benchmarks/blimp/results/pythia-1b/blimp.jsonl.gz" if e == "pythia" else RAW / f"{e}.jsonl.gz"
        _cache[e] = wczytaj(p)
    return _cache[e]


def acc_paradygmatow(e):
    m = model(e)
    return {g: float(np.mean(list(v.values()))) for g, v in sorted(m.items())}


def acc(e):
    return float(np.mean(list(acc_paradygmatow(e).values())))


def ols_wagi(x):
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / ((x - x.mean()) ** 2).sum()


def slope_i_klastr(kroki):
    x = [s * TOKENY_NA_KROK / 1e9 for s in kroki]
    w = ols_wagi(x)
    pa = [acc_paradygmatow(f"k{s}") for s in kroki]
    per = np.array([float(sum(wi * p[g] for wi, p in zip(w, pa))) for g in pa[0]])
    se = per.std(ddof=1) / math.sqrt(len(per))
    return per.mean(), se, per.mean() / se


def kr():
    return json.loads(KRZYWA.read_text())


def blisko(a, b, tol=TOL, rel=False):
    assert a is not None, "missing value"
    if rel:
        assert math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-9), (a, b)
    else:
        assert abs(a - b) <= tol, (a, b)


def test_acc_tokeny_i_luka():
    k = kr()
    pk = {p["etykieta"]: p for p in k["punkty"]}
    for e, p in pk.items():
        blisko(p["acc"], acc(e))
        blisko(p["mld"], p["krok"] * TOKENY_NA_KROK / 1e9)
        blisko(p["luka_pythia"]["roznica"], acc(e) - acc("pythia"))
    blisko(k["pythia_acc"], acc("pythia"))
    assert [p["krok"] for p in k["punkty"] if p["glowny_bieg"]] == GLOWNE


def test_nachylenie_glowne_i_klastr():
    n = kr()["nachylenie"]
    b, se, t = slope_i_klastr(GLOWNE)
    blisko(n["nachylenie"], b)
    blisko(n["se_klastr"], se)
    blisko(n["t"], t, rel=True)
    assert n["df"] == 66


def test_nachylenie_bez_ostatniego_i_reszty():
    k = kr()
    b, se, t = slope_i_klastr(GLOWNE[:-1])
    blisko(k["nachylenie_bez_ostatniego"]["nachylenie"], b)
    blisko(k["nachylenie_bez_ostatniego"]["t"], t, rel=True)
    x = np.array([s * TOKENY_NA_KROK / 1e9 for s in GLOWNE])
    y = np.array([acc(f"k{s}") for s in GLOWNE])
    bb, a0 = np.polyfit(x, y, 1)
    res = y - (a0 + bb * x)
    se_r = math.sqrt((res ** 2).sum() / (len(x) - 2) / ((x - x.mean()) ** 2).sum())
    r = k["nachylenie_reszty"]
    blisko(r["nachylenie"], bb)
    blisko(r["se_reszty"], se_r)
    blisko(r["t"], bb / se_r, rel=True)
    assert r["df"] == 2


ARGUMENT_STRUCTURE = ["animate_subject_passive", "animate_subject_trans", "causative", "drop_argument", "inchoative",
                      "intransitive", "passive_1", "passive_2", "transitive"]


def test_zjawisko_reszty_i_kroki_argument_structure():
    r = kr()["nachylenie_zjawiska"]["argument_structure"]
    x = np.array([s * TOKENY_NA_KROK / 1e9 for s in GLOWNE])
    y = np.array([np.mean([acc_paradygmatow(f"k{s}")[g] for g in ARGUMENT_STRUCTURE]) for s in GLOWNE])
    bb, a0 = np.polyfit(x, y, 1)
    res = y - (a0 + bb * x)
    se = math.sqrt((res ** 2).sum() / 2 / ((x - x.mean()) ** 2).sum())
    blisko(r["reszty"]["t"], bb / se, rel=True)
    for i, k in enumerate(r["kroki_sasiednie"]):
        blisko(k["roznica"], float(y[i + 1] - y[i]))


def test_przerwane_z_logow():
    import re
    ost = {}
    for p in sorted(RAW.glob("points_*.log")):
        krok = None
        for l in p.read_text().replace("\r", "\n").splitlines():
            m = re.match(r'\{"step": (\d+)', l)
            if m:
                krok = int(m.group(1))
            m = re.match(r"\[blimp\] (\d+)/(\d+)", l)
            if m and krok:
                ost[krok] = (int(m.group(1)), int(m.group(2)))
    oczek = {s: z for s, (z, w) in ost.items() if z < w}
    assert {r["krok"]: r["pary"] for r in kr()["przerwane"]} == oczek
    assert oczek == {5720: 35840, 11450: 18240}


def test_kroki_wszystkie_pary():
    k = kr()
    pary = {(r["od"], r["do"]): r for r in k["kroki"]}
    assert set(pary) == set(combinations(GLOWNE, 2))
    for (a, b), r in pary.items():
        pa, pb = acc_paradygmatow(f"k{a}"), acc_paradygmatow(f"k{b}")
        d = np.array([pb[g] - pa[g] for g in pa])
        blisko(r["roznica"], float(d.mean()))
        blisko(r["t"], float(d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))), rel=True)


def test_srednie_blimp_wobec_13848():
    k = kr()
    assert set(k["srednie"]) == {"avg3", "avg5", "avg10"}
    for e, r in k["srednie"].items():
        blisko(r["acc"], acc(e))
        blisko(r["blimp"]["roznica"], acc(e) - acc("k13848"))
        pe, p0 = acc_paradygmatow(e), acc_paradygmatow("k13848")
        d = np.array([pe[g] - p0[g] for g in pe])
        blisko(r["blimp"]["t"], float(d.mean() / (d.std(ddof=1) / math.sqrt(len(d)))), rel=True)


def test_sklad_srednich_z_logu():
    log = {json.loads(l)["model"]: sorted(json.loads(l)["kroki"])
           for l in (RAW / "averages.jsonl").read_text().splitlines() if l.strip()}
    assert log == {"avg3": [13750, 13800, 13848], "avg5": [13650, 13700, 13750, 13800, 13848],
                   "avg10": [13400 + 50 * i for i in range(9)] + [13848]}
    for e, r in kr()["srednie"].items():
        assert r["kroki"] == log[e] and r["sklad_zgodny_z_protokolem"] is True


def ho(p):
    return json.loads(Path(p).read_text())


def roznica_okien(a, b):
    assert [(o["komponent"], o["start"]) for o in a["okna"]] == [(o["komponent"], o["start"]) for o in b["okna"]]
    d = np.array([x["loss"] - y["loss"] for x, y in zip(a["okna"], b["okna"])])
    se = d.std(ddof=1) / math.sqrt(len(d))
    return float(d.mean()), float(se), float(d.mean() / se)


def test_heldout_srednie_udzialy_i_werdykt():
    k = kr()
    h = k["heldout"]
    m106, A, B = ho(RAW / "heldout_m106.json"), ho(WYG / "heldout_A.json"), ho(WYG / "heldout_B.json")
    a106 = roznica_okien(A, ho(WYG / "heldout_1.06.json"))[0]
    ab = roznica_okien(A, B)[0]
    blisko(h["wygaszanie_vs_1.06"], a106)
    blisko(h["wygaszanie_vs_staly"], ab)
    blisko(h["loss_1.06"], m106["loss"])
    ok = []
    for e in ("avg3", "avg5", "avg10"):
        r = h["srednie"][e]
        m, se, z = roznica_okien(ho(RAW / f"heldout_{e}.json"), m106)
        blisko(r["roznica"], m)
        blisko(r["se"], se)
        blisko(r["z"], z, rel=True)
        blisko(r["udzial_wygaszania"], m / a106)
        blisko(r["udzial_vs_staly"], m / ab)
        blisko(r["vs_wygaszanie"]["roznica"], roznica_okien(ho(RAW / f"heldout_{e}.json"), A)[0])
        if e in ("avg3", "avg5") and m <= 0.5 * -0.0504 and abs(z) >= 3:
            ok.append(e)
    assert h["werdykt_substytut"] == ("potwierdzone" if ok else "obalone")
    assert h["srednie_werdyktu"] == ["avg3", "avg5"]  # amendment 1: avg10 is not part of the verdict


def test_liczby_klastrowe_porownania_niosa_se_klastra():
    """LICZBY.json: the clustered slope comparison carries the paradigm SE (not the pair SE) and t as its z."""
    liczby = json.loads((KORZEN / "results/LICZBY.json").read_text())
    por = {p["id"]: p for p in liczby["porownania"]}
    b, se, t = slope_i_klastr(GLOWNE)
    p = por["krzywa/blimp_krzywa_nachylenie_klastr/acc"]
    blisko(p["se_parowane"], se)
    blisko(p["z_parowane"], t, rel=True)
    blisko(por["krzywa/blimp_krzywa_nachylenie/acc"]["roznica"], b)
    blisko(por["avg3_vs_1.06/heldout_srednia/loss"]["roznica"],
           roznica_okien(ho(RAW / "heldout_avg3.json"), ho(RAW / "heldout_m106.json"))[0])


def test_liczby_json_rowne_zbuduj():
    """results/LICZBY.json is exactly what tools/liczby.py builds from the current inputs (no hand edits)."""
    sys.path.insert(0, str(KORZEN / "tools"))
    import liczby as Lz
    teraz = json.loads(json.dumps(Lz.zbuduj(), ensure_ascii=False))
    # equal up to the last bits of a float: math.hypot differs in the last digit between Python versions
    assert rowne(json.loads((KORZEN / "results/LICZBY.json").read_text()), teraz)


def rowne(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and math.isclose(a, b, rel_tol=1e-12)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(rowne(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(rowne(x, y) for x, y in zip(a, b))
    return a == b


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
