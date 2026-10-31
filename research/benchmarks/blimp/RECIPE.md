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
