# Slayer 1B — wyniki dla Arka i zadania dla chętnych (30.10.2026)

## Część 1. Wiadomość do Arka

Arek, sprawdziliśmy, skąd Slayer 1.06 siedzi na poziomie losowym na większości testów w Space.

| # | Co sprawdziliśmy | Wynik | Pewność | Co to znaczy |
|---|---|---|---|---|
| 1 | Którą literę wybiera Slayer w pytaniach A/B/C/D | „A” w 92% (ARC-C), 93% (MedMCQA), 83% (MMLU); poprawne „A” to 22,7% | n=1172 (ARC-C) | Model nie łączy treści z literą |
| 2 | Czy po przesunięciu odpowiedzi wybór idzie za treścią | 95% wyborów zostaje na tej samej literze | jw. | Potwierdza punkt 1 |
| 3 | Pythia-1B na tych samych testach | Jedna litera w 84–96%, MMLU z literami 0,231 (Slayer też 0,231) | ten sam pomiar | Cecha skali ~1B, nie Twojego modelu |
| 4 | Literatura (OLMES, arXiv 2406.08446) | Modele 1B: ARC-C z literami 24–26, po treści 31–39 | publikacja | To samo u Pythii, OLMo, TinyLlamy |
| 5 | ARC-C liczone po treści (PMI) | 0,298 przy bazie 0,25 | SE 0,013 (autorzy ARC podają ±2,5 pkt na 95%, zgodne) | Wiedza jest, litery jej nie pokazują. ARC-C to z definicji pytania, których nie rozwiązały proste statystyki słów (arXiv 1803.05457), więc dla 1B lepszym sygnałem postępu jest ARC-E |
| 6 | Postęp 1.00 → 1.06 po treści | acc_norm 0,218 → 0,258 (+0,040); BPB poprawnej odp. −0,114 | SE 0,011 / 0,007 | Trening działa, Space tego nie widzi |
| 7 | Polski vs Pythia-1B | Belebele (po treści, acc) 0,330 vs 0,297; MultiBLiMP-PL 0,986 vs 0,774 | Belebele 1,5 SE, MultiBLiMP 28 SE | MultiBLiMP pewny, ale oczekiwany (Pythia uczona na angielskim); Belebele w granicach szumu |
| 8 | Angielski vs Pythia-1B | ARC-E −4,4 pkt, MMLU −2,2 pkt, SIQA −0,9 pkt (po treści, acc) | 3,0 / 4,2 / 0,6 SE | ARC-E i MMLU prawdopodobna luka; SIQA bez różnicy |
| 9 | WikiText-2 byte_ppl | Nasz 1,893, Space 1,846 (+2,5%) | — | Do wyjaśnienia (zadanie A5) |
| 10 | Wygaszanie LR (150 kroków z ckpt_13848, 157 mln tokenów) | Loss na odłożonych danych: wygaszanie 2,2807, stały LR 2,3276 (Δ −0,047 nat), spadek we wszystkich częściach danych (web, core, legal, en); trafność ARC-C, MedMCQA, SIQA, MultiBLiMP bez zmian | SE różnicy 0,0006; szum między checkpointami 0,0011 | Wygaszenie obniża perplexity, testów nie podnosi; warto zrobić przed wydaniem |
| 11 | Testy danych na Slayerze (EN 10% vs 25%, lepszy polski web) | Plan i progi gotowe, nie uruchomione | — | Czekamy na Twoje zdanie, czy warto |

Krótko:

**1. To głównie format pytań, nie brak wiedzy.** W pytaniach z literami (A/B/C/D) Slayer wybiera „A” w 92% odpowiedzi na ARC-C (poprawne „A” to 22,7%, n=1172) i w 93% na MedMCQA (MMLU: 83%). Po przesunięciu treści odpowiedzi 95% wyborów zostaje na tej samej literze. Model nie łączy treści z literą.

**2. Pythia-1B robi dokładnie to samo** (jedna litera w 84–96% odpowiedzi, MMLU z literami 0,231 u obu modeli). To cecha skali ~1B, nie Twojego modelu ani danych. Potwierdza to publikacja Ai2 OLMES (arXiv 2406.08446): Pythia-1B, OLMo-1B i TinyLlama-1.1B mają ARC-C z literami 24–26, a liczone po treści 31–39.

**3. Liczone po treści, Slayer się uczy.** ARC-C (PMI) 0,298 przy bazie 0,25 (SE 0,013). Między 1.00 a 1.06: acc_norm 0,218 → 0,258 (+0,040, SE 0,011), BPB poprawnej odpowiedzi −0,114 (SE 0,007).

**4. Porównanie z Pythią-1B: pewna jest tylko część różnic** (różnica w jednostkach SE, SE różnicy liczone jak dla niezależnych prób, czyli ostrożnie; po jednym modelu na stronę, bez powtórzeń treningu):
- Po polsku: MultiBLiMP-PL 0,986 vs 0,774 (28 SE) to pewna różnica, ale oczekiwana, bo Pythia uczyła się na angielskim. Belebele po treści 0,330 vs 0,297 to 1,5 SE, czyli w granicach szumu.
- Po angielsku: ARC-E −4,4 pkt (3,0 SE) i MMLU −2,2 pkt (4,2 SE) to prawdopodobna luka. SIQA −0,9 pkt (0,6 SE) to brak wykrywalnej różnicy.
- Luka EN może wynikać po prostu z udziału angielskiego (10% danych Slayera wobec 100% u Pythii), więc nie jest jeszcze wnioskiem o jakości danych (zob. B2).

**Propozycja do Space:** obok surowego wyniku z liter dodać miarę po treści (prawdopodobieństwo / BPB poprawnej odpowiedzi, 5-shot, kilka szablonów pytania — tak zaleca praca na 26 modelach 2B, arXiv 2610.19185). Wtedy tabela pokaże postęp, który dziś jest niewidoczny.

**Trzy pytania:**
1. Czy angielska część danych (fineweb-edu + finemath wg `dataset.json`) była czyszczona z pytań ARC/MMLU? W `dataset.json` dekontaminacja jest opisana tylko dla web i tylko wobec 8tags/polemo2.
2. Czy planujesz wygaszanie LR na końcu treningu? Nasz krótki test (150 kroków z ckpt_13848) dał −0,047 nat lossu wobec stałego LR, bez zmiany trafności (wiersz 10). Kod i wyniki: katalog `wygaszanie/`, opis w `wygaszanie/README.md`.
3. Skąd są dodatki w `polish-dynaword-mix-extended-500M` ponad dynaword?

**Odpowiedzi Arka (30.10):**
1. Dekontaminacja wobec ARC była na pewno, wobec MMLU nie jest pewien. Trzeba sprawdzić jeszcze raz (A2).
2. Wygaszanie LR planuje, ale dopiero przy ok. 100 mld tokenów; dziś trening jest w 1/8.
3. Zbiór 500M to generowane dane SFT, licencja niepewna, został tylko u niego i go nie używa. Pomijamy.

Wszystko jest do sprawdzenia: surowe wyniki per pytanie, kod i komendy. Dla chętnych do niezależnego powtórzenia jest „ślepa” paczka (surowe dane i instrukcja, bez naszych liczb), suma kontrolna zipa `da0edbd792d2c8074bda39d7232c628fcfbf60933278728afd6db9220c225303`.

---

## Część 2. Zadania dla chętnych

Zasada dla każdego zadania: **zanim coś policzysz, odpowiedz, jaką decyzję zmieni wynik i czy efekt da się w ogóle zmierzyć.** Dziś sami się na tym złapaliśmy: test na 120 krokach mierzyłby głównie szum, bo trafność (accuracy) nie ruszyła nawet między wersjami 1.03 i 1.06. Dlatego przy testach z treningiem pierwszy krok to zawsze oszacowanie szumu i najmniejszego wykrywalnego efektu.

Każde zadanie ma: po co, jaką decyzję zmienia, czy się skaluje na większe modele, jak sprawdzić, że gotowe. Kto bierze, pisze pod wiadomością numer.

### A. Bez karty graficznej (start od zaraz)

**A1. Niezależne powtórzenie pomiaru formatu (ślepa paczka).**
Po co: potwierdzić albo obalić punkty 1–3 bez naszej sugestii. Zmienia: czy Space przechodzi na miarę po treści. Skaluje się: tak (metoda oceny). Gotowe: Twoje liczby + kod, porównane z naszymi dopiero po oddaniu.

**A2. Audyt przecieku testów w angielskiej części danych.**
Po co: jeśli fineweb-edu/finemath zawiera pytania ARC/MMLU, wyniki EN są zawyżone. Zmienia: czy wyniki EN w Space są wiarygodne i czy przed większym modelem trzeba dodać dekontaminację. Skaluje się: tak, problem rośnie z ilością danych. Jak: 13-gramy słów pytań i odpowiedzi ARC-C/E, MMLU, BoolQ, SIQA wobec `shared/en.parquet`; najpierw MMLU (Arek nie jest pewien dekontaminacji), ARC jako kontrola (wg Arka czyszczony). Gotowe: liczba trafień per test + lista przykładów.

**A3. PolQA w danych treningowych.**
Po co: `polqa` jest w rdzeniu danych Slayera, więc wynik na PolQA może być zawyżony. Zmienia: czy PolQA zostaje w porównaniu z Bielikiem. Skaluje się: tak. Gotowe: odsetek pytań testowych PolQA obecnych w danych.

**A4. Licencje per składnik `slayer-pl-8x3b`.**
Po co: przed publikacją większego modelu trzeba wiedzieć, co jest CC-BY-SA (wymusza tę samą licencję pochodnych). Zmienia: licencję przyszłego modelu. Gotowe: tabela składnik → licencja → źródło, z `shared/manifest.json` i `pack-XX/manifest.json`.

**A5. Rozbieżność WikiText.**
Po co: nasz byte_ppl na WikiText-2 to 1,893, w Space 1,846 (+2,5%), a forward modelu zgadza się z kodem treningu. Zmienia: czy nasz pipeline oceny jest wierny Space (od tego zależą wszystkie porównania). Gotowe: przyczyna różnicy albo dowód, że to ustawienie okna/tokenizacji.

**A6. Tokenizacja litery odpowiedzi.**
Po co: „ A” ze spacją i „A” bez spacji dają inne wyniki (arXiv 2509.15020). Mamy oba warianty dla ARC-C, brakuje reszty testów. Zmienia: dokładny przepis oceny w Space. Gotowe: tabela obu wariantów dla wszystkich testów z literami.

**A7. Kandydaci na dane — licencja i rozmiar.**
Lista: `HuggingFaceFW/finepdfs-edu` (pol_Latn), `Helsinki-NLP/fineweb-edu-translated` (pol), `epfml/FineWeb2-HQ` (pol_Latn), `openbmb/Ultra-FineWeb`, `PleIAs/SYNTH`. Po co: zanim cokolwiek trafi do treningu, licencja musi pozwalać trenować, a rozmiar PL musi być znany. Gotowe: licencja potwierdzona u źródła, liczba tokenów PL, ryzyko nakładania się z HPLT.

### B. Z kartą graficzną (po zgodzie Arka, każde z oszacowaniem szumu PRZED startem)

**B1. Kiedy model uczy się odpowiadać literą.**
Po co: SmolLM2-1.7B łapie format liter dopiero po 6–8 bln tokenów (arXiv 2502.02737). Śledzenie tego na kolejnych checkpointach pokazuje postęp, którego trafność nie widzi. Zmienia: kiedy przy większym modelu przejść z oceny po treści na ocenę z literami. Skaluje się: tak, to jest właśnie sygnał skalowania. Gotowe: krzywa „odsetek najczęstszej litery” i trafności z liter po checkpointach.

**B2. Udział angielskiego w danych (10% vs 25%).**
Po co: przy 10% wiedza z EN może w ogóle nie wchodzić (arXiv 2505.18091). Zmienia: przepis mieszanki dla większych modeli. Warunek: miarą jest BPB (pewność poprawnej odpowiedzi), nie trafność; polski musi zmieścić się w tolerancji ustalonej z góry. Plan i progi są gotowe, po recenzji.

**B3. Jakość polskiego webu (HPLT vs FineWeb2-HQ).**
Po co: przy dużych modelach brakuje dobrego polskiego tekstu, więc filtr jakości będzie ważniejszy niż ilość. Zmienia: źródło webu dla większych modeli. Warunek jak w B2.

**B4. Dłuższe wygaszanie LR.**
Krótki test pokazał spadek straty o 0,047 nat (wiersz 10), więc ma sens. Ramiona: do zera, umiarkowane, średnia ostatnich checkpointów (arXiv 2511.18903). Zmienia: harmonogram końca treningu.

**Czego NIE robimy:** poprawiania wyniku z liter przez dokładanie pytań testowych do danych — to uczy formatu, nie wiedzy.
