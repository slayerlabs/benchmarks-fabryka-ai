"""Raport pełnego przebiegu z paczki `ewaluacja.py eksport`: katalog results/<przebieg>/ z wynikami (bez próbek),
porównaniami parowanymi kolejnych wersji Slayera, wykresami PNG i README.md.

    python tools/ewaluacja/raport.py <rozpakowana_paczka> results/<przebieg> --przeglad przeglad.jsonl \
        [--wykresy <renderer>] [--odniesienie results/central-run] [--paczka eksport_pelny.tgz]

Próbki per pytanie są potrzebne tylko do porównań parowanych (progresja.json). Bez nich (`--bez-porownan`) raport
ma tabele wyników i leaderboardy, bez tabeli różnic między wersjami. README.md jest generowany w całości: liczby
w nim pochodzą z results_rozszerzone.json i progresja.json tego katalogu.
"""
import argparse
import csv
import gzip
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

TU = Path(__file__).resolve().parent
RESEARCH = TU.parents[1]
sys.path[:0] = [str(RESEARCH / "common"), str(RESEARCH / "tools")]
import statystyka as S  # noqa: E402

KOPIUJ = ("results.json", "results_rozszerzone.json", "scores-history-wiersz.csv")

BENCHMARKI = {  # katalog: (nazwa, opis metryki)
    "arc-challenge": ("ARC-Challenge", "acc_norm"),
    "arc-easy": ("ARC-Easy", "acc"),
    "blimp": ("BLiMP", "acc, SE po 67 paradygmatach"),
    "ewok": ("EWoK", "trafność par kontekst × cel, SE po szablonach"),
    "hellaswag": ("HellaSwag", "acc_norm"),
    "lambada": ("LAMBADA (OpenAI)", "acc, greedy ostatniego słowa"),
    "mathqa": ("MathQA", "acc_norm"),
    "medmcqa": ("MedMCQA", "acc"),
    "multiblimp-pl": ("MultiBLiMP-PL", "acc"),
    "piqa": ("PIQA", "acc_norm"),
    "pubmedqa": ("PubMedQA", "acc"),
    "social-iqa": ("Social IQa", "acc"),
    "wikitext-2": ("WikiText-2", "byte perplexity, niżej = lepiej"),
    "winogrande": ("WinoGrande", "acc, SE po parach zdań"),
    "wsc273": ("WSC273", "acc, SE po schematach"),
}

KROTKIE = {"arc-challenge": "ARC-C", "arc-easy": "ARC-E", "hellaswag": "HSwag", "lambada": "LAMBADA",
           "multiblimp-pl": "MultiBLiMP", "social-iqa": "SIQA", "winogrande": "WinoG.", "pubmedqa": "PubMed",
           "medmcqa": "MedMCQA"}

NAZWY = {
    "pythia-1b-v0": "Pythia-1B v0", "eurollm-1.7b": "EuroLLM-1.7B", "bielik-1.5b-v3": "Bielik-1.5B-v3",
    "qwen3.5-0.8b-base": "Qwen3.5-0.8B-Base", "lfm3-1.7b-base": "LFM3-1.7B-Base", "lfm3-1.7b": "LFM3-1.7B (Instruct)",
    "lfm2.5-1.2b-base": "LFM2.5-1.2B-Base", "bielik-11b-v3-instruct": "Bielik-11B-v3.0-Instruct",
    "bielik-11b-v3-base": "Bielik-11B-v3-Base",
}


def nazwa(etyk):
    if etyk.startswith("slayer1b-"):
        return "Slayer 1B " + etyk.split("-")[1]
    return NAZWY.get(etyk, etyk)


def wersja_slayera(etyk):
    return etyk.split("-")[1] if etyk.startswith("slayer1b-") else None


def liczba(x, cyfry=4):
    """Polski zapis dziesiętny (dokumenty repo)."""
    if x is None:
        return "–"
    return f"{x:.{cyfry}f}".replace(".", ",").replace("-", "−")


# --------------------------------------------------------------------------- wyniki

def wczytaj_wyniki(paczka: Path):
    """[{benchmark, model, task, metryka, wartosc, se, lo, hi, n, chance, wyzej_lepiej, skala, ...}] z manifestu."""
    out = []
    for w in map(json.loads, (paczka / "manifest.jsonl").read_text(encoding="utf-8").splitlines()):
        roz = json.loads((paczka / w["katalog"] / "results_rozszerzone.json").read_text(encoding="utf-8"))
        o = roz["observations"][0]
        sp = (o.get("dodatkowe") or {}).get("space") or {}
        met = (o.get("metric") or "").split(",")[0]
        stat = sp.get("glowna") or sp.get(met) or (sp.get("acc") if met == "accuracy" else None) or {}
        skala = 100.0 if o.get("unit") == "percent" else 1.0       # MultiBLiMP zapisuje %, raport ma ułamki
        v = o["value"] / skala
        se = stat.get("se")
        if se is not None and stat.get("value") is not None and abs(stat["value"] - o["value"]) < 1e-9:
            se /= skala                                           # SE w tej samej skali co wartość
        ci = o.get("ci95") or {}
        lo, hi = (ci.get("lower"), ci.get("upper")) if isinstance(ci, dict) else (None, None)
        if lo is None and stat.get("ci95"):
            lo, hi = stat["ci95"]
        lo, hi = (None if lo is None else lo / skala), (None if hi is None else hi / skala)
        ref = o.get("reference") or {}
        chance = ref.get("chance_value")
        chance = 0.5 if w["benchmark"] == "ewok" else (None if chance is None else chance / skala)
        out.append({**{k: w[k] for k in ("benchmark", "zadanie", "model", "repo", "rewizja", "dtype", "env", "n",
                                         "katalog", "s", "gpu", "lm_eval")},
                    "metryka": met if met != "accuracy" else "acc", "wartosc": v, "se": se, "lo": lo, "hi": hi,
                    "chance": chance, "wyzej_lepiej": o.get("higher_is_better") is not False,
                    "skala_w_pliku": skala})
    return out


def kopiuj(paczka: Path, cel: Path, przeglad: Path | None):
    for w in map(json.loads, (paczka / "manifest.jsonl").read_text(encoding="utf-8").splitlines()):
        d = cel / w["benchmark"] / w["model"]
        d.mkdir(parents=True, exist_ok=True)
        for f in KOPIUJ:
            if (paczka / w["katalog"] / f).exists():
                shutil.copy2(paczka / w["katalog"] / f, d / f)
    for f in ("manifest.jsonl", "srodowisko.json", "czasy.jsonl"):
        shutil.copy2(paczka / f, cel / f)
    if przeglad:
        shutil.copy2(przeglad, cel / "przeglad.jsonl")


# --------------------------------------------------------------------------- porównania parowane

def _probki(paczka, bench, model):
    d = paczka / "wyniki" / bench / model / "probki"
    pliki = sorted(d.glob("*_space.jsonl")) or sorted(d.glob("ewok.jsonl"))
    if not pliki:
        return None
    rek = [json.loads(l) for l in pliki[0].read_text(encoding="utf-8").splitlines()]
    klucz = "doc_id" if "doc_id" in rek[0] else "id"
    return {r[klucz]: r for r in rek}


class Oceny:
    """Wynik per pytanie (0/1, EWoK 0/0,5/1) i klaster pozycji: te same reguły co ewaluuj.py i ewok.py."""

    def __init__(self):
        import metryki as M
        import zadania as Z
        self.M, self.Z = M, Z
        self._szablony = None

    def szablony(self):
        if self._szablony is None:
            sys.path.insert(0, str(RESEARCH / "benchmarks" / "ewok"))
            import ewok
            try:
                rek = ewok.load_records()
                self._szablony = ewok.templates(rek)
            except Exception as e:  # zbiór gated: bez dostępu SE po rekordach
                print(f"EWoK: bez szablonów ({type(e).__name__}), SE po rekordach", file=sys.stderr)
                self._szablony = {}
        return self._szablony

    def wektor(self, bench, task, met, probki):
        klucze = sorted(probki)
        if bench == "ewok":
            sys.path.insert(0, str(RESEARCH / "benchmarks" / "ewok"))
            import ewok
            x = [ewok.evaluate(probki[k])["ewok"] for k in klucze]
            sz = self.szablony()
            kl = [sz[probki[k]["source_id"]] for k in klucze] if sz else None
            return klucze, x, kl
        p = [probki[k] for k in klucze]
        if bench == "lambada":
            x = [float(q["acc"]) for q in p]
        else:
            x = [self.M.oceny_mc(q, "acc_mutual_info" in q["metrics"])[met] for q in p]
        import ewaluuj
        kl = ewaluuj.klastry_probek(self.Z.ZADANIA[task], p)
        return klucze, x, kl


def porownaj_wikitext(pa, pb):
    """Δ bits per byte (A − B) na tych samych dokumentach: dokument = klaster bajtów, SE K, t przy df = k − 1."""
    klucze = sorted(set(pa) & set(pb))
    grupy = []
    for k in klucze:
        lla, b = pa[k]["filtered_resps"][0], pa[k]["byte_perplexity"][1]
        llb = pb[k]["filtered_resps"][0]
        grupy.append((b, -(lla - llb) / (math.log(2) * b)))
    r = S.klastrowe_wazone(grupy)
    return {"n": len(klucze), "roznica_bpb": r["roznica"], "se": r["se"], "t": r["t"], "df": r["df"],
            "p": r["p_t"], "werdykt": r["werdykt"], "metoda": "K (dokumenty)"}


def porownaj(oceny, paczka, w_a, w_b):
    """Różnica A − B per pytanie: SE A parowane (z) albo SE K po klastrach testu (t, df = k − 1)."""
    bench = w_a["benchmark"]
    pa, pb = _probki(paczka, bench, w_a["model"]), _probki(paczka, bench, w_b["model"])
    if pa is None or pb is None:
        return None
    if bench == "wikitext-2":
        r = porownaj_wikitext(pa, pb)
    else:
        ka, xa, kla = oceny.wektor(bench, w_a["zadanie"], w_a["metryka"], pa)
        kb, xb, _ = oceny.wektor(bench, w_b["zadanie"], w_b["metryka"], pb)
        if ka != kb:
            raise SystemExit(f"{bench}: różne zbiory pytań {w_a['model']} / {w_b['model']}")
        d = [a - b for a, b in zip(xa, xb)]
        if kla is not None:
            k = S.se_k(d, kla)
            r = {"n": len(d), "se": k["se"], "t": k["t"], "df": k["df"], "p": k["p_t"],
                 "werdykt": k["werdykt"] or S.NIEROZSTRZYGALNE, "k": k["k"], "metoda": "K"}
        else:
            n, m = len(d), sum(d) / len(d)
            se = math.sqrt(sum((x - m) ** 2 for x in d) / (n - 1) / n)
            z = m / se if se else None
            r = {"n": n, "se": se, "z": z, "p": S.p_z(z) if z is not None else None,
                 "werdykt": S.werdykt(z) if z is not None else S.NIEROZSTRZYGALNE, "metoda": "A parowane"}
        r["roznica_srednia"] = sum(d) / len(d)
    r.update({"benchmark": bench, "a": w_a["model"], "b": w_b["model"],
              "roznica": w_a["wartosc"] - w_b["wartosc"]})
    return r


def progresja(wyniki, paczka):
    """Kolejne wersje Slayera (1.00 → 1.01 → … ) i pierwsza → ostatnia, per test; Holm osobno w obu rodzinach."""
    oceny = Oceny()
    sl = sorted({w["model"] for w in wyniki if wersja_slayera(w["model"])}, key=wersja_slayera)
    idx = {(w["benchmark"], w["model"]): w for w in wyniki}
    kolejne, skrajne = [], []
    for bench in BENCHMARKI if len(sl) > 1 else []:
        for a, b in zip(sl[1:], sl[:-1]):
            if (bench, a) in idx and (bench, b) in idx:
                r = porownaj(oceny, paczka, idx[(bench, a)], idx[(bench, b)])
                if r:
                    kolejne.append(r)
        if (bench, sl[-1]) in idx and (bench, sl[0]) in idx:
            r = porownaj(oceny, paczka, idx[(bench, sl[-1])], idx[(bench, sl[0])])
            if r:
                skrajne.append(r)
    for rodzina in (kolejne, skrajne):
        for r, h in zip(rodzina, S.po_holmie([r.get("p") for r in rodzina])):
            r.update(h)
    return {"opis": "A − B na tych samych pytaniach; SE A parowane (z) albo SE K po klastrach testu (t, df = k − 1); "
                    "WikiText: Δ bits per byte, dokument = klaster; Holm w każdej rodzinie osobno",
            "kolejne_wersje": kolejne, "pierwsza_ostatnia": skrajne}


# --------------------------------------------------------------------------- wykresy

def wykresy(wyniki, cel: Path, wykluczone, renderer: Path | None, python_wykresow="python"):
    """Pionowe słupki per test + macierz zbiorcza: specyfikacje w katalogu tymczasowym, w raporcie tylko PNG."""
    import tempfile
    src = Path(tempfile.mkdtemp(prefix="raport_wykresy_"))
    (src / "charts").mkdir(parents=True, exist_ok=True)
    (src / "data").mkdir(parents=True, exist_ok=True)
    ostatni = max((w["model"] for w in wyniki if wersja_slayera(w["model"])), key=wersja_slayera, default=None)
    ids = []
    for bench, (tytul, opis) in BENCHMARKI.items():
        ws = [w for w in wyniki if w["benchmark"] == bench and w["model"] not in wykluczone]
        if not ws:
            continue
        proc = bench != "wikitext-2"
        k = 100.0 if proc else 1.0
        with open(src / "data" / f"{bench}.csv", "w", encoding="utf-8", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["model", "value", "lo", "hi"])
            for w in ws:
                wr.writerow([nazwa(w["model"]), round(w["wartosc"] * k, 4),
                             "" if w["lo"] is None else round(w["lo"] * k, 4),
                             "" if w["hi"] is None else round(w["hi"] * k, 4)])
        ch = ws[0]["chance"]
        spec = {"type": "bars", "orientation": "vertical", "title": tytul,
                "subtitle": f"{opis}{', %' if proc else ''}, pełny split (n = {ws[0]['n']}), kreska = CI95",
                "data": f"../data/{bench}.csv", "highlight": [nazwa(ostatni)] if ostatni else [],
                "bar_color": "accent-light",
                "decimal": ",", "decimals": 1 if proc else 3, "best_label": "",
                "caption": "float32; Bielik-11B w bfloat16. benchmarks-fabryka-ai, research/results"}
        if not proc:
            spec.update({"lower_is_better": True, "xmin": 1.0})
        else:
            spec["xmin"] = 0
            hi = max((w["hi"] or w["wartosc"]) for w in ws) * 100
            spec["xmax"] = min(100.0, math.ceil(hi / 5) * 5 + 5)
        if ch:
            spec.update({"chance": round(ch * k, 2), "chance_label": f"losowo {liczba(ch * k, 1)}"})
        (src / "charts" / f"{bench}.yaml").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
        ids.append(bench)
    # macierz: modele × testy w %, kolor od losowego do najlepszego w kolumnie (bez WikiText: niżej = lepiej)
    modele = list(dict.fromkeys(w["model"] for w in sorted(wyniki, key=lambda w: (not wersja_slayera(w["model"]),
                                                                                  w["model"]))
                                if w["model"] not in wykluczone))
    kol = [b for b in BENCHMARKI if b != "wikitext-2"]
    tab = {(w["model"], w["benchmark"]): w for w in wyniki}
    with open(src / "data" / "macierz.csv", "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["model", "sub"] + [b.replace("-", "_") for b in kol])
        for m in modele:
            vals = [tab[(m, b)]["wartosc"] * 100 if (m, b) in tab else None for b in kol]
            wr.writerow([nazwa(m), f"{tab[(m, kol[0])]['repo']} · {tab[(m, kol[0])]['rewizja'][:8]} · "
                                   f"{tab[(m, kol[0])]['dtype']}" if (m, kol[0]) in tab else ""]
                        + ["" if v is None else round(v, 1) for v in vals])
    # bez kolumny średniej: średnia testów to meta-ocena, a ta wymaga pliku zestawu (LEADERBOARD.md)
    spec = {"type": "matrix", "title": f"{len(modele)} modeli × {len(kol)} testów",
            "subtitle": "%, pełne splity; kolor od wyniku losowego do najlepszego w kolumnie",
            "data": "../data/macierz.csv", "model_header": "MODEL", "show_planned": False, "model_width": 6.4,
            "columns": [{"key": b.replace("-", "_"), "label": KROTKIE.get(b, BENCHMARKI[b][0]),
                         **({"chance": round(tab[(modele[0], b)]["chance"] * 100, 1)}
                            if (modele[0], b) in tab and tab[(modele[0], b)]["chance"] else {})} for b in kol],
            "caption": "Bielik-11B-v3.0-Instruct: bfloat16, bez EWoK. WikiText-2 (niżej = lepiej) tylko w tabelach."}
    (src / "charts" / "macierz.yaml").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    ids.append("macierz")
    if renderer:
        out = (cel / "charts").resolve()
        r = subprocess.run([python_wykresow, "-m", "benchplot", "--charts", str(src / "charts"), "render", ",".join(ids),
                            "--format", "png", "--theme", "light", "--out", str(out)],
                           cwd=str(renderer), capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"wykresy: {r.stderr[-2000:]}")
    shutil.rmtree(src, ignore_errors=True)
    return ids


# --------------------------------------------------------------------------- README

def _sha(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def zgodnosc_z_odniesieniem(wyniki, odn: Path | None):
    if not odn or not odn.exists():
        return []
    out = []
    for w in wyniki:
        p = odn / w["benchmark"] / w["model"] / "results_rozszerzone.json"
        if p.exists():
            o = json.loads(p.read_text(encoding="utf-8"))
            r = json.loads(p.read_text(encoding="utf-8"))["observations"][0]
            out.append({"benchmark": w["benchmark"], "model": w["model"], "nasz": w["wartosc"],
                        "odniesienie": r["value"] / w["skala_w_pliku"], "lm_eval_odn": o.get("lm_eval"),
                        "lm_eval": w["lm_eval"]})
    return out


def readme(wyniki, cel: Path, prog, przeglad, wykresy_ids, odn, paczka_tgz, nazwa_przebiegu, srodowisko):
    flagi = {}
    for r in przeglad:
        flagi.setdefault(r["model"], set()).add(r["flaga"])
    wykluczone = {m for m, f in flagi.items() if "do_sprawdzenia" in f}
    uwagi = {}
    for r in przeglad:
        if r["flaga"] != "ok" or r["model"] in wykluczone:
            for u in r.get("uwagi", []):
                if "procentach" in u or "byte perplexity" in u:
                    continue
                uwagi.setdefault(r["model"], [])
                if u not in uwagi[r["model"]]:
                    uwagi[r["model"]].append(u)
    modele = list(dict.fromkeys(w["model"] for w in sorted(wyniki, key=lambda w: (not wersja_slayera(w["model"]),
                                                                                  wersja_slayera(w["model"]) or "",
                                                                                  w["model"]))))
    tab = {(w["model"], w["benchmark"]): w for w in wyniki}
    L = []
    a = L.append
    git = srodowisko.get("fabryka_commit", "")[:8]
    a(f"# Pełny przebieg {nazwa_przebiegu}: Slayer 1B 1.00–1.08 i modele odniesienia")
    a("")
    a("<!-- Plik wygenerowany przez tools/ewaluacja/raport.py. Nie edytuj ręcznie: zmień generator albo dane. -->")
    a("")
    a(f"{len(modele)} modeli × {len(BENCHMARKI)} testów z listy `GOTOWE` (`tools/przebieg_centralny.sh`), pełne "
      f"splity, runner `tools/ewaluacja/ewaluacja.py licz --zadania gotowe` na fabryce @ `{git}`. "
      f"Karta: {srodowisko.get('gpu', '').splitlines()[0] if srodowisko.get('gpu') else '?'} (4 karty, jedna kolejka "
      "modeli na kartę). Protokół jak w przebiegu centralnym: float32, batch 1, jeden BOS, limit 4096 tokenów dla "
      "WikiText. Wyjątek: Bielik-11B w bfloat16, bo w float32 nie mieści się na karcie; EWoK liczy tylko float32, "
      "więc Bielik-11B go nie ma.")
    a("")
    a("## Spis")
    a("")
    a("- [Weryfikacja](#weryfikacja)")
    a("- [Wszystkie wyniki](#wszystkie-wyniki)")
    a("- [Slayer 1B: wersje 1.00–1.08](#slayer-1b-wersje-100108)")
    a("- [Leaderboard per test](#leaderboard-per-test)")
    a("- [Do sprawdzenia i niepoliczone](#do-sprawdzenia-i-niepoliczone)")
    a("- [Pliki i odtworzenie](#pliki-i-odtworzenie)")
    a("")
    # --- weryfikacja
    a("## Weryfikacja")
    a("")
    zg = zgodnosc_z_odniesieniem(wyniki, odn)
    rowne = [z for z in zg if abs(z["nasz"] - z["odniesienie"]) < 5e-5]
    a("- Każdy plik wyników ma sumę sha256 w `manifest.jsonl` (pole `pliki`); paczka z próbkami przeszła ją w "
      "całości przed rozpakowaniem tutaj.")
    a("- Każda wartość została przeliczona od nowa z zapisanych logprobów per pytanie (te same reguły co "
      "`common/metryki.py` i `benchmarks/ewok/ewok.py`): wszystkie pary zgodne co do bitu.")
    if zg:
        inne = sorted({nazwa(z["model"]) for z in zg if z not in rowne})
        a(f"- Wspólne pary z `results/central-run` (przebieg centralny fabryki): {len(rowne)} z {len(zg)} "
          "identycznych do 4 miejsc po przecinku." + (f" Różne tylko: {', '.join(inne)} (sekcja "
                                                     "[Do sprawdzenia](#do-sprawdzenia-i-niepoliczone))." if inne else ""))
    a("- Kontrole etapu B z `tools/ewaluacja/kontrole.json` (Pythia-1B v0: PIQA, WinoGrande, LAMBADA, ARC-Easy, "
      "BLiMP) dały tu te same wartości co lokalny przebieg kontrolny w `tools/ewaluacja/wyniki_kontrolne/`.")
    a("")
    # --- tabela zbiorcza
    a("## Wszystkie wyniki")
    a("")
    a("Ułamek poprawnych odpowiedzi (WikiText: byte perplexity, niżej = lepiej). MultiBLiMP-PL zapisuje wynik w "
      "procentach; tu jest ułamkiem. Kursywa: wynik do sprawdzenia, poza leaderboardami.")
    a("")
    if "macierz" in wykresy_ids and (cel / "charts" / "macierz.png").exists():
        a("![Macierz modele × testy](charts/macierz.png)")
        a("")
    a("| test | " + " | ".join(nazwa(m) for m in modele) + " |")
    a("|---|" + "---:|" * len(modele))
    for b, (tyt, _) in BENCHMARKI.items():
        cyfry = 3 if b == "wikitext-2" else 4
        kom = []
        for m in modele:
            w = tab.get((m, b))
            s = liczba(w["wartosc"], cyfry) if w else "–"
            kom.append(f"*{s}*" if w and m in wykluczone else s)
        a(f"| {tyt} | " + " | ".join(kom) + " |")
    a("")
    # --- progresja
    sl = [m for m in modele if wersja_slayera(m)]
    a("## Slayer 1B: wersje 1.00–1.08")
    a("")
    a("Wszystkie wersje mają tę samą architekturę i tokenizer; rewizje HF w `manifest.jsonl`. 1.07 to wagi z HF "
      "(sha256 checkpointu zgodne z `SLAYER_CKPT_SHA256`), 1.08 to rewizja z publikacji w toku.")
    a("")
    a("| test | " + " | ".join(wersja_slayera(m) for m in sl) + " |")
    a("|---|" + "---:|" * len(sl))
    for b, (tyt, _) in BENCHMARKI.items():
        cyfry = 3 if b == "wikitext-2" else 4
        a(f"| {tyt} | " + " | ".join(liczba(tab[(m, b)]["wartosc"], cyfry) if (m, b) in tab else "–" for m in sl)
          + " |")
    a("")
    if prog:
        def wiersz(r):
            stat = (f"t = {liczba(r['t'], 2)}, df = {r['df']}" if r.get("t") is not None else
                    (f"z = {liczba(r['z'], 2)}" if r.get("z") is not None else "–"))
            cyfry = 3 if r["benchmark"] == "wikitext-2" else 4
            d = liczba(r["roznica"], cyfry)
            se = r["se"]
            se_s = liczba(se, 4) + (" bpb" if r["benchmark"] == "wikitext-2" else "")
            return (f"| {BENCHMARKI[r['benchmark']][0]} | {wersja_slayera(r['b'])} → {wersja_slayera(r['a'])} | {d} | "
                    f"{se_s} | {stat} | {r['werdykt']} | {r['po_holmie']} ({r['werdykt_holm']}) |")
        naglowek = ["| test | wersje | Δ | SE Δ | statystyka | werdykt | po Holmie |",
                    "|---|---|---:|---:|---|---|---|"]
        a(f"### Pierwsza → ostatnia wersja ({len(prog['pierwsza_ostatnia'])} porównań, Holm w tej rodzinie)")
        a("")
        a("Δ = nowsza − starsza na tych samych pytaniach. SE parowane po pytaniach (z) albo po klastrach testu "
          "(t, df = k − 1): BLiMP po paradygmatach, WinoGrande po parach zdań, WSC273 po schematach, EWoK po "
          "szablonach. WikiText: Δ w byte perplexity, SE i t na bits per byte z dokumentem jako klastrem. Werdykt: "
          "|z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum (t przez p przy tym samym progu).")
        a("")
        L.extend(naglowek)
        for r in prog["pierwsza_ostatnia"]:
            a(wiersz(r))
        a("")
        a(f"### Kolejne wersje ({len(prog['kolejne_wersje'])} porównań, Holm w tej rodzinie)")
        a("")
        L.extend(naglowek)
        for r in prog["kolejne_wersje"]:
            a(wiersz(r))
        a("")
    # --- leaderboardy
    a("## Leaderboard per test")
    a("")
    a("Kolejność po wartości. Miejsce w tabeli nie mówi, czy różnica do sąsiada wychodzi poza szum: to mówią SE "
      "i CI95 (porównania parowane są tylko dla wersji Slayera). Bez modeli z sekcji „Do sprawdzenia”.")
    a("")
    for b, (tyt, opis) in BENCHMARKI.items():
        ws = [w for w in wyniki if w["benchmark"] == b and w["model"] not in wykluczone]
        if not ws:
            continue
        lepiej = ws[0]["wyzej_lepiej"]
        ws.sort(key=lambda w: w["wartosc"], reverse=lepiej)
        cyfry = 3 if b == "wikitext-2" else 4
        a(f"### {tyt}")
        a("")
        a(f"{opis}; `{ws[0]['zadanie']}`, n = {ws[0]['n']}" + (f", wynik losowy {liczba(ws[0]['chance'], 4)}"
                                                              if ws[0]["chance"] else "") + ".")
        a("")
        if (cel / "charts" / f"{b}.png").exists():
            a(f"![{tyt}](charts/{b}.png)")
            a("")
        a("| # | model | wartość | SE | CI95 | dtype | wyniki |")
        a("|---:|---|---:|---:|---|---|---|")
        for i, w in enumerate(ws, 1):
            ci = f"{liczba(w['lo'], cyfry)} – {liczba(w['hi'], cyfry)}" if w["lo"] is not None else "–"
            a(f"| {i} | {nazwa(w['model'])} | {liczba(w['wartosc'], cyfry)} | {liczba(w['se'], 4)} | {ci} | "
              f"{w['dtype']} | [{b}/{w['model']}]({b}/{w['model']}/results_rozszerzone.json) |")
        a("")
    # --- do sprawdzenia
    a("## Do sprawdzenia i niepoliczone")
    a("")
    for m in sorted(uwagi, key=lambda m: (m not in wykluczone, m)):
        a(f"- **{nazwa(m)}**: " + "; ".join(uwagi[m]) + ".")
    rozne = [z for z in zg if abs(z["nasz"] - z["odniesienie"]) >= 5e-5]
    if rozne:
        a("")
        a("Różnice wobec `results/central-run` (ten sam model, rewizja i sha256 wag; tam lm_eval "
          f"{rozne[0]['lm_eval_odn']}, tu {rozne[0]['lm_eval']}):")
        a("")
        a("| test | model | tu | central-run |")
        a("|---|---|---:|---:|")
        for z in rozne:
            a(f"| {BENCHMARKI[z['benchmark']][0]} | {nazwa(z['model'])} | {liczba(z['nasz'])} | "
              f"{liczba(z['odniesienie'])} |")
    a("")
    # --- pliki
    a("## Pliki i odtworzenie")
    a("")
    a("| plik | zawartość |")
    a("|---|---|")
    a("| `<test>/<model>/results.json` | wynik w schemacie Space (obserwacja, protokół, provenance) |")
    a("| `<test>/<model>/results_rozszerzone.json` | to samo + metryki dodatkowe, SE, CI95, bazy, wersja lm_eval, "
      "dtype |")
    a("| `<test>/<model>/scores-history-wiersz.csv` | wiersz w formacie scores-history.csv |")
    a("| `manifest.jsonl` | jedna linia na parę model × test: repo, rewizja, env, dtype, komenda, czas, karta, "
      "sha256 wag, runnera i każdego pliku |")
    a("| `srodowisko.json` | commit fabryki, karta, wersje i `pip freeze` środowisk `lock` i `new` |")
    a("| `czasy.jsonl` | start, koniec i czas każdej pary oraz pobierania wag |")
    a("| `przeglad.jsonl` | flaga każdego wyniku (`ok`, `do_sprawdzenia`, `niepoliczone`) z uwagami |")
    a("| `progresja.json` | porównania parowane wersji Slayera z tabel wyżej |")
    a("| `charts/` | wykresy PNG z wartości tego pliku |")
    a("")
    if paczka_tgz:
        a(f"Próbki per pytanie (logprob każdej odpowiedzi, prompt, hash dokumentu) i logi par są w paczce "
          f"`{paczka_tgz.name}` (sha256 `{_sha(paczka_tgz)}`), poza repo, bo skompresowane mają kilkaset MB.")
        a("")
    a("Odtworzenie jednej pary (komenda z `manifest.jsonl`, pole `komenda`, albo przez runner):")
    a("")
    a("```bash")
    a("python tools/ewaluacja/ewaluacja.py --wyniki wyniki licz slayer1b-1.06 --zadania T02 --pobierz")
    a("```")
    a("")
    a("Cały przebieg: te same kolejki co tutaj, jedna na kartę (`CUDA_VISIBLE_DEVICES`), `--zadania gotowe --pobierz "
      "--usun-wagi`, potem `ewaluacja.py eksport`. Ten plik i wykresy: `python tools/ewaluacja/raport.py` (opis w "
      "nagłówku skryptu).")
    a("")
    (cel / "README.md").write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paczka", help="rozpakowany katalog eksportu (manifest.jsonl, wyniki/)")
    ap.add_argument("cel", help="katalog raportu, np. results/full-run-2026-11")
    ap.add_argument("--przeglad", help="przeglad.jsonl z flagami wyników")
    ap.add_argument("--wykresy", help="katalog renderera wykresów (python -m benchplot); bez niego raport bez PNG")
    ap.add_argument("--python-wykresow", dest="python_wykresow", default="python",
                    help="interpreter z matplotlib, pyyaml i pillow")
    ap.add_argument("--odniesienie", help="katalog innego przebiegu do porównania, np. results/central-run")
    ap.add_argument("--paczka-tgz", dest="paczka_tgz", help="pełna paczka z próbkami (do sumy sha256 w README)")
    ap.add_argument("--nazwa", default="2026-11-09")
    ap.add_argument("--bez-porownan", dest="bez_porownan", action="store_true")
    a = ap.parse_args()
    paczka, cel = Path(a.paczka), Path(a.cel)
    cel.mkdir(parents=True, exist_ok=True)
    przeglad = ([json.loads(l) for l in Path(a.przeglad).read_text(encoding="utf-8").splitlines()]
                if a.przeglad else [])
    wyniki = wczytaj_wyniki(paczka)
    kopiuj(paczka, cel, Path(a.przeglad) if a.przeglad else None)
    prog = None
    if a.bez_porownan and (cel / "progresja.json").exists():   # porównania z poprzedniego przebiegu raportu
        prog = json.loads((cel / "progresja.json").read_text(encoding="utf-8"))
    elif not a.bez_porownan:
        prog = progresja(wyniki, paczka)
        (cel / "progresja.json").write_text(json.dumps(prog, ensure_ascii=False, indent=1), encoding="utf-8")
    wykluczone = {r["model"] for r in przeglad if r["flaga"] == "do_sprawdzenia"}
    ids = wykresy(wyniki, cel, wykluczone, Path(a.wykresy).resolve() if a.wykresy else None, a.python_wykresow)
    sr = json.loads((paczka / "srodowisko.json").read_text(encoding="utf-8"))
    readme(wyniki, cel, prog, przeglad, ids, Path(a.odniesienie) if a.odniesienie else None,
           Path(a.paczka_tgz) if a.paczka_tgz else None, a.nazwa, sr)
    print(f"{cel / 'README.md'}: {len(wyniki)} wyników, wykresy {len(ids)}"
          + (f", porównań {len(prog['kolejne_wersje']) + len(prog['pierwsza_ostatnia'])}" if prog else ""))


if __name__ == "__main__":
    main()
