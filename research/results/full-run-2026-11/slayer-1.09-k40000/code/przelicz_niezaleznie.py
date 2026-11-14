"""Niezależne przeliczenie kluczowych liczb LICZBY.json z surowych próbek, bez importu raport.py, metryki.py,
statystyka.py i ewaluuj.py: wynik pytania z pola metryki zapisanego przez lm_eval (EWoK z loglików, WikiText z
logliku i bajtów dokumentu), klastry z pól dokumentów własnym kodem, p z rozkładów scipy, Holm z m = 15.

    python przelicz_niezaleznie.py <eksport z próbkami> <LICZBY.json> [<wynik.json>]

Kod 0: każdy test ma Δ równe LICZBY.json do 1e-9, SE Δ do 1e-6 względnie, ten sam werdykt po Holmie i ten sam wynik
końcowy; kod 1: rozjazd (lista w wyniku). Rozjazd podziału lepsze/gorsze/szum obala główne twierdzenie (PROTOKOL.md).
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from scipy import stats

A, B = "slayer1b-1.09-k40000", "slayer1b-1.08"
METRYKA = {"arc-challenge": "acc_norm", "arc-easy": "acc", "blimp": "acc", "hellaswag": "acc_norm", "lambada": "acc",
           "mathqa": "acc_norm", "medmcqa": "acc", "multiblimp-pl": "acc", "piqa": "acc_norm", "pubmedqa": "acc",
           "social-iqa": "acc", "winogrande": "acc", "wsc273": "acc", "ewok": "ewok", "wikitext-2": "bpb"}
WYZEJ_LEPIEJ = {b: b != "wikitext-2" for b in METRYKA}
M = 15
P3, P2 = 2 * stats.norm.sf(3), 2 * stats.norm.sf(2)


def probki(eksport, bench, model):
    d = eksport / "wyniki" / bench / model / "probki"
    pliki = sorted(d.glob("*_space.jsonl")) or sorted(d.glob("ewok.jsonl"))
    rek = [json.loads(l) for l in pliki[0].read_text(encoding="utf-8").splitlines()]
    klucz = "doc_id" if "doc_id" in rek[0] else "id"
    return {r[klucz]: r for r in rek}


def wynik_pytania(bench, r):
    if bench == "ewok":
        ll = r["ll"]
        return ((ll[0][0] > ll[1][0]) + (ll[1][1] > ll[0][1])) / 2
    return float(r[METRYKA[bench]])


def klastry(bench, klucze, rek, szablony):
    docs = [rek[k]["doc"] for k in klucze] if bench != "ewok" else None
    if bench == "blimp":
        return [d["UID"] for d in docs]
    if bench == "winogrande":
        ids, i, c = [], 0, 0
        while i < len(docs):
            para = i + 1 < len(docs) and {docs[i]["option1"], docs[i]["option2"]} == {docs[i + 1]["option1"], docs[i + 1]["option2"]}
            ids += [c] * (2 if para else 1)
            i += 2 if para else 1
            c += 1
        return ids
    if bench == "wsc273":
        slowa = lambda t: set(re.sub(r"[.,]", " ", t.lower()).split())
        ids, g = [], 0
        for i, d in enumerate(docs):
            if i:
                a, b = slowa(d["text"]), slowa(docs[i - 1]["text"])
                g += len(a & b) / len(a | b) < 0.6
            ids.append(g)
        return ids
    if bench == "ewok":
        return [szablony[rek[k]["source_id"]] for k in klucze]
    return None


def szablony_ewok():
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download("ewok-core/ewok-core-1.0", "data/test/ewok-core-1.0.parquet", repo_type="dataset",
                        revision="34d912a608066c92e2990a0328ffc3bd9a716042")
    recs = pd.read_parquet(p).to_dict("records")
    pola = ("Context1", "Context2", "Target1", "Target2")
    grupy = defaultdict(list)
    for i, r in enumerate(recs):
        grupy[(r["ConceptA"], r["ConceptB"], r["Domain"])].append((i, r))
    klucze = {}
    for g, xs in grupy.items():
        df = Counter(w for _, x in xs for w in set(re.findall(r"[A-Za-z']+", " ".join(x[f] for f in pola))))
        for i, x in xs:
            klucze[i] = (g,) + tuple(" ".join(w if df[w] >= 0.3 * len(xs) else "_" for w in re.findall(r"[A-Za-z']+", x[f]))
                                     for f in pola)
    numer = {k: n for n, k in enumerate(sorted(set(klucze.values())))}
    return {i: numer[k] for i, k in klucze.items()}


def se_klastrowe(d, kl, wagi=None):
    """Średnia ważona i SE po klastrach: √(G/(G−1) Σ_c (Σ_{i∈c} w_i (d_i − d̄))²) / Σ w; t przy df = G − 1."""
    w = wagi or [1.0] * len(d)
    W = sum(w)
    m = sum(a * b for a, b in zip(w, d)) / W
    sumy = defaultdict(float)
    for a, b, c in zip(w, d, kl):
        sumy[c] += a * (b - m)
    G = len(sumy)
    if G < 2:
        return m, None, None, G - 1, None, G
    se = math.sqrt(sum(s * s for s in sumy.values()) * G / (G - 1)) / W
    t = m / se if se else None
    return m, se, t, G - 1, (2 * stats.t.sf(abs(t), G - 1) if t is not None else None), G


def porownaj(eksport, bench, szablony):
    pa, pb = probki(eksport, bench, A), probki(eksport, bench, B)
    klucze = sorted(pa)
    assert klucze == sorted(pb), bench
    if bench == "wikitext-2":
        bajty = [pa[k]["byte_perplexity"][1] for k in klucze]
        d = [-(pa[k]["filtered_resps"][0] - pb[k]["filtered_resps"][0]) / (math.log(2) * b) for k, b in zip(klucze, bajty)]
        m, se, t, df, p, G = se_klastrowe(d, klucze, bajty)
        bpp = lambda P: math.exp(-sum(P[k]["filtered_resps"][0] for k in klucze) / sum(bajty))
        return {"roznica": bpp(pa) - bpp(pb), "se": se, "t": t, "df": df, "p": p, "n": len(klucze)}
    xa = [wynik_pytania(bench, pa[k]) for k in klucze]
    xb = [wynik_pytania(bench, pb[k]) for k in klucze]
    d = [a - b for a, b in zip(xa, xb)]
    kl = klastry(bench, klucze, pa, szablony)
    if kl is not None:
        m, se, t, df, p, G = se_klastrowe(d, kl)
        return {"roznica": sum(xa) / len(xa) - sum(xb) / len(xb), "se": se, "t": t, "df": df, "p": p, "n": len(d)}
    n, m = len(d), sum(d) / len(d)
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n)
    z = m / se if se else None
    return {"roznica": sum(xa) / n - sum(xb) / n, "se": se, "z": z, "p": 2 * stats.norm.sf(abs(z)) if z is not None else None, "n": n}


def holm(ps, m=M):
    idx = sorted((i for i, p in enumerate(ps) if p is not None), key=lambda i: ps[i])
    out, mx = [None] * len(ps), 0.0
    for r, i in enumerate(idx):
        mx = max(mx, min(1.0, (m - r) * ps[i]))
        out[i] = mx
    return out


def werdykt(p):
    return "nierozstrzygalne" if p is None else "pewne" if p <= P3 else "prawdopodobne" if p <= P2 else "szum"


def main():
    eksport, liczby = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    szablony = szablony_ewok()
    testy = {t["benchmark"]: t for t in liczby["testy"]}
    wyniki = {b: porownaj(eksport, b, szablony) for b in testy}
    for b, p in zip(wyniki, holm([wyniki[b]["p"] for b in wyniki])):
        w = wyniki[b]
        w["p_holm"], w["werdykt_holm"] = p, werdykt(p)
        zgodna = testy[b]["kontrola"]["zgodna"]
        if not zgodna:
            w["wynik"] = "nierozstrzygnięte (kontrola narzędzia)"
        elif w["werdykt_holm"] in ("pewne", "prawdopodobne"):
            lepiej = (w["roznica"] > 0) == WYZEJ_LEPIEJ[b]
            w["wynik"] = f"{'lepszy' if lepiej else 'gorszy'} ({w['werdykt_holm']})"
        else:
            w["wynik"] = "szum" if p is not None else "nierozstrzygalne"
    rozjazdy = []
    for b, w in wyniki.items():
        L = testy[b]["porownanie"]
        if abs(w["roznica"] - L["roznica"]) > 1e-9:
            rozjazdy.append(f"{b}: Δ {w['roznica']} != {L['roznica']}")
        if (w["se"] is None) != (L["se"] is None) or (L["se"] and abs(w["se"] - L["se"]) > 1e-6 * L["se"]):
            rozjazdy.append(f"{b}: SE {w['se']} != {L['se']}")
        if w["werdykt_holm"] != L["werdykt_holm"]:
            rozjazdy.append(f"{b}: po Holmie {w['werdykt_holm']} != {L['werdykt_holm']}")
        if w["wynik"] != testy[b]["werdykt_koncowy"]:
            rozjazdy.append(f"{b}: wynik {w['wynik']} != {testy[b]['werdykt_koncowy']}")
    out = {"rozjazdy": rozjazdy, "testy": wyniki,
           "podzial": {k: sorted(b for b, w in wyniki.items() if w["wynik"].startswith(k)) for k in ("lepszy", "gorszy", "szum")}}
    tekst = json.dumps(out, ensure_ascii=False, indent=1)
    if len(sys.argv) > 3:
        Path(sys.argv[3]).write_text(tekst + "\n", encoding="utf-8")
    print("\n".join(rozjazdy) if rozjazdy else f"zgodne: {len(wyniki)} testów, podział {out['podzial']}")
    return 1 if rozjazdy else 0


if __name__ == "__main__":
    raise SystemExit(main())
