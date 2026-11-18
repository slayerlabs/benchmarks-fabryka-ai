# Polish Summaries Corpus (T27)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czy streszczenie pasuje do tekstu, Tak/Nie.

- Test T27, typ `f1-korpus +klastry +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allegro/klej-psc` @ `9585582aef37e7747ef174b0ec3b74855da8bad2`, split `test`, n = 1078.
- Metryka decyzyjna: `f1 (korpusowe)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-sa-3.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T27` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, bez kandydata z opublikowanym wynikiem, kontrola `+pl` (model znający polski, F1 parowane z bazą stałej „Tak” po klastrach `extract_text`); werdykt po przebiegu centralnym.
- Test: `tests/test_psc.py`.

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a. F1 korpusowe jak T25; długie teksty.
