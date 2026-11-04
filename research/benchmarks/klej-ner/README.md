# KLEJ NKJP-NER (Space T29)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: rodzaj nazwy własnej w zdaniu, 6 klas.

- Space: T29, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allegro/klej-nkjp-ner` @ `bfae4047738b985bc2ad533d339dd89c3f7de00d`, split `test`, n = 2058.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): unknown.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T29` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje losuje sampler lm-eval (seed 1234) ze splitu few-shot YAML-a; Space bierze je z rozłącznego banku wybranego hashem (METHOD.md), więc demonstracje różnią się od Space, dopóki `common/` nie ma banku Space.
