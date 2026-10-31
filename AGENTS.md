# AGENTS.md

Krótki opis repo dla każdego, kto pisze tu kod. Szczegóły: [`README.md`](README.md),
[`research/README.md`](research/README.md), [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## Układ

- `research/benchmarks/<name>/`: jeden benchmark (dokumenty, kod, `results/`); wersja polska w osobnym katalogu
  `research/benchmarks/<name>-pl/` z `POLISH.md`.
- `research/benchmarks/_template/`: wzór nowego benchmarku.
- `research/analyses/<name>/`: analiza na wielu benchmarkach naraz.
- `research/common/`: kod używany przez więcej niż jeden benchmark.
- `research/tools/`: bramka liczb. `research/results/`: liczby wygenerowane przez bramkę liczb.
- `research/tests/`: testy kodu, bez sieci i bez wag.
- `research/slayer-1b/`, `frontend-beta/`: nie ruszać przy pracy nad benchmarkami.

## Gdzie co dodać

- Nowy benchmark: skopiuj `research/benchmarks/_template/` do `research/benchmarks/<name>/` (małe litery, myślnik) i
  idź etapami z `research/METODOLOGIA.md`.
- Analiza na wielu benchmarkach: `research/analyses/<name>/`.
- Kod do `research/common/` tylko wtedy, gdy używa go więcej niż jeden benchmark; inaczej zostaje w katalogu benchmarku.
- Test: `research/tests/test_<name>.py`, dane próbki w `research/common/tests/data/<name>.jsonl`.

## Przed PR

Autor PR uruchamia w `research/` testy zmienionego benchmarku, `tests/test_liczby_raportow.py` i bramkę liczb; każda
komenda kończy się kodem 0. CI dla `research/` nie ma.

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
.venv-eval/bin/python tests/test_<name>.py
.venv-eval/bin/python tests/test_<name>_zgodnosc.py   # tylko gdy benchmark ma własną implementację
.venv-eval/bin/python tests/test_liczby_raportow.py
```

Każda liczba w raporcie `.md` pod `research/` musi być w `results/LICZBY.json`; każde porównanie ma SE i werdykt.

## Zasady

- Język: nazwy katalogów, plików i kod po angielsku; dokumenty po polsku.
- Nie commitujesz wag modeli (`*.safetensors`, `*.bin`, `*.pt`, katalog `models/`), zbiorów danych (`*.parquet`,
  `*.arrow`), archiwów `*.zip` ani żadnego pliku powyżej 10 MB; zobacz `research/.gitignore`.
- Wyniki per pytanie wolno commitować skompresowane, jako `results/<model>/<zadanie>.jsonl.gz`, do około 10 MB na
  plik: są potrzebne do testu zgodności i do odtworzenia wyniku przez recenzenta. Surowe `*.jsonl` w
  `results/<model>/` zostają lokalnie (`.gitignore`).
- Pytania benchmarku nie trafiają do danych treningowych (`research/METODOLOGIA.md`, sekcja „Czystość benchmarku”).
- PR do `main` z `Refs #N` zadania z tego repo.
