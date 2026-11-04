# ANLI R3 (Space T16)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: adwersarialne wynikanie, runda 3, 3 klasy.

- Space: T16, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `facebook/anli` @ `8e4813d81f46d313dac7892e1c28076917cfcdf9`, konfiguracja `plain_text`, split `test_r3`, n = 1200.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-nc-4.0 (NC: bramka licencyjna Space).
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T16` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Baza większościowa (`klasy_stale`).
