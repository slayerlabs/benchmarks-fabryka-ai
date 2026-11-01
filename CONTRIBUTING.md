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
   Dopóki pracujesz, PR jest w trybie **Draft** (`gh pr create --draft`), a zadanie stoi w In Progress. Gdy
   komendy z punktu 2 kończą się kodem 0 i ktoś inny może PR przejąć, kliknij **Ready for review** (`gh pr ready`)
   i przestaw zadanie na Review.
   Piszesz `Refs`, a nie `Closes`, bo issue zamyka przestawienie zadania na Done na tablicy. Na Done przestawia je
   recenzent, a przy ścieżce „bez recenzji” autor po scaleniu PR.
4. Recenzja (ścieżki „recenzja” i „recenzja i przeliczenie”, akapit „Ścieżka sprawdzenia” niżej) ma dwa kroki. Najpierw recenzent sprawdza, że komendy z punktu 2 kończą się kodem 0. Potem osoba, która
   zna ten kod, odtwarza co najmniej jeden wynik z `RECIPE.md`. Wynik z etykietą `needs-recheck` liczy od zera druga
   osoba, na innym sprzęcie.

**PR z samą kartą (etap A)** ma krótszą drogę, opisaną w wariancie „Sama karta” sekcji
[„Przed PR”](README.md#przed-pr).

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

**Ścieżkę sprawdzenia** podaje każde zadanie w linii „Sprawdzenie:”. Siłę sprawdzenia dobiera się do kosztu błędu
(METODOLOGIA, sekcja „Siła dowodu”):

- **bez recenzji**: In Progress → Done po scaleniu PR. Automaty z „Przed PR” kończą się kodem 0. Tylko gdy zadanie
  podaje tę ścieżkę wprost i zmiana nie dotyka żadnej liczby. Przykład: poprawka linku albo literówki w dokumentacji.
- **recenzja**: In Progress → Review → Done. Jedna osoba sprawdza. To domyślna ścieżka, także gdy zadanie jej nie
  podaje. Przykład: karta oryginału.
- **recenzja i przeliczenie** (etykieta `needs-recheck`): In Progress → Review → Independent Check → Done. Druga osoba
  liczy wynik od zera. Dla wyniku, który idzie do Space albo do decyzji o treningu.

## Jak piszemy zadania

Zadanie mówi, co ma powstać, a nie jak to zrobić krok po kroku. Ma pięć części:

1. **Cel**: jedno zdanie, po co jest zadanie i jaka decyzja zależy od wyniku.
2. **Co zrobić**: rodzaj pracy i odesłanie do sekcji METODOLOGII. Sposób wykonania opisuje metodologia, nie zadanie.
3. **Dane wejściowe**: tylko fakty potrzebne do startu, każdy z linkiem do źródła. Liczba w zadaniu jest dokładna, nie
   zaokrąglona z abstraktu.
4. **Gotowe**: sprawdzalne kryteria, w tym automaty z kodem 0.
5. **Sprawdzenie**: jedna z trzech ścieżek wyżej.

Nie podpowiadaj w zadaniu rozstrzygnięć, które należą do metodologii, także jako przykładu w nawiasie. Gdy zadanie i
metodologia mówią co innego, autor robi według zadania, a błąd poprawiamy w metodologii albo w zadaniu, nie u
autora.

## Pliki w repo

- Dokumenty piszesz po polsku. Nazwy katalogów, plików i kod piszesz po angielsku.
- Nie commitujesz wag modeli (`*.safetensors`, `*.bin`, `*.pt`, katalog `models/`), zbiorów danych (`*.parquet`,
  `*.arrow`), archiwów `*.zip` ani żadnego pliku powyżej 10 MB.
- Wyniki per pytanie wolno commitować skompresowane, jako `results/<model>/<zadanie>.jsonl.gz`, do około 10 MB na
  plik. Surowe `*.jsonl` zostają na Twoim komputerze, bo wyklucza je `.gitignore`.
