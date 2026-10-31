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
    return lls[:k], bezw, konty, indeks_celu(probka["target"], konty)


def indeks_celu(target, konty):
    """lm-eval zapisuje cel jako indeks albo jako tekst wyboru (PubMedQA: „yes"/„no"/„maybe")."""
    try:
        return int(target)
    except (TypeError, ValueError):
        return [c.strip() for c in konty].index(str(target).strip())


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
