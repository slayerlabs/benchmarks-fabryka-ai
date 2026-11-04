# SQuAD 2.0 (T38)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

SQuAD 2.0 sprawdza czytanie ze zrozumieniem z pytaniami bez odpowiedzi w tekście. Zadanie lm-eval: legacy klasa `squadv2/task.py`, split `validation`, demonstracje: 0.
Metryka decyzyjna: `f1` w procentach. Typ `ciagla +proc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T38` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- Klasa legacy zostaje (prompt, żądania, `until: \n`), podmienione są zbiór i metryka: F1 i EM oficjalnego skryptu per pytanie offline (`metryki.squad_f1`) zamiast modułu `evaluate`. Próg no-answer modułu jest równy 1, a prawdopodobieństwo go nie przekracza, więc średnia jest ta sama.
- Baza i kontrola na podzbiorze HasAns (`dodatkowe.space.podzbior`), wynik pełny obok.
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
