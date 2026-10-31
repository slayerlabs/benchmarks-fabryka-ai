# AGENTS.md

Krótki opis repo dla każdego, kto pisze tu kod. Szczegóły: [`README.md`](README.md),
[`research/README.md`](research/README.md), [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## Układ

- `research/benchmarks/<name>/`: jeden benchmark (dokumenty, kod, `results/`).
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

W `research/`, oba z kodem 0:

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
.venv-eval/bin/python tests/test_<name>.py
```

Każda liczba w raporcie `.md` pod `research/` musi być w `results/LICZBY.json`; każde porównanie ma SE i werdykt.

## Zasady

- Język: nazwy katalogów, plików i kod po angielsku; dokumenty po polsku.
- Nie commitujesz wag modeli, zbiorów danych ani dużych plików (`*.safetensors`, `*.bin`, `*.pt`, `*.parquet`,
  `*.zip`, wyniki per pytanie `*.jsonl` w `results/<model>/`); zobacz `research/.gitignore`.
- Pytania benchmarku nie trafiają do danych treningowych (`research/METODOLOGIA.md`, sekcja „Czystość benchmarku”).
- PR do `main` z `Refs #N` zadania.
