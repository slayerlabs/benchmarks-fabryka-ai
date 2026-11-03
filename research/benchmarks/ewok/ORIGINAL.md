# EWoK: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Wersja
polska jest w [`../ewok-pl/`](../ewok-pl/README.md). Odczyt pracy, kodu i wyników autorów: 2026-11-03.

Materiały EWoK (zbiór, szablony, wyniki per rekord) autorzy udostępniają tylko w zipach z hasłem i proszą, by nie
publikować ich jawnym tekstem (TERMS_OF_USE). Ta karta nie cytuje więc żadnego rekordu. Podaje tylko liczby i
ścieżki.

| pole | wartość |
|---|---|
| Co mierzy | Podstawową wiedzę o świecie: czy model rozpoznaje, które zdanie pasuje do opisanej sytuacji. Autorzy mówią o „basic world knowledge” z 11 domen poznania (np. właściwości agentów, relacje przestrzenne, interakcje społeczne, dynamika materiałów) |
| Źródła | praca: Ivanova, Sathe, Lipkin i in. 2024, *Elements of World Knowledge (EWoK)*, [arXiv:2405.09605](https://arxiv.org/abs/2405.09605) (v1 z 15.05.2024, v2 z 3.07.2025; tabela wyników to Tabela A); repo autorów: [`ewok-core/ewok-paper`](https://github.com/ewok-core/ewok-paper/tree/9e40d30e242925866ee50448f80a13bcdf971318) @ `9e40d30e242925866ee50448f80a13bcdf971318` (kod ewaluacji `ewok/evaluate/`, analiza `analyses/scripts/inspect_results.Rmd`, wyniki w `analyses/data.zip`); generator zbioru: [`ewok-core/ewok`](https://github.com/ewok-core/ewok/tree/c4602f486da4ed765577b44485fa8977bf29b945) @ `c4602f486da4ed765577b44485fa8977bf29b945`; zbiór HF: [`ewok-core/ewok-core-1.0`](https://huggingface.co/datasets/ewok-core/ewok-core-1.0/tree/34d912a608066c92e2990a0328ffc3bd9a716042) @ `34d912a608066c92e2990a0328ffc3bd9a716042`, plik `data/test/ewok-core-1.0.parquet` |
| Dane: split w pracy | split: `test` (jedyny). Praca liczy 5 wersji zbioru (`vers=0…4`, te same szablony z innymi wypełnieniami: imionami, obiektami). Każda wersja ma 911 rekordów przed filtrami autorów <!-- liczba-spoza-wynikow: data.zip, outputs_20240429/dataset/ewok1.0/*__vers=*/testsuite-*.csv, policzone 2026-11-03 --> |
| Dane: n po filtrach (`ewok-core-1.0`) | 4374 rekordy (875 na wersję, w jednej 874), czyli 4357 różnych czwórek (C1, C2, T1, T2) <!-- liczba-spoza-wynikow: ewok-core-1.0.parquet @ 34d912a6 i data.zip, policzone 2026-11-03 --> |
| Dane: split w Space/repo | split: `test`; n: 4374, pełny zbiór, nie panel 200 (`benchmarks/ewok/ewok.py score`). Space nie liczy EWoK <!-- liczba-spoza-wynikow: ewok-core-1.0.parquet @ 34d912a6 --> |
| Dane: licencja | licencja autorów: CC BY 4.0 (`LICENSE.txt` w repo i zbiorze) plus TERMS_OF_USE (bez jawnego tekstu w sieci, zgłaszanie użycia w treningu); tag HF: `cc-by-4.0`, repo z bramką zgody; ukryte odpowiedzi w teście: nie (T1 zawsze pasuje do C1, T2 do C2) |
| Format zadania | para minimalna 2×2: dwa konteksty C1, C2 i dwa zdania docelowe T1, T2. T1 pasuje do C1, T2 do C2 |
| Prompt | brak promptu w trybie głównym (LOGPROBS). Kod autorów (`ewok/evaluate/model.py`, `Model._score`) skleja `f"{context} {target}"` (jedna spacja), liczy surprisal paczką [`surprisal`](https://github.com/benlipkin/surprisal/tree/366b074e3efb1e4d83ae8242013880c5e15851da) @ `366b074` z `use_bos_token=False` i sumuje go po tokenach od `len(tokenize(context))` do `len(tokenize(query))`. `tokenize` woła tokenizer z `add_special_tokens=True`, więc BOS jest wtedy, gdy tokenizer sam go dokleja (np. Bielik, EuroLLM, LFM2.5), a `surprisal` nic nie dodaje. Przed softmaxem logit tokenu pad (albo EOS, gdy tokenizer nie ma pad) to −inf. 0-shot. Domyślnie bf16 i batch 1 (`ewok/evaluate/args.py`). Tryby pomocnicze `choice` i `likert` mają szablony promptów w `ewok/evaluate/util.py`. Nie przenosimy ich |
| Ocena | trafność. Dla rekordu `s1 = [log P(T1\|C1) > log P(T1\|C2)]`, `s2 = [log P(T2\|C2) > log P(T2\|C1)]`, wynik rekordu = (s1 + s2) / 2. Remis liczy się jako 0,5 (`count_equal_as_half = TRUE` w `inspect_results.Rmd`). Bez normalizacji długości: po obu stronach porównania jest ten sam napis T |
| Metryka decyzyjna | trafność LOGPROBS (wynik rekordu wyżej) |
| Agregacja | średnia po rekordach (każdy rekord to dwa porównania o równej wadze) w każdej z 5 wersji, potem średnia z 5 wersji. Przed tym `inspect_results.Rmd` usuwa duplikaty, rekordy bez danych ludzi, szablony oflagowane po badaniu z ludźmi i 5 szablonów z wersji 0.9. Odwraca też T1 i T2 w szablonach oflagowanych jako odwrócone. Wynik tych filtrów to `ewok-core-1.0` z HF. Bez wag domen |
| Bazy | losowa: 0,5. Większościowa: nie dotyczy, bo nie ma opcji do wybrania. Model, który zawsze woli ten sam kontekst albo to samo zdanie, dostaje dokładnie 0,5 (s1 + s2 = 1) |
| SNR: źródło | tabela 20 modeli z pracy, `analyses/tables/ 20240429 _mean_accuracy_allmodels.tex` (bez wiersza `human`) |
| SNR: rozrzut | odchylenie std. średniej trafności 20 modeli: 0,063 <!-- liczba-spoza-wynikow: policzone z tabeli pracy, 20 modeli --> |
| SNR: SE | √(0,7·0,3/n). Dla n = 4374 rekordów wychodzi 0,0069. Rekordy jednego szablonu nie są niezależne (5 wersji to te same szablony), więc uczciwsze jest n = 843 szablony (`ewok.templates`, `README.md`): 0,0158 <!-- liczba-spoza-wynikow: wzór z METODOLOGIA.md dla p = 0,7 --> |
| SNR: iloraz | 9,2 po rekordach i 4,0 po szablonach <!-- liczba-spoza-wynikow: 0,063 / 0,0069 i 0,063 / 0,0158 --> |
| Wyniki referencyjne (odczyt 2026-11-03) | lista niżej, jedna pozycja na linię |
| Train policy | `eval_only` dla całego zbioru. TERMS_OF_USE wymaga też jawnego zgłoszenia każdego użycia EWoK w treningu |
| Decyzja treningowa | Słaby wynik w domenie mówi, że model nie wiąże opisu sytuacji z jej konsekwencją w tej domenie (np. przestrzeń, materiały, relacje społeczne). Wskazuje na braki w danych z prostymi opisami świata fizycznego i społecznego. Nie wolno trenować na szablonach ani rekordach EWoK ani pisać danych „w ich stylu”. Wynik bliski 0,5 przy słabym modelu nie odróżnia braku wiedzy od zbyt słabego modelu języka |
| Znane rozbieżności | lista niżej |

## Wyniki referencyjne

Tabela z repo autorów, `analyses/tables/ 20240429 _mean_accuracy_allmodels.tex` @ `9e40d30e` (średnia z 5 wersji, w
nawiasie zakres między wersjami), modele do pobrania z HF:

- `gpt2-xl` (dziś `openai-community/gpt2-xl`): 0,656 (0,646–0,663) <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->
- `microsoft/phi-1_5`: 0,728 (0,687–0,757) <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->
- `microsoft/phi-2`: 0,720 (0,698–0,773) <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->
- `google/gemma-2b`: 0,678 (0,658–0,706) <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->
- `mistralai/Mistral-7B-v0.1`: 0,777 (0,770–0,784) <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->
- `meta-llama/Meta-Llama-3-8B`: 0,746 (0,742–0,757) <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->
- ludzie (nie model): 0,954 <!-- liczba-spoza-wynikow: tabela w repo autorów @ 9e40d30e, mean_accuracy_allmodels.tex -->

Tabela A w pracy na arXiv (źródła TeX v1 i v2, w obu te same liczby) różni się od pliku w repo o 0,001–0,003. Dla <!-- liczba-spoza-wynikow: arXiv 2405.09605 v1 i v2, Tabela A, wobec mean_accuracy_allmodels.tex -->
modelu kontrolnego i ludzi: gpt2-xl 0,655 (0,645–0,662) zamiast 0,656, ludzie 0,951 zamiast 0,954. Na werdykt <!-- liczba-spoza-wynikow: arXiv 2405.09605 v1 i v2, Tabela A (tab:results-mean), odczyt 2026-11-03 -->
etapu B to nie wpływa (`REPRODUCTION.md`).

Na liście modeli kontrolnych z METODOLOGIA.md Pythia v0 i EuroLLM nie mają wyniku EWoK (plik wyników Pythii v0 nie
ma tego zadania, karta EuroLLM-1.7B też nie). Model kontrolny etapu B to więc `gpt2-xl` z tabeli pracy (punkt 3
listy). Nie jest najmniejszym modelem w tabeli (`phi-1_5` jest mniejszy), ale ma wynik ponad 2 SE nad bazą 0,5. Autorzy podają też surowe wyniki
per rekord (`analyses/data.zip`, `eval=logprobs/model=gpt2_xl`). Etap B porównuje z nimi każdy rekord.

## Znane rozbieżności

- **Remis.** Kod autorów liczy remis log P jako 0,5. Nasz `benchmarks/ewok/ewok.py` liczy go jako pudło. Remis
  zdarza się, gdy kontekst nie zmienia rozkładu po sobie, czyli praktycznie tylko przy niskiej precyzji.
- **BOS i precyzja.** Kod autorów daje BOS tylko wtedy, gdy dokleja go tokenizer (`add_special_tokens=True`), i
  liczy w bf16. Nasz kod domyślnie robi to samo z tokenami (reguła `authors`), ale liczy w float32. Pierwsze przebiegi
  tego katalogu nie dawały BOS nigdy (`--rule plain`), a `benchmarks/ewok-pl` daje BOS każdemu modelowi
  (`--rule bos`). Wpływ na decyzje mierzy `REPRODUCTION.md`.
- **Granica kontekstu.** Kod autorów tnie zapytanie na tokenach `tokenize(context)`. Gdy tokenizer skleja spację z
  następnym słowem inaczej w zapytaniu niż w samym kontekście, granica może się przesunąć o token. Nasz kod koduje
  parę jak lm-eval: całość raz, a długość kontekstu z osobnego kodowania.
- **Filtry autorów.** Surowe wyniki per wersja w `data.zip` obejmują 911 rekordów na wersję. Tabela pracy liczy
  tylko rekordy po filtrach (`ewok-core-1.0`), więc średnia z surowych wyników (0,6515 dla gpt2-xl) jest niższa niż <!-- liczba-spoza-wynikow: data.zip, wszystkie 911 rekordów na wersję, policzone 2026-11-03 -->
  w tabeli.
- **Duplikaty.** `ewok-core-1.0` ma 17 czwórek, które powtarzają się między wersjami. Średnia po 4374 wierszach
  liczy je dwa razy, jak tabela pracy. <!-- liczba-spoza-wynikow: ewok-core-1.0.parquet @ 34d912a6 -->
- **Inne implementacje.** lm-eval przy commicie `6d2abda4` nie ma zadania EWoK (nie znaleźliśmy go w
  `lm_eval/tasks/`, 147 katalogów). Innych implementacji nie porównywaliśmy.
- **Kontaminacja.** Rekordy są w zipach z hasłem i w repo HF z bramką zgody, z kanarkami (UUID w README autorów).
  Korpusu treningowego Slayera nie skanowaliśmy pod kątem kanarka.
