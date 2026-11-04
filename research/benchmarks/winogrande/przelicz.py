"""Builds results/winogrande.json from the three results/*/winogrande.jsonl.gz files.

Type `mc +klastry` (METODOLOGIA.md): clusters are twin pairs, i.e. adjacent validation items with the same
option set. Binding SE is SE K with a t test at df = k - 1; SE A stays as an informational column.

Run in research/:
  python benchmarks/winogrande/przelicz.py klastry   # HF validation split at the pinned revision -> klastry.json
  python benchmarks/winogrande/przelicz.py           # klastry.json + results/*/winogrande.jsonl.gz -> winogrande.json
"""
import gzip
import hashlib
import json
import math
import re
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
sys.path.insert(0, str(TU.parent.parent / "tools"))
from liczby import p_t, werdykt, werdykt_t  # noqa: E402

WYNIKI = TU / "results"
KLASTRY = TU / "klastry.json"
YAML = TU / "lm_eval_tasks" / "winogrande" / "default.yaml"
MODELE = {"pythia": "pythia-1b-v0", "pythia_bos": "pythia-1b-v0-bos", "slayer": "slayer-1.06"}
POROWNANIA = [("slayer", "pythia"), ("pythia_bos", "pythia"), ("slayer", "pythia_bos")]
P_PRAWDOPODOBNE = math.erfc(2 / math.sqrt(2))  # p for |z| = 2, the Holm threshold
# thresholds written in RECIPE.md before the runs
PROG = {"opublikowane": 0.5375, "se_karty": 0.014, "dwa_se": 0.028, "furtka_dol": 0.5095, "furtka_gora": 0.5655,
        "pasmo_2pkt_dol": 0.5175, "pasmo_2pkt_gora": 0.5575, "pasmo_slayer_dol": 0.505, "pasmo_slayer_gora": 0.584,
        "pythia_skrot": 0.5446, "se_roznicy_niezaleznej": 0.0198}


def rewizja():
    return re.search(r"revision:\s*(\w+)", YAML.read_text()).group(1)


def klastry_z_opcji(opcje):
    """opcje: [(option1, option2)] in split order. Adjacent items with the same option set share a cluster id."""
    ids, i, c = [], 0, 0
    while i < len(opcje):
        if i + 1 < len(opcje) and set(opcje[i]) == set(opcje[i + 1]):
            ids += [c, c]
            i += 2
        else:
            ids.append(c)
            i += 1
        c += 1
    return ids


def cmd_klastry():
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq

    rev = rewizja()
    plik = hf_hub_download("allenai/winogrande", "winogrande_xl/validation-00000-of-00001.parquet",
                           repo_type="dataset", revision=rev)
    wiersze = pq.read_table(plik).to_pylist()
    ids = klastry_z_opcji([(r["option1"], r["option2"]) for r in wiersze])
    rozmiary = [ids.count(c) for c in range(ids[-1] + 1)]
    KLASTRY.write_text(json.dumps({
        "zbior": "allenai/winogrande winogrande_xl validation", "rewizja": rev,
        "sha256_parquet": hashlib.sha256(Path(plik).read_bytes()).hexdigest(),
        "zloto": [int(r["answer"]) for r in wiersze],
        "pary": rozmiary.count(2), "pojedyncze": rozmiary.count(1), "k": len(rozmiary), "klaster": ids,
    }) + "\n")
    print(f"n {len(ids)}, par {rozmiary.count(2)}, pojedynczych {rozmiary.count(1)}, k {len(rozmiary)}")


def wczytaj(katalog):
    with gzip.open(WYNIKI / katalog / "winogrande.jsonl.gz", "rt") as f:
        wiersze = sorted((json.loads(x) for x in f), key=lambda r: r["doc_id"])
    assert [r["doc_id"] for r in wiersze] == list(range(len(wiersze)))
    return wiersze


def se_a(x):
    n = len(x)
    m = sum(x) / n
    return math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1) / n)


def se_k(x, klaster):
    n, m, sumy = len(x), sum(x) / len(x), {}
    for c, v in zip(klaster, x):
        sumy[c] = sumy.get(c, 0.0) + v - m
    k = len(sumy)
    return math.sqrt(k / (k - 1) * sum(s * s for s in sumy.values())) / n


def roznica(x, y, klaster):
    """Paired a - b per item: SE K with t at df = k - 1 (binding), SE A with z (informational)."""
    d = [a - b for a, b in zip(x, y)]
    m, sk, sa = sum(d) / len(d), se_k(d, klaster), se_a(d)
    df = len(set(klaster)) - 1
    return {"roznica": m, "se_k": sk, "t": m / sk, "df": df, "p": p_t(m / sk, df), "werdykt": werdykt_t(m / sk, df),
            "se_a": sa, "z": m / sa, "werdykt_a": werdykt(m / sa)}


def holm(wyniki):
    """Holm step-down on the p of each comparison; 'tak' when the adjusted p is at most p(|z| = 2)."""
    kolejnosc = sorted(wyniki, key=lambda r: r["p"])
    m, biezace = len(kolejnosc), 0.0
    for i, r in enumerate(kolejnosc):
        biezace = max(biezace, min(1.0, (m - i) * r["p"]))
        r["p_holm"] = biezace
        r["po_holmie"] = "tak" if biezace <= P_PRAWDOPODOBNE else "nie"


def main():
    kl = json.loads(KLASTRY.read_text())
    klaster, zloto = kl["klaster"], kl["zloto"]
    out, acc = {}, {}
    for klucz, katalog in MODELE.items():
        wiersze = wczytaj(katalog)
        assert [r["gold"] for r in wiersze] == zloto, katalog + ": gold differs from the split"
        pred = [1 if r["logliki"][0] >= r["logliki"][1] else 2 for r in wiersze]  # tie takes option 1, as lm-eval
        assert pred == [r["pred"] for r in wiersze], katalog + ": pred differs from logliki"
        x = [float(p == g) for p, g in zip(pred, zloto)]
        acc[klucz] = x
        n, n1 = len(x), pred.count(1)
        out[klucz] = {"acc": sum(x) / n, "se_a": se_a(x), "se_k": se_k(x, klaster), "n": n, "k": kl["k"],
                      "correct": int(sum(x)), "pred_n1": n1, "pred_n2": n - n1,
                      "majority_prediction_share": max(n1, n - n1) / n}
    n = len(zloto)
    n2 = zloto.count(2)
    stala = [float(g == 2) for g in zloto]  # "always option 2", the more frequent gold position
    out["bazy"] = {"losowa": 0.5, "wiekszosciowa": n2 / n, "wiekszosciowa_n2": n2}
    out["klastry"] = {"pary": kl["pary"], "pojedyncze": kl["pojedyncze"], "k": kl["k"], "df": kl["k"] - 1}
    out["prog"] = PROG
    porownania = {f"{a}_minus_{b}": roznica(acc[a], acc[b], klaster) for a, b in POROWNANIA}
    holm(list(porownania.values()))
    out.update(porownania)
    for klucz in ("pythia", "slayer"):
        out[f"{klucz}_wobec_b"] = roznica(acc[klucz], stala, klaster)
    d = out["pythia"]["acc"] - PROG["opublikowane"]
    out["pythia_wobec_opublikowanego"] = {"roznica": d, "se_k": out["pythia"]["se_k"],
                                          "t": d / out["pythia"]["se_k"], "df": kl["k"] - 1,
                                          "werdykt": werdykt_t(d / out["pythia"]["se_k"], kl["k"] - 1)}
    (WYNIKI / "winogrande.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    for nazwa in list(porownania) + ["pythia_wobec_b", "slayer_wobec_b"]:
        r = out[nazwa]
        print(f"{nazwa}: {r['roznica']:+.6f} SE K {r['se_k']:.6f} t {r['t']:.3f} p {r['p']:.3f} {r['werdykt']}"
              f" | SE A {r['se_a']:.6f} z {r['z']:.3f}" + (f" | Holm {r['po_holmie']}" if "po_holmie" in r else ""))


if __name__ == "__main__":
    cmd_klastry() if sys.argv[1:] == ["klastry"] else main()
