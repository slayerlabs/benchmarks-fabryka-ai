# WSC273: przepis

Jak odtworzyć każdy wynik z [`README.md`](README.md). Wszystkie komendy uruchamiasz w `research/`. Pola, których
nie zapisano w czasie pomiaru: „nie zapisano”.

## Wspólne dla obu modeli

- Commit kodu: `53502fe` z `main` (od niego wychodzi gałąź PR) plus kod z tego PR.
- Środowisko: Python 3.12.10, `torch 2.8.0+cpu`, `transformers 4.57.6`, `tokenizers` i `numpy` z
  `common/requirements.lock.txt`, `lm_eval 0.4.9.1`, `datasets 3.6.0`. Transformers to wydanie z PyPI; commit gita nie
  jest przypięty.
- Zbiór: [`ErnestSDavis/winograd_wsc` @ `8052c534a4cecd8328c0bc879f6a5aa07404c4da`](https://huggingface.co/datasets/ErnestSDavis/winograd_wsc/tree/8052c534a4cecd8328c0bc879f6a5aa07404c4da).
  Bajty: `wsc273/test/0000.parquet` z `refs/convert/parquet` @ `24cdebf4993560f25ff220b171e40f1027f3d9e6`, git oid
  `b398b87a…`; adres jest w `lm_eval_tasks/wsc273/wsc273.yaml`.
- Zadanie: `lm_eval_tasks/wsc273/`. Katalog `lm_eval/tasks/wsc273` jest identyczny w `6d2abda4` (commit Space) i
  w `v0.4.9.1` (lock): ten sam blob `utils.py` i `default.yaml`. <!-- liczba-spoza-wynikow: wersje i commity lm-eval -->
- Ocena: `wsc273.py evaluate`, `simple_evaluate` z lm-eval, partial evaluation, 0-shot, bez szablonu czatu, bez
  obcinania kontekstu (asercja najdłuższego żądania wobec `max_length`).
- Seed: `random_seed=0`, `numpy_random_seed=1234`, `torch_random_seed=1234`, `fewshot_random_seed=1234`. Bootstrap <!-- liczba-spoza-wynikow: seedy z METHOD -->
  CI95: 10 000 powtórzeń, seed `20261028`. <!-- liczba-spoza-wynikow: parametry bootstrapu z METHOD -->
- Precyzja: float32, batch 1.
- Sprzęt: CPU, Windows 11 x86-64, bez GPU i bez płatnej instancji; model procesora i liczba wątków: nie zapisano.
- Data: 2026-11-02.
- Protokół: [`PROTOCOL-space.md`](PROTOCOL-space.md). Próbka zamrożona w [`panel200.json`](panel200.json) przed <!-- liczba-spoza-wynikow: nazwa pliku -->
  pierwszym uruchomieniem modelu. Wszystko to weszło do repo jednym commitem z wynikami, więc historia gita tej
  kolejności nie potwierdza.

Próbkę odtwarzasz bez wag:

```bash
python benchmarks/wsc273/wsc273.py panel
```

## Wynik 1: Slayer 1.06 na próbce

- Model: [`SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`](https://huggingface.co/SlayerLab/Slayer1B-1.06/tree/ef81be58742544ad32e1afab38db011fec209609), <!-- liczba-spoza-wynikow: nazwa modelu w adresie URL -->
  nakładka `common/slayer_lm.py`, znane rozbieżności nakładki: `common/RECIPE.md`.
- BOS: model nie ma `tokenizer_config.json`, a `tokenizer.json` nie ma post-processora, więc tokenizer BOS nie dodaje.
  Nakładka dodaje jeden BOS (`<|endoftext|>`) przed kontekstem. Ustalone po pomiarze z plików i kodu; log przebiegu tego
  nie zapisał.
- Komenda:

```bash
huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir <slayer-1.06 dir>
python benchmarks/wsc273/wsc273.py evaluate --model slayer-1.06 --model_path <slayer-1.06 dir> --sample panel200
```

- Wynik per pytanie: `benchmarks/wsc273/results/slayer-1.06/panel200.jsonl.gz` (hasz dokumentu, złota etykieta,
  logliki, predykcja, bez tekstu pytań). <!-- liczba-spoza-wynikow: nazwa pliku -->
- Wynik: `benchmarks/wsc273/results/wsc273.json`, klucz `slayer_panel200`. <!-- liczba-spoza-wynikow: nazwa klucza -->

## Wynik 2: Slayer 1.06 na pełnym splicie

- Model: jak w wyniku 1.
- Komenda:

```bash
python benchmarks/wsc273/wsc273.py evaluate --model slayer-1.06 --model_path <slayer-1.06 dir> --sample full
```

- Wynik per pytanie: `benchmarks/wsc273/results/slayer-1.06/full.jsonl.gz`. <!-- liczba-spoza-wynikow: nazwa modelu w ścieżce -->
- Wynik: `benchmarks/wsc273/results/wsc273.json`, klucz `slayer_pelny`.

## Wynik 3: kontrola `bigscience/bloom-560m` <!-- liczba-spoza-wynikow: nazwa modelu -->

- Model: [`bigscience/bloom-560m` @ `ac2ae5fab2ce3f9f40dc79b5ca9f637430d24971`](https://huggingface.co/bigscience/bloom-560m/tree/ac2ae5fab2ce3f9f40dc79b5ca9f637430d24971), <!-- liczba-spoza-wynikow: nazwa modelu w adresie URL -->
  `HFLM` z lm-eval.
- BOS: `tokenizer_config.json` nie ma `add_bos_token`, tokenizer BOS nie dodaje, a `HFLM` ma domyślnie
  `add_bos_token=False`, więc kontrola liczona jest bez BOS. Ustalone po pomiarze z plików i kodu; log przebiegu tego nie
  zapisał.
- Komenda:

```bash
huggingface-cli download bigscience/bloom-560m --revision ac2ae5fab2ce3f9f40dc79b5ca9f637430d24971 --local-dir <bloom-560m dir>
python benchmarks/wsc273/wsc273.py evaluate --model bloom-560m --model_path <bloom-560m dir> --sample full
```

- Wynik per pytanie: `benchmarks/wsc273/results/bloom-560m/full.jsonl.gz`. <!-- liczba-spoza-wynikow: nazwa modelu w ścieżce -->
- Wynik: `benchmarks/wsc273/results/wsc273.json`, klucz `kontrola`.

## Raport

```bash
python benchmarks/wsc273/wsc273.py report
python tools/liczby.py && python tools/sprawdz_raporty.py
python -m pytest tests/test_wsc273.py
```

`report` nie potrzebuje wag: czyta pliki per pytanie i przerywa, gdy próbka różni się od podzbioru pełnego przebiegu
albo kontrola wypada poza progiem.
