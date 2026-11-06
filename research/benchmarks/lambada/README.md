# LAMBADA (T17)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: przewidzenie ostatniego słowa fragmentu powieści, które da się odgadnąć tylko z szerszego kontekstu.

- Test T17, typ `cloze` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `EleutherAI/lambada_openai` @ `900124bf3b8235c6daf21033af9948b3f07346c4`, konfiguracja `default`, split `test`, n = 5153. <!-- liczba-spoza-wynikow: ORIGINAL.md, pole „Dane: split w pracy” -->
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): `mit`; licencja autorów zbioru: CC BY 4.0.
- Definicja zadania: lm-eval `lambada_openai`, `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`).
- Przebieg centralny: podpięty (`T17` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- Etap B (`REPRODUCTION.md`): jeszcze go nie ma.

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
