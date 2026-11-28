# MATH (T34)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

MATH sprawdza zadania konkursowe z matematyki, odpowiedź generowana. Zadanie lm-eval: grupa `hendrycks_math` (7 członków), split `test`, demonstracje: 0.
Metryka decyzyjna: `exact_match`. Typ `gen +warstwy` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T34` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Ustawienia poza YAML-em lm-eval

- Ekstraktor źródłowy: tekst między pierwszym a ostatnim `$`, bez `\boxed{}`, zostaje taki, jak w YAML-u lm-eval (wpis `T34` w `common/zadania.py` go nie podmienia).
- YAML-e 6d2abda4 i 0.4.9.1 różnią się tylko białym znakiem przed `doc_to_text`.
- Kontekst najwyżej 4096 tokenów ([METODOLOGIA, „Ustawienia przebiegu centralnego”](../../METODOLOGIA.md#ustawienia-przebiegu-centralnego)): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
