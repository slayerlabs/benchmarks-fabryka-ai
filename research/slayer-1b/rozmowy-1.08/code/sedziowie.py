"""Paczka ślepej oceny parami (metryka e): polecenia `otwarte`, odpowiedź z dekodowania s1 (temp 0,7, seed 1),
szablon A, każda para modeli na każdym poleceniu. Kolejność par i strona A/B losowane (random.Random(SEED)).

python -I code/sedziowie.py <katalog_paczki> <plik_klucza>
  paczka: INSTRUKCJA.md (kopia z dane/INSTRUKCJA_SEDZIEGO.md), pary.jsonl, SHA256SUMS — bez nazw modeli
  klucz:  para_id -> model po stronie A i B (poza paczką; sędziowie go nie dostają)
"""
import hashlib
import itertools
import json
import random
import sys
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
SEED = 20261112
MODELE = ["slayer", "bielik", "lfm"]
DEKODOWANIE = "s1"


def wczytaj_gen(klucz):
    out = {}
    for x in (BADANIE / "wyniki" / "surowe" / f"gen_{klucz}_A.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(x)
        if r.get("naglowek"):
            continue
        w = next(w for w in r["wyniki"] if w["dekodowanie"] == DEKODOWANIE)
        out[r["id"]] = w
    return out


def main():
    paczka, plik_klucza = Path(sys.argv[1]), Path(sys.argv[2])
    paczka.mkdir(parents=True, exist_ok=True)
    plik_klucza.parent.mkdir(parents=True, exist_ok=True)
    pozycje = [json.loads(x) for x in (BADANIE / "dane" / "polecenia.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    otwarte = [p for p in pozycje if p["typ"] == "otwarte"]
    gen = {m: wczytaj_gen(m) for m in MODELE}
    rng = random.Random(SEED)
    pary = []
    for p in otwarte:
        for m1, m2 in itertools.combinations(MODELE, 2):
            a, b = (m1, m2) if rng.random() < 0.5 else (m2, m1)
            pary.append((p, a, b))
    rng.shuffle(pary)
    klucz, wiersze = {}, []
    for i, (p, a, b) in enumerate(pary, 1):
        pid = f"P{i:03d}"
        klucz[pid] = dict(id=p["id"], kat=p["kat"], A=a, B=b,
                          koniec_A=gen[a][p["id"]]["koniec"], koniec_B=gen[b][p["id"]]["koniec"])
        wiersze.append(dict(para_id=pid, polecenie=p["polecenie"], kryteria=p["kryteria"],
                            odpowiedz_A=gen[a][p["id"]]["odpowiedz"].strip(),
                            odpowiedz_B=gen[b][p["id"]]["odpowiedz"].strip()))
    (paczka / "pary.jsonl").write_text("".join(json.dumps(w, ensure_ascii=False) + "\n" for w in wiersze), encoding="utf-8")
    (paczka / "INSTRUKCJA.md").write_text((BADANIE / "dane" / "INSTRUKCJA_SEDZIEGO.md").read_text(encoding="utf-8"), encoding="utf-8")
    sumy = "".join(f"{hashlib.sha256((paczka / f).read_bytes()).hexdigest()}  {f}\n" for f in ("INSTRUKCJA.md", "pary.jsonl"))
    (paczka / "SHA256SUMS").write_text(sumy)
    plik_klucza.write_text(json.dumps(dict(seed=SEED, dekodowanie=DEKODOWANIE, pary=klucz), ensure_ascii=False, indent=1),
                           encoding="utf-8")
    print(len(wiersze), "par;", sumy, "klucz sha256", hashlib.sha256(plik_klucza.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
