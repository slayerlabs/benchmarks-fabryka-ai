# ReCoRD: przepis

## Przebieg centralny (wynik jeszcze niepoliczony)

- Commit kodu: niezapisane (wynik niepoliczony)
- Środowisko: `common/requirements.lock.txt`, lm-eval 0.4.9.1; Qwen3.5 i LFM3 w środowisku `new`
  (`NEW_ENV_PINS` w `tools/przebieg_centralny.sh`)
- Model: modele z `MODELE` w `tools/przebieg_centralny.sh`
- Zbiór: `aps/super_glue@3de24cf8022e94f4ee4b9d55a6f539891524d646 (`record`)`
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz "<etykiety>"`; jedno zadanie:
  `python common/ewaluuj.py --model hf --repo <repo> --revision <rewizja> --zadania T50 --probka pelna --device cuda --wyjscie results/central-run/record/<etykieta>`
- Seed: harness (python, numpy, torch, fewshot) = (0, 1234, 1234, 1234); bootstrap 20261028
- Precyzja: float32
- Sprzęt: niezapisane
- Data: niezapisane
- Smoke test: niezapisane; test bez wag `tests/test_przebieg_c.py`
- Wynik: `results/central-run/record/<etykieta>/results.json`
