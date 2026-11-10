# Pełny przebieg 2026-11-09: Slayer 1B 1.07 i modele odniesienia

<!-- Plik wygenerowany przez tools/ewaluacja/raport.py. Nie edytuj ręcznie: zmień generator albo dane. -->

17 modeli, 15 testów, pełne zbiory. Karta NVIDIA GeForce RTX 5090, float32, batch 1. Wyjątek: Bielik-11B w bfloat16, bez EWoK.

<a href="../../STATUS.md"><img src="../../../docs/img/stan-benchmarkow.svg" alt="Stan benchmarków" height="36"></a> <a href="../../METODOLOGIA.md"><img src="../../../docs/img/metodologia.svg" alt="Metodologia" height="36"></a> <a href="https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks"><img src="../../../docs/img/wyniki-na-hf.svg" alt="Wyniki na HF" height="36"></a>

> [!WARNING]
> **BOS nie jest liczony jednakowo.** Slayer ma jeden wiodący BOS, a modele odniesienia były liczone bez BOS. Wpływ zmierzono wyłącznie na Pythii-1B v0: [najwyżej 0,0105 na testach z pomiaru BOS](#bos-okno-wikitext-i-kontrola-arc-challenge). Pozostałe zastrzeżenia: [Zastrzeżenia](#zastrzeżenia).

<p align="center"><img src="charts/przemiana-wersji.svg" alt="Animacja: Slayer 1B od wersji 1.00 do 1.07 na tle modeli odniesienia" width="100%"></p>

**Slayer 1.07**: ostatnia przyjęta wersja, bez wygaszania LR. **1.08**: [karta modelu](https://huggingface.co/SlayerLab/Slayer1B-1.08/blob/5f854a0cc7160594d54d1788d37a44e8ebabe16c/README.md), checkpoint eksperymentalny: bramka przyjęcia niezaliczona (ARC-Easy), nie jest następcą 1.07.

## Tabela CodeSOTA

| Test | n | Slayer 1.07 | Pythia-1B | Qwen 0.8B | Baza b | Miejsce | 1.00 → 1.08 |
|---|---:|---:|---:|---:|---:|:---:|---|
| [ARC-Easy](#arc-easy) | 2 376 | **0,5981&nbsp;±&nbsp;0,0101** | 0,5585&nbsp;±&nbsp;0,0102 | 0,7054&nbsp;±&nbsp;0,0094 | 0,2664 (stała odpowiedź) | 5/7 | ▲&nbsp;pewna |
| [BLiMP](#blimp) | 67 000 | **0,7982&nbsp;±&nbsp;0,0212** | 0,8244&nbsp;±&nbsp;0,0208 | 0,7986&nbsp;±&nbsp;0,0223 | 0,5000 (losowa) | 6/7 | ▲&nbsp;pewna |
| [EWoK](#ewok) | 4 374 | **0,6089&nbsp;±&nbsp;0,0074** | 0,6471&nbsp;±&nbsp;0,0080 | 0,6757&nbsp;±&nbsp;0,0083 | 0,5000 (losowa) | 6/6 | ▲&nbsp;pewna |
| [HellaSwag](#hellaswag) | 10 042 | **0,4337&nbsp;±&nbsp;0,0049** | 0,4679&nbsp;±&nbsp;0,0050 | 0,5482&nbsp;±&nbsp;0,0050 | 0,2573 (stała odpowiedź) | 7/7 | ▲&nbsp;pewna |
| [LAMBADA](#lambada) | 5 153 | **0,4122&nbsp;±&nbsp;0,0069** | 0,5657&nbsp;±&nbsp;0,0069 | 0,5119&nbsp;±&nbsp;0,0070 | 0,0031 (stała odpowiedź) | 7/7 | ▲&nbsp;pewna |
| [PIQA](#piqa) | 1 838 | **0,6697&nbsp;±&nbsp;0,0110** | 0,7095&nbsp;±&nbsp;0,0106 | 0,7133&nbsp;±&nbsp;0,0106 | 0,5049 (stała odpowiedź) | 7/7 | ▲&nbsp;pewna |
| [WikiText-2](#wikitext-2) | 62 | **1,782&nbsp;±&nbsp;0,0147** | 1,688&nbsp;±&nbsp;0,0139 | 1,717&nbsp;±&nbsp;0,0130 | nie dotyczy | 7/7 | ▲&nbsp;pewna |
| [WinoGrande](#winogrande) | 1 267 | **0,5359&nbsp;±&nbsp;0,0129** | 0,5446&nbsp;±&nbsp;0,0125 | 0,6006&nbsp;±&nbsp;0,0129 | 0,5043 (stała odpowiedź) | 7/7 | ≈&nbsp;szum |
| [WSC273](#wsc273) | 273 | **0,6154&nbsp;±&nbsp;0,0206** | 0,6740&nbsp;±&nbsp;0,0211 | 0,7143&nbsp;±&nbsp;0,0233 | 0,5018 (stała odpowiedź) | 7/7 | △&nbsp;prawdopodobna |

<details>
<summary><b>Wiersze tabeli</b> (62)</summary>

| Test | Model | Etykieta | Parametry | Klasa | Wartość | SE | CI95 | b | lm_eval | Kontaminacja | Wyniki |
|---|---|---|---:|---|---:|---:|---|---:|---|---|---|
| ARC-Easy | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,8186 | 0,0079 | 0,8030 – 0,8338 | 0,2664 | 0.4.9.1 | nieznana | [plik](arc-easy/bielik-11b-v3-instruct/results_rozszerzone.json) |
| ARC-Easy | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,7172 | 0,0092 | 0,6991 – 0,7353 | 0,2664 | 0.4.13 | nieznana | [plik](arc-easy/lfm3-1.7b-base/results_rozszerzone.json) |
| ARC-Easy | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,7054 | 0,0094 | 0,6869 – 0,7235 | 0,2664 | 0.4.13 | nieznana | [plik](arc-easy/qwen3.5-0.8b-base/results_rozszerzone.json) |
| ARC-Easy | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,6852 | 0,0095 | 0,6667 – 0,7037 | 0,2664 | 0.4.9.1 | nieznana | [plik](arc-easy/eurollm-1.7b/results_rozszerzone.json) |
| ARC-Easy | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,5981 | 0,0101 | 0,5787 – 0,6174 | 0,2664 | 0.4.9.1 | nieznana | [plik](arc-easy/slayer1b-1.07-hf/results_rozszerzone.json) |
| ARC-Easy | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,5585 | 0,0102 | 0,5383 – 0,5787 | 0,2664 | 0.4.9.1 | nieznana | [plik](arc-easy/pythia-1b-v0/results_rozszerzone.json) |
| ARC-Easy | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,5459 | 0,0102 | 0,5261 – 0,5661 | 0,2664 | 0.4.9.1 | nieznana | [plik](arc-easy/bielik-1.5b-v3/results_rozszerzone.json) |
| BLiMP | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,8318 | 0,0178 | 0,7966 – 0,8658 | 0,5000 | 0.4.9.1 | nieznana | [plik](blimp/bielik-11b-v3-instruct/results_rozszerzone.json) |
| BLiMP | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,8244 | 0,0208 | 0,7827 – 0,8627 | 0,5000 | 0.4.9.1 | nieznana | [plik](blimp/pythia-1b-v0/results_rozszerzone.json) |
| BLiMP | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,8191 | 0,0201 | 0,7797 – 0,8563 | 0,5000 | 0.4.9.1 | nieznana | [plik](blimp/bielik-1.5b-v3/results_rozszerzone.json) |
| BLiMP | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,8036 | 0,0182 | 0,7679 – 0,8383 | 0,5000 | 0.4.9.1 | nieznana | [plik](blimp/eurollm-1.7b/results_rozszerzone.json) |
| BLiMP | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,7986 | 0,0223 | 0,7541 – 0,8408 | 0,5000 | 0.4.13 | nieznana | [plik](blimp/qwen3.5-0.8b-base/results_rozszerzone.json) |
| BLiMP | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,7982 | 0,0212 | 0,7554 – 0,8384 | 0,5000 | 0.4.9.1 | nieznana | [plik](blimp/slayer1b-1.07-hf/results_rozszerzone.json) |
| BLiMP | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,7930 | 0,0230 | 0,7478 – 0,8361 | 0,5000 | 0.4.13 | nieznana | [plik](blimp/lfm3-1.7b-base/results_rozszerzone.json) |
| EWoK | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,6946 | 0,0080 | 0,6787 – 0,7101 | 0,5000 | nie dotyczy (własny kod testu) | nieznana | [plik](ewok/bielik-1.5b-v3/results_rozszerzone.json) |
| EWoK | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,6757 | 0,0083 | 0,6596 – 0,6921 | 0,5000 | nie dotyczy (własny kod testu) | nieznana | [plik](ewok/qwen3.5-0.8b-base/results_rozszerzone.json) |
| EWoK | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,6621 | 0,0080 | 0,6463 – 0,6778 | 0,5000 | nie dotyczy (własny kod testu) | nieznana | [plik](ewok/eurollm-1.7b/results_rozszerzone.json) |
| EWoK | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,6596 | 0,0077 | 0,6449 – 0,6747 | 0,5000 | nie dotyczy (własny kod testu) | nieznana | [plik](ewok/lfm3-1.7b-base/results_rozszerzone.json) |
| EWoK | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,6471 | 0,0080 | 0,6314 – 0,6630 | 0,5000 | nie dotyczy (własny kod testu) | nieznana | [plik](ewok/pythia-1b-v0/results_rozszerzone.json) |
| EWoK | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,6089 | 0,0074 | 0,5944 – 0,6235 | 0,5000 | nie dotyczy (własny kod testu) | nieznana | [plik](ewok/slayer1b-1.07-hf/results_rozszerzone.json) |
| HellaSwag | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,7940 | 0,0040 | 0,7860 – 0,8018 | 0,2573 | 0.4.9.1 | nieznana | [plik](hellaswag/bielik-11b-v3-instruct/results_rozszerzone.json) |
| HellaSwag | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,6372 | 0,0048 | 0,6280 – 0,6467 | 0,2573 | 0.4.9.1 | nieznana | [plik](hellaswag/bielik-1.5b-v3/results_rozszerzone.json) |
| HellaSwag | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,5927 | 0,0049 | 0,5833 – 0,6023 | 0,2573 | 0.4.9.1 | nieznana | [plik](hellaswag/eurollm-1.7b/results_rozszerzone.json) |
| HellaSwag | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,5891 | 0,0049 | 0,5797 – 0,5989 | 0,2573 | 0.4.13 | nieznana | [plik](hellaswag/lfm3-1.7b-base/results_rozszerzone.json) |
| HellaSwag | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,5482 | 0,0050 | 0,5386 – 0,5581 | 0,2573 | 0.4.13 | nieznana | [plik](hellaswag/qwen3.5-0.8b-base/results_rozszerzone.json) |
| HellaSwag | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,4679 | 0,0050 | 0,4582 – 0,4777 | 0,2573 | 0.4.9.1 | nieznana | [plik](hellaswag/pythia-1b-v0/results_rozszerzone.json) |
| HellaSwag | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,4337 | 0,0049 | 0,4240 – 0,4433 | 0,2573 | 0.4.9.1 | nieznana | [plik](hellaswag/slayer1b-1.07-hf/results_rozszerzone.json) |
| LAMBADA | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,7140 | 0,0063 | 0,7015 – 0,7264 | 0,0031 | 0.4.9.1 | nieznana | [plik](lambada/bielik-11b-v3-instruct/results_rozszerzone.json) |
| LAMBADA | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,6107 | 0,0068 | 0,5975 – 0,6241 | 0,0031 | 0.4.9.1 | nieznana | [plik](lambada/bielik-1.5b-v3/results_rozszerzone.json) |
| LAMBADA | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,5657 | 0,0069 | 0,5519 – 0,5791 | 0,0031 | 0.4.9.1 | nieznana | [plik](lambada/pythia-1b-v0/results_rozszerzone.json) |
| LAMBADA | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,5302 | 0,0070 | 0,5164 – 0,5436 | 0,0031 | 0.4.9.1 | nieznana | [plik](lambada/eurollm-1.7b/results_rozszerzone.json) |
| LAMBADA | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,5119 | 0,0070 | 0,4984 – 0,5255 | 0,0031 | 0.4.13 | nieznana | [plik](lambada/qwen3.5-0.8b-base/results_rozszerzone.json) |
| LAMBADA | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,5069 | 0,0070 | 0,4933 – 0,5207 | 0,0031 | 0.4.13 | nieznana | [plik](lambada/lfm3-1.7b-base/results_rozszerzone.json) |
| LAMBADA | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,4122 | 0,0069 | 0,3984 – 0,4254 | 0,0031 | 0.4.9.1 | nieznana | [plik](lambada/slayer1b-1.07-hf/results_rozszerzone.json) |
| PIQA | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,7889 | 0,0095 | 0,7704 – 0,8074 | 0,5049 | 0.4.9.1 | nieznana | [plik](piqa/bielik-11b-v3-instruct/results_rozszerzone.json) |
| PIQA | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,7345 | 0,0103 | 0,7138 – 0,7541 | 0,5049 | 0.4.9.1 | nieznana | [plik](piqa/eurollm-1.7b/results_rozszerzone.json) |
| PIQA | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,7187 | 0,0105 | 0,6980 – 0,7394 | 0,5049 | 0.4.9.1 | nieznana | [plik](piqa/bielik-1.5b-v3/results_rozszerzone.json) |
| PIQA | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,7133 | 0,0106 | 0,6926 – 0,7339 | 0,5049 | 0.4.13 | nieznana | [plik](piqa/qwen3.5-0.8b-base/results_rozszerzone.json) |
| PIQA | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,7095 | 0,0106 | 0,6882 – 0,7301 | 0,5049 | 0.4.9.1 | nieznana | [plik](piqa/pythia-1b-v0/results_rozszerzone.json) |
| PIQA | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,6855 | 0,0108 | 0,6643 – 0,7067 | 0,5049 | 0.4.13 | nieznana | [plik](piqa/lfm3-1.7b-base/results_rozszerzone.json) |
| PIQA | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,6697 | 0,0110 | 0,6485 – 0,6910 | 0,5049 | 0.4.9.1 | nieznana | [plik](piqa/slayer1b-1.07-hf/results_rozszerzone.json) |
| WikiText-2 | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 1,566 | 0,0110 | 1,545 – 1,588 | nie dotyczy | 0.4.9.1 | nieznana | [plik](wikitext-2/bielik-11b-v3-instruct/results_rozszerzone.json) |
| WikiText-2 | EuroLLM-1.7B | – | 1,66B | poza klasą | 1,608 | 0,0137 | 1,582 – 1,635 | nie dotyczy | 0.4.9.1 | nieznana | [plik](wikitext-2/eurollm-1.7b/results_rozszerzone.json) |
| WikiText-2 | LFM3-1.7B-Base | – | 1,73B | poza klasą | 1,616 | 0,0142 | 1,588 – 1,644 | nie dotyczy | 0.4.13 | nieznana | [plik](wikitext-2/lfm3-1.7b-base/results_rozszerzone.json) |
| WikiText-2 | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 1,674 | 0,0109 | 1,653 – 1,695 | nie dotyczy | 0.4.9.1 | nieznana | [plik](wikitext-2/bielik-1.5b-v3/results_rozszerzone.json) |
| WikiText-2 | Pythia-1B v0 | – | 1,08B | ok. 1B | 1,688 | 0,0139 | 1,661 – 1,715 | nie dotyczy | 0.4.9.1 | nieznana | [plik](wikitext-2/pythia-1b-v0/results_rozszerzone.json) |
| WikiText-2 | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 1,717 | 0,0130 | 1,692 – 1,743 | nie dotyczy | 0.4.13 | nieznana | [plik](wikitext-2/qwen3.5-0.8b-base/results_rozszerzone.json) |
| WikiText-2 | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 1,782 | 0,0147 | 1,754 – 1,811 | nie dotyczy | 0.4.9.1 | nieznana | [plik](wikitext-2/slayer1b-1.07-hf/results_rozszerzone.json) |
| WinoGrande | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,7301 | 0,0124 | 0,7063 – 0,7546 | 0,5043 | 0.4.9.1 | nieznana | [plik](winogrande/bielik-11b-v3-instruct/results_rozszerzone.json) |
| WinoGrande | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,6235 | 0,0129 | 0,5987 – 0,6491 | 0,5043 | 0.4.9.1 | nieznana | [plik](winogrande/bielik-1.5b-v3/results_rozszerzone.json) |
| WinoGrande | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,6006 | 0,0129 | 0,5751 – 0,6255 | 0,5043 | 0.4.13 | nieznana | [plik](winogrande/qwen3.5-0.8b-base/results_rozszerzone.json) |
| WinoGrande | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,5904 | 0,0127 | 0,5658 – 0,6154 | 0,5043 | 0.4.9.1 | nieznana | [plik](winogrande/eurollm-1.7b/results_rozszerzone.json) |
| WinoGrande | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,5856 | 0,0132 | 0,5595 – 0,6116 | 0,5043 | 0.4.13 | nieznana | [plik](winogrande/lfm3-1.7b-base/results_rozszerzone.json) |
| WinoGrande | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,5446 | 0,0125 | 0,5196 – 0,5697 | 0,5043 | 0.4.9.1 | nieznana | [plik](winogrande/pythia-1b-v0/results_rozszerzone.json) |
| WinoGrande | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,5359 | 0,0129 | 0,5107 – 0,5614 | 0,5043 | 0.4.9.1 | nieznana | [plik](winogrande/slayer1b-1.07-hf/results_rozszerzone.json) |
| WSC273 | Bielik-11B-v3.0-Instruct | model instruct, surowy tekst | 11,17B | poza klasą | 0,8242 | 0,0244 | 0,7757 – 0,8704 | 0,5018 | 0.4.9.1 | nieznana | [plik](wsc273/bielik-11b-v3-instruct/results_rozszerzone.json) |
| WSC273 | Bielik-1.5B-v3 | – | 1,60B | poza klasą | 0,7656 | 0,0243 | 0,7159 – 0,8118 | 0,5018 | 0.4.9.1 | nieznana | [plik](wsc273/bielik-1.5b-v3/results_rozszerzone.json) |
| WSC273 | LFM3-1.7B-Base | – | 1,73B | poza klasą | 0,7143 | 0,0242 | 0,6666 – 0,7610 | 0,5018 | 0.4.13 | nieznana | [plik](wsc273/lfm3-1.7b-base/results_rozszerzone.json) |
| WSC273 | Qwen3.5-0.8B-Base | – | 0,87B | ok. 1B | 0,7143 | 0,0233 | 0,6691 – 0,7591 | 0,5018 | 0.4.13 | nieznana | [plik](wsc273/qwen3.5-0.8b-base/results_rozszerzone.json) |
| WSC273 | EuroLLM-1.7B | – | 1,66B | poza klasą | 0,7106 | 0,0263 | 0,6593 – 0,7609 | 0,5018 | 0.4.9.1 | nieznana | [plik](wsc273/eurollm-1.7b/results_rozszerzone.json) |
| WSC273 | Pythia-1B v0 | – | 1,08B | ok. 1B | 0,6740 | 0,0211 | 0,6327 – 0,7143 | 0,5018 | 0.4.9.1 | nieznana | [plik](wsc273/pythia-1b-v0/results_rozszerzone.json) |
| WSC273 | Slayer 1B 1.07 | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | ok. 1B | 0,6154 | 0,0206 | 0,5745 – 0,6556 | 0,5018 | 0.4.9.1 | nieznana | [plik](wsc273/slayer1b-1.07-hf/results_rozszerzone.json) |

</details>

<details>
<summary><b>Typ testu i kontrola etapu B</b></summary>

| Test | Typ | Kontrola etapu B |
|---|---|---|
| ARC-Easy | `mc-k` | spełniony: `acc` w furtce 0,5381–0,5789 i nad b + 2 SE; przebieg bez BOS, tak jak harness z 2022 <!-- liczba-spoza-wynikow: furtka z wiersza „warunek odtworzenia” --> |
| BLiMP | `para +klastry` | spełniony, 0,10 pkt |
| EWoK | `para +klastry` | spełniony |
| HellaSwag | `mc` | spełniony |
| LAMBADA | `cloze` | spełniony: `acc` w furtce 0,5422–0,5822 i nad b + 2 SE; przebieg bez BOS, tak jak harness z 2022 <!-- liczba-spoza-wynikow: furtka z wiersza „warunek odtworzenia” --> |
| PIQA | `mc` | spełniony: obie metryki w furtce |
| WikiText-2 | `ppl` | zgodne; dla perpleksji nie ma formalnego progu ([METODOLOGIA.md, „Próg dla perpleksji i BPB”](../../METODOLOGIA.md#próg-dla-perpleksji-i-bpb)), więc wobec spisanej reguły werdykt jest nierozstrzygalny |
| WinoGrande | `mc +klastry` | spełniony |
| WSC273 | `mc +klastry` | kontrola spoza listy źródeł `METODOLOGIA.md`, liczbowo w progu 2 SE; wynik Slayera wstępny |

</details>

### Poza tabelą

- ARC-Challenge, MathQA, MedMCQA, MultiBLiMP-PL, PubMedQA, Social IQa: bez kontroli, nierozstrzygnięte.
- LFM2.5-1.2B-Base: reguła kontekstu: acc_pmi poniżej bazy losowej na 2 testach PMI (ARC-Challenge, PIQA); próg 2 ustalony po obejrzeniu tego przebiegu; reguła przebiegu centralnego: wynik różni się od results/central-run dla tej samej rewizji i wag.
- LFM3-1.7B (Instruct): reguła kontekstu: acc_pmi poniżej bazy losowej na 2 testach PMI (ARC-Challenge, PIQA); próg 2 ustalony po obejrzeniu tego przebiegu.
- Slayer 1.00, 1.01, 1.02, 1.03, 1.04, 1.05, 1.06, 1.08: inne wersje niż główna, wartości w [postępie wersji](#postęp-wersji-slayera).

<details>
<summary><b>6 testów bez kontroli</b> (wyniki wstępne)</summary>

| Test | n | Slayer 1.07 | Pythia-1B | Qwen 0.8B | Baza b | Miejsce | 1.00 → 1.08 |
|---|---:|---:|---:|---:|---:|:---:|---|
| [ARC-Challenge](#arc-challenge) | 1 172 | **0,2730&nbsp;±&nbsp;0,0130** | 0,2747&nbsp;±&nbsp;0,0130 | 0,4044&nbsp;±&nbsp;0,0143 | 0,2654 (stała odpowiedź) | 7/7 | ▲&nbsp;pewna |
| [MathQA](#mathqa) | 2 985 | **0,2345&nbsp;±&nbsp;0,0078** | 0,2352&nbsp;±&nbsp;0,0078 | 0,3337&nbsp;±&nbsp;0,0086 | 0,2265 (stała odpowiedź) | 7/7 | ≈&nbsp;szum |
| [MedMCQA](#medmcqa) | 4 183 | **0,2991&nbsp;±&nbsp;0,0071** | 0,2811&nbsp;±&nbsp;0,0070 | 0,4026&nbsp;±&nbsp;0,0076 | 0,3223 (stała odpowiedź) | 5/7 | ≈&nbsp;szum |
| [MultiBLiMP-PL](#multiblimp-pl) | 3 272 | **0,9887&nbsp;±&nbsp;0,0018** | 0,8013&nbsp;±&nbsp;0,0070 | 0,8450&nbsp;±&nbsp;0,0063 | 0,5000 (losowa) | 2/7 | △&nbsp;prawdopodobna |
| [PubMedQA](#pubmedqa) | 500 | **0,5360&nbsp;±&nbsp;0,0223** | 0,5660&nbsp;±&nbsp;0,0222 | 0,6760&nbsp;±&nbsp;0,0210 | 0,5520 (stała odpowiedź) | 6/7 | ≈&nbsp;szum |
| [Social IQa](#social-iqa) | 1 954 | **0,3910&nbsp;±&nbsp;0,0110** | 0,4023&nbsp;±&nbsp;0,0111 | 0,4186&nbsp;±&nbsp;0,0112 | 0,3362 (stała odpowiedź) | 7/7 | ▲&nbsp;pewna |

</details>

## Mapa modeli

<p align="center"><img src="charts/macierz.svg" alt="Macierz modeli i testów" width="100%"></p>

| Model | Parametry (z wag) | Klasa |
|---|---:|---|
| Slayer 1B 1.07 | 1,07B | ok. 1B |
| Bielik-1.5B-v3 | 1,60B | poza klasą |
| Bielik-11B-v3.0-Instruct | 11,17B | poza klasą |
| EuroLLM-1.7B | 1,66B | poza klasą |
| LFM2.5-1.2B-Base | 1,17B | poza klasą |
| LFM3-1.7B (Instruct) | 1,73B | poza klasą |
| LFM3-1.7B-Base | 1,73B | poza klasą |
| Pythia-1B v0 | 1,08B | ok. 1B |
| Qwen3.5-0.8B-Base | 0,87B | ok. 1B |

Klasa „ok. 1B”: do 1,10B parametrów policzonych z wag ([`sizes.json`](sizes.json)).

## Postęp wersji Slayera

<p align="center"><img src="charts/postep-wersji.svg" alt="Postęp wersji Slayera na każdym teście" width="100%"></p>

<details>
<summary><b>Pierwsza → ostatnia wersja</b> (15 porównań, Holm w tej rodzinie)</summary>

Δ = nowsza − starsza na tych samych pytaniach. SE parowane po pytaniach (z) albo po klastrach testu (t, df = k − 1): BLiMP po paradygmatach, WinoGrande po parach zdań, WSC273 po schematach, EWoK po szablonach. WikiText: Δ w byte perplexity, SE i t na bits per byte z dokumentem jako klastrem. Werdykt: |z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum (t przez p przy tym samym progu).

| test | wersje | Δ | SE Δ | statystyka | werdykt | po Holmie |
|---|---|---:|---:|---|---|---|
| ARC-Challenge | 1.00 → 1.08 | 0,0828 | 0,0124 | z = 6,68 | pewne | tak (pewne) |
| ARC-Easy | 1.00 → 1.08 | 0,1595 | 0,0107 | z = 14,93 | pewne | tak (pewne) |
| BLiMP | 1.00 → 1.08 | 0,0666 | 0,0096 | t = 6,92, df = 66 | pewne | tak (pewne) |
| EWoK | 1.00 → 1.08 | 0,0694 | 0,0093 | t = 7,43, df = 842 | pewne | tak (pewne) |
| HellaSwag | 1.00 → 1.08 | 0,1495 | 0,0043 | z = 34,39 | pewne | tak (pewne) |
| LAMBADA (OpenAI) | 1.00 → 1.08 | 0,1941 | 0,0068 | z = 28,58 | pewne | tak (pewne) |
| MathQA | 1.00 → 1.08 | 0,0178 | 0,0075 | z = 2,37 | prawdopodobne | nie (szum) |
| MedMCQA | 1.00 → 1.08 | −0,0057 | 0,0027 | z = −2,14 | prawdopodobne | nie (szum) |
| MultiBLiMP-PL | 1.00 → 1.08 | 0,0076 | 0,0026 | z = 2,89 | prawdopodobne | tak (prawdopodobne) |
| PIQA | 1.00 → 1.08 | 0,0860 | 0,0104 | z = 8,30 | pewne | tak (pewne) |
| PubMedQA | 1.00 → 1.08 | −0,0640 | 0,0314 | z = −2,04 | prawdopodobne | nie (szum) |
| Social IQa | 1.00 → 1.08 | 0,0389 | 0,0087 | z = 4,48 | pewne | tak (pewne) |
| WikiText-2 | 1.00 → 1.08 | −0,290 | 0,0036 bpb | t = −60,23, df = 61 | pewne | tak (pewne) |
| WinoGrande | 1.00 → 1.08 | 0,0316 | 0,0170 | t = 1,86, df = 982 | szum | nie (szum) |
| WSC273 | 1.00 → 1.08 | 0,0769 | 0,0283 | t = 2,72, df = 134 | prawdopodobne | tak (prawdopodobne) |

</details>

<details>
<summary><b>Kolejne wersje</b> (120 porównań)</summary>

| test | wersje | Δ | SE Δ | statystyka | werdykt | po Holmie |
|---|---|---:|---:|---|---|---|
| ARC-Challenge | 1.00 → 1.01 | 0,0239 | 0,0096 | z = 2,48 | prawdopodobne | nie (szum) |
| ARC-Challenge | 1.01 → 1.02 | 0,0051 | 0,0090 | z = 0,57 | szum | nie (szum) |
| ARC-Challenge | 1.02 → 1.03 | 0,0094 | 0,0088 | z = 1,06 | szum | nie (szum) |
| ARC-Challenge | 1.03 → 1.04 | −0,0009 | 0,0096 | z = −0,09 | szum | nie (szum) |
| ARC-Challenge | 1.04 → 1.05 | 0,0051 | 0,0086 | z = 0,59 | szum | nie (szum) |
| ARC-Challenge | 1.05 → 1.06 | −0,0026 | 0,0089 | z = −0,29 | szum | nie (szum) |
| ARC-Challenge | 1.06 → 1.07 | 0,0154 | 0,0104 | z = 1,47 | szum | nie (szum) |
| ARC-Challenge | 1.07 → 1.08 | 0,0273 | 0,0096 | z = 2,84 | prawdopodobne | nie (szum) |
| ARC-Easy | 1.00 → 1.01 | 0,0492 | 0,0086 | z = 5,71 | pewne | tak (pewne) |
| ARC-Easy | 1.01 → 1.02 | 0,0101 | 0,0087 | z = 1,17 | szum | nie (szum) |
| ARC-Easy | 1.02 → 1.03 | 0,0109 | 0,0085 | z = 1,29 | szum | nie (szum) |
| ARC-Easy | 1.03 → 1.04 | 0,0202 | 0,0087 | z = 2,32 | prawdopodobne | nie (szum) |
| ARC-Easy | 1.04 → 1.05 | 0,0168 | 0,0083 | z = 2,03 | prawdopodobne | nie (szum) |
| ARC-Easy | 1.05 → 1.06 | −0,0055 | 0,0075 | z = −0,73 | szum | nie (szum) |
| ARC-Easy | 1.06 → 1.07 | 0,0720 | 0,0087 | z = 8,30 | pewne | tak (pewne) |
| ARC-Easy | 1.07 → 1.08 | −0,0143 | 0,0069 | z = −2,07 | prawdopodobne | nie (szum) |
| BLiMP | 1.00 → 1.01 | 0,0235 | 0,0072 | t = 3,24, df = 66 | pewne | nie (szum) |
| BLiMP | 1.01 → 1.02 | 0,0049 | 0,0071 | t = 0,69, df = 66 | szum | nie (szum) |
| BLiMP | 1.02 → 1.03 | 0,0078 | 0,0074 | t = 1,04, df = 66 | szum | nie (szum) |
| BLiMP | 1.03 → 1.04 | −0,0036 | 0,0046 | t = −0,77, df = 66 | szum | nie (szum) |
| BLiMP | 1.04 → 1.05 | 0,0208 | 0,0053 | t = 3,95, df = 66 | pewne | tak (prawdopodobne) |
| BLiMP | 1.05 → 1.06 | 0,0005 | 0,0041 | t = 0,13, df = 66 | szum | nie (szum) |
| BLiMP | 1.06 → 1.07 | 0,0062 | 0,0050 | t = 1,23, df = 66 | szum | nie (szum) |
| BLiMP | 1.07 → 1.08 | 0,0065 | 0,0032 | t = 2,04, df = 66 | szum | nie (szum) |
| EWoK | 1.00 → 1.01 | 0,0245 | 0,0062 | t = 3,96, df = 842 | pewne | tak (prawdopodobne) |
| EWoK | 1.01 → 1.02 | 0,0079 | 0,0064 | t = 1,22, df = 842 | szum | nie (szum) |
| EWoK | 1.02 → 1.03 | 0,0039 | 0,0055 | t = 0,71, df = 842 | szum | nie (szum) |
| EWoK | 1.03 → 1.04 | 0,0080 | 0,0058 | t = 1,38, df = 842 | szum | nie (szum) |
| EWoK | 1.04 → 1.05 | 0,0103 | 0,0053 | t = 1,94, df = 842 | szum | nie (szum) |
| EWoK | 1.05 → 1.06 | 0,0056 | 0,0049 | t = 1,14, df = 842 | szum | nie (szum) |
| EWoK | 1.06 → 1.07 | 0,0192 | 0,0066 | t = 2,92, df = 842 | prawdopodobne | nie (szum) |
| EWoK | 1.07 → 1.08 | −0,0099 | 0,0053 | t = −1,89, df = 842 | szum | nie (szum) |
| HellaSwag | 1.00 → 1.01 | 0,0231 | 0,0030 | z = 7,59 | pewne | tak (pewne) |
| HellaSwag | 1.01 → 1.02 | 0,0321 | 0,0031 | z = 10,36 | pewne | tak (pewne) |
| HellaSwag | 1.02 → 1.03 | 0,0110 | 0,0030 | z = 3,70 | pewne | tak (prawdopodobne) |
| HellaSwag | 1.03 → 1.04 | 0,0166 | 0,0031 | z = 5,43 | pewne | tak (pewne) |
| HellaSwag | 1.04 → 1.05 | 0,0149 | 0,0029 | z = 5,11 | pewne | tak (pewne) |
| HellaSwag | 1.05 → 1.06 | 0,0109 | 0,0027 | z = 4,00 | pewne | tak (prawdopodobne) |
| HellaSwag | 1.06 → 1.07 | 0,0405 | 0,0032 | z = 12,78 | pewne | tak (pewne) |
| HellaSwag | 1.07 → 1.08 | 0,0004 | 0,0025 | z = 0,16 | szum | nie (szum) |
| LAMBADA (OpenAI) | 1.00 → 1.01 | 0,0706 | 0,0052 | z = 13,56 | pewne | tak (pewne) |
| LAMBADA (OpenAI) | 1.01 → 1.02 | 0,0411 | 0,0054 | z = 7,57 | pewne | tak (pewne) |
| LAMBADA (OpenAI) | 1.02 → 1.03 | 0,0116 | 0,0053 | z = 2,18 | prawdopodobne | nie (szum) |
| LAMBADA (OpenAI) | 1.03 → 1.04 | 0,0225 | 0,0055 | z = 4,12 | pewne | tak (prawdopodobne) |
| LAMBADA (OpenAI) | 1.04 → 1.05 | 0,0095 | 0,0053 | z = 1,78 | szum | nie (szum) |
| LAMBADA (OpenAI) | 1.05 → 1.06 | 0,0017 | 0,0052 | z = 0,34 | szum | nie (szum) |
| LAMBADA (OpenAI) | 1.06 → 1.07 | 0,0477 | 0,0058 | z = 8,19 | pewne | tak (pewne) |
| LAMBADA (OpenAI) | 1.07 → 1.08 | −0,0109 | 0,0048 | z = −2,25 | prawdopodobne | nie (szum) |
| MathQA | 1.00 → 1.01 | 0,0054 | 0,0062 | z = 0,87 | szum | nie (szum) |
| MathQA | 1.01 → 1.02 | 0,0013 | 0,0060 | z = 0,22 | szum | nie (szum) |
| MathQA | 1.02 → 1.03 | −0,0017 | 0,0060 | z = −0,28 | szum | nie (szum) |
| MathQA | 1.03 → 1.04 | −0,0067 | 0,0060 | z = −1,12 | szum | nie (szum) |
| MathQA | 1.04 → 1.05 | 0,0074 | 0,0057 | z = 1,30 | szum | nie (szum) |
| MathQA | 1.05 → 1.06 | 0,0027 | 0,0056 | z = 0,47 | szum | nie (szum) |
| MathQA | 1.06 → 1.07 | 0,0157 | 0,0071 | z = 2,22 | prawdopodobne | nie (szum) |
| MathQA | 1.07 → 1.08 | −0,0064 | 0,0061 | z = −1,05 | szum | nie (szum) |
| MedMCQA | 1.00 → 1.01 | −0,0048 | 0,0027 | z = −1,78 | szum | nie (szum) |
| MedMCQA | 1.01 → 1.02 | 0,0043 | 0,0027 | z = 1,60 | szum | nie (szum) |
| MedMCQA | 1.02 → 1.03 | 0,0031 | 0,0019 | z = 1,61 | szum | nie (szum) |
| MedMCQA | 1.03 → 1.04 | −0,0098 | 0,0030 | z = −3,28 | pewne | nie (szum) |
| MedMCQA | 1.04 → 1.05 | 0,0045 | 0,0028 | z = 1,64 | szum | nie (szum) |
| MedMCQA | 1.05 → 1.06 | 0,0007 | 0,0026 | z = 0,28 | szum | nie (szum) |
| MedMCQA | 1.06 → 1.07 | −0,0170 | 0,0054 | z = −3,14 | pewne | nie (szum) |
| MedMCQA | 1.07 → 1.08 | 0,0131 | 0,0050 | z = 2,61 | prawdopodobne | nie (szum) |
| MultiBLiMP-PL | 1.00 → 1.01 | 0,0052 | 0,0023 | z = 2,21 | prawdopodobne | nie (szum) |
| MultiBLiMP-PL | 1.01 → 1.02 | 0,0018 | 0,0025 | z = 0,73 | szum | nie (szum) |
| MultiBLiMP-PL | 1.02 → 1.03 | −0,0012 | 0,0021 | z = −0,58 | szum | nie (szum) |
| MultiBLiMP-PL | 1.03 → 1.04 | 0,0067 | 0,0020 | z = 3,32 | pewne | nie (szum) |
| MultiBLiMP-PL | 1.04 → 1.05 | −0,0049 | 0,0021 | z = −2,36 | prawdopodobne | nie (szum) |
| MultiBLiMP-PL | 1.05 → 1.06 | −0,0015 | 0,0021 | z = −0,75 | szum | nie (szum) |
| MultiBLiMP-PL | 1.06 → 1.07 | 0,0028 | 0,0021 | z = 1,31 | szum | nie (szum) |
| MultiBLiMP-PL | 1.07 → 1.08 | −0,0012 | 0,0019 | z = −0,65 | szum | nie (szum) |
| PIQA | 1.00 → 1.01 | 0,0114 | 0,0087 | z = 1,31 | szum | nie (szum) |
| PIQA | 1.01 → 1.02 | 0,0180 | 0,0084 | z = 2,14 | prawdopodobne | nie (szum) |
| PIQA | 1.02 → 1.03 | 0,0163 | 0,0081 | z = 2,02 | prawdopodobne | nie (szum) |
| PIQA | 1.03 → 1.04 | 0,0038 | 0,0081 | z = 0,47 | szum | nie (szum) |
| PIQA | 1.04 → 1.05 | 0,0125 | 0,0078 | z = 1,60 | szum | nie (szum) |
| PIQA | 1.05 → 1.06 | 0,0033 | 0,0071 | z = 0,46 | szum | nie (szum) |
| PIQA | 1.06 → 1.07 | 0,0283 | 0,0079 | z = 3,58 | pewne | tak (prawdopodobne) |
| PIQA | 1.07 → 1.08 | −0,0076 | 0,0066 | z = −1,16 | szum | nie (szum) |
| PubMedQA | 1.00 → 1.01 | 0,0460 | 0,0192 | z = 2,40 | prawdopodobne | nie (szum) |
| PubMedQA | 1.01 → 1.02 | −0,0060 | 0,0151 | z = −0,40 | szum | nie (szum) |
| PubMedQA | 1.02 → 1.03 | −0,0140 | 0,0166 | z = −0,84 | szum | nie (szum) |
| PubMedQA | 1.03 → 1.04 | 0,0040 | 0,0237 | z = 0,17 | szum | nie (szum) |
| PubMedQA | 1.04 → 1.05 | −0,0280 | 0,0192 | z = −1,46 | szum | nie (szum) |
| PubMedQA | 1.05 → 1.06 | −0,0240 | 0,0181 | z = −1,33 | szum | nie (szum) |
| PubMedQA | 1.06 → 1.07 | 0,0600 | 0,0245 | z = 2,45 | prawdopodobne | nie (szum) |
| PubMedQA | 1.07 → 1.08 | −0,1020 | 0,0221 | z = −4,62 | pewne | tak (pewne) |
| Social IQa | 1.00 → 1.01 | 0,0005 | 0,0070 | z = 0,07 | szum | nie (szum) |
| Social IQa | 1.01 → 1.02 | 0,0107 | 0,0067 | z = 1,61 | szum | nie (szum) |
| Social IQa | 1.02 → 1.03 | 0,0051 | 0,0068 | z = 0,75 | szum | nie (szum) |
| Social IQa | 1.03 → 1.04 | 0,0056 | 0,0070 | z = 0,80 | szum | nie (szum) |
| Social IQa | 1.04 → 1.05 | 0,0107 | 0,0067 | z = 1,61 | szum | nie (szum) |
| Social IQa | 1.05 → 1.06 | −0,0010 | 0,0061 | z = −0,17 | szum | nie (szum) |
| Social IQa | 1.06 → 1.07 | 0,0015 | 0,0069 | z = 0,22 | szum | nie (szum) |
| Social IQa | 1.07 → 1.08 | 0,0056 | 0,0061 | z = 0,92 | szum | nie (szum) |
| WikiText-2 | 1.00 → 1.01 | −0,111 | 0,0014 bpb | t = −55,54, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.01 → 1.02 | −0,042 | 0,0013 bpb | t = −24,94, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.02 → 1.03 | −0,018 | 0,0007 bpb | t = −18,56, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.03 → 1.04 | −0,028 | 0,0008 bpb | t = −27,17, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.04 → 1.05 | −0,019 | 0,0006 bpb | t = −24,78, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.05 → 1.06 | −0,005 | 0,0005 bpb | t = −7,98, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.06 → 1.07 | −0,065 | 0,0014 bpb | t = −37,62, df = 61 | pewne | tak (pewne) |
| WikiText-2 | 1.07 → 1.08 | −0,001 | 0,0008 bpb | t = −1,48, df = 61 | szum | nie (szum) |
| WinoGrande | 1.00 → 1.01 | 0,0150 | 0,0156 | t = 0,96, df = 982 | szum | nie (szum) |
| WinoGrande | 1.01 → 1.02 | −0,0095 | 0,0149 | t = −0,64, df = 982 | szum | nie (szum) |
| WinoGrande | 1.02 → 1.03 | 0,0245 | 0,0139 | t = 1,76, df = 982 | szum | nie (szum) |
| WinoGrande | 1.03 → 1.04 | −0,0237 | 0,0138 | t = −1,72, df = 982 | szum | nie (szum) |
| WinoGrande | 1.04 → 1.05 | 0,0110 | 0,0134 | t = 0,83, df = 982 | szum | nie (szum) |
| WinoGrande | 1.05 → 1.06 | −0,0008 | 0,0122 | t = −0,06, df = 982 | szum | nie (szum) |
| WinoGrande | 1.06 → 1.07 | 0,0142 | 0,0131 | t = 1,08, df = 982 | szum | nie (szum) |
| WinoGrande | 1.07 → 1.08 | 0,0008 | 0,0116 | t = 0,07, df = 982 | szum | nie (szum) |
| WSC273 | 1.00 → 1.01 | 0,0147 | 0,0270 | t = 0,54, df = 134 | szum | nie (szum) |
| WSC273 | 1.01 → 1.02 | 0,0183 | 0,0287 | t = 0,64, df = 134 | szum | nie (szum) |
| WSC273 | 1.02 → 1.03 | −0,0110 | 0,0230 | t = −0,48, df = 134 | szum | nie (szum) |
| WSC273 | 1.03 → 1.04 | 0,0000 | 0,0265 | t = 0,00, df = 134 | szum | nie (szum) |
| WSC273 | 1.04 → 1.05 | 0,0256 | 0,0262 | t = 0,98, df = 134 | szum | nie (szum) |
| WSC273 | 1.05 → 1.06 | 0,0037 | 0,0252 | t = 0,15, df = 134 | szum | nie (szum) |
| WSC273 | 1.06 → 1.07 | 0,0256 | 0,0197 | t = 1,30, df = 134 | szum | nie (szum) |
| WSC273 | 1.07 → 1.08 | 0,0000 | 0,0201 | t = 0,00, df = 134 | szum | nie (szum) |

</details>

<details>
<summary><b>Wszystkie wersje Slayera</b>, wartości</summary>

Wszystkie wersje mają tę samą architekturę i tokenizer; rewizje HF w `manifest.jsonl`. 1.07 to wagi z HF (sha256 checkpointu zgodne z `SLAYER_CKPT_SHA256`), etykieta: ostatnia przyjęta wersja, bez wygaszania LR. 1.08: checkpoint eksperymentalny: bramka przyjęcia niezaliczona (ARC-Easy), nie jest następcą 1.07; z wygaszaniem LR ([karta modelu](https://huggingface.co/SlayerLab/Slayer1B-1.08/blob/5f854a0cc7160594d54d1788d37a44e8ebabe16c/README.md)). Pozostałe wersje: bez wygaszania LR.

| test | 1.00 | 1.01 | 1.02 | 1.03 | 1.04 | 1.05 | 1.06 | 1.07 | 1.08 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ARC-Challenge | 0,2176 | 0,2415 | 0,2466 | 0,2560 | 0,2551 | 0,2602 | 0,2577 | 0,2730 | 0,3003 |
| ARC-Easy | 0,4242 | 0,4735 | 0,4836 | 0,4945 | 0,5147 | 0,5316 | 0,5261 | 0,5981 | 0,5838 |
| BLiMP | 0,7382 | 0,7616 | 0,7665 | 0,7743 | 0,7707 | 0,7915 | 0,7921 | 0,7982 | 0,8047 |
| EWoK | 0,5296 | 0,5541 | 0,5620 | 0,5658 | 0,5738 | 0,5841 | 0,5897 | 0,6089 | 0,5990 |
| HellaSwag | 0,2846 | 0,3077 | 0,3398 | 0,3507 | 0,3674 | 0,3823 | 0,3931 | 0,4337 | 0,4341 |
| LAMBADA (OpenAI) | 0,2073 | 0,2779 | 0,3190 | 0,3307 | 0,3532 | 0,3627 | 0,3644 | 0,4122 | 0,4013 |
| MathQA | 0,2104 | 0,2157 | 0,2171 | 0,2154 | 0,2087 | 0,2161 | 0,2188 | 0,2345 | 0,2281 |
| MedMCQA | 0,3180 | 0,3132 | 0,3175 | 0,3206 | 0,3108 | 0,3153 | 0,3160 | 0,2991 | 0,3122 |
| MultiBLiMP-PL | 0,9798 | 0,9850 | 0,9869 | 0,9856 | 0,9924 | 0,9875 | 0,9859 | 0,9887 | 0,9875 |
| PIQA | 0,5762 | 0,5876 | 0,6055 | 0,6219 | 0,6257 | 0,6382 | 0,6415 | 0,6697 | 0,6621 |
| PubMedQA | 0,4980 | 0,5440 | 0,5380 | 0,5240 | 0,5280 | 0,5000 | 0,4760 | 0,5360 | 0,4340 |
| Social IQa | 0,3577 | 0,3582 | 0,3690 | 0,3741 | 0,3797 | 0,3905 | 0,3895 | 0,3910 | 0,3966 |
| WikiText-2 | 2,071 | 1,959 | 1,917 | 1,899 | 1,870 | 1,851 | 1,846 | 1,782 | 1,780 |
| WinoGrande | 0,5051 | 0,5201 | 0,5107 | 0,5351 | 0,5114 | 0,5225 | 0,5217 | 0,5359 | 0,5367 |
| WSC273 | 0,5385 | 0,5531 | 0,5714 | 0,5604 | 0,5604 | 0,5861 | 0,5897 | 0,6154 | 0,6154 |

</details>

<a id="bos-okno-wikitext-i-kontrola-arc-challenge"></a>
<details>
<summary><b>BOS, okno WikiText, kontrola ARC-Challenge</b> (<a href="bos-window-check/README.md">pliki pomiaru</a>)</summary>

BOS, sprawdzona wyłącznie Pythia-1B v0: próg protokołu 0,04, SE niezależne. Tabele raportu zostawiają Pythię bez BOS.

| Test | bez BOS | z BOS | Δ | SE Δ | z | werdykt |
|---|---:|---:|---:|---:|---:|---|
| ARC-Easy | 0,5585 | 0,5690 | +0,0105 | 0,0144 | 0,73 | szum |
| HellaSwag | 0,4679 | 0,4695 | +0,0016 | 0,0070 | 0,23 | szum |
| LAMBADA | 0,5657 | 0,5605 | −0,0052 | 0,0098 | −0,54 | szum |
| PIQA | 0,7095 | 0,7095 | 0,0000 | 0,0150 | 0,00 | szum |
| WinoGrande | 0,5446 | 0,5438 | −0,0008 | 0,0177 | −0,04 | szum |
| WSC273 | 0,6740 | 0,6813 | +0,0073 | 0,0303 | 0,24 | szum |

- ARC-Easy: Slayer 1.07 − Pythia z BOS = 0,0290, z = 2,03, SE niezależne, prawdopodobne.
- WikiText: Pythia oknem 2048 ma 1,6877 (0,0139) zamiast 2,4234 przy `--max_length 4096`; wobec Slayera 1.07 (1,7817) różnica −0,0940, z = −4,64, SE niezależne, pewne, eksploracyjnie.
- Kontrola ARC-Challenge nierozstrzygnięta: EuroLLM-1.7B 25-shot 0,4087 wobec 0,4061, próg 0,0286; demonstracje pochodzą z testu, a ustawienia referencji nie odtworzono.

</details>

## Rankingi testów

<a id="arc-easy"></a>
<details>
<summary><b>ARC-Easy</b>: Slayer 1.07 0,5981, miejsce 5 z 7</summary>

acc, `T51`, n = 2 376, wynik losowy 0,2502, najczęstsza odpowiedź 0,2664.

<p align="center"><img src="charts/arc-easy.svg" alt="ARC-Easy: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="blimp"></a>
<details>
<summary><b>BLiMP</b>: Slayer 1.07 0,7982, miejsce 6 z 7</summary>

acc, `T01`, n = 67 000, wynik losowy 0,5000.

<p align="center"><img src="charts/blimp.svg" alt="BLiMP: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="ewok"></a>
<details>
<summary><b>EWoK</b>: Slayer 1.07 0,6089, miejsce 6 z 6</summary>

ewok, `T53`, n = 4 374, wynik losowy 0,5000.

<p align="center"><img src="charts/ewok.svg" alt="EWoK: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="hellaswag"></a>
<details>
<summary><b>HellaSwag</b>: Slayer 1.07 0,4337, miejsce 7 z 7</summary>

acc_norm, `T05`, n = 10 042, wynik losowy 0,2500, najczęstsza odpowiedź 0,2573.

<p align="center"><img src="charts/hellaswag.svg" alt="HellaSwag: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="lambada"></a>
<details>
<summary><b>LAMBADA</b>: Slayer 1.07 0,4122, miejsce 7 z 7</summary>

acc, `T17`, n = 5 153, wynik losowy 0,0000, najczęstsza odpowiedź 0,0031.

<p align="center"><img src="charts/lambada.svg" alt="LAMBADA: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="piqa"></a>
<details>
<summary><b>PIQA</b>: Slayer 1.07 0,6697, miejsce 7 z 7</summary>

acc_norm, `T06`, n = 1 838, wynik losowy 0,5000, najczęstsza odpowiedź 0,5049.

<p align="center"><img src="charts/piqa.svg" alt="PIQA: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="wikitext-2"></a>
<details>
<summary><b>WikiText-2</b>: Slayer 1.07 1,782, miejsce 7 z 7</summary>

byte perplexity, `T03`, n = 62.

<p align="center"><img src="charts/wikitext-2.svg" alt="WikiText-2: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="winogrande"></a>
<details>
<summary><b>WinoGrande</b>: Slayer 1.07 0,5359, miejsce 7 z 7</summary>

acc, `T07`, n = 1 267, wynik losowy 0,5000, najczęstsza odpowiedź 0,5043.

<p align="center"><img src="charts/winogrande.svg" alt="WinoGrande: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="wsc273"></a>
<details>
<summary><b>WSC273</b>: Slayer 1.07 0,6154, miejsce 7 z 7</summary>

acc, `T14`, n = 273, wynik losowy 0,5000, najczęstsza odpowiedź 0,5018.

<p align="center"><img src="charts/wsc273.svg" alt="WSC273: ranking z przedziałami 95%" width="100%"></p>


</details>

<a id="arc-challenge"></a>
<details>
<summary><b>ARC-Challenge</b> (wstępny): Slayer 1.07 0,2730, miejsce 7 z 7</summary>

acc_norm, `T02`, n = 1 172, wynik losowy 0,2502, najczęstsza odpowiedź 0,2654.

<p align="center"><img src="charts/arc-challenge.svg" alt="ARC-Challenge: ranking z przedziałami 95%" width="100%"></p>

| # | Model | Etykieta | Rozmiar | Wartość | SE | CI95 | lm_eval | Precyzja | Kontaminacja | Wyniki |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
| 1 | Bielik-11B-v3.0-Instruct | instruct, surowy tekst | 11,17B | 0,5811 | 0,0144 | 0,5529 – 0,6101 | 0.4.9.1 | bfloat16 | nieznana | [plik](arc-challenge/bielik-11b-v3-instruct/results_rozszerzone.json) |
| 2 | LFM3-1.7B-Base | – | 1,73B | 0,4292 | 0,0145 | 0,4010 – 0,4582 | 0.4.13 | float32 | nieznana | [plik](arc-challenge/lfm3-1.7b-base/results_rozszerzone.json) |
| 3 | Qwen3.5-0.8B-Base | – | 0,87B | 0,4044 | 0,0143 | 0,3763 – 0,4326 | 0.4.13 | float32 | nieznana | [plik](arc-challenge/qwen3.5-0.8b-base/results_rozszerzone.json) |
| 4 | EuroLLM-1.7B | – | 1,66B | 0,3746 | 0,0141 | 0,3473 – 0,4027 | 0.4.9.1 | float32 | nieznana | [plik](arc-challenge/eurollm-1.7b/results_rozszerzone.json) |
| 5 | Bielik-1.5B-v3 | – | 1,60B | 0,3609 | 0,0140 | 0,3336 – 0,3891 | 0.4.9.1 | float32 | nieznana | [plik](arc-challenge/bielik-1.5b-v3/results_rozszerzone.json) |
| 6 | Pythia-1B v0 | – | 1,08B | 0,2747 | 0,0130 | 0,2500 – 0,3020 | 0.4.9.1 | float32 | nieznana | [plik](arc-challenge/pythia-1b-v0/results_rozszerzone.json) |
| 7 | **Slayer 1B 1.07** | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | **0,2730** | 0,0130 | 0,2474 – 0,2995 | 0.4.9.1 | float32 | nieznana | [plik](arc-challenge/slayer1b-1.07-hf/results_rozszerzone.json) |

</details>

<a id="mathqa"></a>
<details>
<summary><b>MathQA</b> (wstępny): Slayer 1.07 0,2345, miejsce 7 z 7</summary>

acc_norm, `T19`, n = 2 985, wynik losowy 0,2000, najczęstsza odpowiedź 0,2265.

<p align="center"><img src="charts/mathqa.svg" alt="MathQA: ranking z przedziałami 95%" width="100%"></p>

| # | Model | Etykieta | Rozmiar | Wartość | SE | CI95 | lm_eval | Precyzja | Kontaminacja | Wyniki |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
| 1 | Bielik-11B-v3.0-Instruct | instruct, surowy tekst | 11,17B | 0,4848 | 0,0091 | 0,4670 – 0,5025 | 0.4.9.1 | bfloat16 | nieznana | [plik](mathqa/bielik-11b-v3-instruct/results_rozszerzone.json) |
| 2 | LFM3-1.7B-Base | – | 1,73B | 0,3906 | 0,0089 | 0,3735 – 0,4084 | 0.4.13 | float32 | nieznana | [plik](mathqa/lfm3-1.7b-base/results_rozszerzone.json) |
| 3 | Qwen3.5-0.8B-Base | – | 0,87B | 0,3337 | 0,0086 | 0,3169 – 0,3511 | 0.4.13 | float32 | nieznana | [plik](mathqa/qwen3.5-0.8b-base/results_rozszerzone.json) |
| 4 | Bielik-1.5B-v3 | – | 1,60B | 0,3240 | 0,0086 | 0,3075 – 0,3407 | 0.4.9.1 | float32 | nieznana | [plik](mathqa/bielik-1.5b-v3/results_rozszerzone.json) |
| 5 | EuroLLM-1.7B | – | 1,66B | 0,2422 | 0,0078 | 0,2271 – 0,2580 | 0.4.9.1 | float32 | nieznana | [plik](mathqa/eurollm-1.7b/results_rozszerzone.json) |
| 6 | Pythia-1B v0 | – | 1,08B | 0,2352 | 0,0078 | 0,2204 – 0,2503 | 0.4.9.1 | float32 | nieznana | [plik](mathqa/pythia-1b-v0/results_rozszerzone.json) |
| 7 | **Slayer 1B 1.07** | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | **0,2345** | 0,0078 | 0,2194 – 0,2499 | 0.4.9.1 | float32 | nieznana | [plik](mathqa/slayer1b-1.07-hf/results_rozszerzone.json) |

</details>

<a id="medmcqa"></a>
<details>
<summary><b>MedMCQA</b> (wstępny): Slayer 1.07 0,2991, miejsce 5 z 7</summary>

acc, `T45`, n = 4 183, wynik losowy 0,2500, najczęstsza odpowiedź 0,3223.

<p align="center"><img src="charts/medmcqa.svg" alt="MedMCQA: ranking z przedziałami 95%" width="100%"></p>

| # | Model | Etykieta | Rozmiar | Wartość | SE | CI95 | lm_eval | Precyzja | Kontaminacja | Wyniki |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
| 1 | Bielik-11B-v3.0-Instruct | instruct, surowy tekst | 11,17B | 0,5357 | 0,0077 | 0,5209 – 0,5508 | 0.4.9.1 | bfloat16 | nieznana | [plik](medmcqa/bielik-11b-v3-instruct/results_rozszerzone.json) |
| 2 | Qwen3.5-0.8B-Base | – | 0,87B | 0,4026 | 0,0076 | 0,3880 – 0,4176 | 0.4.13 | float32 | nieznana | [plik](medmcqa/qwen3.5-0.8b-base/results_rozszerzone.json) |
| 3 | Bielik-1.5B-v3 | – | 1,60B | 0,3913 | 0,0075 | 0,3765 – 0,4062 | 0.4.9.1 | float32 | nieznana | [plik](medmcqa/bielik-1.5b-v3/results_rozszerzone.json) |
| 4 | LFM3-1.7B-Base | – | 1,73B | 0,3782 | 0,0075 | 0,3636 – 0,3930 | 0.4.13 | float32 | nieznana | [plik](medmcqa/lfm3-1.7b-base/results_rozszerzone.json) |
| 5 | **Slayer 1B 1.07** | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | **0,2991** | 0,0071 | 0,2854 – 0,3125 | 0.4.9.1 | float32 | nieznana | [plik](medmcqa/slayer1b-1.07-hf/results_rozszerzone.json) |
| 6 | Pythia-1B v0 | – | 1,08B | 0,2811 | 0,0070 | 0,2678 – 0,2948 | 0.4.9.1 | float32 | nieznana | [plik](medmcqa/pythia-1b-v0/results_rozszerzone.json) |
| 7 | EuroLLM-1.7B | – | 1,66B | 0,2582 | 0,0068 | 0,2450 – 0,2713 | 0.4.9.1 | float32 | nieznana | [plik](medmcqa/eurollm-1.7b/results_rozszerzone.json) |

</details>

<a id="multiblimp-pl"></a>
<details>
<summary><b>MultiBLiMP-PL</b> (wstępny): Slayer 1.07 0,9887, miejsce 2 z 7</summary>

acc, `T04`, n = 3 272, wynik losowy 0,5000.

<p align="center"><img src="charts/multiblimp-pl.svg" alt="MultiBLiMP-PL: ranking z przedziałami 95%" width="100%"></p>

| # | Model | Etykieta | Rozmiar | Wartość | SE | CI95 | lm_eval | Precyzja | Kontaminacja | Wyniki |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
| 1 | Bielik-11B-v3.0-Instruct | instruct, surowy tekst | 11,17B | 0,9957 | 0,0011 | 0,9933 – 0,9979 | 0.4.9.1 | bfloat16 | nieznana | [plik](multiblimp-pl/bielik-11b-v3-instruct/results_rozszerzone.json) |
| 2 | **Slayer 1B 1.07** | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | **0,9887** | 0,0018 | 0,9850 – 0,9921 | 0.4.9.1 | float32 | nieznana | [plik](multiblimp-pl/slayer1b-1.07-hf/results_rozszerzone.json) |
| 3 | Bielik-1.5B-v3 | – | 1,60B | 0,9447 | 0,0040 | 0,9364 – 0,9526 | 0.4.9.1 | float32 | nieznana | [plik](multiblimp-pl/bielik-1.5b-v3/results_rozszerzone.json) |
| 4 | EuroLLM-1.7B | – | 1,66B | 0,9386 | 0,0042 | 0,9303 – 0,9468 | 0.4.9.1 | float32 | nieznana | [plik](multiblimp-pl/eurollm-1.7b/results_rozszerzone.json) |
| 5 | LFM3-1.7B-Base | – | 1,73B | 0,8915 | 0,0054 | 0,8808 – 0,9022 | 0.4.13 | float32 | nieznana | [plik](multiblimp-pl/lfm3-1.7b-base/results_rozszerzone.json) |
| 6 | Qwen3.5-0.8B-Base | – | 0,87B | 0,8450 | 0,0063 | 0,8325 – 0,8576 | 0.4.13 | float32 | nieznana | [plik](multiblimp-pl/qwen3.5-0.8b-base/results_rozszerzone.json) |
| 7 | Pythia-1B v0 | – | 1,08B | 0,8013 | 0,0070 | 0,7873 – 0,8148 | 0.4.9.1 | float32 | nieznana | [plik](multiblimp-pl/pythia-1b-v0/results_rozszerzone.json) |

</details>

<a id="pubmedqa"></a>
<details>
<summary><b>PubMedQA</b> (wstępny): Slayer 1.07 0,5360, miejsce 6 z 7</summary>

acc, `T44`, n = 500, wynik losowy 0,3333, najczęstsza odpowiedź 0,5520.

<p align="center"><img src="charts/pubmedqa.svg" alt="PubMedQA: ranking z przedziałami 95%" width="100%"></p>

| # | Model | Etykieta | Rozmiar | Wartość | SE | CI95 | lm_eval | Precyzja | Kontaminacja | Wyniki |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
| 1 | Bielik-11B-v3.0-Instruct | instruct, surowy tekst | 11,17B | 0,7300 | 0,0199 | 0,6900 – 0,7680 | 0.4.9.1 | bfloat16 | nieznana | [plik](pubmedqa/bielik-11b-v3-instruct/results_rozszerzone.json) |
| 2 | Qwen3.5-0.8B-Base | – | 0,87B | 0,6760 | 0,0210 | 0,6360 – 0,7160 | 0.4.13 | float32 | nieznana | [plik](pubmedqa/qwen3.5-0.8b-base/results_rozszerzone.json) |
| 3 | Bielik-1.5B-v3 | – | 1,60B | 0,6240 | 0,0217 | 0,5820 – 0,6660 | 0.4.9.1 | float32 | nieznana | [plik](pubmedqa/bielik-1.5b-v3/results_rozszerzone.json) |
| 4 | LFM3-1.7B-Base | – | 1,73B | 0,5940 | 0,0220 | 0,5500 – 0,6360 | 0.4.13 | float32 | nieznana | [plik](pubmedqa/lfm3-1.7b-base/results_rozszerzone.json) |
| 5 | Pythia-1B v0 | – | 1,08B | 0,5660 | 0,0222 | 0,5220 – 0,6080 | 0.4.9.1 | float32 | nieznana | [plik](pubmedqa/pythia-1b-v0/results_rozszerzone.json) |
| 6 | **Slayer 1B 1.07** | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | **0,5360** | 0,0223 | 0,4920 – 0,5800 | 0.4.9.1 | float32 | nieznana | [plik](pubmedqa/slayer1b-1.07-hf/results_rozszerzone.json) |
| 7 | EuroLLM-1.7B | – | 1,66B | 0,5300 | 0,0223 | 0,4860 – 0,5740 | 0.4.9.1 | float32 | nieznana | [plik](pubmedqa/eurollm-1.7b/results_rozszerzone.json) |

</details>

<a id="social-iqa"></a>
<details>
<summary><b>Social IQa</b> (wstępny): Slayer 1.07 0,3910, miejsce 7 z 7</summary>

acc, `T46`, n = 1 954, wynik losowy 0,3333, najczęstsza odpowiedź 0,3362.

<p align="center"><img src="charts/social-iqa.svg" alt="Social IQa: ranking z przedziałami 95%" width="100%"></p>

| # | Model | Etykieta | Rozmiar | Wartość | SE | CI95 | lm_eval | Precyzja | Kontaminacja | Wyniki |
|---:|---|---|---:|---:|---:|---|---|---|---|---|
| 1 | Bielik-11B-v3.0-Instruct | instruct, surowy tekst | 11,17B | 0,5113 | 0,0113 | 0,4893 – 0,5338 | 0.4.9.1 | bfloat16 | nieznana | [plik](social-iqa/bielik-11b-v3-instruct/results_rozszerzone.json) |
| 2 | LFM3-1.7B-Base | – | 1,73B | 0,4545 | 0,0113 | 0,4324 – 0,4770 | 0.4.13 | float32 | nieznana | [plik](social-iqa/lfm3-1.7b-base/results_rozszerzone.json) |
| 3 | Bielik-1.5B-v3 | – | 1,60B | 0,4360 | 0,0112 | 0,4135 – 0,4585 | 0.4.9.1 | float32 | nieznana | [plik](social-iqa/bielik-1.5b-v3/results_rozszerzone.json) |
| 4 | Qwen3.5-0.8B-Base | – | 0,87B | 0,4186 | 0,0112 | 0,3966 – 0,4406 | 0.4.13 | float32 | nieznana | [plik](social-iqa/qwen3.5-0.8b-base/results_rozszerzone.json) |
| 5 | EuroLLM-1.7B | – | 1,66B | 0,4150 | 0,0111 | 0,3930 – 0,4371 | 0.4.9.1 | float32 | nieznana | [plik](social-iqa/eurollm-1.7b/results_rozszerzone.json) |
| 6 | Pythia-1B v0 | – | 1,08B | 0,4023 | 0,0111 | 0,3808 – 0,4237 | 0.4.9.1 | float32 | nieznana | [plik](social-iqa/pythia-1b-v0/results_rozszerzone.json) |
| 7 | **Slayer 1B 1.07** | ostatnia przyjęta wersja, bez wygaszania LR | 1,07B | **0,3910** | 0,0110 | 0,3695 – 0,4130 | 0.4.9.1 | float32 | nieznana | [plik](social-iqa/slayer1b-1.07-hf/results_rozszerzone.json) |

</details>

## Zastrzeżenia

- BOS: Slayer ma jeden wiodący BOS, modele odniesienia były liczone bez BOS, EWoK liczy kod autorów z tokenami specjalnymi tokenizera; wpływ zmierzono wyłącznie na Pythii-1B v0.
- Dwa środowiska, wpływu wersji nie mierzono: lm_eval 0.4.13: LFM3-1.7B (Instruct), LFM3-1.7B-Base, Qwen3.5-0.8B-Base, pozostałe lm_eval 0.4.9.1.
- Różnice między modelami pokazują tylko przedziały; porównania parowane są wyłącznie między wersjami Slayera, a miejsce w tabeli nie mówi o istotności.
- Slayer jest uczony głównie po polsku, a testy poza MultiBLiMP-PL są po angielsku; bez oceny łącznej, bo zestaw testów i wagi nie są ustalone.
- Slayer 1.00–1.07 to checkpointy bez wygaszania LR; wniosek „słabszy od modelu X” wymaga porównania z Pythią przy tej samej liczbie tokenów, którego tu nie ma.
- Kontaminacja: nieznana przy każdym wyniku, skanu nie było.
- Slayer na WikiText-2 mieści się w oknie modelu: 4096 tokenów = `block`, wszystkie wersje (9).
- Pythia-1B na WikiText-2: wynik z limitem 2048 tokenów (okno modelu), poprzedni w polu `poprawka` manifestu.

<details>
<summary><b>Weryfikacja</b></summary>

### Weryfikacja

- Każdy plik wyników ma sumę sha256 w `manifest.jsonl` (pole `pliki`); paczka z próbkami przeszła ją w całości przed rozpakowaniem tutaj.
- Każda wartość została przeliczona od nowa z zapisanych logprobów per pytanie (te same reguły co `common/metryki.py` i `benchmarks/ewok/ewok.py`): wszystkie pary zgodne co do bitu.
- Wspólne pary z `results/central-run` (przebieg centralny fabryki): 28 z 32 identycznych do 4 miejsc po przecinku. Różne tylko: LFM2.5-1.2B-Base (sekcja [Do sprawdzenia](#do-sprawdzenia-i-niepoliczone)).
- Kontrole etapu B z `tools/ewaluacja/kontrole.json` (Pythia-1B v0: PIQA, WinoGrande, LAMBADA, ARC-Easy, BLiMP) dały tu te same wartości co lokalny przebieg kontrolny w `tools/ewaluacja/wyniki_kontrolne/`.

</details>

<details>
<summary><b>Do sprawdzenia i niepoliczone</b></summary>

### Do sprawdzenia i niepoliczone

Flagi nadają reguły `flag_rules` i `window_exceeded` w `tools/ewaluacja/raport.py`, te same dla każdego modelu: (1) `acc_pmi` poniżej bazy losowej na co najmniej 2 testach z PMI (kontekst obniża prawdopodobieństwo poprawnej odpowiedzi); próg ustalony po obejrzeniu tego przebiegu, nie przed nim; (2) wynik różni się od `results/central-run` przy tej samej rewizji i wagach; (3) WikiText liczony oknem dłuższym niż okno modelu. Spełnienie (1) albo (2) flaguje wszystkie wyniki modelu.

- **Bielik-11B-v3-Base** (wszystkie testy), niepoliczone: tokenizer: add_prefix_space=true w tokenizer_config wymusza budowę slow tokenizera, a repo nie ma tokenizer.model (transformers 4.57.6).
- **Bielik-11B-v3.0-Instruct** (EWoK), niepoliczone: ewok.py liczy tylko float32.

Różnice wobec `results/central-run` (ten sam model, rewizja i sha256 wag; tam lm_eval 0.4.13, tu 0.4.9.1):

| test | model | tu | central-run |
|---|---|---:|---:|
| ARC-Challenge | LFM2.5-1.2B-Base | 0,2517 | 0,5094 |
| MedMCQA | LFM2.5-1.2B-Base | 0,2611 | 0,4059 |
| PubMedQA | LFM2.5-1.2B-Base | 0,5680 | 0,6380 |
| Social IQa | LFM2.5-1.2B-Base | 0,3398 | 0,4284 |

</details>

<details>
<summary><b>Pliki i odtworzenie</b></summary>

### Pliki i odtworzenie

| plik | zawartość |
|---|---|
| `<test>/<model>/results.json` | wynik w schemacie Space (obserwacja, protokół, provenance) |
| `<test>/<model>/results_rozszerzone.json` | to samo + metryki dodatkowe, SE, CI95, bazy, wersja lm_eval, dtype |
| `<test>/<model>/scores-history-wiersz.csv` | wiersz w formacie scores-history.csv |
| `manifest.jsonl` | jedna linia na parę model × test: repo, rewizja, env, dtype, komenda, czas, karta, sha256 wag, runnera i każdego pliku; SE w skali wartości z tego wiersza |
| `srodowisko.json` | commit fabryki, karta i stan środowisk `lock` i `new` |
| `czasy.jsonl` | start, koniec i czas każdej pary oraz pobierania wag |
| `przeglad.jsonl` | flaga, uwagi, kontaminacja, baza b, wersja lm_eval i `w_tabeli_codesota` każdego wyniku |
| `sizes.json` | liczba parametrów każdego modelu policzona z wag |
| `progresja.json` | porównania parowane wersji Slayera z tabel wyżej |
| `bos-window-check/` | pomiar BOS i okna na Pythii oraz kontrola ARC-Challenge: protokół, raport, liczby, kod, wyniki bez próbek |
| `charts/` | wykresy SVG z wartości tego katalogu |

Próbki per pytanie (logprob każdej odpowiedzi, prompt, hash dokumentu) i logi par są w paczce `eksport_glowny_pelny.tgz` (sha256 `c91c940b8843a102399f1bc1052d564728781df85071f3701660ea5ccecd4317`), poza repo, bo skompresowane mają kilkaset MB.

Odtworzenie jednej pary (komenda z `manifest.jsonl`, pole `komenda`, albo przez runner):

```bash
python tools/ewaluacja/ewaluacja.py --wyniki wyniki licz slayer1b-1.06 --zadania T02 --pobierz
```

Cały przebieg: te same kolejki co tutaj, jedna na kartę (`CUDA_VISIBLE_DEVICES`), `--zadania gotowe --pobierz --usun-wagi`, potem `ewaluacja.py eksport`. Ten plik i wykresy: `python tools/ewaluacja/raport.py results/full-run-2026-11 results/full-run-2026-11 --bez-porownan --odniesienie results/central-run`.

</details>
