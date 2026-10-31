# Jak współtworzyć

## Kontakt

Discord, kanał **#bench-team**: https://discord.gg/HnTkVR4c5T. Tam pytasz, ogłaszasz, że bierzesz zadanie, i
zgłaszasz potknięcia: jednym zdaniem, w którym kroku i czego brakuje. Dostęp do repo daje Elwenor (koordynacja
zespołu): napisz mu na Discordzie swój nick GitHub. Wyniki do Space wgrywa Arek (właściciel modelu Slayer i Space).

## Pierwsze zadanie

Weź zadanie z etykietą `good first issue`
([lista w tym repo](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22)).
To karta oryginału jednego benchmarku (zadanie „Karta oryginału: <benchmark>”, plik `ORIGINAL.md`, etap A, około 2 h,
bez GPU). Przypisz się do zadania, zanim zaczniesz; jedno zadanie naraz. Recenzję cudzej karty bierzesz, gdy masz już
za sobą jedną własną kartę. Wszystkie zadania:
https://github.com/slayerlabs/benchmarks-fabryka-ai/issues, tablica: https://github.com/orgs/slayerlabs/projects/10.
Przygotowanie komputera: [`research/README.md`, „Przygotowanie (raz)”](research/README.md#przygotowanie-raz).
Procedura: [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## PR

1. Gałąź od `main`, nazwa `research/<name>` (benchmark) albo `docs/<temat>`.
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

Dokumenty piszesz po polsku, nazwy katalogów, plików i kod po angielsku. Wag modeli, zbiorów i plików powyżej 10 MB
nie commitujesz; wyniki per pytanie jako `.jsonl.gz` do około 10 MB na plik wolno ([`AGENTS.md`](AGENTS.md), „Zasady”).
