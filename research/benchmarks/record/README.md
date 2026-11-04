# ReCoRD (T50)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

ReCoRD sprawdza uzupełnienie encji w zdaniu o artykule prasowym. Zadanie lm-eval: `record`, split `validation`, demonstracje: 0.
Metryka decyzyjna: `f1` per pytanie (max po złotych odpowiedziach). Typ `ciagla` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T50` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- Encja o najwyższym loglik; baza losowa = średnie F1 losowo wybranej encji.
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
