# Polish Paraphrase Corpus (T26): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `sdadas/ppc@073012dc81efb47b0fd66b0ab48bf06ddb62f528` (wpis `T26` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T26 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T26 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/ppc/<model>/results.json`
