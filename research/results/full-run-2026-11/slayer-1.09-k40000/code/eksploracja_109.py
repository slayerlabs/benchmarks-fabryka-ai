"""Analizy EKSPLORACYJNE pomiaru 1.09 k40000, dopisane po wyniku na żądanie weryfikacji (rundy poprawek 1):
nie zmieniają głównego twierdzenia ani werdyktów protokołu. Wołane z liczby_109.py, wynik w LICZBY.json pod kluczem
`eksploracyjne`, więc RAPORT.md bierze z niego każdą liczbę.

- remisy: reguła runnera (`metryki.argmax`, pierwszy indeks przy remisie) zapisana jako stan, liczba remisów, remisów
  z poprawną opcją i pytań ze zdublowaną treścią opcji, per test i etykieta;
- rozbicie: BLiMP po paradygmatach (UID), MultiBLiMP-PL po zjawiskach (`phenomenon`), EWoK po domenach (`Domain`):
  n, wartości obu etykiet z CI95 (±1,96 SE z pozycji), Δ parowane z SE i z, Holm w obrębie rozbicia;
- formaty MC: każdy wariant pliku próbek (space, mc, cloze): acc, acc_norm, BPB poprawnej obu etykiet, Δ parowane acc
  i acc_norm, rozkład wybieranych pozycji wobec poprawnych (reguła wyboru = metryka testu);
- wobec bazy: `wobec_b` z results_rozszerzone.json (b = wyższa z bazy losowej i stałej odpowiedzi);
- wrażliwość werdyktów „prawdopodobne” po Holmie: margines p Holma do progu, test McNemara (dokładny, dwumianowy) na
  pozycjach i najmniejsza liczba wygranych 1.09 zamienionych na remis, po której p Holma przekracza próg.
"""
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

TU = Path(__file__).resolve().parent
RESEARCH = TU.parents[3]
for p in (RESEARCH / "tools" / "ewaluacja", RESEARCH / "tools", RESEARCH / "common", RESEARCH / "benchmarks" / "ewok"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import raport as R  # noqa: E402
import statystyka as S  # noqa: E402

A, B = "slayer1b-1.09-k40000", "slayer1b-1.08"
ROZBICIE = {"blimp": "UID", "multiblimp-pl": "phenomenon", "ewok": "Domain"}
BEZ_MC = {"ewok", "wikitext-2", "lambada"}
LITERY = "ABCDEFGHIJ"


def probki_pliku(p: Path) -> dict:
    rek = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    klucz = "doc_id" if "doc_id" in rek[0] else "id"
    return {r[klucz]: r for r in rek}


def pliki_wariantow(eksport, bench, model):
    d = eksport / "wyniki" / bench / model / "probki"
    return {p.name.split("_", 1)[1].removesuffix(".jsonl"): p for p in sorted(d.glob("*_*.jsonl"))}


def oceny_wariantu(M, probki):
    """[(oceny_mc, wyniki punktowe acc i acc_norm, kontynuacje)] w kolejności kluczy."""
    out = {}
    for k, p in probki.items():
        z_pmi = "acc_mutual_info" in p["metrics"]
        lls, _, konty, gold = M.rozbierz_mc(p, z_pmi)
        norm = [ll / max(len(c.lstrip(" ")), 1) for ll, c in zip(lls, konty)]
        out[k] = {"o": M.oceny_mc(p, z_pmi), "acc": lls, "acc_norm": norm, "konty": konty, "gold": gold,
                  "wielokontekst": len({a[0] for a in p["arguments"][:len(konty)]}) > 1}
    return out


def remisy_mc(oceny, klucz):
    rem = rem_gold = dubel = 0
    for x in oceny.values():
        s = x[klucz]
        mx = max(s)
        rowne = [i for i, v in enumerate(s) if v == mx]
        if len(rowne) > 1:
            rem += 1
            rem_gold += x["gold"] in rowne
        if not x["wielokontekst"] and len(set(x["konty"])) < len(x["konty"]):
            dubel += 1
    return {"remisy": rem, "remisy_z_poprawna": rem_gold, "pytan_ze_zdublowana_opcja": dubel, "n": len(oceny)}


def parowane(d):
    n = len(d)
    m = sum(d) / n
    se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n) if n > 1 else None
    z = m / se if se else None
    return {"n": n, "roznica": m, "se": se, "z": z, "p": S.p_z(z) if z is not None else None}


def srednia_ci(x):
    n = len(x)
    m = sum(x) / n
    se = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1) / n) if n > 1 else None
    return {"wartosc": m, "se": se, "ci95": [m - 1.96 * se, m + 1.96 * se] if se is not None else None}


def rozbicie(bench, wa, wb, grupy):
    """Grupy pozycji: n, obie etykiety z CI, Δ parowane, Holm w obrębie rozbicia (m = liczba grup)."""
    g = defaultdict(list)
    for k in wa:
        g[grupy[k]].append(k)
    wiersze = []
    for nazwa in sorted(g, key=str):
        ks = g[nazwa]
        xa, xb = [wa[k] for k in ks], [wb[k] for k in ks]
        wiersze.append({"grupa": str(nazwa), "n": len(ks), "v109": srednia_ci(xa), "v108": srednia_ci(xb),
                        "porownanie": parowane([a - b for a, b in zip(xa, xb)])})
    for w, h in zip(wiersze, S.po_holmie([w["porownanie"]["p"] for w in wiersze], m=len(wiersze))):
        w["porownanie"]["werdykt"] = S.werdykt(w["porownanie"]["z"]) if w["porownanie"]["z"] is not None else S.NIEROZSTRZYGALNE
        w["porownanie"].update(h)
    licz = Counter(w["porownanie"]["werdykt_holm"] for w in wiersze)
    return {"pole": ROZBICIE[bench], "k": len(wiersze), "po_holmie": dict(licz), "grupy": wiersze}


def mcnemar(d):
    """Dokładny dwustronny test znaków na pozycjach z różnicą (wygrane 1.09 wobec wygranych 1.08)."""
    w, l = sum(1 for x in d if x > 0), sum(1 for x in d if x < 0)
    n = w + l
    k = min(w, l)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n) if n else None
    return {"wygrane_109": w, "wygrane_108": l, "p": p}


def wrazliwosc(t, wektor, klastry, ps_protokolu, m):
    """Margines Holma i ile wygranych 1.09 zamienić na remis, żeby p Holma przekroczyło próg „prawdopodobne”."""
    p = t["porownanie"]
    ranga = sorted(x for x in ps_protokolu if x is not None).index(p["p"])
    mnoznik = m - ranga
    d = list(wektor)

    def p_holma(dd):
        r = S.se_k(dd, klastry) if klastry is not None else None
        pz = r["p_t"] if r is not None else parowane(dd)["p"]
        return min(1.0, pz * mnoznik)

    wygrane = [i for i, x in enumerate(d) if x > 0]
    ile = None
    for j in range(1, min(len(wygrane), 50) + 1):
        kandydaci = []  # zachłannie: zerujemy wygraną, której utrata najbardziej podnosi p (najgorszy przypadek dla 1.09)
        for i in wygrane:
            dd = d.copy()
            dd[i] = 0.0
            kandydaci.append((p_holma(dd), i))
        best, i_best = max(kandydaci)
        d[i_best] = 0.0
        wygrane.remove(i_best)
        if best > S.P_PRAWDOPODOBNE:
            ile = j
            break
    mc = mcnemar(wektor)
    return {"p_holm": p["p_holm"], "prog": S.P_PRAWDOPODOBNE, "mnoznik_holma": mnoznik,
            "wygranych_do_szumu": ile, "mcnemar": {**mc, "p_holm_ta_sama_ranga": None if mc["p"] is None
                                                     else min(1.0, mc["p"] * mnoznik)}}


def zbuduj(eksport: Path, liczby: dict) -> dict:
    oceny = R.Oceny()
    M = oceny.M
    out = {"uwaga": "analizy po wyniku, eksploracyjne; nie zmieniają werdyktów protokołu",
           "regula_remisu": "argmax z pierwszym indeksem (metryki.argmax runnera); EWoK: remis T1 = T2 liczony jako brak "
                            "wyboru (ewok.evaluate)",
           "remisy": {}, "rozbicie": {}, "formaty": {}, "wobec_bazy": {}, "wrazliwosc": {}}
    ps = [t["porownanie"]["p"] for t in liczby["testy"]]
    for t in liczby["testy"]:
        bench, zad, met = t["benchmark"], t["zadanie"], t["metryka"]
        # wobec bazy z plików wyników
        wb_ = {}
        for model in (A, B):
            roz = json.loads((eksport / "wyniki" / bench / model / "results_rozszerzone.json").read_text(encoding="utf-8"))
            sp = ((roz["observations"][0].get("dodatkowe") or {}).get("space") or {})
            if sp.get("wobec_b"):
                wb_[model] = {k: sp["wobec_b"].get(k) for k in ("b", "baza", "roznica", "se", "z", "t", "df", "werdykt")}
        out["wobec_bazy"][bench] = wb_
        if bench == "ewok":
            pa, pb = (probki_pliku(eksport / "wyniki" / bench / m / "probki" / "ewok.jsonl") for m in (A, B))
            import ewok
            rek = ewok.load_records()
            out["remisy"][bench] = {m: {"remisy": sum(ewok.ties(w) > 0 for w in p.values()),
                                        "porownan_z_remisem": sum(ewok.ties(w) for w in p.values()), "n": len(p)}
                                    for m, p in ((A, pa), (B, pb))}
            wa = {k: ewok.evaluate(v)["ewok"] for k, v in pa.items()}
            wb = {k: ewok.evaluate(v)["ewok"] for k, v in pb.items()}
            out["rozbicie"][bench] = rozbicie(bench, wa, wb, {k: rek[v["source_id"]]["Domain"] for k, v in pa.items()})
            continue
        if bench in BEZ_MC:
            continue
        warianty = {}
        for war, plik_a in pliki_wariantow(eksport, bench, A).items():
            plik_b = eksport / "wyniki" / bench / B / "probki" / plik_a.name
            oa, ob = oceny_wariantu(M, probki_pliku(plik_a)), oceny_wariantu(M, probki_pliku(plik_b))
            klucze = sorted(oa)
            klucz_w = met if met in ("acc", "acc_norm") else "acc"
            w = {"plik": plik_a.name, "n": len(klucze), "regula_wyboru": klucz_w}
            for model, oc in ((A, oa), (B, ob)):
                gold = Counter(LITERY[oc[k]["gold"]] for k in klucze)
                pred = Counter(LITERY[oc[k]["o"][f"pred_{klucz_w}"]] for k in klucze)
                w[model] = {"acc": sum(oc[k]["o"]["acc"] for k in klucze) / len(klucze),
                            "acc_norm": sum(oc[k]["o"]["acc_norm"] for k in klucze) / len(klucze),
                            "bpb_poprawnej": sum(oc[k]["o"]["bpb_poprawnej"] for k in klucze) / len(klucze),
                            "wybrane": dict(sorted(pred.items())), "poprawne": dict(sorted(gold.items())),
                            "remisy": remisy_mc(oc, klucz_w)}
            for m_ in ("acc", "acc_norm"):
                w[f"delta_{m_}"] = parowane([oa[k]["o"][m_] - ob[k]["o"][m_] for k in klucze])
                w[f"delta_{m_}"]["werdykt"] = (S.werdykt(w[f"delta_{m_}"]["z"]) if w[f"delta_{m_}"]["z"] is not None
                                              else S.NIEROZSTRZYGALNE)
            warianty[war] = w
            if war == "space":
                out["remisy"][bench] = {A: w[A]["remisy"], B: w[B]["remisy"]}
                if met == "acc_norm":  # definicja lm_eval: pole próbki (długość wyboru liczona ze spacjami)
                    pa_, pb_ = probki_pliku(plik_a), probki_pliku(plik_b)
                    la, lb = [float(pa_[k]["acc_norm"]) for k in klucze], [float(pb_[k]["acc_norm"]) for k in klucze]
                    dl = parowane([x - y for x, y in zip(la, lb)])
                    mnoznik = liczby["m_holm"] - sorted(x for x in ps if x is not None).index(t["porownanie"]["p"])
                    dl.update({"werdykt": S.werdykt(dl["z"]) if dl["z"] is not None else S.NIEROZSTRZYGALNE,
                               "p_holm_ta_sama_ranga": None if dl["p"] is None else min(1.0, dl["p"] * mnoznik)})
                    dl["werdykt_holm"] = S.werdykt_p(dl["p_holm_ta_sama_ranga"])
                    out.setdefault("definicja_lm_eval", {})[bench] = {
                        "v109": sum(la) / len(la), "v108": sum(lb) / len(lb), "porownanie": dl,
                        "pytan_rozne_od_runnera": {A: sum(x != oa[k]["o"]["acc_norm"] for x, k in zip(la, klucze)),
                                                   B: sum(x != ob[k]["o"]["acc_norm"] for x, k in zip(lb, klucze))}}
                if bench in ROZBICIE:
                    pa = probki_pliku(plik_a)
                    out["rozbicie"][bench] = rozbicie(bench, {k: oa[k]["o"][klucz_w] for k in klucze},
                                                      {k: ob[k]["o"][klucz_w] for k in klucze},
                                                      {k: pa[k]["doc"][ROZBICIE[bench]] for k in klucze})
                if t["porownanie"]["werdykt_holm"] == "prawdopodobne":
                    wa_ = [oa[k]["o"][klucz_w] - ob[k]["o"][klucz_w] for k in klucze]
                    pa = [probki_pliku(plik_a)[k] for k in klucze]
                    import ewaluuj
                    import zadania as Z
                    kl = ewaluuj.klastry_probek(Z.ZADANIA[zad], pa)
                    out["wrazliwosc"][bench] = wrazliwosc(t, wa_, kl, ps, liczby["m_holm"])
        out["formaty"][bench] = warianty
    return out
