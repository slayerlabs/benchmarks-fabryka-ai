# RACE (high) (Space T40)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czytanie ze zrozumieniem, egzaminy szkoły średniej, 4 odpowiedzi.

- Space: T40, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `EleutherAI/race` @ `66ca2e6374282f5e35b11559e87185db911a6900`, konfiguracja `high`, split `test`, n = 1045.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T40` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Prompt z `race/preprocess_race.py`; długie artykuły.
