# Analiza formatu odpowiedzi: karta oryginału (etap A)

Ten katalog to **analiza**, nie benchmark. Zadaje jedno pytanie: gdy Slayer 1B wypada losowo w testach
wyboru, w których odpowiada się literą (A/B/C/D), to dlatego, że model nie zna odpowiedzi, czy dlatego, że nie
radzi sobie z formatem litery? Analiza liczy istniejące benchmarki na nowo w kilku formatach jednym wspólnym
scorerem (`common/hipoteza_formatu.py`) i przeprowadza sześć testów (T0-T5). Progi testów ustalono przed
wynikami (docstring `analiza_formatu.py`).

Nie ma więc jednego „oryginału”. Ta karta opisuje (1) hipotezy i testy, (2) formaty oceny i ich źródła,
(3) każde zadanie: pracę o benchmarku, kartę zbioru i kod ewaluacji, którego prompt naśladujemy.

## Co mierzy

Czy losowa trafność przy odpowiedziach literą ukrywa wiedzę, która widać, gdy model ocenia samą treść
odpowiedzi (cloze, cloze normalizowane długością, bity na bajt poprawnej odpowiedzi, PMI).

## Hipotezy i testy (progi ustalone przed wynikami)

| test | pytanie | reguła (z `analiza_formatu.py`) | dane |
|---|---|---|---|
| T0 | Czy nasz scorer odtwarza opublikowane liczby? | `abs(nasza - opublikowana) <= 2 pkt` | Pythia-1B 0-shot ARC-E i ARC-C (acc, acc_norm); `Qwen2.5-0.5B` ARC-C 25-shot acc_norm |
| T1 | Czy model woli jedną literę? | jedna litera `> 50%` wyborów i ponad jej udział wśród poprawnych odpowiedzi w jednostronnym teście dwumianowym przy `p < 0.05`; obok chi-kwadrat rozkładu liter | Slayer 1.06: ARC-C litery, MedMCQA litery |
| T2 | Czy wybór idzie za pozycją, nie treścią? | po cyklicznym przesunięciu treści odpowiedzi (A->B->C->D->A) `>= 70%` wyborów zostaje na tej samej literze | Slayer 1.06: ARC-C litery vs ARC-C litery po przesunięciu |
| T3 | Czy format ukrywa wiedzę? | acc_norm, reguła BPB albo PMI powyżej bazy losowej `+ 2 SE` (którakolwiek) | Slayer 1.06: ARC-C cloze, MedMCQA cloze |
| T4 | Czy błąd to pułapka „częstej odpowiedzi”? | `> 50%` błędnych wyborów acc ma wyższe prawdopodobieństwo bezwarunkowe niż poprawna ORAZ acc PMI > acc (McNemar `p < 0.05`). Kryterium dopisane przed wynikami; pierwotne zlecenie go nie podało | Slayer 1.06: ARC-C cloze |
| T5 | Czy model uczy się treści, gdy trafność stoi? | średnie BPB poprawnej odpowiedzi spada od Slayer 1.00 do Slayer 1.06 o więcej niż 2 sparowane SE ORAZ sparowana zmiana acc_norm jest mniejsza niż 2 SE. Kryterium dopisane przed wynikami | ARC-C cloze, Slayer 1.00 / Slayer 1.03 / Slayer 1.06 |

Tabela opisowa (`zestawienie` w `results/raport_formatu.json`) dodaje dla każdego modelu i zadania: n, bazę
losową i większościową, udział najczęstszej predykcji, rozkład liter, cztery trafności z SE, średnie BPB
poprawnej odpowiedzi, a dla MMLU i MultiBLiMP trafność per grupa i średnią makro.

## Źródła

- Konwencje oceny: lm-evaluation-harness `lm-eval 0.4.9.1`
  ([tag v0.4.9.1](https://github.com/EleutherAI/lm-evaluation-harness/tree/v0.4.9.1)): kodowanie kontekstu
  i kontynuacji, acc i acc_norm oraz prompty zadań wymienionych niżej.
- Format cloze vs format liter („MCF”) w małych modelach: OLMES, Gu i in. 2024, [arXiv](https://arxiv.org/abs/2406.08446). <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie -->
- PMI (logliki warunkowy minus bezwarunkowy, „surface form competition”): Holtzman i in. 2021,
  [arXiv](https://arxiv.org/abs/2104.08315). <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie -->
- Liczby referencyjne do T0: Pythia, Biderman i in. 2023, [arXiv](https://arxiv.org/abs/2304.01373) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie -->
  i jej opublikowany plik ewaluacji
  ([`1b-bf16_step143000.json`](https://github.com/EleutherAI/pythia/blob/58f33c6e3b521435f5af695eeb3a327a35ac4e58/evals/pythia-v1/pythia-1b-bf16/zero-shot/1b-bf16_step143000.json));
  raport techniczny Qwen2.5, [arXiv](https://arxiv.org/abs/2412.15115), tabela modeli bazowych, ARC-C 25-shot (numer <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie -->
  tabeli jak w `analiza_formatu.py`: Tab. 5).

## Zadania

16 plików wyników dla Slayer 1.06 (13 dla Pythii-1B, po 2 dla Slayer 1.00 i Slayer 1.03, 3 dla `Qwen2.5-0.5B`).
„litery” = opcje wypisane jako A./B./..., kontynuacja `" A"`; „cloze” = kontynuacją jest treść odpowiedzi.

| plik zadania | benchmark | format | prompt (dokładny, z `common/hipoteza_formatu.py`) | prompt naśladuje |
|---|---|---|---|---|
| `arc_c_cloze` | ARC-Challenge test | cloze | `"Question: {q}\nAnswer:"` + `" {option}"` | lm-eval `arc_challenge` (Space T02) |
| `arc_c_mc` | ARC-Challenge test | litery | `"Question: {q}\nA. {a}\nB. {b}\n...\nAnswer:"` + `" A"` | nasz wariant z literami (lm-eval nie ma domyślnego); ten sam kształt co MCF w OLMES |
| `arc_c_mc_przes` | ARC-Challenge test | litery | jak `arc_c_mc`, treści odpowiedzi przesunięte o jedną pozycję (A->B, ..., ostatnia->A), poprawna idzie ze swoją treścią | nasz (T2) |
| `arc_c_mc_bezspacji` | ARC-Challenge test | litery | jak `arc_c_mc`, kontynuacja `"A"` bez spacji | nasz (kontrola tokenizacji) |
| `arc_c_mc_5shot` | ARC-Challenge test | litery | 5 przykładów z train w formacie `arc_c_mc`, każdy z `" {litera poprawnej}\n\n"`; losowanie `random.Random("1234|5|{id}")` | nasz |
| `arc_c_cloze_25shot` | ARC-Challenge test | cloze | 25 przykładów z train `"Question: {q}\nAnswer: {treść poprawnej}\n\n"`, losowanie `random.Random("1234|{id}")`, potem prompt cloze | lm-eval `arc_challenge` z 25 przykładami, jak w raporcie Qwen2.5 (tylko `Qwen2.5-0.5B` w T0) |
| `arc_e_cloze` | ARC-Easy test | cloze | jak `arc_c_cloze` | lm-eval `arc_easy` |
| `arc_e_mc` | ARC-Easy test | litery | jak `arc_c_mc` | nasz |
| `med_mc` | MedMCQA validation | litery | `"Question: {q}\nChoices:\nA. {a}\nB. {b}\nC. {c}\nD. {d}\nAnswer:"` + `" A"` | lm-eval `medmcqa` (`utils_medmcqa.py`, Space T45) |
| `med_cloze` | MedMCQA validation | cloze | `"Question: {q}\nAnswer:"` + `" {option}"` | nasz (lm-eval nie ma MedMCQA w cloze) |
| `siqa_cloze` | Social IQa validation | cloze | `"Q: {context} {question}\nA:"` + `" {answer}"` | lm-eval `social_iqa` (Space T46) |
| `siqa_mc` | Social IQa validation | litery | `"Question: {context} {question}\nA. ...\nB. ...\nC. ...\nAnswer:"` + `" A"` | nasz |
| `belebele_mc` | Belebele `pol_Latn` test | litery | `"P: {passage}\nQ: {question}\nA: {a}\nB: {b}\nC: {c}\nD: {d}\nAnswer:"` + `" A"` | lm-eval `belebele_pol_Latn` |
| `belebele_cloze` | Belebele `pol_Latn` test | cloze | `"P: {passage}\nQ: {question}\nAnswer:"` + `" {option}"` | nasz |
| `mmlu_mc` | MMLU test, 57 przedmiotów | litery | `"The following are multiple choice questions (with answers) about {subject}.\n\n{q}\nA. ...\nD. ...\nAnswer:"` + `" A"` | lm-eval `mmlu` (domyślny) |
| `mmlu_cloze` | MMLU test, 57 przedmiotów | cloze | `"Question: {q}\nAnswer:"` + `" {option}"` (bez linii z przedmiotem) | nasz |
| `multiblimp` | MultiBLiMP polski | para zdań | pusty kontekst, kontynuacja `" {zdanie}"`, suma logprob; wygrywa zdanie poprawne gramatycznie | ocena par jak lm-eval `blimp` (Space T04) |

Wszystkie zadania są 0-shot poza `arc_c_mc_5shot` i `arc_c_cloze_25shot`.

### Źródła benchmarków

| benchmark | praca | kod autorów / karta zbioru | split, n | licencja |
|---|---|---|---|---|
| ARC (Easy, Challenge) | Clark i in. 2018, [arXiv](https://arxiv.org/abs/1803.05457) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> | [allenai/ARC-Solvers](https://github.com/allenai/ARC-Solvers); [`allenai/ai2_arc` @ `210d026f`](https://huggingface.co/datasets/allenai/ai2_arc/tree/210d026faf9955653af8916fad021475a3f00453) | test; Challenge 1172, Easy 2376 | CC BY-SA 4.0 (karta HF) |
| MedMCQA | Pal i in. 2022, [arXiv](https://arxiv.org/abs/2203.14371) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> | [MedMCQA/MedMCQA](https://github.com/MedMCQA/MedMCQA); [`openlifescienceai/medmcqa` @ `91c6572c`](https://huggingface.co/datasets/openlifescienceai/medmcqa/tree/91c6572c454088bf71b679ad90aa8dffcd0d5868) | validation (odpowiedzi testu są ukryte); 4183 | Apache-2.0 (karta HF) |
| Social IQa | Sap i in. 2019, [arXiv](https://arxiv.org/abs/1904.09728) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> | [`allenai/social_i_qa`](https://huggingface.co/datasets/allenai/social_i_qa), gałąź `refs/convert/parquet` (bez przypiętego sha) | validation (odpowiedzi testu są ukryte); 1954 | nieustalone (karta HF nie ma znacznika licencji) |
| Belebele | Bandarkar i in. 2023, [arXiv](https://arxiv.org/abs/2308.16884) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> | [facebookresearch/belebele](https://github.com/facebookresearch/belebele); [`facebook/belebele`](https://huggingface.co/datasets/facebook/belebele), konfiguracja `pol_Latn`, bez przypiętej rewizji | test; 900 | CC BY-SA 4.0 (karta HF) |
| MMLU | Hendrycks i in. 2020, [arXiv](https://arxiv.org/abs/2009.03300) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> | [hendrycks/test](https://github.com/hendrycks/test); [`cais/mmlu`](https://huggingface.co/datasets/cais/mmlu), przedmioty z lokalnego cache HF, bez przypiętej rewizji | test; 14042 | MIT (karta HF) |
| MultiBLiMP | Jumelet i in. 2025, [arXiv](https://arxiv.org/abs/2504.02768) <!-- liczba-spoza-wynikow: identyfikator arXiv w adresie --> | [jumelet/multiblimp](https://github.com/jumelet/multiblimp); [`jumelet/multiblimp` @ `de923efa`](https://huggingface.co/datasets/jumelet/multiblimp/tree/de923efa8d2483d6b13364ee68e65308e990a991), `pol/data.tsv` | plik polski; 3272 pary | CC BY 4.0 (karta HF) |

PubMedQA (Space T44) jest zdefiniowany w `common/zadania.py`, ale **nie** należy do tej analizy: w
`results/raport_formatu.json` nie ma pliku PubMedQA.

## Dane

Pełne splity jak wyżej, bez losowania próbki (n w raporcie są równe rozmiarom splitów powyżej). ARC ma kilka
pytań z 3 albo 5 opcjami; baza losowa to średnia `1/k` po pytaniach. W `multiblimp` zdanie poprawne jest
zawsze opcją 0, więc zapisana „baza większościowa” równa 1 wynika z układu pliku, a nie z danych.

## Format zadania i ocena

Jeden scorer logliku dla każdego modelu (`common/hipoteza_formatu.py`). Podział na kontekst i kontynuację jak w
`lm-eval 0.4.9.1` `_encode_pair` (końcowe spacje kontekstu przechodzą do kontynuacji). Modele z Hugging Face
(Pythia, Qwen) nie dostają BOS, jak w lm-eval HFLM; pusty kontekst to jeden token prefiksu. Slayer zawsze dostaje
jeden BOS `<|endoftext|>`, jak w protokole Space. Cztery reguły wyboru na tych samych loglikach:

| reguła | definicja | uwaga |
|---|---|---|
| acc | opcja z największą sumą logprob | główna reguła Space dla zadań z literami |
| acc_norm | największy logprob na znak treści opcji | konwencja lm-eval; przy literach każda opcja ma 1 znak, więc acc_norm = acc |
| reguła BPB (`bpb`) | największy logprob na bajt UTF-8 kontynuacji | przy literach to samo co acc |
| PMI (`pmi`) | największy logliki warunkowy minus bezwarunkowy (bezwarunkowy = ta sama kontynuacja po pustym kontekście) | liczone tylko dla `arc_c_cloze`, `med_cloze`, `siqa_cloze`, `belebele_cloze` |

Do tego miara bez progu decyzyjnego: **BPB poprawnej odpowiedzi**, `-loglik / (ln 2 * bajty)` poprawnej
kontynuacji, uśredniona po pytaniach. Przy remisie wygrywa opcja o najniższym indeksie.

## Agregacja

Średnia po pytaniach (mikro). SE proporcji: `sqrt(p(1-p)/n)`. MMLU i MultiBLiMP podają też trafność per grupa i
nieważoną średnią makro po grupach. Porównania wersji na tych samych pytaniach używają sparowanego SE (T5);
porównania modeli używają niezależnego SE (`results/LICZBY.json`).

## Wyniki referencyjne

| model | zadanie | metryka | opublikowane | gdzie |
|---|---|---|---|---|
| Pythia-1B | ARC-Easy 0-shot | acc / acc_norm | 0,5694 / 0,4903 | plik ewaluacji Pythii (link wyżej); model w pliku: `EleutherAI/pythia-v1.1-1b-bf16` @ `step143000`, stary harness `hf-causal`, wersja zadania 0 |
| Pythia-1B | ARC-Challenge 0-shot | acc / acc_norm | 0,2440 / 0,2713 | ten sam plik |
| `Qwen2.5-0.5B` | ARC-Challenge 25-shot | acc_norm | 0,356 | raport techniczny Qwen2.5; raport nie publikuje kodu ewaluacji |

## Znane rozbieżności

- Formaty z literami dla ARC, Social IQa i cloze dla MMLU, MedMCQA i Belebele to nasze warianty; żadna praca nie
  podaje dla nich liczby referencyjnej.
- Referencja Pythii była liczona na wagach bfloat16 starszym harnessem; my liczymy `EleutherAI/pythia-1b`
  w float32 naszym scorerem (zob. `REPRODUCTION.md`).
- Przykłady 25-shot dla Qwena losujemy własnym seedem; jakich przykładów użyli autorzy Qwena, nie ustalono.
- lm-eval `acc_norm` dzieli przez długość napisu opcji; my dzielimy przez liczbę znaków treści opcji bez
  początkowej spacji. Czy to kiedykolwiek zmienia decyzję, nie sprawdzono.
- Kontaminacja tych zbiorów testowych w danych treningowych Slayera: nie sprawdzona (brak korpusu treningowego).
