## Co zmienia ten PR

<!-- Jedno-dwa zdania: jaki benchmark albo etap, jaki wynik. -->

Refs #

## Checklista benchmarku

<!-- Usuń punkty, które nie dotyczą PR (np. PR z samą kartą oryginału). Definicja „zrobione”: research/METODOLOGIA.md. PR z samą kartą oryginału zostawia punkt 1 (tylko bramka liczb), `ORIGINAL.md` z punktu 2 i ostatni punkt. -->

- [ ] Komendy z sekcji „Przed PR” w CONTRIBUTING.md kod 0 (w `research/`): bramka liczb, testy zmienionego benchmarku (z testem zgodności, jeśli jest własna implementacja), `tests/test_liczby_raportow.py`
- [ ] `ORIGINAL.md` i `REPRODUCTION.md` z wartością referencyjną, modelem kontrolnym i warunkiem odtworzenia albo „bez kontroli” (albo `DATASET.md`)
- [ ] Podpięty do przebiegu centralnego: wpis w `ZADANIA` (`research/common/zadania.py`) i `KATALOGI` (`research/tools/przebieg_centralny.sh`), test bez sieci sprawdza wpis
- [ ] Wiersz testu w `research/README.md`, „Benchmarki i typy” (karta linkuje do niego, nie powtarza typu)
- [ ] `RECIPE.md` z komendą przebiegu; wiersz w `research/STATUS.md` przestawiony
- [ ] Jeśli PR wnosi wynik: n i SE, każde porównanie różnicę w SE i werdykt
- [ ] Bez wag modeli, zbiorów i plików powyżej 10 MB w commitach
