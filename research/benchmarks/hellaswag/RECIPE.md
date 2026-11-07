# HellaSwag (T05): przepis

Liczby etapu B są w [`results/HELLASWAG.md`](results/HELLASWAG.md). Niżej przepis przebiegu centralnego i trzech przebiegów z vast.ai.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `Rowan/hellaswag@218ec52e09a7e7462a5400043bb9a69a41d06b76` (wpis `T05` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T05 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T05 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/hellaswag/<model>/results.json`

Niżej: skąd każdy przebieg i odczyt promptu przed wagami.

## Co znaczą pola, zanim padnie jakikolwiek model

Każde pytanie ma cztery zakończenia, ponumerowane 0, 1, 2, 3. Pole `label` w zbiorze mówi, które z nich jest poprawne. To jest klucz zbioru, nie wybór modelu. Modelu przy tym odczycie nie było.

`split_type` też nie jest wynikiem. Autorzy HellaSwag dzielą pytania na dwie grupy:

- `indomain`: czynność z tego pytania występowała w ich danych treningowych.
- `zeroshot`: tej czynności w treningu nie było.

`ind` to numer przykładu nadany w zbiorze. Nie jest równy numerowi wiersza w pliku walidacji. Wiersz 0 ma `ind` 24.

Prompt buduje `hellaswag.py`. Nie bierze gotowej kolumny `ctx`. Ta kolumna skleja `ctx_a` i `ctx_b` małą literą. lm-eval bierze `ctx_b` i podnosi jego pierwszą literę. Na wierszu 0 kolumna `ctx` kończy się na „he”, a prompt na „He”.

## Dane i komendy

- Zbiór: `Rowan/hellaswag` @ `218ec52e09a7e7462a5400043bb9a69a41d06b76`.
- Walidacja: `data/validation-00000-of-00001.parquet`, sha256 `899813071e1e95efafec90f856e1987d2150fa4d020fc005df6962c259f660cd`, 10042 wiersze. Na tym liczymy wynik.
- Trening, tylko jako 10 przykładów w promptcie 10-shot: `data/train-00000-of-00001.parquet`, sha256 `cacb12587faa63d7f723a72d61d12bfa94b140446f5a6a0a2e1c6906ab88bf02`. Plików nie ma w repo.
- Pobranie, w `research/`: `python benchmarks/hellaswag/hellaswag.py fetch --out /ścieżka/data`
- Odczyt tych samych siedmiu promptów, bez wag: `python benchmarks/hellaswag/hellaswag.py show`
- Liczenie na vast.ai: [`instance.sh`](instance.sh). Najpierw `bash instance.sh setup 28800`, potem `eurollm`, `slayer` i `slayer-space`.
- Raport, w `research/`: `python benchmarks/hellaswag/hellaswag.py report`

Data odczytu promptów: 2026-11-04. Logprob przy tamtym odczycie nie był liczony. Autor czyta te siedem przykładów osobiście.

## Wspólne dla trzech przebiegów

- Kod: gałąź `research/hellaswag-bc`, `benchmarks/hellaswag/hellaswag.py` i `instance.sh`.
- Środowisko: obraz vast.ai z torch 2.8.0+cu128 i CUDA 12.8, potem `common/requirements.lock.txt` (lm-eval 0.4.9.1, transformers 4.57.6). Lockfile nie zawiera trzech paczek, które trzeba było dołożyć, żeby tokenizer i import wstały: `torchvision` 0.23.0+cu128, `sentencepiece` 0.2.0, `protobuf` 5.29.5.
- Zbiór: jak wyżej. Sumy sha256 surowych wyników: [`results/raw/SHA256SUMS`](results/raw/SHA256SUMS).
- Seedy: python 0, numpy 1234, torch 1234, fewshot 1234.
- Precyzja: float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`.
- Sprzęt: NVIDIA GeForce RTX 4090 (vast.ai).

## utter-project/EuroLLM-1.7B, 10-shot

- Model: `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374`, wrapper `hf`.
- Komenda: `bash benchmarks/hellaswag/instance.sh eurollm`
- Data: 2026-11-05.
- Wynik: `results/raw/eurollm-1.7b-10shot.jsonl.gz`. `acc_norm` 0,6074 (SE 0,0049), n = 10042.

## SlayerLab/Slayer1B-1.06, 10-shot

- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, wrapper `slayer`.
- Komenda: `bash benchmarks/hellaswag/instance.sh slayer`
- Data: 2026-11-05.
- Wynik: `results/raw/slayer-1.06-10shot.jsonl.gz`. `acc_norm` 0,3953 (SE 0,0049), n = 10042.

## SlayerLab/Slayer1B-1.06, 0-shot

- Ten sam model i wrapper. Komenda: `bash benchmarks/hellaswag/instance.sh slayer-space`
- Data: 2026-11-06.
- Wynik: `results/raw/slayer-1.06-0shot.jsonl.gz`. Cały split: `acc_norm` 0,3938 (SE 0,0049).
- Zgodność ze Space: niepotwierdzona, skład panelu niesprawdzony. `source_id` nie jest unikalny, więc hasz po nim nie jest panelem T05.

## Wiersz 0, ActivityNet, indomain

`ind` 24, źródło `activitynet~v_-JhWjGDPHMY`. `ctx_b` w zbiorze to „he”.

Prompt:

> Roof shingle removal: A man is sitting on a roof. He

Zakończenia:

- 0: is using wrap to wrap a pair of skis.
- 1: is ripping level tiles off.
- 2: is holding a rubik's cube.
- 3: starts pulling up roofing on a roof. To jest poprawne zakończenie (`label` 3). Mówi o zrywaniu pokrycia dachu, czyli o czynności z nagłówka.

## Wiersz 1, ActivityNet, zeroshot

`ind` 92, źródło `activitynet~v_-lJS58hyo1c`. `ctx_b` w zbiorze to „the lady”, w prompcie „The lady”.

Prompt:

> Clean and jerk: A lady walks to a barbell. She bends down and grabs the pole. The lady

Zakończenia:

- 0: swings and lands in her arms.
- 1: pulls the barbell forward.
- 2: pulls a rope attached to the barbell.
- 3: stands and lifts the weight over her head. To jest poprawne zakończenie (`label` 3).

## Wiersz 3243, WikiHow, zeroshot

`ind` 1, źródło `wikihow~4`. Surowe pola mają nawiasy `[header]`, `[title]`, `[step]`, `[substeps]`. Po cleanupie `[title]` w środku zdania staje się kropką. Nawias na początku zakończenia zostawia spację. Ta spacja jest częścią tekstu, więc wydłuża zakończenie o jeden znak i przez to wchodzi do dzielnika `acc_norm`.

Prompt:

> Personal Care and Style: How to become a fashion consultant. Obtain your high school diploma or ged. This job requires a high school diploma or equivalent, so make sure to apply yourself and finish school. If your high school offers these classes, take art, design, and sewing to familiarize yourself with foundational concepts in fashion.

Zakończenia (spacja na początku jest naprawdę w tekście):

- 0: zaczyna się spacją, potem „Many high schools have classes offered…”. W środku jest „field.. Search”, bo kropka ze zdania zeszła się z kropką z `[title]`.
- 1: Having an associate's degree in business…
- 2: You should also be able to show the world what fashion is…
- 3: zaczyna się spacją, potem „Earn a bachelor's degree in a fashion-related field…”. To jest poprawne zakończenie (`label` 3).

## Wiersz 5000, WikiHow, zeroshot

`ind` 13249, źródło `wikihow~21950`. Poprawne jest zakończenie 1 (`label` 1).

Prompt:

> Personal Care and Style: How to buy a wedding band for men. Find a ring suitable for his lifestyle. Your fiancé is going to wear this ring every day, so choose one that will mesh with his daily routine. A guy who works a lot with his hands, for example, would appreciate a slim ring with round edges so he can easily take it on and off.

Zakończenia:

- 0: spacja, potem „Check the band's design…”.
- 1: spacja, potem „Men with active lifestyles might prefer a platinum ring…”. To jest poprawne zakończenie.
- 2: spacja, potem „You can buy rings in black, silver, or pink…”.
- 3: „A girl who works a lot with her hands… married.. Consider the person's other interests.” Podwójna kropka jest z `[title]`.

## Wiersz 7500, WikiHow, indomain

`ind` 31630, źródło `wikihow~52149`. Poprawne jest zakończenie 1 (`label` 1).

Prompt:

> Food and Entertaining: How to make spicy hot chocolate. Put the chocolate in a mug and add a splash of the milk or milk substitute so that the chocolate is almost covered. Melt the chocolate in the microwave and stir until the consistency is creamy. This step can also be done on the stove in a pot.

Zakończenia, każde zaczyna się od spacji po wyciętym `[title]`:

- 0: Heat the milk and cream over the stove…
- 1: Once the chocolate is a smooth consistency add the remainder of the milk and heat until warm. Add a teaspoon of vanilla extract. To jest poprawne zakończenie.
- 2: Add a dollop of marshmallow syrup…
- 3: Add the cold milk and some ice cream…

## Wiersz 10000, WikiHow, indomain

`ind` 50351, źródło `wikihow~82854`. Poprawne jest zakończenie 1 (`label` 1).

Prompt:

> Food and Entertaining: How to remove wine labels for collecting. Soak the bottle in hot water for 15 minutes. If wished, you can purchase a chlorinated soap from a store that carries wine-making equipment and add a little of this following the instructions. This will help to dissolve the glue.

Zakończenia:

- 0: spacja, „Dab it onto the label…”.
- 1: spacja, „Remove the bottle from the hot water. Gently peel the label off the bottle.” To jest poprawne zakończenie.
- 2: „If that doesn't work, soak the bottle…”.
- 3: spacja, „Scrape the label off with a wire-brush…”.

## Wiersz 10041, WikiHow, zeroshot, ostatni wiersz splitu

`ind` 50657, źródło `wikihow~83366`. Poprawne jest zakończenie 2 (`label` 2).

Prompt:

> Family Life: How to tell if your teen is being abused. Pay attention to your teen dressing inappropriately. If you suspect that your teen is being beaten by someone in their life, you will want to pay close attention to their dress code. While all teens have different styles and preferences, be on the lookout for any clothing that is out of the norm for your child.

Zakończenia:

- 0: „Try to figure out why they are dressing something that is frowned upon.. Understand why your child is acting different.”
- 1: „Read the following as a rule for determining your teen's behaviour…”.
- 2: spacja, potem „For instance, your teen may try to hide the signs of abuse…”. To jest poprawne zakończenie. Spacja została po `[substeps]` i liczy się do długości w `acc_norm`.
- 3: spacja, „Ask your teen if they have black tights…”.
