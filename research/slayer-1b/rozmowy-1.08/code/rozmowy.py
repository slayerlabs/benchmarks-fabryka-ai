"""ROZMOWY.md: wszystkie 240 poleceń z odpowiedziami trzech modeli (szablon A, seed 1 i greedy), wzorcem i oceną
automatyczną. Pozostałe seedy (2, 3) i szablon B zostają w wyniki/surowe/gen_*.jsonl.gz.

python -I code/rozmowy.py  -> ROZMOWY.md
"""
import gzip
import json
from pathlib import Path

BADANIE = Path(__file__).resolve().parent.parent
MODELE = ["slayer", "bielik", "lfm"]
KAT = ["pl_jezyk", "pl_wiedza", "wiedza_ogolna", "rozumowanie", "matematyka", "kod", "angielski", "tekst_techniczny"]


def jsonl(p):
    """jsonl albo jsonl.gz (w repo leżą wersje .gz surowych wyników; rozpakowane są gitignorowane)."""
    p = Path(p)
    tekst = gzip.decompress(p.read_bytes()).decode("utf-8") if p.suffix == ".gz" else p.read_text(encoding="utf-8")
    return [json.loads(x) for x in tekst.splitlines() if x.strip()]


def blok(tekst):
    """Dosłowna odpowiedź w bloku kodu; potrójny backtick w środku rozbity, żeby nie zamknął bloku."""
    t = tekst.replace("```", "` ` `")
    return "```text\n" + (t if t.strip() else "(pusta odpowiedź)") + ("\n" if not t.endswith("\n") else "") + "```"


def ocena_slownie(typ, v):
    if typ == "otwarte":
        return "bez oceny automatycznej (polecenie otwarte)"
    return "poprawna" if v == 1 else "niepoprawna"


def tresc(L):
    nazwy = L["modele"]
    poz = jsonl(BADANIE / "dane/polecenia.jsonl")
    oceny = {(r["model"], r["id"]): r for r in jsonl(BADANIE / "wyniki/oceny_pozycji.jsonl.gz")[1:]}
    gen = {}
    for m in MODELE:
        for r in jsonl(BADANIE / f"wyniki/surowe/gen_{m}_A.jsonl.gz"):
            if not r.get("naglowek"):
                gen[(m, r["id"])] = {w["dekodowanie"]: w for w in r["wyniki"]}
    out = ["# Rozmowy: wszystkie polecenia i odpowiedzi trzech modeli", "",
           "Plik generuje `code/rozmowy.py` z `dane/polecenia.jsonl`, `wyniki/surowe/gen_*_A.jsonl` i "
           "`wyniki/oceny_pozycji.jsonl`; nie edytuj go ręcznie. Szablon A (few-shot „Polecenie:/Odpowiedź:”), "
           "dwa dekodowania: seed 1 (temperatura 0,7, top-p 0,9) i greedy. Odpowiedź jest dosłowna, po obcięciu "
           "na znaczniku końca szablonu; potrójny backtick w środku odpowiedzi zapisano jako „` ` `”. "
           "Seedy 2 i 3 oraz szablon B są w `wyniki/surowe/`. Ocena automatyczna według reguł z "
           "`code/ocena.py` (protokół, sekcja 4); polecenia otwarte nie mają oceny automatycznej.", "",
           "Modele: " + ", ".join(f"{nazwy[m]} (`{m}`)" for m in MODELE) + ".", ""]
    out.append("## Spis kategorii")
    out.append("")
    for k in KAT:
        out.append(f"- [{k}](#{k.replace('_', '_')})")
    out.append("")
    for k in KAT:
        out.append(f"## {k}")
        out.append("")
        for p in [p for p in poz if p["kat"] == k]:
            out.append(f"### {p['id']} ({p['typ']}, trudność {p['trudnosc']})")
            out.append("")
            out.append("**Polecenie:** " + p["polecenie"].replace("\n", "  \n"))
            out.append("")
            if p["typ"] == "kod":
                out.append("**Wzorzec (rozwiązanie wzorcowe):**")
                out.append("")
                out.append(blok(p["wzorzec"]))
                out.append("")
            else:
                out.append("**Wzorzec:** " + str(p["wzorzec"]).replace("\n", "  \n"))
                out.append("")
            for m in MODELE:
                d = oceny[(m, p["id"])]["dekodowania"]
                for dek, klucz, opis in (("s1", "A_s1", "seed 1"), ("greedy", "A_greedy", "greedy")):
                    w = gen[(m, p["id"])][dek]
                    out.append(f"**{nazwy[m]}, {opis}** — ocena: {ocena_slownie(p['typ'], d[klucz]['poprawna'])}; "
                               f"koniec: {w['koniec']}, tokenów: {w['tokeny']}")
                    out.append("")
                    out.append(blok(w["odpowiedz"]))
                    out.append("")
    return "\n".join(out)


def main():
    L = json.loads((BADANIE / "wyniki/LICZBY.json").read_text(encoding="utf-8"))
    (BADANIE / "ROZMOWY.md").write_text(tresc(L), encoding="utf-8")
    print("ROZMOWY.md: zapisany")


if __name__ == "__main__":
    main()
