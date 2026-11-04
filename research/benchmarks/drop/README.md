# DROP (T39)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

DROP sprawdza czytanie z dyskretnym rozumowaniem (liczenie, porównania). Zadanie lm-eval: `drop`, split `validation`, demonstracje: 0.
Metryka decyzyjna: `f1` per pytanie lm-eval. Typ `ciagla` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T39` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- YAML-e różnią się tylko `trust_remote_code`; generacja do kropki.
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
