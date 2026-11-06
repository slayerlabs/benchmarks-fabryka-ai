# MultiBLiMP PL (T04): przepis

Jeden wpis na każdy wynik. Wyniki liczy przebieg centralny.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13); wersje w `results/central-run/freeze_lock.txt` i `freeze_new.txt`
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `jumelet/multiblimp@de923efa8d2483d6b13364ee68e65308e990a991`, plik `pol/data.tsv` (wpis `T04` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T04 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T04 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32, batch 1
- Sprzęt: NVIDIA GeForce RTX 4090 (`results/central-run/environment.json`)
- Data: 2026-11-03 (`run_id` w `results.json`)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/multiblimp-pl/<model>/results.json`
