# MathQA (T19)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: zadania tekstowe z matematyki, 5 odpowiedzi.

- Test T19, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allenai/math_qa` @ `c4f1cc784c04c4957b50c97858f23893b633eea6`, konfiguracja `default`, split `test`, n = 2985.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): apache-2.0.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T19` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Repo z loading scriptem: dane z `refs/convert/parquet` @ `fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6`. Opcje z `mathqa/utils.py`.
