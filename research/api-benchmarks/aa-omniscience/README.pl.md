# AA-Omniscience (public)

Wersja angielska: [README.md](README.md).

Czy model zna fakty z sześciu dziedzin, a gdy ich nie zna, mówi to zamiast zgadywać. Model-sędzia ocenia każdą
krótką odpowiedź jako poprawną, częściowo poprawną, błędną albo bez próby odpowiedzi; Omniscience Index nagradza
poprawne odpowiedzi i karze błędne, więc wstrzymanie się od odpowiedzi wychodzi lepiej niż błędny strzał.

- Publikacja: [AA-Omniscience: Evaluating Cross-Domain Knowledge Reliability in Large Language Models](https://huggingface.co/datasets/ArtificialAnalysis/AA-Omniscience-Public)
  (Artificial Analysis; PDF w repozytorium zbioru)
- Harness: prompt odpowiedzi i szablon oceniającego z README zbioru (`OMNISCIENCE_ANSWER_PROMPT`,
  `OMNISCIENCE_GRADER_TEMPLATE`), wycięte dosłownie przez `prepare.py`; `generate.py` pyta model, `judge.py` ocenia
- Dane: [ArtificialAnalysis/AA-Omniscience-Public](https://huggingface.co/datasets/ArtificialAnalysis/AA-Omniscience-Public)
  @ `e4883edbb9f5ccf2b2a8fdc6fb65e01a58e99849`, 600 pytań (cały zbiór publiczny, 6 dziedzin x 100)
- Metryka: Omniscience Index, OI = 100 (correct - incorrect) / N; accuracy, odsetek halucynacji (błędne / wszystkie
  niepoprawne) i liczby ocen w `other_metrics`
- Ustawienia: jedna tura, 1 próba, jedno przejście sędziego. Bielik: temperatura 0.6, top_p 0.95, bez limitu
  wyjścia poza kontekstem (ustawienia domyślne z karty LFM3-1.7B). Slayer: greedy, do 1280 tokenów wyjścia, surowy
  tekst
- Dodatkowe usługi: model-sędzia (zob. Odstępstwa)

## Wyniki

| model | score | stderr | n | data |
|---|---|---|---|---|
| Bielik 11B v3.1, własny vLLM (`bielik-11b-v3.1-vllm`) | -77.33 | 2.58 | 600 | 2026-11-19 |
| Slayer 1B, krok 60000 (`slayer1b-60000`) | -59.33 | 2.14 | 600 | 2026-11-19 |
| LFM3-1.7B, karta modelu | 0.50 | | | |

Bielik odpowiada poprawnie na 67 z 600 pytań (accuracy 11.17 ± 1.29), błędnie na 531 i częściowo poprawnie na 2, a
"I don't know" nie odpowiada na żadne (odsetek halucynacji 99.62). Wobec stałej odpowiedzi "I don't know." jego OI
jest niższy o 77.33 ± 2.58 punktu (test parami, z = -30.0), a accuracy jest wyższe od 0 tej stałej (z = +8.7).
Żadna z jego odpowiedzi nie kończy się na limicie długości.

OI trzeba czytać razem z accuracy i odsetkiem halucynacji. Bielik wie więcej niż Slayer (accuracy 11.17 wobec
1.67), ale ma niższy OI (-77.33 wobec -59.33), bo OI odejmuje każdą błędną odpowiedź, a Bielik nigdy nie wstrzymuje
się od odpowiedzi, podczas gdy Slayer nie próbuje odpowiedzieć na 223 pytania.

Slayer odpowiada poprawnie na 10 z 600 pytań (accuracy 1.67 ± 0.52), błędnie na 366, częściowo poprawnie na 1 i nie
próbuje odpowiedzieć na 223. Wobec stałej odpowiedzi "I don't know." (OI 0, accuracy 0) jego OI jest niższy o
59.33 ± 2.14 punktu (test parami, z = -27.7): model bazowy zgaduje zamiast się wstrzymać. 598 z jego 600 odpowiedzi
kończy się na limicie 1280 tokenów, a sędzia ocenia cały tekst.

Żeby ograniczyć kontaminację, każdy wiersz `results/<model-id>.jsonl.gz` zawiera tylko id pytania, dziedzinę, ocenę
i wynik (+1 / 0 / -1), z `output` ustawionym na null. W tym katalogu nie ma treści pytań ani odpowiedzi modeli.

## Odstępstwa

- **Model-sędzia.** README AA-Omniscience podaje jako oceniającego Gemini 2.5 Flash Preview (09-2025). Nasze oceny
  pochodzą z GPT-6.1 Sol (thinking high), wywoływanego przez klienta wiersza poleceń, z oficjalnym szablonem
  oceniającego jako jedyną wiadomością i odpowiedzią w postaci dokładnie jednej litery. `judge.py` wysyła ten sam
  prompt do dowolnego endpointu zgodnego z OpenAI (`JUDGE_BASE_URL`, `JUDGE_MODEL`, `JUDGE_API_KEY`), więc powtórka
  z innym sędzią może dać inne wyniki. Przed oceną muszą przejść wszystkie 12 kontroli (4 pytania x {wzorcowa
  odpowiedź -> A, wzorcowa odpowiedź innego pytania -> B, "I don't know." -> D}); przeszły (12/12). Każda odpowiedź
  jest oceniana raz, w jednym przejściu sędziego bez powtórzeń, tak jak robi to AA; wszystkie 600 dostały ocenę w tym
  przejściu. `judge.py` buduje te same 612 promptów (12 kontroli + 600 odpowiedzi), bajt w bajt, co oceniający, który
  dał nasze oceny, a jego parser zamienia zapisane odpowiedzi sędziego na te same 600 ocen.
- **Własny vLLM, nie API fabryka.ai.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) jest serwowany przez vLLM 0.34.0 na wynajętym GPU (NVIDIA
  RTX 6000 Ada Generation) (`vllm.sh`), z domyślnymi ustawieniami szablonu czatu, w tym z promptem systemowym
  dostawcy, i z datą ustawioną na 2026-11-18. To konfiguracja wierszy `-vllm` benchmarku IFEval (#313), a nie
  wiersza API.
- **Seed dla każdego pytania.** Zapytania Bielika mają seed 20261119 + indeks pytania.
- **Slayer to model bazowy** bez szablonu czatu: `slayer_server.py` zamienia prompt systemowy i pytanie na surowy
  tekst (system + pusta linia + pytanie) i dekoduje greedy do 1280 tokenów, tak jak w benchmarku IFEval (#313).
  Wagi: [SlayerLab/Slayer1B-1.09-checkpoints](https://huggingface.co/SlayerLab/Slayer1B-1.09-checkpoints)
  @ `dc3b6a9b0f87305da7ceca39ca27a79fa60b34cd`, `wagi_60000.pt`, wczytywane przez `slayer_package.py` do klasy GPT z
  publicznego trenera `train_gpt_ref_r24_2.py`; ponowne zbudowanie paczki przez `slayer_package.py` daje identyczne
  bit w bit wagi (202/202 tensorów) i identyczne logity (max |Δ| = 0.0 na 3 promptach) jak paczka użyta do tych
  wyników. Działał na wynajętym NVIDIA GeForce RTX 4090 w fp32 (TF32 wyłączone) z pamięcią KV, 32 zapytania w
  partii (`slayer_batch.py`). Flagi wiersza poleceń serwera są po angielsku (`--limit-mode fixed`, `--batch`,
  `--default-seed`); poza tym kod nie różni się od tego, który dał wynik.

## Jak powtórzyć

```bash
export JUDGE_BASE_URL=https://... JUDGE_MODEL=... JUDGE_API_KEY=...
HF_TOKEN=hf_... bash vllm.sh                # jedno GPU z co najmniej 48 GB; serwuje na 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # w drugiej powłoce
bash run.sh slayer1b-60000                  # lokalne GPU CUDA z co najmniej 24 GB; pobiera publiczne wagi kroku 60000
```

`--limit 5` zadaje tylko pierwsze 5 pytań i zapisuje do `out/limit/`; 12 kontroli sędziego i tak się wykonuje.
