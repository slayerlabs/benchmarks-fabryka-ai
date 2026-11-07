# MathQA (T19): przepis

Jeden wpis na każdy wynik. Jest jeden wynik: pomiar autora protokołem Space (wpis niżej). Przebieg centralny tego
zadania jeszcze nie liczył, więc jego wpis zostaje bez commitu, sprzętu i daty.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `allenai/math_qa@c4f1cc784c04c4957b50c97858f23893b633eea6` (wpis `T19` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T19 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T19 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/mathqa/<model>/results.json`

## Pomiar autora (protokół Space, #97)

- Commit kodu: `366aa7e` (stan gałęzi `research/mathqa` w chwili pomiaru; commit protokołu, bez zmian w `common/`)
- Środowisko: `common/requirements.lock.txt` (lm-eval 0.4.9.1, transformers 4.57.6) z jednym odstępstwem:
  `torch 2.8.0+cu128` z indeksu PyTorcha zamiast buildu CPU, który PyPI daje na Windows dla `torch==2.8.0`.
  Ta sama wersja, inny build; karta RTX 5080 (Blackwell, sm_120) wymaga CUDA 12.8
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, wagi lokalnie w
  `models/slayer-1.06`, `weights_sha256` w `results_rozszerzone.json`
- Zbiór: `allenai/math_qa@c4f1cc784c04c4957b50c97858f23893b633eea6`, dane z `refs/convert/parquet`
  @ `fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6`
- Komendy (w `research/`), panel i pełny split osobno:
  `python common/ewaluuj.py --model slayer --repo SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --model_path models/slayer-1.06 --zadania T19 --probka panel200 --device cuda --batch 1 --etykieta 1.06 --wyjscie benchmarks/mathqa/results/slayer-1.06/panel200`
  oraz to samo z `--probka pelna` i `--wyjscie benchmarks/mathqa/results/slayer-1.06/pelna`
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234; bootstrap CI95 seed 20261028
- Precyzja: float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`
- Sprzęt: RTX 5080, Windows 11, Git Bash
- Data: 2026-11-07; panel 17:35:24–17:35:55 CET (2000 żądań), pełny split 17:37:12–17:40:37 CET (29 850 żądań)
- Smoke test: dane i prompt przed pomiarem, [`notatki/SMOKE.md`](notatki/SMOKE.md) (idx 0, 2288, 2532, 2823, 2984;
  ziarno losowania 20261028)
- Wynik: `results/slayer-1.06/{panel200,pelna}/results.json`; próbki per pytanie spakowane gzipem, katalog `trace/`
  zostaje lokalnie

## Liczby raportu (bez GPU, z próbek w repo)

- Komenda (w `research/`): `python benchmarks/mathqa/zbierz_wyniki.py`
- Wejście: `results/slayer-1.06/<przebieg>/results_rozszerzone.json` i `probki/T19_space.jsonl.gz`
- Wyjście: `benchmarks/mathqa/results/mathqa.json`, skąd liczby bierze bramka (`tools/liczby.py`)
- Co liczy od nowa: rozkład celu i predykcji, bazy (wpis T19 ma `klasy_stale=False`, więc `ewaluuj.py` ich nie
  wypełnia), porównania z bazami parowane po pytaniach, wpływ długości opcji na `acc_norm` i zgodność panelu
  z pełnym splitem; wartości, SE i CI95 przepisuje z przebiegu
- Środowisko: biblioteka standardowa Pythona, bez sieci i bez wag
- Data: 2026-11-07
