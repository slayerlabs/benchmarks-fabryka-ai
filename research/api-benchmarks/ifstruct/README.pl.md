# IFStruct

Wersja angielska: [README.md](README.md).

Czy model tworzy poprawny JSON albo YAML zgodny ze schematem docelowym: właściwy format i ogrodzenie bloku kodu, bez
dodatkowego komentarza, wymagany kształt najwyższego poziomu i liczba elementów, a każde pole zgodne ze schematem.
Sprawdza to walidator harnessu, bez modelu-sędziego.

- Harness: [Liquid4All/ifstruct](https://github.com/Liquid4All/ifstruct) @ `73e03a6d3a8508357ba430675a106d4887abedf3`
  (`ifstruct-eval`)
- Dane: [LiquidAI/ifstruct-v1.0](https://huggingface.co/datasets/LiquidAI/ifstruct-v1.0) @
  `2e342ca5f2673fb1287411fdbadcdfde82b35682`, 2000 próbek (cały zbiór: 1000 JSON, 1000 YAML)
- Metryka: odsetek zaliczonych (próbka jest zaliczona tylko wtedy, gdy walidator nie zgłasza żadnego błędu);
  odsetki dla każdego formatu w `other_metrics`
- Ustawienia: jedna tura, 1 próba. Bielik: temperatura 0.6, top_p 0.95, do 29 603 tokenów wyjścia (ustawienia
  domyślne z karty LFM3-1.7B, zob. Odstępstwa). Slayer: greedy, do 1280 tokenów wyjścia, surowy tekst
- Dodatkowe usługi: brak

## Wyniki

| model | score | stderr | n | data |
|---|---|---|---|---|
| Bielik 11B v3.1, własny vLLM (`bielik-11b-v3.1-vllm`) | 30.95 | 1.03 | 2000 | 2026-11-19 |
| Slayer 1B, krok 60000 (`slayer1b-60000`) | 0.00 | 0.00 | 2000 | 2026-11-19 |
| LFM3-1.7B, karta modelu | 93.72 | | | |

Wobec pustej odpowiedzi (która nigdy nie przechodzi walidatora, więc ma wynik 0) Bielik jest wyżej o 30.95 ± 1.03
punktu (test parami, z = 29.9). Wszystkie 1381 porażek to błędy walidacji wyjścia, żadna nie jest błędem zapytania;
najczęstszy to brak bloku kodu tam, gdzie prompt go wymaga (651). Każdy wiersz `results/<model-id>.jsonl.gz` zawiera
seed próbki, wynik 0/1, format, typ encji, błędy walidatora, prompt i surowy `output`.

Slayer nie zalicza żadnej z 2000 próbek (JSON 0/1000, YAML 0/1000), tak samo jak pusta odpowiedź, więc nie da się go
tu odróżnić od odpowiedzi trywialnej. Model bazowy przy surowym prompcie dochodzi do limitu 1280 tokenów (2203 z
2216 generacji serwera, łącznie z ponowieniami) i nigdy nie tworzy poprawnego obiektu; najczęstsze błędy walidatora
to brak wymaganych pól i tekst tam, gdzie oczekiwany jest obiekt. Wszystkie 2000 próbek dostały odpowiedź (brak
błędów zapytań po ponowieniach, żadna poza oknem 4096 tokenów modelu: najdłuższy prompt ma 1975 tokenów).

## Odstępstwa

- **Własny vLLM, nie API fabryka.ai.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) jest serwowany przez vLLM 0.34.0 na wynajętym NVIDIA RTX PRO
  5000 Blackwell (`vllm.sh`), z domyślnymi ustawieniami szablonu czatu, w tym z promptem systemowym dostawcy, i z
  datą ustawioną na 2026-11-18. To konfiguracja wierszy `-vllm` benchmarku IFEval (#313), a nie wiersza API: w
  IFEval oba różniły się o około 5 punktów.
- **top_p jest ustawione na serwerze.** `ifstruct-eval` wysyła tylko temperaturę i max_tokens, więc top_p 0.95 z
  karty jest ustawieniem domyślnym serwera (`--override-generation-config`), widocznym w logu startowym vLLM. Harness
  nie ma opcji seeda, więc zapytania nie mają seeda.
- **Limit wyjścia 29 603 zamiast "bez limitu".** Karta nie podaje limitu wyjścia; serwowany kontekst to 32 768
  tokenów, a najdłuższy prompt zbioru z szablonem czatu ma 3 165 tokenów. Żaden prompt nie został ucięty.
- **Dane z Hugging Face.** Przypięta rewizja jest identyczna z dołączonym do repozytorium `data/test.jsonl` (0 z
  2000 próbek się różni); `convert_hf.py` zamienia kolumny parquet zapisane jako tekst JSON z powrotem na obiekty.
- **Zapytania idą w partiach.** Bielik: 32 zapytania naraz, łączone w partie przez vLLM; harness ponawia nieudane
  zapytanie dwa razy. Żadne zapytanie nie zakończyło się błędem.
- **Slayer to model bazowy** bez szablonu czatu: `slayer_server.py` przekazuje prompt jako surowy tekst i dekoduje
  greedy do 1280 tokenów niezależnie od `max_tokens` (harness wysyła 4096), tak jak w benchmarku IFEval (#313).
  Wagi: [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints)
  @ `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt`, wczytywane przez `slayer_package.py` do klasy GPT z
  publicznego trenera `train_gpt_ref_r24_2.py`; ponowne zbudowanie paczki przez `slayer_package.py` daje identyczne
  bit w bit wagi (202/202 tensorów) i identyczne logity (max |Δ| = 0.0 na 3 promptach) jak paczka użyta do tych
  wyników. Działał na wynajętym NVIDIA GeForce RTX 4090 w fp32 (TF32 wyłączone) z pamięcią KV, 32 zapytania w
  partii (`slayer_batch.py`), 32 wątki harnessu.
- **Przekroczenia czasu po stronie klienta przy Slayerze.** Przy 32 wątkach odpowiedź z 1280 tokenów trwa średnio
  około 85 s; 216 zapytań przekroczyło limit odczytu harnessu 120 s, a 1 trafiło na zerwane połączenie. Każde
  zostało raz ponowione i dostało odpowiedź. Serwer dekoduje greedy i dla każdego z 216 promptów, które wygenerował
  dwa razy, obie generacje mają tę samą długość i ten sam powód zakończenia.

## Jak powtórzyć

```bash
HF_TOKEN=hf_... bash vllm.sh                # jedno GPU z co najmniej 48 GB; serwuje na 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # w drugiej powłoce
bash run.sh slayer1b-60000                  # jedno GPU CUDA z co najmniej 24 GB; sam uruchamia slayer_server.py
```

`--limit 5` uruchamia tylko pierwsze 5 próbek i zapisuje do `out/limit/`. `BASE_URL` kieruje `run.sh` na inny
endpoint, który serwuje model jako `bielik`.
