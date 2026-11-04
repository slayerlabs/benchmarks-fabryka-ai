# Polish Cyberbullying Dataset (Space T28)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: rodzaj szkodliwości wypowiedzi, 6 klas.

- Space: T28, typ `f1-korpus +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `ptaszynski/PolishCyberbullyingDataset` @ `be3b1236598a02eff6db05ea7ac386afaabc33e8`, split `test`, n = 1000.
- Metryka decyzyjna: `f1 (makro, korpusowe)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-4.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T28` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje losuje sampler lm-eval (seed 1234) ze splitu few-shot YAML-a; Space bierze je z rozłącznego banku wybranego hashem (METHOD.md), więc demonstracje różnią się od Space, dopóki `common/` nie ma banku Space. F1 makro (`utils.agg_f1_macro`).
