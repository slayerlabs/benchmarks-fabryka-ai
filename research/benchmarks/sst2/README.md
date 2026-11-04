# SST-2 (Space T21)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: sentyment zdania z recenzji filmu, 2 klasy.

- Space: T21, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `nyu-mll/glue` @ `bcdcba79d07bc864c1c254ccfcedcce55bcc9a8c`, konfiguracja `sst2`, split `validation`, n = 872.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T21` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Baza większościowa (`klasy_stale`).
