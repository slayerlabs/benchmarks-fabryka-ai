# PIQA: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpis brzmi „nieustalone” i podaje, gdzie szukano. Wszystkie źródła odczytano 2026-11-04.

| pole | wartość |
|---|---|
| Co mierzy | Fizyczny zdrowy rozsądek: model wybiera, które z dwóch rozwiązań osiąga podany cel. Autorzy: „the task of physical commonsense reasoning”; pytania dotyczą codziennych przedmiotów i tego, jak można ich użyć (źródłem inspiracji dla anotatorów był instructables.com). |
| Źródła | praca: Bisk, Zellers, Le Bras, Gao, Choi, „PIQA: Reasoning about Physical Commonsense in Natural Language”, AAAI 2020, [arXiv:1911.11641](https://arxiv.org/abs/1911.11641) (źródło TeX v1); strona danych autorów: [`ybisk/ybisk.github.io` @ `21edab439af693b961be2f069e8690a88d3b4e37`, katalog `piqa/`](https://github.com/ybisk/ybisk.github.io/tree/21edab439af693b961be2f069e8690a88d3b4e37/piqa) (dane w `piqa/data/`; kodu ewaluacji autorzy nie publikują); zbiór HF: [`ybisk/piqa` @ `2e8ac2dffd59bac8c3c6714948f4c551a0848bb0`](https://huggingface.co/datasets/ybisk/piqa/tree/2e8ac2dffd59bac8c3c6714948f4c551a0848bb0) (tylko skrypt ładujący `piqa.py`, blob `0f0d96172f9bf7aa10069374b3236ef083cfeb8e`); dane czytane z `refs/convert/parquet` @ `142c51238b3ca2bc61e9a075913871b8b600e8e1`, `plain_text/validation/0000.parquet`, sha256 `40e1677bba609c8801deacc171d76f3e24c083f365c95a1cbda7520c923dfea2` |
| Dane: split w pracy | split: train, dev, test; n: „over 16,000” train, „~2K” dev, „~3k” test (sekcja „Dataset”). W plikach autorów: train 16113, dev 1838, test 3084 (te same liczby w metadanych `ybisk/piqa`). <!-- liczba-spoza-wynikow: Bisk i in. 2020, sekcja „Dataset”; pliki autorów @ 21edab43 i karta ybisk/piqa @ 2e8ac2df --> |
| Dane: split w repo | split: `validation` (dev z pracy, bo test ma ukryte odpowiedzi; YAML lm-eval `piqa`: `validation_split: validation`, ten sam split w pliku Pythii); n: 1838; repo liczy pełny split i panel z tego samego przebiegu (`results/PIQA.md`). Informacyjnie: Space liczy panel 200 (`min(200, N)`). |
| Dane: licencja | licencja autorów: Academic Free License v. 3.0 (`piqa/README.md` i `piqa/data/README.md` @ `21edab43`); tag HF: `license:unknown` (`ybisk/piqa` @ `2e8ac2df`); ukryte odpowiedzi w teście: tak (`piqa/data/` ma `tests.jsonl` bez pliku etykiet; test oceniał leaderboard autorów). |
| Typ testu | [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy), wiersz `piqa` |
| Format zadania | Wybór jednej z 2 opcji. Pola: `goal`, `sol1`, `sol2`, `label` (0 albo 1; w plikach autorów etykiety są w osobnym `valid-labels.lst`). Bez natywnego id w HF (paczka `physicaliqa-train-dev.zip` ma pole `id`, skrypt HF go nie przenosi). |
| Prompt | Praca nie ma promptu modelu językowego: modele z tabeli 1 to klasyfikatory dostrajane na train (każda para cel + rozwiązanie osobno, token `[CLS]`, softmax po dwóch opcjach). lm-eval, oba commity i harness z 2022 (`lm_eval/tasks/piqa.py` @ `v0.2.0`), 0-shot: kontekst `Question: {goal}\nAnswer:`, kontynuacja to `target_delimiter` (spacja) i pełny tekst opcji. Przykład (pierwszy wiersz `validation`, `label` = 0): kontekst `Question: How do I ready a guinea pig cage for it's new occupants?\nAnswer:`, kontynuacja ` Provide the guinea pig with a cage full of a few inches of bedding made of ripped paper strips, you will also need to supply it with a water bottle and a food dish.` |
| Ocena | Praca: trafność. lm-eval (`output_type: multiple_choice`): log-prawdopodobieństwo kontynuacji dla każdej opcji; `acc` = argmax po sumie log P; `acc_norm` = argmax po sumie log P podzielonej przez długość opcji w znakach, bez wiodącej spacji (`len(choice)`; `lm_eval/api/task.py` @ `v0.4.9.1` i `lm_eval/base.py` @ `v0.2.0`, ten sam wzór). Przy remisie wygrywa wcześniejsza opcja. Bez normalizacji tekstu odpowiedzi. |
| Metryka decyzyjna | `acc_norm` (zadanie lm-eval `piqa` liczy `acc` i `acc_norm`; obie są w pliku Pythii, z którym porównuje etap B). `acc` pomocnicza. |
| Agregacja i grupy | średnia po pytaniach, bez wag (`aggregation: mean`); bez grup. |
| Bazy | losowa: 0,5 (2 opcje); stała odpowiedź: zawsze `sol2`, 928 z 1838 = 0,5049; b: 0,5049. |
| SNR: źródło | opublikowane wyniki Pythii v0 bez `-deduped` od 400 mln do 3 mld parametrów (410m, 1b, 1.4b, 2.8b), `piqa` `acc_norm`, 0-shot, końcowy checkpoint, `evals/pythia-v0` w `EleutherAI/pythia` @ `a19eecb807ec2c79a39ebf18108816e6ffffc1d5` (te same pliki co w `benchmarks/arc-easy/results/snr_baselines.json`). |
| SNR: 410m | 0,6703 <!-- liczba-spoza-wynikow: plik Pythii v0 410m (global_step71500) @ a19eecb, odczyt 2026-11-04 --> |
| SNR: 1b | 0,7051 |
| SNR: 1.4b | 0,7100 <!-- liczba-spoza-wynikow: plik Pythii v0 1.4b (global_step71500) @ a19eecb, odczyt 2026-11-04 --> |
| SNR: 2.8b | 0,7394 <!-- liczba-spoza-wynikow: plik Pythii v0 2.8b @ a19eecb, odczyt 2026-11-04 --> |
| SNR: rozrzut | odchylenie std. `acc_norm` 4 modeli (ddof=1): 0,0283 (ddof=0: 0,0245). <!-- liczba-spoza-wynikow: 4 pliki Pythii v0 @ a19eecb, odczyt 2026-11-04 --> |
| SNR: SE | SE A dla n 1838: √(p̄(1−p̄)/n) = 0,0106, p̄ = 0,7062; mediana `acc_norm_stderr` z plików: 0,0106. <!-- liczba-spoza-wynikow: 4 pliki Pythii v0 @ a19eecb, odczyt 2026-11-04 --> |
| SNR: iloraz | 2,67, ponad progiem 2. Informacyjnie wszystkie 8 rozmiarów (70m–12b): rozrzut 0,0626, iloraz 5,84. <!-- liczba-spoza-wynikow: 4 i 8 plików Pythii v0 @ a19eecb, odczyt 2026-11-04 --> |
| SNR: szum checkpointów | `pythia-1b-v0`, 5 ostatnich checkpointów (step 103000–143000), `acc_norm`: odchylenie std. 0,0047 (ddof=1), czyli mniej niż SE jednego wyniku. <!-- liczba-spoza-wynikow: pliki Pythii v0 1b, global_step103000–143000 @ a19eecb, odczyt 2026-11-04 --> |
| MDE | pełny split: 2,70 pkt jako jedno porównanie, 3,33 pkt w rodzinie sześciu porównań pod Holmem (kwantyl 2,67); panel 200: 7,73 pkt i 9,56 pkt. SE różnicy wzięte z: SE parowane Slayer 1.06 − Pythia-1B v0, `acc_norm` (`results/piqa.json`, `comparisons.slayer_minus_pythia_full.se` i `..._panel.se`); MDE = (z_próg + 0,84) · SE. Policzone po przebiegu. <!-- liczba-spoza-wynikow: MDE przeliczone z SE w piqa.json, wzór z METODOLOGIA.md --> |
| Kontaminacja | znana: Space oznacza T06 dla Slayera 1.06 jako `contamination: flagged` (`PROTOCOL.md`). Dla Pythii nieznana. Własnego skanu korpusów nie robiono. |
| Wyniki referencyjne (odczyt 2026-11-04): Pythia acc | `EleutherAI/pythia-1b-v0` @ `step143000` → `acc` 0,7040 (SE 0,0107), 0-shot, pełny `validation`, źródło: [plik Pythii v0 @ `a19eecb`](https://github.com/EleutherAI/pythia/blob/a19eecb807ec2c79a39ebf18108816e6ffffc1d5/evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json) (blob `63988cb9c80e6f3b7ab3bb2fe18202b65104dfa3`, `versions.piqa` = 0). |
| Wyniki referencyjne (odczyt 2026-11-04): Pythia acc_norm | ten sam plik → `acc_norm` 0,7051 (SE 0,0106). <!-- liczba-spoza-wynikow: SE z results.piqa.acc_norm_stderr w pliku Pythii v0 @ a19eecb --> |
| Wyniki referencyjne: kontrola a bazy | `acc_norm` Pythii minus 2 SE: 0,6838, daleko ponad bazą losową (0,5) i b (0,5049). <!-- liczba-spoza-wynikow: policzone z pliku Pythii v0 @ a19eecb i validation parquet --> |
| Wyniki referencyjne (odczyt 2026-11-04): praca | Tabela 1, trafność validation / test (%), modele dostrajane: GPT 70,9 / 69,2; BERT-Large 67,1 / 66,8; RoBERTa-Large 79,2 / 77,1; ludzie 94,9. Inne zadanie niż 0-shot (trening na train), więc nie służy jako kontrola. <!-- liczba-spoza-wynikow: Bisk i in. 2020, tabela 1, źródło TeX arXiv 1911.11641 --> |
| Wyniki referencyjne: Space | Space nie ma wartości T06 dla żadnego modelu (`results/PIQA.md`, sekcja „Panel”). |
| Train policy | `eval_only`: żaden split (`train`, `validation`, `test`) nie trafia do treningu. YAML lm-eval ma `training_split: train` tylko jako źródło przykładów few-shot; liczymy 0-shot. Zbioru wolno użyć do dekontaminacji (`should_decontaminate: true`, zapytanie to `goal`). |
| Decyzja treningowa | Niski `acc_norm` znaczy, że model słabo odróżnia wykonalne rozwiązanie codziennego zadania od podobnie brzmiącego niewykonalnego. Może wskazywać na brak angielskich tekstów instruktażowych i opisów czynności (poradniki, przepisy, majsterkowanie) w pretreningu. Nie wolno trenować na pytaniach PIQA ani pisać danych na ich wzór. Przy skażeniu (Space: `flagged` dla Slayera 1.06) wysoki wynik nie dowodzi rozumowania fizycznego. Różnica w pkt, która zmieniłaby decyzję: nieustalona, więc MDE jest informacyjne. Wynik nie mówi nic o polszczyźnie. |
| Znane rozbieżności | lista niżej |

## Znane rozbieżności

- **lm-eval `6d2abda4` wobec `v0.4.9.1`** (katalog `lm_eval/tasks/piqa`): `README.md` identyczny (blob
  `e0d7d05d99fee62fed27374e5cf9f2daee9032b8`), `piqa.yaml` różny (`1a34cc6670bffba45b9a2c3613cca7a60b37bb36` wobec
  `b147daea44b3bf3cd8f795be37dd3522f88afa3a`). Różnią się tylko `dataset_path` (`piqa` wobec `baber/piqa`) i
  `dataset_kwargs: trust_remote_code: true` w `6d2abda4`. Prompt, opcje, cel, split i metryki są te same.
- **`baber/piqa` a `ybisk/piqa`:** split `validation` w `baber/piqa` @ `142f6d7367fd9877f0fb3b5734ea6a545f54cdd1`
  (`piqa_validation.parquet`) ma te same 1838 wierszy (`goal`, `sol1`, `sol2`, `label`) w tej samej kolejności co
  parquet `ybisk/piqa` wyżej. Na tej rewizji `--tasks piqa` z `v0.4.9.1` liczyłoby więc te same pytania. `piqa.py`
  i tak czyta parquet `ybisk/piqa` wprost (`PROTOCOL.md`), bo `baber/piqa` nie jest przypięte i może się zmienić.
- **Rewizja zbioru:** YAML nie przypina rewizji; ta karta przypina `ybisk/piqa` @ `2e8ac2df` (rewizja z
  `tasks_50.json`) i parquet @ `142c5123`. `tasks_50.json` nie podaje commita `refs/convert/parquet`.
- **Zbiór w 2022:** opublikowany wynik Pythii policzono harnessem lm-eval `0.2.0` (`requirements/requirements.txt`
  w `EleutherAI/gpt-neox` @ `dfc018a`, commit z `config.git_hash` pliku wyników), zadanie `PiQA` w wersji 0 z
  `DATASET_PATH = "piqa"`, czyli przez skrypt HF `piqa.py`. Ten skrypt ma ten sam blob `0f0d9617` we wszystkich
  rewizjach `ybisk/piqa` od 2022-01-25 do `2e8ac2df` i jest identyczny z `datasets/piqa/piqa.py` w
  `huggingface/datasets` @ `1.18.0` i `2.0.0`. Pobiera `physicaliqa-train-dev.zip` z
  `storage.googleapis.com/ai2-mosaic/public/physicaliqa/` (SHA-256 paczki pobranej 2026-11-04:
  `54d32a04f59a7e354396f321723c8d7ec35cc6b08506563d8d1ffcc15ce98ddd`). Jej `dev.jsonl` i `dev-labels.lst` mają te
  same 1838 pytań i etykiet w tej samej kolejności co `piqa/data/valid*.jsonl` autorów i parquet HF. Czy paczka pod
  tym adresem była ta sama w listopadzie 2022: nieustalone (bez sumy kontrolnej z 2022; szukano w pliku wyników
  Pythii, skrypcie HF i README `ybisk/piqa`). Wersja `datasets` użyta w 2022: nieustalona (plik wyników jej nie
  zapisuje).
- **Harness i precyzja:** opublikowana wartość pochodzi z GPT-NeoX `evaluate.py` z lm-eval `0.2.0`, fp16, batch 16
  (plik wyników, `config`). Repo liczy lm-eval `0.4.9.1` przez `HFLM`, float32, batch 1. Prompt, kontynuacja i wzór
  `acc_norm` są w obu wersjach te same (odczyt kodu wyżej). Wyników per pytanie z 2022 nie ma, więc różnic na
  poziomie pytań nie da się porównać.
- **Praca a lm-eval:** praca ocenia dostrajane klasyfikatory i raportuje też test (ukryte odpowiedzi); lm-eval,
  Space i plik Pythii liczą 0-shot na `validation`. Wyniki z tabeli 1 pracy to inna metoda.
- **Panel Space:** wiersze nie mają natywnego id, a `METHOD.md` nie definiuje postaci kanonicznej wiersza, więc
  panelu Space nie da się odtworzyć z pewnością (`SPACE_METHOD.md`).
- **Kontaminacja:** zbiór jest publiczny od 2019 roku. Space oznacza Slayera 1.06 na T06 jako `flagged`.
