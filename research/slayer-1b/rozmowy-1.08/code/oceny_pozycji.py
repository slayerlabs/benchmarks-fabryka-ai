"""Metryki automatyczne per pozycja × model × dekodowanie z surowych generacji i BPB (bez agregacji i statystyki).

python -I code/oceny_pozycji.py  -> wyniki/oceny_pozycji.jsonl  (+ sha256 wejść w nagłówku)

Ocena (a) wg typu, (c) naturalny koniec, (d) rep3 i distinct-2 (tylko `otwarte`), przecieki i format GSM8K,
długość odpowiedzi w bajtach; BPB (b) i sonda EOS (c2) z bpb_<model>.jsonl. Agregacja i werdykty: osobny skrypt
po ocenie sędziów.
"""
import json
import math
import sys
from pathlib import Path

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import ocena  # noqa: E402
from generuj import BADANIE, sha256_pliku, wczytaj_zestaw  # noqa: E402

MODELE = ["slayer", "bielik", "lfm"]
SUROWE = BADANIE / "wyniki" / "surowe"


def wczytaj_jsonl(p):
    rows = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
    naglowki = [r for r in rows if r.get("naglowek")]  # wznowiony przebieg dopisuje kolejny nagłówek
    return naglowki, {r["id"]: r for r in rows if not r.get("naglowek")}


def ocen(p, odp):
    t = p["typ"]
    if t == "krotka":
        return ocena.ocen_krotka(odp, p["akceptowane"], p["zakazane"])
    if t == "zdanie":
        return ocena.ocen_zdanie(odp, p["akceptowane"])
    if t == "liczba":
        return ocena.ocen_liczba(odp, p["liczba"])
    if t == "kod":
        return ocena.ocen_kod(odp, p["testy"])[0]
    return None


def main():
    pozycje, _ = wczytaj_zestaw()
    wejscia = {}
    out = []
    for m in MODELE:
        gens = {}
        for sz in ("A", "B"):
            f = SUROWE / f"gen_{m}_{sz}.jsonl"
            wejscia[f.name] = sha256_pliku(f)
            gens[sz] = wczytaj_jsonl(f)[1]
        fb = SUROWE / f"bpb_{m}.jsonl"
        wejscia[fb.name] = sha256_pliku(fb)
        bpb = wczytaj_jsonl(fb)[1]
        for p in pozycje:
            b = bpb[p["id"]]
            wiersz = dict(model=m, id=p["id"], kat=p["kat"], typ=p["typ"], trudnosc=p["trudnosc"], dekodowania={})
            for sz in ("A", "B"):
                x = b[sz]
                wiersz[f"bpb_{sz}"] = ocena.bpb(x["logprob"], x["bajty"])
                wiersz[f"nll_na_token_{sz}"] = -x["logprob"] / x["tokeny"]
                wiersz[f"bajty_na_token_{sz}"] = x["bajty"] / x["tokeny"]
                wiersz[f"granica_zgodna_{sz}"] = x["granica_zgodna"]
            for k in ("eos", "eos_po_nl"):
                if k in b:
                    wiersz[f"log10_p_{k}"] = math.log10(max(b[k]["p"], 1e-300))
                    wiersz[f"ranga_{k}"] = b[k]["ranga"]
            for sz in ("A", "B"):
                for w in gens[sz][p["id"]]["wyniki"]:
                    odp = w["odpowiedz"]
                    d = dict(poprawna=ocen(p, odp), koniec=w["koniec"], naturalny_koniec=int(w["koniec"] in ("eos", "stop")),
                             tokeny=w["tokeny"], bajty=len(odp.encode("utf-8")),
                             przeciek=ocena.przeciek_rozumowania(w["surowa"]), format_gsm8k=ocena.format_gsm8k(odp))
                    if p["typ"] == "otwarte":
                        d["rep3"] = ocena.powtorzone_3gramy(odp)
                        d["distinct2"] = ocena.distinct_n(odp, 2)
                    wiersz["dekodowania"][f"{sz}_{w['dekodowanie']}"] = d
            out.append(wiersz)
    wyj = BADANIE / "wyniki" / "oceny_pozycji.jsonl"
    with open(wyj, "w", encoding="utf-8") as f:
        f.write(json.dumps(dict(naglowek=True, wejscia_sha256=wejscia, ocena_sha256=sha256_pliku(KOD / "ocena.py"),
                                polecenia_sha256=sha256_pliku(BADANIE / "dane" / "polecenia.jsonl")), ensure_ascii=False) + "\n")
        for w in out:
            f.write(json.dumps(w, ensure_ascii=False) + "\n")
    print(len(out), "wierszy ->", wyj)


if __name__ == "__main__":
    main()
