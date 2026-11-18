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

## Kontrola etapu B (`+pl`): model znający polski

Model i warunek zapisuje [`REPRODUCTION.md`](REPRODUCTION.md). Wyników jeszcze nie ma: wpis dostaje commit, sprzęt i datę po przebiegu centralnym.

- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3` w `MODELE`); zapas, gdy przebieg pominie Bielika (repo z bramką zgody na HF): `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` (etykieta `eurollm-1.7b`). Oba liczą wszystkie zadania przebiegu, bez osobnego wpisu w `TESTY_MODELU`.
- Środowisko: `lock` (lm-eval 0.4.9.1, `common/requirements.lock.txt`), precyzja float32.
- Zbiór: `sdadas/ppc@073012dc81efb47b0fd66b0ab48bf06ddb62f528` (wpis `T26` w `common/zadania.py`), split `test`, n = 1000, 5-shot z banku przykładów. <!-- liczba-spoza-wynikow: wpis T26 w common/zadania.py i plik test @ 073012dc -->
- Komenda (w `research/`): linia przebiegu `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T26 ' | grep bielik-1.5b-v3`, czyli `common/ewaluuj.py --model hf --repo speakleash/Bielik-1.5B-v3 --revision 4b25049621bf3952a1fc9314c89773102eda0333 --model_path /workspace/modele/bielik-1.5b-v3 --zadania T26 --probka pelna --device cuda --batch 1 --eval_gpu <GPU> --etykieta bielik-1.5b-v3 --wyjscie /workspace/wyniki/ppc/bielik-1.5b-v3` (dla EuroLLM ta sama linia z jego repo, rewizją i etykietą; nazwę GPU i katalog wag, przy kilku GPU z sufiksem `.gpu<N>`, ustawia przebieg).
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Commit kodu, sprzęt, data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/ppc/bielik-1.5b-v3/results.json` i próbki per pytanie w `probki/`; kontrola: `tools/statystyka.wobec_stalej` na wynikach per pytanie (z ≥ 2, `REPRODUCTION.md`).

## Smoke test przed przebiegiem

Wyrenderowane 2026-11-17 funkcjami repo, bez wag: `zadania.konfiguracje("T26", "hf")`, `ewaluuj.zbuduj_zadania`, `ewaluuj.ustaw_bank` dla pełnego splitu, potem `fewshot_context` lm-eval 0.4.9.1. Logprobu modelu nie ma, bo wag nie ładowano. Indeksy są od 0; pytania testu to pierwsze, ostatnie i trzy wylosowane `random.Random(0)` z pozostałych.

Bank (`train`, 5 000 wierszy): indeksy 635, 3693, 2754, 3332, 1358, złoto kolejno „A”, „B”, „A”, „A”, „C”. Każde pytanie dostaje te same demonstracje w tej kolejności (prefiks kontekstu identyczny w pięciu pytaniach niżej). Demonstracja to prompt, spacja i litera, demonstracje rozdziela `\n\n`; prompt pytania kończy się `Prawidłowa odpowiedź:` bez spacji, a trzy kontynuacje to ` A`, ` B`, ` C` (`target_delimiter` spacja). Opcje mają po 1 znaku, więc `acc_norm` = `acc`. <!-- liczba-spoza-wynikow: ewaluuj.ustaw_bank i fewshot_context na test.jsonl i train.jsonl @ 073012dc, 2026-11-17 -->

- 0: `Piasek nad Chinami.` / `Burza piaskowa w Chinach.`, `label` 2, czyli indeks 1 „B” (podobne znaczenie). Pasuje. <!-- liczba-spoza-wynikow: test.jsonl @ 073012dc, wiersz 0 -->
- 999: `Dziecko w czerwonym stroju skacze na trampolinie.` / `Nie ma dziecka w czerwonym stroju skaczącego na trampolinę.`, `label` 3, indeks 2 „C” (różne znaczenie). Pasuje. <!-- liczba-spoza-wynikow: test.jsonl @ 073012dc, wiersz 999 -->
- 395: `Wziął książkę z półki.` / `Ukradł książkę z półki.`, `label` 2, indeks 1 „B”. Pasuje, choć granica B/C jest tu umowna. <!-- liczba-spoza-wynikow: test.jsonl @ 073012dc, wiersz 395 -->
- 777: `Jak leci?` / `Jak się masz?`, `label` 1, indeks 0 „A” (to samo znaczenie). Pasuje. <!-- liczba-spoza-wynikow: test.jsonl @ 073012dc, wiersz 777 -->
- 865: `Nie ma psa liżącego dziecko.` / `Dziecko jest lizane przez psa.`, `label` 3, indeks 2 „C”. Pasuje. <!-- liczba-spoza-wynikow: test.jsonl @ 073012dc, wiersz 865 -->

Na całym splicie `test`: 1 000 pytań, 0 pustych zdań, 0 powtórzonych promptów, 0 par z identycznymi zdaniami; `label` przyjmuje tylko 1, 2 i 3 (419, 185, 396), więc `{{label|int - 1}}` daje indeksy 0–2 i nie ma etykiety 0 („not used”). 18 par ma cudzysłów w zdaniu. Najdłuższe wejście (BOS, prompt z 5 demonstracjami, opcja) ma 973 tokeny Pythii (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5`), mediana 848, najkrótsze 822. <!-- liczba-spoza-wynikow: test.jsonl @ 073012dc i tokenizator Pythii @ f3f1b6d5, wyliczenie 2026-11-17 -->
