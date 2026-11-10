"""LICZBY.json z surowych wynikow pomiaru (PROTOKOL.md @ 7f09124). Jedyne zrodlo liczb raportu.

python zbierz.py <surowe> <manifest.jsonl> <LICZBY.json> <sha_wejsc.json> [faktura.json]
<surowe>/{kontrola,bos,okno,kontrola-arc}/<benchmark>/<model>/...
sha_wejsc.json (zrob_sha_wejsc.py) przypina kazdy plik wejscia; niezgodnosc konczy liczenie kodem 1.
"""
import gzip
import hashlib
import json
import math
import sys
from pathlib import Path

SZESC = ["T51", "T05", "T17", "T06", "T07", "T14"]
KATALOG = {"T51": "arc-easy", "T05": "hellaswag", "T17": "lambada", "T06": "piqa", "T07": "winogrande",
           "T14": "wsc273", "T03": "wikitext-2", "T02": "arc-challenge"}
STARE = {"T51": 0.558502, "T05": 0.467935, "T17": 0.565690, "T06": 0.709467, "T07": 0.544594, "T14": 0.673993,
         "T03": 2.423435}
PROG_WPLYW = 0.04
ARC_ODN = 0.4061
ARC_PROG = 0.0286


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def czytaj_jsonl(p):
    p = Path(p)
    if not p.exists() and Path(str(p) + ".gz").exists():
        p = Path(str(p) + ".gz")
    if not p.exists():
        return None
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt", encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def plik_jsonl(p):
    p = Path(p)
    return p if p.exists() else Path(str(p) + ".gz")


def werdykt_z(z):
    a = abs(z)
    return "pewne" if a >= 3 else "prawdopodobne" if a >= 2 else "szum"


def obserwacja(kat):
    p = Path(kat) / "results_rozszerzone.json"
    if not p.exists():
        return None
    o = json.loads(p.read_text(encoding="utf-8"))["observations"][0]
    sp = o["dodatkowe"]["space"]
    klucz = o["metric"].split(",")[0]
    g = sp.get("glowna") or sp[klucz]
    ref = o.get("reference") or {}
    return {"value": o["value"], "se": g["se"], "n": o["n_scored"], "state": o["state"], "metric": o["metric"],
            "results_sha256": o["results_sha256"], "runner_sha256": o["runner_sha256"],
            "chance": ref.get("chance_value"), "majority": ref.get("majority_value"),
            "plik": str(p), "sha_pliku": sha(p), "klucz": klucz, "se_a": g.get("se_a"), "metoda_se": g.get("metoda_se")}


def poboczne(p):
    sp = json.loads(Path(p).read_text(encoding="utf-8"))["observations"][0]["dodatkowe"]["space"]
    return {"bpb_poprawnej": sp["bpb_poprawnej"]["value"], "udzial_najczestszej_predykcji": sp["udzial_najczestszej_predykcji"]}


def sprawdz_wejscia(plik, sur, manifest, stary_wsc):
    """Przed liczeniem: sha manifestu, starego WSC273 i kazdego pliku surowego; brak, nadmiar albo rozjazd = kod 1."""
    z = json.loads(Path(plik).read_text(encoding="utf-8"))
    bledy = []
    if sha(manifest) != z["manifest"]:
        bledy.append("manifest")
    if sha(stary_wsc) != z["wsc273_stary"]:
        bledy.append("wsc273_stary")
    na_dysku = {str(p.relative_to(sur)): p for p in Path(sur).rglob("*") if p.is_file()}
    for nazwa in sorted(set(na_dysku) ^ set(z["surowe"])):
        bledy.append(f"zbior plikow: {nazwa}")
    for nazwa, oczek in z["surowe"].items():
        if nazwa in na_dysku and sha(na_dysku[nazwa]) != oczek:
            bledy.append(f"sha: {nazwa}")
    if bledy:
        print("NIEZGODNE WEJSCIA:\n" + "\n".join(bledy[:20]), file=sys.stderr)
        sys.exit(1)


def demonstracje(kat):
    """Liczba demonstracji w prompcie per pytanie i czy tresc demonstracji pochodzi ze splitu testu."""
    p = czytaj_jsonl(Path(kat) / "probki" / "T02_space.jsonl") or []
    testowe = {s["doc"]["question"] for s in p}
    rozklad, spoza = {}, 0
    for s in p:
        czesci = s["arguments"][0][0].split("Question: ")[1:]
        n = len(czesci) - 1
        rozklad[str(n)] = rozklad.get(str(n), 0) + 1
        spoza += sum(1 for c in czesci[:-1] if c.split("\nAnswer:")[0] not in testowe)
    return {"pytan": len(p), "rozklad_liczby_demonstracji": dict(sorted(rozklad.items())), "demonstracje_spoza_testu": spoza}


def kontrola_sensu(ob):
    if ob["metric"].startswith("byte_perplexity"):
        return ob["value"] > 1.0
    if ob["value"] == 1.0:
        return False
    return ob["chance"] is None or ob["value"] >= ob["chance"] - 0.05


def trafienia(kat, zad, klucz):
    w = czytaj_jsonl(Path(kat) / "probki" / f"{zad}_space.jsonl")
    return None if w is None else {s["doc_id"]: float(s[klucz]) for s in w}


def bos_kontrola(kat, zad):
    w = czytaj_jsonl(Path(kat) / "bos.jsonl")
    if w is None:
        return None
    z = [r for r in w if r["t"] == "z"]
    m = [r for r in w if r["t"] == "m"]
    pr = czytaj_jsonl(Path(kat) / "probki" / f"{zad}_space.jsonl") or []
    zad_prob = sum(len(s.get("arguments", [])) for s in pr)
    return {"zadan_w_dzienniku": len(z), "zadan_w_probkach": zad_prob, "zgodne": len(z) == zad_prob,
            "zadan_z_jednym_bos": sum(1 for r in z if r["n"] == 1 and r["w"] == 1),
            "wywolan_modelu": len(m), "wywolan_z_jednym_bos": sum(1 for r in m if r["n"] == 1),
            "procent_jeden_bos": (100.0 * sum(1 for r in z if r["n"] == 1 and r["w"] == 1) / len(z)) if z else None,
            "sha_dziennika": sha(plik_jsonl(Path(kat) / "bos.jsonl"))}


def main():
    sur, manifest, wy = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    fakt = sys.argv[5] if len(sys.argv) > 5 else None
    stary_wsc = Path(manifest).parent / "wsc273" / "pythia-1b-v0" / "results_rozszerzone.json"
    sprawdz_wejscia(sys.argv[4], sur, manifest, stary_wsc)
    man = [json.loads(l) for l in open(manifest, encoding="utf-8")]
    def wiersz(model, t):
        return next(r for r in man if r["model"] == model and r["zadanie"] == t)

    kat = lambda war, t, m="pythia-1b-v0": sur / war / KATALOG[t] / m
    L = {"protokol_commit": "7f09124", "manifest_sha": sha(manifest), "testy_wariantu_bos": SZESC, "pary": {}}

    # Tylko pary policzone po znaczniku nowego startu kolejki; wpisy nieudanego startu sa pomijane.
    znacznik = (sur / "NOWY_START").read_text().strip()
    wpisy = [json.loads(l) for l in open(sur / "kolejka.jsonl", encoding="utf-8") if l.strip()]
    wazne = {(w["wariant"], w["zadanie"]): w for w in wpisy if w["start"] >= znacznik}
    L["znacznik_nowego_startu"] = znacznik
    L["wpisy_kolejki"] = {"przed_znacznikiem_pominiete": sum(1 for w in wpisy if w["start"] < znacznik),
                          "po_znaczniku": list(wazne.values())}
    NAZWA = {"kontrola": "KONTROLA", "bos": "BOS", "okno": "OKNO", "kontrola-arc": "KONTROLA-ARC"}

    def ob_po_znaczniku(war, t, sciezka):
        w = wazne.get((NAZWA[war], t))
        return obserwacja(sciezka) if w and w["kod"] == 0 else None

    k = ob_po_znaczniku("kontrola", "T06", kat("kontrola", "T06"))
    L["kontrola"] = None
    wazny = False
    if k:
        wazny = k["state"] == "ok" and round(k["value"], 4) == 0.7095
        st = wiersz("pythia-1b-v0", "T06")
        L["kontrola"] = {**k, "zaokraglone_4": round(k["value"], 4), "warunek_0_7095": wazny,
                         "results_sha_taki_jak_w_manifescie": k["results_sha256"] == st["results_sha256"],
                         "sensowny": kontrola_sensu(k)}
    L["pomiar_wazny"] = wazny

    for t in SZESC + ["T03"]:
        war = "okno" if t == "T03" else "bos"
        st = wiersz("pythia-1b-v0", t)
        ob = ob_po_znaczniku(war, t, kat(war, t))
        p = {"zadanie": t, "wariant": "OKNO" if t == "T03" else "BOS", "metryka": st["metryka"], "stara": st["wartosc"],
             "stara_z_protokolu": STARE[t], "se_stara": st["se"], "n_stara": st["n"]}
        if ob is None:
            p["stan"] = "brak wyniku"
            L["pary"][t] = p
            continue
        d = ob["value"] - st["wartosc"]
        se_d = math.sqrt(ob["se"] ** 2 + st["se"] ** 2)
        p.update({"stan": ob["state"], "nowa": ob["value"], "se_nowa": ob["se"], "n_nowa": ob["n"], "roznica": d,
                  "abs_roznica": abs(d), "se_roznicy": se_d, "z": d / se_d, "werdykt_z": werdykt_z(d / se_d),
                  "adnotacja_se": "SE niezalezne (ostrozne)", "baza_losowa": ob["chance"],
                  "baza_wiekszosciowa": ob["majority"], "sensowny": kontrola_sensu(ob),
                  "runner_sha256": ob["runner_sha256"], "results_sha256": ob["results_sha256"], "plik": ob["plik"],
                  "sha_pliku": ob["sha_pliku"]})
        if t in SZESC:
            p["ponizej_progu_0_04"] = abs(d) < PROG_WPLYW
            p["kontrola_bos"] = bos_kontrola(kat(war, t), t)
        if t in ("T07", "T14"):  # SE glowne jest klastrowe (metoda K); obok SE nowej po pozycjach
            se_p = math.sqrt(ob["se_a"] ** 2 + st["se"] ** 2)
            p["se_klastrowe"] = {"metoda_se": ob["metoda_se"], "se_a_nowa_po_pozycjach": ob["se_a"], "se_roznicy_po_pozycjach": se_p,
                                 "z_po_pozycjach": d / se_p, "werdykt_po_pozycjach": werdykt_z(d / se_p)}
        L["pary"][t] = p

    # T06 w parach (KONTROLA i BOS per pytanie)
    p6 = L["pary"]["T06"]
    if k and p6.get("nowa") is not None:
        a = trafienia(kat("kontrola", "T06"), "T06", k["klucz"])
        b = trafienia(kat("bos", "T06"), "T06", k["klucz"])
        if a and b and set(a) == set(b):
            ids = sorted(a)
            r = [b[i] - a[i] for i in ids]
            n = len(r)
            sr = sum(r) / n
            wa = sum((x - sr) ** 2 for x in r) / (n - 1)
            se = math.sqrt(wa / n)
            z = sr / se if se else 0.0
            p6["w_parach"] = {"n": n, "srednia_roznica_bos_minus_kontrola": sr, "se": se, "z": z,
                              "werdykt_z": werdykt_z(z), "zmienione_pytania": sum(1 for x in r if x != 0)}

    testy = [L["pary"][t] for t in SZESC]
    if all(p.get("nowa") is not None for p in testy) and wazny:
        L["wplyw"] = "maly" if all(p["abs_roznica"] < PROG_WPLYW for p in testy) else "duzy"
        L["wplyw_tekst"] = ("Wplyw maly: brak wplywu wiekszego niz 0,04 na Pythii na kazdym z 6 testow."
                            if L["wplyw"] == "maly" else "Wplyw duzy: 88 par trzeba przeliczyc.")
    elif not wazny:
        L["wplyw"] = "nierozstrzygniete"
        L["wplyw_tekst"] = "Nierozstrzygniete: srodowisko."
    else:
        L["wplyw"] = "niekompletne"
        L["wplyw_tekst"] = "Niekompletne: brak wyniku co najmniej jednego z 6 testow."

    # ARC-Easy: Slayer 1.07 minus nowa Pythia
    sl = wiersz("slayer1b-1.07-hf", "T51")
    a51 = L["pary"]["T51"]
    if a51.get("nowa") is not None:
        d = sl["wartosc"] - a51["nowa"]
        se = math.sqrt(sl["se"] ** 2 + a51["se_nowa"] ** 2)
        L["arc_easy"] = {"slayer_1_07": sl["wartosc"], "se_slayer": sl["se"], "pythia_nowa": a51["nowa"],
                         "se_pythia_nowa": a51["se_nowa"], "roznica": d, "se_roznicy": se, "z": d / se,
                         "werdykt_z": werdykt_z(d / se), "adnotacja_se": "SE niezalezne (ostrozne)",
                         "stara_roznica": sl["wartosc"] - a51["stara"],
                         "trafien_nad_progiem_z_2": (d - 2 * se) * a51["n_nowa"]}

    # T03: porownanie ze Slayerem (nizsza perpleksja = lepiej); okna u Slayera tu nie sprawdzano
    sl3 = wiersz("slayer1b-1.07-hf", "T03")
    p3 = L["pary"]["T03"]
    if p3.get("nowa") is not None:
        d = p3["nowa"] - sl3["wartosc"]
        se = math.sqrt(sl3["se"] ** 2 + p3["se_nowa"] ** 2)
        L["t03_slayer"] = {"slayer_1_07": sl3["wartosc"], "se_slayer": sl3["se"], "pythia_stara": p3["stara"], "pythia_nowa": p3["nowa"],
                           "stara_roznica_pythia_minus_slayer": p3["stara"] - sl3["wartosc"], "nowa_roznica_pythia_minus_slayer": d,
                           "se_nowej_roznicy": se, "z": d / se, "werdykt_z": werdykt_z(d / se), "adnotacja_se": "SE niezalezne (ostrozne)"}

    # WSC273: metryki poboczne, poza protokolem
    nowy_wsc = kat("bos", "T14") / "results_rozszerzone.json"
    if nowy_wsc.exists() and L["pary"]["T14"].get("nowa") is not None:
        a, b = poboczne(stary_wsc), poboczne(nowy_wsc)
        L["wsc273_poboczne_poza_protokolem"] = {"stare": a, "nowe": b, "roznica": {k: b[k] - a[k] for k in a}}

    # KONTROLA-ARC
    arc = ob_po_znaczniku("kontrola-arc", "T02", sur / "kontrola-arc" / KATALOG["T02"] / "eurollm-1.7b")
    L["kontrola_arc"] = None
    if arc:
        d = arc["value"] - ARC_ODN
        sp = json.loads(Path(arc["plik"]).read_text(encoding="utf-8"))["observations"][0]["dodatkowe"]["space"]
        liczbowy = abs(d) <= ARC_PROG
        L["kontrola_arc"] = {**arc, "odniesienie": ARC_ODN, "roznica": d, "abs_roznica": abs(d), "prog": ARC_PROG,
                             "warunek_liczbowy_spelniony": liczbowy, "sensowny": kontrola_sensu(arc),
                             "werdykt_kontroli": ("warunek liczbowy spelniony, ustawienie referencji nieodtworzone, kontrola nierozstrzygnieta"
                                                  if liczbowy else "warunek liczbowy niespelniony, ustawienie referencji nieodtworzone"),
                             "slad_runnera_demonstracje": sp.get("demonstracje_skrocone"),
                             "demonstracje": demonstracje(sur / "kontrola-arc" / KATALOG["T02"] / "eurollm-1.7b")}

    L["srodowisko"] = {"karta": "NVIDIA GeForce RTX 5090, 32607 MiB", "sterownik": "580.178.04",
                       "sterownik_pelnego_przebiegu": "615.71.09", "obraz": "pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime",
                       "instancja": 60052345, "host": 393738, "commit_kodu": "fe82b632887857585cc5482741d19b500868698d",
                       "runner_sha256": "7597c0de7273004dcd099c7e2fb7083b6232e43c17e1822fc291923210d5c1fa",
                       "ewaluuj_py_sha256": "94a1bdaacc1673f8c2afb861d871a75d81f6f5b4aac4bd92b0775e39ac2a472d",
                       "lm_eval": "0.4.9.1", "transformers": "4.57.6", "torch": "2.8.0+cu129", "precyzja": "float32",
                       "batch": 1, "wagi_pythia_sha256": "92589a02cfd745884f8473b0a975a93cea4cdaacf8333b0c047dab41623396b2",
                       "wagi_eurollm_sha256": "bfe9be53d19031a71d013ded9939747ae8e0c5dd7f07b9173cfa25521d7a9bc8"}
    L["sha_wszystkich_plikow"] = {str(p.relative_to(sur)): sha(p) for p in sorted(sur.rglob("*")) if p.is_file()}
    if fakt:
        L["koszt"] = json.loads(Path(fakt).read_text(encoding="utf-8"))
    wy.write_text(json.dumps(L, ensure_ascii=False, indent=1), encoding="utf-8")
    print(L["pomiar_wazny"], L["wplyw"])


if __name__ == "__main__":
    main()
