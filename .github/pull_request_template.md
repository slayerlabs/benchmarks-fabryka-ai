## Co zmienia ten PR

<!-- Jedno-dwa zdania: jaki benchmark albo etap, jaki wynik. -->

Refs #

## Checklista benchmarku

<!-- Usuń punkty, które nie dotyczą PR (np. PR z samą kartą oryginału). Definicja „zrobione”: README.md. -->

- [ ] Bramka liczb kod 0: `.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py` (w `research/`)
- [ ] Testy zmienionych plików kod 0: `.venv-eval/bin/python tests/test_<name>.py`, także test zgodności, jeśli jest własna implementacja
- [ ] `ORIGINAL.md` i `REPRODUCTION.md` ze spełnionym warunkiem odtworzenia (albo `DATASET.md` z kontrolą na modelu, który zna polski)
- [ ] Kontrola na `EleutherAI/pythia-1b-v0` @ `step143000` tym samym kodem
- [ ] `RECIPE.md` z wpisem dla każdego wyniku w tym PR
- [ ] Każdy wynik ma n i SE, każde porównanie różnicę w SE i werdykt
- [ ] Bez wag modeli, zbiorów i dużych plików w commitach

Zmiany w `frontend-beta/`: komendy sprawdzające są w [`frontend-beta/README.md`](../frontend-beta/README.md).
