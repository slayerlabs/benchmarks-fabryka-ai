# IFBench

Wersja angielska: [README.md](README.md).

Czy model przestrzega nowych, trudniejszych, sprawdzalnych ograniczeń wyjścia ("use exactly 3 palindromes", "end
every sentence with a different punctuation mark") na prawdziwych promptach użytkowników. Sprawdzają to reguły, bez
modelu-sędziego.

- Publikacja: [Pyatkin et al. 2025, Generalizing Verifiable Instruction Following](https://arxiv.org/abs/2507.02833)
- Harness: [allenai/IFBench](https://github.com/allenai/IFBench) @ `488918665d53f867fa908a293769ec6e71e74aec`
  (`generate_responses.py`, `run_eval`)
- Dane: [allenai/IFBench_test](https://huggingface.co/datasets/allenai/IFBench_test) @
  `ed7c12452594b7028b15807b86d3938150b663ae`, 300 promptów (cały zbiór, jedna tura)
- Metryka: prompt-level strict accuracy (`follow_all_instructions` w `eval_results_strict`); wyniki na poziomie
  instrukcji i wyniki loose są w `other_metrics`
- Ustawienia: jedna tura, 1 próba. Bielik: temperatura 0.6, top_p 0.95, do 31 238 tokenów wyjścia (ustawienia
  domyślne z karty LFM3-1.7B, zob. Odstępstwa). Slayer: greedy, do 1280 tokenów wyjścia, surowy prompt
- Dodatkowe usługi: brak

## Wyniki

| model | score | stderr | n | data |
|---|---|---|---|---|
| Bielik 11B v3.1, własny vLLM (`bielik-11b-v3.1-vllm`) | 18.33 | 2.23 | 300 | 2026-11-19 |
| Slayer 1B, krok 60000 (`slayer1b-60000`) | 8.33 | 1.60 | 300 | 2026-11-19 |
| LFM3-1.7B, karta modelu | 73.03 | | | |

Wobec pustej odpowiedzi (która tu nie spełnia żadnego ograniczenia, więc ma wynik 0) Bielik jest wyżej o 18.33 ±
2.23 punktu (test parami, z = 8.2). Slayer też przechodzi ten test (z = 5.2), ale nie wygrywa z innymi trywialnymi
odpowiedziami: powtórzenie promptu daje 13.00 (39/300), a własne wyjścia Slayera przetasowane między promptami dają
to samo 25/300 (McNemar p = 1.0). Wynik 8.33 Slayera należy czytać jako dno dla zdegenerowanego wyjścia, a nie
jako wykonywanie instrukcji. Każdy wiersz `results/<model-id>.jsonl.gz` zawiera klucz zadania, wynik 0/1, flagi
strict i loose dla każdej instrukcji, prompt i surowy `output`.

## Odstępstwa

- **Własny vLLM, nie API fabryka.ai.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) jest serwowany przez vLLM 0.34.0 na wynajętym NVIDIA RTX PRO
  5000 Blackwell (`vllm.sh`), z domyślnymi ustawieniami szablonu czatu, w tym z promptem systemowym dostawcy, i z
  datą ustawioną na 2026-11-18. To konfiguracja wierszy `-vllm` benchmarku IFEval (#313), a nie wiersza API: w
  IFEval oba różniły się o około 5 punktów.
- **top_p jest ustawione na serwerze.** `generate_responses.py` wysyła tylko temperaturę, max_tokens i seed, więc
  top_p 0.95 z karty jest ustawieniem domyślnym serwera (`--override-generation-config`), widocznym w logu startowym
  vLLM.
- **Limit wyjścia 31 238 zamiast "bez limitu".** Karta nie podaje limitu wyjścia; serwowany kontekst to 32 768
  tokenów, a najdłuższy prompt zbioru z szablonem czatu ma 1 530 tokenów. Żaden prompt nie został ucięty.
- **Jeden seed dla wszystkich zapytań.** `generate_responses.py` wysyła ten sam `seed` (20261119) z każdym
  zapytaniem, więc próbkowanie jest powtarzalne dla danego promptu na tym samym serwerze, ale prompty nie dostają
  niezależnych seedów.
- **Dane z Hugging Face, nie kopia z repozytorium.** Przypięta rewizja na Hugging Face różni się od dołączonego do
  repozytorium `data/IFBench_test.jsonl` w 2 z 300 promptów (klucze 13 i 19); używamy wersji z Hugging Face
  (`convert_hf.py`, który dodatkowo zamienia z powrotem na liczby całkowite argumenty zapisane w parquet jako float).
- **Zapytania idą w partiach.** 32 zapytania naraz, łączone w partie przez vLLM.
- **Slayer to model bazowy** bez szablonu czatu: dostaje surowy prompt i dekoduje greedy do 1280 tokenów, tak jak w
  benchmarku IFEval (#313). Jego kontekst to 4096 tokenów. Wagi:
  [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints) @
  `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt` (krok treningu 60000). Działał na wynajętym NVIDIA
  GeForce RTX 4090 w fp32 (TF32 wyłączone) z pamięcią KV, po jednym prompcie naraz (`slayer_lm.py`). 280 z 300 wyjść
  kończy się na limicie 1280 tokenów, a 1 jest puste. Jego wyjścia ocenił ten sam `run_eval`.
- **Kod modelu Slayera.** `slayer_package.py` wczytuje checkpoint do klasy GPT z publicznego trenera
  `train_gpt_ref_r24_2.py` (SlayerLab/Slayer1B-1.09 @ `58d8f359c1fdd887f1b7344ec52c5511c111f790`), z tokenizerem
  SlayerLab/Slayer1B-1.08 @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`. Raportowany bieg używał wcześniejszej
  rewizji trenera, której klasy modelu mają identyczny kod źródłowy; ponowne zbudowanie paczki przez
  `slayer_package.py` daje identyczne bit w bit wagi (202/202 tensorów) i identyczne logity (max |Δ| = 0.0 na 3
  promptach) jak paczka użyta do tych wyników.
- **Pliki przykładowe w harnessie.** Repozytorium IFBench zawiera `eval/eval_results_{strict,loose}.jsonl` (294
  wiersze, nie nasze); `run_eval` zapisuje nasze jako `eval/<model-id>-eval_results_*.jsonl` i czytane są tylko one.

## Jak powtórzyć

```bash
HF_TOKEN=hf_... bash vllm.sh                # jedno GPU z co najmniej 48 GB; serwuje na 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # w drugiej powłoce
bash run.sh slayer1b-60000                  # lokalne GPU CUDA z co najmniej 24 GB; pobiera publiczne wagi kroku 60000
```

`--limit 5` uruchamia tylko pierwsze 5 promptów i zapisuje do `out/limit/`. `BASE_URL` kieruje `run.sh` na inny
endpoint, który serwuje model jako `bielik`.
