"""Niezależna ewaluacja checkpointu Slayera 1B: lm-eval + metryki dodatkowe, wynik w formacie Space.

Przykłady:
  python common/ewaluuj.py --model hf --repo SlayerLab/Slayer1B-1.06 --revision <sha> --wyjscie results/1.06

Wyjście w --wyjscie: results.json (schemat Space, bez pól spoza schematu),
results_rozszerzone.json (te same obserwacje + `dodatkowe`: acc, acc_norm, acc_pmi,
BPB poprawnej, wariant cloze, n, SE, CI95, bazy), probki/*.jsonl, podsumowanie.md.
"""

import argparse
import copy
import datetime
import hashlib
import json
import subprocess
import sys
import traceback
from collections import Counter
from pathlib import Path

import numpy as np

KATALOG = Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG))

import metryki as M  # noqa: E402
import zadania as Z  # noqa: E402

PROTOKOLY = {"panel200": "bench50-v0.3.1-panel200", "pelna": "bench50-v0.3.1-fullB"}


def sha256_bajtow(b):
    return hashlib.sha256(b).hexdigest()


def sha256_runnera():
    pliki = sorted(KATALOG.glob("*.py")) + sorted(KATALOG.glob("*.sh"))
    return sha256_bajtow(b"".join(p.read_bytes() for p in pliki))


def zbuduj_model(a):
    # --model_path: katalog z wagami pobranymi wcześniej (np. models/slayer-1.06); repo i rewizja idą do raportu
    weights_path = a.model_path or a.repo
    if a.model == "slayer":
        import slayer_lm
        lm = slayer_lm.SlayerLM(pretrained=weights_path, dtype="float32", batch_size=a.batch, device=a.device)
    else:
        from lm_eval.models.huggingface import HFLM
        lm = HFLM(pretrained=weights_path, revision=None if a.model_path else a.revision,
                  dtype="float32", batch_size=a.batch, device=a.device, trust_remote_code=a.trust_remote_code,
                  max_length=a.max_length)
    return lm, a.repo or Path(a.model_path).resolve().name, a.revision


def licznik_tokenow(lm):
    """Liczba tokenów tekstu w tokenizerze ocenianego modelu (do token ppl i logprob na token)."""
    if hasattr(lm, "m"):
        return lambda t: len(lm.m.encode(t))
    return lambda t: len(lm.tok_encode(t))


def opis_sprzetu(device):
    import torch
    if device.startswith("cuda") and torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    return device


def sha_pliku(sciezka):
    h = hashlib.sha256()
    with open(sciezka, "rb") as f:
        for blok in iter(lambda: f.read(1 << 24), b""):
            h.update(blok)
    return h.hexdigest()


def sha_wag(repo, revision, model_path=None):
    """SHA-256 pliku wag z katalogu modelu albo lokalnego cache HF; None, gdy się nie da (np. wagi w kilku plikach)."""
    if model_path:
        pliki = sorted(Path(model_path).glob("*.safetensors")) or sorted(Path(model_path).glob("pytorch_model*.bin"))
        return sha_pliku(pliki[0]) if len(pliki) == 1 else None
    try:
        from huggingface_hub import hf_hub_download
        for nazwa in ("model.safetensors", "pytorch_model.bin"):
            try:
                sciezka = hf_hub_download(repo, nazwa, revision=revision, local_files_only=True)
            except Exception:
                continue
            return sha_pliku(sciezka)
    except Exception:
        pass
    return None


def zbuduj_zadania(cfgs):
    """Obiekty zadań lm-eval z konfiguracji-słowników.

    lm-eval 0.4.9.1 gubi klucz `task` przy ładowaniu słownika (task_name = None i tabela
    wyników się wywraca), więc nazwę wpisujemy z powrotem w obiekt.
    """
    from lm_eval.tasks import TaskManager, get_task_dict
    tm, wynik = TaskManager(), []
    for cfg in cfgs:
        if (cfg.get("metadata") or {}).get("klasa") == "squadv2":  # legacy task class, built directly
            zad = Z.squad2_klasa(cfg)()
        else:
            zad = list(get_task_dict([copy.deepcopy(cfg)], tm).values())[0]
        zad.config.task = cfg["task"]
        wynik.append(zad)
    return wynik


def z_pmi(cfg):
    """Whether lm-eval logged unconditional logliks (second half of filtered_resps) for this config.

    GOTCHA: BLiMP scores `acc` only; reading its two choices as one choice + PMI gave acc 1.000.
    """
    return any(m["metric"] == "acc_mutual_info" for m in cfg.get("metric_list", []))


def wybor_probki(zad, meta, tryb, czlonek=None, n=None, wykluczone=()):
    """(indeksy albo None = całość, n_population, source_ids wybranych); `n` = przydział podtestu grupy.
    `wykluczone`: indeksy dokumentów banku demonstracji z tego samego splitu (T24), poza populacją i oceną."""
    docs = list(zad.eval_docs)
    pole = meta.get("pole_id")
    ids = [d.get(pole, i) if pole else i for i, d in enumerate(docs)]
    wykluczone = set(wykluczone)
    kandydaci = [i for i in range(len(docs)) if i not in wykluczone]
    if meta.get("probkowanie") is False and tryb.isdigit():
        # unsampled task (WikiText-2) cut to its first documents: a load test, not a panel
        idx = kandydaci[:int(tryb)]
        return idx, len(kandydaci), [ids[i] for i in idx]
    if tryb == "pelna" or meta.get("probkowanie") is False:
        return (kandydaci if wykluczone else None), len(kandydaci), [ids[i] for i in kandydaci]
    if n is None:
        n = 200 if tryb == "panel200" else int(tryb)
    idx = [kandydaci[j] for j in M.ranking_panel(meta["benchmark_id"], czlonek or meta["task"],
                                                  [ids[i] for i in kandydaci], n)]
    return idx, len(kandydaci), [ids[i] for i in idx]


# --- (c): groups, demonstrations, context limit, generation and corpus metrics ---

LIMIT_KONTEKSTU = 4096  # METODOLOGIA "Ustawienia przebiegu centralnego": longer inputs are rejected, never truncated
BUDZET_GEN = 256  # same section: default generation budget (HFLM max_gen_toks)


def czlonek(cfg):
    """Podtest configu (grupy i zadania z YAML-a lm-eval), None dla configów pisanych ręcznie."""
    return (cfg.get("metadata") or {}).get("czlonek")


def rodzaj(meta):
    """`gen` (T30, T31) liczy się jak `proba`: metryka per pytanie z lm-eval."""
    return "proba" if meta["rodzaj"] == "gen" else meta["rodzaj"]


def metryka(meta):
    return meta.get("klucz", "acc")


def przydzialy(space, meta, tryb):
    """{podtest: n} grupy: panel200 według metryki.przydzial_grupy, liczba = tyle na podtest; {} = jak dla jednego zadania."""
    if len(space) == 1 or tryb == "pelna":
        return {}
    if tryb == "panel200":
        return M.przydzial_grupy({czlonek(c): len(z.eval_docs) for c, z in space}, 200)
    return {czlonek(c): int(tryb) for c, _ in space}


def uzyj_banku(zad):
    """Bank przykładów (METODOLOGIA „Przykłady few-shot”) dla każdego zadania z demonstracjami, także z tego samego splitu co test (Belebele T24, jedyny
    split). Zostają tylko demonstracje źródłowe (BBH, stała lista w YAML-u)."""
    cfg = zad.config
    fs = cfg.fewshot_config or {}  # GOTCHA: słownik w 0.4.9.1, dataclass FewshotConfig w 0.4.13
    if not (cfg.num_fewshot or 0) or (fs.get("samples") if isinstance(fs, dict) else fs.samples) is not None:
        return False
    return (cfg.fewshot_split or cfg.training_split) is not None


def demonstracje_z_testu(zad):
    return (zad.config.fewshot_split or zad.config.training_split) == zad.config.test_split


def ustaw_bank(zad, meta, czl, idx):
    """Demonstracje: pierwsze dokumenty splitu few-shot w kolejności M.ranking_banku, bez tych, których prompt
    równa się promptowi ocenianego dokumentu (`idx`, None = cały test); zawsze te same, w tej kolejności. Zwraca id.

    Split few-shot = test (T24) przy pełnym splicie: wołane przed próbą z `idx` None, bank bierze pierwsze dokumenty
    całego splitu, a `zad.bank_testu` (ich indeksy) wypada z populacji i oceny (wybor_probki `wykluczone`)."""
    k = zad.config.num_fewshot
    docs = list(zad.fewshot_docs())
    oceniane = list(zad.eval_docs)
    z_testu = demonstracje_z_testu(zad)
    if z_testu and docs != oceniane:
        raise ValueError(f"{czl}: dokumenty few-shot różne od testowych przy tym samym splicie")
    if idx is None:
        zakazane = set() if z_testu else {str(zad.doc_to_text(d)) for d in oceniane}
    else:
        zakazane = {str(zad.doc_to_text(oceniane[i])) for i in idx}
    ids = [M.sha256_tekstu(json.dumps(d, sort_keys=True, ensure_ascii=False, default=str)) for d in docs]
    bank = []
    for i in M.ranking_banku(meta["benchmark_id"], czl or meta["task"], ids):
        if len(bank) == k:
            break
        if str(zad.doc_to_text(docs[i])) not in zakazane:
            bank.append(i)
    if len(bank) < k:
        raise ValueError(f"bank demonstracji {czl}: {len(bank)} z {k}")
    zad.sampler = sampler_banku([docs[i] for i in bank], zad)
    zad.bank_testu = bank if z_testu and idx is None else []
    return [ids[i] for i in bank]


def sampler_banku(docs, zad):
    """Sampler zwracający pierwsze `n` dokumentów `docs` w tej kolejności, w lm-eval 0.4.9.1 i 0.4.13.

    GOTCHA: 0.4.9.1 bierze (docs, task, rnd=Random), 0.4.13 (środowisko `new`) (df, *, rnd=int|None). Przy splicie
    few-shot = test 0.4.9.1 prosi o n + 1 i odrzuca oceniany dokument; bank nie ma ocenianych, więc zostaje n."""
    import inspect
    from lm_eval.api.samplers import ContextSampler, FirstNSampler

    class Bank(FirstNSampler):
        def sample(self, n, *args, **kwargs):
            return list(self.docs if hasattr(self, "docs") else self.fewshot_docs())[:n]

    if "task" in inspect.signature(ContextSampler.__init__).parameters:
        return Bank(docs, zad, rnd=zad.fewshot_rnd)
    return Bank(list(docs), rnd=None)


def licznik_wejscia(lm, licz_tokeny):
    """Tokeny tekstu żądania z jednym wiodącym BOS (METODOLOGIA, „Wejście”): tokenizer modelu i BOS, gdy tokenizer sam go nie
    dał. Model bez BOS dostaje limit ostrzejszy najwyżej o jeden token."""
    bos = getattr(lm, "prefix_token_id", None)
    if bos is None or not hasattr(lm, "tok_encode"):
        return lambda t: licz_tokeny(t) + 1

    def licz(t):
        ids = list(lm.tok_encode(t))
        return len(ids) + (0 if ids[:1] == [bos] else 1)
    return licz


def ogranicz_kontekst(zad, licz_tokeny, limit, licz_wejscie):
    """METODOLOGIA, „Wejście”: prompt z BOS (`licz_wejscie`) + budżet ≤ limit; budżet MC = najdłuższa kontynuacja
    (`licz_tokeny`, bez BOS). Demonstracje zdejmowane od końca; pytania, opcje i odniesienia nie są cięte, więc prompt
    za długi bez demonstracji (także MC 0-shot) kończy zadanie błędem."""
    oryginal = zad.fewshot_context
    budzet_gen = (zad.config.generation_kwargs or {}).get("max_gen_toks", BUDZET_GEN)

    def budzet(doc):
        if zad.OUTPUT_TYPE == "generate_until":
            return budzet_gen
        cele = zad.doc_to_choice(doc) if zad.OUTPUT_TYPE == "multiple_choice" else [zad.doc_to_target(doc)]
        return max(licz_tokeny(zad.config.target_delimiter + str(c)) for c in cele)

    def fewshot_context(doc, num_fewshot, **kw):
        for k in range(num_fewshot, -1, -1):
            ctx = oryginal(doc, num_fewshot=k, **kw)
            if max(licz_wejscie(c) for c in (ctx if isinstance(ctx, list) else [ctx])) + budzet(doc) <= limit:
                return ctx
        raise ValueError(f"{zad.config.task}: prompt bez demonstracji + budżet > {limit} tokenów")

    zad.fewshot_context = fewshot_context


def wartosc_odpowiedzi(zad, meta, doc, tekst):
    """Metryka testu dla odpowiedzi `tekst` podanej zamiast generacji: filtry zadania, potem jego process_results."""
    resps = [[tekst]]
    for zespol in getattr(zad, "_filters", []):
        if zespol.name == meta.get("filtr", "none"):
            for f in zespol.filters:
                resps = list(f().apply(resps, [doc]))
    odp = resps[0]
    if meta.get("strip"):
        return float(str(odp).strip() == str(zad.doc_to_target(doc)))
    reszta = [(0.0, False)] if meta["task"] == "squadv2" else []  # legacy SQuAD2: second request = loglik
    return float(zad.process_results(doc, [odp] + reszta)[metryka(meta)])


def _pierwszy(cel):
    return str(cel[0] if isinstance(cel, list) and cel else cel)


def bazy_proby(zad, meta, docs):
    """(bazy w schemacie Space, szczegóły) wg wiersza typu w METODOLOGII: gen/ciagla = wyższa z pustej odpowiedzi
    i najczęstszej złotej, ifeval = pusta, cloze = udział najczęstszego słowa docelowego, masa = jednakowe logliki,
    wybor_losowy = średnia po losowej opcji, mcc = 0."""
    baza = meta.get("baza", "gen")
    n = len(docs)
    bazy = {"chance_value": 0.0, "majority_value": None, "majority_prediction_share": None,
            "constant_prediction": None}
    szczegoly = {"baza": baza}
    sr = lambda v: sum(v) / len(v)
    if baza in ("gen", "pusta"):
        szczegoly["pusta"] = sr([wartosc_odpowiedzi(zad, meta, d, "") for d in docs])
        stale = [szczegoly["pusta"]]
        if baza == "gen":
            tekst = Counter(_pierwszy(zad.doc_to_target(d)) for d in docs).most_common(1)[0][0]
            v = sr([wartosc_odpowiedzi(zad, meta, d, tekst) for d in docs])
            szczegoly["najczestsza_zlota"] = {"tekst": tekst[:80], "value": v}
            stale.append(v)
        bazy["majority_value"] = max(stale)
    elif baza == "cloze":
        cele = Counter(str(zad.doc_to_target(d)).strip() for d in docs)
        bazy["majority_value"] = cele.most_common(1)[0][1] / n
    elif baza == "masa":
        bazy["chance_value"] = sr([zad.process_results(d, [(0.0, False)] * len(zad.doc_to_choice(d)))[metryka(meta)]
                                   for d in docs])
    elif baza == "wybor_losowy":
        def losowa(d):
            k = len(zad.doc_to_choice(d))
            return sr([zad.process_results(d, [(0.0 if j == i else -1e9, False) for j in range(k)])[metryka(meta)]
                       for i in range(k)])
        bazy["chance_value"] = sr([losowa(d) for d in docs])
    elif baza == "mcc":
        bazy["majority_value"] = 0.0
    return bazy, szczegoly


def bazy_f1_korpus(zlote, k, funkcja, seed=M.SEED, losowania=200):
    """f1-korpus: oczekiwane F1 predykcji klas z równymi szansami (średnia z `losowania`) i F1 najlepszej stałej klasy."""
    rng = np.random.default_rng(seed)
    losowa = float(np.mean([funkcja(zlote, list(rng.integers(0, k, len(zlote)))) for _ in range(losowania)]))
    stala = max(funkcja(zlote, [c] * len(zlote)) for c in range(k))
    return {"chance_value": losowa, "majority_value": stala, "majority_prediction_share": None,
            "constant_prediction": None}


def funkcja_korpusowa(cfg, nazwa):
    """Agregacja metryki korpusowej z configu (f1 forka OpenPL: binarne albo makro), na listach (złote, pred)."""
    if nazwa == "mcc":
        return M.mcc
    for m in cfg.get("metric_list") or []:
        if getattr(m["metric"], "__name__", m["metric"]) == nazwa and callable(m.get("aggregation")):
            agg = m["aggregation"]
            return lambda z, p: float(agg(list(zip(p, z))))  # fork: items = (prediction, reference)
    return lambda z, p: M.f1_korpus(z, p, "macro" if meta_srednia_makro(cfg) else "binary")


def meta_srednia_makro(cfg):
    return any("macro" in getattr(m.get("aggregation"), "__name__", "") for m in cfg.get("metric_list") or [])


def podsumuj_wariant(meta, czlonkowie):
    """Metryki jednego wariantu. `czlonkowie` = [(podtest, cfg, zad, próbki)]; więcej niż jeden = grupa, średnia
    podtestów z wagami populacji (MMLU, MATH, BBH) i bazy złożone tymi samymi wagami."""
    wagi = {n: len(z.eval_docs) for n, _, z, _ in czlonkowie}
    klasy_stale = meta.get("klasy_stale", False)
    if rodzaj(meta) == "mc":
        klucz = meta.get("klucz", "acc")
        korpus = klucz not in ("acc", "acc_norm")  # f1 of the OpenPL fork (T25, T27, T28)
        if len(czlonkowie) == 1:
            _, cfg, zad, probki = czlonkowie[0]
            wynik = M.podsumuj_mc(probki, klasy_stale, z_pmi=z_pmi(cfg), klucz="acc" if korpus else klucz)
            if korpus:
                oceny = [M.oceny_mc(p, z_pmi(cfg)) for p in probki]
                zlote, pred = [o["gold"] for o in oceny], [o["pred"] for o in oceny]
                f = funkcja_korpusowa(cfg, klucz)
                wynik["glowna"] = {**M.korpusowa_z_niepewnoscia(zlote, pred, f), "metryka": klucz}
                wynik["bazy"] = bazy_f1_korpus(zlote, max(o["k"] for o in oceny), f)
            return wynik
        oceny = {n: [M.oceny_mc(p, z_pmi(cfg)) for p in probki] for n, cfg, _, probki in czlonkowie}
        wynik = {m: M.warstwy({n: [o[m] for o in oc] for n, oc in oceny.items()}, wagi)
                 for m in ("acc", "acc_norm", "acc_pmi", "bpb_poprawnej")
                 if all(m in o for oc in oceny.values() for o in oc)}
        wynik["bazy"] = M.wazona_baza({n: M.bazy_mc(oc, klasy_stale, klucz) for n, oc in oceny.items()}, wagi)
        wszystkie = [o for oc in oceny.values() for o in oc]
        wynik["udzial_najczestszej_predykcji"] = (Counter(o[f"pred_{klucz}"] for o in wszystkie).most_common(1)[0][1]
                                                  / len(wszystkie))
        return wynik
    nazwa, filtr = metryka(meta), meta.get("filtr", "none")
    wartosci, bazy, szczegoly, predykcje, wynik = {}, {}, {}, [], {}
    for n, cfg, zad, probki in czlonkowie:
        wybrane = [s for s in probki if s.get("filter", "none") == filtr]
        if rodzaj(meta) == "korpus":
            pary = [s[nazwa] for s in wybrane]  # lm-eval MC: (gold, pred)
            f = funkcja_korpusowa(cfg, nazwa)
            wynik["glowna"] = {**M.korpusowa_z_niepewnoscia([g for g, _ in pary], [p for _, p in pary], f),
                               "metryka": nazwa}
            predykcje += [p for _, p in pary]
        elif meta.get("strip"):  # BBH: answer stripped before exact match; the source-literal value is a diagnostic
            wartosci[n] = [float(str(s["filtered_resps"][0]).strip() == str(s["target"])) for s in wybrane]
            wynik.setdefault("zrodlowa_doslowna", {})[n] = sum(float(s[nazwa]) for s in wybrane) / len(wybrane)
        else:
            wartosci[n] = [float(s[nazwa]) for s in wybrane]
        if zad.OUTPUT_TYPE == "generate_until":
            predykcje += [str(s["filtered_resps"][0]).strip() for s in wybrane]
        bazy[n], szczegoly[n] = bazy_proby(zad, meta, [s["doc"] for s in wybrane])
        if meta.get("podzbior"):  # SQuAD2: b and the control on HasAns, the full value next to it
            maska = [s[meta["podzbior"]] == 1 for s in wybrane]
            wynik["podzbior"] = {"nazwa": meta["podzbior"],
                                 "glowna": M.srednia_z_niepewnoscia([v for v, m in zip(wartosci[n], maska) if m]),
                                 "bazy": bazy_proby(zad, meta, [s["doc"] for s, m in zip(wybrane, maska) if m])[0]}
    if "glowna" not in wynik:
        glowna = (M.srednia_z_niepewnoscia(next(iter(wartosci.values()))) if len(wartosci) == 1
                  else M.warstwy(wartosci, wagi))
        wynik["glowna"] = {**glowna, "metryka": nazwa}
    wynik["bazy"] = next(iter(bazy.values())) if len(bazy) == 1 else M.wazona_baza(bazy, wagi)
    wynik["bazy_szczegoly"] = szczegoly
    wynik["udzial_najczestszej_predykcji"] = (Counter(predykcje).most_common(1)[0][1] / len(predykcje)
                                              if predykcje else None)
    return wynik


def ocen_zadanie(lm, task_id, dane, probka, licz_tokeny, wyj, runner, model_id, protocol_id):
    """Jedno zadanie ZADANIA na modelu `lm`: (obserwacja, wpis rozszerzony, bazy, sha256 próbek); wyjątek = brak wyniku."""
    from lm_eval import simple_evaluate
    import trace_pytan as T

    meta = Z.ZADANIA[task_id]
    warianty = Z.konfiguracje(task_id, dane)
    obiekty = zbuduj_zadania([c for _, c in warianty])
    po_wariancie = {}
    for (wariant, cfg), zad in zip(warianty, obiekty):
        po_wariancie.setdefault(wariant, []).append((cfg, zad))
    space = po_wariancie["space"]
    n_czl = przydzialy(space, meta, probka)
    demonstracje, przed_proba = {}, set()
    # Bank z testu (T24) przy pełnym splicie: przed próbą, jego dokumenty nie wchodzą do oceny. Przy panelu
    # najpierw próba z całego splitu, bank z dokumentów spoza niej (METODOLOGIA „Przykłady few-shot”, punkt 4).
    if probka == "pelna" or meta.get("probkowanie") is False:
        for lista in po_wariancie.values():
            for cfg, zad in lista:
                if uzyj_banku(zad) and demonstracje_z_testu(zad):
                    demonstracje[czlonek(cfg) or meta["task"]] = ustaw_bank(zad, meta, czlonek(cfg), None)
                    przed_proba.add(id(zad))
    wybory = [wybor_probki(zad, meta, probka, czlonek(cfg), n_czl.get(czlonek(cfg)), getattr(zad, "bank_testu", ()))
              for cfg, zad in space]
    limit = min(LIMIT_KONTEKSTU, getattr(lm, "max_length", None) or LIMIT_KONTEKSTU)
    licz_wejscie = licznik_wejscia(lm, licz_tokeny)
    samples = {}
    for lista in po_wariancie.values():
        for (cfg, zad), (idx, _, _) in zip(lista, wybory):
            if idx is not None:
                samples[cfg["task"]] = idx
            if uzyj_banku(zad) and id(zad) not in przed_proba:
                demonstracje[czlonek(cfg) or meta["task"]] = ustaw_bank(zad, meta, czlonek(cfg), idx)
            if zad.OUTPUT_TYPE != "loglikelihood_rolling":  # rolling: okna modelu, bez promptu do odrzucenia
                ogranicz_kontekst(zad, licz_tokeny, limit, licz_wejscie)
    wynik = simple_evaluate(model=lm, tasks=obiekty, samples=samples or None, log_samples=True,
                            bootstrap_iters=0, random_seed=0, numpy_random_seed=1234,
                            torch_random_seed=1234, fewshot_random_seed=1234)

    dodatkowe, digest = {}, hashlib.sha256()
    for wariant, lista in po_wariancie.items():
        czlonkowie = []
        for cfg, zad in lista:
            probki = wynik["samples"][cfg["task"]]
            if getattr(zad, "multiple_input", 0):  # WinoGrande, WSC273: gold index comes from doc_to_text
                for s in probki:
                    s["gold"] = int(zad.doc_to_text(s["doc"]))
            nazwa = f"{task_id}_{wariant}" + (f"_{czlonek(cfg)}" if len(lista) > 1 else "")
            tresc = "".join(json.dumps(s, ensure_ascii=False, default=str) + "\n" for s in probki).encode()
            (wyj / "probki" / f"{nazwa}.jsonl").write_bytes(tresc)
            digest.update(tresc)
            czlonkowie.append((czlonek(cfg) or meta["task"], cfg, zad, probki))
        if meta["rodzaj"] == "rolling":
            _, cfg, _, probki = czlonkowie[0]
            dodatkowe[wariant] = M.podsumuj_rolling(probki, cfg["process_results"], licz_tokeny)
            continue
        dodatkowe[wariant] = podsumuj_wariant(meta, czlonkowie)
        if meta.get("trace") and len(czlonkowie) == 1:
            probki = czlonkowie[0][3]
            pole = meta.get("pole_id")
            wiersze = [T.trace_pytania(s, licz_tokeny, id_pytania=s["doc"].get(pole) if pole else s["doc_id"])
                       for s in probki]
            (wyj / "trace" / f"{task_id}_{wariant}.jsonl").write_text(
                "".join(json.dumps(w, ensure_ascii=False) + "\n" for w in wiersze))
            dodatkowe[wariant]["rozklad_wyborow"] = T.rozklad_wyborow(wiersze)
    d = dodatkowe["space"]
    if demonstracje:
        d["demonstracje"] = demonstracje
    if meta["rodzaj"] == "rolling":
        glowna, bazy = d["byte_perplexity"], None
    else:
        glowna, bazy = d.get("glowna") or d[meta.get("klucz", "acc")], d["bazy"]
    n_pop = sum(w[1] for w in wybory)
    wybrane_ids = [i for (cfg, _), w in zip(space, wybory)
                   for i in (w[2] if len(space) == 1 else [f"{czlonek(cfg)}|{x}" for x in w[2]])]
    digests = {"source_id": M.sha256_tekstu("\n".join(map(str, wybrane_ids))),
               "results": digest.hexdigest(), "runner": runner}
    obs = M.obserwacja(task_id, meta, model_id, protocol_id, glowna, bazy, n_pop, len(wybrane_ids), digests)
    roz = {**obs, "dodatkowe": dodatkowe, "zrodlo_danych": {"repo": meta["repo"], "rewizja": meta["rewizja"],
                                                             "tryb": dane}}
    return obs, roz, bazy, digests["results"]


def zapisz_historie(sciezka, wiersz, nowy):
    """Wiersz w formacie scores-history.csv: nowy plik z nagłówkiem albo dopisanie do istniejącego."""
    import csv
    istnieje = sciezka.exists() and not nowy
    if istnieje:
        with open(sciezka, newline="", encoding="utf-8") as f:
            naglowek = next(csv.reader(f))
        if naglowek != M.KOLUMNY_HISTORII:
            raise SystemExit(f"{sciezka}: nagłówek inny niż scores-history.csv: {naglowek}")
    with open(sciezka, "a" if istnieje else "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=M.KOLUMNY_HISTORII)
        if not istnieje:
            w.writeheader()
        w.writerow(wiersz)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", choices=["hf", "slayer"], default="hf")
    p.add_argument("--repo")
    p.add_argument("--revision")
    p.add_argument("--ckpt")
    p.add_argument("--zadania", default=",".join(Z.PIATKA))
    p.add_argument("--dane", choices=["hf", "lokalne"], default="hf")
    p.add_argument("--probka", default="panel200", help="panel200 | pelna | liczba dokumentów")
    p.add_argument("--wyjscie", required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--batch", default="1")
    p.add_argument("--trust_remote_code", action="store_true")
    p.add_argument("--max_length", type=int, help="token window of the model (rolling perplexity: window size); "
                   "default from the model config, which for 128k-262k context models does not fit a 24 GB GPU in float32")
    p.add_argument("--model_path", help="lokalny katalog wag zamiast pobierania z HF; przy --model slayer wymagany")
    p.add_argument("--etykieta", help="kolumna model w scores-history.csv, np. 1.06")
    p.add_argument("--step", type=int)
    p.add_argument("--tokens", type=int, help="domyślnie step * 2^20, jak w scores-history.csv")
    p.add_argument("--eval_gpu", default="", help="kolumna eval_gpu (oznaczenie maszyny w konwencji Space)")
    p.add_argument("--historia_csv", help="istniejący CSV w formacie scores-history.csv, do którego dopisać wiersz")
    a = p.parse_args()
    if a.model == "slayer" and not a.model_path:
        p.error("--model slayer requires --model_path (local weights directory, e.g. models/slayer-1.06); --repo and --revision only go to the report")

    wyj = Path(a.wyjscie)
    for podkatalog in ("probki", "trace"):
        (wyj / podkatalog).mkdir(parents=True, exist_ok=True)
    lm, model_id, rewizja = zbuduj_model(a)
    licz_tokeny = licznik_tokenow(lm)
    sprzet = opis_sprzetu(a.device)
    protocol_id = PROTOKOLY.get(a.probka, PROTOKOLY["panel200"])
    runner = sha256_runnera()
    obserwacje, rozszerzone, zadania_space, zrodla, bazy_wszystkie, nieudane = [], [], [], [], {}, []

    for task_id in a.zadania.split(","):
        meta = Z.ZADANIA[task_id]
        zadania_space.append({"task_id": task_id, "task": meta["task"], "family": meta["family"],
                              "language": meta["language"], "split": meta["split"]})
        try:
            obs, roz, bazy, digest = ocen_zadanie(lm, task_id, a.dane, a.probka, licz_tokeny, wyj, runner,
                                                  model_id, protocol_id)
        except Exception as e:  # zadanie, którego nie dało się uruchomić, zostaje w raporcie ze stanem
            stan = "blocked_access" if "huggingface" in repr(e).lower() or "connect" in repr(e).lower() else "failed"
            obs = M.obserwacja(task_id, meta, model_id, protocol_id, {"n": 0}, None, None, None, {},
                               state=stan, reason=f"{type(e).__name__}: {e}")
            obserwacje.append(obs)
            rozszerzone.append({**obs, "dodatkowe": None})
            print(f"[{task_id}] {stan}: {type(e).__name__}: {str(e)[:200]}", file=sys.stderr)
            traceback.print_exc()
            nieudane.append(task_id)
            continue
        zrodla.append(digest)
        bazy_wszystkie[task_id] = bazy
        obserwacje.append(obs)
        rozszerzone.append(roz)

    teraz = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"niezalezny-{model_id.replace('/', '_')}-{(rewizja or 'lokalny')[:8]}-{teraz}"
    commit = subprocess.run(["git", "-C", str(KATALOG), "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    wagi_sha = sha_wag(a.repo, rewizja, a.model_path) if a.model in ("hf", "slayer") else sha_pliku(a.ckpt)
    wyniki = {
        "schema_version": 2, "protocol_id": protocol_id, "run_id": run_id,
        "models": [{"model_id": model_id, "repo": a.repo or model_id, "revision": rewizja,
                    "weights_sha256": wagi_sha if a.model in ("hf", "slayer") else None}],
        "tasks": zadania_space, "observations": obserwacje, "contrasts": [],
        "provenance": {"inventory_commit": commit, "kind": "measurement",
                       "sources": [{"run_id": run_id, "results_sha256": s} for s in zrodla]
                       or [{"run_id": run_id, "results_sha256": M.sha256_tekstu("")}],
                       "qualification_sha256": M.sha256_tekstu(freeze),
                       "contamination_sha256": M.sha256_tekstu("unscanned"),
                       "references_sha256": M.sha256_tekstu(json.dumps(bazy_wszystkie, sort_keys=True))},
    }
    bledy = M.bledy_schematu(wyniki)
    (wyj / "results.json").write_text(json.dumps(wyniki, ensure_ascii=False, indent=1))
    (wyj / "results_rozszerzone.json").write_text(
        json.dumps({**wyniki, "observations": rozszerzone, "ewaluator": "niezależny (slayer_eval)",
                    "lm_eval": __import__("lm_eval").__version__, "dane": a.dane, "probka": a.probka,
                    "eval_gpu": a.eval_gpu, "sprzet": sprzet, "max_length": getattr(lm, "max_length", None)},
                   ensure_ascii=False, indent=1))
    (wyj / "podsumowanie.md").write_text(M.tabela_md(rozszerzone))
    tokens = a.tokens if a.tokens is not None else (a.step * 2 ** 20 if a.step is not None else None)
    wiersz = M.wiersz_historii(rozszerzone, a.etykieta or model_id, a.step, tokens, wagi_sha, a.eval_gpu or sprzet)
    zapisz_historie(wyj / "scores-history-wiersz.csv", wiersz, nowy=True)
    if a.historia_csv:
        zapisz_historie(Path(a.historia_csv), wiersz, nowy=False)
    print((wyj / "podsumowanie.md").read_text())
    if bledy:
        print("NIEZGODNE ZE SCHEMATEM:\n" + "\n".join(bledy), file=sys.stderr)
        sys.exit(2)
    if nieudane:
        print(f"ZADANIA BEZ WYNIKU: {','.join(nieudane)}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
