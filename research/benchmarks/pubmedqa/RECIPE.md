# PubMedQA (T44): przepis

Jeden wpis na każdy wynik. Wyniki liczy przebieg centralny.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane. Jedyny hash w wynikach to `provenance.inventory_commit`
  `041795175bedc3e647a736fed09a3c7f54b73b1c` w `results.json`; to commit spisu zadań, nie commit kodu przebiegu,
  więc nie wpisujemy go jako commitu wyniku (METODOLOGIA, „Przepis”: czego nie zapisano, nie zgadujemy)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13); wersje w `results/central-run/freeze_lock.txt` i `freeze_new.txt`
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `bigbio/pubmed_qa@15578e80ef02c2c9636d33fdd7eb6b05b987ba60`, konfiguracja `pubmed_qa_labeled_fold0_source`, split `test`, czytany z parquetu `refs/convert/parquet` @ `13a7d15476092370cbabb6475390e7e69b74d2f2` (wpis `T44` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T44 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T44 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32, batch 1
- Sprzęt: NVIDIA GeForce RTX 4090 (`results/central-run/environment.json`)
- Data: 2026-11-03 (`run_id` w `results.json`)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie). Zapis 5 dokumentów
  z id i tym, co się zgadzało, odczytany po przebiegu z jego próbek: [`notatki/SMOKE.md`](notatki/SMOKE.md)
  (idx 0, 286, 317, 498, 499; ziarno losowania 20261028)
- Wynik: `results/central-run/pubmedqa/<model>/results.json`

## Liczby raportu (bez GPU, z próbek w repo)

- Komenda (w `research/`): `python benchmarks/pubmedqa/zbierz_wyniki.py`
- Wejście: `results/central-run/pubmedqa/<model>/results_rozszerzone.json` i `probki/T44_space.jsonl.gz`
- Wyjście: `benchmarks/pubmedqa/results/pubmedqa.json`, skąd liczby bierze bramka (`tools/liczby.py`)
- Co liczy od nowa: tylko rozkład celu i predykcji, porównanie z b parowane po pytaniach i średnie log P
  kontynuacji; wartości, SE i CI95 przepisuje z przebiegu
- Środowisko: biblioteka standardowa Pythona, bez sieci i bez wag
- Data: 2026-11-07
