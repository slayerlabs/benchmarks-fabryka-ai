## Co zmienia ten PR

<!-- Jedno-dwa zdania: jaki benchmark albo etap, jaki wynik. -->

Refs #

## Checklista benchmarku

<!-- Usuń punkty, które nie dotyczą PR (np. PR z samą kartą oryginału). Definicja „zrobione”: research/METODOLOGIA.md. -->

- [ ] Komendy z sekcji „Przed PR” w CONTRIBUTING.md kod 0 (w `research/`): bramka liczb, testy zmienionego benchmarku (z testem zgodności, jeśli jest własna implementacja), `tests/test_liczby_raportow.py`
- [ ] `ORIGINAL.md` i `REPRODUCTION.md` ze spełnionym warunkiem odtworzenia (albo `DATASET.md` z kontrolą na modelu, który zna polski)
- [ ] Wiersz testu w `research/README.md`, „Benchmarki i typy” (karta linkuje do niego, nie powtarza typu) i kontrola tym samym kodem według kolumny „kontrola” tego typu, albo „bez kontroli” ze zgodnością kodu
- [ ] `RECIPE.md` z wpisem dla każdego wyniku w tym PR
- [ ] Każdy wynik ma n i SE, każde porównanie różnicę w SE i werdykt
- [ ] Bez wag modeli, zbiorów i plików powyżej 10 MB w commitach
