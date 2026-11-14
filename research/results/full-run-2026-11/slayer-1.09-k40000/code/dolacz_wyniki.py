"""Eksport instancji → repo i z powrotem. Surowe wyniki obu etykiet są w repo (próbki, trace i podsumowanie jako gzip),
więc LICZBY.json da się odtworzyć bez paczki spoza repo.

    python dolacz_wyniki.py dolacz <rozpakowany eksport> <results/full-run-2026-11>
    python dolacz_wyniki.py odtworz <results/full-run-2026-11> <katalog roboczy>

`dolacz` (raz, przed LICZBY.json):
- sprawdza sha256 każdego pliku `wyniki/` eksportu wobec `probki_sha256.json` (zapisanego przez zrob_sha.py przed
  raportem) i wobec pola `pliki` wiersza `manifest.jsonl` eksportu; jakakolwiek różnica → SystemExit, nic nie zapisane;
- 1.09 k40000: `<test>/slayer1b-1.09-k40000/` w formacie reszty przebiegu (`results.json`, `results_rozszerzone.json`,
  `scores-history-wiersz.csv`) plus surowe pliki gzip: `probki/*.jsonl.gz`, `trace/*.jsonl.gz`, `podsumowanie.md.gz`;
  wiersze 1.09 dopisane na koniec `manifest.jsonl` i `czasy.jsonl` przebiegu (reszta tych plików bez zmian);
- 1.08 przeliczone: te same pliki w `slayer-1.09-k40000/wyniki/<test>/slayer1b-1.08/`; jego wiersze NIE wchodzą do
  manifestu przebiegu (wartości 1.08 w tabeli zostają z przebiegu, PROTOKOL.md);
- `manifest.jsonl`, `srodowisko.json`, `czasy.jsonl` eksportu bez zmian do `slayer-1.09-k40000/eksport/`, logi par
  jako `slayer-1.09-k40000/logi/*.log.gz`;
- sha256 każdego zapisanego pliku gzip dopisuje do `probki_sha256.json` (klucz `pliki_gz`, ścieżki względem
  results/full-run-2026-11); klucze `pliki`, `paczka` i `srodowisko` zostają bez zmian.
Odmawia, gdy przebieg ma już wiersze 1.09 albo katalog 1.09 istnieje (drugie dołączenie dublowałoby wiersze).

`odtworz`: składa z plików repo katalog w układzie eksportu (manifest.jsonl, srodowisko.json, czasy.jsonl,
wyniki/<test>/<etykieta>/...) i sprawdza sha256 każdego rozpakowanego pliku wobec `probki_sha256.json`. Kod 0 tylko
przy pełnej zgodności: wtedy liczby_109.py i przelicz_niezaleznie.py liczą na bajtach identycznych z eksportem.

gzip: poziom 9, mtime 0, bez nazwy pliku w nagłówku (jak `gzip -9 -n`), więc ten sam plik daje te same bajty.
"""
import gzip
import hashlib
import json
import sys
from pathlib import Path

A, B = "slayer1b-1.09-k40000", "slayer1b-1.08"
KATALOG = "slayer-1.09-k40000"
JAWNE = ("results.json", "results_rozszerzone.json", "scores-history-wiersz.csv")
PLIKI_EKSPORTU = ("manifest.jsonl", "srodowisko.json", "czasy.jsonl")
MAKS_GZ = 50 * 1024 * 1024


def sha256_bajtow(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def gz(b: bytes) -> bytes:
    return gzip.compress(b, compresslevel=9, mtime=0)


def wiersze(p: Path) -> list:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def katalog_w_repo(cel: Path, model: str, bench: str) -> Path:
    """Gdzie w repo leżą pliki wyniku: 1.09 w katalogu testu przebiegu, 1.08 przeliczone w katalogu pomiaru."""
    if model == A:
        return cel / bench / A
    if model == B:
        return cel / KATALOG / "wyniki" / bench / B
    raise SystemExit(f"nieznana etykieta {model}")


def nazwa_w_repo(wzgl: str) -> str:
    """Ścieżka pliku względem katalogu wyniku → nazwa w repo (surowe i podsumowanie jako .gz)."""
    return wzgl if wzgl in JAWNE else wzgl + ".gz"


def sprawdz_wejscie(eksport: Path, sumy: dict, manifest: list) -> None:
    pliki = {p.relative_to(eksport).as_posix() for p in (eksport / "wyniki").rglob("*") if p.is_file()}
    if pliki != set(sumy["pliki"]):
        raise SystemExit(f"pliki eksportu różne od probki_sha256.json: nadmiar {sorted(pliki - set(sumy['pliki']))[:5]}, "
                         f"brak {sorted(set(sumy['pliki']) - pliki)[:5]}")
    zle = [p for p in sorted(pliki) if sha256_bajtow((eksport / p).read_bytes()) != sumy["pliki"][p]]
    if zle:
        raise SystemExit(f"sha256 różne od probki_sha256.json: {zle[:5]}")
    for w in manifest:
        for wzgl, s in (w.get("pliki") or {}).items():
            p = f"{w['katalog']}/{wzgl}"
            if sumy["pliki"].get(p) != s:
                raise SystemExit(f"{p}: sha256 w manifest.jsonl eksportu różne od pliku")
    pary = {(w["benchmark"], w["model"]) for w in manifest}
    if len(pary) != len(manifest) or {m for _, m in pary} != {A, B}:
        raise SystemExit("manifest eksportu: zdublowana para albo inne etykiety niż 1.09 k40000 i 1.08")


def dolacz(eksport: Path, cel: Path) -> dict:
    pomiar = cel / KATALOG
    sumy_p = pomiar / "probki_sha256.json"
    sumy = json.loads(sumy_p.read_text(encoding="utf-8"))
    manifest = wiersze(eksport / "manifest.jsonl")
    sprawdz_wejscie(eksport, sumy, manifest)
    manifest_przebiegu = cel / "manifest.jsonl"
    stary = manifest_przebiegu.read_text(encoding="utf-8")
    if any(w["model"] == A for w in wiersze(manifest_przebiegu)):
        raise SystemExit(f"{manifest_przebiegu} ma już wiersze {A}")
    for w in manifest:
        if w["model"] == A and katalog_w_repo(cel, A, w["benchmark"]).exists():
            raise SystemExit(f"{katalog_w_repo(cel, A, w['benchmark'])} już istnieje")
    pliki_gz = {}
    for w in manifest:
        zrodlo, dokad = eksport / w["katalog"], katalog_w_repo(cel, w["model"], w["benchmark"])
        for p in sorted(zrodlo.rglob("*")):
            if not p.is_file():
                continue
            wzgl = p.relative_to(zrodlo).as_posix()
            cel_p = dokad / nazwa_w_repo(wzgl)
            cel_p.parent.mkdir(parents=True, exist_ok=True)
            dane = p.read_bytes()
            if wzgl in JAWNE:
                cel_p.write_bytes(dane)
                continue
            z = gz(dane)
            if len(z) > MAKS_GZ:
                raise SystemExit(f"{cel_p}: {len(z)} B po gzip, ponad limit {MAKS_GZ}")
            cel_p.write_bytes(z)
            pliki_gz[cel_p.relative_to(cel).as_posix()] = sha256_bajtow(z)
    (pomiar / "eksport").mkdir(parents=True, exist_ok=True)
    for f in PLIKI_EKSPORTU:
        (pomiar / "eksport" / f).write_bytes((eksport / f).read_bytes())
    for p in sorted((eksport / "logi").glob("*")) if (eksport / "logi").exists() else []:
        if p.is_file():
            cel_p = pomiar / "logi" / (p.name + ".gz")
            cel_p.parent.mkdir(parents=True, exist_ok=True)
            z = gz(p.read_bytes())
            cel_p.write_bytes(z)
            pliki_gz[cel_p.relative_to(cel).as_posix()] = sha256_bajtow(z)
    linie = lambda ws: "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in ws)
    nowe = [w for w in manifest if w["model"] == A]
    manifest_przebiegu.write_text(stary + ("" if stary.endswith("\n") or not stary else "\n") + linie(nowe),
                                  encoding="utf-8")
    czasy = cel / "czasy.jsonl"
    stare_czasy = czasy.read_text(encoding="utf-8")
    nowe_czasy = [w for w in wiersze(eksport / "czasy.jsonl") if w.get("model") == A]
    czasy.write_text(stare_czasy + ("" if stare_czasy.endswith("\n") or not stare_czasy else "\n") + linie(nowe_czasy),
                     encoding="utf-8")
    sumy["pliki_gz"] = dict(sorted(pliki_gz.items()))
    sumy_p.write_text(json.dumps(sumy, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"manifest": len(nowe), "czasy": len(nowe_czasy), "gz": len(pliki_gz),
            "bajty_gz": sum((cel / p).stat().st_size for p in pliki_gz)}


def odtworz(cel: Path, roboczy: Path, testy=None) -> list:
    """Katalog w układzie eksportu z plików repo; zwraca listę rozjazdów sha256 (pusta = zgodne).
    `testy`: tylko te katalogi testów i ich wiersze manifestu (testy na danych rzeczywistych); domyślnie wszystko."""
    pomiar = cel / KATALOG
    sumy = json.loads((pomiar / "probki_sha256.json").read_text(encoding="utf-8"))
    roboczy.mkdir(parents=True, exist_ok=True)
    for f in PLIKI_EKSPORTU:
        (roboczy / f).write_bytes((pomiar / "eksport" / f).read_bytes())
    if testy is not None:
        ws = [x for x in (roboczy / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
              if x.strip() and json.loads(x)["benchmark"] in testy]
        (roboczy / "manifest.jsonl").write_text("".join(x + "\n" for x in ws), encoding="utf-8")
    rozjazdy = []
    for p, s in sumy["pliki"].items():
        _, bench, model, wzgl = p.split("/", 3)
        if testy is not None and bench not in testy:
            continue
        zrodlo = katalog_w_repo(cel, model, bench) / nazwa_w_repo(wzgl)
        if not zrodlo.exists():
            rozjazdy.append(f"{p}: brak {zrodlo.relative_to(cel)}")
            continue
        dane = zrodlo.read_bytes()
        if wzgl not in JAWNE:
            dane = gzip.decompress(dane)
        if sha256_bajtow(dane) != s:
            rozjazdy.append(f"{p}: sha256 różne od probki_sha256.json")
        (roboczy / p).parent.mkdir(parents=True, exist_ok=True)
        (roboczy / p).write_bytes(dane)
    return rozjazdy


def main():
    tryb = sys.argv[1]
    if tryb == "dolacz":
        r = dolacz(Path(sys.argv[2]), Path(sys.argv[3]))
        print(f"{A}: {r['manifest']} wierszy manifestu, {r['czasy']} wierszy czasów; plików gzip {r['gz']}, "
              f"{r['bajty_gz']} B")
        return 0
    if tryb == "odtworz":
        rozjazdy = odtworz(Path(sys.argv[2]), Path(sys.argv[3]))
        print("\n".join(rozjazdy) if rozjazdy else f"odtworzone w {sys.argv[3]}: sha256 zgodne z probki_sha256.json")
        return 1 if rozjazdy else 0
    raise SystemExit(f"nieznany tryb {tryb}: dolacz albo odtworz")


if __name__ == "__main__":
    raise SystemExit(main())
