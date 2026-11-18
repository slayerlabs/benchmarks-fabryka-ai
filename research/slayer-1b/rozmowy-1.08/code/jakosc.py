"""Analizy A1-A3 z PROTOKOL_ANEKS.md: jakość pozycji, rzetelność (seedy, szablony, SNR), trafność zewnętrzna.

python -I code/jakosc.py  -> wyniki/jakosc.json   (wejście: wyniki/oceny_pozycji.jsonl, results/full-run-2026-11)
Czyste funkcje (testy w test_rozmowy.py) + odczyt plików. Bez werdyktów porównań modeli (to osobny skrypt).
"""
import hashlib
import json
import math
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
RESEARCH = BADANIE.parents[1]
MODELE = ["slayer", "bielik", "lfm"]
SEEDY = ["A_s1", "A_s2", "A_s3"]
KATEGORIE = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski", "tekst_techniczny"]
PROG_ROZROZNIA = 2 / 3
CENTRALNY = {  # PROTOKOL_ANEKS.md, A3 (ustalone z góry)
    "pl_jezyk": ["multiblimp-pl"], "pl_wiedza": [], "wiedza_ogolna": ["arc-easy", "arc-challenge"],
    "rozumowanie": ["winogrande", "wsc273"], "matematyka": ["mathqa"], "kod": [], "angielski": ["blimp", "lambada"],
    "tekst_techniczny": [],
}
KATALOGI_CENTRALNE = {"slayer": "slayer1b-1.08", "bielik": "bielik-1.5b-v3", "lfm": "lfm2.5-1.2b-base"}


def srednia(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def wariancja(xs):
    """Wariancja z próby (n−1); None przy n < 2."""
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def pearson(a, b):
    pary = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pary) < 3:
        return None
    ma = sum(x for x, _ in pary) / len(pary)
    mb = sum(y for _, y in pary) / len(pary)
    sab = sum((x - ma) * (y - mb) for x, y in pary)
    sa = math.sqrt(sum((x - ma) ** 2 for x, _ in pary))
    sb = math.sqrt(sum((y - mb) ** 2 for _, y in pary))
    return None if sa == 0 or sb == 0 else sab / (sa * sb)


def rangi(xs):
    """Rangi średnie (remisy dostają średnią rangę)."""
    por = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(por):
        j = i
        while j + 1 < len(por) and xs[por[j + 1]] == xs[por[i]]:
            j += 1
        for k in range(i, j + 1):
            r[por[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(a, b):
    pary = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pary) < 3:
        return None
    return pearson(rangi([x for x, _ in pary]), rangi([y for _, y in pary]))


def kendall_tau(a, b):
    """tau-a na małej liczbie obiektów (tu 3 modele); remis w którejkolwiek parze liczony jako 0."""
    n, s = len(a), 0
    for i in range(n):
        for j in range(i + 1, n):
            s += (1 if (a[i] - a[j]) * (b[i] - b[j]) > 0 else -1 if (a[i] - a[j]) * (b[i] - b[j]) < 0 else 0)
    return s / (n * (n - 1) / 2)


def jakosc_pozycji(wyniki):
    """wyniki: {id: {model: [0/1 seed1..3]}} -> trudność, zakres modeli, klasa pozycji."""
    out = {}
    for pid, po_mod in wyniki.items():
        wszystkie = [x for m in MODELE for x in po_mod[m]]
        p_m = {m: srednia(po_mod[m]) for m in MODELE}
        R = max(p_m.values()) - min(p_m.values())
        klasa = ("zawsze_dobrze" if all(x == 1 for x in wszystkie) else "zawsze_zle" if all(x == 0 for x in wszystkie)
                 else "rozroznia" if R >= PROG_ROZROZNIA - 1e-9 else "nie_rozroznia")
        out[pid] = dict(trudnosc=srednia(wszystkie), p_modeli=p_m, zakres=R, klasa=klasa)
    return out


def snr(srednie_modeli, wariancje_szumu):
    s = wariancja(srednie_modeli)
    n = srednia(wariancje_szumu)
    if s is None or not n:
        return None
    return s / n


def wczytaj_oceny():
    rows = [json.loads(x) for x in (BADANIE / "wyniki/oceny_pozycji.jsonl").read_text(encoding="utf-8").splitlines()]
    return rows[0], rows[1:]


def main():
    nagl, rows = wczytaj_oceny()
    idx = {(r["model"], r["id"]): r for r in rows}
    ids = sorted({r["id"] for r in rows}, key=lambda i: [r["id"] for r in rows].index(i))
    kat_id = {r["id"]: r["kat"] for r in rows}
    typ_id = {r["id"]: r["typ"] for r in rows}
    wer = [i for i in ids if typ_id[i] != "otwarte"]
    out = dict(wejscie_sha256=hashlib.sha256((BADANIE / "wyniki/oceny_pozycji.jsonl").read_bytes()).hexdigest(),
               a1={}, a2={}, a3={})
    # A1
    wyn = {i: {m: [idx[(m, i)]["dekodowania"][s]["poprawna"] for s in SEEDY] for m in MODELE} for i in wer}
    poz = jakosc_pozycji(wyn)
    for i in wer:
        poz[i]["greedy_A"] = {m: idx[(m, i)]["dekodowania"]["A_greedy"]["poprawna"] for m in MODELE}
        poz[i]["greedy_B"] = {m: idx[(m, i)]["dekodowania"]["B_greedy"]["poprawna"] for m in MODELE}
    out["a1"]["pozycje"] = poz
    out["a1"]["kategorie"] = {}
    for k in KATEGORIE:
        ki = [i for i in wer if kat_id[i] == k]
        if not ki:
            continue
        out["a1"]["kategorie"][k] = dict(
            n=len(ki), **{kl: sum(poz[i]["klasa"] == kl for i in ki) for kl in ("rozroznia", "nie_rozroznia", "zawsze_dobrze", "zawsze_zle")},
            zawsze_dobrze_id=[i for i in ki if poz[i]["klasa"] == "zawsze_dobrze"],
            zawsze_zle_id=[i for i in ki if poz[i]["klasa"] == "zawsze_zle"])
    out["a1"]["bpb_rozrzut"] = {i: math.sqrt(wariancja([idx[(m, i)]["bpb_A"] for m in MODELE])) for i in ids}
    # A2
    for k in KATEGORIE:
        ki = [i for i in ids if kat_id[i] == k]
        kw = [i for i in ki if typ_id[i] != "otwarte"]
        wiersz = {}
        for m in MODELE:
            d = {}
            if kw:
                s = {sd: [idx[(m, i)]["dekodowania"][sd]["poprawna"] for i in kw] for sd in SEEDY}
                kor = [pearson(s[a], s[b]) for a, b in (("A_s1", "A_s2"), ("A_s1", "A_s3"), ("A_s2", "A_s3"))]
                d["seedy_pearson_srednia"] = srednia(kor)
                d["seedy_pearson_pary"] = kor
                d["seedy_ten_sam_wynik"] = srednia([int(len({s[sd][j] for sd in SEEDY}) == 1) for j in range(len(kw))])
                ga = [idx[(m, i)]["dekodowania"]["A_greedy"]["poprawna"] for i in kw]
                gb = [idx[(m, i)]["dekodowania"]["B_greedy"]["poprawna"] for i in kw]
                d["greedy_A_B_pearson"] = pearson(ga, gb)
                d["greedy_A_B_zgodnosc"] = srednia([int(x == y) for x, y in zip(ga, gb)])
            ba = [idx[(m, i)]["bpb_A"] for i in ki]
            bb = [idx[(m, i)]["bpb_B"] for i in ki]
            d["bpb_A_B_pearson"] = pearson(ba, bb)
            d["bpb_A_B_spearman"] = spearman(ba, bb)
            wiersz[m] = d
        if kw:
            sr = [srednia([srednia([idx[(m, i)]["dekodowania"][sd]["poprawna"] for sd in SEEDY]) for i in kw]) for m in MODELE]
            szum = [wariancja([srednia([idx[(m, i)]["dekodowania"][sd]["poprawna"] for i in kw]) for sd in SEEDY]) for m in MODELE]
            wiersz["snr_poprawnosc"] = dict(sygnal=wariancja(sr), szum=srednia(szum), snr=snr(sr, szum), srednie_modeli=sr)
        srb = [srednia([idx[(m, i)]["bpb_A"] for i in ki]) for m in MODELE]
        szb = [wariancja([srednia([idx[(m, i)][f"bpb_{sz}"] for i in ki]) for sz in ("A", "B")]) for m in MODELE]
        wiersz["snr_bpb_wzgledem_szablonu"] = dict(sygnal=wariancja(srb), szum=srednia(szb), snr=snr(srb, szb), srednie_modeli=srb)
        out["a2"][k] = wiersz
    # A3
    fr = RESEARCH / "results/full-run-2026-11"
    for k in KATEGORIE:
        ki = [i for i in ids if kat_id[i] == k]
        kw = [i for i in ki if typ_id[i] != "otwarte"]
        if kw:
            nasza = {m: srednia([srednia([idx[(m, i)]["dekodowania"][sd]["poprawna"] for sd in SEEDY]) for i in kw]) for m in MODELE}
            metryka = "poprawnosc_A_srednia_seedow (wyzej lepiej)"
        else:
            nasza = {m: -srednia([idx[(m, i)]["bpb_A"] for i in ki]) for m in MODELE}
            metryka = "minus BPB_A (wyzej lepiej)"
        wpis = dict(nasza_metryka=metryka, nasza=nasza, testy={})
        if not CENTRALNY[k]:
            wpis["stan"] = "NOT RUN: brak dopasowanego testu w przebiegu centralnym (aneks A3)"
        for t in CENTRALNY[k]:
            wart, braki, wersje = {}, [], {}
            for m in MODELE:
                p = fr / t / KATALOGI_CENTRALNE[m] / "results.json"
                if not p.exists():
                    braki.append(f"{m} x {t}")
                    continue
                d = json.loads(p.read_text())
                o = d["observations"][0]
                v = o["value"] if o["higher_is_better"] else -o["value"]
                wart[m] = v
                wersje[m] = dict(katalog=str(p.relative_to(RESEARCH)), model=d["models"], metryka=o["metric"],
                                 wyzej_lepiej=o["higher_is_better"], results_sha256=o.get("results_sha256"))
            t_wpis = dict(wartosci=wart, wersje=wersje)
            if braki:
                t_wpis["stan"] = "NOT RUN: " + ", ".join(braki)
            else:
                a = [nasza[m] for m in MODELE]
                b = [wart[m] for m in MODELE]
                t_wpis["kendall_tau"] = kendall_tau(a, b)
                znaki = {}
                for x, y in (("slayer", "bielik"), ("slayer", "lfm"), ("bielik", "lfm")):
                    dn, dc = nasza[x] - nasza[y], wart[x] - wart[y]
                    znaki[f"{x}-{y}"] = dict(nasza=dn, centralny=dc, zgodny_znak=(dn > 0) == (dc > 0) if dn and dc else None)
                t_wpis["roznice_par"] = znaki
            wpis["testy"][t] = t_wpis
        out["a3"][k] = wpis
    (BADANIE / "wyniki/jakosc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("zapisano wyniki/jakosc.json")


if __name__ == "__main__":
    main()
