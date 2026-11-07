# ARC-Easy (T51): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer, modele odniesienia i kontrola etapu B)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII); kontrola etapu B to wiersz `pythia-1b-v0` (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`, loader `hf`, env `lock`), [`REPRODUCTION.md`](REPRODUCTION.md)
- Zbiór: `allenai/ai2_arc@210d026faf9955653af8916fad021475a3f00453`, konfiguracja `ARC-Easy`, split `test` (wpis `T51` w `common/zadania.py`, zadanie `slayer_arc_easy` przepisane z lm-eval `arc_easy`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T51 --probka pelna --device cuda --batch 1` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T51 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32 (`common/ewaluuj.py`, `zbuduj_model`); sprzęt i data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/arc-easy/<model>/results.json`

## Sprawdzenie kodowania par dla Pythii (etap B, bez GPU)

- Komenda (w `research/`): `python -I benchmarks/arc-easy/kodowanie_par.py <katalog pythia-1b-v0 @ f3f1b6d5> <ARC-Easy/test-00000-of-00001.parquet @ 210d026>`
- Środowisko: `.venv-eval` (transformers, pyarrow z `common/requirements.lock.txt`); dane i tokenizer z cache HF
- Data: 2026-11-07, CPU (Apple M5 Pro)
- Wynik: `n=2376 pairs=9501 golds_differing=0 contexts_with_bos=0 pairs_differing=0`, wpisany w `REPRODUCTION.md`, „BOS i kodowanie” <!-- liczba-spoza-wynikow: wyjście kodowanie_par.py, 2026-11-07 -->
