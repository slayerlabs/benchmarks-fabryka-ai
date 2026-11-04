# 8tags (T23)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: kategoria tematyczna tytułu, 8 klas.

- Test T23, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `sdadas/8tags` @ `82ddf9c0d06ffc982aeccf2473b7ce31f2167adf`, split `test`, n = 4372.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-nc-sa-4.0 (NC: bramka licencyjna Space).
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T23` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a.
