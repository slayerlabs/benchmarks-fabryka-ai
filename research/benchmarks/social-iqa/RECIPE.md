# Social IQa (T46): przepis

Jeden wpis na każdy wynik. Wyniki liczy przebieg centralny.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13); wersje w `results/central-run/freeze_lock.txt` i `freeze_new.txt`
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `allenai/social_i_qa@8835ceb9141d7896d9d968634a9b21ae440e3ec5`, dane z `refs/convert/parquet` (gałąź, bez przypiętego SHA), split `validation` (wpis `T46` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T46 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T46 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32, batch 1
- Sprzęt: NVIDIA GeForce RTX 4090 (`results/central-run/environment.json`)
- Data: 2026-11-03 (`run_id` w `results.json`)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/social-iqa/<model>/results.json`

## Pomiar wstępny autora (nie wynik przebiegu)

Zapis pomocniczy: autor PR policzył Slayera 1.06 przed przebiegiem centralnym. Liczby z tego pomiaru nie idą do
tabeli wyników ani do CodeSOTA ([`README.md`](README.md), „Pomiar wstępny autora”). Na pełnym splicie decyzje
zgadzają się z przebiegiem centralnym we wszystkich 1954 pytaniach. <!-- liczba-spoza-wynikow: porównanie results/slayer-1.06/social_iqa_full.jsonl.gz z probki/ przebiegu centralnego -->

- Commit: `a80e693` (gałąź `research/siqa`, od `origin/main` @ `476ffa7`).
- lm-eval 0.4.9.1, transformers 4.57.6, torch 2.8.0+cu128, Python 3.9.25.
- GPU NVIDIA GeForce RTX 5060 Ti 16 GB, Windows 11, `--device cuda --batch 8`, float32.
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`.
- Zbiór: jak w przebiegu centralnym; stan gałęzi `refs/convert/parquet` przy odczycie 2026-11-04:
  `537a2ec8ec565adc0b70b70752893e59e024df26`.
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234.
- Data: niezapisane (commit z 2026-11-04).
- Smoke test: pięć dokumentów z panelu (`--probka 5`), sprawdzone ręcznie: prompt `Q: {context} {question}\nA:`, trzy
  kontynuacje ze spacją na początku, cel `label - 1`; `doc_id` 260 (`label` 3 → `target` 2, kontynuacje
  ` accomplished`, ` apprehension for Aubrey`, ` energized`), 575, 851, 1273, 1708.
- Komenda (panel Space 200; pełny split z `--probka pelna`):

  ```bash
  python common/ewaluuj.py --model slayer --model_path <wagi> \
    --revision ef81be58742544ad32e1afab38db011fec209609 --repo SlayerLab/Slayer1B-1.06 \
    --zadania T46 --dane hf --probka panel200 --wyjscie <dir> --device cuda --batch 8 --etykieta 1.06
  ```

- Plik liczb: `python benchmarks/social-iqa/zbierz_wyniki.py <katalog panelu> <katalog pełnego splitu>` przepisuje z
  `results_rozszerzone.json` wartości, SE i CI95 (nie liczy metryk ponownie) i dokłada bazy policzone z goldów, bo
  `ewaluuj.py` zostawia je puste przy `klasy_stale=False`.
- Wynik: `results/social_iqa.json`; per pytanie `results/slayer-1.06/social_iqa.jsonl.gz` (panel) i
  `results/slayer-1.06/social_iqa_full.jsonl.gz` (pełny split). `source_id_digest` pełnego splitu
  `e92365ff54129c93eb518df4c5544bb39847ea762c2b5c970cef0ad5afeef808`, ten sam co w przebiegu centralnym.
