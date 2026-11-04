# MMLU (T32)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01–T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

MMLU sprawdza wiedzę akademicką: pytania z czterema opcjami z 57 przedmiotów, odpowiedź literą. Zadanie lm-eval: grupa `mmlu` (członkowie `mmlu_<przedmiot>` z `mmlu/default/`), split `test`, demonstracje: 5.
Metryka decyzyjna: `acc`, średnia przedmiotów z wagami populacji (SE W). Typ `mc +warstwy` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T32` w `common/zadania.py` i `KATALOGI`), wyników jeszcze nie ma.
Kartę oryginału i odtworzenie (`ORIGINAL.md`, `REPRODUCTION.md`) dopisuje osobne zadanie.

## Rozbieżności wobec Space

- YAML 0.4.9.1 ładuje `cais/mmlu`; `zadania.py` podmienia zbiór na `hails/mmlu_no_train` (Space).
- Demonstracje z banku Space: split `dev` ma pięć dokumentów na przedmiot, więc bank to te same dokumenty, ale w kolejności hasha (`metryki.ranking_banku`), a nie w kolejności pliku jak w lm-eval.
- Do metryk dochodzi `acc_mutual_info`, co podwaja liczbę żądań (logliki bezwarunkowe).
- Kontekst najwyżej 4096 tokenów (METHOD.md §2, §4): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
