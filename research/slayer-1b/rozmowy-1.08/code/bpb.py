"""BPB wzorcowej odpowiedzi przy prompcie few-shot (szablony A i B) i sonda EOS po zakończonej odpowiedzi.

python -I code/bpb.py <slayer|bielik|lfm> [--limit N]  -> wyniki/surowe/bpb_<model>.jsonl

Zapisuje surowe składniki (suma log p w nat, liczba bajtów UTF-8 ciągu, liczba tokenów ciągu, flaga granicy
tokenizacji), żeby każdą metrykę dało się przeliczyć bez modelu. Sonda EOS tylko dla typów krótkich.
"""
import json
import sys
import time
from pathlib import Path

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import modele  # noqa: E402
import szablony  # noqa: E402
from generuj import BADANIE, sha256_pliku, wczytaj_zestaw  # noqa: E402

KROTKIE = {"krotka", "zdanie", "liczba"}


def main():
    klucz = sys.argv[1]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    pozycje, shoty = wczytaj_zestaw()
    if limit:
        pozycje = pozycje[:limit]
    t0 = time.time()
    model = modele.wczytaj(klucz)
    katalog = modele.MODELE / modele.REJESTR[klucz][0]
    wyj = BADANIE / "wyniki" / "surowe" / f"bpb_{klucz}{'_dym' if limit else ''}.jsonl"
    with open(wyj, "w", encoding="utf-8") as f:
        f.write(json.dumps(dict(naglowek=True, model=modele.REJESTR[klucz][1], rewizja=modele.REJESTR[klucz][2],
                                urzadzenie=model.device, dtype="float32",
                                wagi_sha256=sha256_pliku(katalog / "model.safetensors"),
                                polecenia_sha256=sha256_pliku(BADANIE / "dane" / "polecenia.jsonl"),
                                shoty_sha256=sha256_pliku(BADANIE / "dane" / "shoty.jsonl"),
                                bpb_sha256=sha256_pliku(Path(__file__)), modele_sha256=sha256_pliku(KOD / "modele.py"),
                                szablony_sha256=sha256_pliku(KOD / "szablony.py"), eos=sorted(model.eos)),
                           ensure_ascii=False) + "\n")
        for p in pozycje:
            wiersz = dict(id=p["id"], kat=p["kat"], typ=p["typ"])
            for sz in ("A", "B"):
                ctx = szablony.prompt(sz, p, shoty[p["kat"]])
                ciag = szablony.ciag_wzorca(sz, p)
                lp, n_tok, zgodna = modele.logprob_ciagu(model, ctx, ciag)
                wiersz[sz] = dict(logprob=lp, bajty=len(ciag.encode("utf-8")), tokeny=n_tok, granica_zgodna=zgodna,
                                  znaki=len(ciag))
            if p["typ"] in KROTKIE:
                for nl in (False, True):
                    pe, ranga = modele.p_nastepnego(model, szablony.prompt_sondy(p, nl), model.eos)
                    wiersz["eos_po_nl" if nl else "eos"] = dict(p=pe, ranga=ranga)
            f.write(json.dumps(wiersz, ensure_ascii=False) + "\n")
            f.flush()
            print(p["id"], round(wiersz["A"]["logprob"], 2), wiersz["A"]["bajty"], flush=True)
    print(f"KONIEC bpb {klucz} {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
