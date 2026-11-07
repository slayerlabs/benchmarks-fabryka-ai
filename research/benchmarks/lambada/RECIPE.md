# LAMBADA (T17): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII); kontrola etapu B to wiersz `pythia-1b-v0` (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`, loader `hf`, env `lock`), [`REPRODUCTION.md`](REPRODUCTION.md)
- Zbiór: `EleutherAI/lambada_openai@900124bf3b8235c6daf21033af9948b3f07346c4`, konfiguracja `default` (wpis `T17` w `common/zadania.py`, zadanie lm-eval `lambada_openai`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T17 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T17 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/lambada/<model>/results.json`

## Sprawdzenie kodowania par dla Pythii (etap B, bez GPU)

- Komenda (w `research/`): `python -I benchmarks/lambada/kodowanie_par.py <katalog pythia-1b-v0 @ f3f1b6d5> <test lambada_openai w parquet z cache HF @ 900124bf>`
- Środowisko: `.venv-eval` (transformers, pyarrow z `common/requirements.lock.txt`); dane i tokenizer z cache HF
- Data: 2026-11-07, CPU (Apple M5 Pro)
- Wynik: `n=5153 bos_id=0 contexts_with_bos=0 pairs_differing=0`, wpisany w `REPRODUCTION.md`, „BOS i kodowanie” <!-- liczba-spoza-wynikow: wyjście kodowanie_par.py, 2026-11-07 -->
