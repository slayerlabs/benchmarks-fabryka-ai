# Belebele-PL (Space T24)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czytanie ze zrozumieniem fragmentu FLORES, 4 odpowiedzi literą.

- Space: T24, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `facebook/belebele` @ `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, konfiguracja `pol_Latn`, split `test`, n = 900.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-sa-4.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T24` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Zbiór ma tylko split `test`; YAML forka bierze 5 pierwszych dokumentów testu (`fewshot_split: test`, `first_n`), więc demonstracje są też oceniane. Space bierze je z rozłącznego banku; różnica zostaje do czasu banku Space w `common/`.
