# Jak współtworzyć

## Kontakt

Discord, kanał **#bench-team**: https://discord.gg/HnTkVR4c5T. Tam pytasz i zgłaszasz potknięcia: jednym
zdaniem, w którym kroku i czego brakuje. Opiekunowie to osoby z sekcji
[„Kto jest kim”](README.md#kto-jest-kim) w README: Elwenor (koordynacja zespołu, dostęp do repo) i Arek (właściciel
modelu Slayer i Space, wgrywa wyniki do Space).

## Pierwsze zadanie

Weź zadanie z etykietą `good first issue`
([lista w tym repo](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22)).
To karta oryginału jednego benchmarku (zadanie „Karta oryginału: <benchmark>”, plik `ORIGINAL.md`, etap A, około 2 h,
bez GPU). Żeby wziąć zadanie, napisz w nim komentarz, że je bierzesz; opiekun przypisze Cię do zadania. Zacznij po
przypisaniu; jedno zadanie naraz. Recenzję cudzej karty bierzesz, gdy masz już
za sobą jedną własną kartę. Wszystkie zadania:
https://github.com/slayerlabs/benchmarks-fabryka-ai/issues, tablica: https://github.com/orgs/slayerlabs/projects/10.
Przygotowanie komputera: [`research/README.md`, „Przygotowanie (raz)”](research/README.md#przygotowanie-raz).
Procedura: [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## PR

1. Gałąź od `main`, nazwa `research/<name>` (benchmark) albo `docs/<temat>`. PR z forka jest dozwolony: dostęp do
   zapisu w repo nie jest potrzebny.
2. Przed PR uruchamiasz sam (CI dla `research/` nie ma) w `research/` testy zmienionego benchmarku,
   `tests/test_liczby_raportow.py` i bramkę liczb; każda komenda kończy się kodem 0:

   ```bash
   .venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
   .venv-eval/bin/python tests/test_<name>.py
   .venv-eval/bin/python tests/test_<name>_zgodnosc.py   # tylko gdy benchmark ma własną implementację
   .venv-eval/bin/python tests/test_liczby_raportow.py
   ```

3. PR do `main`; wypełnij checklistę z szablonu. W opisie `Refs #N` zadania z tego repo. `Refs`, nie `Closes`:
   zadanie zamyka recenzent.
4. Recenzja: najpierw recenzent sprawdza, że komendy z punktu 2 kończą się kodem 0, potem osoba, która zna ten kod,
   odtwarza co najmniej jeden wynik z `RECIPE.md`. Wynik z etykietą `needs-recheck` liczy druga osoba od zera na innym
   sprzęcie.

## Etykiety

- `good first issue`: tylko zadania „Karta oryginału: <benchmark>” (etap A, około 2 h, bez GPU).
- `research`: zadanie badawcze (benchmark, pomiar, analiza).
- `dev`: zadanie techniczne (kod wspólny, narzędzia, CI).
- `needs-recheck`: wynik idzie dalej (do Space albo do decyzji o treningu), więc musi przejść niezależne sprawdzenie.

## Tablica

Tablica zadań: https://github.com/orgs/slayerlabs/projects/10. Kolumny Status po kolei:

1. **Backlog**: zadanie czeka, jeszcze nie do wzięcia.
2. **Ready**: zadanie można brać.
3. **In Progress**: ktoś je robi.
4. **Review**: pierwsze sprawdzenie.
5. **Independent Check**: drugie, niezależne sprawdzenie.
6. **Done**: zrobione.

Pola zadania:

- **Czas**: ile pracy zajmie zadanie: „do 2 h”, „do 1 dnia” albo „kilka dni”.
- **Rodzaj**: „Kroki podane”, gdy wystarczy wykonać rozpisane kroki, albo „Do zbadania”, gdy sposób wykonania trzeba
  najpierw samemu ustalić.
- **Obszar**: Dane, Architektura i uczenie, Systemy treningu, Infrastruktura albo Ewaluacja i pomiar.

## Pliki w repo

- Dokumenty piszesz po polsku, nazwy katalogów, plików i kod po angielsku.
- Nie commitujesz wag modeli (`*.safetensors`, `*.bin`, `*.pt`, katalog `models/`), zbiorów danych (`*.parquet`,
  `*.arrow`), archiwów `*.zip` ani żadnego pliku powyżej 10 MB.
- Wyniki per pytanie wolno commitować skompresowane, jako `results/<model>/<zadanie>.jsonl.gz`, do około 10 MB na
  plik. Surowe `*.jsonl` zostają lokalnie (`.gitignore`).
