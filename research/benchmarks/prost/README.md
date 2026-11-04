# PROST (Space T20)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: rozumowanie o własnościach fizycznych przedmiotów, 4 odpowiedzi.

- Space: T20, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `corypaik/prost` @ `b3efebf08969fc19335ba894353316878b6fa493`, konfiguracja `default`, split `test`, n = 18736.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): apache-2.0.
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T20` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Dane z `refs/convert/parquet` @ `0e475b574d98e7d79de2064252dd2fb75bcaa0a8`.
