# LogiQA (Space T18)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: rozumowanie logiczne z egzaminów, 4 odpowiedzi.

- Space: T18, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `EleutherAI/logiqa` @ `c1eee1b2fd0ddc87777e36490f7ad54d0b97d141`, konfiguracja `logiqa`, split `test`, n = 651.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T18` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Repo z loading scriptem: dane z `refs/convert/parquet` @ `fcd80241270118cd52c96dc517dc38804025f3f5`. Prompt z `logiqa/utils_logiqa.py`.
