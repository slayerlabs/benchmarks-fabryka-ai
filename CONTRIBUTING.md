# Jak współtworzyć

## Kontakt

Rozmawiamy na Discordzie, na kanale **#bench-team**: https://discord.gg/HnTkVR4c5T. Na start napisz tam do LoIlita
albo Elwenora i podaj swój login GitHub. Dodadzą Cię do zespołu Benchmark Team. Wtedy możesz brać zadania, przesuwać
karty na tablicy i pushować gałęzie.

Na tym samym kanale zadajesz pytania. Tam też piszesz, gdy coś nie działa albo w dokumentacji czegoś brakuje. Podaj
krok, w którym utknąłeś, i czego zabrakło. Wystarczy jedno zdanie. Opiekunowie to osoby z sekcji
[„Kto jest kim”](README.md#kto-jest-kim) w README.

## Pierwsze zadanie

Wybierz zadanie, przypisz się do niego (Assignees → Assign yourself) i przestaw je na tablicy na In Progress.
Bierzesz jedno zadanie naraz. Jeśli zaczynasz, weź zadanie z etykietą `good first issue`
([lista w tym repo](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22)).
Takie zadanie nazywa się „Karta oryginału: <benchmark>”. Piszesz w nim kartę oryginału jednego benchmarku, czyli plik
`ORIGINAL.md` (etap A). Zajmuje to około 2 h.

Recenzję cudzej karty możesz wziąć, gdy masz już za sobą jedną własną kartę.

Wszystkie zadania są pod adresem https://github.com/slayerlabs/benchmarks-fabryka-ai/issues. Tablica jest pod
adresem https://github.com/orgs/slayerlabs/projects/10. Jak przygotować komputer, opisuje
[`research/README.md`, „Przygotowanie (raz)”](research/README.md#przygotowanie-raz). Procedurę pracy opisuje
[`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## PR

1. Załóż gałąź od `main`. Nazwij ją `research/<name>` (benchmark) albo `docs/<temat>`. Możesz też otworzyć PR z
   forka. Wtedy nie potrzebujesz prawa zapisu w repo.
2. Przed PR (poza PR z samą kartą, wariant niżej) uruchom w `research/` testy zmienionego benchmarku, `tests/test_liczby_raportow.py` i bramkę liczb.
   Katalog `research/` nie ma CI, więc robisz to sam. Każda komenda musi zakończyć się kodem 0:

   ```bash
   .venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
   .venv-eval/bin/python tests/test_<name>.py
   .venv-eval/bin/python tests/test_<name>_zgodnosc.py   # tylko gdy benchmark ma własną implementację
   .venv-eval/bin/python tests/test_liczby_raportow.py
   ```

3. Otwórz PR do `main` i wypełnij checklistę z szablonu. W opisie wpisz `Refs #N` z numerem zadania z tego repo.
   Piszesz `Refs`, a nie `Closes`, bo zadanie zamyka recenzent.
4. Recenzja ma dwa kroki. Najpierw recenzent sprawdza, że komendy z punktu 2 kończą się kodem 0. Potem osoba, która
   zna ten kod, odtwarza co najmniej jeden wynik z `RECIPE.md`. Wynik z etykietą `needs-recheck` liczy od zera druga
   osoba, na innym sprzęcie.

**PR z samą kartą (etap A)** ma krótszą drogę. Przed PR wystarczy bramka liczb z kodem 0, bez testów benchmarku:

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
```

Recenzent nie odtwarza `RECIPE.md`. Sprawdza u źródła prompt, ocenę, wynik referencyjny i bazy, a przy „brak” albo
„nieustalone” listę przeszukanych miejsc.

## Etykiety

- `good first issue`: tylko zadania „Karta oryginału: <benchmark>” (etap A, około 2 h).
- `research`: zadanie badawcze, np. benchmark, pomiar albo analiza.
- `dev`: zadanie techniczne, np. kod wspólny, narzędzia albo CI.
- `needs-recheck`: wynik trafi dalej, do Space albo do decyzji o treningu. Dlatego musi przejść niezależne
  sprawdzenie.

## Tablica

Tablica zadań jest pod adresem https://github.com/orgs/slayerlabs/projects/10. Zadanie przechodzi przez kolumny
Status w tej kolejności:

1. **Backlog**: zadanie czeka i jeszcze nie można go brać.
2. **Ready**: zadanie można brać.
3. **In Progress**: ktoś je robi. Przestawiasz je tu sam, gdy się do niego przypiszesz.
4. **Review**: pierwsze sprawdzenie.
5. **Independent Check**: drugie, niezależne sprawdzenie.
6. **Done**: zrobione.

Pola zadania:

- **Czas**: ile pracy zajmie zadanie. Wartości to „do 2 h”, „do 1 dnia” albo „kilka dni”.
- **Rodzaj**: „Kroki podane” albo „Do zbadania”. „Kroki podane” znaczy, że wystarczy wykonać rozpisane kroki. „Do
  zbadania” znaczy, że sposób wykonania trzeba najpierw ustalić samemu.
- **Obszar**: Dane, Architektura i uczenie, Systemy treningu, Infrastruktura albo Ewaluacja i pomiar.

## Pliki w repo

- Dokumenty piszesz po polsku. Nazwy katalogów, plików i kod piszesz po angielsku.
- Nie commitujesz wag modeli (`*.safetensors`, `*.bin`, `*.pt`, katalog `models/`), zbiorów danych (`*.parquet`,
  `*.arrow`), archiwów `*.zip` ani żadnego pliku powyżej 10 MB.
- Wyniki per pytanie wolno commitować skompresowane, jako `results/<model>/<zadanie>.jsonl.gz`, do około 10 MB na
  plik. Surowe `*.jsonl` zostają na Twoim komputerze, bo wyklucza je `.gitignore`.
