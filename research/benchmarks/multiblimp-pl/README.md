# MultiBLiMP PL (T04)

Polski podzbiór MultiBLiMP 1.0 ([arXiv:2504.02768](https://arxiv.org/abs/2504.02768)): 3272 pary minimalne na <!-- liczba-spoza-wynikow: n_scored T04 w results.json przebiegu centralnego -->
zgodność podmiotu z orzeczeniem i imiesłowem w liczbie, osobie i rodzaju. Para jest trafiona, gdy model daje
zdaniu poprawnemu wyższe log-prawdopodobieństwo. Typ: [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy).

- Karta oryginału (etap A): [`ORIGINAL.md`](ORIGINAL.md)
- Odtworzenie (etap B, bez kontroli: nierozstrzygnięte): [`REPRODUCTION.md`](REPRODUCTION.md)
- Przepis przebiegu centralnego: [`RECIPE.md`](RECIPE.md)
- Wyniki: `../../results/central-run/multiblimp-pl/` (przebieg centralny: Slayer i cztery modele odniesienia)

Wyniki przebiegu centralnego z 03.11 policzył kod sprzed zmian z 04.11 (limit 4096 tokenów z BOS, budżet loglik jak HFLM), więc są do przeliczenia w przebiegu Slayera 1.07; bazy, SE i porównanie z b przeliczono 07.11 z próbek per pytanie bez modelu (`tools/podsumuj_ponownie.py`). <!-- liczba-spoza-wynikow: daty commitów 592c8af i 3ba8ae3 -->

Slayer 1.06 ma 98,59%. Podejrzenie, że zbiór jest w danych treningowych Slayera, jest do sprawdzenia w
[#36](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/36). <!-- liczba-spoza-wynikow: results.json przebiegu centralnego, slayer1b-1.06 -->
