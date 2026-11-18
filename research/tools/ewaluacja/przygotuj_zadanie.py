"""Przygotowanie jednego testu na CPU (z siecią): pobranie i zmaterializowanie zbiorów do cache HF.

    python przygotuj_zadanie.py T05 <katalog_znacznikow>

Te same argumenty `load_dataset` co konfiguracje w fabryka/research/common/zadania.py (jak pobierz_zbiory.py),
więc późniejsze liczenie z HF_HUB_OFFLINE=1 / HF_DATASETS_OFFLINE=1 trafia w gotowy cache. Wynik: plik
<katalog>/<T>.ok (JSON z rozmiarami splitów i czasem) albo <T>.blad (błąd). Testy z własnym kodem (EWoK) i z
plikami OSF przygotowują się same przy liczeniu: dostają .ok z adnotacją.
"""
import json
import sys
import time
import traceback
from pathlib import Path

_TU = Path(__file__).resolve().parent
FABRYKA_COMMON = (_TU.parents[1] / "common") if (_TU.parents[1] / "common" / "zadania.py").exists() else (_TU / "fabryka" / "research" / "common")
sys.path.insert(0, str(FABRYKA_COMMON))


def przygotuj(task_id: str) -> dict:
    import zadania as Z
    from datasets import load_dataset

    meta = Z.ZADANIA[task_id]
    if meta.get("kod"):
        return {"uwaga": f"własny kod {meta['kod']}: zbiór pobiera sam przy liczeniu"}
    rozmiary = {}
    for wariant, cfg in Z.konfiguracje(task_id, "hf"):
        if not cfg.get("dataset_path"):
            rozmiary[wariant] = "bez dataset_path (pliki OSF / własne źródło)"
            continue
        kw = {"path": cfg["dataset_path"], "name": cfg.get("dataset_name"), **(cfg.get("dataset_kwargs") or {})}
        ds = load_dataset(**kw)
        rozmiary[f"{wariant}:{cfg['task']}"] = {s: len(ds[s]) for s in ds}
    return {"zbiory": rozmiary}


def main():
    task_id, katalog = sys.argv[1], Path(sys.argv[2])
    katalog.mkdir(parents=True, exist_ok=True)
    for stary in (katalog / f"{task_id}.ok", katalog / f"{task_id}.blad"):
        stary.unlink(missing_ok=True)
    t0 = time.time()
    try:
        wynik = przygotuj(task_id)
    except Exception as e:
        traceback.print_exc()
        (katalog / f"{task_id}.blad").write_text(f"{type(e).__name__}: {e}", encoding="utf-8")
        sys.exit(1)
    wynik["s"] = round(time.time() - t0, 1)
    (katalog / f"{task_id}.ok").write_text(json.dumps(wynik, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
