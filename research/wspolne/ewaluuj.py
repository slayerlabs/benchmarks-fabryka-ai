"""Niezależna ewaluacja checkpointu Slayera 1B: lm-eval + metryki dodatkowe, wynik w formacie Space.

Przykłady:
  python slayer_eval/ewaluuj.py --model hf --repo SlayerLab/Slayer1B-1.06 --revision <sha> --wyjscie wyniki/1.06

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
from pathlib import Path

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
    from lm_eval.models.huggingface import HFLM
    # --model_path: katalog z wagami pobranymi wcześniej (np. models/slayer1b-106); repo i rewizja idą do raportu
    lm = HFLM(pretrained=a.model_path or a.repo, revision=None if a.model_path else a.revision,
              dtype="float32", batch_size=a.batch, device=a.device, trust_remote_code=a.trust_remote_code)
    return lm, a.repo, a.revision


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
        zad = list(get_task_dict([copy.deepcopy(cfg)], tm).values())[0]
        zad.config.task = cfg["task"]
        wynik.append(zad)
    return wynik


def wybor_probki(zad, meta, tryb):
    """(indeksy albo None = całość, n_population, source_ids wybranych)."""
    docs = list(zad.eval_docs)
    pole = meta.get("pole_id")
    ids = [d.get(pole, i) if pole else i for i, d in enumerate(docs)]
    if tryb == "pelna" or meta.get("probkowanie") is False:
        return None, len(docs), ids
    n = 200 if tryb == "panel200" else int(tryb)
    idx = M.ranking_panel(meta["benchmark_id"], meta["task"], ids, n)
    return idx, len(docs), [ids[i] for i in idx]


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
    p.add_argument("--model", choices=["hf"], default="hf")
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
    p.add_argument("--model_path", help="lokalny katalog wag zamiast pobierania z HF")
    p.add_argument("--etykieta", help="kolumna model w scores-history.csv, np. 1.06")
    p.add_argument("--step", type=int)
    p.add_argument("--tokens", type=int, help="domyślnie step * 2^20, jak w scores-history.csv")
    p.add_argument("--eval_gpu", default="", help="kolumna eval_gpu (oznaczenie maszyny w konwencji Space)")
    p.add_argument("--historia_csv", help="istniejący CSV w formacie scores-history.csv, do którego dopisać wiersz")
    a = p.parse_args()

    from lm_eval import simple_evaluate
    import trace_pytan as T

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
        warianty = Z.konfiguracje(task_id, a.dane)
        try:
            obiekty = zbuduj_zadania([c for _, c in warianty])
            idx, n_pop, wybrane_ids = wybor_probki(obiekty[0], meta, a.probka)
            samples = {c["task"]: idx for _, c in warianty} if idx is not None else None
            wynik = simple_evaluate(model=lm, tasks=obiekty, samples=samples, log_samples=True,
                                    bootstrap_iters=0, random_seed=0, numpy_random_seed=1234,
                                    torch_random_seed=1234, fewshot_random_seed=1234)
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

        dodatkowe, glowna, bazy = {}, None, None
        digest_wynikow = hashlib.sha256()
        for wariant, cfg in warianty:
            probki = wynik["samples"][cfg["task"]]
            plik = wyj / "probki" / f"{task_id}_{wariant}.jsonl"
            tresc = "".join(json.dumps(s, ensure_ascii=False, default=str) + "\n" for s in probki).encode()
            plik.write_bytes(tresc)
            digest_wynikow.update(tresc)
            if meta["rodzaj"] == "rolling":
                pp = M.podsumuj_rolling(probki, cfg["process_results"], licz_tokeny)
                dodatkowe[wariant] = pp
                glowna = pp["byte_perplexity"] if wariant == "space" else glowna
                continue
            klucz = meta.get("klucz", "acc")
            mc = M.podsumuj_mc(probki, meta.get("klasy_stale", False), klucz=klucz)
            dodatkowe[wariant] = mc
            if wariant == "space":
                glowna, bazy = mc[klucz], mc["bazy"]
            if meta.get("trace"):
                pole = meta.get("pole_id")
                wiersze = [T.trace_pytania(s, licz_tokeny, id_pytania=s["doc"].get(pole) if pole else s["doc_id"])
                           for s in probki]
                (wyj / "trace" / f"{task_id}_{wariant}.jsonl").write_text(
                    "".join(json.dumps(w, ensure_ascii=False) + "\n" for w in wiersze))
                mc["rozklad_wyborow"] = T.rozklad_wyborow(wiersze)
        digests = {"source_id": M.sha256_tekstu("\n".join(map(str, wybrane_ids))),
                   "results": digest_wynikow.hexdigest(), "runner": runner}
        zrodla.append(digests["results"])
        bazy_wszystkie[task_id] = bazy
        obs = M.obserwacja(task_id, meta, model_id, protocol_id, glowna, bazy, n_pop,
                           len(wybrane_ids), digests)
        obserwacje.append(obs)
        rozszerzone.append({**obs, "dodatkowe": dodatkowe,
                            "zrodlo_danych": {"repo": meta["repo"], "rewizja": meta["rewizja"], "tryb": a.dane}})

    teraz = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"niezalezny-{model_id.replace('/', '_')}-{(rewizja or 'lokalny')[:8]}-{teraz}"
    commit = subprocess.run(["git", "-C", str(KATALOG), "rev-parse", "HEAD"], capture_output=True,
                            text=True).stdout.strip()
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
    wagi_sha = sha_wag(a.repo, rewizja, a.model_path) if a.model == "hf" else sha_pliku(a.ckpt)
    wyniki = {
        "schema_version": 2, "protocol_id": protocol_id, "run_id": run_id,
        "models": [{"model_id": model_id, "repo": a.repo or model_id, "revision": rewizja,
                    "weights_sha256": wagi_sha if a.model == "hf" else None}],
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
                    "eval_gpu": a.eval_gpu, "sprzet": sprzet},
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
