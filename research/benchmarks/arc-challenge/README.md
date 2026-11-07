# ARC-Challenge (T02)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Pytania przyrodnicze ze szkolnych testów, cztery opcje, część trudna (ARC-Challenge). lm-eval `0.4.9.1`, zadanie
`arc_challenge`, 0-shot, zbiór `allenai/ai2_arc` @ `210d026faf9955653af8916fad021475a3f00453` (konfiguracja
`ARC-Challenge`), split `test`, metryka decyzyjna `acc_norm`.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, werdykt: bez kontroli: nierozstrzygnięte.
- [`RECIPE.md`](RECIPE.md): przepis przebiegu centralnego.
- Test: [`tests/test_arc_challenge.py`](../../tests/test_arc_challenge.py).
- Wyniki: [`results/central-run/arc-challenge/`](../../results/central-run/arc-challenge/) (przebieg centralny).

Wyniki przebiegu centralnego z 03.11 policzył kod sprzed zmian z 04.11 (limit 4096 tokenów z BOS, budżet loglik jak HFLM), więc są do przeliczenia w przebiegu Slayera 1.07; bazy, SE i porównanie z b przeliczono 07.11 z próbek per pytanie bez modelu (`tools/podsumuj_ponownie.py`). <!-- liczba-spoza-wynikow: daty commitów 592c8af i 3ba8ae3 -->
