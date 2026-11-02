## Co zmienia ten PR

<!-- Jedno-dwa zdania: jaki benchmark albo etap, jaki wynik. -->

Refs #

## Checklista benchmarku

<!-- Usuń punkty, które nie dotyczą PR (np. PR z samą kartą oryginału). Definicja „zrobione”: README.md. -->

- [ ] Komendy z sekcji „Przed PR” w README.md kod 0 (w `research/`): bramka liczb, testy zmienionego benchmarku (z testem zgodności, jeśli jest własna implementacja), `tests/test_liczby_raportow.py`
- [ ] `ORIGINAL.md` i `REPRODUCTION.md` ze spełnionym warunkiem odtworzenia (albo `DATASET.md` z kontrolą na modelu, który zna polski)
- [ ] Kontrola tym samym kodem: pierwszy dostępny model z sekcji „Model kontrolny etapu B” w `research/METODOLOGIA.md` (benchmark polski i bez oryginału: Bielik-1.5B-v3 albo EuroLLM-1.7B), albo wprost „bez kontroli” (tylko 7 testów Space do 8.11)
- [ ] `RECIPE.md` z wpisem dla każdego wyniku w tym PR
- [ ] Każdy wynik ma n i SE, każde porównanie różnicę w SE i werdykt
- [ ] Bez wag modeli, zbiorów i plików powyżej 10 MB w commitach

Zmiany w `frontend-beta/`: komendy sprawdzające są w [`frontend-beta/README.md`](../frontend-beta/README.md).
