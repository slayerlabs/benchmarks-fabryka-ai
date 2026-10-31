# Jak współtworzyć

## Kontakt

Discord, kanał **#bench-team**: https://discord.gg/HnTkVR4c5T. Tam pytasz, ogłaszasz, że bierzesz zadanie, i
zgłaszasz potknięcia: jednym zdaniem, w którym kroku i czego brakuje. Dostęp do repo: napisz swój nick GitHub do
Elwenora.

## Pierwsze zadanie

Weź zadanie z etykietą `good first issue`. To zawsze jeden etap pracy, np. karta oryginału `ORIGINAL.md` jednego
benchmarku (około 2 h, bez GPU), albo recenzja cudzej karty. Przypisz się do zadania, zanim zaczniesz; jedno zadanie
naraz. Przygotowanie komputera: [`research/README.md`, „Przygotowanie (raz)”](research/README.md#przygotowanie-raz).
Procedura: [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## PR

1. Gałąź od `main`, nazwa `research/<name>` (benchmark) albo `docs/<temat>`.
2. Przed PR: bramka liczb i testy zmienionych plików z kodem 0
   ([komendy](research/README.md#bramka-liczb)).
3. PR do `main`; wypełnij checklistę z szablonu. W opisie `Refs #N` zadania (dla zadania w innym repo: `Refs
   właściciel/repo#N`). `Refs`, nie `Closes`: zadanie zamyka recenzent.
4. Recenzja: najpierw automaty (bramka liczb, testy, test zgodności), potem osoba, która zna ten kod, odtwarza co
   najmniej jeden wynik z `RECIPE.md`. Wynik z etykietą `needs-recheck` liczy druga osoba od zera na innym sprzęcie.

## Etykiety

- `good first issue`: pierwsze zadanie, jeden etap, do 2 h, dokładne kroki.
- `research`: zadanie badawcze (benchmark, pomiar, analiza).
- `dev`: zadanie techniczne (kod wspólny, narzędzia, CI).
- `needs-recheck`: wynik idzie dalej (do Space albo do decyzji o treningu), więc musi przejść niezależne sprawdzenie.

Dokumenty piszesz po polsku, nazwy katalogów, plików i kod po angielsku. Wag modeli, zbiorów i dużych plików nie
commitujesz.
