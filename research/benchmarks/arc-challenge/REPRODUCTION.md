# ARC-Challenge: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Karta: [`ORIGINAL.md`](ORIGINAL.md). Wyniki: przebieg centralny, `results/central-run/arc-challenge/<model>/results.json` i próbki per pytanie w `probki/T02_space.jsonl.gz`. Ustawienia: `common/zadania.py`, `T02`. Odczyt źródeł 2026-11-04. Żadnego modelu nie liczono na potrzeby tego pliku.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1` (`common/requirements.lock.txt`), silnik `multiple_choice` z konfiguracją `T02` w `common/zadania.py`: ten sam prompt `Question: {{question}}\nAnswer:`, opcje `{{choices.text}}`, cel z `answerKey`, `num_fewshot` 0, metryka decyzyjna `acc_norm`. To przepisany YAML `arc_challenge.yaml`, którego katalog w `6d2abda4` i `v0.4.9.1` jest identyczny (`ORIGINAL.md`, „Znane rozbieżności”). |
| dlaczego ten kod | Praca nie ma promptu modelu językowego; karta (`ORIGINAL.md`) wskazuje zadanie lm-eval `lm_eval/tasks/arc/arc_challenge.yaml`, które liczą też pliki Pythii. |
| model kontrolny @ rewizja albo „bez kontroli” | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | (1) `EleutherAI/pythia-1b-v0` @ `step143000`, plik 0-shot @ `a19eecb`: jest wynik, ale nie przechodzi kontroli typu, bo leży na poziomie losowym (`ORIGINAL.md`, pole „Pythia-1B a klasa C”). (2) `utter-project/EuroLLM-1.7B` @ `c730cd9`, karta modelu: wynik tylko 25-shot `acc_norm` (Open LLM Leaderboard v1), a przebieg liczy 0-shot. (3) Karty `Qwen/Qwen3.5-0.8B-Base`, `LiquidAI/LFM2.5-1.2B-Base`, `LiquidAI/LFM3-1.7B-Base`: bez liczb ARC. (4) Praca TinyLlama arXiv:2401.02385, tabela 3: 0-shot bez nazwy metryki. (5) Praca ARC arXiv:1803.05457, tabela 6: solvery bez wag do pobrania. |
| bez kontroli: modele z opublikowanym wynikiem, których nie liczono | `EleutherAI/pythia-2.8b-v0` @ `step143000`, 0-shot (`ORIGINAL.md`, „Druga kontrola, 0-shot”), i EuroLLM-1.7B w 25-shot. Oba wymagają nowego przebiegu modelu; z decyzji zadania liczony jest wyłącznie Slayer i modele przebiegu centralnego. |
| bez kontroli: model liczony kodem autorów i kodem z repo | nie dotyczy. Repo woła ten sam kod co implementacja referencyjna (zadanie lm-eval z tym samym promptem i metryką), więc porównanie kodu z kodem niczego nie sprawdza (METODOLOGIA, „Bez kontroli”). |
| bez kontroli: zgodność według kolumny „test zgodności” typu | nie dotyczy (wiersz wyżej) |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić | kod autorów (`allenai/ARC-Solvers` @ `8f21cb8`) to solvery IR, PMI i modele z 2018 r., nie ocena modelu językowego |
| zbiór @ rewizja, split, n | `allenai/ai2_arc` @ `210d026faf9955653af8916fad021475a3f00453`, `ARC-Challenge`, `test`, n = 1172 <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, n_scored T02 --> |
| wynik (SE) | modeli kontrolnych brak; wyniki modeli przebiegu w tabeli niżej |
| wartość referencyjna i źródło | brak w protokole przebiegu (0-shot `acc_norm`) dla modelu przebiegu |
| różnica | nie dotyczy |
| kontrola odróżnia działający kod od zepsutego | bez modelu kontrolnego nie ma kontroli. Informacyjnie niżej: cztery modele przebiegu leżą wysoko nad b, Slayer nie. |
| warunek odtworzenia | ±2 pkt w skali metryki; gdy 2 SE > 2 pkt, w granicach 2 SE |
| werdykt | bez kontroli: nierozstrzygnięte. Wynik T02 z przebiegu centralnego nie idzie do Space ani do meta-oceny, dopóki model kontrolny (Pythia-2.8b-v0 0-shot albo EuroLLM-1.7B 25-shot) nie zostanie policzony tym kodem. |

## Modele przebiegu wobec bazy (informacyjnie, to nie jest kontrola)

b = 0,2654, stała odpowiedź „zawsze indeks 1”, wyższa niż baza losowa 0,2502 (`ORIGINAL.md`, „Bazy”). <!-- liczba-spoza-wynikow: reference.majority_value i chance_value w results.json przebiegu centralnego, T02 -->
SE A = √(p(1−p)/1172). z liczone wobec stałej b, bez parowania z predyktorem stałym (przybliżenie).

| model | `acc_norm` | trafienia | SE | z wobec b |
|---|---|---|---|---|
| Slayer 1.06 | 0,2577 | 302 | 0,0128 | −0,60 <!-- liczba-spoza-wynikow: probki/T02_space.jsonl.gz przebiegu centralnego, slayer1b-1.06 --> |
| EuroLLM-1.7B | 0,3746 | 439 | 0,0141 | 7,72 <!-- liczba-spoza-wynikow: probki/T02_space.jsonl.gz przebiegu centralnego, eurollm-1.7b --> |
| LFM2.5-1.2B-Base | 0,5094 | 597 | 0,0146 | 16,71 <!-- liczba-spoza-wynikow: probki/T02_space.jsonl.gz przebiegu centralnego, lfm2.5-1.2b-base --> |
| LFM3-1.7B-Base | 0,4292 | 503 | 0,0145 | 11,33 <!-- liczba-spoza-wynikow: probki/T02_space.jsonl.gz przebiegu centralnego, lfm3-1.7b-base --> |
| Qwen3.5-0.8B-Base | 0,4044 | 474 | 0,0143 | 9,70 <!-- liczba-spoza-wynikow: probki/T02_space.jsonl.gz przebiegu centralnego, qwen3.5-0.8b-base --> |

EuroLLM-1.7B w 0-shot ma 0,3746, a karta modelu podaje 0,4061 w 25-shot; różnica liczby przykładów w prompcie robi z tego dwa różne protokoły, więc to nie jest odtworzenie. <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, eurollm-1.7b; karta EuroLLM-1.7B @ c730cd9 -->

## Slayer w Space (informacyjnie: nie kontrola ani wzorzec)

Space ma wynik Slayera 1.06 na T02. Ładowania Slayera ta wartość nie sprawdza: sprawdzają je testy kodu Slayera ([METODOLOGIA, „Model kontrolny etapu B”](../../METODOLOGIA.md#model-kontrolny-etapu-b)), a tabela niżej jest informacją. Panelu nie udało się odtworzyć: reguła z `METHOD.md` §3 (SHA-256 klucza `20261028|benchmark_id|member_task|id`, 200 najniższych) w 2592 wariantach (nazwa testu i członka, separator, zapis daty, postać id, kierunek sortowania) nie daje `source_id_digest` panelu T02 z `results.json` Space (`1caa76f5…`), choć ten sam wzór skrótu (SHA-256 listy id w kolejności zbioru, rozdzielonej `\n`) odtwarza `source_id_digest` pełnego splitu z przebiegu centralnego. Porównanie niżej bierze więc pełny split zamiast panelu i jest przybliżeniem: panel to 200 z tych 1172 pytań. <!-- liczba-spoza-wynikow: METHOD.md i results.json Space @ 2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9; results.json przebiegu centralnego, source_id_digest -->

| | wartość |
|---|---|
| Space, T02, Slayer 1.06 @ `ef81be58` | `acc_norm` 0,25, n = 200, CI95 0,19–0,31, `results.json` Space @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f, observations T02, SlayerLab/Slayer1B-1.06 --> |
| przebieg centralny, Slayer 1.06 @ `ef81be58` | `acc_norm` 0,2577, n = 1172, pełny split <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, slayer1b-1.06 --> |
| SE panelu (typ `mc-k`, SE A) | 0,0306 = √(0,25 · 0,75 / 200) <!-- liczba-spoza-wynikow: wartość Space T02 i n panelu --> |
| różnica | +0,77 pkt, z = 0,25 wobec SE panelu, w granicach 2 SE <!-- liczba-spoza-wynikow: 0,2577 − 0,25 i SE panelu --> |
| wniosek (informacyjnie) | zgodne w przybliżeniu pełnym splitem. Porównania na tych samych 200 pytaniach nie zrobiono, bo składu panelu nie odtworzono. |
