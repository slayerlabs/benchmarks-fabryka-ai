"""LICZBY.json pomiaru 1.09 krok 40 000 wobec 1.08 (PROTOKOL.md): jedyne źródło liczb RAPORT.md i wykresów.

    python liczby_109.py <eksport z próbkami> <manifest.jsonl przebiegu> <probki_sha256.json> <LICZBY.json> [dodatki.json]

Najpierw sha256 każdego pliku eksportu wobec `probki_sha256.json` (zapisanego przed raportem). Porównanie parowane
`porownaj` z tools/ewaluacja/raport.py (metoda progresja.json, jak każe protokół), Holm z m = 15 z protokołu,
kontrola narzędzia: 1.08 przeliczone − 1.08 z manifestu przebiegu w SE testu, próg 0,5 SE i równe n.
"""
import hashlib
import json
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
RESEARCH = TU.parents[3]
sys.path[:0] = [str(RESEARCH / "tools" / "ewaluacja"), str(RESEARCH / "tools"), str(RESEARCH / "common")]
import kontrola_sensu as KS  # noqa: E402
import raport as R  # noqa: E402
import statystyka as S  # noqa: E402

A, B = "slayer1b-1.09-k40000", "slayer1b-1.08"
TESTY = {"arc-challenge": "T02", "arc-easy": "T51", "blimp": "T01", "ewok": "T53", "hellaswag": "T05", "lambada": "T17",
         "mathqa": "T19", "medmcqa": "T45", "multiblimp-pl": "T04", "piqa": "T06", "pubmedqa": "T44", "social-iqa": "T46",
         "wikitext-2": "T03", "winogrande": "T07", "wsc273": "T14"}
M_HOLM = 15
PROG_KONTROLI_SE = 0.5
MAKS_NIEZGODNYCH = 3
NIEROZSTRZYGNIETE_KONTROLA = "nierozstrzygnięte (kontrola narzędzia)"


def sha256_pliku(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for kawalek in iter(lambda: f.read(1 << 20), b""):
            h.update(kawalek)
    return h.hexdigest()


def sprawdz_sumy(eksport: Path, sumy: dict):
    """Każdy plik w wyniki/ eksportu jest w spisie i ma jego sumę; inaczej SystemExit przed liczeniem."""
    pliki = {str(p.relative_to(eksport)).replace("\\", "/") for p in (eksport / "wyniki").rglob("*") if p.is_file()}
    spis = set(sumy["pliki"])
    if pliki != spis:
        raise SystemExit(f"spis sum różny od plików eksportu: brak w spisie {sorted(pliki - spis)[:5]}, "
                         f"brak plików {sorted(spis - pliki)[:5]}")
    zle = [p for p in sorted(spis) if sha256_pliku(eksport / p) != sumy["pliki"][p]]
    if zle:
        raise SystemExit(f"sha256 różne od probki_sha256.json: {zle[:5]}")


def kontrola(przeliczone: dict, manifest: dict) -> dict:
    """1.08 przeliczone wobec manifestu przebiegu, w skali pliku wyników (MultiBLiMP w %)."""
    skala = przeliczone["skala_w_pliku"]
    roznica = przeliczone["wartosc"] * skala - manifest["wartosc"]
    w_se = roznica / manifest["se"] if manifest["se"] else None
    n_zgodne = przeliczone["n"] == manifest["n"]
    return {"roznica": roznica / skala, "w_se": w_se, "n_zgodne": n_zgodne, "prog_se": PROG_KONTROLI_SE,
            "zgodna": n_zgodne and w_se is not None and abs(w_se) <= PROG_KONTROLI_SE}


def wynik_koncowy(porownanie: dict, wyzej_lepiej: bool, zgodna: bool) -> tuple:
    """(werdykt protokołu, kierunek): lepszy/gorszy tylko przy „pewne” albo „prawdopodobne” po Holmie."""
    if not zgodna:
        return NIEROZSTRZYGNIETE_KONTROLA, None
    w = porownanie["werdykt_holm"]
    if w not in ("pewne", "prawdopodobne"):
        return ("szum" if porownanie.get("p") is not None else S.NIEROZSTRZYGALNE), None
    lepiej = porownanie["roznica"] > 0 if wyzej_lepiej else porownanie["roznica"] < 0
    return f"{'lepszy' if lepiej else 'gorszy'} ({w})", "lepiej" if lepiej else "gorzej"


def podsumuj(testy: list) -> dict:
    grupy = {"lepsze": [], "gorsze": [], "szum": [], "nierozstrzygniete": []}
    for t in testy:
        klucz = {"lepiej": "lepsze", "gorzej": "gorsze"}.get(t["kierunek"]) or (
            "szum" if t["werdykt_koncowy"] == "szum" else "nierozstrzygniete")
        grupy[klucz].append(t["nazwa"])
    niezgodne = [t["nazwa"] for t in testy if not t["kontrola"]["zgodna"]]
    caly = len(niezgodne) > MAKS_NIEZGODNYCH
    zdanie = (f"Po Holmie (m = {M_HOLM}) Slayer 1B 1.09 z kroku 40 000 jest lepszy od 1.08 na {len(grupy['lepsze'])} "
              f"z {len(testy)} testów, gorszy na {len(grupy['gorsze'])}, w szumie na {len(grupy['szum'])}, "
              f"nierozstrzygnięty na {len(grupy['nierozstrzygniete'])}.")
    if caly:
        zdanie = (f"Cały wynik nierozstrzygnięty: kontrola narzędzia niezgodna na {len(niezgodne)} testach "
                  f"(więcej niż {MAKS_NIEZGODNYCH}).")
    return {**grupy, "kontrole_niezgodne": niezgodne, "caly_wynik_nierozstrzygniety": caly, "twierdzenie": zdanie,
            "obalenie": "inny podział lepsze/gorsze/szum po przeliczeniu niezależnym kodem z tych samych próbek "
                        "albo niezgodna kontrola narzędzia na teście z werdyktem"}


def zbuduj(eksport: Path, manifest_przebiegu: Path, sumy_plik: Path) -> dict:
    sumy = json.loads(sumy_plik.read_text(encoding="utf-8"))
    sprawdz_sumy(eksport, sumy)
    wyniki = {(w["benchmark"], w["model"]): w for w in R.wczytaj_wyniki(eksport)}
    manifest = {w["benchmark"]: w for w in map(json.loads, manifest_przebiegu.read_text(encoding="utf-8").splitlines())
                if w["model"] == B}
    oceny = R.Oceny()
    testy = []
    for bench, zad in TESTY.items():
        a, b = wyniki[(bench, A)], wyniki[(bench, B)]
        m = manifest[bench]
        assert a["zadanie"] == b["zadanie"] == m["zadanie"] == zad, bench
        p = R.porownaj(oceny, eksport, a, b)
        if p is None:
            raise SystemExit(f"{bench}: brak próbek per pytanie w eksporcie")
        skala = b["skala_w_pliku"]
        testy.append({
            "benchmark": bench, "zadanie": zad, "nazwa": R.TEST_NAMES[bench][0], "metryka": b["metryka"],
            "wyzej_lepiej": b["wyzej_lepiej"], "chance": b["chance"], "majority": b["majority"],
            "v108_manifest": {"wartosc": m["wartosc"] / skala, "se": m["se"] / skala, "n": m["n"],
                              "results_sha256": m["results_sha256"]},
            "v108_przeliczone": {"wartosc": b["wartosc"], "se": b["se"], "n": b["n"]},
            "v109": {"wartosc": a["wartosc"], "se": a["se"], "n": a["n"]},
            "kontrola": kontrola(b, m),
            "porownanie": {k: p.get(k) for k in ("n", "roznica", "roznica_srednia", "roznica_bpb", "se", "z", "t", "df",
                                                 "k", "p", "werdykt", "metoda")},
            "kontrola_sensu": {mod: KS.bledy_obserwacji(json.loads((eksport / w["katalog"] / "results_rozszerzone.json")
                                                                   .read_text(encoding="utf-8"))["observations"][0])
                               for mod, w in ((A, a), (B, b))},
        })
    for t, h in zip(testy, S.po_holmie([t["porownanie"]["p"] for t in testy], m=M_HOLM)):
        t["porownanie"].update(h)
        t["werdykt_koncowy"], t["kierunek"] = wynik_koncowy(t["porownanie"], t["wyzej_lepiej"], t["kontrola"]["zgodna"])
    return {"protokol": "PROTOKOL.md", "etykieta": R.W_TOKU[A][1], "model": A, "odniesienie": B, "m_holm": M_HOLM,
            "wejscia": {"probki_sha256": sha256_pliku(sumy_plik), "manifest_przebiegu": sha256_pliku(manifest_przebiegu),
                        "paczka": sumy.get("paczka")},
            "srodowisko": sumy.get("srodowisko"), "testy": testy, "podsumowanie": podsumuj(testy)}


def main():
    eksport, manifest, sumy, wyj = map(Path, sys.argv[1:5])
    liczby = zbuduj(eksport, manifest, sumy)
    if len(sys.argv) > 5:  # odstepstwa i not_run: zdania bez liczb, spisane przed raportem
        dodatki = json.loads(Path(sys.argv[5]).read_text(encoding="utf-8"))
        liczby.update({k: dodatki[k] for k in ("odstepstwa", "not_run") if k in dodatki})
    wyj.write_text(json.dumps(liczby, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(liczby["podsumowanie"]["twierdzenie"])


if __name__ == "__main__":
    main()
