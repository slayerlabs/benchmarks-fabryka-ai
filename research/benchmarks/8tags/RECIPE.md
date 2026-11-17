# 8tags (T23): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `sdadas/8tags@82ddf9c0d06ffc982aeccf2473b7ce31f2167adf` (wpis `T23` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T23 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T23 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/8tags/<model>/results.json`

## Kontrola etapu B (`+pl`): model znający polski

Model i warunek zapisuje [`REPRODUCTION.md`](REPRODUCTION.md). Wyników jeszcze nie ma: wpis dostaje commit, sprzęt i datę po przebiegu centralnym.

- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3` w `MODELE`); zapas, gdy przebieg pominie Bielika (repo z bramką zgody na HF): `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` (etykieta `eurollm-1.7b`). Oba liczą wszystkie zadania przebiegu, bez osobnego wpisu w `TESTY_MODELU`.
- Środowisko: `lock` (lm-eval 0.4.9.1, `common/requirements.lock.txt`), precyzja float32.
- Zbiór: `sdadas/8tags@82ddf9c0d06ffc982aeccf2473b7ce31f2167adf` (wpis `T23` w `common/zadania.py`), split `test`, n = 4372, 5-shot z banku przykładów. <!-- liczba-spoza-wynikow: wpis T23 w common/zadania.py i plik test @ 82ddf9c0 -->
- Komenda (w `research/`): linia przebiegu `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T23 ' | grep bielik-1.5b-v3`, czyli `common/ewaluuj.py --model hf --repo speakleash/Bielik-1.5B-v3 --revision 4b25049621bf3952a1fc9314c89773102eda0333 --model_path /workspace/modele/bielik-1.5b-v3 --zadania T23 --probka pelna --device cuda --batch 1 --etykieta bielik-1.5b-v3 --wyjscie /workspace/wyniki/8tags/bielik-1.5b-v3` (dla EuroLLM ta sama linia z jego repo, rewizją i etykietą).
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Commit kodu, sprzęt, data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/8tags/bielik-1.5b-v3/results.json` i próbki per pytanie w `probki/`; kontrola: `tools/statystyka.wobec_stalej` na wynikach per pytanie (z ≥ 2, `REPRODUCTION.md`).

## Smoke test przed przebiegiem

Wyrenderowane 2026-11-17 funkcjami repo, bez wag: `zadania.konfiguracje("T23", "hf")`, `ewaluuj.zbuduj_zadania`, `ewaluuj.ustaw_bank` dla pełnego splitu, potem `fewshot_context` lm-eval 0.4.9.1. Logprobu modelu nie ma, bo wag nie ładowano. Indeksy są od 0; pytania testu to pierwsze, ostatnie i trzy wylosowane `random.Random(0)` z pozostałych.

Bank (`train`, `fewshot_split: train`, 40 001 wierszy): indeksy 9941, 35963, 34140, 26412, 12779, złoto kolejno „Sport”, „Praca”, „Sport”, „Technologie”, „Praca”. Każde pytanie dostaje te same demonstracje w tej kolejności (prefiks kontekstu identyczny w pięciu pytaniach niżej). Demonstracja to prompt, spacja i kategoria, demonstracje rozdziela `\n\n`; prompt pytania kończy się `Kategoria:` bez spacji, a osiem kontynuacji to spacja i nazwa kategorii (`target_delimiter` spacja). Długości opcji w znakach (do `acc_norm`): 4, 8, 8, 8, 11, 5, 5, 11. <!-- liczba-spoza-wynikow: ewaluuj.ustaw_bank i fewshot_context na test.jsonl i train.jsonl @ 82ddf9c0, 2026-11-17 -->

- 0: `Akcję zgłoszono do konkursu platformy projektów społecznych: "Zwolnieni z teorii".`, `label` 3 „Medycyna”. Kategorii nie da się wywnioskować z samego zdania. <!-- liczba-spoza-wynikow: test.jsonl @ 82ddf9c0, wiersz 0 -->
- 4371: `Rodzice Evie Mitchell od momentu narodzin córki często bywają w szpitalu.`, `label` 3 „Medycyna”. Pasuje. <!-- liczba-spoza-wynikow: test.jsonl @ 82ddf9c0, wiersz 4371 -->
- 332: `Siewierz (woj. śląskie), noc z czwartku na piątek.`, `label` 4 „Motoryzacja”. Kategorii nie da się wywnioskować z samego zdania. <!-- liczba-spoza-wynikow: test.jsonl @ 82ddf9c0, wiersz 332 -->
- 3156: `Zinterpretowaliśmy - Wyniki badań zwykłej i BIO włoszczyzny z Lidla.`, `label` 2 „Jedzenie”. Pasuje. <!-- liczba-spoza-wynikow: test.jsonl @ 82ddf9c0, wiersz 3156 -->
- 3446: `Póki mogą, udają, że są zdrowe.`, `label` 5 „Praca”. Kategorii nie da się wywnioskować z samego zdania. <!-- liczba-spoza-wynikow: test.jsonl @ 82ddf9c0, wiersz 3446 -->

W 3 z 5 pytań i w 2 z 5 demonstracji (35963 `Rosjanin szedł autostradą A2 do Niemiec.` i 12779 `Dowolnego, nie tylko z Zespołem Aspergera..`, obie „Praca”) etykieta nie wynika z samego zdania. To cecha zbioru, a nie błąd renderowania: prompt, opcje i indeks złota zgadzają się z YAML-em (`{{label|int}}`), więc trafność modelu ma sufit poniżej 1, którego ten smoke test nie mierzy. Na całym splicie `test`: 4 372 pytania, 0 pustych zdań, 0 powtórzonych promptów, etykiety 0–7. 361 zdań ma cudzysłów, co daje cudzysłów w cudzysłowie (`Tytuł: "…"Zwolnieni z teorii"."`), tak samo jak w YAML-u forka. Najdłuższe wejście (BOS, prompt z 5 demonstracjami, najdłuższa opcja) ma 734 tokeny Pythii (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5`), mediana 625, najkrótsze 602. <!-- liczba-spoza-wynikow: test.jsonl @ 82ddf9c0 i tokenizator Pythii @ f3f1b6d5, wyliczenie 2026-11-17 -->
