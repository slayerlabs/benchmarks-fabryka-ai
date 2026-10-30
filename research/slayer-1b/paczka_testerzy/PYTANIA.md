# Zadania do policzenia samodzielnie

Licz wyłącznie z plików w `dane/` (opis pól: `INSTRUKCJA.md`). Nie podajemy żadnych
oczekiwanych wartości. Przy remisie w argmax wybieraj niższy indeks i napisz, że tak robisz
(albo jaką regułę przyjąłeś).

Dla każdego modelu (`slayer-1.06`, `pythia-1b`) i każdego pliku:

a) **Rozkład wyborów w mc.** Dla każdego pliku `*_mc*`: ile razy model wybrał każdą pozycję
   (A, B, C, …) jako argmax `ll`, obok rozkładu poprawnych odpowiedzi (`gold`) w tym samym pliku.
   Liczby bezwzględne i udziały.

b) **Accuracy w mc**: odsetek pytań, w których argmax `ll` == `gold`.

c) **Cloze** (pliki `*_cloze`): trzy reguły wyboru i ich accuracy:
   - `acc` — argmax `ll`,
   - `acc_norm` — argmax `ll / bajty`,
   - `PMI` — argmax `ll − bezw` (tylko tam, gdzie `bezw` nie jest `null`).
   Jeśli chcesz, dodatkowo `ll / znaki` i `ll / ntok` — podpisz, która normalizacja jest która.

d) **Bazy odniesienia** dla każdego pliku: baza losowa (średnio 1/k) i baza większościowa
   (zawsze wybierana najczęstsza pozycja `gold` w tym pliku). Także rozkład wyborów w cloze po
   pozycjach, jeśli uznasz za przydatny.

e) **Błąd standardowy** każdego accuracy (napisz wzór; np. sqrt(p(1−p)/n) albo bootstrap).

f) **Slayer vs Pythia** na tych samych `id`: różnica accuracy z niepewnością, oraz liczba pytań
   dobrze u jednego / źle u drugiego (w obie strony); test, który uznasz za właściwy.

g) **Dowolne inne obserwacje**: np. `arc_c_mc_przes` vs `arc_c_mc` (czy wybór idzie za treścią,
   czy za pozycją), `arc_c_mc_bezspacji`, `arc_c_mc_5shot`, `multiblimp` (accuracy pary =
   `ll[0] > ll[1]`), wpływ długości odpowiedzi, cokolwiek uznasz za podejrzane w danych.

## Co oddać

1. Tabelę liczb (CSV albo Markdown) dla punktów a–f, z `n` przy każdej liczbie.
2. Kod, którym je policzyłeś (skrypt albo notebook), uruchamialny na tej paczce.
3. Wynik `shasum -a 256 -c SHA256SUMS` z początku pracy.
4. Krótki opis przyjętych założeń (remisy, wzór błędu, test w punkcie f).
