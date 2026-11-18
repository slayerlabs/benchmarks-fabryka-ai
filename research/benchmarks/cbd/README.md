# Polish Cyberbullying Dataset (T28)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: rodzaj szkodliwości wypowiedzi, 6 klas.

- Test T28, typ `f1-korpus +klastry +pl`, klastry `TEXT` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `ptaszynski/PolishCyberbullyingDataset` @ `be3b1236598a02eff6db05ea7ac386afaabc33e8`, split `test`, n = 1000.
- Metryka decyzyjna: `f1 (makro, korpusowe)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-4.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T28` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, bez kandydata z opublikowanym wynikiem, kontrola `+pl` (model znający polski, makro-F1 parowane z bazą stałej „nieszkodliwa”); werdykt po przebiegu centralnym.
- Test: `tests/test_cbd.py`.

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a. F1 makro (`utils.agg_f1_macro`).
