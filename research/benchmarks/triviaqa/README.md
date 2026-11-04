# TriviaQA (T43)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

TriviaQA sprawdza wiedza bez kontekstu: pytania quizowe. Zadanie lm-eval: `triviaqa`, split `validation`, demonstracje: 0.
Metryka decyzyjna: `exact_match`, filtr `remove_whitespace`. Typ `gen` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T43` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Ustawienia poza YAML-em lm-eval

- Katalog zadania identyczny w 6d2abda4 i 0.4.9.1.
- Kontekst najwyżej 4096 tokenów ([METODOLOGIA, „Ustawienia przebiegu centralnego”](../../METODOLOGIA.md#ustawienia-przebiegu-centralnego)): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
