"""Jedno źródło liczb badania: wyniki/LICZBY.json z surowych plików (PROTOKOL.md, PROTOKOL_ANEKS.md, zlecenie dokończenia).

python -I code/analiza.py <sedzia1.jsonl> <sedzia2.jsonl> <klucz.json> <kontrola_wzorcow_oceny.jsonl>

Wejścia z sha256 w LICZBY.json["wejscia"]. Reguły statystyki: PROTOKOL.md sekcje 1 i 5 (różnice parowane po
poleceniach, SE = sd/√n, z, werdykt, Holm po kategoriach w rodzinie hipoteza × para × metryka, bootstrap po
poleceniach 10 000 losowań, seed 20261112). Analizy wrażliwości (6 reguł oceny, greedy, szablon B) są oznaczone
jako eksploracyjne albo wtórne zgodnie z protokołem.
"""
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

KOD = Path(__file__).resolve().parent
BADANIE = KOD.parent
RESEARCH = BADANIE.parents[1]
sys.path.insert(0, str(KOD))
sys.path.insert(0, str(RESEARCH / "tools"))
import ocena  # noqa: E402
from statystyka import holm, werdykt, werdykt_p  # noqa: E402

MODELE = ["slayer", "bielik", "lfm"]
NAZWY = {"slayer": "Slayer 1.08", "bielik": "Bielik 1.5B", "lfm": "LFM2.5 1.2B"}
PARY = [("slayer", "bielik"), ("slayer", "lfm"), ("bielik", "lfm")]
KATEGORIE = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski", "tekst_techniczny"]
SEEDY = ["A_s1", "A_s2", "A_s3"]
SEED_BOOT, N_BOOT = 20261112, 10000
MARGINES_H61 = 0.05


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def p_z(z):
    return math.erfc(abs(z) / math.sqrt(2))


def z_kwantyl(p):
    """|z| o dwustronnym p (bisekcja)."""
    lo, hi = 0.0, 40.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if p_z(mid) > p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def bootstrap_ci(d, rng):
    d = np.asarray(d, dtype=float)
    idx = rng.integers(0, len(d), size=(N_BOOT, len(d)))
    m = d[idx].mean(axis=1)
    return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def opis(xs):
    x = np.asarray(xs, dtype=float)
    n = len(x)
    se = float(x.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    return dict(srednia=float(x.mean()), se=se, n=n)


def porownaj(x, y, rng=None):
    d = np.asarray(x, dtype=float) - np.asarray(y, dtype=float)
    n = len(d)
    se = float(d.std(ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    r = dict(roznica=float(d.mean()), se=se, n=n)
    if se > 0:
        r["z"] = r["roznica"] / se
        r["p"] = p_z(r["z"])
        r["werdykt"] = werdykt(r["z"])
    else:
        r.update(z=None, p=None, werdykt="nierozstrzygalne")
    r["dwa_se"] = 2 * se
    if rng is not None:
        r["ci95_bootstrap"] = bootstrap_ci(d, rng)
    return r


class Dane:
    def __init__(self):
        rows = jsonl(BADANIE / "wyniki/oceny_pozycji.jsonl")
        self.wiersze = rows[1:]
        self.idx = {(r["model"], r["id"]): r for r in self.wiersze}
        self.poz = {p["id"]: p for p in jsonl(BADANIE / "dane/polecenia.jsonl")}
        self.ids = list(self.poz)

    def ids_kat(self, kat, typy=None):
        return [i for i in self.ids if (kat == "razem" or self.poz[i]["kat"] == kat)
                and (typy is None or self.poz[i]["typ"] in typy)]

    def wartosc(self, metryka, m, i):
        r = self.idx[(m, i)]
        d = r["dekodowania"]
        if metryka == "poprawnosc":
            return float(np.mean([d[s]["poprawna"] for s in SEEDY]))
        if metryka == "poprawnosc_greedy_A":
            return float(d["A_greedy"]["poprawna"])
        if metryka == "poprawnosc_greedy_B":
            return float(d["B_greedy"]["poprawna"])
        if metryka in ("bpb_A", "bpb_B"):
            return r[metryka]
        if metryka == "nll_na_token_A":
            return r["nll_na_token_A"]
        if metryka == "bajty_na_token_A":
            return r["bajty_na_token_A"]
        if metryka == "koniec":
            return float(np.mean([d[s]["naturalny_koniec"] for s in SEEDY]))
        if metryka == "koniec_greedy_A":
            return float(d["A_greedy"]["naturalny_koniec"])
        if metryka == "rep3":
            return float(np.mean([d[s]["rep3"] if d[s]["rep3"] is not None else 0.0 for s in SEEDY]))
        if metryka == "rep3_greedy_A":
            v = d["A_greedy"]["rep3"]
            return 0.0 if v is None else float(v)
        if metryka == "distinct2":
            v = [d[s]["distinct2"] for s in SEEDY if d[s]["distinct2"] is not None]
            return float(np.mean(v)) if v else 1.0
        if metryka == "log10_p_eos_po_nl":
            return r["log10_p_eos_po_nl"]
        if metryka == "log10_p_eos":
            return r["log10_p_eos"]
        if metryka == "przeciek":
            return float(np.mean([d[s]["przeciek"] for s in SEEDY + ["A_greedy"]]))
        if metryka == "format_gsm8k":
            return float(np.mean([d[s]["format_gsm8k"] for s in SEEDY + ["A_greedy"]]))
        if metryka == "bajty_odpowiedzi":
            return float(np.mean([d[s]["bajty"] for s in SEEDY]))
        if metryka == "pusta":
            return float(np.mean([int(d[s]["bajty"] == 0 or not d[s].get("bajty")) for s in SEEDY]))
        raise KeyError(metryka)


TYPY = {
    "poprawnosc": {"krotka", "zdanie", "liczba", "kod"}, "poprawnosc_greedy_A": {"krotka", "zdanie", "liczba", "kod"},
    "poprawnosc_greedy_B": {"krotka", "zdanie", "liczba", "kod"}, "bpb_A": None, "bpb_B": None,
    "nll_na_token_A": None, "bajty_na_token_A": None, "koniec": None, "koniec_greedy_A": None,
    "rep3": {"otwarte"}, "rep3_greedy_A": {"otwarte"}, "distinct2": {"otwarte"},
    "log10_p_eos_po_nl": {"krotka", "zdanie", "liczba"}, "log10_p_eos": {"krotka", "zdanie", "liczba"},
    "przeciek": None, "format_gsm8k": None, "bajty_odpowiedzi": None, "pusta": None,
}


def tabele(dane, rng):
    """Opis per model × kategoria i porównania par per kategoria z Holmem w rodzinie para × metryka."""
    opisy, por = {}, {}
    for met, typy in TYPY.items():
        opisy[met], por[met] = {}, {}
        for kat in KATEGORIE + ["razem"]:
            ids = dane.ids_kat(kat, typy)
            if len(ids) < 2:
                continue
            opisy[met][kat] = {m: opis([dane.wartosc(met, m, i) for i in ids]) for m in MODELE}
            por[met][kat] = {}
            for a, b in PARY:
                por[met][kat][f"{a}-{b}"] = porownaj([dane.wartosc(met, a, i) for i in ids],
                                                     [dane.wartosc(met, b, i) for i in ids], rng)
        for a, b in PARY:
            k = f"{a}-{b}"
            kats = [kat for kat in KATEGORIE if kat in por[met]]
            ph = holm([por[met][kat][k]["p"] for kat in kats])
            for kat, p in zip(kats, ph):
                por[met][kat][k]["p_holm"] = p
                por[met][kat][k]["werdykt_holm"] = werdykt_p(p) if p is not None else "nierozstrzygalne"
                por[met][kat][k]["m_holm"] = len(kats)
    return opisy, por


HIPOTEZY = [
    # id, metryka, (a, b), znak oczekiwany różnicy a − b, kategorie (rodzina Holma)
    ("H1.1", "koniec", ("slayer", "bielik"), -1, KATEGORIE),
    ("H1.2", "koniec", ("slayer", "lfm"), -1, KATEGORIE),
    ("H1.3", "log10_p_eos_po_nl", ("slayer", "bielik"), -1, ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "angielski"]),
    ("H1.4", "log10_p_eos_po_nl", ("slayer", "lfm"), -1, ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "angielski"]),
    ("H2.1", "rep3", ("slayer", "bielik"), 1, ["pl_jezyk", "angielski", "tekst_techniczny"]),
    ("H2.2", "rep3", ("slayer", "lfm"), 1, ["pl_jezyk", "angielski", "tekst_techniczny"]),
    ("H3.1", "poprawnosc", ("slayer", "bielik"), -1, ["pl_wiedza", "wiedza_ogolna"]),
    ("H3.2", "bpb_A", ("slayer", "bielik"), 1, ["pl_wiedza", "wiedza_ogolna"]),
    ("H4.1", "poprawnosc", ("slayer", "bielik"), -1, ["matematyka", "rozumowanie"]),
    ("H4.2", "poprawnosc", ("slayer", "lfm"), -1, ["matematyka", "rozumowanie"]),
    ("H4.3", "bpb_A", ("slayer", "bielik"), 1, ["matematyka", "rozumowanie"]),
    ("H4.4", "bpb_A", ("slayer", "lfm"), 1, ["matematyka", "rozumowanie"]),
    ("H5.1", "poprawnosc", ("slayer", "bielik"), -1, ["kod"]),
    ("H5.2", "poprawnosc", ("slayer", "lfm"), -1, ["kod"]),
    ("H6.2", "bpb_A", ("slayer", "lfm"), -1, ["pl_jezyk", "pl_wiedza", "tekst_techniczny"]),
    ("H8.1", "format_gsm8k", ("lfm", "slayer"), 1, ["matematyka"]),
    ("H8.2", "format_gsm8k", ("lfm", "bielik"), 1, ["matematyka"]),
    ("H10", "bpb_A", ("slayer", "lfm"), 1, ["angielski"]),
]
WTORNE = {"poprawnosc": ["poprawnosc_greedy_A", "poprawnosc_greedy_B"], "bpb_A": ["bpb_B"], "koniec": ["koniec_greedy_A"],
          "rep3": ["rep3_greedy_A"]}


def stan_tezy(znak, r):
    if r.get("p_holm") is None:
        return "nierozstrzygnięta"
    if r["p_holm"] <= 0.0455 and np.sign(r["roznica"]) == znak:
        return "potwierdzona"
    if r["p_holm"] <= 0.0455 and np.sign(r["roznica"]) == -znak:
        return "obalona"
    return "nierozstrzygnięta"


def hipotezy(dane, rng):
    out = []
    for hid, met, (a, b), znak, kats in HIPOTEZY:
        rows = []
        for kat in kats:
            ids = dane.ids_kat(kat, TYPY[met])
            r = porownaj([dane.wartosc(met, a, i) for i in ids], [dane.wartosc(met, b, i) for i in ids], rng)
            r["kategoria"] = kat
            for w in WTORNE.get(met, []):
                ids_w = dane.ids_kat(kat, TYPY[w])
                rw = porownaj([dane.wartosc(w, a, i) for i in ids_w], [dane.wartosc(w, b, i) for i in ids_w])
                r[f"wtorne_{w}"] = dict(roznica=rw["roznica"], z=rw["z"], ten_sam_znak=bool(np.sign(rw["roznica"]) == np.sign(r["roznica"])))
            rows.append(r)
        ph = holm([r["p"] for r in rows])
        for r, p in zip(rows, ph):
            r["p_holm"] = p
            r["werdykt_holm"] = werdykt_p(p) if p is not None else "nierozstrzygalne"
            r["teza"] = stan_tezy(znak, r)
            r["m_holm"] = len(rows)
        out.append(dict(id=hid, metryka=met, a=a, b=b, znak=znak, wiersze=rows))
    # H6.1: równoważność S − B w BPB z marginesem 0,05 bit/bajt (bootstrap CI95)
    h61 = []
    for kat in ["pl_jezyk", "tekst_techniczny"]:
        ids = dane.ids_kat(kat)
        r = porownaj([dane.wartosc("bpb_A", "slayer", i) for i in ids], [dane.wartosc("bpb_A", "bielik", i) for i in ids], rng)
        lo, hi = r["ci95_bootstrap"]
        r["kategoria"] = kat
        r["teza"] = "potwierdzona" if hi < MARGINES_H61 else "obalona" if lo > MARGINES_H61 else "nierozstrzygnięta"
        h61.append(r)
    # H7: przecieki S (łącznie, 4 dekodowania szablonu A)
    ids = dane.ids_kat("razem")
    sl = [dane.wartosc("przeciek", "slayer", i) for i in ids]
    h7 = dict(odsetek_slayer=float(np.mean(sl)), ci95_bootstrap=bootstrap_ci(sl, rng),
              odsetek=dict((m, float(np.mean([dane.wartosc("przeciek", m, i) for i in ids]))) for m in MODELE),
              porownania={})
    for y in ("bielik", "lfm"):
        h7["porownania"][f"slayer-{y}"] = porownaj(sl, [dane.wartosc("przeciek", y, i) for i in ids], rng)
    warunek = h7["ci95_bootstrap"][0] > 0 and all(
        r["z"] is not None and r["z"] >= 2 for r in h7["porownania"].values())
    h7["teza"] = "potwierdzona" if warunek else "nierozstrzygnięta"
    return out, h61, h7


def sedziowie(p1, p2, pklucz, dane):
    klucz = json.loads(Path(pklucz).read_text())["pary"]
    oceny = {"sedzia1": {o["para_id"]: o for o in jsonl(p1)}, "sedzia2": {o["para_id"]: o for o in jsonl(p2)}}
    assert all(set(o) == set(klucz) for o in oceny.values())

    def klasa(pid, w):
        k = klucz[pid]
        if w == "remis":
            return "remis"
        zwyc = k["A"] if w == "A" else k["B"]
        a, b = sorted([k["A"], k["B"]], key=MODELE.index)
        return "pierwszy" if zwyc == a else "drugi"

    out = dict(n_par=len(klucz), sedziowie={})
    kl = {s: {pid: klasa(pid, o["werdykt"]) for pid, o in oc.items()} for s, oc in oceny.items()}
    # kappa Cohena na 3 klasach
    pids = sorted(klucz)
    a = [kl["sedzia1"][p] for p in pids]
    b = [kl["sedzia2"][p] for p in pids]
    po = sum(x == y for x, y in zip(a, b)) / len(pids)
    pe = sum((a.count(c) / len(a)) * (b.count(c) / len(b)) for c in ("pierwszy", "drugi", "remis"))
    out["kappa"] = (po - pe) / (1 - pe)
    out["zgodnosc_surowa"] = po
    out["kappa_ponizej_progu_0_20"] = out["kappa"] < 0.20
    for s, oc in oceny.items():
        w = [o["werdykt"] for o in oc.values()]
        nie_remis = [x for x in w if x != "remis"]
        pa = sum(x == "A" for x in nie_remis) / len(nie_remis)
        se = math.sqrt(0.25 / len(nie_remis))
        out["sedziowie"][s] = dict(A=w.count("A"), B=w.count("B"), remis=w.count("remis"),
                                   strona_A_odsetek=pa, strona_A_se=se, strona_A_z=(pa - 0.5) / se,
                                   strona_A_werdykt=werdykt((pa - 0.5) / se), sha256=sha(p1 if s == "sedzia1" else p2))
    # odsetek wygranych per para: wartość polecenia = wynik pierwszego modelu pary (1 / 0,5 / 0)
    def wynik(s, pid):
        c = kl[s][pid]
        return 1.0 if c == "pierwszy" else 0.0 if c == "drugi" else 0.5
    puste = sum(1 for pid in pids for st in ("A", "B")
                if not dane_odp(dane, klucz[pid]["id"], klucz[pid][st]))
    out["pary_z_pusta_odpowiedzia"] = puste
    out["wygrane"] = {}
    for x, y in PARY:
        par_pids = [p for p in pids if {klucz[p]["A"], klucz[p]["B"]} == {x, y}]
        for zakres in ["razem", "pl_jezyk", "angielski", "tekst_techniczny"]:
            pp = [p for p in par_pids if zakres == "razem" or klucz[p]["kat"] == zakres]
            wpis = {}
            for s in ("sedzia1", "sedzia2", "lacznie"):
                v = [(wynik("sedzia1", p) + wynik("sedzia2", p)) / 2 if s == "lacznie" else wynik(s, p) for p in pp]
                # odsetek wygranych DRUGIEGO modelu pary nad pierwszym (H9: Bielik i LFM nad Slayerem)
                w2 = [1 - t for t in v]
                o = opis(w2)
                o["z"] = (o["srednia"] - 0.5) / o["se"] if o["se"] else None
                o["werdykt"] = werdykt(o["z"]) if o["z"] is not None else "nierozstrzygalne"
                o["p"] = p_z(o["z"]) if o["z"] is not None else None
                wpis[s] = o
            out["wygrane"].setdefault(f"{y}_nad_{x}", {})[zakres] = wpis
    # H9: łącznie po dwóch sędziach, 42 polecenia, bez Holma (dwa osobne porównania z protokołu)
    h9 = {}
    for hid, klucz_w in (("H9.1", "bielik_nad_slayer"), ("H9.2", "lfm_nad_slayer")):
        r = out["wygrane"][klucz_w]["razem"]["lacznie"]
        stan = "nierozstrzygnięta"
        if not out["kappa_ponizej_progu_0_20"] and r["z"] is not None and abs(r["z"]) >= 2:
            stan = "potwierdzona" if r["z"] > 0 else "obalona"
        h9[hid] = dict(odsetek=r["srednia"], se=r["se"], z=r["z"], werdykt=r["werdykt"], teza=stan, n=r["n"])
    out["hipotezy"] = h9
    return out


def wczytaj_gen():
    gen = {}
    for m in MODELE:
        for r in jsonl(BADANIE / f"wyniki/surowe/gen_{m}_A.jsonl"):
            if not r.get("naglowek"):
                gen[(m, r["id"])] = {w["dekodowanie"]: w["odpowiedz"] for w in r["wyniki"]}
    return gen


def dane_odp(dane, pid, model):
    """Czy odpowiedź s1 szablonu A pokazana sędziom ma treść po obcięciu białych znaków."""
    if not hasattr(dane, "gen"):
        dane.gen = wczytaj_gen()
    return bool(dane.gen[(model, pid)]["s1"].strip())


POPRAWKI = {  # zlecenie: wrażliwość na 6 reguł wskazanych przez kontrolę wzorców (eksploracyjna)
    "pl_wiedza-27": lambda p: p.update(zakazane=p["zakazane"] + ["Józef"]),
    "pl_jezyk-13": lambda p: p.update(akceptowane=p["akceptowane"] + ["Wczoraj poszłam do sklepu po chleb."]),
    "wiedza_ogolna-08": lambda p: p.update(zakazane=[z for z in p["zakazane"] if z != "0"]),
    "wiedza_ogolna-20": lambda p: p.update(zakazane=[z for z in p["zakazane"] if z != "23"]),
    "wiedza_ogolna-04": lambda p: p.update(zakazane=[z for z in p["zakazane"] if z not in ("Azja", "Azji")]),
    "kod-26": lambda p: p.update(testy="\n".join(t for t in p["testy"].splitlines() if 'najczestsze_slowa("", ' not in t)),
}


def ocen_poz(p, odp):
    t = p["typ"]
    if t == "krotka":
        return ocena.ocen_krotka(odp, p["akceptowane"], p["zakazane"])
    if t == "zdanie":
        return ocena.ocen_zdanie(odp, p["akceptowane"])
    if t == "kod":
        return ocena.ocen_kod(odp, p["testy"])[0]
    return ocena.ocen_liczba(odp, p["liczba"])


def wrazliwosc_regul(dane):
    gen = {}
    for m in MODELE:
        for r in jsonl(BADANIE / f"wyniki/surowe/gen_{m}_A.jsonl"):
            if not r.get("naglowek"):
                gen[(m, r["id"])] = {w["dekodowanie"]: w["odpowiedz"] for w in r["wyniki"]}
    zmiany, nowe = [], {}
    for pid, fn in POPRAWKI.items():
        p = copy.deepcopy(dane.poz[pid])
        fn(p)
        for m in MODELE:
            stare = [dane.idx[(m, pid)]["dekodowania"][s]["poprawna"] for s in SEEDY]
            nowe_w = [ocen_poz(p, gen[(m, pid)][s[2:]]) for s in SEEDY]
            nowe[(m, pid)] = float(np.mean(nowe_w))
            if stare != nowe_w:
                zmiany.append(dict(id=pid, model=m, przed=stare, po=nowe_w))
    out = dict(eksploracyjna=True, zmienione_oceny=zmiany, liczba_zmienionych_ocen=sum(
        sum(a != b for a, b in zip(z["przed"], z["po"])) for z in zmiany), kategorie={})

    def w(m, i):
        return nowe.get((m, i), dane.wartosc("poprawnosc", m, i))
    for kat in sorted({dane.poz[p]["kat"] for p in POPRAWKI}, key=KATEGORIE.index):
        ids = dane.ids_kat(kat, TYPY["poprawnosc"])
        e = dict(opis={m: opis([w(m, i) for i in ids]) for m in MODELE}, porownania={})
        for a, b in PARY:
            e["porownania"][f"{a}-{b}"] = porownaj([w(a, i) for i in ids], [w(b, i) for i in ids])
        out["kategorie"][kat] = e
    return out


def clopper_pearson_gorna(k, n, alfa=0.05):
    if k == n:
        return 1.0
    lo, hi = k / n, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i) for i in range(k + 1))
        if cdf > alfa / 2:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def main():
    s1, s2, kl, kw = sys.argv[1:5]
    rng = np.random.default_rng(SEED_BOOT)
    dane = Dane()
    opisy, por = tabele(dane, rng)
    hip, h61, h7 = hipotezy(dane, rng)
    sedz = sedziowie(s1, s2, kl, dane)
    wzorce = jsonl(kw)
    jak = json.loads((BADANIE / "wyniki/jakosc.json").read_text())
    audyt = json.loads((BADANIE / "wyniki/audyt.json").read_text())
    kontrola = json.loads((BADANIE / "wyniki/kontrola.json").read_text())
    skaz = json.loads((BADANIE / "wyniki/skazenie.json").read_text())
    sonda = json.loads((BADANIE / "wyniki/sonda_eos_kod_lfm.json").read_text())
    z_holm8 = z_kwantyl(0.0455 / 8)
    z_moc80 = z_kwantyl(0.4)  # 0,84: jednostronny kwantyl mocy 80% (PROTOKOL.md, „Moc (MDE)”)
    mde = {kat: {met: {k: dict(dwa_se=v["dwa_se"], holm_se=z_holm8 * v["se"], mde80=(z_holm8 + z_moc80) * v["se"])
                       for k, v in por[met][kat].items()}
                 for met in ("poprawnosc", "bpb_A") if kat in por[met]} for kat in KATEGORIE}
    wyn = dict(
        opis="LICZBY.json badania rozmowy-1.08 (generowany przez code/analiza.py, nie edytować ręcznie)",
        protokol_commit="99bfeab", aneks_commit="3ad7739",
        wejscia={"oceny_pozycji.jsonl": sha(BADANIE / "wyniki/oceny_pozycji.jsonl"), "polecenia.jsonl": sha(BADANIE / "dane/polecenia.jsonl"),
                 "sedzia1": sha(s1), "sedzia2": sha(s2), "klucz": sha(kl), "kontrola_wzorcow_oceny": sha(kw),
                 "jakosc.json": sha(BADANIE / "wyniki/jakosc.json"), "audyt.json": sha(BADANIE / "wyniki/audyt.json")},
        modele=NAZWY, opisy=opisy, porownania=por,
        hipotezy=hip, h6_1=h61, h7=h7, sedziowie=sedz,
        wrazliwosc_regul=wrazliwosc_regul(dane),
        mde=dict(z_holm_m8=z_holm8, z_moc80=z_moc80, kategorie=mde),
        kontrola_narzedzia=kontrola,
        skazenie={n: {zb: len(v) for zb, v in skaz["trafienia"][n].items()} for n in ("13", "8")},
        kontrola_wzorcow=dict(n=len(wzorce), poprawne=sum(o["wzorzec"] == "poprawny" for o in wzorce),
                              bledne=sum(o["wzorzec"] == "bledny" for o in wzorce),
                              niejednoznaczne=sum(o["wzorzec"] == "niejednoznaczny" for o in wzorce),
                              ryzyko_oceny=sum(o["ryzyko_oceny"] != "brak" for o in wzorce),
                              bledne_gorna_ci95=clopper_pearson_gorna(sum(o["wzorzec"] != "poprawny" for o in wzorce), len(wzorce)),
                              ryzyko_id=[o["id"] for o in wzorce if o["ryzyko_oceny"] != "brak"]),
        audyt=dict({k: v for k, v in audyt.items() if k != "bledy_szczegoly"},
                   bledy_gorna_ci95=clopper_pearson_gorna(audyt["falszywe_trafienia"] + audyt["falszywe_odrzucenia"], audyt["n"])),
        jakosc=dict(a1=jak["a1"]["kategorie"], a2=jak["a2"], a3=jak["a3"]),
        sonda_eos_kod_lfm=dict(eksploracyjna=True, n=len(sonda),
                               mediana_p_im_end=float(np.median([s["p_eos"]["7"] for s in sonda])),
                               mediana_p_endoftext=float(np.median([s["p_eos"]["2"] for s in sonda]))),
        # per pozycja (do wykresu trudności): średnia poprawność 3 seedów A; strażnik liczb pomija ten klucz
        pozycje={i: dict(kat=dane.poz[i]["kat"], typ=dane.poz[i]["typ"],
                         **{m: dane.wartosc("poprawnosc", m, i) for m in MODELE})
                 for i in dane.ids_kat("razem", TYPY["poprawnosc"])},
    )
    (BADANIE / "wyniki/LICZBY.json").write_text(json.dumps(wyn, ensure_ascii=False, indent=1), encoding="utf-8")
    print("zapisano wyniki/LICZBY.json")


if __name__ == "__main__":
    main()
