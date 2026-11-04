# MultiBLiMP PL: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Karta: [`ORIGINAL.md`](ORIGINAL.md). Wyniki: przebieg centralny, `results/central-run/multiblimp-pl/<model>/results.json` i próbki per para w `probki/T04_space.jsonl.gz`. Ustawienia: `common/zadania.py`, `T04`. Odczyt źródeł 2026-11-04. Żadnego modelu nie liczono na potrzeby tego pliku.

| | wartość |
|---|---|
| kod referencyjny @ commit | Protokół repo z karty (`ORIGINAL.md`, „Format zadania i prompt”): suma log-prawdopodobieństw zdania po spacji, pusty kontekst (T04). Repo: lm-eval `0.4.9.1`, silnik `multiple_choice` z konfiguracją `T04` w `common/zadania.py` (to samo: `doc_to_text` pusty, `target_delimiter` spacja, opcje `[sen, wrong_sen]`, cel 0). Kod autorów: `jumelet/multiblimp` @ `e05dba5`, `src/lm_eval/score.py` (`minicons`, suma log-prawdopodobieństw tokenów). |
| dlaczego ten kod | Protokół z karty (`ORIGINAL.md`); kod autorów wymaga `minicons` w wersji, której repo nie przypina. |
| model kontrolny @ rewizja albo „bez kontroli” | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | (1) Praca arXiv:2504.02768v4, źródła LaTeX, tabela per język, wiersz `pol`: wyniki tylko dla Llama3 8B i 70B, Aya 32B, Gemma3 27B, OLMo2 32B, Qwen3 14B, EuroLLM 9B i Goldfisha 125M. EuroLLM-1.7B praca ocenia, ale wyniku dla `pol` nie podaje (sprawdzone w źródle tabeli, nie w streszczeniu HTML). (2) Repo autorów @ `e05dba5`: brak plików wyników. (3) Karta zbioru HF @ `de923ef`: brak wyników. (4) Karty Qwen3.5-0.8B-Base, LFM2.5-1.2B-Base, LFM3-1.7B-Base (`main`) i EuroLLM-1.7B (@ `c730cd9`): słowo „BLiMP” nie występuje. Żaden z pięciu modeli przebiegu centralnego nie ma opublikowanego wyniku dla `pol`. |
| bez kontroli: modele z opublikowanym wynikiem, których nie liczono | Goldfish 125M (polski), 96,3 w pracy; to najtańsza kontrola. Z decyzji zadania liczony jest wyłącznie Slayer i modele przebiegu centralnego, więc go nie policzono. <!-- liczba-spoza-wynikow: arXiv 2504.02768v4, full_results.tex, wiersz pol --> |
| bez kontroli: model liczony kodem autorów i kodem z repo | nie liczono: wymagałoby nowego przebiegu modelu kodem autorów |
| bez kontroli: zgodność według kolumny „test zgodności” typu | niesprawdzona (≥ 99% zgodnych decyzji per para wymaga przebiegu kodem autorów) |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić | kod da się uruchomić; nie uruchomiono z decyzji zadania |
| zbiór @ rewizja, split, n | `jumelet/multiblimp` @ `de923efa8d2483d6b13364ee68e65308e990a991`, `pol/data.tsv`, n = 3272 <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, n_scored T04 --> |
| wynik (SE) | modeli kontrolnych brak; wyniki modeli przebiegu w tabeli niżej |
| wartość referencyjna i źródło | brak dla modelu przebiegu |
| różnica | nie dotyczy |
| kontrola odróżnia działający kod od zepsutego | bez modelu kontrolnego nie ma kontroli typu. Informacyjnie niżej: wiersz `+pl` (model znający polski > b + 2 SE) i sprawdzenie zamiany kolejności. |
| warunek odtworzenia | ±2 pkt; gdy 2 SE > 2 pkt, w granicach 2 SE |
| werdykt | bez kontroli: nierozstrzygnięte. Wynik T04 z przebiegu centralnego nie idzie do tabeli CodeSOTA ani do meta-oceny, dopóki model kontrolny (Goldfish 125M) nie zostanie policzony kodem autorów i kodem repo. |

## Modele przebiegu wobec bazy (informacyjnie, to nie jest kontrola)

b = 50%. SE A = √(p(1−p)/3272), w pkt. Bez opublikowanego wyniku warunek z wiersza `+pl` brzmiałby: model znający polski > b + 2 SE. EuroLLM-1.7B (trenowany m.in. na polskim) go spełnia, z = 104,5. Ale oryginał z wynikiem istnieje, więc obowiązuje odtworzenie, a nie ten warunek. <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, eurollm-1.7b -->

| model | trafność % | trafienia | SE pkt | z wobec b |
|---|---|---|---|---|
| Slayer 1.06 | 98,59 | 3226 | 0,21 | 236,1 <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, slayer1b-1.06 --> |
| EuroLLM-1.7B | 93,86 | 3071 | 0,42 | 104,5 <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, eurollm-1.7b --> |
| LFM3-1.7B-Base | 89,15 | 2917 | 0,54 | 72,0 <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, lfm3-1.7b-base --> |
| Qwen3.5-0.8B-Base | 84,50 | 2765 | 0,63 | 54,5 <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, qwen3.5-0.8b-base --> |
| LFM2.5-1.2B-Base | 82,95 | 2714 | 0,66 | 50,1 <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, lfm2.5-1.2b-base --> |

Zamiana kolejności zdań w parze (typ `para`): wyliczona z zapisanych log-prawdopodobieństw obu zdań, nie osobnym przebiegiem. Remisów jest 0 u każdego z pięciu modeli, więc wynik z zamienioną kolejnością równa się oryginalnemu (różnica 0, dopuszczalna: udział remisów 0). <!-- liczba-spoza-wynikow: probki/T04_space.jsonl.gz przebiegu centralnego, pięć modeli -->

Slayer ma 98,59%: więcej niż EuroLLM 9B (97,3) i blisko Gemmy3 27B (98,8) z pracy. Space oznacza go na T04 jako `flagged`. Podejrzenie, że zdania z `pol/data.tsv` (publiczne drzewa UD) są w danych treningowych Slayera, jest do sprawdzenia w [#36](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/36). Do tego czasu ten wynik nie mówi o polskiej gramatyce Slayera. <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, slayer1b-1.06; arXiv 2504.02768v4, wiersz pol -->

## Slayer w Space (informacyjnie: nie kontrola ani wzorzec)

Space ma wynik Slayera 1.06 na T04. Ładowania Slayera ta wartość nie sprawdza: sprawdzają je testy kodu Slayera ([METODOLOGIA, „Model kontrolny etapu B”](../../METODOLOGIA.md#model-kontrolny-etapu-b)), a tabela niżej jest informacją. Panelu nie udało się odtworzyć: przebieg centralny identyfikuje parę numerem wiersza (`source_id_digest` pełnego pliku to SHA-256 listy numerów wierszy), ale 200 najniższych skrótów `20261028|benchmark_id|member_task|id` w 24 wariantach (numer wiersza, `sent_id`, skrót dokumentu, skrót kanoniczny; trzy nazwy członka, dwie nazwy testu) nie daje `source_id_digest` panelu T04 z `results.json` Space (`c9aba49d…`). Porównanie niżej bierze więc pełny plik zamiast panelu i jest przybliżeniem. <!-- liczba-spoza-wynikow: METHOD.md i results.json Space @ 2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9; results.json przebiegu centralnego, source_id_digest -->

| | wartość |
|---|---|
| Space, T04, Slayer 1.06 @ `ef81be58` | 99,0%, n = 200, CI95 97,5–100,0, `results.json` Space @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f, observations T04, SlayerLab/Slayer1B-1.06 --> |
| przebieg centralny, Slayer 1.06 @ `ef81be58` | 98,59%, n = 3272, pełny plik <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, slayer1b-1.06 --> |
| SE panelu (SE A) | 0,70 pkt = √(0,99 · 0,01 / 200) <!-- liczba-spoza-wynikow: wartość Space T04 i n panelu --> |
| różnica | −0,41 pkt, z = −0,58 wobec SE panelu, w granicach 2 SE <!-- liczba-spoza-wynikow: 98,59 − 99,0 i SE panelu --> |
| wniosek (informacyjnie) | zgodne w przybliżeniu pełnym plikiem. Porównania na tych samych 200 parach nie zrobiono, bo składu panelu nie odtworzono. |
