# PIQA: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md), wpis „EleutherAI/pythia-1b-v0 (kontrola)”. Liczby: [`results/PIQA.md`](results/PIQA.md), sekcja „Kontrola”.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1` (PyPI, `common/requirements.lock.txt`), konfiguracja `piqa.yaml` przekazana przez `piqa.py` (`task_config`) bez zmian promptu, opcji, celu i metryk; zmienione tylko źródło danych (`dataset_path: parquet` z plikiem `ybisk/piqa` wyżej) |
| dlaczego ten kod | Autorzy PIQA nie publikują kodu 0-shot dla modelu językowego (praca ocenia dostrajane klasyfikatory). Opublikowany wynik Pythii policzył lm-eval `0.2.0` (zadanie `PiQA` w wersji 0); repo ma przypięty lm-eval `0.4.9.1`. Prompt `Question: {goal}\nAnswer:`, kontynuacja ze spacją i wzór `acc_norm` (dzielenie przez długość opcji w znakach) są w `v0.2.0`, `6d2abda4` i `v0.4.9.1` te same (`ORIGINAL.md`, „Ocena” i „Znane rozbieżności”). To jest kod wskazany przez repo, nie harness z 2022 bajt w bajt. |
| model kontrolny @ rewizja | `EleutherAI/pythia-1b-v0` @ `step143000`, `HFLM`, bez BOS (konwencja tokenizera Pythii i harnessu z 2022) |
| dlaczego ten model | Pierwszy z listy w sekcji „Model kontrolny etapu B”; plik wyników Pythii v0 ma `piqa` z `acc` i `acc_norm`. |
| zbiór @ rewizja, split, n | `ybisk/piqa` @ `2e8ac2dffd59bac8c3c6714948f4c551a0848bb0`, parquet `refs/convert/parquet` @ `142c51238b3ca2bc61e9a075913871b8b600e8e1`, `validation`, n = 1838 |
| zbiór w 2022 a dziś | Ten sam zestaw pytań. Harness z 2022 ładował `piqa` skryptem HF, który ma ten sam blob od 2022-01-25 do `2e8ac2df` i pobiera paczkę AI2 `physicaliqa-train-dev.zip`; jej `dev` ma dziś te same 1838 pytań i etykiet w tej samej kolejności co parquet. Niesprawdzalne: czy paczka w listopadzie 2022 była bajtowo ta sama (`ORIGINAL.md`, „Zbiór w 2022”). |
| wynik (SE): acc_norm | 0,7095 (1304 z 1838), SE A 0,0106 |
| wynik (SE): acc | 0,7051 (1296 z 1838), SE A 0,0106 |
| wartość referencyjna i źródło: acc_norm | 0,7051 (1296 z 1838), SE 0,0106. [Plik Pythii v0 @ `a19eecb`](https://github.com/EleutherAI/pythia/blob/a19eecb807ec2c79a39ebf18108816e6ffffc1d5/evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json), odczyt 2026-11-04 (`ORIGINAL.md`) <!-- liczba-spoza-wynikow: results.piqa.acc_norm_stderr w pliku Pythii v0 @ a19eecb --> |
| wartość referencyjna i źródło: acc | 0,7040 (1294 z 1838), SE 0,0107. Ten sam plik <!-- liczba-spoza-wynikow: results.piqa.acc_stderr w pliku Pythii v0 @ a19eecb --> |
| różnica: acc_norm | +0,44 pkt. Ostrożne SE (te same pytania, brak wyników per pytanie z 2022) √(SE² + SE_ref²) = 0,0150, z = 0,29, szum <!-- liczba-spoza-wynikow: SE z piqa.json i z pliku Pythii v0 @ a19eecb --> |
| różnica: acc | +0,11 pkt. Ostrożne SE 0,0151, z = 0,07, szum <!-- liczba-spoza-wynikow: SE z piqa.json i z pliku Pythii v0 @ a19eecb --> |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,5049, stała odpowiedź „zawsze `sol2`” (928 z 1838). Pythia minus ten predyktor, `acc_norm`, parowane po pytaniach: +20,46 pkt, SE 0,0157, z = 13,07, pewne, czyli wynik > b + 2 SE. Typ `mc` nie wymaga dodatkowego przebiegu. <!-- liczba-spoza-wynikow: pkt wprost z klucza control.discriminates.full.difference_pts w piqa.json --> |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE. SE z pliku Pythii: 0,0106 dla `acc_norm` i 0,0107 dla `acc`, więc 2 SE = 2,13 pkt dla obu metryk. Furtka `acc_norm`: 0,6838–0,7264; furtka `acc`: 0,6827–0,7253. Próg zapisany w `PROTOCOL.md` przed pomiarem. <!-- liczba-spoza-wynikow: 2 × SE z pliku Pythii v0 @ a19eecb --> |
| werdykt | spełniony: obie metryki w furtce |

Ten sam przebieg Pythii na RTX 4090, RTX A6000 i RTX 3090 daje te same decyzje `acc_norm` na wszystkich 1838
pytaniach (`results/PIQA.md`, „Ten sam przebieg Pythii na innych GPU”).

Ładowania Slayera kontrola nie sprawdza ([METODOLOGIA, „Model kontrolny etapu B”](../../METODOLOGIA.md#model-kontrolny-etapu-b)):
sprawdzają je testy kodu Slayera. Slayer idzie przez wrapper `slayer` z `common/slayer_lm.py` (#44).
