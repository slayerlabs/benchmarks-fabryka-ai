# HellaSwag (Space T05)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: dokończenie opisu sytuacji, 4 zakończenia.

- Space: T05, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `Rowan/hellaswag` @ `218ec52e09a7e7462a5400043bb9a69a41d06b76`, split `validation`, n = 10042.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): unknown.
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T05` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

`process_docs` z `hellaswag/utils.py` zainstalowanego lm-eval.

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
