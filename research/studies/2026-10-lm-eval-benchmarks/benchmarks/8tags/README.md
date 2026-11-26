# 8tags (T23)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: kategoria tematyczna tytułu, 8 klas.

- Test T23, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `sdadas/8tags` @ `82ddf9c0d06ffc982aeccf2473b7ce31f2167adf`, split `test`, n = 4372.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-nc-sa-4.0 (licencja niekomercyjna: liczymy i publikujemy wynik, danych nie publikujemy).
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T23` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, bez kandydata z opublikowanym wynikiem, kontrola `+pl` (model znający polski > b + 2 SE); werdykt po przebiegu centralnym.
- Test: `tests/test_8tags.py`.

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a.
