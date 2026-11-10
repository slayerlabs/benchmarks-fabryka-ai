"""Raport pełnego przebiegu z paczki `ewaluacja.py eksport`: katalog results/<przebieg>/ z wynikami (bez próbek),
porównaniami parowanymi kolejnych wersji Slayera, wykresami SVG i README.md.

    python tools/ewaluacja/raport.py <paczka_albo_katalog_przebiegu> results/<przebieg> \
        [--odniesienie results/central-run] [--bez-porownan]

Bez próbek per pytanie (`--bez-porownan`) raport bierze porównania wersji z istniejącego progresja.json. README.md,
wykresy, `se` w manifest.jsonl oraz flagi i pola CodeSOTA w przeglad.jsonl są generowane w całości z plików wyników,
kart `benchmarks/*/REPRODUCTION.md`, tabeli typów w README, `sizes.json` i `bos-window-check/LICZBY.json`. Reguły
flag: `flag_rules` i `window_exceeded`.
"""
import argparse
import json
import math
import re
import shutil
import sys
from html import escape as E
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
        katalog = paczka / w["katalog"] if (paczka / w["katalog"]).exists() else paczka / w["benchmark"] / w["model"]
        roz = json.loads((katalog / "results_rozszerzone.json").read_text(encoding="utf-8"))
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
        bazy = sp.get("bazy") or {}
        out.append({**{k: w[k] for k in ("benchmark", "zadanie", "model", "repo", "rewizja", "dtype", "env", "n",
                                         "katalog", "s", "gpu", "lm_eval")},
                    "metryka": met if met != "accuracy" else "acc", "metryka_raw": w["metryka"], "wartosc": v, "se": se,
                    "lo": lo, "hi": hi, "chance": bazy.get("chance_value"), "majority": bazy.get("majority_value"),
                    "wyzej_lepiej": o.get("higher_is_better") is not False, "skala_w_pliku": skala,
                    "max_length": roz.get("max_length"), "contamination": o.get("contamination"),
                    "pmi": sp.get("acc_pmi"), "wobec_b": sp.get("wobec_b")})
    return out


def kopiuj(paczka: Path, cel: Path):
    for w in map(json.loads, (paczka / "manifest.jsonl").read_text(encoding="utf-8").splitlines()):
        d = cel / w["benchmark"] / w["model"]
        d.mkdir(parents=True, exist_ok=True)
        for f in KOPIUJ:
            if (paczka / w["katalog"] / f).exists():
                shutil.copy2(paczka / w["katalog"] / f, d / f)
    for f in ("manifest.jsonl", "srodowisko.json", "czasy.jsonl"):
        shutil.copy2(paczka / f, cel / f)


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


# ------------------------------------------------------------------------- run metadata (rules applied to all models)

CLASS_1B_LIMIT = 1_100_000_000
"""Models up to this many parameters (counted from the weights) are the about-1B class; everything above is out of it."""

PMI_BELOW_CHANCE_TESTS = 2
"""A model is flagged when `acc_pmi` falls below the random baseline on at least this many PMI tests (see `flag_rules`).
The threshold was set after looking at this run, so it is a stated rule, not a preregistered one."""

CENTRAL_DIFF = 5e-5
INSTRUCT_MODELS = {"bielik-11b-v3-instruct", "lfm3-1.7b"}
AUTO_NOTES = ("reguła ", "liczony w env lock", "w testach z PMI", "do powtórki", "model instruct liczony",
              "w PIQA kontekst", "rewizja 5f854a0c", "checkpoint eksperymentalny")
SHORT_NAMES = {"pythia-1b-v0": "Pythia", "qwen3.5-0.8b-base": "Qwen"}
VERDICT_NO_CONTROL = "bez kontroli: nierozstrzygnięte"
VERDICT_PENDING = "po przebiegu centralnym"
VERDICT_MET = "spełnion"
"""Only a stage B verdict starting with this stem (METODOLOGIA, warunek odtworzenia spełniony) enters the table."""
OUT_OF_TABLE_REASONS = {
    "wikitext-2": "werdykt etapu B „nierozstrzygalny”: perpleksja nie ma progu zapisanego przed pomiarem (METODOLOGIA, „Próg dla perpleksji i BPB”)",
    "wsc273": "źródło kontroli nie podaje rewizji modelu, a wartość policzył inny kod zadania (METODOLOGIA, „Model kontrolny etapu B”, punkt 3: wynik „z rewizją i ustawieniami”); wynik wstępny",
}
PROTOCOL_BOS_THRESHOLD = 0.04

CARD_1_08 = ("https://huggingface.co/SlayerLab/Slayer1B-1.08/blob/5f854a0cc7160594d54d1788d37a44e8ebabe16c/README.md")
SLAYER_1_08_STATUS = ("checkpoint eksperymentalny: bramka przyjęcia niezaliczona (ARC-Easy), nie jest następcą 1.07")
TEST_NAMES = {
    "arc-challenge": ("ARC-Challenge", "ARC-C"), "arc-easy": ("ARC-Easy", "ARC-E"), "blimp": ("BLiMP", "BLiMP"),
    "ewok": ("EWoK", "EWoK"), "hellaswag": ("HellaSwag", "Hella"), "lambada": ("LAMBADA", "LAMB"),
    "mathqa": ("MathQA", "Math"), "medmcqa": ("MedMCQA", "Med"), "multiblimp-pl": ("MultiBLiMP-PL", "Multi"),
    "piqa": ("PIQA", "PIQA"), "pubmedqa": ("PubMedQA", "PubMed"), "social-iqa": ("Social IQa", "Social"),
    "wikitext-2": ("WikiText-2", "Wiki"), "winogrande": ("WinoGrande", "Wino"), "wsc273": ("WSC273", "WSC"),
}
METRIC_NAMES = {"acc": "acc", "acc_norm": "acc_norm", "ewok": "ewok", "byte_perplexity": "byte perplexity"}


def parse_verdict(card_text: str) -> str:
    """Value of the first `werdykt` row of a REPRODUCTION.md table, without bold markers; a card with a `## Werdykt`
    section instead of that row (BLiMP) gives the first row of the section that names stage B."""
    for line in card_text.splitlines():
        m = re.match(r"\|\s*\**werdykt(?: etapu B)?\**\s*\|\s*(.+?)\s*\|", line, re.I)
        if m:
            return m.group(1).replace("*", "").strip()
    section = re.search(r"^## Werdykt\n(.*?)(?=^## |\Z)", card_text, re.M | re.S)
    m = section and re.search(r"^\|\s*etap B[^|]*\|\s*(.+?)\s*\|", section.group(1), re.M | re.I)
    if m:
        return m.group(1).replace("*", "").strip()
    raise ValueError("REPRODUCTION.md has no verdict row")


def control_state(verdict: str) -> str:
    """`control` only for a met stage B condition, `no_control` otherwise; a card still waiting for its run is an error."""
    low = verdict.lower()
    if low.startswith(VERDICT_PENDING):
        raise ValueError(f"card without a stage B verdict: {verdict}")
    return "control" if low.startswith(VERDICT_MET) else "no_control"


def read_cards(benchmarks: Path, names) -> dict:
    """{test: {verdict, state, text}} read from `benchmarks/<test>/REPRODUCTION.md`."""
    out = {}
    for name in names:
        text = (benchmarks / name / "REPRODUCTION.md").read_text(encoding="utf-8")
        verdict = parse_verdict(text)
        out[name] = {"verdict": verdict, "state": control_state(verdict), "text": text}
    return out


def hellaswag_control_note(card_text: str) -> str:
    """Control and table of HellaSwag differ in few-shot; the two values come from the card."""
    value = re.search(r"^\| wynik \(SE\) \| `acc_norm` (\d,\d+)", card_text, re.M).group(1)
    reference = re.search(r"^\| wartość referencyjna i źródło \| (\d,\d+)", card_text, re.M).group(1)
    return (f"Kontrola HellaSwag to EuroLLM-1.7B 10-shot `acc_norm` ({value} wobec {reference}), a tabela to 0-shot, "
            "którego opublikowanej wartości nikt nie odtworzył.")


def pmi_below_chance(results) -> list:
    """Every result with `acc_pmi` below the random baseline, with z of that difference, in reading order."""
    rows = []
    for r in results:
        pmi, chance = r.get("pmi"), r.get("chance")
        if pmi is not None and chance is not None and pmi["value"] < chance:
            z = (pmi["value"] - chance) / pmi["se"]
            rows.append({"model": r["model"], "benchmark": r["benchmark"], "value": pmi["value"], "se": pmi["se"],
                         "chance": chance, "z": z, "verdict": S.werdykt(z)})
    return sorted(rows, key=lambda x: (x["model"], x["benchmark"]))


def models_at_threshold(rows, threshold) -> list:
    """Models with at least `threshold` entries of `pmi_below_chance`."""
    counts = {}
    for row in rows:
        counts[row["model"]] = counts.get(row["model"], 0) + 1
    return sorted(m for m, n in counts.items() if n >= threshold)


def environment_gap(central) -> dict | None:
    """Largest difference among results computed in both lm_eval versions: {models, diff, benchmark}."""
    both = [z for z in central if z["lm_eval"] and z["lm_eval_odn"] and z["lm_eval"] != z["lm_eval_odn"]]
    if not both:
        return None
    top = max(both, key=lambda z: abs(z["nasz"] - z["odniesienie"]))
    return {"models": sorted({z["model"] for z in both}), "diff": abs(top["nasz"] - top["odniesienie"]), "benchmark": top["benchmark"]}


def first_to_front(t: dict, first: dict, front: dict) -> str:
    """Slayer 1.00 → 1.07 as a plain difference: METODOLOGIA pairs the same questions, and those samples are not in the repository."""
    return format_number(front["v"] - first["v"], digits_of(t), plus=True)


def read_test_types(readme_text: str) -> dict:
    """{directory: type} from the table in research/README.md."""
    return {m.group(1): m.group(2) for m in re.finditer(r"^\| \[`([\w.-]+)`\]\([^)]*\) \| [^|]* \| `([^`]+)`", readme_text, re.M)}


def baseline(test_type: str, row: dict) -> tuple | None:
    """(b, name) of a result from the METODOLOGIA type table, or None when the type has none (`ppl`)."""
    if test_type.split()[0] == "ppl":
        return None
    versus = row.get("wobec_b")
    if versus:
        return versus["b"], "losowa" if versus["baza"] == "losowa" else "stała odpowiedź"
    chance, majority = row.get("chance"), row.get("majority")
    if majority is not None and (chance is None or majority > chance):
        return majority, "stała odpowiedź"
    return chance, "losowa"


def contamination_label(raw) -> str:
    """Value of the METODOLOGIA contamination field; no scan means `nieznana`."""
    if raw in (None, "unscanned"):
        return "nieznana"
    if str(raw).startswith(("sprawdzona:", "znana:")):
        return raw
    raise ValueError(f"contamination outside METODOLOGIA values: {raw}")


def slayer_label(version: str) -> str:
    """Label required by METODOLOGIA; 1.08 follows its model card."""
    if version == "1.08":
        return SLAYER_1_08_STATUS + "; z wygaszaniem LR"
    return ("ostatnia przyjęta wersja, " if version == "1.07" else "") + "bez wygaszania LR"


def size_class(params) -> str:
    if params is None:
        return "nieustalona"
    return "ok. 1B" if params <= CLASS_1B_LIMIT else "poza klasą"


def size_label(params) -> str:
    return "nieustalone" if params is None else f"{params / 1e9:.2f}B".replace(".", ",")


def format_number(x, digits=4, plus=False):
    if x is None:
        return "–"
    text = f"{abs(x):.{digits}f}".replace(".", ",")
    return ("−" if x < 0 else ("+" if plus and x > 0 else "")) + text


def format_count(n):
    return f"{n:,}".replace(",", " ")


def flag_rules(results, central_diffs) -> dict:
    """{model: [reasons]}: rules applied to every model alike; any reason marks all its results `do_sprawdzenia`."""
    reasons = {}
    for model in {r["model"] for r in results}:
        below = [r["benchmark"] for r in results
                 if r["model"] == model and r.get("pmi") is not None and r.get("chance") is not None
                 and r["pmi"]["value"] < r["chance"]]
        if len(below) >= PMI_BELOW_CHANCE_TESTS:
            names = ", ".join(TEST_NAMES[b][0] for b in sorted(below))
            reasons.setdefault(model, []).append(
                f"reguła kontekstu: acc_pmi poniżej bazy losowej na {len(below)} testach PMI ({names}); "
                f"próg {PMI_BELOW_CHANCE_TESTS} ustalony po obejrzeniu tego przebiegu")
    for z in central_diffs:
        if abs(z["nasz"] - z["odniesienie"]) >= CENTRAL_DIFF:
            note = "reguła przebiegu centralnego: wynik różni się od results/central-run dla tej samej rewizji i wag"
            if note not in reasons.setdefault(z["model"], []):
                reasons[z["model"]].append(note)
    return reasons


def window_exceeded(row: dict, own_window) -> bool:
    """WikiText windows longer than the model's own window: the run asked for tokens the model cannot place."""
    return row["benchmark"] == "wikitext-2" and own_window is not None and (row.get("max_length") or 0) > own_window


def own_window(results, model):
    """Model window: `max_length` written by a test that did not override it (not the rolling WikiText one)."""
    return next((r["max_length"] for r in results if r["model"] == model and r["benchmark"] != "wikitext-2"
                 and r.get("max_length")), None)


def refresh_files(cel: Path, results, old_rows, reasons, cards, test_types):
    """Rewrites `manifest.jsonl` and `przeglad.jsonl`: SE from the same statistic as the report, flags from the rules."""
    index = {(r["benchmark"], r["model"]): r for r in results}
    manifest_rows = []
    for row in map(json.loads, (cel / "manifest.jsonl").read_text(encoding="utf-8").splitlines()):
        r = index[(row["benchmark"], row["model"])]
        row["se"] = r["se"] * r["skala_w_pliku"]
        manifest_rows.append(row)
    (cel / "manifest.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in manifest_rows) + "\n",
                                        encoding="utf-8")
    new_rows = []
    known = set()
    for row in old_rows:
        key = (row.get("benchmark"), row.get("model"))
        r = index.get(key)
        if r is None:
            new_rows.append({**row, "kontaminacja": None, "w_tabeli_codesota": False})
            continue
        known.add(key)
        new_rows.append(flag_row(row, r, results, reasons, cards, test_types))
    for key, r in index.items():
        if key not in known:
            new_rows.append(flag_row({"benchmark": r["benchmark"], "model": r["model"], "uwagi": []}, r, results, reasons,
                                     cards, test_types))
    (cel / "przeglad.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in new_rows) + "\n",
                                        encoding="utf-8")
    return new_rows


def flag_row(row, r, results, reasons, cards, test_types):
    """One `przeglad.jsonl` record: every value, flag and note comes from the rules and the result files."""
    notes = [n for n in row.get("uwagi", []) if not n.startswith(AUTO_NOTES)]
    if r["model"] in INSTRUCT_MODELS and "model instruct liczony na surowym tekście, bez chat template" not in notes:
        notes.append("model instruct liczony na surowym tekście, bez chat template")
    if wersja_slayera(r["model"]) == "1.08":
        notes.insert(0, SLAYER_1_08_STATUS)
    flag_reasons = list(reasons.get(r["model"], []))
    window = own_window(results, r["model"])
    if window_exceeded(r, window):
        flag_reasons.append(f"reguła okna: WikiText liczony oknem {r['max_length']} tokenów przy oknie modelu {window}")
    notes += flag_reasons
    flag = "do_sprawdzenia" if flag_reasons else "ok"
    base = baseline(test_types[r["benchmark"]], r)
    in_table = cards[r["benchmark"]]["state"] == "control" and flag == "ok" and bool(wersja_slayera(r["model"]) in (None, "1.07"))
    return {"benchmark": r["benchmark"], "zadanie": r["zadanie"], "model": r["model"], "metryka": r["metryka_raw"],
            "wartosc": r["wartosc"] * r["skala_w_pliku"], "se": r["se"] * r["skala_w_pliku"], "n": r["n"], "dtype": r["dtype"],
            "flaga": flag, "uwagi": notes, "kontaminacja": contamination_label(r.get("contamination")),
            "lm_eval": r["lm_eval"], "baza_b": None if base is None else base[0], "w_tabeli_codesota": in_table}


# ------------------------------------------------------------------------- report model

class Run:
    """Data of the README and charts: everything is read from the files of the run directory."""

    def __init__(self, cel: Path, results, flags_rows, cards, test_types, sizes, prog):
        self.cel, self.cards, self.test_types = cel, cards, test_types
        self.flags = {(r["benchmark"], r["model"]): r for r in flags_rows if r.get("benchmark") != "*"}
        self.results = results
        order = list(BENCHMARKI)
        by_test = {}
        for r in results:
            by_test.setdefault(r["benchmark"], {})[r["model"]] = r
        self.V, self.T = {}, []
        for bench in sorted(by_test, key=order.index):
            sample = next(iter(by_test[bench].values()))
            self.V[bench] = {}
            for model, r in by_test[bench].items():
                flag_row_ = self.flags[(bench, model)]
                lo, hi = r["lo"], r["hi"]
                self.V[bench][model] = {"v": r["wartosc"], "se": r["se"], "lo": lo if lo is not None else r["wartosc"],
                                        "hi": hi if hi is not None else r["wartosc"], "f": flag_row_["flaga"],
                                        "u": flag_row_.get("uwagi", []), "dt": r["dtype"], "env": r["env"],
                                        "lm": r["lm_eval"], "base": flag_row_.get("baza_b")}
            type_ = test_types[bench]
            base = baseline(type_, sample)
            self.T.append({"id": bench, "nazwa": TEST_NAMES[bench][0], "sk": TEST_NAMES[bench][1],
                           "metric": METRIC_NAMES.get(sample["metryka"], sample["metryka"]), "n": sample["n"],
                           "chance": sample["chance"], "majority": sample["majority"], "higher": sample["wyzej_lepiej"],
                           "zad": sample["zadanie"], "bk": cards[bench]["state"] != "control", "type": type_,
                           "b": None if base is None else base[0], "b_name": None if base is None else base[1],
                           "verdict": cards[bench]["verdict"]})
        models = sorted({r["model"] for r in results}, key=lambda m: (wersja_slayera(m) or "9", m))
        self.SL = [m for m in models if wersja_slayera(m)]
        self.SLN = [wersja_slayera(m) for m in self.SL]
        self.front = self.SLN.index("1.07")
        self.exp = self.SLN.index("1.08")
        size = lambda m: (sizes.get(m) or {}).get("params")
        self.M = [{"id": m, "label": nazwa(m), "params": size(m), "size": size_label(size(m)), "cl": size_class(size(m)),
                   "kind": "slayer" if wersja_slayera(m) else "ref"} for m in models]
        self.REFS = [x for x in self.M if x["kind"] == "ref"]
        self.MN = {x["id"]: x for x in self.M}
        self.TK = [t for t in self.T if not t["bk"]]
        self.TW = [t for t in self.T if t["bk"]]
        self.ORD = self.TK + self.TW
        self.P1M = {p["benchmark"]: p for p in prog["pierwsza_ostatnia"]}
        self.CH = cel / "charts"
        self.CH.mkdir(parents=True, exist_ok=True)


def digits_of(t):
    return 4 if t["higher"] else 3


def verdict_label(p, t):
    if not p:
        return "–"
    up = p["roznica"] > 0 if t["higher"] else p["roznica"] < 0
    w = p["werdykt_holm"]
    if w == "szum":
        return "≈ szum"
    if w == "pewne":
        return "▲ pewna poprawa" if up else "▼ pewny spadek"
    return "△ prawdopodobna poprawa" if up else "▽ prawdopodobny spadek"


SVG_STYLE = """<style>
svg{--bg:#ffffff;--ink:#1f2328;--mut:#59636e;--grid:#d1d9e0;--sl:#0969da;--ref:#59636e;--tick:#afb8c1;--band:rgba(9,105,218,.1);
--h0:#ddf4ff;--h1:#b6e3ff;--h2:#80ccff;--h3:#54aeff;--h4:#218bff;--h5:#0969da;--h6:#0550ae;--t0:#1f2328;--t1:#1f2328;--t2:#1f2328;--t3:#1f2328;--t4:#1f2328;--t5:#fff;--t6:#fff}
@media (prefers-color-scheme:dark){svg{--bg:#0d1117;--ink:#f0f6fc;--mut:#9198a1;--grid:#3d444d;--sl:#4493f8;--ref:#c9d1d9;--tick:#656c76;--band:rgba(68,147,248,.16);
--h0:#0c2d6b;--h1:#0d419d;--h2:#1158c7;--h3:#1f6feb;--h4:#388bfd;--h5:#58a6ff;--h6:#a5d6ff;--t0:#f0f6fc;--t1:#f0f6fc;--t2:#f0f6fc;--t3:#f0f6fc;--t4:#0d1117;--t5:#0d1117;--t6:#0d1117}}
text{font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;fill:var(--ink);font-size:14px}
.m{fill:var(--mut);font-size:12px}.b{font-weight:600}.n{font-variant-numeric:tabular-nums}.sl{fill:var(--sl)}
.bg{fill:var(--bg);stroke:var(--grid);stroke-width:1}.gl{stroke:var(--grid);stroke-width:1}.dash{stroke:var(--mut);stroke-width:1;stroke-dasharray:4 3}
.wh{stroke:var(--ref);stroke-width:2;stroke-linecap:round}.dot{fill:var(--ref)}.wsl{stroke:var(--sl);stroke-width:3;stroke-linecap:round}
.dsl{fill:var(--sl)}.tk{stroke:var(--tick);stroke-width:3;stroke-linecap:round}.ring{fill:none;stroke:var(--sl);stroke-width:1.5}
</style>"""


def svg_doc(w, h, body, extra="", title=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{E(title)}">'
            f'<title>{E(title)}</title>{SVG_STYLE}{extra}<rect class="bg" x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="8"/>{body}</svg>')


class Charts:
    """SVG charts in the GitHub style: light and dark from `prefers-color-scheme`, motion honours `prefers-reduced-motion`."""

    def __init__(self, run: Run):
        self.run = run

    def save(self, name, text):
        (self.run.CH / name).write_text(text, encoding="utf-8")

    def ok(self, t, mid):
        d = self.run.V[t["id"]].get(mid)
        return d if d and d["f"] == "ok" else None

    def ok_any(self, mid):
        return any((self.run.V[t["id"]].get(mid) or {}).get("f") == "ok" for t in self.run.T)

    def value_range(self, t, ids, margin=0.06):
        values = []
        for i in ids:
            d = self.run.V[t["id"]].get(i)
            if d:
                values += [d["lo"], d["hi"]]
        lo, hi = min(values), max(values)
        b = t["chance"]
        if b is not None and lo - (hi - lo) * 0.9 < b < hi + (hi - lo) * 0.9:
            lo, hi = min(lo, b), max(hi, b)
        pad = (hi - lo) * margin
        return lo - pad, hi + pad

    @staticmethod
    def scale(t, a, b, x0, x1):
        def g(v):
            q = (v - a) / (b - a)
            if not t["higher"]:
                q = 1 - q
            return x0 + q * (x1 - x0)
        return g

    def animation(self):
        r_ = self.run
        tests, cycle, W = r_.TK, 11, 1000
        H0, RH = 92, 50
        H = H0 + len(tests) * RH + 40
        x0, x1 = 250, 830
        front = r_.front
        body, css = [], []
        pc = lambda s: f"{s / cycle * 100:.2f}%"
        for i in range(front + 1):
            a, b = i, (i + 1 if i < front else cycle)
            css.append(f"@keyframes v{i}{{0%,{pc(a - 0.01) if a else '0%'}{{opacity:0}}{pc(a)},{pc(b - 0.02)}{{opacity:1}}{pc(b)},100%{{opacity:{'1' if i == front else '0'}}}}}")
            css.append(f".v{i}{{opacity:{1 if i == front else 0};animation:v{i} {cycle}s linear infinite}}")
        for i, name in enumerate(r_.SLN[: front + 1]):
            body.append(f'<text x="28" y="48" class="b v{i}" style="font-size:30px">Slayer 1B <tspan class="sl">{name}</tspan></text>')
        body.append(f'<text x="28" y="72" class="m">Przemiana wersji {r_.SLN[0]} → {r_.SLN[front]} na tle modeli odniesienia. Testy z przechodzącą kontrolą, lepiej w prawo.</text>')
        body.append(f'<text x="{W - 28}" y="72" class="m" text-anchor="end">wartość</text>')
        ids = r_.SL + [x["id"] for x in r_.REFS if self.ok_any(x["id"])]
        for row, t in enumerate(tests):
            y = H0 + row * RH + 26
            used = [i for i in ids if (r_.V[t["id"]].get(i) or {}).get("f") == "ok"]
            a, b = self.value_range(t, used)
            g = self.scale(t, a, b, x0, x1)
            body.append(f'<text x="28" y="{y - 2}" class="b">{E(t["nazwa"])}</text><text x="28" y="{y + 14}" class="m">{E(t["metric"])}, n = {format_count(t["n"])}</text>')
            body.append(f'<line class="gl" x1="{x0}" x2="{x1}" y1="{y}" y2="{y}"/>')
            if t["chance"] is not None and a < t["chance"] < b:
                xc = g(t["chance"])
                body.append(f'<line class="dash" x1="{xc:.1f}" x2="{xc:.1f}" y1="{y - 12}" y2="{y + 12}"/><text x="{xc:.1f}" y="{y + 23}" class="m" text-anchor="middle" style="font-size:10px">losowy</text>')
            cls_ok = [g(self.ok(t, x["id"])["v"]) for x in r_.REFS if x["cl"] == "ok. 1B" and self.ok(t, x["id"])]
            close = len(cls_ok) == 2 and abs(cls_ok[0] - cls_ok[1]) < 52
            for x in r_.REFS:
                d = self.ok(t, x["id"])
                if not d:
                    continue
                xr = g(d["v"])
                if x["cl"] == "ok. 1B":
                    yt = y + 20 if close and "qwen" in x["id"] else y - 11
                    body.append(f'<circle class="dot" cx="{xr:.1f}" cy="{y}" r="5"/><text x="{xr:.1f}" y="{yt}" class="m" text-anchor="middle">{SHORT_NAMES.get(x["id"], x["label"])}</text>')
                else:
                    body.append(f'<line class="tk" x1="{xr:.1f}" x2="{xr:.1f}" y1="{y - 7}" y2="{y + 7}"/>')
            exp = r_.V[t["id"]][r_.SL[r_.exp]]
            body.append(f'<circle class="ring" cx="{g(exp["v"]):.1f}" cy="{y}" r="6.5"/>')
            xs = [g(r_.V[t["id"]][r_.SL[i]]["v"]) for i in range(front + 1)]
            frames = "".join(f"{pc(i)}{{transform:translateX({xs[i]:.1f}px)}}" for i in range(front + 1))
            css.append(f"@keyframes p{row}{{{frames}{pc(cycle - 1)}{{transform:translateX({xs[front]:.1f}px)}}100%{{transform:translateX({xs[0]:.1f}px)}}}}")
            css.append(f".p{row}{{transform:translateX({xs[front]:.1f}px);animation:p{row} {cycle}s ease-in-out infinite}}")
            body.append(f'<g class="p{row}"><circle class="dsl" cx="0" cy="{y}" r="8"/></g>')
            for i in range(front + 1):
                body.append(f'<text x="{W - 28}" y="{y + 4}" class="n v{i}" text-anchor="end">{format_number(r_.V[t["id"]][r_.SL[i]]["v"], digits_of(t))}</text>')
        yl = H - 16
        body.append(f'<circle class="dsl" cx="36" cy="{yl - 4}" r="6"/><text x="48" y="{yl}" class="m">Slayer, kolejne wersje</text>'
                    f'<circle class="ring" cx="212" cy="{yl - 4}" r="6"/><text x="224" y="{yl}" class="m">1.08, checkpoint eksperymentalny</text>'
                    f'<circle class="dot" cx="442" cy="{yl - 4}" r="5"/><text x="452" y="{yl}" class="m">klasa ok. 1B</text>'
                    f'<line class="tk" x1="548" x2="548" y1="{yl - 10}" y2="{yl + 2}"/><text x="558" y="{yl}" class="m">pozostałe modele odniesienia</text>')
        extra = "<style>" + "".join(css) + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>"
        self.save("przemiana-wersji.svg", svg_doc(W, H, "".join(body), extra, f"Slayer 1B: przemiana wersji {r_.SLN[0]} do {r_.SLN[front]} na tle modeli odniesienia"))

    def matrix(self):
        r_ = self.run
        rows = [(r_.SL[r_.front], f"Slayer 1B {r_.SLN[r_.front]}", True), (r_.SL[r_.exp], "Slayer 1B 1.08 eksp.", True)] + [(x["id"], x["label"], False) for x in r_.REFS]
        cw, ch, X0, Y0 = 52, 30, 210, 62
        W, H = X0 + cw * len(r_.ORD) + 20, Y0 + ch * len(rows) + 44
        b = ['<defs><pattern id="h" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2" height="6" fill="var(--grid)"/></pattern></defs>']
        for j, t in enumerate(r_.ORD):
            x = X0 + j * cw + cw / 2
            b.append(f'<text x="{x}" y="{Y0 - 12}" class="m b" text-anchor="middle">{E(t["sk"] + ("°" if t["bk"] else ""))}</text>')
        if r_.TW:
            xs = X0 + len(r_.TK) * cw - 1
            b.append(f'<line class="gl" x1="{xs}" x2="{xs}" y1="16" y2="{Y0 + ch * len(rows)}"/><text x="{xs + 8}" y="26" class="m">° poza tabelą CodeSOTA</text>')
        for i, (mid, lab, sl) in enumerate(rows):
            y = Y0 + i * ch
            cls = "b sl" if sl else ("" if self.ok_any(mid) else "m")
            b.append(f'<text x="20" y="{y + 20}" class="{cls}">{E(lab)}</text>')
            for j, t in enumerate(r_.ORD):
                x = X0 + j * cw + 1
                d = r_.V[t["id"]].get(mid)
                if not d:
                    b.append(f'<text x="{x + cw / 2 - 1}" y="{y + 20}" class="m" text-anchor="middle">–</text>')
                    continue
                tx = format_number(d["v"], 2).replace("0,", ",", 1) if d["v"] < 1 else format_number(d["v"], 2)
                if d["f"] != "ok":
                    b.append(f'<rect x="{x}" y="{y + 1}" width="{cw - 2}" height="{ch - 2}" rx="3" fill="url(#h)"/><text x="{x + cw / 2 - 1}" y="{y + 20}" class="m n" text-anchor="middle" font-style="italic">{tx}</text>')
                    continue
                vals = [r_.V[t["id"]][k["id"]]["v"] for k in r_.M if (r_.V[t["id"]].get(k["id"]) or {}).get("f") == "ok"]
                best, worst = (max(vals), min(vals)) if t["higher"] else (min(vals), max(vals))
                if t["higher"]:
                    base = t["chance"] if t["chance"] is not None else worst
                    c = (d["v"] - base) / (best - base) if best != base else 0
                else:
                    c = (worst - d["v"]) / (worst - best)
                l = max(0, min(6, round(c * 6)))
                mark = "▾" if t["chance"] is not None and t["higher"] and d["v"] < t["chance"] else ""
                b.append(f'<rect x="{x}" y="{y + 1}" width="{cw - 2}" height="{ch - 2}" rx="3" style="fill:var(--h{l})"/><text x="{x + cw / 2 - 1}" y="{y + 20}" class="n" text-anchor="middle" style="fill:var(--t{l})">{mark}{tx}</text>')
            if sl:
                b.append(f'<rect x="{X0}" y="{y}" width="{cw * len(r_.ORD)}" height="{ch}" rx="4" fill="none" stroke="var(--sl)" stroke-width="1.5"/>')
        yl = H - 16
        for k in range(7):
            b.append(f'<rect x="{62 + k * 22}" y="{yl - 11}" width="20" height="12" style="fill:var(--h{k})"/>')
        b.append(f'<text x="20" y="{yl}" class="m">baza</text><text x="{62 + 7 * 22 + 6}" y="{yl}" class="m">najlepszy w kolumnie</text><text x="{62 + 7 * 22 + 150}" y="{yl}" class="m">▾ poniżej wyniku losowego   paski: do sprawdzenia, poza rankingiem</text>')
        self.save("macierz.svg", svg_doc(W, H, "".join(b), "", "Macierz modeli i testów"))

    def progress(self):
        r_ = self.run
        cols, pw, ph, W = 3, 320, 118, 1000
        rows = (len(r_.ORD) + cols - 1) // cols
        H = rows * ph + 16
        b = []
        strength = lambda t: -abs(r_.P1M[t["id"]].get("z") or r_.P1M[t["id"]].get("t") or 0)
        for n, t in enumerate(sorted(r_.ORD, key=lambda t: (t["bk"], strength(t)))):
            ox, oy = 16 + (n % cols) * (pw + 8), 12 + (n // cols) * ph
            pts = [r_.V[t["id"]][s] for s in r_.SL]
            lo, hi = min(p["lo"] for p in pts), max(p["hi"] for p in pts)
            lines = []
            for c in (t["chance"], t["majority"]):
                if c is not None and lo - (hi - lo) < c < hi + (hi - lo):
                    lo, hi = min(lo, c), max(hi, c)
                    lines.append(c)
            x = lambda i: ox + 8 + i * (pw - 18) / 8
            y = lambda v: oy + 30 + ((1 - (v - lo) / (hi - lo)) if t["higher"] else (v - lo) / (hi - lo)) * 56
            b.append(f'<text x="{ox + 8}" y="{oy + 18}" class="b">{E(t["nazwa"])}{"°" if t["bk"] else ""}</text><text x="{ox + pw - 10}" y="{oy + 18}" class="m" text-anchor="end">{E(verdict_label(r_.P1M[t["id"]], t))}</text>')
            for c in lines:
                b.append(f'<line class="dash" x1="{ox + 8}" x2="{ox + pw - 10}" y1="{y(c):.1f}" y2="{y(c):.1f}"/>')
            up = " ".join(f"{x(i):.1f},{y(p['hi']):.1f}" for i, p in enumerate(pts))
            dn = " ".join(f"{x(i):.1f},{y(p['lo']):.1f}" for i, p in reversed(list(enumerate(pts))))
            b.append(f'<polygon points="{up} {dn}" style="fill:var(--band)"/>')
            line = " ".join(f"{x(i):.1f},{y(p['v']):.1f}" for i, p in enumerate(pts[: r_.front + 1]))
            b.append(f'<polyline points="{line}" fill="none" stroke="var(--sl)" stroke-width="2" stroke-linejoin="round"/>')
            b.append(f'<line x1="{x(r_.front):.1f}" y1="{y(pts[r_.front]["v"]):.1f}" x2="{x(r_.exp):.1f}" y2="{y(pts[r_.exp]["v"]):.1f}" stroke="var(--sl)" stroke-width="1.5" stroke-dasharray="3 3"/>')
            b.append(f'<circle class="dsl" cx="{x(r_.front):.1f}" cy="{y(pts[r_.front]["v"]):.1f}" r="4.5"/><circle class="ring" cx="{x(r_.exp):.1f}" cy="{y(pts[r_.exp]["v"]):.1f}" r="4"/>')
            b.append(f'<text x="{ox + 8}" y="{oy + 104}" class="m n">{r_.SLN[0]}: {format_number(pts[0]["v"], digits_of(t))}</text><text x="{ox + pw - 10}" y="{oy + 104}" class="m n" text-anchor="end">{r_.SLN[r_.front]}: {format_number(pts[r_.front]["v"], digits_of(t))}   1.08: {format_number(pts[r_.exp]["v"], digits_of(t))}</text>')
        self.save("postep-wersji.svg", svg_doc(W, H, "".join(b), "", "Postęp wersji Slayera na każdym teście"))

    def entries(self, t):
        r_ = self.run
        e = [(r_.SL[r_.front], True)] + [(x["id"], False) for x in r_.REFS if self.ok(t, x["id"])]
        e = [(i, s) for i, s in e if self.ok(t, i)]
        e.sort(key=lambda z: r_.V[t["id"]][z[0]]["v"], reverse=t["higher"])
        return e

    def forest(self, t):
        r_ = self.run
        e = self.entries(t)
        W, RH, Y0, x0, x1 = 860, 28, 92, 260, 760
        H = Y0 + RH * len(e) + 58
        a, c = self.value_range(t, [i for i, _ in e])
        g = self.scale(t, a, c, x0, x1)
        step = next(s for s in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1) if s >= (c - a) / 4)
        b, v = [], (int(a / step) + 1) * step
        while v <= c:
            xv = g(v)
            b.append(f'<line class="gl" x1="{xv:.1f}" x2="{xv:.1f}" y1="{Y0 - 6}" y2="{H - 58}"/><text x="{xv:.1f}" y="{Y0 - 12}" class="m n" text-anchor="middle">{format_number(v, 2)}</text>')
            v = round(v + step, 6)
        for base, lab in ((t["chance"], "losowy"), (t["majority"], "najczęstsza")):
            if base is not None and a < base < c:
                xb = g(base)
                b.append(f'<line class="dash" x1="{xb:.1f}" x2="{xb:.1f}" y1="{Y0 - 6}" y2="{H - 58}"/><text x="{xb:.1f}" y="{H - 42}" class="m" text-anchor="middle">{lab}</text>')
        for i, (mid, sl) in enumerate(e):
            y = Y0 + i * RH + 14
            d = r_.V[t["id"]][mid]
            if sl:
                b.append(f'<rect x="12" y="{y - 13}" width="{W - 24}" height="26" rx="5" style="fill:var(--band)"/>')
            b.append(f'<text x="24" y="{y + 4}" class="{"b sl" if sl else ""}">{E(r_.MN[mid]["label"])}</text>')
            l, ri = sorted((g(d["lo"]), g(d["hi"])))
            b.append(f'<line class="{"wsl" if sl else "wh"}" x1="{l:.1f}" x2="{ri:.1f}" y1="{y}" y2="{y}"/><circle class="{"dsl" if sl else "dot"}" cx="{g(d["v"]):.1f}" cy="{y}" r="{7 if sl else 4.5}"/>')
            b.append(f'<text x="{W - 24}" y="{y + 4}" class="n {"b" if sl else ""}" text-anchor="end">{format_number(d["v"], digits_of(t))}</text>')
        b.insert(0, f'<text x="24" y="36" class="b" style="font-size:20px">{E(t["nazwa"])}</text><text x="24" y="58" class="m">{E(t["metric"])}, pełny split (n = {t["n"]}), kreska = CI95</text>')
        b.append(f'<text x="24" y="{H - 14}" class="m">float32; Bielik-11B w bfloat16. benchmarks-fabryka-ai, research/results</text>')
        self.save(f"{t['id']}.svg", svg_doc(W, H, "".join(b), "", f"{t['nazwa']}: ranking z przedziałami 95%"))

    def render_all(self):
        self.animation()
        self.matrix()
        self.progress()
        for t in self.run.ORD:
            self.forest(t)


def md_row(*cells):
    return "| " + " | ".join(str(c) for c in cells) + " |"


def result_row(run: Run, charts: Charts, t):
    d = lambda i: run.V[t["id"]].get(i)
    front = run.SL[run.front]
    cell = lambda x: "–" if not x else (f"{format_number(x['v'], digits_of(t))}&nbsp;±&nbsp;{format_number(x['se'], 4)}" if x["f"] == "ok" else f"*{format_number(x['v'], digits_of(t))}*")
    entries = charts.entries(t)
    place = next(n for n, (i, _) in enumerate(entries, 1) if i == front)
    base = f"{format_number(t['b'], 4)} ({t['b_name']})" if t["b"] is not None else "nie dotyczy"
    in_class = [i for i, _ in entries if run.MN[i]["cl"] == "ok. 1B"]
    progress = first_to_front(t, d(run.SL[0]), d(front))
    mark = ROW_MARKS.get(t["id"], "") if not t["bk"] else ""
    return md_row(f"[{t['nazwa']}](#{t['id']}){mark}", format_count(t["n"]), f"**{cell(d(front))}**", cell(d("pythia-1b-v0")), cell(d("qwen3.5-0.8b-base")), base,
                  f"{place}/{len(entries)}", f"{in_class.index(front) + 1}/{len(in_class)}", progress)


def rel(path, root: Path):
    return str(Path(path).relative_to(root)) if str(path).startswith(str(root)) else str(path)


# --------------------------------------------------------------------------- README

BOS_DIR = "bos-window-check"
ROW_MARKS = {"hellaswag": "¹"}
BOS_SCOPE = ("Testy z niepustym kontekstem: Slayer ma jeden wiodący BOS, modele odniesienia były liczone bez BOS; wpływ zmierzono wyłącznie na Pythii-1B v0. "
             "Nie dotyczy BLiMP i WikiText-2 (pusty kontekst). EWoK: reguła z karty, BOS jest wtedy, gdy dokleja go tokenizer modelu.")


def bos_summary(numbers: dict) -> dict:
    """Headline values of the BOS and window measurement, read from its LICZBY.json."""
    pairs = numbers["pary"]
    bos = [pairs[t] for t in numbers["testy_wariantu_bos"]]
    return {"max_change": max(p["abs_roznica"] for p in bos), "tests": len(bos), "window": pairs["T03"],
            "arc_easy": numbers["arc_easy"], "wikitext_slayer": numbers["t03_slayer"], "arc_control": numbers["kontrola_arc"]}


def slayer_window_check(results) -> dict:
    """Does the rolling WikiText window fit the window of every Slayer version: {ok, length, versions}."""
    rows = [r for r in results if r["benchmark"] == "wikitext-2" and wersja_slayera(r["model"])]
    fits = [r["max_length"] == own_window(results, r["model"]) and own_window(results, r["model"]) is not None for r in rows]
    return {"ok": all(fits) and bool(rows), "length": rows[0]["max_length"] if rows else None, "versions": len(rows)}


def weryfikacja_section(run, a, central):
    a("### Weryfikacja")
    a("")
    equal = [z for z in central if abs(z["nasz"] - z["odniesienie"]) < CENTRAL_DIFF]
    a("- Każdy plik wyników ma sumę sha256 w `manifest.jsonl` (pole `pliki`); paczka z próbkami przeszła ją w "
      "całości przed rozpakowaniem tutaj.")
    a("- Każda wartość została przeliczona od nowa z zapisanych logprobów per pytanie (te same reguły co "
      "`common/metryki.py` i `benchmarks/ewok/ewok.py`): wszystkie pary zgodne co do bitu.")
    if central:
        other = sorted({nazwa(z["model"]) for z in central if z not in equal})
        a(f"- Wspólne pary z `results/central-run` (przebieg centralny fabryki): {len(equal)} z {len(central)} "
          "identycznych do 4 miejsc po przecinku." + (f" Różne tylko: {', '.join(other)} (sekcja "
                                                     "[Do sprawdzenia](#do-sprawdzenia-i-niepoliczone))." if other else ""))
    a("- Kontrole etapu B z `tools/ewaluacja/kontrole.json` (Pythia-1B v0: PIQA, WinoGrande, LAMBADA, ARC-Easy, "
      "BLiMP) dały tu te same wartości co lokalny przebieg kontrolny w `tools/ewaluacja/wyniki_kontrolne/`.")
    a("")


def versions_section(run, a, prog):
    sl = run.SL
    tab = {(m, b): run.V[b].get(m) for b in run.V for m in sl}
    a("Wszystkie wersje mają tę samą architekturę i tokenizer; rewizje HF w `manifest.jsonl`. "
      f"1.07 to wagi z HF (sha256 checkpointu zgodne z `SLAYER_CKPT_SHA256`), etykieta: {slayer_label('1.07')}. "
      f"1.08: {slayer_label('1.08')} ([karta modelu]({CARD_1_08})). Pozostałe wersje: {slayer_label('1.00')}.")
    a("")
    a("| test | " + " | ".join(run.SLN) + " |")
    a("|---|" + "---:|" * len(sl))
    for b, (title, _) in BENCHMARKI.items():
        digits = 3 if b == "wikitext-2" else 4
        a(f"| {title} | " + " | ".join(format_number(tab[(m, b)]["v"], digits) if tab[(m, b)] else "–" for m in sl) + " |")
    a("")
    if not prog:
        return

    def row(r):
        stat = (f"t = {liczba(r['t'], 2)}, df = {r['df']}" if r.get("t") is not None else
                (f"z = {liczba(r['z'], 2)}" if r.get("z") is not None else "–"))
        digits = 3 if r["benchmark"] == "wikitext-2" else 4
        se = liczba(r["se"], 4) + (" bpb" if r["benchmark"] == "wikitext-2" else "")
        return (f"| {BENCHMARKI[r['benchmark']][0]} | {wersja_slayera(r['b'])} → {wersja_slayera(r['a'])} | {liczba(r['roznica'], digits)} | "
                f"{se} | {stat} | {r['werdykt']} | {r['po_holmie']} ({r['werdykt_holm']}) |")
    header = ["| test | wersje | Δ | SE Δ | statystyka | werdykt | po Holmie |", "|---|---|---:|---:|---|---|---|"]
    a(f"### Pierwsza → ostatnia wersja ({len(prog['pierwsza_ostatnia'])} porównań, Holm w tej rodzinie)")
    a("")
    a("Δ = nowsza − starsza na tych samych pytaniach. SE parowane po pytaniach (z) albo po klastrach testu "
      "(t, df = k − 1): BLiMP po paradygmatach, WinoGrande po parach zdań, WSC273 po schematach, EWoK po "
      "szablonach. WikiText: Δ w byte perplexity, SE i t na bits per byte z dokumentem jako klastrem. Werdykt: "
      "|z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum (t przez p przy tym samym progu).")
    a("")
    for x in header:
        a(x)
    for r in prog["pierwsza_ostatnia"]:
        a(row(r))
    a("")
    a(f"### Kolejne wersje ({len(prog['kolejne_wersje'])} porównań, Holm w tej rodzinie)")
    a("")
    for x in header:
        a(x)
    for r in prog["kolejne_wersje"]:
        a(row(r))
    a("")


def bos_section(run, a, bos):
    s = bos_summary(bos)
    win, easy, wiki, arc = s["window"], s["arc_easy"], s["wikitext_slayer"], s["arc_control"]
    a('<a id="bos-okno-wikitext-i-kontrola-arc-challenge"></a>')
    a(f"<details>\n<summary><b>BOS, okno WikiText, kontrola ARC-Challenge</b> (<a href=\"{BOS_DIR}/README.md\">pliki pomiaru</a>)</summary>\n")
    a(f"BOS, sprawdzona wyłącznie Pythia-1B v0: próg protokołu {format_number(PROTOCOL_BOS_THRESHOLD, 2)}, SE niezależne. Tabele raportu zostawiają Pythię bez BOS.")
    a("")
    a(md_row("Test", "bez BOS", "z BOS", "Δ", "SE Δ", "z", "werdykt"))
    a("|---|---:|---:|---:|---:|---:|---|")
    for key in bos["testy_wariantu_bos"]:
        p = bos["pary"][key]
        name = {"T51": "ARC-Easy", "T05": "HellaSwag", "T17": "LAMBADA", "T06": "PIQA", "T07": "WinoGrande", "T14": "WSC273"}[key]
        a(md_row(name, format_number(p["stara"], 4), format_number(p["nowa"], 4), format_number(p["roznica"], 4, plus=True),
                 format_number(p["se_roznicy"], 4), format_number(p["z"], 2), p["werdykt_z"]))
    a("")
    a(f"- ARC-Easy: Slayer 1.07 − Pythia z BOS = {format_number(easy['roznica'], 4)}, z = {format_number(easy['z'], 2)}, SE niezależne, {easy['werdykt_z']}.")
    a(f"- WikiText: Pythia oknem 2048 ma {format_number(win['nowa'], 4)} ({format_number(win['se_nowa'], 4)}) zamiast {format_number(win['stara'], 4)} przy `--max_length 4096`; "
      f"wobec Slayera 1.07 ({format_number(wiki['slayer_1_07'], 4)}) różnica {format_number(wiki['nowa_roznica_pythia_minus_slayer'], 4)}, z = {format_number(wiki['z'], 2)}, SE niezależne, {wiki['werdykt_z']}, eksploracyjnie.")
    a(f"- Kontrola ARC-Challenge nierozstrzygnięta: EuroLLM-1.7B 25-shot {format_number(arc['value'], 4)} wobec {format_number(arc['odniesienie'], 4)}, próg {format_number(arc['prog'], 4)}; "
      "demonstracje pochodzą z testu, a ustawienia referencji nie odtworzono.")
    a("\n</details>\n")


def write_readme(run: Run, charts: Charts, prog, rows, central, env, run_name, bos):
    L = []
    a = L.append
    front_name = run.SLN[run.front]
    front_id = run.SL[run.front]
    gpu = (env.get("gpu") or "?").splitlines()[0].split(",")[0]
    in_table = [r for r in rows if r.get("w_tabeli_codesota")]
    flagged_models = sorted({r["model"] for r in rows if r.get("flaga") == "do_sprawdzenia"})
    a(f"# Pełny przebieg {run_name}: Slayer 1B {front_name} i modele odniesienia")
    a("")
    a("<!-- Plik wygenerowany przez tools/ewaluacja/raport.py. Nie edytuj ręcznie: zmień generator albo dane. -->")
    a("")
    a(f"{len(run.M)} modeli, {len(run.T)} testów, pełne zbiory. Karta {gpu}, float32, batch 1. Wyjątek: Bielik-11B w bfloat16, bez EWoK.")
    a("")
    a('<a href="../../STATUS.md"><img src="../../../docs/img/stan-benchmarkow.svg" alt="Stan benchmarków" height="36"></a> '
      '<a href="../../METODOLOGIA.md"><img src="../../../docs/img/metodologia.svg" alt="Metodologia" height="36"></a> '
      '<a href="https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks"><img src="../../../docs/img/wyniki-na-hf.svg" alt="Wyniki na HF" height="36"></a>')
    a("")
    a("> [!WARNING]")
    a(f"> **BOS nie jest liczony jednakowo.** {BOS_SCOPE} Zmiana u Pythii: "
      f"[najwyżej {format_number(bos_summary(bos)['max_change'], 4)} na testach z pomiaru BOS](#bos-okno-wikitext-i-kontrola-arc-challenge). Pozostałe zastrzeżenia: [Zastrzeżenia](#zastrzeżenia).")
    a("")
    a(f'<p align="center"><img src="charts/przemiana-wersji.svg" alt="Animacja: Slayer 1B od wersji {run.SLN[0]} do {front_name} na tle modeli odniesienia" width="100%"></p>')
    a("")
    a(f"**Slayer {front_name}**: ostatnia przyjęta wersja, bez wygaszania LR. **1.08**: [karta modelu]({CARD_1_08}), {SLAYER_1_08_STATUS}.")
    a("")
    a("## Tabela CodeSOTA")
    a("")
    header = md_row("Test", "n", f"Slayer {front_name}", "Pythia-1B", "Qwen 0.8B", "Baza b", "Miejsce", "W klasie ok. 1B", f"{run.SLN[0]} → {front_name}")
    sep = "|---|---:|---:|---:|---:|---:|:---:|:---:|---|"
    L += [header, sep] + [result_row(run, charts, t) for t in run.TK] + [""]
    hellaswag_note = hellaswag_control_note(run.cards["hellaswag"]["text"])
    a(f"¹ {hellaswag_note}")
    a("")
    a(f"Porównanie parowane {run.SLN[0]} → {front_name} wymaga próbek spoza repo; parowane {run.SLN[0]} → 1.08 jest w [postępie wersji](#postęp-wersji-slayera).")
    a("")
    a(f"<details>\n<summary><b>Wiersze tabeli</b> ({len(in_table)})</summary>\n")
    a(md_row("Test", "Model", "Etykieta", "Parametry", "Klasa", "Wartość", "SE", "CI95", "b", "lm_eval", "Kontaminacja", "Wyniki"))
    a("|---|---|---|---:|---|---:|---:|---|---:|---|---|---|")
    for t in run.TK:
        for mid, _ in charts.entries(t):
            d = run.V[t["id"]][mid]
            x = run.MN[mid]
            version = wersja_slayera(mid)
            label = slayer_label(version) if version else ("model instruct, surowy tekst" if mid in INSTRUCT_MODELS else "–")
            r = run.flags[(t["id"], mid)]
            a(md_row(t["nazwa"], x["label"], label, x["size"], x["cl"], format_number(d["v"], digits_of(t)), format_number(d["se"], 4),
                     f"{format_number(d['lo'], digits_of(t))} – {format_number(d['hi'], digits_of(t))}",
                     "nie dotyczy" if t["b"] is None else format_number(t["b"], 4), d["lm"] or "nie dotyczy (własny kod testu)",
                     r["kontaminacja"], f"[plik]({t['id']}/{mid}/results_rozszerzone.json)"))
    a("\n</details>\n")
    a("<details>\n<summary><b>Typ testu i kontrola etapu B</b></summary>\n")
    a(md_row("Test", "Typ", "Kontrola etapu B"))
    a("|---|---|---|")
    for t in run.TK:
        a(md_row(t["nazwa"], f"`{t['type']}`", t["verdict"]))
    a("\n</details>\n")
    a("### Poza tabelą")
    a("")
    no_control = [t for t in run.TW if t["verdict"].lower().startswith(VERDICT_NO_CONTROL)]
    a(f"- {', '.join(t['nazwa'] for t in no_control)}: bez kontroli, nierozstrzygnięte.")
    for t in run.TW:
        if t not in no_control:
            a(f"- {t['nazwa']}: {OUT_OF_TABLE_REASONS.get(t['id'], t['verdict'])}.")
    for model in flagged_models:
        reasons = sorted({n for r in rows if r.get("model") == model for n in r.get("uwagi", []) if n.startswith("reguła ")})
        a(f"- {nazwa(model)}: " + "; ".join(reasons) + ".")
    a(f"- Slayer {', '.join(v for v in run.SLN if v != front_name)}: inne wersje niż główna, wartości w [postępie wersji](#postęp-wersji-slayera).")
    a("")
    a(f"<details>\n<summary><b>{len(run.TW)} testów poza tabelą</b> (wyniki wstępne)</summary>\n")
    L += [header, sep] + [result_row(run, charts, t) for t in run.TW] + ["", "</details>", ""]
    a("## Mapa modeli")
    a("")
    a('<p align="center"><img src="charts/macierz.svg" alt="Macierz modeli i testów" width="100%"></p>')
    a("")
    a("| Model | Parametry (z wag) | Klasa |\n|---|---:|---|")
    for x in [run.MN[front_id]] + run.REFS:
        a(f"| {x['label']} | {x['size']} | {x['cl']} |")
    a("")
    a(f"Klasa „ok. 1B”: do {format_number(CLASS_1B_LIMIT / 1e9, 2)}B parametrów policzonych z wag ([`sizes.json`](sizes.json)).")
    a("")
    a("## Postęp wersji Slayera")
    a("")
    a('<p align="center"><img src="charts/postep-wersji.svg" alt="Postęp wersji Slayera na każdym teście" width="100%"></p>')
    a("")
    b_lines = []
    versions_section(run, b_lines.append, prog)
    full = "\n".join(b_lines)
    first_key = "### Pierwsza → ostatnia wersja"
    second_key = "### Kolejne wersje"
    values, rest = full.split(first_key, 1) if first_key in full else (full, "")
    a(f"<details>\n<summary><b>Pierwsza → ostatnia wersja</b> ({len(prog['pierwsza_ostatnia'])} porównań, Holm w tej rodzinie)</summary>\n")
    a(rest.split("\n", 1)[1].split(second_key)[0].strip())
    a("\n</details>\n")
    a(f"<details>\n<summary><b>Kolejne wersje</b> ({len(prog['kolejne_wersje'])} porównań)</summary>\n")
    a(rest.split(second_key)[1].split("\n", 1)[1].strip())
    a("\n</details>\n")
    a("<details>\n<summary><b>Wszystkie wersje Slayera</b>, wartości</summary>\n")
    a(values.strip())
    a("\n</details>\n")
    bos_section(run, a, bos)
    a("## Rankingi testów")
    a("")
    for t in run.ORD:
        e = charts.entries(t)
        s = run.V[t["id"]][front_id]
        place = next(n for n, (i, _) in enumerate(e, 1) if i == front_id)
        a(f'<a id="{t["id"]}"></a>\n<details>\n<summary><b>{E(t["nazwa"])}</b>{" (wstępny)" if t["bk"] else ""}: Slayer {front_name} {format_number(s["v"], digits_of(t))}, miejsce {place} z {len(e)}</summary>\n')
        a(f"{t['metric']}, `{t['zad']}`, n = {format_count(t['n'])}" + (f", wynik losowy {format_number(t['chance'], 4)}" if t["chance"] is not None else "") + (f", najczęstsza odpowiedź {format_number(t['majority'], 4)}" if t["majority"] is not None else "") + ".")
        a("")
        a(f'<p align="center"><img src="charts/{t["id"]}.svg" alt="{E(t["nazwa"])}: ranking z przedziałami 95%" width="100%"></p>\n')
        if not t["bk"]:
            a("\n</details>\n")
            continue
        L.extend([md_row("#", "Model", "Etykieta", "Rozmiar", "Wartość", "SE", "CI95", "lm_eval", "Precyzja", "Kontaminacja", "Wyniki"), "|---:|---|---|---:|---:|---:|---|---|---|---|---|"])
        for n, (mid, sl) in enumerate(e, 1):
            d = run.V[t["id"]][mid]
            bold = "**" if sl else ""
            version = wersja_slayera(mid)
            label = slayer_label(version) if version else ("instruct, surowy tekst" if mid in INSTRUCT_MODELS else "–")
            a(md_row(n, f"{bold}{run.MN[mid]['label']}{bold}", label, run.MN[mid]["size"], f"{bold}{format_number(d['v'], digits_of(t))}{bold}", format_number(d["se"], 4),
                     f"{format_number(d['lo'], digits_of(t))} – {format_number(d['hi'], digits_of(t))}", d["lm"] or "nie dotyczy", d["dt"], run.flags[(t["id"], mid)]["kontaminacja"],
                     f"[plik]({t['id']}/{mid}/results_rozszerzone.json)"))
        a("\n</details>\n")
    a("## Zastrzeżenia")
    a("")
    envs = {}
    for r in run.results:
        envs.setdefault(r["lm_eval"], set()).add(r["model"])
    newer = sorted(v for v in envs if v and v != "0.4.9.1")
    lm_note = "; ".join(f"lm_eval {k}: {', '.join(sorted(nazwa(m) for m in envs[k]))}" for k in newer)
    window = slayer_window_check(run.results)
    gap = environment_gap(central)
    gap_note = (f" {'Jedyny model policzony' if len(gap['models']) == 1 else 'Modele policzone'} w obu środowiskach: {', '.join(nazwa(m) for m in gap['models'])}, "
                f"różnica do {format_number(gap['diff'], 4)} ({TEST_NAMES[gap['benchmark']][0]}), przyczyna nieustalona (mogą to być też inne pakiety).") if gap else ""
    notes = [
        f"BOS. {BOS_SCOPE}",
        hellaswag_note,
        f"Dwa środowiska: {lm_note}, pozostałe lm_eval 0.4.9.1.{gap_note}",
        "Różnice między modelami pokazują tylko przedziały; porównania parowane są wyłącznie między wersjami Slayera, a miejsce w tabeli nie mówi o istotności.",
        "Slayer jest uczony głównie po polsku, a testy poza MultiBLiMP-PL są po angielsku; bez oceny łącznej, bo zestaw testów i wagi nie są ustalone.",
        "Slayer 1.00–1.07 to checkpointy bez wygaszania LR; wniosek „słabszy od modelu X” wymaga porównania z Pythią przy tej samej liczbie tokenów, którego tu nie ma.",
        "Kontaminacja: nieznana przy każdym wyniku, skanu nie było.",
        f"Slayer na WikiText-2 mieści się w oknie modelu: {window['length']} tokenów = `block`, wszystkie wersje ({window['versions']})." if window["ok"] else "Slayer na WikiText-2: okno nie zostało potwierdzone.",
        "Pythia-1B na WikiText-2: wynik z limitem 2048 tokenów (okno modelu), poprzedni w polu `poprawka` manifestu.",
    ]
    for x in notes:
        a(f"- {x}")
    a("")
    a("<details>\n<summary><b>Weryfikacja</b></summary>\n")
    weryfikacja_section(run, a, central)
    a("</details>\n")
    a("<details>\n<summary><b>Do sprawdzenia i niepoliczone</b></summary>\n")
    a("### Do sprawdzenia i niepoliczone")
    a("")
    a("Flagi nadają reguły `flag_rules` i `window_exceeded` w `tools/ewaluacja/raport.py`, te same dla każdego modelu: "
      f"(1) `acc_pmi` poniżej bazy losowej na co najmniej {PMI_BELOW_CHANCE_TESTS} testach z PMI (kontekst obniża prawdopodobieństwo poprawnej odpowiedzi); próg ustalony po obejrzeniu tego przebiegu, nie przed nim; "
      "(2) wynik różni się od `results/central-run` przy tej samej rewizji i wagach; (3) WikiText liczony oknem dłuższym niż okno modelu. Spełnienie (1) albo (2) flaguje wszystkie wyniki modelu.")
    a("")
    below = pmi_below_chance(run.results)
    a("Wrażliwość reguły (1), `acc_pmi` poniżej bazy losowej, z = (wartość − baza) / SE:")
    a("")
    a(md_row("Model", "Test", "acc_pmi", "SE", "Baza losowa", "z", "werdykt"))
    a("|---|---|---:|---:|---:|---:|---|")
    for x in below:
        a(md_row(nazwa(x["model"]), TEST_NAMES[x["benchmark"]][0], format_number(x["value"], 4), format_number(x["se"], 4),
                 format_number(x["chance"], 4), format_number(x["z"], 2), x["verdict"]))
    a("")
    at_rule = models_at_threshold(below, PMI_BELOW_CHANCE_TESTS)
    weak = [m for m in at_rule if all(abs(x["z"]) < 2 for x in below if x["model"] == m)]
    extra = [m for m in models_at_threshold(below, 1) if m not in at_rule]
    a(f"Przy progu {PMI_BELOW_CHANCE_TESTS} wypadają {', '.join(nazwa(m) for m in at_rule)}; "
      f"{', '.join(nazwa(m) for m in weak)} przez wartości z |z| < 2. Przy progu 1 wypadłyby też {', '.join(nazwa(m) for m in extra)}.")
    a("")
    for r in rows:
        if r.get("flaga") == "niepoliczone":
            where = "wszystkie testy" if r.get("benchmark") == "*" else BENCHMARKI[r["benchmark"]][0]
            a(f"- **{nazwa(r['model'])}** ({where}), niepoliczone: " + "; ".join(r.get("uwagi", [])) + ".")
    diffs = [z for z in central if abs(z["nasz"] - z["odniesienie"]) >= CENTRAL_DIFF]
    if diffs:
        a("")
        a(f"Różnice wobec `results/central-run` (ten sam model, rewizja i sha256 wag; tam lm_eval {diffs[0]['lm_eval_odn']}, tu {diffs[0]['lm_eval']}):")
        a("")
        a("| test | model | tu | central-run |")
        a("|---|---|---:|---:|")
        for z in diffs:
            a(f"| {BENCHMARKI[z['benchmark']][0]} | {nazwa(z['model'])} | {liczba(z['nasz'])} | {liczba(z['odniesienie'])} |")
    a("\n</details>\n")
    a("<details>\n<summary><b>Pliki i odtworzenie</b></summary>\n")
    a("### Pliki i odtworzenie")
    a("")
    a("| plik | zawartość |")
    a("|---|---|")
    a("| `<test>/<model>/results.json` | wynik w schemacie Space (obserwacja, protokół, provenance) |")
    a("| `<test>/<model>/results_rozszerzone.json` | to samo + metryki dodatkowe, SE, CI95, bazy, wersja lm_eval, dtype |")
    a("| `<test>/<model>/scores-history-wiersz.csv` | wiersz w formacie scores-history.csv |")
    a("| `manifest.jsonl` | jedna linia na parę model × test: repo, rewizja, env, dtype, komenda, czas, karta, sha256 wag, runnera i każdego pliku; SE w skali wartości z tego wiersza |")
    a("| `srodowisko.json` | commit fabryki, karta i stan środowisk `lock` i `new` |")
    a("| `czasy.jsonl` | start, koniec i czas każdej pary oraz pobierania wag |")
    a("| `przeglad.jsonl` | flaga, uwagi, kontaminacja, baza b, wersja lm_eval i `w_tabeli_codesota` każdego wyniku |")
    a("| `sizes.json` | liczba parametrów każdego modelu policzona z wag |")
    a("| `progresja.json` | porównania parowane wersji Slayera z tabel wyżej |")
    a(f"| `{BOS_DIR}/` | pomiar BOS i okna na Pythii oraz kontrola ARC-Challenge: protokół, raport, liczby, kod, wyniki bez próbek |")
    a("| `charts/` | wykresy SVG z wartości tego katalogu |")
    a("")
    pack = env.get("paczka_probek") or {}
    if pack:
        a(f"Próbki per pytanie (logprob każdej odpowiedzi, prompt, hash dokumentu) i logi par są w paczce `{pack['nazwa']}` (sha256 `{pack['sha256']}`), poza repo, bo skompresowane mają kilkaset MB.")
        a("")
    a("Odtworzenie jednej pary (komenda z `manifest.jsonl`, pole `komenda`, albo przez runner):")
    a("")
    a("```bash")
    a("python tools/ewaluacja/ewaluacja.py --wyniki wyniki licz slayer1b-1.06 --zadania T02 --pobierz")
    a("```")
    a("")
    a("Cały przebieg: te same kolejki co tutaj, jedna na kartę (`CUDA_VISIBLE_DEVICES`), `--zadania gotowe --pobierz --usun-wagi`, potem `ewaluacja.py eksport`. "
      "Ten plik i wykresy: `python tools/ewaluacja/raport.py results/full-run-2026-11 results/full-run-2026-11 --bez-porownan --odniesienie results/central-run`.")
    a("\n</details>\n")
    (run.cel / "README.md").write_text("\n".join(L), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paczka", help="katalog z manifest.jsonl: rozpakowany eksport albo sam katalog przebiegu")
    ap.add_argument("cel", help="katalog raportu, np. results/full-run-2026-11")
    ap.add_argument("--przeglad", help="przeglad.jsonl z flagami wyników (domyślnie z katalogu raportu)")
    ap.add_argument("--odniesienie", help="katalog innego przebiegu do porównania, np. results/central-run")
    ap.add_argument("--nazwa", default="2026-11-09")
    ap.add_argument("--bez-porownan", dest="bez_porownan", action="store_true",
                    help="bez przeliczania porównań parowanych (progresja.json z katalogu raportu)")
    a = ap.parse_args()
    paczka, cel = Path(a.paczka), Path(a.cel)
    cel.mkdir(parents=True, exist_ok=True)
    source_list = Path(a.przeglad) if a.przeglad else cel / "przeglad.jsonl"
    old_rows = [json.loads(l) for l in source_list.read_text(encoding="utf-8").splitlines()] if source_list.exists() else []
    results = wczytaj_wyniki(paczka)
    if paczka.resolve() != cel.resolve():
        kopiuj(paczka, cel)
    prog = None
    if a.bez_porownan and (cel / "progresja.json").exists():
        prog = json.loads((cel / "progresja.json").read_text(encoding="utf-8"))
    elif not a.bez_porownan:
        prog = progresja(results, paczka)
        (cel / "progresja.json").write_text(json.dumps(prog, ensure_ascii=False, indent=1), encoding="utf-8")
    env = json.loads((cel / "srodowisko.json").read_text(encoding="utf-8"))
    bos = json.loads((cel / BOS_DIR / "LICZBY.json").read_text(encoding="utf-8"))
    sizes = json.loads((cel / "sizes.json").read_text(encoding="utf-8"))
    cards = read_cards(RESEARCH / "benchmarks", BENCHMARKI)
    test_types = read_test_types((RESEARCH / "README.md").read_text(encoding="utf-8"))
    central = zgodnosc_z_odniesieniem(results, Path(a.odniesienie) if a.odniesienie else None)
    rows = refresh_files(cel, results, old_rows, flag_rules(results, central), cards, test_types)
    run = Run(cel, results, rows, cards, test_types, sizes, prog)
    charts = Charts(run)
    charts.render_all()
    write_readme(run, charts, prog, rows, central, env, a.nazwa, bos)
    print(f"{cel / 'README.md'}: {len(results)} wyników, testów w tabeli {len(run.TK)}, wierszy {sum(1 for r in rows if r.get('w_tabeli_codesota'))}")


if __name__ == "__main__":
    main()
