# IFEval (T36)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Pojęcia (Space, T01-T50, SE, werdykt):
> [słowniczek](../../METODOLOGIA.md#słowniczek).

IFEval sprawdza wykonywanie instrukcji sprawdzanych regułami (długość, format, język). Zadanie lm-eval: `ifeval`, split `train`, demonstracje: 0.
Metryka decyzyjna: `prompt_level_strict_acc`. Typ `ifeval` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).

Stan: podpięty do przebiegu centralnego (wpis `T36` w `common/zadania.py` i `KATALOGI`). Wyniki wariantu A (Bielik-11B-v3.1-Instruct) i przebiegi kontrolne Pythii-1b są w `results/`. Karta oryginału (etap A): [`ORIGINAL.md`](ORIGINAL.md). Odtworzenie (etap B): [`REPRODUCTION.md`](REPRODUCTION.md), werdykt zostaje dla recenzenta.

## Wyniki (n = 541, protokół `bench50-v0.3.1-fullB`)

| model | `prompt_level_strict_acc` | trafienia | BOS | dtype |
|---|---:|---:|---|---|
| Bielik-11B-v3.1-Instruct (wariant A) | 0,3715 (loose 0,3919 = 212/541) | 201/541 | 1 | bf16 |
| `pythia-1b` (kontrola, 1 BOS) | 0,2033, CI95 [0,1701; 0,2384] | 110/541 | 1 | float32 |
| `pythia-1b` (diagnostyka, 0 BOS) | 0,1701, CI95 [0,1384; 0,2017] (przybliżenie normalne) | 92/541 | 0 | float32 |

Wartość referencyjna 0,168207 (91/541), okno odtworzenia [0,136; 0,200]. Wynik kontroli 1 BOS leży ok. 2 prompty powyżej okna, więc warunek etapu B formalnie nie przechodzi o włos. Przebieg 0 BOS (w oknie) jest diagnostyką i nie zmienia tej oceny. Szczegóły i test McNemara 1 BOS vs 0 BOS: [`REPRODUCTION.md`](REPRODUCTION.md).

## Pliki

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A)
- [`REPRODUCTION.md`](REPRODUCTION.md): odtworzenie wyniku kontroli (etap B); [`REPRODUCTION.en.md`](REPRODUCTION.en.md): wersja angielska
- [`RECIPE.md`](RECIPE.md): komendy, środowisko, oba przebiegi BOS, luka odtwarzalności
- [`results/ifeval.json`](results/ifeval.json): liczby zbiorcze; `results/<model>/ifeval.jsonl.gz`: flagi per prompt (`bielik-11b-v3.1-instruct-variant-a`, `pythia-1b-1bos`, `pythia-1b-0bos`), bez odpowiedzi modelu (limit rozmiaru repo)

## Ustawienia poza YAML-em lm-eval

- Budżet generacji z YAML-a: 1280 tokenów.
- `langdetect` z seedem 0 ([METODOLOGIA, „Ustawienia przebiegu centralnego”](../../METODOLOGIA.md#ustawienia-przebiegu-centralnego), seedy); `langdetect` i `immutabledict` są w locku.
- Dane NLTK `punkt_tab` pobiera raz etap `przygotuj` przebiegu do `$WS/nltk_data` (`NLTK_DATA`) przed
  ewaluacją; bez nich lm-eval pobiera je przy imporcie.
- Kontekst najwyżej 4096 tokenów ([METODOLOGIA, „Ustawienia przebiegu centralnego”](../../METODOLOGIA.md#ustawienia-przebiegu-centralnego)): gdy prompt z budżetem generacji się nie mieści, demonstracje schodzą od końca, a prompt za długi bez demonstracji kończy zadanie błędem (`ewaluuj.ogranicz_kontekst`).
