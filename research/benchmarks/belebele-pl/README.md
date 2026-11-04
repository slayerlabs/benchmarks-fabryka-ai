# Belebele-PL (Space T24)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czytanie ze zrozumieniem fragmentu FLORES, 4 odpowiedzi literą.

- Space: T24, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `facebook/belebele` @ `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, konfiguracja `pol_Latn`, split `test`, n = 900.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-sa-4.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T24` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Zbiór ma tylko split `test`. YAML forka bierze 5 pierwszych dokumentów testu (`fewshot_split: test`, `first_n`), więc te demonstracje byłyby też oceniane, a Space (METHOD.md §4) każe brać demonstracje z rozłącznego banku wybranego hashem i nigdy ich nie oceniać.

Decyzja (`common/ewaluuj.py`, `ustaw_bank`): demonstracje to pierwsze 5 dokumentów splitu `test` w kolejności `ranking_banku` (SHA-256 `20261028|belebele|polish_belebele_mc|support|<sha dokumentu>`), z pominięciem ocenianych. Każde pytanie dostaje te same 5 w tej kolejności; prompt i metryki zostają z YAML-a forka.

- Panel 200 (jak Space, `n_population` 900 w `results.json` Space @ `2d3d73f`): najpierw próba z wszystkich 900, potem bank z dokumentów spoza niej.
- Pełny split (przebieg centralny, `--probka pelna`): bank wybierany najpierw z całego splitu, a jego 5 dokumentów wypada z populacji i z oceny (`wybor_probki`, `wykluczone`), więc ocenianych jest 895. Inaczej się nie da: przy 900 ocenianych żadna demonstracja nie byłaby spoza oceny.

Wynik nie jest porównywalny wprost z liczbą forka (900 dokumentów, 5 pierwszych jako demonstracje, oceniane też).
