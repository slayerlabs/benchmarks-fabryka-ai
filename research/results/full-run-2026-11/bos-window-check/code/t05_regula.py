"""T05 BOS: acc_norm z probek dwiema regulami dlugosci opcji, bez kodu ewaluuj.py. python t05_regula.py <probki.jsonl> <oczekiwana>"""
import json
import sys

w = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
tr_lm, tr_lstrip, roznice = 0, 0, 0
for s in w:
    k = len(s["arguments"]) // 2
    conts = [a[1] for a in s["arguments"][:k]]
    ll = [float(r[0]) for r in s["filtered_resps"][:k]]
    gold = int(s["target"])
    z_lm = [ll[i] / len(conts[i]) for i in range(k)]
    z_ls = [ll[i] / max(len(conts[i].lstrip(" ")), 1) for i in range(k)]
    a, b = max(range(k), key=lambda i: z_lm[i]), max(range(k), key=lambda i: z_ls[i])
    tr_lm += a == gold
    tr_lstrip += b == gold
    roznice += a != b
n = len(w)
print(f"n {n}; dlugosc z separatorem (kontynuacja) {tr_lm / n:.6f}; dlugosc bez spacji wiodacej {tr_lstrip / n:.6f}; decyzje rozne {roznice}")
print("pole acc_norm w probkach:", round(sum(float(s['acc_norm']) for s in w) / n, 6), "| LICZBY:", sys.argv[2])
