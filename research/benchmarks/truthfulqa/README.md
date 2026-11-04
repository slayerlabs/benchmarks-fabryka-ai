# TruthfulQA MC2 (T35)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

TruthfulQA MC2 sprawdza czy model daje masę prawdopodobieństwa odpowiedziom zgodnym z faktami zamiast popularnym błędom. Zadanie lm-eval: `truthfulqa_mc2`, split `validation`, demonstracje: 0.
Metryka decyzyjna: `acc` = masa poprawnych opcji. Typ `masa` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T35` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- `utils.py` 0.4.9.1 przepisało MC2; liczymy wersją 6d2abda4 (`zadania.mc2_wyniki`, `metryki.mc2`). Gdy poprawne opcje stoją na początku listy, obie dają to samo (test `test_mc2_matches_lm_eval_on_true_first_labels`).
- Baza losowa: średni udział poprawnych opcji (jednakowe logliki).
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
