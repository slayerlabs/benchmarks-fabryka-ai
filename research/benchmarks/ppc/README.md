# Polish Paraphrase Corpus (T26)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: zależność znaczeń dwóch zdań, 3 klasy literą.

- Test T26, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `sdadas/ppc` @ `073012dc81efb47b0fd66b0ab48bf06ddb62f528`, split `test`, n = 1000.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-nc-sa-4.0 (licencja niekomercyjna: liczymy i publikujemy wynik, danych nie publikujemy).
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T26` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a.
