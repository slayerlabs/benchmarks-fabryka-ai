"""Niezależne przeliczenie kluczowych liczb LICZBY.json z surowych próbek, bez importu raport.py, metryki.py,
statystyka.py i ewaluuj.py: wynik pytania własnym kodem (acc z pola lm_eval; acc_norm z loglików i kontynuacji w
definicji runnera i pełnego przebiegu: loglik / długość kontynuacji bez wiodących spacji, remis → pierwszy indeks;
EWoK z loglików, WikiText z logliku i bajtów dokumentu), klastry z pól dokumentów, p z rozkładów scipy, Holm z m = 15.

    python przelicz_niezaleznie.py <eksport z próbkami> <LICZBY.json> <manifest.jsonl przebiegu> <probki_sha256.json>
                                   [<wynik.json>]

Eksport z próbkami: rozpakowana paczka albo katalog złożony z plików repo przez `dolacz_wyniki.py odtworz`.
Najpierw sha256 wejść: każdy plik `wyniki/` eksportu wobec probki_sha256.json, a sha256 probki_sha256.json i manifestu
wobec pola `wejscia` LICZBY.json; różnica → kod 2, nic nie liczone.
Kod 0: każdy test ma Δ równe LICZBY.json do 1e-9, SE Δ do 1e-6 względnie, p Holma do 1e-6 względnie, ten sam werdykt
po Holmie, tę samą kontrolę narzędzia (1.08 z próbek wobec manifestu przebiegu, policzoną tu od nowa), ten sam wynik
końcowy, te same liczby remisów co `eksploracyjne.remisy` i to samo rozbicie BLiMP/MultiBLiMP-PL/EWoK
(`eksploracyjne.rozbicie`: n, Δ, CI95 obu etykiet, p Holma z m = liczba grup, werdykt); kod 1: rozjazd (lista w wyniku). Rozjazd podziału
lepsze/gorsze/szum obala główne twierdzenie (PROTOKOL.md). Obok, bez wpływu na kod: Δ acc_norm w definicji lm_eval
(pole próbki; długość wyboru ze spacjami), bo na HellaSwag różni się od definicji runnera (problem pełnego przebiegu).

Zmiana po wyniku (runda poprawek 1): wcześniej acc_norm brany z pola lm_eval; dzięki temu przeliczenie liczy tę samą
definicję co protokół (wartość z pliku wyników przebiegu), a różnica definicji stoi osobno.
"""
import hashlib
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


def pierwszy_max(x):
    """Indeks największej wartości; przy remisie pierwszy (reguła runnera)."""
    best = 0
    for i, v in enumerate(x):
        if v > x[best]:
            best = i
    return best


def opcje(r):
    """(logliki warunkowe, kontynuacje, indeks poprawnej) z próbki lm_eval; zadania z PMI mają w drugiej połowie
    logliki bezwarunkowe, cel jest indeksem, tekstem wyboru albo polem `gold` (wiele kontekstów)."""
    lls = [float(x[0]) for x in r["filtered_resps"]]
    k = len(lls) // 2 if "acc_mutual_info" in r["metrics"] else len(lls)
    konty = [a[1] for a in r["arguments"][:k]]
    if "gold" in r:
        gold = int(r["gold"])
    else:
        try:
            gold = int(r["target"])
        except (TypeError, ValueError):
            gold = [c.strip() for c in konty].index(str(r["target"]).strip())
    return lls[:k], konty, gold


def acc_norm_runnera(r):
    lls, konty, gold = opcje(r)
    return float(pierwszy_max([ll / max(len(c.lstrip(" ")), 1) for ll, c in zip(lls, konty)]) == gold)


def remis(r, metryka):
    """(remis przy maksimum, remis obejmuje poprawną) w regule wyboru metryki."""
    lls, konty, gold = opcje(r)
    s = lls if metryka == "acc" else [ll / max(len(c.lstrip(" ")), 1) for ll, c in zip(lls, konty)]
    rowne = [i for i, v in enumerate(s) if v == max(s)]
    return len(rowne) > 1, len(rowne) > 1 and gold in rowne


def wynik_pytania(bench, r):
    if bench == "ewok":
        ll = r["ll"]
        return ((ll[0][0] > ll[1][0]) + (ll[1][1] > ll[0][1])) / 2
    if METRYKA[bench] == "acc_norm":
        return acc_norm_runnera(r)
    return float(r[METRYKA[bench]])


def sha256_pliku(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for kawalek in iter(lambda: f.read(1 << 20), b""):
            h.update(kawalek)
    return h.hexdigest()


def sprawdz_wejscia(eksport, liczby, manifest_p, sumy_p):
    """Lista niezgodności sha256 wejść (pusta = zgodne)."""
    bledy = []
    w = liczby.get("wejscia") or {}
    if sha256_pliku(sumy_p) != w.get("probki_sha256"):
        bledy.append(f"{sumy_p.name}: sha256 różne od LICZBY.json wejscia.probki_sha256")
    if sha256_pliku(manifest_p) != w.get("manifest_przebiegu"):
        bledy.append(f"{manifest_p.name}: sha256 różne od LICZBY.json wejscia.manifest_przebiegu")
    spis = json.loads(sumy_p.read_text(encoding="utf-8"))["pliki"]
    pliki = {p.relative_to(eksport).as_posix() for p in (eksport / "wyniki").rglob("*") if p.is_file()}
    if pliki != set(spis):
        bledy.append(f"pliki eksportu różne od spisu: nadmiar {sorted(pliki - set(spis))[:3]}, "
                     f"brak {sorted(set(spis) - pliki)[:3]}")
    bledy += [f"{p}: sha256 różne od spisu" for p in sorted(pliki & set(spis)) if sha256_pliku(eksport / p) != spis[p]]
    return bledy


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


def domeny_ewok():
    """Domena każdego rekordu EWoK (indeks wiersza parquetu = source_id), z tej samej przypiętej rewizji."""
    import pandas as pd
    from huggingface_hub import hf_hub_download
    p = hf_hub_download("ewok-core/ewok-core-1.0", "data/test/ewok-core-1.0.parquet", repo_type="dataset",
                        revision="34d912a608066c92e2990a0328ffc3bd9a716042")
    return {i: r["Domain"] for i, r in enumerate(pd.read_parquet(p).to_dict("records"))}


POLE_ROZBICIA = {"blimp": "UID", "multiblimp-pl": "phenomenon", "ewok": "Domain"}
Z95 = 1.96


def rozbicie(eksport, bench, domeny):
    """Rozbicie eksploracyjne własnym kodem: grupa → n, średnie obu etykiet z przedziałem Walda ±1,96 SE przyciętym do
    [0, 1], Δ parowane (z, p z rozkładu normalnego), Holm w obrębie rozbicia z m = liczba grup."""
    pa, pb = probki(eksport, bench, A), probki(eksport, bench, B)
    grupy = defaultdict(list)
    for k in sorted(pa):
        g = domeny[pa[k]["source_id"]] if bench == "ewok" else pa[k]["doc"][POLE_ROZBICIA[bench]]
        grupy[str(g)].append(k)

    def sr(x):
        n, m = len(x), sum(x) / len(x)
        se = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1) / n) if n > 1 else None
        return m, se, (None if se is None else [max(0.0, m - Z95 * se), min(1.0, m + Z95 * se)])

    out = {}
    for g in sorted(grupy):
        ks = grupy[g]
        xa = [wynik_pytania(bench, pa[k]) for k in ks]
        xb = [wynik_pytania(bench, pb[k]) for k in ks]
        d = [a - b for a, b in zip(xa, xb)]
        md, sd, _ = sr(d)
        z = md / sd if sd else None
        out[g] = {"n": len(ks), "v109": sr(xa), "v108": sr(xb), "roznica": md, "se": sd, "z": z,
                  "p": 2 * stats.norm.sf(abs(z)) if z is not None else None}
    nazwy = list(out)
    for g, ph in zip(nazwy, holm([out[g]["p"] for g in nazwy], m=len(nazwy))):
        out[g]["p_holm"], out[g]["werdykt_holm"] = ph, werdykt(ph)
    return out


def porownaj_rozbicie(bench, wlasne, L_rozb):
    """Rozjazdy rozbicia wobec LICZBY.json eksploracyjne.rozbicie (pusta lista = zgodne)."""
    bl = []
    if not L_rozb:
        return [f"{bench}: brak rozbicia w LICZBY.json"]
    L_g = {g["grupa"]: g for g in L_rozb["grupy"]}
    if set(L_g) != set(wlasne) or L_rozb["k"] != len(wlasne):
        return [f"{bench}: rozbicie, inne grupy niż w LICZBY.json"]
    for g, w in wlasne.items():
        x = L_g[g]
        p = x["porownanie"]
        if w["n"] != x["n"] or abs(w["roznica"] - p["roznica"]) > 1e-9:
            bl.append(f"{bench}/{g}: n albo Δ rozbicia różne")
        for et in ("v109", "v108"):
            m, se, ci = w[et]
            ci_L = x[et]["ci95"]
            if abs(m - x[et]["wartosc"]) > 1e-9 or (ci is None) != (ci_L is None) or (
                    ci and any(abs(a - b) > 1e-9 for a, b in zip(ci, ci_L))):
                bl.append(f"{bench}/{g}: CI95 {et} {ci} != {ci_L}")
        if (w["p_holm"] is None) != (p.get("p_holm") is None) or (
                w["p_holm"] is not None and abs(w["p_holm"] - p["p_holm"]) > 1e-6 * max(p["p_holm"], 1e-300)):
            bl.append(f"{bench}/{g}: p Holma rozbicia {w['p_holm']} != {p.get('p_holm')}")
        if w["werdykt_holm"] != p.get("werdykt_holm"):
            bl.append(f"{bench}/{g}: werdykt po Holmie rozbicia {w['werdykt_holm']} != {p.get('werdykt_holm')}")
    return bl


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
        return {"roznica": bpp(pa) - bpp(pb), "se": se, "t": t, "df": df, "p": p, "n": len(klucze), "v108": bpp(pb)}
    xa = [wynik_pytania(bench, pa[k]) for k in klucze]
    xb = [wynik_pytania(bench, pb[k]) for k in klucze]
    d = [a - b for a, b in zip(xa, xb)]
    kl = klastry(bench, klucze, pa, szablony)
    v108 = sum(xb) / len(xb)
    obok = {}
    if bench not in ("ewok", "lambada"):  # LAMBADA: greedy ostatniego słowa, bez wyboru między opcjami
        met = METRYKA[bench]
        rem = {m: [remis(P[k], met) for k in klucze] for m, P in ((A, pa), (B, pb))}
        obok["remisy"] = {m: {"remisy": sum(r for r, _ in x), "remisy_z_poprawna": sum(g for _, g in x)}
                          for m, x in rem.items()}
        if met == "acc_norm":  # definicja lm_eval (pole próbki), tylko do wglądu
            la = [float(pa[k]["acc_norm"]) for k in klucze]
            lb = [float(pb[k]["acc_norm"]) for k in klucze]
            obok["acc_norm_lm_eval"] = {"v109": sum(la) / len(la), "v108": sum(lb) / len(lb),
                                        "roznica": (sum(la) - sum(lb)) / len(la),
                                        "pytan_rozne_od_runnera": {A: sum(x != y for x, y in zip(la, xa)),
                                                                   B: sum(x != y for x, y in zip(lb, xb))}}
    if kl is not None:
        m, se, t, df, p, G = se_klastrowe(d, kl)
        return {"roznica": sum(xa) / len(xa) - v108, "se": se, "t": t, "df": df, "p": p, "n": len(d), "v108": v108,
                **obok}
    n, m = len(d), sum(d) / len(d)
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n)
    z = m / se if se else None
    return {"roznica": sum(xa) / n - v108, "se": se, "z": z, "p": 2 * stats.norm.sf(abs(z)) if z is not None else None, "n": n,
            "v108": v108, **obok}


def kontrola_zgodna(w, m):
    """1.08 policzone tu z próbek wobec wiersza manifestu przebiegu: to samo n i |różnica| ≤ 0,5 SE z manifestu
    (MultiBLiMP-PL zapisuje procenty)."""
    skala = 100.0 if m["benchmark"] == "multiblimp-pl" else 1.0
    return w["n"] == m["n"] and bool(m["se"]) and abs(w["v108"] * skala - m["wartosc"]) <= 0.5 * m["se"]


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
    bledy = sprawdz_wejscia(eksport, liczby, Path(sys.argv[3]), Path(sys.argv[4]))
    if bledy:
        print("\n".join(bledy[:10]))
        return 2
    manifest = {w["benchmark"]: w for w in map(json.loads, Path(sys.argv[3]).read_text(encoding="utf-8").splitlines())
                if w["model"] == B}
    szablony = szablony_ewok()
    testy = {t["benchmark"]: t for t in liczby["testy"]}
    if len(testy) != M:
        raise SystemExit(f"LICZBY.json ma {len(testy)} testów, protokół {M}")
    wyniki = {b: porownaj(eksport, b, szablony) for b in testy}
    for b, p in zip(wyniki, holm([wyniki[b]["p"] for b in wyniki])):
        w = wyniki[b]
        w["p_holm"], w["werdykt_holm"] = p, werdykt(p)
        w["kontrola_zgodna"] = zgodna = kontrola_zgodna(w, manifest[b])
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
        if abs(w["v108"] - testy[b]["v108_przeliczone"]["wartosc"]) > 1e-9:
            rozjazdy.append(f"{b}: 1.08 przeliczone {w['v108']} != {testy[b]['v108_przeliczone']['wartosc']}")
        if (w["p_holm"] is None) != (L.get("p_holm") is None) or (
                w["p_holm"] is not None and abs(w["p_holm"] - L["p_holm"]) > 1e-6 * max(L["p_holm"], 1e-300)):
            rozjazdy.append(f"{b}: p Holma {w['p_holm']} != {L.get('p_holm')}")
        if w["kontrola_zgodna"] != testy[b]["kontrola"]["zgodna"]:
            rozjazdy.append(f"{b}: kontrola narzędzia {w['kontrola_zgodna']} != {testy[b]['kontrola']['zgodna']}")
        if w["werdykt_holm"] != L["werdykt_holm"]:
            rozjazdy.append(f"{b}: po Holmie {w['werdykt_holm']} != {L['werdykt_holm']}")
        if w["wynik"] != testy[b]["werdykt_koncowy"]:
            rozjazdy.append(f"{b}: wynik {w['wynik']} != {testy[b]['werdykt_koncowy']}")
        lm_L = ((liczby.get("eksploracyjne") or {}).get("definicja_lm_eval") or {}).get(b)
        if "acc_norm_lm_eval" in w and (lm_L is None or abs(w["acc_norm_lm_eval"]["roznica"] - lm_L["porownanie"]["roznica"]) > 1e-9
                                        or abs(w["acc_norm_lm_eval"]["v109"] - lm_L["v109"]) > 1e-9):
            rozjazdy.append(f"{b}: acc_norm w definicji lm_eval {w['acc_norm_lm_eval']} != {lm_L and lm_L['porownanie']['roznica']}")
        rem_L = ((liczby.get("eksploracyjne") or {}).get("remisy") or {}).get(b)
        if "remisy" in w:
            for m_, r_ in w["remisy"].items():
                x = (rem_L or {}).get(m_) or {}
                if (x.get("remisy"), x.get("remisy_z_poprawna")) != (r_["remisy"], r_["remisy_z_poprawna"]):
                    rozjazdy.append(f"{b}: remisy {m_} {r_} != {x}")
    domeny = domeny_ewok()
    rozb = {}
    for b in POLE_ROZBICIA:
        rozb[b] = rozbicie(eksport, b, domeny)
        rozjazdy += porownaj_rozbicie(b, rozb[b], ((liczby.get("eksploracyjne") or {}).get("rozbicie") or {}).get(b))
    out = {"rozjazdy": rozjazdy, "testy": wyniki, "rozbicie": rozb,
           "podzial": {k: sorted(b for b, w in wyniki.items() if w["wynik"].startswith(k)) for k in ("lepszy", "gorszy", "szum")}}
    tekst = json.dumps(out, ensure_ascii=False, indent=1)
    if len(sys.argv) > 5:
        Path(sys.argv[5]).write_text(tekst + "\n", encoding="utf-8")
    print("\n".join(rozjazdy) if rozjazdy else f"zgodne: {len(wyniki)} testów, podział {out['podzial']}")
    return 1 if rozjazdy else 0


if __name__ == "__main__":
    raise SystemExit(main())
