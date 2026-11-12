"""Niezależne przeliczenie kluczowych liczb wyniki/LICZBY.json, bez importu kodu analizy (notatka zasad: test
odtwarzający liczby inną drogą).

python -I code/test_niezalezny.py [sedzia1.jsonl sedzia2.jsonl klucz.json]

- BPB szablonu A: z surowych log p (wyniki/surowe/bpb_*.jsonl): −logprob / (ln 2 · bajty), średnia po poleceniach;
- poprawność: średnia 3 seedów z wyniki/oceny_pozycji.jsonl, typy sprawdzalne;
- różnica parowana, SE = sd(ddof=1)/√n i z dla poprawności i BPB wszystkich par i kategorii;
- kappa Cohena sędziów (gdy podano pliki ocen i klucz, które leżą poza repo).
Kod wyjścia 1 przy pierwszej niezgodności.
"""
import json
import math
import statistics
import sys
from pathlib import Path

B = Path(__file__).resolve().parent.parent
MODELE = ["slayer", "bielik", "lfm"]
TOL = 1e-9


def jsonl(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def sprawdz(nazwa, a, b, bledy):
    if a is None or b is None:
        ok = a is b
    else:
        ok = abs(a - b) <= TOL * max(1.0, abs(a))
    if not ok:
        bledy.append(f"{nazwa}: przeliczone {a} wobec LICZBY.json {b}")
    return ok


def main():
    L = json.loads((B / "wyniki/LICZBY.json").read_text(encoding="utf-8"))
    bledy, n_spr = [], 0
    poz = {p["id"]: p for p in jsonl(B / "dane/polecenia.jsonl")}
    kats = sorted({p["kat"] for p in poz.values()})
    # BPB z surowych log p
    bpb = {}
    for m in MODELE:
        for r in jsonl(B / f"wyniki/surowe/bpb_{m}.jsonl"):
            if r.get("naglowek"):
                continue
            bpb[(m, r["id"])] = -r["A"]["logprob"] / (math.log(2) * r["A"]["bajty"])
    # poprawność z ocen pozycji
    pop = {}
    for r in jsonl(B / "wyniki/oceny_pozycji.jsonl"):
        if "dekodowania" in r and r["typ"] != "otwarte":
            pop[(r["model"], r["id"])] = sum(r["dekodowania"][s]["poprawna"] for s in ("A_s1", "A_s2", "A_s3")) / 3
    for met, wart, klucz in (("bpb_A", bpb, "bpb_A"), ("poprawnosc", pop, "poprawnosc")):
        for k in kats + ["razem"]:
            ids = [i for i in poz if (k == "razem" or poz[i]["kat"] == k) and (MODELE[0], i) in wart]
            if len(ids) < 2:
                continue
            for m in MODELE:
                n_spr += 1
                sprawdz(f"{met}/{k}/{m}/srednia", statistics.fmean(wart[(m, i)] for i in ids),
                        L["opisy"][klucz][k][m]["srednia"], bledy)
            for a, b in (("slayer", "bielik"), ("slayer", "lfm"), ("bielik", "lfm")):
                d = [wart[(a, i)] - wart[(b, i)] for i in ids]
                se = statistics.stdev(d) / math.sqrt(len(d))
                z = statistics.fmean(d) / se if se > 0 else None
                r = L["porownania"][klucz][k][f"{a}-{b}"]
                n_spr += 3
                sprawdz(f"{met}/{k}/{a}-{b}/roznica", statistics.fmean(d), r["roznica"], bledy)
                sprawdz(f"{met}/{k}/{a}-{b}/se", se, r["se"], bledy)
                sprawdz(f"{met}/{k}/{a}-{b}/z", z, r["z"], bledy)
    # Holm: m = wszystkie kategorie z metryką (wiersz z SE = 0 liczy się jak p = 1), każda metryka i para
    for met, kat_dict in L["porownania"].items():
        kats = [k for k in kat_dict if k != "razem"]
        for para in ("slayer-bielik", "slayer-lfm", "bielik-lfm"):
            ps = [kat_dict[k][para]["p"] for k in kats]
            m = len(ps)
            kolej = sorted(range(m), key=lambda i: 1.0 if ps[i] is None else ps[i])
            maks, ph = 0.0, {}
            for r, i in enumerate(kolej):
                maks = max(maks, min(1.0, (m - r) * (1.0 if ps[i] is None else ps[i])))
                ph[i] = None if ps[i] is None else maks
            for i, k in enumerate(kats):
                n_spr += 1
                sprawdz(f"holm/{met}/{k}/{para}", ph[i], kat_dict[k][para]["p_holm"], bledy)
    # kappa sędziów
    if len(sys.argv) == 4:
        klucz = json.loads(Path(sys.argv[3]).read_text())["pary"]
        kl = []
        for p in sys.argv[1:3]:
            oc = {o["para_id"]: o["werdykt"] for o in jsonl(p)}
            c = {}
            for pid, w in oc.items():
                if w == "remis":
                    c[pid] = "remis"
                else:
                    zw = klucz[pid][w]
                    c[pid] = min(klucz[pid]["A"], klucz[pid]["B"], key=MODELE.index) == zw
            kl.append(c)
        pids = sorted(klucz)
        po = sum(kl[0][p] == kl[1][p] for p in pids) / len(pids)
        klasy = {v for c in kl for v in c.values()}
        pe = sum((sum(kl[0][p] == x for p in pids) / len(pids)) * (sum(kl[1][p] == x for p in pids) / len(pids))
                 for x in klasy)
        n_spr += 1
        sprawdz("sedziowie/kappa", (po - pe) / (1 - pe), L["sedziowie"]["kappa"], bledy)
    else:
        print("kappa: NOT RUN (nie podano plików sędziów i klucza)")
    for b in bledy:
        print("FAIL", b)
    print(f"{n_spr} sprawdzeń, {len(bledy)} niezgodności")
    sys.exit(1 if bledy else 0)


if __name__ == "__main__":
    main()
