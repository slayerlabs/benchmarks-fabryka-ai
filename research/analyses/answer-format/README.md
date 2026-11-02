# Format odpowiedzi: Slayer 1B nic nie wie, czy tylko nie radzi sobie z formatem liter?

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md): etap A to karta oryginału (`ORIGINAL.md`), etap B to
> odtworzenie opublikowanego wyniku kodem autorów (`REPRODUCTION.md`), etap D to wersja polska tą samą metodą.
> Pojęcia (Space, T01–T50, acc_norm, cloze, PMI, BPB, SE, werdykt): [słowniczek](../../METODOLOGIA.md#słowniczek).

To analiza, nie benchmark. Istniejące testy wyboru (ARC-Easy, ARC-Challenge, MedMCQA, Social IQa, MMLU, polski
Belebele, polski MultiBLiMP) liczymy jednym scorerem w dwóch formatach: litery (A/B/C/D) i cloze (treść
odpowiedzi), czterema regułami wyboru (acc, acc_norm, reguła BPB, PMI) plus BPB poprawnej odpowiedzi.
Rozstrzyga sześć testów z progami ustalonymi przed wynikami (T0-T5).

- Karta zadań, testów i oceny: [ORIGINAL.md](ORIGINAL.md)
- Sprawdzenie scorera z opublikowanymi liczbami (etap B): [REPRODUCTION.md](REPRODUCTION.md)
- Dokładne komendy, rewizje i to, czego nie zapisano: [RECIPE.md](RECIPE.md)
- Kod: [`analiza_formatu.py`](analiza_formatu.py) (testy), [`../../common/hipoteza_formatu.py`](../../common/hipoteza_formatu.py) (scorer)
- Pełne liczby: [`results/raport_formatu.json`](results/raport_formatu.json); każde porównanie z SE i werdyktem:
  [`../../results/LICZBY.md`](../../results/LICZBY.md)

Modele: Slayer 1.06 (16 plików zadań), Slayer 1.03 i Slayer 1.00 (tylko ARC-C), Pythia-1B (13 plików zadań),
`Qwen2.5-0.5B` (tylko ARC cloze, do T0). Werdykty: |z| >= 3 pewne, od 2 do 3 prawdopodobne, poniżej 2 szum.
Slayer vs Pythia liczony z niezależnym SE (ostrożnie); porównania wersji ze sparowanym SE tam, gdzie są dane per
pytanie.

## Krótka odpowiedź

Slayer 1.06 wypada losowo w testach z literami, bo prawie zawsze wybiera tę samą literę.
Najczęstsza predykcja to od 83,0% do 94,0% jego odpowiedzi w pięciu angielskich testach z literami.
W polskim Belebele to 62,6% (Pythia-1B: 43,1%).
Pythia-1B robi to samo w angielskich testach z literami (od 84,4% do 96,0%).
Trafność z liter obu modeli różni się tylko o szum we wszystkich sześciu testach z literami (tabela niżej). Losowe
wyniki w formacie liter to więc cecha modeli tej skali, a nie dowód, że Slayer nic nie wie.
Liczony po treści odpowiedzi Slayer uczy się między wersjami: ARC-C acc_norm, Slayer 1.00 -> Slayer 1.06:
0,2176 -> 0,2577, +4,0 pkt, sparowane SE 1,12 pkt, z = 3,57, pewne; trafność z liter stoi na 0,2304 w obu (szum).

Eksperyment z wygaszaniem LR z tego samego raportu leży w [`../../slayer-1b/wygaszanie/`](../../slayer-1b/wygaszanie/README.md).

## Testy T0-T5 (Slayer 1.06, chyba że zaznaczono inaczej)

| test | wynik | reguła spełniona? |
|---|---|---|
| T0 scorer vs opublikowane | Pythia-1B ARC-E/ARC-C acc i acc_norm w granicach dziesiątej części punktu od opublikowanych wartości; `Qwen2.5-0.5B` ARC-C 25-shot acc_norm 0,3609 wobec opublikowanego 0,356 | tak, scorer OK |
| T1 jedna litera | ARC-C: „A” w 92,0% z 1172 wyborów, „A” poprawne w 22,7%; MedMCQA: „A” w 93,3% z 4183, poprawne w 32,2%; p dwumianowe zapisane jako 0 w obu | tak (oba) |
| T2 pozycja | po przesunięciu treści odpowiedzi 95,1% wyborów w ARC-C zostaje na tej samej literze (SE 0,6 pkt); 1,7% idzie za treścią | tak |
| T3 ukryta wiedza | ARC-C cloze: tylko PMI 0,2978 przekracza bazę losową + 2 SE (próg 0,2769); MedMCQA cloze: przekraczają acc_norm 0,2711 i reguła BPB 0,2706 (próg 0,2637) | tak (słabo: kilka punktów ponad bazą) |
| T4 pułapka częstej odpowiedzi | ARC-C cloze: w 80,1% z 900 błędnych wyborów acc wybrana odpowiedź ma wyższe prawdopodobieństwo bezwarunkowe niż poprawna; PMI 0,2978 wobec acc 0,2321, 245 pytań z błędnych na dobre, 168 z dobrych na błędne, McNemar p 0,00018 | tak |
| T5 treść wyuczona, trafność stoi | BPB poprawnej odpowiedzi w ARC-C spada z 1,5757 do 1,4621, sparowana różnica −0,1136, SE 0,0072; ale acc_norm też rośnie (z = 3,57) | nie: trafność nie stoi |

T5 nie przechodzi z dobrego powodu. Reguła zapisana przed wynikami zakładała, że BPB poprawnej odpowiedzi spada, a
trafność liczona po treści się nie zmienia. Tymczasem od Slayer 1.00 do Slayer 1.06 poprawiają się obie: spada BPB
poprawnej odpowiedzi i rośnie trafność liczona po treści. Bez zmian zostaje tylko wynik z liter.

Dwa dodatkowe warianty liter na ARC-C (opisowo, bez testu): z 5 przykładami w prompcie najczęstsza litera spada do
40,7% wyborów, a trafność zostaje na 0,2466 (SE 0,0126, baza losowa 0,2502); bez spacji przed literą trafność to
0,2210 (SE 0,0121), a jedna litera dalej bierze 91,5%.
Prior litery skalibrowany przez odjęcie średniego logprob każdej litery daje 0,2389 na ARC-C (SE 0,0125).
Ta sama kalibracja daje 0,2513 na MedMCQA (SE 0,0067).

## Slayer 1.06 vs Pythia-1B

Różnica = Slayer minus Pythia; SE niezależne. Litery: acc (acc_norm i reguła BPB przy literach są identyczne).
Cloze: acc_norm, plus PMI tam, gdzie werdykt nie jest szumem.

| zadanie | format | n | Slayer 1.06 | Pythia-1B | różnica | SE | z | werdykt |
|---|---|---:|---:|---:|---:|---:|---:|---|
| ARC-C | litery | 1172 | 0,2304 | 0,2287 | 0,17 pkt | 1,74 pkt | z = 0,10 | szum |
| ARC-E | litery | 2376 | 0,2534 | 0,2542 | −0,08 pkt | 1,26 pkt | z = −0,07 | szum |
| MedMCQA | litery | 4183 | 0,3160 | 0,3158 | 0,02 pkt | 1,02 pkt | z = 0,02 | szum |
| SIQA | litery | 1954 | 0,3275 | 0,3311 | −0,36 pkt | 1,50 pkt | z = −0,24 | szum |
| MMLU | litery | 14042 | 0,2307 | 0,2314 | −0,06 pkt | 0,50 pkt | z = −0,13 | szum |
| Belebele | litery | 900 | 0,2522 | 0,2422 | 1,00 pkt | 2,03 pkt | z = 0,49 | szum |
| ARC-C | cloze acc_norm | 1172 | 0,2577 | 0,2705 | −1,28 pkt | 1,82 pkt | z = −0,70 | szum |
| ARC-E | cloze acc_norm | 2376 | 0,4588 | 0,4899 | −3,11 pkt | 1,45 pkt | z = −2,15 | prawdopodobne |
| ARC-E | cloze acc | 2376 | 0,5261 | 0,5699 | −4,38 pkt | 1,44 pkt | z = −3,03 | pewne |
| MedMCQA | cloze acc_norm | 4183 | 0,2711 | 0,2838 | −1,27 pkt | 0,98 pkt | z = −1,29 | szum |
| MedMCQA | cloze PMI | 4183 | 0,2577 | 0,2972 | −3,94 pkt | 0,98 pkt | z = −4,03 | pewne |
| SIQA | cloze acc_norm | 1954 | 0,4237 | 0,4396 | −1,59 pkt | 1,58 pkt | z = −1,00 | szum |
| SIQA | cloze PMI | 1954 | 0,3746 | 0,4094 | −3,48 pkt | 1,56 pkt | z = −2,23 | prawdopodobne |
| MMLU | cloze acc_norm | 14042 | 0,2813 | 0,2997 | −1,84 pkt | 0,54 pkt | z = −3,39 | pewne |
| Belebele | cloze acc_norm | 900 | 0,3189 | 0,2767 | 4,22 pkt | 2,15 pkt | z = 1,96 | szum |
| MultiBLiMP | para, acc | 3272 | 0,9859 | 0,7735 | 21,24 pkt | 0,76 pkt | z = 27,94 | pewne |

Bazy losowe: ARC-C 0,2502; 0,25 dla MedMCQA, MMLU i Belebele; SIQA 0,3333; MultiBLiMP 0,5.
Bazy większościowe są w `zestawienie` raportu.

Jak czytać: na literach obu modeli nie da się rozróżnić (szum we wszystkich sześciu zadaniach). Po treści
Pythia-1B wypada wyżej w ARC-E cloze (acc z = −3,03, pewne) i w MMLU cloze (z = −3,39, pewne).
Slayer wypada wyżej w polskiej gramatyce (MultiBLiMP, z = 27,94, pewne), co zgadza się z tym, że Pythię trenowano
na tekście angielskim (the Pile); mieszanki danych Slayera tu nie badamy.

## Wersje Slayera (ARC-C, te same 1172 pytania)

| porównanie | format / metryka | różnica | SE | z | werdykt |
|---|---|---:|---:|---:|---|
| Slayer 1.00 do Slayer 1.06 | litery acc | 0,00 pkt | 1,74 pkt | z = 0,00 | szum |
| Slayer 1.00 do Slayer 1.06 | cloze acc_norm (sparowane) | 4,01 pkt | 1,12 pkt | z = 3,57 | pewne |
| Slayer 1.00 do Slayer 1.06 | cloze PMI | 6,23 pkt | 1,82 pkt | z = 3,42 | pewne |
| Slayer 1.00 do Slayer 1.06 | BPB poprawnej odpowiedzi (sparowane), bity na bajt | −0,1136 | 0,0072 | z = −15,78 | pewne |
| Slayer 1.00 do Slayer 1.03 | cloze acc_norm | 3,84 pkt | 1,75 pkt | z = 2,19 | prawdopodobne |
| Slayer 1.03 do Slayer 1.06 | cloze acc_norm | 0,17 pkt | 1,80 pkt | z = 0,09 | szum |

Wiersz BPB podaje różnicę i SE w bitach na bajt (z 1,5757 do 1,4621), nie w punktach. Udział najczęstszej litery wynosi
98,0% (Slayer 1.00), 96,6% (Slayer 1.03), 92,0% (Slayer 1.06); dla tych udziałów nie zapisano SE.

## Wnioski

1. Losowe wyniki Slayera 1.06 w formacie liter biorą się ze stałej preferencji jednej litery (T1), która idzie za
   pozycją, a nie treścią (T2). Pythia-1B zachowuje się tak samo, a jej trafność z liter różni się od Slayera
   tylko o szum. Trafność z liter nie nadaje się do porządkowania modeli tej wielkości.
2. Miary liczone po treści niosą sygnał: PMI na ARC-C i acc_norm na MedMCQA przekraczają bazę losową + 2 SE (T3),
   PMI naprawia część pułapki częstej odpowiedzi (T4), a acc_norm, PMI i BPB poprawnej odpowiedzi rosną od
   Slayer 1.00 do Slayer 1.06 z werdyktem pewnym.
3. Wobec Pythii-1B w angielskich zadaniach wiedzy liczonych po treści Slayer 1.06 wypada niżej z werdyktem pewnym
   w ARC-E cloze acc, MMLU cloze i MedMCQA PMI.
   Wypada niżej z werdyktem prawdopodobnym w SIQA PMI, a w pozostałych miarach cloze różnica to szum.
   W polskiej gramatyce (MultiBLiMP) wypada wyżej z werdyktem pewnym.
4. Dla Slayera raportujemy liczby z cloze, BPB i PMI; wyniki z liter pokazujemy razem z udziałem najczęstszej
   predykcji.

## Co dodaje metodologia

Lista tego, czego ta praca jeszcze nie spełnia według [`METODOLOGIA.md`](../../METODOLOGIA.md); każdy punkt to osobne
zadanie do wzięcia.

- [ ] Etap B oryginalnym kodem: żadnego zadania nie policzono lm-eval ani kodem autorów benchmarku; T0 sprawdza
      nasz scorer tylko na ARC cloze.
- [ ] Model kontrolny: `EleutherAI/pythia-1b-v0` @ `step143000` nie był liczony; T0 użył `EleutherAI/pythia-1b`
      (float32) wobec referencji w bfloat16.
- [ ] Test zgodności: brak `tests/test_<name>_zgodnosc.py` z 10-20 decyzjami lm-eval per pytanie dla scorera
      (potrzebny dla każdego zadania, w którym twierdzimy, że prompt jest z lm-eval: ARC, MedMCQA litery, SIQA
      cloze, Belebele litery, MMLU litery, MultiBLiMP).
- [ ] Pięć modeli odniesienia (`Qwen3.5-0.8B-Base`, `LFM2.5-1.2B-Base`, `Bielik-1.5B-v3`, `LFM3-1.7B-Base`,
      `EuroLLM-1.7B`) nie policzone; przy jedynym punkcie odniesienia Pythii-1B teza „cecha skali ~1B” opiera się
      na jednym modelu i literaturze (OLMES).
- [ ] Brakujące pola przepisu: commit kodu przebiegów, sprzęt, data przebiegu, rewizje Slayer 1.00 / Slayer 1.03 i
      modelu Qwen oraz rewizje `social_i_qa`, `belebele`, `mmlu`; surowych plików per pytanie nie ma w repo.
- [ ] Karty oryginałów: osobnych kart etapu A dla każdego benchmarku (z protokołem ewaluacji autorów i wynikami
      referencyjnymi) nie ma; `ORIGINAL.md` streszcza je w jednej tabeli.
- [ ] PubMedQA (Space T44) jest zdefiniowany w `common/zadania.py`, ale nie wchodzi do tej analizy.
