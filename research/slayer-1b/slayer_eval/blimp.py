"""BLiMP (EN, 67 paradigms x 1000 minimal pairs): data, panel selection, statistics, report.

Scoring itself goes through `hipoteza_formatu.py licz --zadania blimp` (one scorer for Slayer and
HF models, lm-eval pair encoding). This module holds the pure parts, tested in
tests/test_blimp.py without network or weights:

  python slayer_eval/blimp.py zbierz --wyniki <dir with <model>/blimp.jsonl> --wyjscie wyniki/blimp/blimp.json
  python slayer_eval/blimp.py raport          # wyniki/LICZBY.json -> wyniki/blimp/BLIMP.md + blimp.svg

Protocol and thresholds: wyniki/blimp/THRESHOLDS.md (written before the measurement).
"""

import argparse
import glob
import gzip
import hashlib
import json
import math
import os
import sys
from pathlib import Path

REPO = "nyu-mll/blimp"
REWIZJA = "877fba0801ffb7cbd8c39c1ff314a46f053f6036"
SEED = 20261028
BOOTSTRAP = 10000
PROG_PEWNE, PROG_PRAWDOPODOBNE = 3.0, 2.0
KORZEN = Path(__file__).resolve().parent.parent

# Mean of the 67 blimp_* acc values in EleutherAI/pythia, evals/pythia-v0/pythia-1b/zero-shot/
# pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json (v0 weights, old harness
# without the leading space). The v1 eval folders have no BLiMP; no other published value was found.
REFERENCJA_PYTHIA = {"wartosc": 0.8234328358208955, "prog": 0.02,
                     "zrodlo": "github.com/EleutherAI/pythia evals/pythia-v0/pythia-1b/zero-shot/"
                               "pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json",
                     "uwaga": "v0 weights and old harness (sentence scored without leading space)"}
# Space SlayerLab/Slayer1B-Benchmarks, results.json, T01 observation of SlayerLab/Slayer1B-1.06
SPACE_T01 = {"wartosc": 0.8407960199004975, "ci95": [0.8059701492537314, 0.8756218905472644], "n": 200,
             "source_id_digest": "9d6d5c8b444b57a4043af8030c77daca572418a54ace83cd6c16ebe8945faf67"}

# The 12 phenomena of Warstadt et al. 2020 (Table 4). The HF dataset labels the two
# animate_subject_* paradigms `s-selection`; the paper counts them under argument structure.
ZJAWISKO_HF = {"s-selection": "argument_structure"}


def zjawisko(linguistics_term):
    return ZJAWISKO_HF.get(linguistics_term, linguistics_term)


def dokument(rekord):
    """Row of the dataset -> scored document: two choices, gold = 0 (good sentence first)."""
    uid = rekord["UID"]
    return {"id": f"blimp_{uid}/{rekord['pair_id']}", "grupa": uid, "zjawisko": zjawisko(rekord["linguistics_term"]),
            "pytanie": "", "opcje": [rekord["sentence_good"], rekord["sentence_bad"]], "gold": 0,
            "rekord": rekord}


def katalog_danych():
    """Pinned snapshot: BLIMP_DIR or the HF cache of the pinned revision."""
    d = os.environ.get("BLIMP_DIR") or os.path.expanduser(
        f"~/.cache/huggingface/hub/datasets--nyu-mll--blimp/snapshots/{REWIZJA}")
    return Path(d)


def wczytaj(sciezka=None):
    """All BLiMP documents, paradigms sorted by name, pairs in file order.
    `sciezka` = snapshot directory with <UID>/train-*.parquet, or a .jsonl file with dataset rows."""
    sciezka = Path(sciezka) if sciezka else katalog_danych()
    if sciezka.suffix == ".jsonl":
        wiersze = [json.loads(l) for l in sciezka.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        import pyarrow.parquet as pq
        pliki = sorted(glob.glob(str(sciezka / "*" / "train-*.parquet")))
        if len(pliki) != 67:
            raise FileNotFoundError(f"BLiMP: expected 67 parquet files in {sciezka}, found {len(pliki)} (BLOCKED)")
        wiersze = [r for p in pliki for r in pq.read_table(p).to_pylist()]
    docs = [dokument(r) for r in wiersze]
    docs.sort(key=lambda d: d["grupa"])  # stable: file order inside a paradigm
    return docs


# ---------------------------------------------------------------- panel200 (METHOD.md section 3)

def kanoniczny(rekord):
    return json.dumps(rekord, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def id_zrodla(rekord, wariant):
    """Source id in the selection hash. The Space does not publish its definition for BLiMP,
    so both readings of METHOD.md are kept: the native `pair_id`, or SHA-256 of the canonical row."""
    if wariant == "pair_id":
        return str(rekord["pair_id"])
    if wariant == "sha256":
        return hashlib.sha256(kanoniczny(rekord).encode()).hexdigest()
    raise ValueError(wariant)


def klucz_wyboru(benchmark_id, member, source_id):
    return hashlib.sha256(f"{SEED}|{benchmark_id}|{member}|{source_id}".encode()).hexdigest()


def panel(docs, wariant="pair_id", budzet=200, benchmark_id="blimp"):
    """Documents of the panel: min(2, N) per member, the rest by largest deficit against
    budget x weight (equal weights), ties by member task name; inside a member the smallest hash."""
    czlonkowie = {}
    for d in docs:
        czlonkowie.setdefault(f"blimp_{d['grupa']}", []).append(d)
    kolejki = {m: sorted(ds, key=lambda d: (klucz_wyboru(benchmark_id, m, id_zrodla(d["rekord"], wariant)),
                                             kanoniczny(d["rekord"])))
               for m, ds in czlonkowie.items()}
    przydzial = {m: min(2, len(ds)) for m, ds in kolejki.items()}
    waga = 1 / len(kolejki)
    while sum(przydzial.values()) < min(budzet, len(docs)):
        wolni = [m for m in kolejki if przydzial[m] < len(kolejki[m])]
        m = min(wolni, key=lambda m: (-(budzet * waga - przydzial[m]), m))
        przydzial[m] += 1
    return [d for m in sorted(kolejki) for d in kolejki[m][:przydzial[m]]]


def wartosc_grupy(trafienia, grupy):
    """Mean of member accuracies with equal member weights (lm-eval group `blimp`, weight_by_size False)."""
    po = {}
    for t, g in zip(trafienia, grupy):
        po.setdefault(g, []).append(t)
    return sum(sum(v) / len(v) for v in po.values()) / len(po)


# ---------------------------------------------------------------- statistics

def trafienie(ll):
    """lm-eval acc: argmax over [good, bad]; a tie picks the first choice (good) = correct."""
    return 1 if ll[0] >= ll[1] else 0


def werdykt(z):
    if z is None:
        return None
    a = abs(z)
    return "pewne" if a >= PROG_PEWNE else "prawdopodobne" if a >= PROG_PRAWDOPODOBNE else "szum"


def wilson(k, n, z=1.959963984540054):
    p = k / n
    m = 1 + z * z / n
    c = (p + z * z / (2 * n)) / m
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / m
    return c - h, c + h


def se_proporcji(p, n):
    return math.sqrt(p * (1 - p) / n)


def _wariancja(xs):
    n = len(xs)
    m = sum(xs) / n
    return sum((x - m) ** 2 for x in xs) / (n - 1) if n > 1 else 0.0


def se_warstwowe(warstwy):
    """SE of the equal-weight mean of stratum means: sqrt(sum var_k / n_k) / K."""
    K = len(warstwy)
    return math.sqrt(sum(_wariancja(x) / len(x) for x in warstwy)) / K


def bootstrap_ci(warstwy, powtorzen=BOOTSTRAP, seed=SEED):
    """CI95 of the equal-weight mean of stratum means, resampling within strata (percentile)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    srednie = np.zeros(powtorzen)
    # Data take few distinct values (0/1, or -1/0/1 for paired differences): resampling n items
    # with replacement is exactly a multinomial draw over the value counts.
    for x in warstwy:
        wart = sorted(set(x))
        liczn = [x.count(v) for v in wart]
        n = len(x)
        los = rng.multinomial(n, [c / n for c in liczn], size=powtorzen)
        srednie += (los * np.array(wart, dtype=np.int64)).sum(axis=1) / n
    srednie /= len(warstwy)
    lo, hi = np.percentile(srednie, [2.5, 97.5])
    return float(lo), float(hi)


def wczytaj_wyniki(plik):
    """<model>/blimp.jsonl from hipoteza_formatu (gzip allowed) -> {id: row}."""
    otworz = gzip.open if str(plik).endswith(".gz") else open
    with otworz(plik, "rt") as f:
        return {w["id"]: w for w in (json.loads(l) for l in f if l.strip())}


def statystyki_modelu(wiersze, docs, bootstrap=True):
    po_gr, po_zj = {}, {}
    for d in docs:
        t = trafienie(wiersze[d["id"]]["ll"])
        po_gr.setdefault(d["grupa"], []).append(t)
        po_zj.setdefault(d["zjawisko"], {}).setdefault(d["grupa"], []).append(t)
    warstwy = [po_gr[g] for g in sorted(po_gr)]
    acc = sum(sum(x) / len(x) for x in warstwy) / len(warstwy)
    out = {"n": sum(len(x) for x in warstwy), "n_paradygmatow": len(warstwy), "acc": acc,
           "se": se_warstwowe(warstwy), "baza_losowa": 0.5, "baza_wiekszosciowa": None,
           "baza_wiekszosciowa_uwaga": "not applicable: gold is always the first choice by construction"}
    if bootstrap:
        out["ci95"] = list(bootstrap_ci(warstwy))
    out["paradygmaty"] = {}
    for g in sorted(po_gr):
        x = po_gr[g]
        k, n = sum(x), len(x)
        out["paradygmaty"][g] = {"n": n, "acc": k / n, "se": se_proporcji(k / n, n), "ci95": list(wilson(k, n))}
    out["zjawiska"] = {}
    for z in sorted(po_zj):
        w = [po_zj[z][g] for g in sorted(po_zj[z])]
        a = sum(sum(x) / len(x) for x in w) / len(w)
        s = se_warstwowe(w)
        out["zjawiska"][z] = {"n": sum(len(x) for x in w), "n_paradygmatow": len(w), "acc": a, "se": s,
                              "ci95": [a - 1.959963984540054 * s, a + 1.959963984540054 * s]}
    return out


def porownanie_parowane(wa, wb, docs):
    """Slayer - Pythia on the same pairs: overall, per phenomenon, per paradigm; paired SE, z, verdict."""
    po_gr, zj_gr = {}, {}
    for d in docs:
        r = trafienie(wa[d["id"]]["ll"]) - trafienie(wb[d["id"]]["ll"])
        po_gr.setdefault(d["grupa"], []).append(r)
        zj_gr[d["grupa"]] = d["zjawisko"]

    def wpis(warstwy):
        dlt = sum(sum(x) / len(x) for x in warstwy) / len(warstwy)
        se = se_warstwowe(warstwy)
        z = dlt / se if se > 0 else None
        return {"roznica": dlt, "se": se, "z": z, "werdykt": werdykt(z)}

    out = {"ogolem": wpis([po_gr[g] for g in sorted(po_gr)]), "zjawiska": {}, "paradygmaty": {}}
    for z in sorted(set(zj_gr.values())):
        out["zjawiska"][z] = wpis([po_gr[g] for g in sorted(po_gr) if zj_gr[g] == z])
    for g in sorted(po_gr):
        out["paradygmaty"][g] = wpis([po_gr[g]])
    return out


# ---------------------------------------------------------------- commands

def cmd_zbierz(a):
    docs = wczytaj(a.dane)
    modele = {}
    for m in a.modele.split(","):
        plik = Path(a.wyniki) / m / "blimp.jsonl"
        modele[m] = wczytaj_wyniki(plik if plik.exists() else Path(a.wyniki) / f"{m}.jsonl.gz")  # raw/ in the repo
        brak = [d["id"] for d in docs if d["id"] not in modele[m]]
        if brak:
            raise SystemExit(f"{m}: {len(brak)} pairs without a result (first {brak[0]})")
    out = {"zbior": {"repo": REPO, "rewizja": REWIZJA, "n": len(docs)}, "modele": {}, "panel_space": {}}
    for m, w in modele.items():
        out["modele"][m] = statystyki_modelu(w, docs)
    a_, b_ = a.modele.split(",")[:2]
    out["porownanie"] = {"a": a_, "b": b_, **porownanie_parowane(modele[a_], modele[b_], docs)}
    for wariant in ("pair_id", "sha256"):
        p = panel(docs, wariant)
        out["panel_space"][wariant] = {
            "n": len(p), **{m: wartosc_grupy([trafienie(w[d["id"]]["ll"]) for d in p], [d["grupa"] for d in p])
                            for m, w in modele.items()}}
    if "pythia-1b" in out["modele"]:
        nasza = out["modele"]["pythia-1b"]["acc"]
        out["kontrola_pythia"] = {**REFERENCJA_PYTHIA, "nasza": nasza, "roznica": nasza - REFERENCJA_PYTHIA["wartosc"],
                                  "w_progu": abs(nasza - REFERENCJA_PYTHIA["wartosc"]) <= REFERENCJA_PYTHIA["prog"]}
    if "1.06" in out["modele"]:
        out["space"] = {"wartosc": SPACE_T01["wartosc"], "ci95": SPACE_T01["ci95"], "n": SPACE_T01["n"],
                        "digest_odtworzony": False,
                        "uwaga": "no id/separator/order format tried reproduces the Space source_id_digest"}
        for wariant, p in out["panel_space"].items():
            p["roznica_1.06_do_space"] = p["1.06"] - SPACE_T01["wartosc"]
            p["w_ci95_space"] = SPACE_T01["ci95"][0] <= p["1.06"] <= SPACE_T01["ci95"][1]
            p["rowna_space"] = abs(p["roznica_1.06_do_space"]) < 1e-9
    Path(a.wyjscie).parent.mkdir(parents=True, exist_ok=True)
    Path(a.wyjscie).write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({m: (s["acc"], s["ci95"]) for m, s in out["modele"].items()}))


def main(argv=None):
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    z = sub.add_parser("zbierz")
    z.add_argument("--wyniki", required=True)
    z.add_argument("--modele", default="1.06,pythia-1b")
    z.add_argument("--dane")
    z.add_argument("--wyjscie", default=str(KORZEN / "wyniki/blimp/blimp.json"))
    r = sub.add_parser("raport")
    r.add_argument("--liczby", default=str(KORZEN / "wyniki/LICZBY.json"))
    r.add_argument("--katalog", default=str(KORZEN / "wyniki/blimp"))
    a = p.parse_args(argv)
    if a.cmd == "zbierz":
        cmd_zbierz(a)
    else:
        from blimp_raport import raport
        raport(Path(a.liczby), Path(a.katalog))
    return 0


if __name__ == "__main__":
    sys.exit(main())
