# GSM8K (T33)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

GSM8K sprawdza zadania tekstowe z arytmetyki szkolnej, odpowiedź generowana po `#### `. Zadanie lm-eval: `gsm8k`, split `test`, demonstracje: 5.
Metryka decyzyjna: `exact_match`, filtr `strict-match`. Typ `gen` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T33` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- Katalog zadania identyczny w 6d2abda4 i 0.4.9.1 (mapa braków).
- Demonstracje: pięć pierwszych dokumentów `train` w kolejności hasha, te same dla każdego pytania; lm-eval losuje je per pytanie (seed 1234).
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
