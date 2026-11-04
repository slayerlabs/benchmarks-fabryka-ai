# BoolQ (T10)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: pytanie tak/nie do ustępu Wikipedii.

- Test T10, typ `mc +klastry` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `aps/super_glue` @ `3de24cf8022e94f4ee4b9d55a6f539891524d646`, konfiguracja `boolq`, split `validation`, n = 3270.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T10` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Baza większościowa (`klasy_stale`).

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
