# HellaSwag (T05)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: dokończenie opisu sytuacji, 4 zakończenia.

- Test T05, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `Rowan/hellaswag` @ `218ec52e09a7e7462a5400043bb9a69a41d06b76`, split `validation`, n = 10042.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): unknown.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T05` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- Etap B i C, własny przebieg na vast.ai: [`REPRODUCTION.md`](REPRODUCTION.md), liczby w [`results/HELLASWAG.md`](results/HELLASWAG.md).

`process_docs` z `hellaswag/utils.py` zainstalowanego lm-eval.

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).

EuroLLM 10-shot, n = 10042: `acc_norm` 0,6074 (SE 0,0049). Karta modelu podaje 0,6057 bez nazwy metryki. Różnica `acc_norm` to 0,0017, a `acc` to 0,4534, więc liczba z karty pasuje do `acc_norm`. Warunek ±0,02 jest spełniony.

Slayer 1.06, ten sam kod i te same pytania: `acc_norm` 0,3953 (SE 0,0049). Wobec EuroLLM różnica −0,2121, SE 0,0045, z = −46,83, pewne. Baza losowa 0,25. Baza większościowa 0,2573.

Zgodność ze Space jest niepotwierdzona: skład panelu 200 jest niesprawdzony.
