# BLiMP: karta oryginału (etap A)

Karta oryginalnego benchmarku, spisana z pracy, repozytorium autorów i karty zbioru.
Nasze wyniki: [`README.md`](README.md); stan odtworzenia: [`REPRODUCTION.md`](REPRODUCTION.md).

## Co mierzy

Słowami autorów: "a challenge set for evaluating the linguistic knowledge of language models (LMs) on major
grammatical phenomena in English" (zestaw do sprawdzania wiedzy językowej modeli o głównych zjawiskach gramatyki
angielskiej). Sprawdza, czy model "assigns a higher probability to the acceptable sentence in each minimal pair",
czyli czy daje wyższe prawdopodobieństwo zdaniu poprawnemu w każdej parze minimalnej.

## Źródła

- Praca: Warstadt, Parrish, Liu, Mohananey, Peng, Wang, Bowman, "BLiMP: The Benchmark of Linguistic Minimal
  Pairs for English", TACL 8 (2020), strony 377-392.
  - wersja TACL: [ACL Anthology `2020.tacl-1.25`](https://aclanthology.org/2020.tacl-1.25/) <!-- liczba-spoza-wynikow: identyfikator pracy w adresie URL -->
  - wersja poprawiona (errata z 16 sierpnia 2021, patrz „Znane rozbieżności”): [arXiv `1912.00582v4`](https://arxiv.org/abs/1912.00582v4) <!-- liczba-spoza-wynikow: identyfikator pracy w adresie URL -->
- Repozytorium autorów (dane, poprawiony PDF, wyniki modeli per paradygmat):
  [`alexwarstadt/blimp` @ `3e56b06`](https://github.com/alexwarstadt/blimp/tree/3e56b06fcabca9b30822fc66435fca6b1aa40bb1)
  (ostatni commit, 2022-12-13).
- Kod generowania danych: [`alexwarstadt/data_generation` @ `4aba4ac`](https://github.com/alexwarstadt/data_generation/tree/4aba4ac921cd8dc91eda774cc96fedf8af540417).
- Kod oceny użyty w pracy dla GPT-2 i Transformer-XL (jiant, gałąź `blimp-and-npi`):
  [`nyu-mll/jiant` @ `244c9d8`, `scripts/blimp`](https://github.com/nyu-mll/jiant/tree/244c9d895236c3446c4c36060283645a57a3175a/scripts/blimp).
- Karta zbioru na Hugging Face (kopia, której używamy):
  [`nyu-mll/blimp` @ `877fba0`](https://huggingface.co/datasets/nyu-mll/blimp/tree/877fba0801ffb7cbd8c39c1ff314a46f053f6036)
  (pełna rewizja `877fba0801ffb7cbd8c39c1ff314a46f053f6036`, 67 plików parquet).
- Popularna implementacja: grupa zadań lm-eval `blimp`,
  [`lm_eval/tasks/blimp/_template_yaml` @ `6d2abda`](https://github.com/EleutherAI/lm-evaluation-harness/blob/6d2abda4fd171e68a8789330c4149e37c1ca0bda/lm_eval/tasks/blimp/_template_yaml).

## Dane

- 67 paradygmatów („podzbiorów”) x 1000 par minimalnych = 67 000 par, wygenerowanych z szablonów gramatycznych
  napisanych przez językoznawców, ze słownikiem ponad 3 000 słów. Każda para ma: `sentence_good`,
  `sentence_bad`, a także `field`, `linguistics_term` (12 zjawisk), `UID` (paradygmat), `pairID` i flagi metod
  (`simple_LM_method`, `one_prefix_method`, `two_prefix_method`, `lexically_identical`).
- Split: tylko jeden (`train` na Hugging Face); praca podaje wyniki na wszystkich 67 000 parach. Odpowiedzi nie
  są ukryte: zdanie poprawne jest w danych.
- Walidacja przez ludzi: 20 osób ocenia każdą parę, po 5 par z każdego paradygmatu (6 700 ocen); praca podaje
  zgodność zbiorczą 96,4% i zgodność pojedynczej osoby 88,6% (wiersz „Human” w Tabeli 3). <!-- liczba-spoza-wynikow: zgodność ludzi z pracy, sekcja 3.4 -->
- Licencja: CC-BY 4.0 (README autorów).

## Format zadania

Para minimalna, wymuszony wybór między dwoma pełnymi zdaniami, zero-shot, bez kontekstu. Model ocenia każde
zdanie osobno (nigdy nie widzi obu naraz).

## Prompt

W oryginale nie ma promptu: główna metoda pracy („full-sentence”, „simple LM method”) porównuje
prawdopodobieństwo obu pełnych zdań. Czy jiant dokleja dla GPT-2 token startowy albo spację na początku:
nieustalone (szukałem w pracy, sekcje 4 i 6, i w README autorów; skryptów jiant nie czytałem linijka po
linijce).

lm-eval w `6d2abda`: `doc_to_text: ""`, `doc_to_choice: [sentence_good, sentence_bad]`, `doc_to_target: 0`,
`num_fewshot: 0`, domyślny `target_delimiter` `" "`. Każde zdanie jest więc oceniane jako `" " + sentence` po
jednym nieocenianym tokenie startowym (BOS albo EOT, gdy tokenizer nie ma BOS).

## Ocena

- Metryka: trafność; para jest trafiona, gdy `P(sentence_good) > P(sentence_bad)`, czyli przy sumie
  log-prawdopodobieństw tokenów zdania. Bez normalizacji długości (oba zdania pary mają zwykle tyle samo słów,
  z konstrukcji; liczba tokenów może się różnić).
- Bez normalizacji tekstu odpowiedzi (nic nie jest generowane).
- Remisy: dla pracy nieustalone (w tekście nie znalazłem reguły). lm-eval bierze argmax z dwóch opcji, co przy
  remisie wybiera pierwsze (poprawne) zdanie, więc remis liczy się jako trafienie.
- Praca podaje też dwie metody prefiksowe (one-prefix, two-prefix) na podzbiorach oznaczonych flagami; to
  dodatkowy eksperyment, nie główny wynik.

## Agregacja

Ogółem = odsetek trafionych par spośród 67 000. Każdy paradygmat ma 1000 par, więc to to samo co średnia bez wag
z 67 paradygmatów. Grupa lm-eval `blimp` łączy 67 trafności podzadań przez `aggregation: mean`,
`weight_by_size: False`, co daje tę samą liczbę. Wynik zjawiska (12 grup) to średnia z jego paradygmatów.

## Wyniki referencyjne

Z poprawionej wersji arXiv, Tabela 3 (trafność w procentach, wymuszony wybór, wszystkie 67 000 par):

- GPT-2 (GPT-2-large, 774M parametrów): ogółem 83,0 <!-- liczba-spoza-wynikow: Tabela 3 pracy, poprawiona wersja arXiv v4 -->
- Transformer-XL 69,6, LSTM 69,8, 5-gram 61,2 <!-- liczba-spoza-wynikow: Tabela 3 pracy, poprawiona wersja arXiv v4 -->
- Ludzie 88,6 <!-- liczba-spoza-wynikow: Tabela 3 pracy, poprawiona wersja arXiv v4 -->

Wyniki tych modeli per paradygmat: plik autorów
[`raw_results/summary/models_summary.jsonl`](https://github.com/alexwarstadt/blimp/blob/3e56b06fcabca9b30822fc66435fca6b1aa40bb1/raw_results/summary/models_summary.jsonl).

Model do pobrania z opublikowanym wynikiem BLiMP: `EleutherAI/pythia-1b-v0` @ `step143000`, średnia z 67 wartości
`blimp_*` w pliku
[`evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`](https://github.com/EleutherAI/pythia/blob/a19eecb807ec2c79a39ebf18108816e6ffffc1d5/evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json)
(model: [`EleutherAI/pythia-1b-v0` @ `step143000`](https://huggingface.co/EleutherAI/pythia-1b-v0/tree/step143000)).
Średnia wynosi 0,8234 (liczona starym harnessem lm-eval, bez spacji na początku zdania). Katalogi wyników v1 w
repo Pythii nie mają BLiMP.

## Znane rozbieżności

- **Errata w wersji TACL.** README autorów (16 sierpnia 2021): część wyników w Tabelach 3 i 4 wersji TACL podano
  błędnie; cytować wersję arXiv albo pliki wyników. Tabela 3 w TACL podaje GPT-2 80,1, arXiv v4 podaje 83,0. <!-- liczba-spoza-wynikow: Tabela 3 z TACL i arXiv v4, żeby pokazać erratę -->
- **Spacja na początku.** lm-eval (obecny) ocenia `" " + sentence`; stary harness użyty do wyników Pythii v0
  ocenia zdanie bez niej. Przy tokenizerze BPE zmienia to pierwszy token.
- **Token startowy.** lm-eval warunkuje na jednym tokenie BOS/EOT. Jak to było w pracy: nieustalone.
- **Rewizja zbioru.** lm-eval wczytuje `dataset_path: blimp` bez przypiętej rewizji; my przypinamy
  `nyu-mll/blimp` @ `877fba0`.
- **Etykiety zjawisk.** `linguistics_term` na Hugging Face ma wartość `s-selection`; 12 zjawisk w pracy włącza
  ją do struktury argumentowej (Tabela 4). Nasza tabela zjawisk robi tak samo.
- **Pary zdegenerowane.** 7 par ma identyczne zdanie poprawne i błędne (paradygmaty `passive_1`,
  `principle_A_case_2`). lm-eval liczy je jako remis, czyli trafienie.
- **Kontaminacja.** Zdania BLiMP są syntetyczne, ale zbiór jest publiczny od 2019 roku. Dla mierzonych tu
  modeli nie skanowana (patrz [`results/BLIMP.md`](results/BLIMP.md), „Deviations from METHOD.md and limits”).
