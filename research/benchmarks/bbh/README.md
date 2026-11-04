# BIG-Bench Hard (T47)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

BIG-Bench Hard sprawdza rozumowanie formalne w 27 zadaniach, odpowiedź bezpośrednia. Zadanie lm-eval: grupa `bbh_fewshot` (27 członków), split `test`, demonstracje: 3 (źródłowe).
Metryka decyzyjna: `exact_match` po obcięciu białych znaków odpowiedzi. Typ `gen +warstwy` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T47` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- Demonstracje źródłowe z YAML-a, bez banku (METHOD.md).
- Odpowiedź obcięta z obu stron przed porównaniem (METHOD.md); wartość dosłowna lm-eval zostaje diagnostycznie w `dodatkowe.space.zrodlowa_doslowna`.
- YAML 0.4.9.1 ładuje `SaylorTwift/bbh`; `zadania.py` podmienia zbiór na `lukaemon/bbh`.
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
