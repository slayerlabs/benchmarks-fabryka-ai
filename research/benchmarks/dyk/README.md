# CzyWiesz (DYK) (T25)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czy podana odpowiedź pasuje do pytania, Tak/Nie.

- Test T25, typ `f1-korpus +klastry +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allegro/klej-dyk` @ `dd7c3c3bb336738c853ea17c64b85d876e6714a9`, split `test`, n = 1029.
- Metryka decyzyjna: `f1 (korpusowe)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-sa-3.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T25` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a. Metryka główna to F1 korpusowe (`utils.agg_f1` forka na parach indeksów opcji, klasa pozytywna „Tak”), liczone w `common/ewaluuj.py` (`funkcja_korpusowa`); `utils.f1` forka nie jest wołane ([`ORIGINAL.md`](ORIGINAL.md), pole „Ocena”).
