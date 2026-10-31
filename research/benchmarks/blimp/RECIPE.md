# BLiMP: przepis

Jak odtworzyć każdy wynik z [`README.md`](README.md) i [`results/BLIMP.md`](results/BLIMP.md). Wszystkie
komendy uruchamiasz w `research/`. Pola, których nigdzie nie zapisano w czasie pomiaru: „nie zapisano”.

## Wspólne dla obu modeli

- Commit kodu:
  - log-prawdopodobieństwa per para: policzone kodem z commitu `14af2c8` (2026-10-31, gałąź
    `research/bench-blimp`, PR #9), który dodał je jako `raw/1.06.jsonl.gz` i `raw/pythia-1b.jsonl.gz`;
    te same pliki (ten sam rozmiar w bajtach) leżą teraz w `benchmarks/blimp/results/<model>/blimp.jsonl.gz`;
  - analiza i raport: ostatni commit PR #9, `24a1651` (po 3 rundach recenzji); późniejsze zmiany kodu oceny w
    PR (wejścia dłuższe niż kontekst odrzucane, BOS Slayera jako stała) nie zmieniły głównych liczb, według opisu
    commitu `e17ea4c`;
  - obecny układ (ścieżki w komendach niżej): `a9e8410`, gałąź `research/uklad-repo`.
- Środowisko: `common/requirements.lock.txt` (`torch==2.8.0`, `transformers==4.57.6`, `tokenizers==0.22.2`,
  `numpy==2.0.2`, `lm_eval==0.4.9.1`). Transformers to wydanie z PyPI `4.57.6`; commit gita nie jest przypięty.
  Wersja Pythona w głównym przebiegu: nie zapisano (kontrola forwardu zapisała Python `3.9.6`, torch `2.8.0`,
  tokenizers `0.22.2`).
- Zbiór: [`nyu-mll/blimp` @ `877fba0801ffb7cbd8c39c1ff314a46f053f6036`](https://huggingface.co/datasets/nyu-mll/blimp/tree/877fba0801ffb7cbd8c39c1ff314a46f053f6036)
  (67 plików parquet, split `train`), czytany z `BLIMP_DIR` albo cache HF; sha256 plików: nie zapisano.
- Ocena: `hipoteza_formatu.py licz --zadania blimp`: pusty kontekst, `" " + sentence`, jeden nieoceniany token
  prefiksu, suma log-prawdopodobieństw; remis liczy się jako trafienie; bez obcinania.
- Seed: ocena jest deterministyczna (bez losowania). Seed `20261028` służy do bootstrapu CI95 (10 000
  powtórzeń, losowanie par wewnątrz każdego paradygmatu), haszu panelu i losowania paneli (20 000).
- Precyzja: float32 (model ładowany z `torch_dtype=torch.float32`).
- Sprzęt: Apple MPS (macOS, arm64), batch 64 z dopełnieniem z prawej; dokładny układ (chip): nie zapisano.
  Kontrola forwardu działała na CPU (`macOS-26.6-arm64-arm-64bit`), batch 1.
- Data: 2026-10-31 (progi zacommitowane przed wynikami w `d7b72a9`, wyniki w `14af2c8`).
- Progi zapisane przed pomiarem: [`THRESHOLDS.md`](THRESHOLDS.md).

## Wynik 1: Slayer 1.06

- Model: [`SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`](https://huggingface.co/SlayerLab/Slayer1B-1.06/tree/ef81be58742544ad32e1afab38db011fec209609), <!-- liczba-spoza-wynikow: nazwa modelu w adresie URL -->
  forward z `common/slayer_model.py`, token prefiksu `<|endoftext|>` (BOS).
- Komenda:

```bash
huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir <slayer-1.06 dir>
BLIMP_DIR=<snapshot> python common/hipoteza_formatu.py licz --model <slayer-1.06 dir> --zadania blimp \
  --wyjscie <out>/1.06 --device mps --batch 64
```

- Wynik per para: `benchmarks/blimp/results/1.06/blimp.jsonl.gz` (identyfikatory i log-prawdopodobieństwa, bez
  zdań).

## Wynik 2: Pythia-1B v1 (porównanie, nie kontrola etapu B)

- Model: [`EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`](https://huggingface.co/EleutherAI/pythia-1b/tree/f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2)
  (wagi v1), transformers, kodowanie par jak w lm-eval HFLM (prefiks `<|endoftext|>`).
- Komenda:

```bash
huggingface-cli download EleutherAI/pythia-1b --revision f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2 --local-dir <pythia-1b dir>
BLIMP_DIR=<snapshot> python common/hipoteza_formatu.py licz --model <pythia-1b dir> --zadania blimp \
  --wyjscie <out>/pythia-1b --device mps --batch 64
```

- Wynik per para: `benchmarks/blimp/results/pythia-1b/blimp.jsonl.gz`.
- Uwaga: opublikowana wartość, z którą go porównujemy, dotyczy innego modelu (`EleutherAI/pythia-1b-v0` @
  `step143000`), patrz [`REPRODUCTION.md`](REPRODUCTION.md).

## Wynik 3: kontrola oficjalnego forwardu (`results/kontrola_forward.json`)

- Model: to samo repo i ta sama rewizja Slayera, oficjalny `load_slayer.py`, CPU float32, batch 1; potrzebne
  pliki repo HF razem z wagami.
- Komenda:

```bash
BLIMP_DIR=<snapshot> python benchmarks/blimp/kontrola_forward.py --model <slayer-1.06 dir> \
  --wyniki <out>/1.06/blimp.jsonl --watki 1,6 --sumy float32,float64
```

## Agregaty i raport

```bash
BLIMP_DIR=<snapshot> python benchmarks/blimp/blimp.py zbierz --wyniki <out>
python tools/liczby.py && python benchmarks/blimp/blimp.py raport && python tools/sprawdz_raporty.py
```

Bez wag `blimp.json` odbudujesz z zapisanych plików per para:
`BLIMP_DIR=<snapshot> python benchmarks/blimp/blimp.py zbierz --wyniki benchmarks/blimp/results`.

## Wynik 4: BLiMP po checkpointach treningu i uśrednianie wag (`results/CHECKPOINTS.md`)

- Commit kodu: pomiar liczony kodem z gałęzi `research/bench-blimp` w dawnym układzie `research/slayer-1b/`
  (commity lokalne, nie było ich na GitHubie; ten PR przenosi je w obecny układ). Kolejność: protokół i progi
  `8effddf` (2026-10-31 14:08 CET), kod pomiaru i testy `be98bc9` (14:27), poprawka 1 protokołu, cięcie zakresu
  przed odczytem trafności `bf8aa50` (15:01), wyniki `ba557c7` (15:46), dwie rundy poprawek po weryfikacji
  `cd583e0` (16:21) i `0935e13` (16:38). Pliki per para i held-out przeniesione bez zmian (te same sha256, zapisane
  w `results/checkpoints.json`, pole `sha256_surowych`).
- Protokół i progi zapisane przed pomiarem: [`results/CHECKPOINTS_THRESHOLDS.md`](results/CHECKPOINTS_THRESHOLDS.md).
- Ocena: jak w wyniku 1 (`common/hipoteza_formatu.py licz --zadania blimp`), float32, TF32 wyłączone
  (`NVIDIA_TF32_OVERRIDE=0`), batch 64 z dopełnieniem z prawej, `--device cuda`.
- Sprzęt: vast.ai, trzy instancje: NVIDIA A100-SXM4-40GB, NVIDIA L40S, NVIDIA GeForce RTX 4090; torch
  `2.6.0+cu124`, CUDA `12.4` (pliki `results/checkpoints/environment_<gpu>.json`). Pythia-1B i kontrola urządzenia
  1.06 to pliki z MPS z wyniku 1 i 2 (bez ponownej oceny).
- Checkpointy (pliki trenera `ckpt_<krok>.pt`, rewizja repo HF w chwili pobrania, sha256 każdego pliku zgodny z
  identyfikatorem LFS, zapis w `results/checkpoints/times_<gpu>.jsonl`, etap `pobranie`):

| krok | repo | rewizja | GPU |
|---:|---|---|---|
| 1430 | `SlayerLab/Slayer1B-1.00-checkpoints` | `950a62a9d30b522c65bd76931157cef7929f3113` | A100 |
| 2860 | `SlayerLab/Slayer1B-1.01-checkpoints` | `fd7e55d177c162b3d8f6677d833a34e05afe7275` | A100 |
| 7150 | `SlayerLab/Slayer1B-1.03-checkpoints` | `b8ac4d483204b6d00acade3af2d8bfec95f84bce` | L40S |
| 8600, 10010 | `SlayerLab/Slayer1B-1.04-checkpoints` | `14b5a8ccb60ac79570593e3410124c7edb879780` | L40S |
| 13400-13848 (krok 13848 i średnie avg3, avg5, avg10) | `SlayerLab/Slayer1B-1.06-checkpoints` | `1113e3e657c1e82d0da09c1fb6d08a356edb8aa3` | RTX 4090 (krok 13848 i avg3 też na A100 i L40S) |

- Nie zaraportowane (poprawka 1, przed odczytem trafności): 5720 (A100, `1.02`, rewizja
  `177fe19f9b6583713be0590d06fd4eeba802b8af`) i 11450 (L40S, `1.04`) przerwane w trakcie BLiMP, 12870 niepobrany.
- Konwersja checkpointu na wagi: `slayer-1b/wygaszanie/konwertuj.py` (klucze i kształty z wag Slayera 1.06
  `ef81be58742544ad32e1afab38db011fec209609`). Średnie wag: `benchmarks/blimp/average_weights.py`, suma w float64,
  zapis w float32.
- Held-out: okna z `slayer-1b/wygaszanie/dane.py` i strata z `slayer-1b/wygaszanie/heldout.py`, te same okna co
  w przebiegu wygaszania LR (`slayer-1b/wygaszanie/wyniki/heldout_*.json`).
- Seed: ocena deterministyczna; bootstrap nachylenia i różnic: 2000 powtórzeń (`BOOT` w `checkpoints.py`).
- Data: 2026-10-31.

Etapy skryptu na instancji (kod w `/workspace/kod` = `research/`). Dokładne komendy każdej instancji, w tym kroki
uruchomione ręcznie na RTX 4090 po cięciu zakresu: `results/CHECKPOINTS.md`, sekcja „How to reproduce”.

```bash
bash benchmarks/blimp/checkpoints_instance.sh przygotuj 9000      # limit czasu instancji, zależności, wagi 1.06, BLiMP
bash benchmarks/blimp/checkpoints_instance.sh kalibracja          # krok 13848 i avg3 na każdym GPU
bash benchmarks/blimp/checkpoints_instance.sh punkty "1.03:7150 1.04:8600 1.04:10010"
bash benchmarks/blimp/checkpoints_instance.sh srednie             # avg5, avg10
bash benchmarks/blimp/checkpoints_instance.sh heldout "m106 avg3 avg5 avg10"
```

Lokalnie, bez wag (z plików w repo):

```bash
BLIMP_DIR=<snapshot> python benchmarks/blimp/checkpoints.py zbierz   # -> results/checkpoints.json
python tools/liczby.py && python benchmarks/blimp/checkpoints.py raport && python tools/sprawdz_raporty.py
python tests/test_blimp_checkpoints.py && python tests/test_blimp_checkpoints_independent.py
```

`zbierz` bez katalogu `--gpu` zachowuje zapisaną w `checkpoints.json` kontrolę między GPU.

Pliki w `results/checkpoints/` (wszystkie poniżej 10 MB, więc w repo według `CONTRIBUTING.md`, „Pliki w repo”):

| plik | co zawiera | na instancji |
|---|---|---|
| `k<krok>.jsonl.gz`, `avg3/5/10.jsonl.gz` | wynik per para (identyfikator, log-prawdopodobieństwa, bez zdań) | `wyniki/<etykieta>/blimp.jsonl.gz` |
| `heldout_<model>.json`, `heldout_stats.json` | strata per okno held-out, sha256 plików okien | `wyniki/heldout_*.json`, `wyniki/heldout_statystyki.json` |
| `times_<gpu>.jsonl` | czasy etapów, pobrania z rewizją i sha256 | `czasy.jsonl` |
| `conversions.jsonl` | kontrola konwersji 13848 wobec wag 1.06 | `logi/konwersje.jsonl` |
| `averages.jsonl` | skład średnich (kroki odczytane z plików) | `logi/srednie.jsonl` |
| `points_<gpu>.log` | log etapu `punkty` (z niego odczyt przerwanych przebiegów) | `logi/punkty.log` |
| `environment_<gpu>.json` | torch, CUDA, GPU | `srodowisko.json` |

Poza repo zostały kopie wyników tego samego modelu z różnych GPU (`--gpu <katalog>/<gpu>/<etykieta>.jsonl.gz`,
6 plików po ok. 2 MB): wynik ich porównania jest w `results/checkpoints.json` (`kontrola_gpu`), a pliki dla
krzywej to kopie z jednego GPU na model.
