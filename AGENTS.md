# AGENTS.md

Krótki opis repo dla każdego, kto pisze tu kod. Szczegóły są w [`README.md`](README.md),
[`research/README.md`](research/README.md) i [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## Układ

- `research/benchmarks/<name>/`: jeden benchmark (dokumenty, kod, `results/`). Wersja polska leży w osobnym
  katalogu `research/benchmarks/<name>-pl/` z `POLISH.md`.
- `research/benchmarks/_template/`: wzór nowego benchmarku.
- `research/analyses/<name>/`: analiza na wielu benchmarkach naraz.
- `research/common/`: kod używany przez więcej niż jeden benchmark.
- `research/tools/`: bramka liczb.
- `research/results/`: liczby wygenerowane przez bramkę liczb.
- `research/tests/`: testy kodu, bez sieci i bez wag.
- `research/slayer-1b/` i `frontend-beta/`: nie ruszasz ich przy pracy nad benchmarkami.

## Gdzie co dodać

- Nowy benchmark: skopiuj `research/benchmarks/_template/` do `research/benchmarks/<name>/` (małe litery, myślnik).
  Potem idź etapami z `research/METODOLOGIA.md`.
- Analiza na wielu benchmarkach: `research/analyses/<name>/`.
- Kod trafia do `research/common/` tylko wtedy, gdy używa go więcej niż jeden benchmark. Inaczej zostaje w katalogu
  benchmarku.
- Test: `research/tests/test_<name>.py`. Dane próbki: `research/common/tests/data/<name>.jsonl`.

## Przed PR

Autor PR uruchamia w `research/` testy zmienionego benchmarku, `tests/test_liczby_raportow.py` i bramkę liczb. Każda
komenda musi zakończyć się kodem 0. Katalog `research/` nie ma CI.

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
.venv-eval/bin/python tests/test_<name>.py
.venv-eval/bin/python tests/test_<name>_zgodnosc.py   # tylko gdy benchmark ma własną implementację
.venv-eval/bin/python tests/test_liczby_raportow.py
```

Każda liczba w raporcie `.md` pod `research/` musi być w `results/LICZBY.json`. Każde porównanie ma SE i werdykt.
Liczbę spoza wyników, np. wynik z pracy, oznaczasz na końcu jej linii znacznikiem
`<!-- liczba-spoza-wynikow: skąd jest liczba -->`.

## Zasady

- Język: nazwy katalogów, plików i kod po angielsku. Dokumenty po polsku.
- Nie commitujesz wag modeli (`*.safetensors`, `*.bin`, `*.pt`, katalog `models/`), zbiorów danych (`*.parquet`,
  `*.arrow`), archiwów `*.zip` ani żadnego pliku powyżej 10 MB. Listę wykluczeń ma `research/.gitignore`.
- Wyniki per pytanie wolno commitować skompresowane, jako `results/<model>/<zadanie>.jsonl.gz`, do około 10 MB na
  plik. Potrzebuje ich test zgodności i recenzent, który odtwarza wynik. Surowe `*.jsonl` w `results/<model>/`
  zostają lokalnie (`.gitignore`).
- Pytania benchmarku nie trafiają do danych treningowych (`research/METODOLOGIA.md`, sekcja „Czystość benchmarku”).
- Siła dowodu rośnie z kosztem błędnej decyzji i jej odwrócenia, ponad minimum z bramki liczb (liczba w
  `LICZBY.json`, SE i werdykt). Sekcja „Siła dowodu” w `research/METODOLOGIA.md`.
- PR otwierasz do `main`, z `Refs #N` zadania z tego repo w opisie.
