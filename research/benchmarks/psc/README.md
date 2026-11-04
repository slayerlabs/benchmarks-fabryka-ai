# Polish Summaries Corpus (Space T27)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czy streszczenie pasuje do tekstu, Tak/Nie.

- Space: T27, typ `f1-korpus +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allegro/klej-psc` @ `9585582aef37e7747ef174b0ec3b74855da8bad2`, split `test`, n = 1078.
- Metryka decyzyjna: `f1 (korpusowe)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-sa-3.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T27` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje losuje sampler lm-eval (seed 1234) ze splitu few-shot YAML-a; Space bierze je z rozłącznego banku wybranego hashem (METHOD.md), więc demonstracje różnią się od Space, dopóki `common/` nie ma banku Space. F1 korpusowe jak T25; długie teksty.
