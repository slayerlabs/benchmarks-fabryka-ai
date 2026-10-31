"""Analiza testów 0-5 hipotezy formatu z plików `common/hipoteza_formatu.py licz`.

  python analyses/answer-format/analiza_formatu.py --wyniki analyses/answer-format/results
  (<wyniki>/<model>/<zadanie>.jsonl -> <wyniki>/raport_formatu.json)

Progi ustalone przed wynikami (zlecenie 29.10):
  T0  |nasza - opublikowana| <= 2 pkt (Pythia-1B 0-shot ARC-E/ARC-C acc i acc_norm; Qwen2.5-0.5B ARC-C 25-shot).
  T1  jedna litera > 50% wyborów i istotnie (dwumianowy, p<0,05) ponad jej udział w poprawnych; chi2 rozkładu.
  T2  >= 70% wyborów zostaje na tej samej literze po cyklicznym przesunięciu treści = wybór idzie za pozycją.
  T3  acc_norm / acc wg BPB / acc PMI > baza losowa + 2 SE (którakolwiek) = wiedza ukryta przez format.
  T4  (kryterium dopisane przed wynikami, zlecenie go nie podało) pułapka potwierdzona, gdy > 50% błędnych
      wyborów acc ma wyższe bezwarunkowe prawdopodobieństwo niż poprawna ORAZ acc PMI > acc (McNemar p<0,05).
  T5  (kryterium dopisane przed wynikami) „uczy się treści przy stojącym acc": średnie BPB poprawnej spada
      1.00 -> 1.06 o > 2 SE (sparowane), a |delta acc_norm| < 2 SE (sparowane).
"""

import json
import math
from collections import Counter
from pathlib import Path

from scipy import stats

LITERY = "ABCDEFGH"
LN2 = math.log(2)

# Opublikowane liczby (odczyt 29.10.2026).
REF_PYTHIA = {  # EleutherAI/pythia evals/pythia-v1/pythia-1b-bf16/zero-shot/1b-bf16_step143000.json, lm-eval 0-shot
    "arc_e_cloze": {"acc": 0.5694, "acc_norm": 0.4903},
    "arc_c_cloze": {"acc": 0.2440, "acc_norm": 0.2713},
}
REF_QWEN = {"arc_c_cloze_25shot": {"acc_norm": 0.356}}  # Qwen2.5 Technical Report (arXiv 2412.15115) Tab. 5, ARC-C 25-shot


def wczytaj(p):
    p = Path(p)
    if not p.exists():
        return None
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def argmax(xs):
    return max(range(len(xs)), key=lambda i: (xs[i], -i))


def wybory(w):
    ll, b, z = w["ll"], w["bajty"], w["znaki"]
    r = {"acc": argmax(ll), "acc_norm": argmax([l / max(c, 1) for l, c in zip(ll, z)]),
         "bpb": argmax([l / max(x, 1) for l, x in zip(ll, b)])}
    if w.get("bezw"):
        r["pmi"] = argmax([l - u for l, u in zip(ll, w["bezw"])])
    return r


def prop(k, n):
    p = k / n if n else float("nan")
    return {"wartosc": p, "n": n, "se": math.sqrt(p * (1 - p) / n) if n else float("nan")}


def trafnosci(ws):
    out = {}
    for m in ("acc", "acc_norm", "bpb", "pmi"):
        if m == "pmi" and not ws[0].get("bezw"):
            continue
        out[m] = prop(sum(wybory(w)[m] == w["gold"] for w in ws), len(ws))
    out["losowa"] = sum(1 / w["k"] for w in ws) / len(ws)
    return out


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def test0(R):
    wiersze = []
    for etyk, ref in (("pythia-1b", REF_PYTHIA), ("Qwen2.5-0.5B", REF_QWEN)):
        for zad, metryki in ref.items():
            ws = wczytaj(R / etyk / f"{zad}.jsonl")
            if not ws:
                wiersze.append({"model": etyk, "zadanie": zad, "stan": "NOT RUN"})
                continue
            t = trafnosci(ws)
            for m, v in metryki.items():
                nasza = t[m]["wartosc"]
                wiersze.append({"model": etyk, "zadanie": zad, "metryka": m, "n": t[m]["n"], "nasza": nasza,
                                "opublikowana": v, "roznica_pkt": 100 * (nasza - v),
                                "ok": abs(100 * (nasza - v)) <= 2.0})
    oceniane = [w for w in wiersze if "ok" in w]
    return {"wiersze": wiersze, "narzedzie_ok": bool(oceniane) and all(w["ok"] for w in oceniane),
            "kompletny": all("ok" in w for w in wiersze)}


def test1(ws):
    n = len(ws)
    wyb = Counter(LITERY[wybory(w)["acc"]] for w in ws)
    pop = Counter(LITERY[w["gold"]] for w in ws)
    litery = sorted(set(wyb) | set(pop))
    obs = [wyb.get(l, 0) for l in litery]
    exp = [n * pop.get(l, 0) / n for l in litery]
    # chi2 tylko na literach z oczekiwaną > 0 (litera E występuje w 3 pytaniach ARC-C)
    para = [(o, e) for o, e in zip(obs, exp) if e > 0]
    o2, e2 = [o for o, _ in para], [e for _, e in para]
    e2 = [e * sum(o2) / sum(e2) for e in e2]
    chi2, p_chi2 = stats.chisquare(o2, e2)
    top, ntop = wyb.most_common(1)[0]
    udz_pop = pop.get(top, 0) / n
    p_bin = stats.binomtest(ntop, n, udz_pop, alternative="greater").pvalue if udz_pop > 0 else 0.0
    return {"n": n, "wybory": dict(sorted(wyb.items())), "poprawne": dict(sorted(pop.items())),
            "chi2": chi2, "p_chi2": p_chi2, "ulubiona": top, "udzial_ulubionej": ntop / n,
            "udzial_ulubionej_w_poprawnych": udz_pop, "p_dwumianowy": p_bin,
            "acc_litera": prop(sum(wybory(w)["acc"] == w["gold"] for w in ws), n),
            "potwierdzona": ntop / n > 0.5 and p_bin < 0.05}


def kalibrowana_litera(ws):
    """Trafność liter po odjęciu średniego logprob każdej litery w zbiorze (kalibracja prioru litery)."""
    sr = {}
    for w in ws:
        for i, v in enumerate(w["ll"]):
            sr.setdefault(i, []).append(v)
    sr = {i: sum(v) / len(v) for i, v in sr.items()}
    k = sum(argmax([v - sr[i] for i, v in enumerate(w["ll"])]) == w["gold"] for w in ws)
    return prop(k, len(ws))


def test2(ws, ws_p):
    mp = {w["id"]: w for w in ws_p}
    para = [(w, mp[w["id"]]) for w in ws if w["id"] in mp]
    n = len(para)
    ta_sama = sum(wybory(a)["acc"] == wybory(b)["acc"] for a, b in para)
    za_trescia = sum(wybory(b)["acc"] == (wybory(a)["acc"] + 1) % a["k"] for a, b in para)
    return {"n": n, "ta_sama_litera": prop(ta_sama, n), "za_trescia": prop(za_trescia, n),
            "acc_oryg": prop(sum(wybory(a)["acc"] == a["gold"] for a, _ in para), n),
            "acc_przes": prop(sum(wybory(b)["acc"] == b["gold"] for _, b in para), n),
            "za_pozycja": ta_sama / n >= 0.70 if n else None}


def test3(ws):
    t = trafnosci(ws)
    prog = t["losowa"]
    wyn = {}
    for m in ("acc_norm", "bpb", "pmi"):
        if m in t:
            v = t[m]
            wyn[m] = {**v, "prog": prog + 2 * v["se"], "ponad": v["wartosc"] > prog + 2 * v["se"]}
    bpb_pop = [-w["ll"][w["gold"]] / (LN2 * max(w["bajty"][w["gold"]], 1)) for w in ws]
    return {"losowa": prog, "acc": t["acc"], "metryki": wyn,
            "srednie_bpb_poprawnej": sum(bpb_pop) / len(bpb_pop),
            "wiedza_ukryta": any(x["ponad"] for x in wyn.values())}


def test4(ws):
    zle = [w for w in ws if wybory(w)["acc"] != w["gold"]]
    pulapka = sum(w["bezw"][wybory(w)["acc"]] > w["bezw"][w["gold"]] for w in zle)
    b = sum(wybory(w)["acc"] != w["gold"] and wybory(w)["pmi"] == w["gold"] for w in ws)
    c = sum(wybory(w)["acc"] == w["gold"] and wybory(w)["pmi"] != w["gold"] for w in ws)
    n = len(ws)
    acc = sum(wybory(w)["acc"] == w["gold"] for w in ws) / n
    pmi = sum(wybory(w)["pmi"] == w["gold"] for w in ws) / n
    p = mcnemar(b, c)
    return {"n_blednych": len(zle), "udzial_pulapki": prop(pulapka, len(zle)),
            "acc": acc, "acc_pmi": pmi, "poprawa_pkt": 100 * (pmi - acc), "zle_na_dobre": b, "dobre_na_zle": c,
            "p_mcnemar": p, "potwierdzona": pulapka / max(len(zle), 1) > 0.5 and pmi > acc and p < 0.05}


def test5(R, etykiety):
    dane = {e: wczytaj(R / e / "arc_c_cloze.jsonl") for e in etykiety}
    if any(v is None for v in dane.values()):
        return {"stan": "NOT RUN", "brak": [e for e, v in dane.items() if v is None]}
    wsp = set.intersection(*({w["id"] for w in v} for v in dane.values()))
    mapy = {e: {w["id"]: w for w in v if w["id"] in wsp} for e, v in dane.items()}
    ids = sorted(wsp)

    def bpb(w):
        return -w["ll"][w["gold"]] / (LN2 * max(w["bajty"][w["gold"]], 1))

    def margines(w):
        b = [-l / (LN2 * max(x, 1)) for l, x in zip(w["ll"], w["bajty"])]
        zle = [v for i, v in enumerate(b) if i != w["gold"]]
        return sum(zle) / len(zle) - b[w["gold"]]

    per = {}
    for e in etykiety:
        xs = [bpb(mapy[e][i]) for i in ids]
        ms = [margines(mapy[e][i]) for i in ids]
        sd = stats.tstd(xs)
        per[e] = {"bpb_poprawnej": sum(xs) / len(xs), "se": sd / math.sqrt(len(xs)),
                  "margines_bpb": sum(ms) / len(ms), "se_margines": stats.tstd(ms) / math.sqrt(len(ms)),
                  **{m: prop(sum(wybory(mapy[e][i])[m] == mapy[e][i]["gold"] for i in ids), len(ids))
                     for m in ("acc", "acc_norm", "bpb", "pmi")}}
    a, z = etykiety[0], etykiety[-1]
    d = [bpb(mapy[z][i]) - bpb(mapy[a][i]) for i in ids]
    se_d = stats.tstd(d) / math.sqrt(len(d))
    dacc = [int(wybory(mapy[z][i])["acc_norm"] == mapy[z][i]["gold"]) - int(wybory(mapy[a][i])["acc_norm"] == mapy[a][i]["gold"]) for i in ids]
    se_acc = stats.tstd(dacc) / math.sqrt(len(dacc))
    dm = [margines(mapy[z][i]) - margines(mapy[a][i]) for i in ids]
    return {"n": len(ids), "wersje": per,
            "delta_bpb": sum(d) / len(d), "se_delta_bpb": se_d,
            "delta_acc_norm": sum(dacc) / len(dacc), "se_delta_acc_norm": se_acc,
            "delta_margines": sum(dm) / len(dm), "se_delta_margines": stats.tstd(dm) / math.sqrt(len(dm)),
            "potwierdzona": (sum(d) / len(d)) < -2 * se_d and abs(sum(dacc) / len(dacc)) < 2 * se_acc}


PLIKI_ZESTAWIENIA = ["arc_c_mc", "arc_c_mc_przes", "arc_c_mc_bezspacji", "arc_c_mc_5shot", "arc_c_mc_25shot","arc_c_cloze", "arc_e_mc", "arc_e_cloze", "med_mc", "med_cloze",
                     "siqa_mc", "siqa_cloze", "belebele_mc", "belebele_cloze", "mmlu_mc", "mmlu_cloze", "multiblimp"]


def zestawienie_pliku(ws):
    """n, SE, bazy (losowa, większościowa), udział najczęstszej predykcji, rozkład liter; per grupa, gdy jest."""
    t = trafnosci(ws)
    n = len(ws)
    gold = Counter(w["gold"] for w in ws)
    pred = Counter(wybory(w)["acc"] for w in ws)
    out = {"n": n, "losowa": t["losowa"], "wiekszosciowa": gold.most_common(1)[0][1] / n,
           "najczestsza_predykcja": pred.most_common(1)[0][1] / n,
           "wybory_acc": {LITERY[k]: v for k, v in sorted(pred.items())},
           "poprawne": {LITERY[k]: v for k, v in sorted(gold.items())},
           **{m: t[m] for m in ("acc", "acc_norm", "bpb", "pmi") if m in t},
           "srednie_bpb_poprawnej": sum(-w["ll"][w["gold"]] / (LN2 * max(w["bajty"][w["gold"]], 1)) for w in ws) / n}
    if ws[0].get("grupa"):
        grupy = {}
        for w in ws:
            grupy.setdefault(w["grupa"], []).append(w)
        per = {g: prop(sum(wybory(w)["acc"] == w["gold"] for w in v), len(v)) for g, v in sorted(grupy.items())}
        out["per_grupa"] = per
        out["makro_acc"] = sum(v["wartosc"] for v in per.values()) / len(per)
        if any(w["k"] == 4 for w in ws) and ws[0]["bajty"] and len(ws[0]["ll"]) == 4:
            per_n = {g: prop(sum(wybory(w)["acc_norm"] == w["gold"] for w in v), len(v)) for g, v in sorted(grupy.items())}
            out["per_grupa_acc_norm"] = per_n
    return out


def zestawienie(R, etykieta):
    wyn = {}
    for z in PLIKI_ZESTAWIENIA:
        ws = wczytaj(R / etykieta / f"{z}.jsonl")
        if ws:
            wyn[z] = zestawienie_pliku(ws)
    return wyn


def analiza(R):
    R = Path(R)
    S = R / "1.06"
    wynik = {"test0": test0(R)}
    for nazwa, plik in (("arc_c", "arc_c_mc"), ("medmcqa", "med_mc")):
        ws = wczytaj(S / f"{plik}.jsonl")
        if ws:
            wynik.setdefault("test1", {})[nazwa] = {**test1(ws), "litera_kalibrowana": kalibrowana_litera(ws)}
    a, b = wczytaj(S / "arc_c_mc.jsonl"), wczytaj(S / "arc_c_mc_przes.jsonl")
    if a and b:
        wynik["test2"] = test2(a, b)
    for nazwa, plik in (("arc_c", "arc_c_cloze"), ("medmcqa", "med_cloze")):
        ws = wczytaj(S / f"{plik}.jsonl")
        if ws:
            wynik.setdefault("test3", {})[nazwa] = test3(ws)
            if nazwa == "arc_c":
                wynik["test4"] = test4(ws)
    wynik["test5"] = test5(R, ["1.00", "1.03", "1.06"])
    wynik["zestawienie"] = {e: zestawienie(R, e) for e in ("1.06", "1.03", "1.00", "pythia-1b", "Qwen2.5-0.5B")
                            if (R / e).exists()}
    wt = S / "wikitext.json"
    if wt.exists():
        # results.json Space SlayerLab/Slayer1B-1.06, T03 byte_perplexity (pełna precyzja; 1,846 to zaokrąglenie)
        wynik["slayer_wikitext_kontrola"] = {**json.loads(wt.read_text()), "space_1.06_byte_ppl": 1.846283835597753}
    (R / "raport_formatu.json").write_text(json.dumps(wynik, ensure_ascii=False, indent=1, default=float))
    print(json.dumps(wynik, ensure_ascii=False, indent=1, default=float))
    return wynik


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--wyniki", required=True, help="katalog z <model>/<zadanie>.jsonl z hipoteza_formatu.py licz")
    analiza(Path(p.parse_args().wyniki))
