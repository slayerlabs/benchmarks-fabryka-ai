# GSM8K: przepis

## Przebieg centralny (wynik jeszcze niepoliczony)

- Commit kodu: niezapisane (wynik niepoliczony)
- Środowisko: `common/requirements.lock.txt`, lm-eval 0.4.9.1; Qwen3.5 i LFM3 w środowisku `new`
  (`NEW_ENV_PINS` w `tools/przebieg_centralny.sh`)
- Model: modele z `MODELE` w `tools/przebieg_centralny.sh`
- Zbiór: `openai/gsm8k@740312add88f781978c0658806c59bc2815b9866 (`main`)`
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz "<etykiety>"`; jedno zadanie:
  `python common/ewaluuj.py --model hf --repo <repo> --revision <rewizja> --zadania T33 --probka pelna --device cuda --wyjscie results/central-run/gsm8k/<etykieta>`
- Seed: harness (python, numpy, torch, fewshot) = (0, 1234, 1234, 1234); bootstrap 20261028
- Precyzja: float32
- Sprzęt: niezapisane
- Data: niezapisane
- Smoke test: niezapisane; test bez wag `tests/test_przebieg_c.py`
- Wynik: `results/central-run/gsm8k/<etykieta>/results.json`
