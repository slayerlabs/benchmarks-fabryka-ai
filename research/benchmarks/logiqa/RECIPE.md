# LogiQA (T18): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `EleutherAI/logiqa@c1eee1b2fd0ddc87777e36490f7ad54d0b97d141` (wpis `T18` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T18 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T18 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/logiqa/<model>/results.json`

## Pomiar autora (protokół Space, #97)

- Środowisko: WSL2 Ubuntu, Python `~/bench-team/venv` (lm-eval 0.4.9.1, torch 2.8.0+cu128, transformers 4.57.6).
- Sprzęt: NVIDIA GeForce RTX 5050 (8 GB), float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`, `TOKENIZERS_PARALLELISM=false`.
- Wagi: `~/bench-team/slayer-1.06` (SlayerLab/Slayer1B-1.06 @ `ef81be58742544ad32e1afab38db011fec209609`).
- Commit kodu: `e4dd54f7104c28fb5b19015a58b215892d975175` (po rebase na `main`; wynik policzony kodem z `main`, pliki wyników w commicie z tym wpisem).

### Rewizje
- Model: SlayerLab/Slayer1B-1.06 @ `ef81be58742544ad32e1afab38db011fec209609`.
- Zbiór: EleutherAI/logiqa @ `c1eee1b2fd0ddc87777e36490f7ad54d0b97d141`, split test.
- Parquet: `refs/convert/parquet` @ `fcd80241270118cd52c96dc517dc38804025f3f5`, plik `logiqa/test/0000.parquet`, sha256 `86f8a453cf23670e394960054d2bafc20e672bc39518b5de31fde6826e56cf9e`.
- lm-eval: 0.4.9.1 (Space przypina `6d2abda4` / 0.4.8; katalog zadania różni się tylko `dataset_kwargs.trust_remote_code`).

### Komendy
```
export PYTHONUNBUFFERED=1 NVIDIA_TF32_OVERRIDE=0 TOKENIZERS_PARALLELISM=false
PY=~/bench-team/venv/bin/python
$PY common/ewaluuj.py --model slayer --model_path ~/bench-team/slayer-1.06 --repo SlayerLab/Slayer1B-1.06 \
  --revision ef81be58742544ad32e1afab38db011fec209609 --zadania T18 --probka panel200 --device cuda --batch 1 \
  --wyjscie benchmarks/logiqa/results/slayer-1.06/panel200
$PY common/ewaluuj.py ... --probka pelna --wyjscie benchmarks/logiqa/results/slayer-1.06/pelna
```

### Czasy
- panel200: ok. 5 min (1600 żądań); pelna: ok. 6 min (5208 żądań). Zapisane w meta.json.

### SHA-256 wyników per pytanie
- panel200: `9213fed3b86c210b86d9b5b89cb4a5546a6209d6acd88c758128fb1d545849f7`
- pelna: `a6d0ed72a49c9a0c813c66adc2adf5e76332dff48805021f3be24e2ac526a4c5`
- logiqa.json: `80f2ce9fe68beae22e255d2a5d47337c622ce93642d0f7f508b838a27eb35bbb`

### Smoke test
5 przykładów (pierwszy, ostatni, 3 losowe, seed 20261028) — odpowiedź pasuje do pytania, brak pustych pól/ucięć/duplikatów. n=651, najczęstsza poprawna „d” 181/651 = 0,278. Zapis: `space-19-notatki/SMOKE.md`.

### Kontrola
Bez kontroli — wynik wstępny. Miejsca przeszukane: plik wyników Pythii v0, karta EuroLLM-1.7B, Open LLM Leaderboard v2, praca Liu i in. (2020) i repo autorów (tylko dane). Zapis: `space-19-notatki/REGULA.md`.
