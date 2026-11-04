# SciQ (Space T09)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: pytania z nauk ścisłych z akapitem wsparcia, 4 odpowiedzi, poprawna zawsze ostatnia.

- Space: T09, typ `poz` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allenai/sciq` @ `2c94ad3e1aafab77146f384e23536f97a4849815`, split `test`, n = 1000.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-nc-3.0 (NC: bramka licencyjna Space).
- Definicja zadania: lm-eval `6d2abda4` (Space); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T09` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Typ `poz` wymaga drugiego przebiegu z przemieszanymi opcjami; przebieg centralny liczy tylko kolejność Space.

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
