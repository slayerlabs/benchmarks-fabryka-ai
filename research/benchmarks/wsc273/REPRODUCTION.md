# WSC273: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `6d2abda4fd171e68a8789330c4149e37c1ca0bda` (commit Space), uruchomiony jako `v0.4.9.1` z locka: katalog `lm_eval/tasks/wsc273` jest w obu identyczny |
| dlaczego ten kod | to instrument z `METHOD.md` i `tasks_50.json` Space |
| model kontrolny @ rewizja | `bigscience/bloom-560m` @ `ac2ae5fab2ce3f9f40dc79b5ca9f637430d24971` <!-- liczba-spoza-wynikow: nazwa modelu --> |
| dlaczego ten model | Pythia-1B v0, EuroLLM-1.7B i Open LLM Leaderboard v2 nie mają wyniku WSC273; zobacz sekcję „Wybór kontroli” <!-- liczba-spoza-wynikow: nazwy modeli --> |
| zbiór @ rewizja, split, n | `ErnestSDavis/winograd_wsc` @ `8052c534a4cecd8328c0bc879f6a5aa07404c4da`, split `test`, n = 273 |
| wynik (SE) | 0,623 (0,0294) |
| wartość referencyjna i źródło | 0,667 (0,0286), n = 273, [plik wyników lm-eval](https://github.com/EleutherAI/lm-evaluation-harness/blob/afbf8e6639c86490cc086eb949eac89b55ce58ab/results/bloom/bloom-560m/bloom-560m_common_sense_reasoning_0-shot.json) <!-- liczba-spoza-wynikow: nazwa modelu i pliku w adresie URL --> |
| różnica | -4,4 pkt, 1,5 SE wartości referencyjnej |
| warunek odtworzenia | 2 SE wartości referencyjnej przekracza 2 pkt, więc obowiązuje 2 SE: wynik w [0,6095; 0,7238] <!-- liczba-spoza-wynikow: próg protokołu ustalony przed pomiarem --> |
| werdykt | kontrola spoza listy źródeł `METODOLOGIA.md`, liczbowo w progu 2 SE; wynik Slayera wstępny |

Komendę i środowisko zapisujesz w [`RECIPE.md`](RECIPE.md).

## Wybór kontroli

Ta kontrola jest spoza listy źródeł `METODOLOGIA.md`. Lista przyjmuje tabelę z pracy autorów benchmarku, Open LLM
Leaderboard albo wynik lm-eval opublikowany w pracy modelu z otwartymi wagami. Tu źródłem jest plik wyników lm-eval
opublikowany przez autorów harnessu w ich repo, usunięty z niego w lipcu 2023 (commit `3362727d`). Plik podaje wartość, <!-- liczba-spoza-wynikow: hash commitu -->
SE, n, zadanie i komendę, ale nie rewizji modelu. W przeszukanych źródłach z listy nie znaleźliśmy wyniku WSC273 dla
modelu, który da się pobrać, dlatego wynik Slayera traktujemy jako wstępny.

Warunek liczbowy z sekcji „Model kontrolny etapu B” (opublikowana wartość ponad 2 SE nad obiema bazami) jest spełniony:
0,667 − 2 · 0,0286 ≈ 0,61, a baza większościowa to 0,502. <!-- liczba-spoza-wynikow: opublikowana wartość kontroli i jej dolna granica -->

Próg jest szeroki, bo SE publikacji daje ±5,7 pkt, a nasz wynik leży 1,32 pkt nad jego dolną granicą. Kontrola <!-- liczba-spoza-wynikow: szerokość progu i odległość od granicy wyliczone z progu protokołu i wyniku kontroli -->
wyłapałaby duży błąd zadania, danych albo metryki, ale nie potwierdza zgodności co do punktu.

Gdzie szukano i dlaczego odpadło:
- praca GPT-3: wynik dla WSC273 bez publicznych wag; <!-- liczba-spoza-wynikow: nazwa modelu -->
- GLM-130B: inny prompt; <!-- liczba-spoza-wynikow: nazwa modelu -->
- GPT-NeoX: `WSC` to inny zbiór; <!-- liczba-spoza-wynikow: nazwa modelu -->
- Pythia: `wsc` to wersja SuperGLUE, inny zbiór.

## Znane rozbieżności

- **Inny kod zadania.** Opublikowaną wartość policzył kod z 2023 (`lm_eval/tasks/wsc273.py`), który obcinał spacje <!-- liczba-spoza-wynikow: rok i nazwa pliku -->
  kontynuacji. Obecny `default.yaml` z `utils.py` daje podwójną spację na początku kontynuacji, np. `"  feared
  violence."`. To zachowanie instrumentu Space, więc go nie poprawiamy. Treść dokumentów się nie zmienia. Wariantu z
  jedną spacją nie policzyliśmy, więc nie tłumaczymy nim różnicy -4,4 pkt.
- **Rewizja kontroli.** Plik wyników nie zapisał rewizji modelu. Bierzemy rewizję główną repo modelu.
- **BOS.** `METHOD.md` wymaga konwencji tokenizera modelu i dokładnie jednego BOS na żądanie. Tokenizer `bloom-560m` <!-- liczba-spoza-wynikow: nazwa modelu -->
  nie dodaje BOS, a `HFLM` domyślnie też nie, więc kontrola liczona jest bez BOS. Wariantu z BOS nie policzyliśmy. Dla
  Slayera nakładka dodaje jeden BOS (`RECIPE.md`).
- **Kalibracja.** `METHOD.md` wymaga przed oceną kalibracji środowiska wobec oryginalnego harnessu (różnica logliku na
  token, logity bitowo równe). Tej kalibracji tu nie ma. Jest tylko test logitów nakładki wobec klasy `GPT`
  (`common/RECIPE.md`).
- **Bajty zbioru.** Skrypt ładujący nie działa w `datasets` 3.6.0, więc bajty pochodzą z `refs/convert/parquet` @
  `24cdebf4993560f25ff220b171e40f1027f3d9e6`. Listy `benchmark_sources.json` i `data_access.json` Space nie są <!-- liczba-spoza-wynikow: rewizja zbioru -->
  opublikowane, więc nie porównaliśmy tej rewizji z rewizją Space.
- **Tożsamość dokumentu.** Sekcja „Wrażliwość na tożsamość dokumentu” w [`README.md`](README.md).

## Czego kontrola nie sprawdza

`bloom-560m` przechodzi przez `HFLM`, a Slayer przez `common/slayer_lm.py`. Kontrola potwierdza zadanie, dane i <!-- liczba-spoza-wynikow: nazwa modelu -->
metrykę, nie ładowanie Slayera. To ładowanie pilnuje test logitów nakładki (`common/RECIPE.md`).
