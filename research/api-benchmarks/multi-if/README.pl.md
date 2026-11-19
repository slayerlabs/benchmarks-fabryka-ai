# Multi-IF

Wersja angielska: [README.md](README.md).

Czy model nadal wykonuje instrukcje w trzyturowej rozmowie w ośmiu językach: każda tura dokłada instrukcje w stylu
IFEval (długość, format, słowa kluczowe, język, ...) do wcześniejszych, a odpowiedź z każdej tury sprawdzają reguły
weryfikatorów harnessu, bez modelu-sędziego.

- Publikacja: [Multi-IF: Benchmarking LLMs on Multi-Turn and Multilingual Instructions Following](https://arxiv.org/abs/2410.15553)
- Harness: [facebookresearch/Multi-IF](https://github.com/facebookresearch/Multi-IF) @
  `1cdb53ed18499ad729e0766e5d3099dd5344406f` (`multi_turn_instruct_following_eval_api.py`, `metrics.py`), z
  `patch_api_client.py` (zob. Odstępstwa)
- Dane: [facebook/Multi-IF](https://huggingface.co/datasets/facebook/Multi-IF) @
  `0ab97ce0b45c7f57772e8ba2ac1616f4b00bd3aa`, `multiIF_20241018.csv` (sha256
  `6c588af031fe67b17c535b9ba0ccc14a1b9d77b4faf88c294f83aaa5a3000018`): 4501 rozmów; 4501 ma drugą turę, a 4445
  trzecią, czyli 13 447 ocenianych tur
- Metryka: dla każdej tury `all_languages_overall` harnessu (średnia z prompt-level strict, instruction-level strict,
  prompt-level loose i instruction-level loose po wszystkich językach); wynik to średnia z trzech tur, jak na Fig. 1
  publikacji ("average ... across all languages and across all turns"). Wartości dla tur, cztery składowe i wyniki
  dla języków są w `other_metrics`
- Ustawienia: trzy tury, 1 próba. Bielik: temperatura 0.6, top_p 0.95, seed 20261119, do 8192 nowych tokenów na
  turę. Slayer: greedy, do 1280 nowych tokenów na turę, surowy tekst
- Dodatkowe usługi: brak

## Wyniki

| model | score | stderr | n | data |
|---|---|---|---|---|
| Bielik 11B v3.1, własny vLLM (`bielik-11b-v3.1-vllm`) | 48.66 | 0.44 | 13447 | 2026-11-19 |
| Slayer 1B, krok 60000 (`slayer1b-60000`) | null | null | 0 | 2026-11-19 |
| LFM3-1.7B, karta modelu | 89.10 | | | |

`n` liczy ocenione tury; `n_conversations` w plikach wyników to 4501.

Wynik overall Bielika spada z każdą turą: 62.21, 46.32 i 37.44 dla tur od 1 do 3; prompt-level strict spada z 56.39 do
29.95 i 15.28, a instruction-level strict zostaje między 64.33 a 56.54. Wszystkie 13 447 zapytań dostały odpowiedź
(żadna tura nie została oceniona jako niezaliczona z powodu błędu). W turze 1 wynik dla języków waha się od 68.78
(angielski) do 54.03 (rosyjski).

Odpowiedzi trywialne nie mają tu wyniku 0: powtórzenie instrukcji z danej tury daje 28.73 prompt-level strict w
turze 1, własne odpowiedzi modelu przetasowane między rozmowami w tym samym języku 10.89, a pusta odpowiedź 0.00.
Wynik Bielika 56.39 jest wyżej od wszystkich trzech (McNemar wobec przetasowanych odpowiedzi: p poniżej 1e-160 w
każdej z trzech tur).

Slayer nie ma wyniku: bieg przerwano po 2 z 3 tur ze względu na budżet obliczeń (tura 3 szła w tempie około 10
rozmów na minutę), więc `results/slayer1b-60000.json` ma `score: null` i nie ma `.jsonl.gz`. Jego `other_metrics`
przepisują overall dla wszystkich języków i dla każdego języka z tur 1 i 2 z plików metryk, które harness zapisał w
trakcie biegu (tura 1: 23.65, tura 2: 15.82). To wartości harnessu, nieprzeliczone: jedno nieudane zapytanie w turze 2
harness ocenia po swojemu, a nie jako pustą odpowiedź. Dla przerwanego biegu nie ma porównania z odpowiedziami
trywialnymi.

Każdy wiersz `results/<model-id>.jsonl.gz` to jedna oceniona tura: klucz rozmowy, tura, język, werdykty strict i
loose dla każdej instrukcji, informacja, czy tura została oceniona jako niezaliczona z powodu nieudanego zapytania,
i surowy `output`.

## Odstępstwa

- **Agregacja tur.** Karta LFM3-1.7B podaje jedną liczbę dla Multi-IF i nie mówi, jak agreguje tury. Używamy średniej
  z trzech tur z `all_languages_overall` harnessu, czyli agregatu z Fig. 1 publikacji; wartości dla tur są w
  `other_metrics`.
- **Nieudane zapytania są oceniane jako niezaliczone.** Tura, której zapytanie się nie powiodło (status harnessu inny
  niż `success`), nie ma odpowiedzi modelu, a harness oceniłby tekst błędu. `summarize.py` ocenia tę turę i dalsze
  tury tej samej rozmowy z pustą odpowiedzią, czyli jako niezaliczone, w pełnym N, i liczy je dla każdej tury. 56
  rozmów bez trzeciej tury nie ma zapytania w turze 3 (harness oznacza ten wiersz jako `exception`) i są poza N tury
  3, tak jak w `metrics.py`.
- **Błąd standardowy (SE).** Tury jednej rozmowy nie są niezależne, więc SE pochodzi z bootstrapu klastrowego po
  rozmowach (wszystkie trzy tury razem), 1000 losowań, seed 20261119.
- **Ocena nie jest w pełni deterministyczna.** Reguły języka w harnessie wywołują `langdetect.detect`, a nic w
  harnessie na przypiętym commicie nie ustawia `DetectorFactory.seed`, którego langdetect potrzebuje do powtarzalnych
  wyników. Ponowna ocena tych samych odpowiedzi przez `metrics.py` harnessu przesunęła wyniki tur o najwyżej 0.013
  punktu względem plików metryk, które harness zapisał w trakcie biegu (Bielik: 62.212 / 46.307 / 37.432).
- **Własny vLLM, nie API fabryka.ai.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) jest serwowany przez vLLM 0.34.0 na wynajętym NVIDIA RTX PRO
  5000 Blackwell (`vllm.sh`), z domyślnymi ustawieniami szablonu czatu, w tym z promptem systemowym dostawcy, i z
  datą ustawioną na 2026-11-18. To konfiguracja wierszy `-vllm` benchmarku IFEval (#313), a nie wiersza API.
- **Limit wyjścia 8192 na turę zamiast "bez limitu".** Harness wysyła jeden stały `max_new_tokens` dla każdej tury;
  karta nie podaje limitu. Przy 8192 trzy odpowiedzi zajmują najwyżej 24 576 z 32 768 tokenów kontekstu.
- **Poprawiony klient API.** `patch_api_client.py` wprowadza dwie zmiany w `api_client.py` harnessu: biblioteki
  Anthropic, Gemini i Mistral są importowane wewnątrz swoich backendów (pakiety Gemini i Mistral kłócą się ze
  środowiskiem vLLM), a `bielik` i `slayer` są dopisane do nazw modeli backendu zgodnego z OpenAI. Zachowanie żadnego
  backendu się nie zmienia. `run.sh` kieruje ten backend na lokalny serwer (`OPENAI_BASE_URL`,
  `OPENAI_API_KEY=EMPTY`).
- **Slayer to model bazowy** bez szablonu czatu i z oknem 4096 tokenów: `slayer_server.py` łączy rozmowę w tekst
  "User: ... Assistant: ..." i dekoduje greedy do 1280 tokenów na turę. Tura, której wejście plus 1280 tokenów nie
  mieści się w 4096, jest odrzucana (HTTP 400) i oceniana jako niezaliczona, razem z dalszymi turami rozmowy. Wagi:
  [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints)
  @ `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt`, wczytywane przez `slayer_package.py` do klasy GPT z
  publicznego trenera `train_gpt_ref_r24_2.py`; ponowne zbudowanie paczki przez `slayer_package.py` daje identyczne
  bit w bit wagi (202/202 tensorów) i identyczne logity (max |Δ| = 0.0 na 3 promptach) jak paczka użyta do tych
  wyników. Działał na wynajętym NVIDIA GeForce RTX 4090 w fp32 (TF32 wyłączone) z pamięcią KV, 32 zapytania w
  partii (`slayer_batch.py`).
- **Zapytania idą w partiach.** 32 rozmowy naraz (`--max_workers 32`), łączone w partie przez serwer.

## Jak powtórzyć

```bash
HF_TOKEN=hf_... bash vllm.sh                # jedno GPU z co najmniej 48 GB; serwuje na 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # w drugiej powłoce
bash run.sh slayer1b-60000                  # jedno GPU CUDA z co najmniej 24 GB; sam uruchamia slayer_server.py
```

`--limit 5` zostawia tylko pierwsze 5 rozmów (ze wszystkimi turami) i zapisuje do `out/limit/`. `BASE_URL` kieruje
`run.sh` na inny endpoint, który serwuje model jako `bielik`. `requirements.txt` przypina środowisko harnessu.
