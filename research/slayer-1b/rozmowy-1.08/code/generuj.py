"""Generacje jednego modelu na całym zestawie. Ta sama pętla losowania dla wszystkich modeli.

python -I code/generuj.py <slayer|bielik|lfm> <A|B> [--limit N]  -> wyniki/surowe/gen_<model>_<szablon>.jsonl

Szablon A: jeden batch na polecenie, 4 wiersze = próbkowanie seed 1, 2, 3 (temp 0,7, top-p 0,9) + greedy.
Szablon B (kontrola wrażliwości): tylko greedy. Próbkowanie na CPU, float32, generator torch per wiersz z seedem
SEED_BAZA * seed + numer pozycji w pliku poleceń. Stop: token EOS modelu, napis stopu szablonu albo limit tokenów typu.
Plik jest dopisywany; pozycje już zapisane są pomijane (wznowienie po przerwaniu).
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import torch

KOD = Path(__file__).resolve().parent
sys.path.insert(0, str(KOD))
import modele  # noqa: E402
import szablony  # noqa: E402

BADANIE = KOD.parent
SEED_BAZA = 1_000_003
DEKODOWANIA_A = [dict(nazwa=f"s{s}", temperatura=0.7, top_p=0.9, seed=s) for s in (1, 2, 3)] + \
                [dict(nazwa="greedy", temperatura=0.0, top_p=1.0, seed=0)]
DEKODOWANIA_B = [dict(nazwa="greedy", temperatura=0.0, top_p=1.0, seed=0)]


def sha256_pliku(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for kawal in iter(lambda: f.read(1 << 22), b""):
            h.update(kawal)
    return h.hexdigest()


def wczytaj_zestaw():
    pozycje = [json.loads(x) for x in (BADANIE / "dane" / "polecenia.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    shoty = [json.loads(x) for x in (BADANIE / "dane" / "shoty.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    po_kat = {}
    for s in shoty:
        po_kat.setdefault(s["kat"], []).append(s)
    return pozycje, po_kat


def wybierz_token(logity, dek, gen):
    if dek["temperatura"] <= 0:
        return int(logity.argmax())
    p = torch.softmax(logity / dek["temperatura"], -1)
    ps, idx = p.sort(descending=True)
    cum = ps.cumsum(-1)
    ps[(cum - ps) > dek["top_p"]] = 0
    return int(idx[torch.multinomial(ps / ps.sum(), 1, generator=gen)])


@torch.no_grad()
def generuj_batch(model, tekst, dekodowania, nr_pozycji, max_nowych, stop_napisy):
    ids = model.encode(tekst)
    B = len(dekodowania)
    gens = [torch.Generator().manual_seed(SEED_BAZA * d["seed"] + nr_pozycji) for d in dekodowania]
    t0 = time.time()
    logity = model.start(ids, B)
    nowe = [[] for _ in range(B)]
    koniec = [None] * B
    for _ in range(max_nowych):
        toks = []
        for r in range(B):
            if koniec[r]:
                toks.append(next(iter(model.eos)))
                continue
            t = wybierz_token(logity[r], dekodowania[r], gens[r])
            toks.append(t)
            if t in model.eos:
                koniec[r] = "eos"
                continue
            nowe[r].append(t)
            ogon = model.decode(nowe[r][-24:])
            if any(s in ogon for s in stop_napisy) and szablony.utnij(model.decode(nowe[r]), stop_napisy)[1]:
                koniec[r] = "stop"
        if all(koniec):
            break
        if len(ids) + len(nowe[0]) + 1 >= model.limit:
            break
        logity = model.krok(toks)
    sek = time.time() - t0
    wyn = []
    for r, d in enumerate(dekodowania):
        surowy = model.decode(nowe[r])
        uciety, _ = szablony.utnij(surowy, stop_napisy)
        wyn.append(dict(dekodowanie=d["nazwa"], seed=d["seed"], odpowiedz=uciety, surowa=surowy,
                        tokeny=len(nowe[r]), koniec=koniec[r] or "limit"))
    return wyn, sek, len(ids)


def main():
    klucz, szablon = sys.argv[1], sys.argv[2]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    pozycje, shoty = wczytaj_zestaw()
    if limit:
        pozycje = pozycje[:limit]
    dekodowania = DEKODOWANIA_A if szablon == "A" else DEKODOWANIA_B
    wyj = BADANIE / "wyniki" / "surowe" / f"gen_{klucz}_{szablon}{'_dym' if limit else ''}.jsonl"
    wyj.parent.mkdir(parents=True, exist_ok=True)
    gotowe = set()
    if wyj.exists():
        gotowe = {json.loads(x)["id"] for x in wyj.read_text(encoding="utf-8").splitlines() if x.strip() and '"id"' in x}
    t0 = time.time()
    model = modele.wczytaj(klucz)
    katalog = modele.MODELE / modele.REJESTR[klucz][0]
    naglowek = dict(
        naglowek=True, model=modele.REJESTR[klucz][1], rewizja=modele.REJESTR[klucz][2], klucz=klucz, szablon=szablon,
        urzadzenie=model.device, dtype="float32", torch=torch.__version__,
        wagi_sha256=sha256_pliku(katalog / "model.safetensors"),
        tokenizer_sha256=sha256_pliku(katalog / "tokenizer.json"),
        polecenia_sha256=sha256_pliku(BADANIE / "dane" / "polecenia.jsonl"),
        shoty_sha256=sha256_pliku(BADANIE / "dane" / "shoty.jsonl"),
        generuj_sha256=sha256_pliku(Path(__file__)), szablony_sha256=sha256_pliku(KOD / "szablony.py"),
        modele_sha256=sha256_pliku(KOD / "modele.py"), dekodowania=dekodowania, seed_baza=SEED_BAZA,
        max_tokenow=szablony.MAX_TOKENOW, eos=sorted(model.eos), wczytanie_s=round(time.time() - t0, 1))
    print(json.dumps(naglowek, ensure_ascii=False), flush=True)
    with open(wyj, "a", encoding="utf-8") as f:
        f.write(json.dumps(naglowek, ensure_ascii=False) + "\n")
        for nr, p in enumerate(pozycje):
            if p["id"] in gotowe:
                continue
            tekst = szablony.prompt(szablon, p, shoty[p["kat"]])
            wyn, sek, n_prompt = generuj_batch(model, tekst, dekodowania, nr, szablony.MAX_TOKENOW[p["typ"]],
                                               szablony.stopy(szablon, p["kat"]))
            f.write(json.dumps(dict(id=p["id"], kat=p["kat"], typ=p["typ"], nr=nr, tokeny_promptu=n_prompt,
                                    sekundy=round(sek, 2), wyniki=wyn), ensure_ascii=False) + "\n")
            f.flush()
            print(f"{p['id']} {sek:.1f}s " + " ".join(f"{w['dekodowanie']}:{w['tokeny']}/{w['koniec']}" for w in wyn),
                  flush=True)
    print(f"KONIEC {klucz} {szablon} {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
