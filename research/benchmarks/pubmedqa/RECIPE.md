# PubMedQA (T44): przepis

Jeden wpis na każdy wynik. Wyniki liczy przebieg centralny.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13); wersje w `results/central-run/freeze_lock.txt` i `freeze_new.txt`
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `bigbio/pubmed_qa@15578e80ef02c2c9636d33fdd7eb6b05b987ba60`, konfiguracja `pubmed_qa_labeled_fold0_source`, split `test`, czytany z parquetu `refs/convert/parquet` @ `13a7d15476092370cbabb6475390e7e69b74d2f2` (wpis `T44` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T44 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T44 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32, batch 1
- Sprzęt: NVIDIA GeForce RTX 4090 (`results/central-run/environment.json`)
- Data: 2026-11-03 (`run_id` w `results.json`)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/pubmedqa/<model>/results.json`
