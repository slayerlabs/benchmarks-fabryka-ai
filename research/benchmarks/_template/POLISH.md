# <Benchmark> po polsku: wersja polska (etap D)

Ten plik leży w osobnym katalogu `benchmarks/<name>-pl/`. Procedurę i znaczenie pól opisuje
[METODOLOGIA.md](../../METODOLOGIA.md), sekcja „D. Wersja polska (POLISH.md)”.

Oryginał: `../<name>/`. Wpisz tu link do jego `README.md`. W katalogu oryginału są karta oryginału i odtworzenie,
czyli etapy A–C.

## D1. Przetłumaczyć czy napisać od zera

| | wartość |
|---|---|
| próbka 50 przykładów (jak losowana, seed) | |
| niezależne od kraju i języka / uniwersalne / lokalne i kulturowe / językowe | / / / |
| decyzja | tłumaczenie / tłumaczenie bez przykładów lokalnych i językowych / od zera (wtedy `DATASET.md`) |
| usunięte przykłady i powód | |

## D2. Mapowanie metody

| element | decyzja: „bez zmian” albo „zmiana: co i dlaczego” |
|---|---|
| Metryka, agregacja, liczba opcji, liczba przykładów w prompcie | |
| Normalizacja długości | |
| Prompt | |
| Dane (kto tłumaczył, jakim narzędziem, kto sprawdził próbkę, ile przykładów) | |
| Kontaminacja | |

## D3. Dwie kontrole przed pierwszym wynikiem

| | wartość |
|---|---|
| 1. kod wersji polskiej na danych oryginalnych: wynik, wynik z etapu B, zgodność | |
| 2. bazy polskiego zbioru: losowa; większościowa | |
| 2. model, który zna polski @ rewizja: wynik (SE), różnica od bazy w SE | |
| werdykt | obie kontrole spełnione / niespełnione (stop) |

Komendę i środowisko zapisujesz w [`RECIPE.md`](RECIPE.md).
