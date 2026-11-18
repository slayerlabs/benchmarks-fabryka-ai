# ARC-Easy (T51)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: wybór poprawnej treści odpowiedzi w szkolnych pytaniach przyrodniczych (klasy 3–9), które proste wyszukiwanie albo współwystępowanie słów już rozwiązuje.

- Test T51, typ `mc-k` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allenai/ai2_arc` @ `210d026faf9955653af8916fad021475a3f00453`, konfiguracja `ARC-Easy`, split `test`, n = 2376. <!-- liczba-spoza-wynikow: ORIGINAL.md, pole „Dane” -->
- Metryka decyzyjna: `acc`; `acc_norm` pomocnicza.
- Licencja (karta zbioru na przypiętej rewizji): `cc-by-sa-4.0`.
- Definicja zadania: lm-eval `arc_easy.yaml` (ten sam blob w `6d2abda4` i `v0.4.9.1`), przepisana w `common/zadania.py` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`).
- Przebieg centralny: podpięty (`T51` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- Etap B: [`REPRODUCTION.md`](REPRODUCTION.md), kontrola `EleutherAI/pythia-1b-v0` @ `step143000` z przebiegu centralnego; werdykt po przebiegu.
- Test: `tests/test_arc_easy.py`.
- SNR i bazy z plików Pythii v0: [`PROTOCOL-snr-baselines.md`](PROTOCOL-snr-baselines.md), `snr_and_baselines.py`, `results/`.

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
