"""Jednorazowe pobranie do lokalnego cache HF wszystkich zbiorów, których używa slayer_eval.

  .venv-eval/bin/python slayer_eval/pobierz_zbiory.py

Dwie grupy:
- pipeline: dokładnie te argumenty `load_dataset`, które budują konfiguracje w zadania.py
  (repo i rewizje przypięte jak w tasks_50.json Space, parquet dla repo z loading scriptem);
- kontrola i domyślne lm-eval: repo/konfiguracje odczytane z YAML-i zadań lm-eval 0.4.9.1
  w tym venv (arc_easy, mmlu — 57 przedmiotów, belebele_pol_Latn oraz domyślne ścieżki
  zadań z pipeline'u). Repo z loading scriptem (bigbio/pubmed_qa, social_i_qa) pobieramy tylko
  z gałęzi refs/convert/parquet: samego skryptu nie wykonujemy (trust_remote_code).

Na koniec lista OK/BŁĄD i kod wyjścia 1, jeśli cokolwiek się nie pobrało. Potem ewaluacja
działa bez sieci: HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 (w ewaluuj_slayer.sh: OFFLINE=1).
"""

import re
import sys
import traceback
from pathlib import Path

KATALOG = Path(__file__).resolve().parent
sys.path.insert(0, str(KATALOG))

import zadania as Z  # noqa: E402

PARQUET = "refs/convert/parquet"
REPO_ZE_SKRYPTEM = {"bigbio/pubmed_qa", "social_i_qa", "allenai/social_i_qa"}


def pole_yaml(tekst, klucz):
    m = re.search(rf"^[\"']?{klucz}[\"']?:\s*(.+?)\s*$", tekst, re.M)  # MMLU ma klucze w cudzysłowie
    if not m or m.group(1) in ("null", "None", ""):
        return None
    return m.group(1).strip("'\"")


def z_yaml(wzgledna, rewizja=None):
    """(repo, konfiguracja) z YAML-a zadania lm-eval; `include` czytany z tego samego katalogu."""
    plik = Z.ZADANIA_LM_EVAL / wzgledna
    tekst = plik.read_text()
    repo, nazwa = pole_yaml(tekst, "dataset_path"), pole_yaml(tekst, "dataset_name")
    inc = pole_yaml(tekst, "include")
    if inc and (repo is None or nazwa is None):
        baza = (plik.parent / inc).read_text()
        repo = repo or pole_yaml(baza, "dataset_path")
        nazwa = nazwa or pole_yaml(baza, "dataset_name")
    return repo, nazwa


def kw_load(repo, nazwa=None, rewizja=None):
    if repo in REPO_ZE_SKRYPTEM:
        rewizja = PARQUET
    kw = {"path": repo, "name": nazwa}
    if rewizja:
        kw["revision"] = rewizja
    return kw


def lista_pobran():
    pobrania = []
    # 1) pipeline: te same argumenty co konfiguracje zadań (źródło "hf")
    for task_id, meta in Z.ZADANIA.items():
        cfg = Z.konfiguracje(task_id, "hf")[0][1]
        kw = {"path": cfg["dataset_path"], "name": cfg["dataset_name"], **cfg["dataset_kwargs"]}
        pobrania.append((f"{task_id} {meta['task']} (pipeline)", kw))
    # 2) kontrola: zadania lm-eval, repo i konfiguracje z YAML-i
    arc_rew = Z.ZADANIA["T02"]["rewizja"]
    repo, nazwa = z_yaml("arc/arc_easy.yaml")
    pobrania.append(("arc_easy (lm-eval, rewizja ai2_arc z Space)", kw_load(repo, nazwa, arc_rew)))
    repo, nazwa = z_yaml("belebele/belebele_pol_Latn.yaml")
    pobrania.append(("belebele_pol_Latn (lm-eval)", kw_load(repo, nazwa)))
    szablon = (Z.ZADANIA_LM_EVAL / "mmlu/default/_default_template_yaml").read_text()
    mmlu_repo = pole_yaml(szablon, "dataset_path")
    for plik in sorted((Z.ZADANIA_LM_EVAL / "mmlu/default").glob("mmlu_*.yaml")):
        przedmiot = pole_yaml(plik.read_text(), "dataset_name")
        if przedmiot:
            pobrania.append((f"mmlu {przedmiot} (lm-eval)", kw_load(mmlu_repo, przedmiot)))
    # 3) domyślne ścieżki zadań lm-eval odpowiadających pipeline'owi (gdyby liczyć je nazwą zadania)
    for wzgl in ("arc/arc_challenge.yaml", "wikitext/wikitext.yaml", "medmcqa/medmcqa.yaml",
                 "pubmedqa/pubmedqa.yaml", "siqa/siqa.yaml"):
        repo, nazwa = z_yaml(wzgl)
        pobrania.append((f"{wzgl} (lm-eval domyślne)", kw_load(repo, nazwa)))
    return pobrania


def main():
    import datasets
    from datasets import load_dataset

    print(f"cache: {datasets.config.HF_DATASETS_CACHE}", flush=True)
    if "--lista" in sys.argv:  # tylko wypisz, co byłoby pobrane (bez sieci)
        for etykieta, kw in lista_pobran():
            print(f"{etykieta}: {kw}")
        return
    wyniki = []
    for etykieta, kw in lista_pobran():
        print(f"\n== {etykieta}: {kw}", flush=True)
        try:
            ds = load_dataset(**kw)
            rozmiary = ", ".join(f"{s}={len(ds[s])}" for s in ds)
            wyniki.append(("OK", etykieta, rozmiary))
        except Exception as e:
            traceback.print_exc(limit=2)
            wyniki.append(("BŁĄD", etykieta, f"{type(e).__name__}: {str(e)[:160]}"))

    print("\n=== PODSUMOWANIE ===")
    for stan, etykieta, opis in wyniki:
        print(f"{stan:5} {etykieta} — {opis}")
    bledy = sum(s != "OK" for s, _, _ in wyniki)
    print(f"\nOK: {len(wyniki) - bledy}, BŁĄD: {bledy}")
    print("Dalej bez sieci: HF_DATASETS_OFFLINE=1 HF_HUB_OFFLINE=1 (albo OFFLINE=1 slayer_eval/ewaluuj_slayer.sh …)")
    sys.exit(1 if bledy else 0)


if __name__ == "__main__":
    main()
