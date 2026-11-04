# RTE (Space T15)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: wynikanie tekstowe, 2 klasy.

- Space: T15, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `aps/super_glue` @ `3de24cf8022e94f4ee4b9d55a6f539891524d646`, konfiguracja `rte`, split `validation`, n = 277.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T15` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Zadanie lm-eval `sglue_rte`. Baza większościowa (`klasy_stale`).
