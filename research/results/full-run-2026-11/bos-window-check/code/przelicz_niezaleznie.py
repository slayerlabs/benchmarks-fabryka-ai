"""Niezalezne przeliczenie kluczowych liczb z surowych probek, bez importu zbierz.py i ewaluuj.py.
python przelicz_niezaleznie.py <surowe> <LICZBY.json>. Kod 0 = zgodne, kod 1 = rozjazd."""
import json
import sys
from pathlib import Path

sur, L = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
ZAD = {"T51": ("arc-easy", "acc"), "T05": ("hellaswag", "acc_norm"), "T17": ("lambada", "acc"), "T06": ("piqa", "acc_norm"),
       "T07": ("winogrande", "acc"), "T14": ("wsc273", "acc")}
zle = 0


def probki(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def srednia(p, k):
    w = probki(p)
    return sum(float(s[k]) for s in w) / len(w), len(w)


def sprawdz(opis, a, b):
    global zle
    ok = abs(a - b) < 1e-9
    zle += 0 if ok else 1
    print(f"{opis}: surowe {a:.6f} LICZBY {b:.6f} {'OK' if ok else 'ROZJAZD'}")


def acc_norm_bez_spacji(p):
    """acc_norm jak w metryki.py runnera (dlugosc bez spacji wiodacej), napisane tu osobno. Pole acc_norm probek lm-eval
    dzieli inaczej i na T05 daje 0,469329, wiec nie jest ta sama wielkoscia co metryka manifestu i protokolu."""
    w = probki(p)
    tr = 0
    for s in w:
        k = len(s["arguments"]) // 2
        ll = [float(r[0]) for r in s["filtered_resps"][:k]]
        d = [max(len(a[1].lstrip(" ")), 1) for a in s["arguments"][:k]]
        tr += max(range(k), key=lambda i: ll[i] / d[i]) == int(s["target"])
    return tr / len(w), len(w)


for t, (kat, k) in ZAD.items():
    sciezka = sur / "bos" / kat / "pythia-1b-v0" / "probki" / f"{t}_space.jsonl"
    v, n = acc_norm_bez_spacji(sciezka) if t == "T05" else srednia(sciezka, k)
    sprawdz(f"BOS {t} {k} n={n}", v, L["pary"][t]["nowa"])
v, _ = srednia(sur / "kontrola" / "piqa" / "pythia-1b-v0" / "probki" / "T06_space.jsonl", "acc_norm")
sprawdz("KONTROLA T06", v, L["kontrola"]["value"])
v, _ = srednia(sur / "kontrola-arc" / "arc-challenge" / "eurollm-1.7b" / "probki" / "T02_space.jsonl", "acc_norm")
sprawdz("KONTROLA-ARC T02", v, L["kontrola_arc"]["value"])

a = {s["doc_id"]: float(s["acc_norm"]) for s in probki(sur / "kontrola" / "piqa" / "pythia-1b-v0" / "probki" / "T06_space.jsonl")}
b = {s["doc_id"]: float(s["acc_norm"]) for s in probki(sur / "bos" / "piqa" / "pythia-1b-v0" / "probki" / "T06_space.jsonl")}
popr = sum(1 for i in a if b[i] > a[i])
pogo = sum(1 for i in a if b[i] < a[i])
print(f"T06 pary: poprawione {popr}, pogorszone {pogo}, razem {popr + pogo}; LICZBY zmienione {L['pary']['T06']['w_parach']['zmienione_pytania']}")
zle += 0 if popr + pogo == L["pary"]["T06"]["w_parach"]["zmienione_pytania"] else 1

o = json.loads((sur / "okno" / "wikitext-2" / "pythia-1b-v0" / "results_rozszerzone.json").read_text(encoding="utf-8"))
print("OKNO max_length w pliku:", o.get("max_length"), "byte_perplexity:", o["observations"][0]["value"])
sprawdz("OKNO T03", o["observations"][0]["value"], L["pary"]["T03"]["nowa"])
print("KOD", 1 if zle else 0)
sys.exit(1 if zle else 0)
