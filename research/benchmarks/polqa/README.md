# PolQA (open book) (T30)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: odpowiedź na pytanie z podanego ustępu, generacja do 50 tokenów.

- Test T30, typ `ciagla +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `ipipan/polqa` @ `d78d036ef08ab3b9f4d85a2893f4d3a0c95a6f37`, konfiguracja `pairs`, split `test`, n = nieustalone (po filtrze `process_docs_open`).
- Metryka decyzyjna: `levenshtein (trafienie, gdy odległość < połowy długości złotej odpowiedzi)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-sa-4.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T30` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje z banku przykładów ([METODOLOGIA, „Przykłady few-shot”](../../METODOLOGIA.md#przykłady-few-shot)), nie z samplera YAML-a. Repo z loading scriptem: dane z `refs/convert/parquet` @ `0ba79f193fb3720dc0afa49d13c67abef786977f`, konfiguracja `pairs`, split `test` + `train` (demonstracje). Metryka importuje `Levenshtein` (pin w `tools/przebieg_centralny.sh`). `common/ewaluuj.py` nie obsługuje jeszcze generacji (zadanie generacji i nowych metryk).
