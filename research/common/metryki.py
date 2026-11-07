"""Czyste funkcje: metryki z próbek lm-eval, niepewność, bazy odniesienia, obserwacje Space.

Wejście to rekord `--log_samples` lm-eval: `arguments` = [(kontekst, kontynuacja)],
`filtered_resps` = [(loglik, czy_zachłanne)], `target` = indeks poprawnej odpowiedzi.
Przy `acc_mutual_info` lista ma 2k pozycji: k warunkowych, potem k bezwarunkowych.
"""

import hashlib
import math
from collections import Counter

import numpy as np

SEED = 20261028
POWTORZENIA = 10000
LN2 = math.log(2)


# --- próbka panelu Space ---

def ranking_panel(benchmark_id, member_task, source_ids, n=200):
    """Indeksy dokumentów wybranych jak w METHOD.md: rosnąco po SHA-256 `20261028|benchmark|member|source_id`."""
    klucz = lambda i: hashlib.sha256(f"{SEED}|{benchmark_id}|{member_task}|{source_ids[i]}".encode()).hexdigest()
    return sorted(sorted(range(len(source_ids)), key=klucz)[:n])


def ranking_banku(benchmark_id, member_task, source_ids):
    """Kolejność dokumentów banku demonstracji (METODOLOGIA, „Przykłady few-shot”).

    Klucz panelu z przestrzenią `support`, która oddziela tę kolejność od panelu:
    SHA-256 `20261028|benchmark|member|support|source_id`, rosnąco. Demonstracje to pierwsze dokumenty tej kolejności.
    """
    klucz = lambda i: hashlib.sha256(f"{SEED}|{benchmark_id}|{member_task}|support|{source_ids[i]}".encode()).hexdigest()
    return sorted(range(len(source_ids)), key=klucz)


# --- rozbiór próbki ---

def rozbierz_mc(probka, z_pmi=True):
    """(logliki warunkowe, bezwarunkowe albo None, kontynuacje, indeks poprawnej).

    `z_pmi`: zadanie liczone z `acc_mutual_info`, więc druga połowa listy to logliki bezwarunkowe.
    Przy pustym kontekście (MultiBLiMP) PMI jest tożsamościowo zerowe i zwracamy None.
    """
    lls = [float(r[0]) for r in probka["filtered_resps"]]
    args = probka["arguments"]
    k = len(lls) // 2 if z_pmi else len(lls)
    bezw = lls[k:] if z_pmi and any(a[0] != "" for a in args[:k]) else None
    konty = [a[1] for a in args[:k]]
    gold = int(probka["gold"]) if "gold" in probka else indeks_celu(probka["target"], konty)
    return lls[:k], bezw, konty, gold


def indeks_celu(target, konty):
    """lm-eval zapisuje cel jako indeks albo jako tekst wyboru (PubMedQA: „yes"/„no"/„maybe").

    GOTCHA: in a multi-context task (WinoGrande, WSC273) every choice has the same continuation and
    `target` is that text, so `.index` gave 0 for every question; the gold index comes from the task's
    `doc_to_text` and travels as `probka["gold"]` (ewaluuj.py sets it).
    """
    try:
        return int(target)
    except (TypeError, ValueError):
        konty = [c.strip() for c in konty]
        if len(konty) > 1 and len(set(konty)) == 1:
            raise ValueError("multi-context task: target is the shared continuation, pass probka['gold']")
        return konty.index(str(target).strip())


def argmax(wartosci):
    return max(range(len(wartosci)), key=lambda i: wartosci[i])


def oceny_mc(probka, z_pmi=True):
    """Wyniki jednej próbki MC: trafienia acc / acc_norm / acc_pmi, predykcja i BPB poprawnej odpowiedzi.

    acc_norm jak w lm-eval: loglik dzielony przez długość odpowiedzi w znakach (bez separatora).
    BPB poprawnej: -loglik / (ln2 · bajty kontynuacji z separatorem), bo tyle bajtów model przewidział.
    """
    lls, bezw, konty, gold = rozbierz_mc(probka, z_pmi)
    dlug = [max(len(c.lstrip(" ")), 1) for c in konty]
    pred = argmax(lls)
    pred_norm = argmax([ll / d for ll, d in zip(lls, dlug)])
    wynik = {"k": len(lls), "gold": gold, "pred": pred, "pred_acc": pred, "pred_acc_norm": pred_norm,
             "acc": float(pred == gold), "acc_norm": float(pred_norm == gold),
             "bpb_poprawnej": -lls[gold] / (LN2 * max(len(konty[gold].encode("utf-8")), 1))}
    if bezw is not None:
        wynik["acc_pmi"] = float(argmax([a - b for a, b in zip(lls, bezw)]) == gold)
    return wynik


# --- niepewność ---

def srednia_z_niepewnoscia(wartosci, seed=SEED, powtorzenia=POWTORZENIA):
    """Średnia, n, SE (odchylenie z próby / √n) i CI95 z bootstrapu percentylowego."""
    x = np.asarray(wartosci, dtype=float)
    n = len(x)
    if n == 0:
        return {"value": None, "n": 0, "se": None, "ci95": None}
    se = float(x.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(powtorzenia, n))
    sr = x[idx].mean(axis=1)
    lo, hi = np.percentile(sr, [2.5, 97.5])
    return {"value": float(x.mean()), "n": n, "se": se, "ci95": [float(lo), float(hi)]}


def perplexity(logliki, slowa, bajty, tokeny=None, seed=SEED, powtorzenia=POWTORZENIA):
    """word/byte(/token) perplexity i bits per byte ze strumienia dokumentów; CI95 i SE z bootstrapu po dokumentach.

    token perplexity zależy od tokenizera modelu — porównywalna tylko w obrębie jednej rodziny (kolumna
    wikitext2_token_ppl w scores-history.csv Space Slayer1B).
    """
    ll, w, b = (np.asarray(v, dtype=float) for v in (logliki, slowa, bajty))
    t = np.asarray(tokeny, dtype=float) if tokeny is not None else None
    n = len(ll)

    def miary(ll_, w_, b_, t_):
        m = {"word_perplexity": np.exp(-ll_.sum(-1) / w_.sum(-1)),
             "byte_perplexity": np.exp(-ll_.sum(-1) / b_.sum(-1)),
             "bits_per_byte": -ll_.sum(-1) / (LN2 * b_.sum(-1))}
        if t_ is not None:
            m["token_perplexity"] = np.exp(-ll_.sum(-1) / t_.sum(-1))
        return m

    punkt = miary(ll, w, b, t)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(powtorzenia, n))
    boot = miary(ll[idx], w[idx], b[idx], t[idx] if t is not None else None)
    wynik = {}
    for nazwa, v in punkt.items():
        lo, hi = np.percentile(boot[nazwa], [2.5, 97.5])
        wynik[nazwa] = {"value": float(v), "n": n, "se": float(boot[nazwa].std(ddof=1)),
                        "ci95": [float(lo), float(hi)]}
    return wynik


# --- bazy odniesienia ---

def bazy_mc(oceny, klasy_stale, klucz="acc"):
    """Baza losowa (średnie 1/k), większościowa (stała klasa złota) i udział najczęstszej predykcji metryki `klucz`."""
    n = len(oceny)
    losowa = sum(1 / o["k"] for o in oceny) / n
    if not klasy_stale:
        return {"chance_value": losowa, "majority_value": None,
                "majority_prediction_share": None, "constant_prediction": None}
    zlote = Counter(o["gold"] for o in oceny)
    pred = Counter(o[f"pred_{klucz}"] for o in oceny)
    udzial = pred.most_common(1)[0][1] / n
    return {"chance_value": losowa, "majority_value": zlote.most_common(1)[0][1] / n,
            "majority_prediction_share": udzial, "constant_prediction": udzial == 1.0}


def podsumuj_mc(probki, klasy_stale, z_pmi=True, klucz="acc"):
    """Wszystkie metryki wariantu MC: acc, acc_norm, acc_pmi, BPB poprawnej + bazy (dla metryki głównej `klucz`)."""
    oceny = [oceny_mc(p, z_pmi) for p in probki]
    wynik = {m: srednia_z_niepewnoscia([o[m] for o in oceny])
             for m in ("acc", "acc_norm", "acc_pmi", "bpb_poprawnej") if all(m in o for o in oceny)}
    wynik["bazy"] = bazy_mc(oceny, klasy_stale, klucz)
    # udział najczęstszej predykcji liczony zawsze — to sygnał „stałej litery" także bez stałych klas
    wynik["udzial_najczestszej_predykcji"] = Counter(o[f"pred_{klucz}"] for o in oceny).most_common(1)[0][1] / len(oceny)
    return wynik


def podsumuj_rolling(probki, proces, licz_tokeny=None):
    """Perplexity ze strumienia: `proces(doc, [loglik])` daje (loglik, słowa) i (loglik, bajty) jak w lm-eval.

    `licz_tokeny(tekst)` (tokenizer ocenianego modelu) dokłada token perplexity; tekst = argument żądania.
    """
    ll, w, b, t = [], [], [], []
    for p in probki:
        r = proces(p["doc"], [float(p["filtered_resps"][0])])
        ll.append(r["word_perplexity"][0])
        w.append(r["word_perplexity"][1])
        b.append(r["byte_perplexity"][1])
        if licz_tokeny is not None:
            t.append(licz_tokeny(p["arguments"][0][0]))
    return perplexity(ll, w, b, t if licz_tokeny is not None else None)


# --- grupy z wagami (+warstwy), METODOLOGIA „Ustawienia przebiegu centralnego” ---

def przydzial_grupy(populacje, budzet):
    """Liczba dokumentów panelu per podtest: min(2, N_i), potem każdy slot do podtestu o największym
    budzet·w_i − przydzielone (w_i = N_i / N), remis po nazwie podtestu."""
    nazwy = sorted(populacje)
    suma = sum(populacje.values())
    przydz = {m: min(2, populacje[m]) for m in nazwy}
    while sum(przydz.values()) < min(budzet, suma):
        wolne = [m for m in nazwy if przydz[m] < populacje[m]]
        m = max(wolne, key=lambda m: (budzet * populacje[m] / suma - przydz[m], -nazwy.index(m)))
        przydz[m] += 1
    return przydz


def warstwy(wartosci, wagi, seed=SEED, powtorzenia=POWTORZENIA):
    """Średnia podtestów ze stałymi wagami: SE W = √(Σ wᵢ² SEᵢ²), CI95 z bootstrapu losującego wewnątrz podtestów.

    `wartosci`: {podtest: wyniki per pytanie}; `wagi`: {podtest: waga} (normalizowane do sumy 1 po obecnych podtestach).
    """
    suma_w = sum(wagi[m] for m in wartosci)
    rng = np.random.default_rng(seed)
    wartosc, wariancja, boot, czlonkowie = 0.0, 0.0, np.zeros(powtorzenia), {}
    for m in sorted(wartosci):
        x = np.asarray(wartosci[m], dtype=float)
        if len(x) == 0:
            raise ValueError(f"pusty podtest {m}")  # brak członka grupy to jawny błąd (METODOLOGIA, panel)
        w = wagi[m] / suma_w
        se = float(x.std(ddof=1) / math.sqrt(len(x))) if len(x) > 1 else 0.0
        wartosc += w * x.mean()
        wariancja += w * w * se * se
        boot += w * x[rng.integers(0, len(x), size=(powtorzenia, len(x)))].mean(axis=1)
        czlonkowie[m] = {"value": float(x.mean()), "n": len(x), "se": se, "waga": w}
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"value": float(wartosc), "n": sum(c["n"] for c in czlonkowie.values()), "se": math.sqrt(wariancja),
            "ci95": [float(lo), float(hi)], "czlonkowie": czlonkowie}


def wazona_baza(bazy, wagi):
    """Bazy podtestów złożone wagami oryginału (typ `+warstwy`: baza w każdym podteście osobno, potem średnia)."""
    suma_w = sum(wagi[m] for m in bazy)
    wynik = {}
    for k in ("chance_value", "majority_value"):
        v = [bazy[m][k] for m in bazy]
        wynik[k] = None if any(x is None for x in v) else sum(wagi[m] / suma_w * bazy[m][k] for m in bazy)
    udzialy = [bazy[m].get("majority_prediction_share") for m in bazy]
    wynik["majority_prediction_share"] = None if None in udzialy else max(udzialy)
    wynik["constant_prediction"] = None if None in udzialy else all(u == 1.0 for u in udzialy)
    return wynik


# --- metryki korpusowe (typy `mcc`, `f1-korpus`): SE B z bootstrapu po pytaniach ---

def mcc(zlote, pred):
    """Współczynnik Matthewsa dla k klas (wzór Gorodkina, jak sklearn); 0, gdy mianownik jest zerowy."""
    klasy = sorted(set(zlote) | set(pred), key=str)
    poz = {k: i for i, k in enumerate(klasy)}
    c = np.zeros((len(klasy), len(klasy)))
    for z, p in zip(zlote, pred):
        c[poz[z], poz[p]] += 1
    t, p, s = c.sum(axis=1), c.sum(axis=0), c.sum()
    licznik = np.trace(c) * s - (t * p).sum()
    mianownik = math.sqrt(s * s - (p * p).sum()) * math.sqrt(s * s - (t * t).sum())
    return float(licznik / mianownik) if mianownik else 0.0


def f1_korpus(zlote, pred, srednia="binary", pozytywna=1):
    """F1 na całym zbiorze: `binary` dla klasy `pozytywna` albo `macro` po klasach złotych i przewidzianych."""
    def f1_klasy(k):
        tp = sum(1 for z, p in zip(zlote, pred) if z == k and p == k)
        fp = sum(1 for z, p in zip(zlote, pred) if z != k and p == k)
        fn = sum(1 for z, p in zip(zlote, pred) if z == k and p != k)
        return 2 * tp / (2 * tp + fp + fn) if tp else 0.0
    if srednia == "binary":
        return f1_klasy(pozytywna)
    klasy = sorted(set(zlote) | set(pred), key=str)
    return sum(f1_klasy(k) for k in klasy) / len(klasy)


def korpusowa_z_niepewnoscia(zlote, pred, funkcja, seed=SEED, powtorzenia=POWTORZENIA):
    """Metryka korpusowa: wartość na całym zbiorze, SE i CI95 z bootstrapu pytań liczonego od nowa (SE B)."""
    z, p = list(zlote), list(pred)
    n = len(z)
    rng = np.random.default_rng(seed)
    boot = np.array([funkcja([z[i] for i in idx], [p[i] for i in idx])
                     for idx in rng.integers(0, n, size=(powtorzenia, n))])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"value": funkcja(z, p), "n": n, "se": float(boot.std(ddof=1)), "ci95": [float(lo), float(hi)]}


# --- TruthfulQA MC2 (masa) i SQuAD 2.0 per pytanie ---

def mc2(logliki, etykiety):
    """Masa prawdopodobieństwa poprawnych opcji jak `process_results_mc2` lm-eval 6d2abda4: opcje do pierwszego 0
    w etykietach są prawdziwe. Odjęcie maksimum przed exp nie zmienia ilorazu, a chroni przed 0/0."""
    podzial = list(etykiety).index(0)
    p = np.exp(np.asarray(logliki, dtype=float) - max(logliki))
    return float(p[:podzial].sum() / p.sum())


def squad_normalizuj(tekst):
    """normalize_answer oficjalnego skryptu SQuAD 2.0 (ten sam kod liczy moduł `evaluate` squad_v2)."""
    import re
    import string
    tekst = "".join(ch for ch in tekst.lower() if ch not in set(string.punctuation))
    tekst = re.sub(r"\b(a|an|the)\b", " ", tekst)
    return " ".join(tekst.split())


def _squad_zlote(zlote):
    zlote = [z for z in zlote if squad_normalizuj(z)]
    return zlote or [""]


def squad_em(pred, zlote):
    return float(max(squad_normalizuj(pred) == squad_normalizuj(z) for z in _squad_zlote(zlote)))


def squad_f1(pred, zlote):
    """F1 tokenów najlepszej złotej odpowiedzi; pytanie bez odpowiedzi daje 1 tylko za pustą predykcję."""
    def f1(z):
        tz, tp = squad_normalizuj(z).split(), squad_normalizuj(pred).split()
        if not tz or not tp:
            return float(tz == tp)
        wspolne = sum((Counter(tz) & Counter(tp)).values())
        if wspolne == 0:
            return 0.0
        precyzja, czulosc = wspolne / len(tp), wspolne / len(tz)
        return 2 * precyzja * czulosc / (precyzja + czulosc)
    return max(f1(z) for z in _squad_zlote(zlote))


# --- obserwacja w schemacie Space (urn:fabryka-ai:benchmark-results:2:protocol-0.3.1) ---

def skala(wartosc, unit):
    if wartosc is None:
        return None
    return wartosc * 100 if unit == "percent" else wartosc


def ci_space(ci, unit):
    if ci is None:
        return None
    return {"lower": skala(ci[0], unit), "upper": skala(ci[1], unit), "level": 0.95,
            "method": "paired_bootstrap", "replicates": POWTORZENIA, "seed": SEED}


def obserwacja(task_id, meta, model_id, protocol_id, glowna, bazy, n_population, n_selected,
               digests, state="ok", reason=None):
    """Obserwacja zgodna ze schematem Space; `glowna` = {value, n, ci95} metryki głównej w ułamku."""
    unit = meta["unit"]
    ok = state == "ok"
    ref = None
    if bazy is not None:
        ref = {k: (skala(v, unit) if k in ("chance_value", "majority_value") else v) for k, v in bazy.items()}
    obs = {"task_id": task_id, "model_id": model_id, "protocol_id": protocol_id,
           "metric": meta["metric"], "unit": unit, "higher_is_better": meta["higher_is_better"],
           "n_population": n_population, "n_selected": n_selected,
           "n_scored": glowna["n"] if ok else 0, "state": state,
           "value": skala(glowna["value"], unit) if ok else None,
           "ci95": ci_space(glowna["ci95"], unit) if ok else None,
           "source_id_digest": digests.get("source_id") if ok else None,
           "results_sha256": digests.get("results") if ok else None,
           "runner_sha256": digests.get("runner") if ok else None,
           "contamination": "unscanned", "contamination_receipt_sha256": None, "reference": ref}
    if reason:
        obs["reason"] = reason[:200]
    return obs


KOLUMNY_HISTORII = ["model", "step", "tokens", "checkpoint_sha256", "arc_easy", "blimp", "wikitext2_token_ppl",
                    "wikitext2_byte_ppl", "eff", "multiblimp_pl", "arc_easy_pl", "eval_gpu"]


def wiersz_historii(rozszerzone, model, step, tokens, checkpoint_sha256, eval_gpu):
    """Wiersz w kolumnach scores-history.csv (Space SlayerLab/Slayer1B); puste = nie mierzymy tego tutaj.

    arc_easy, blimp, eff i arc_easy_pl nie są w naszym zestawie (eff nie ma definicji w Space), więc
    zostają puste zamiast zgadniętej wartości. Liczby w konwencji pliku: procenty 2 miejsca, ppl 4.
    """
    po_id = {o["task_id"]: o.get("dodatkowe") or {} for o in rozszerzone}
    wt = po_id.get("T03", {}).get("space", {})
    mb = po_id.get("T04", {}).get("space", {})

    def liczba(m, mnoznik, miejsca):
        return "" if not m or m.get("value") is None else f"{m['value'] * mnoznik:.{miejsca}f}"

    return {"model": model, "step": "" if step is None else step, "tokens": "" if tokens is None else tokens,
            "checkpoint_sha256": checkpoint_sha256 or "", "arc_easy": "", "blimp": "",
            "wikitext2_token_ppl": liczba(wt.get("token_perplexity"), 1, 4),
            "wikitext2_byte_ppl": liczba(wt.get("byte_perplexity"), 1, 4), "eff": "",
            "multiblimp_pl": liczba(mb.get("acc"), 100, 2), "arc_easy_pl": "", "eval_gpu": eval_gpu or ""}


def sha256_tekstu(tekst):
    return hashlib.sha256(tekst.encode("utf-8")).hexdigest()


def _fmt(m):
    if not m or m.get("value") is None:
        return "—"
    se = f" ±{m['se']:.3f}" if m.get("se") is not None else ""
    return f"{m['value']:.3f}{se}"


def tabela_md(rozszerzone):
    """Tabela do podsumowania: wariant × metryki, z SE i bazami; SE przy n tej próbki."""
    wiersze = ["| zadanie | wariant | n | acc | acc_norm | acc_pmi | BPB poprawnej | losowa | większ. | najczęstsza pred. |",
               "|---|---|---|---|---|---|---|---|---|---|"]
    for o in rozszerzone:
        if not o.get("dodatkowe"):
            wiersze.append(f"| {o['task_id']} | — | 0 | {o['state']}: {o.get('reason', '')[:80]} | | | | | | |")
            continue
        for wariant, d in o["dodatkowe"].items():
            if "byte_perplexity" in d:
                bp = d["byte_perplexity"]
                wiersze.append(f"| {o['task_id']} | {wariant} | {bp['n']} | byte_ppl {_fmt(bp)} | "
                               f"word_ppl {_fmt(d['word_perplexity'])} | | BPB {_fmt(d['bits_per_byte'])} | | | |")
                continue
            b = d["bazy"]
            maj = f"{b['majority_value']:.3f}" if b["majority_value"] is not None else "—"
            if "glowna" in d:  # generation, mass, corpus metric: one main metric instead of acc/acc_norm/PMI
                g, udz = d["glowna"], d.get("udzial_najczestszej_predykcji")
                wiersze.append(f"| {o['task_id']} | {wariant} | {g['n']} | {g['metryka']} {_fmt(g)} | | | | "
                               f"{b['chance_value']:.3f} | {maj} | {'—' if udz is None else f'{udz:.2f}'} |")
                continue
            wiersze.append(f"| {o['task_id']} | {wariant} | {d['acc']['n']} | {_fmt(d['acc'])} | {_fmt(d['acc_norm'])} | "
                           f"{_fmt(d.get('acc_pmi'))} | {_fmt(d['bpb_poprawnej'])} | {b['chance_value']:.3f} | {maj} | "
                           f"{d['udzial_najczestszej_predykcji']:.2f} |")
    return "\n".join(wiersze) + "\n"


WYMAGANE_OBS = ["task_id", "model_id", "protocol_id", "metric", "unit", "higher_is_better", "n_population",
                "n_selected", "n_scored", "state", "value", "ci95", "source_id_digest", "results_sha256",
                "runner_sha256", "contamination", "contamination_receipt_sha256"]
WYMAGANE_GORA = ["schema_version", "protocol_id", "run_id", "models", "tasks", "observations", "contrasts",
                 "provenance"]
STANY = {"ok", "not_run", "blocked_access", "blocked_runtime", "blocked_security", "blocked_judge",
         "unsupported", "failed", "skipped"}


def bledy_schematu(wyniki):
    """Lista naruszeń najważniejszych reguł schematu Space (pełny JSON Schema jest w Space, nie lokalnie)."""
    bledy = [f"brak pola {k}" for k in WYMAGANE_GORA if k not in wyniki]
    for o in wyniki.get("observations", []):
        tag = f"{o.get('task_id')}/{o.get('model_id')}"
        bledy += [f"{tag}: brak {k}" for k in WYMAGANE_OBS if k not in o]
        if o.get("state") not in STANY:
            bledy.append(f"{tag}: zły state {o.get('state')}")
        if o.get("state") == "ok":
            if not isinstance(o.get("value"), (int, float)) or o.get("n_scored", 0) < 1:
                bledy.append(f"{tag}: ok bez wartości albo n_scored")
            for k in ("source_id_digest", "results_sha256", "runner_sha256"):
                v = o.get(k)
                if not (isinstance(v, str) and len(v) == 64):
                    bledy.append(f"{tag}: {k} nie jest sha256")
        elif o.get("value") is not None or o.get("ci95") is not None:
            bledy.append(f"{tag}: wartość przy stanie {o.get('state')}")
    return bledy
