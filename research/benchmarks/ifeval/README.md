# IFEval (T36)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

IFEval sprawdza wykonywanie instrukcji sprawdzanych regułami (długość, format, język). Zadanie lm-eval: `ifeval`, split `train`, demonstracje: 0.
Metryka decyzyjna: `prompt_level_strict_acc`. Typ `ifeval` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T36` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- Budżet generacji z YAML-a: 1280 tokenów.
- `langdetect` z seedem 0 (METHOD.md); `langdetect` i `immutabledict` są w locku.
- lm-eval pobiera dane NLTK `punkt_tab` przy imporcie, więc instancja potrzebuje sieci; Space przygotowuje je offline.
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
