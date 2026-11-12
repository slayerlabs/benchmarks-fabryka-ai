"""Audyt oceny automatycznej: próba ocen do oceny przez człowieka (po pomiarze, zlecenie orkiestratora).

python -I code/audyt.py proba   -> dane/audyt_proba.jsonl
  3 oceny na komórkę model × kategoria weryfikowalna (3 × 7 = 21 komórek, 63 oceny; prośba mówiła o 60, 63 daje
  równe komórki), losowo (pozycja, seed s1-s3) przez random.Random(20261113).
python -I code/audyt.py licz    -> wyniki/audyt.json (z dane/audyt_oceny.jsonl: ocena człowieka i powód)
"""
import json
import random
import sys
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
SEED = 20261113
MODELE = ["slayer", "bielik", "lfm"]
KAT = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski"]


def proba():
    poz = {json.loads(x)["id"]: json.loads(x) for x in (BADANIE / "dane/polecenia.jsonl").read_text(encoding="utf-8").splitlines()}
    oceny = [json.loads(x) for x in (BADANIE / "wyniki/oceny_pozycji.jsonl").read_text(encoding="utf-8").splitlines()][1:]
    gen = {}
    for m in MODELE:
        for x in (BADANIE / f"wyniki/surowe/gen_{m}_A.jsonl").read_text(encoding="utf-8").splitlines():
            r = json.loads(x)
            if not r.get("naglowek"):
                gen[(m, r["id"])] = {w["dekodowanie"]: w["odpowiedz"] for w in r["wyniki"]}
    idx = {(o["model"], o["id"]): o for o in oceny}
    rng = random.Random(SEED)
    out = []
    for m in MODELE:
        for k in KAT:
            ids = [i for i, p in poz.items() if p["kat"] == k and p["typ"] != "otwarte"]
            for i, s in rng.sample([(i, s) for i in ids for s in ("s1", "s2", "s3")], 3):
                p = poz[i]
                out.append(dict(audyt_id=f"U{len(out) + 1:02d}", model=m, id=i, kat=k, typ=p["typ"], dekodowanie=s,
                                polecenie=p["polecenie"], wzorzec=p["wzorzec"], akceptowane=p.get("akceptowane"),
                                zakazane=p.get("zakazane"), liczba=p.get("liczba"), testy=p.get("testy"),
                                odpowiedz=gen[(m, i)][s], ocena_auto=idx[(m, i)]["dekodowania"][f"A_{s}"]["poprawna"]))
    (BADANIE / "dane/audyt_proba.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")
    print(len(out))


def licz():
    pr = {json.loads(x)["audyt_id"]: json.loads(x) for x in (BADANIE / "dane/audyt_proba.jsonl").read_text(encoding="utf-8").splitlines()}
    oc = [json.loads(x) for x in (BADANIE / "dane/audyt_oceny.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(oc) == len(pr) and {o["audyt_id"] for o in oc} == set(pr)
    n = len(oc)
    fp = [o["audyt_id"] for o in oc if pr[o["audyt_id"]]["ocena_auto"] == 1 and o["ocena_czlowieka"] == 0]
    fn = [o["audyt_id"] for o in oc if pr[o["audyt_id"]]["ocena_auto"] == 0 and o["ocena_czlowieka"] == 1]
    po_kat = {}
    for o in oc:
        k = pr[o["audyt_id"]]["kat"]
        d = po_kat.setdefault(k, dict(n=0, bledy=0))
        d["n"] += 1
        d["bledy"] += int(pr[o["audyt_id"]]["ocena_auto"] != o["ocena_czlowieka"])
    wynik = dict(seed=SEED, n=n, zgodnosc=(n - len(fp) - len(fn)) / n, odsetek_bledow=(len(fp) + len(fn)) / n,
                 falszywe_trafienia=len(fp), falszywe_odrzucenia=len(fn), falszywe_trafienia_id=fp,
                 falszywe_odrzucenia_id=fn, auto_poprawnych=sum(p["ocena_auto"] for p in pr.values()),
                 czlowiek_poprawnych=sum(o["ocena_czlowieka"] for o in oc), po_kategoriach=po_kat,
                 bledy_szczegoly=[dict(audyt_id=o["audyt_id"], model=pr[o["audyt_id"]]["model"], id=pr[o["audyt_id"]]["id"],
                                       auto=pr[o["audyt_id"]]["ocena_auto"], czlowiek=o["ocena_czlowieka"], powod=o["powod"])
                                  for o in oc if pr[o["audyt_id"]]["ocena_auto"] != o["ocena_czlowieka"]])
    (BADANIE / "wyniki/audyt.json").write_text(json.dumps(wynik, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in wynik.items() if k != "bledy_szczegoly"}, ensure_ascii=False))


if __name__ == "__main__":
    {"proba": proba, "licz": licz}[sys.argv[1]]()
