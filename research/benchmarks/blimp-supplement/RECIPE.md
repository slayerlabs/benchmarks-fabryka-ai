# BLiMP Supplement (T52): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: 5 plików z OSF `ad7qg` (`pliki_osf` wpisu `T52` w `common/zadania.py`: identyfikator pliku OSF i SHA-256 dla każdego podzadania); `zadania.pobierz_osf` pobiera plik i przerywa przy innym SHA-256
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T52 --probka pelna --device cuda --batch 1` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T52 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32 (`common/ewaluuj.py`, `zbuduj_model`); sprzęt i data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/blimp-supplement/<model>/results.json`
