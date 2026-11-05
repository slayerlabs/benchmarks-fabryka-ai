# OpenBookQA (T08)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: pytania z przyrody szkoły podstawowej, 4 odpowiedzi.

- Test T08, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allenai/openbookqa` @ `388097ea7776314e93a529163e0fea805b8a6454`, konfiguracja `main`, split `test`, n = 500.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): unknown.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T08` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
