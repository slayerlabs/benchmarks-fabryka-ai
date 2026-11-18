# PoLEMo2 (in-domain, MC) (T22): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `allegro/klej-polemo2-in@9843af31facd613eb091deaa4141df4331d4f918` (wpis `T22` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie modele z `MODELE` i wszystkie zadania (lista etykiet wymaga `POMIN` z pominiętymi modelami); dla tego zadania woła `common/ewaluuj.py --zadania T22 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T22 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/polemo2/<model>/results.json`

## Kontrola etapu B (`+pl`): model znający polski

Model i warunek zapisuje [`REPRODUCTION.md`](REPRODUCTION.md). Wyników jeszcze nie ma: wpis dostaje commit, sprzęt i datę po przebiegu centralnym.

- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3` w `MODELE`); zapas, gdy przebieg pominie Bielika (repo z bramką zgody na HF): `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` (etykieta `eurollm-1.7b`). Oba liczą wszystkie zadania przebiegu, bez osobnego wpisu w `TESTY_MODELU`.
- Środowisko: `lock` (lm-eval 0.4.9.1, `common/requirements.lock.txt`), precyzja float32.
- Zbiór: `allegro/klej-polemo2-in@9843af31facd613eb091deaa4141df4331d4f918` (wpis `T22` w `common/zadania.py`), split `test`, n = 722, 5-shot z banku przykładów. <!-- liczba-spoza-wynikow: wpis T22 w common/zadania.py i plik test @ 9843af31 -->
- Komenda (w `research/`): linia przebiegu `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T22 ' | grep bielik-1.5b-v3`, czyli `common/ewaluuj.py --model hf --repo speakleash/Bielik-1.5B-v3 --revision 4b25049621bf3952a1fc9314c89773102eda0333 --model_path /workspace/modele/bielik-1.5b-v3 --zadania T22 --probka pelna --device cuda --batch 1 --etykieta bielik-1.5b-v3 --wyjscie /workspace/wyniki/polemo2/bielik-1.5b-v3` (dla EuroLLM ta sama linia z jego repo, rewizją i etykietą).
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Commit kodu, sprzęt, data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/polemo2/bielik-1.5b-v3/results.json` i próbki per pytanie w `probki/`; kontrola: `tools/statystyka.wobec_stalej` na wynikach per pytanie (z ≥ 2, `REPRODUCTION.md`).

## Smoke test przed przebiegiem

Wyrenderowane 2026-11-17 funkcjami repo, bez wag: `zadania.konfiguracje("T22", "hf")`, `ewaluuj.zbuduj_zadania`, `ewaluuj.ustaw_bank` dla pełnego splitu, potem `fewshot_context` lm-eval 0.4.9.1. Logprobu modelu nie ma, bo wag nie ładowano. Indeksy są od 0; pytania testu to pierwsze, ostatnie i trzy wylosowane `random.Random(0)` z pozostałych.

Bank (`train`, 5 783 wiersze): indeksy 3256, 4722, 2992, 5705, 656, złoto kolejno „Negatywny”, „Negatywny”, „Negatywny”, „Niejednoznaczny”, „Pozytywny”. Każde pytanie dostaje te same demonstracje w tej kolejności (prefiks kontekstu identyczny w pięciu pytaniach niżej). Demonstracja to prompt, spacja i nazwa sentymentu, demonstracje rozdziela `\n\n`; prompt pytania kończy się `Sentyment:` bez spacji, a cztery kontynuacje to spacja i nazwa (`target_delimiter` spacja): ` Neutralny`, ` Negatywny`, ` Pozytywny`, ` Niejednoznaczny`. Długości opcji w znakach (do `acc_norm`): 9, 9, 9, 15. <!-- liczba-spoza-wynikow: ewaluuj.ustaw_bank i fewshot_context na test.csv i train.csv @ 9843af31, 2026-11-17 -->

- 0: opinia o lekarce, która nie pomogła (pacjentka wyleczyła się u innego lekarza); `target` `__label__meta_minus_m`, czyli indeks 1 „Negatywny”. Etykieta pasuje do treści. <!-- liczba-spoza-wynikow: test.csv @ 9843af31, wiersz 0 -->
- 721: krótka pochwała hotelu i wyspy Kos; `__label__meta_plus_m`, indeks 2 „Pozytywny”. Pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9843af31, wiersz 721 -->
- 42: długa pochwała dwóch endokrynologów; `__label__meta_plus_m`, indeks 2 „Pozytywny”. Pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9843af31, wiersz 42 -->
- 395: pensjonat w górach, głównie zalety, jedna uwaga o łazienkach; `__label__meta_plus_m`, indeks 2 „Pozytywny”. Pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9843af31, wiersz 395 -->
- 431: hotel z wymienionymi zaletami i wadami; `__label__meta_amb`, indeks 3 „Niejednoznaczny”. Pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9843af31, wiersz 431 -->

Na całym splicie `test`: 722 pytania, 0 pustych zdań, 0 powtórzonych promptów; każda etykieta należy do czterech z YAML-a (117 „Neutralny”, 300 „Negatywny”, 197 „Pozytywny”, 108 „Niejednoznaczny”). Tekst jest po tokenizacji: 714 z 722 zdań ma spację przed przecinkiem albo kropką, a końcówki bywają odcięte (`trafiła m`); tak samo w demonstracjach i w zbiorze leaderboardu, więc to cecha zbioru, nie renderowania. 147 zdań ma cudzysłów wewnątrz `Opinia: "…"`. Najdłuższe wejście (BOS, prompt z 5 demonstracjami, najdłuższa opcja) ma 3332 tokeny Pythii (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5`, pytanie 413), mediana 2551, najkrótsze 2272, więc żadne nie przekracza 4096 i `ewaluuj.ogranicz_kontekst` nie zdejmie demonstracji. Tokenizatora Bielika (repo z bramką) nie liczono. <!-- liczba-spoza-wynikow: test.csv @ 9843af31 i tokenizator Pythii @ f3f1b6d5, wyliczenie 2026-11-17 -->
