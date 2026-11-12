# Protokół: Slayer1B-1.08 wobec Bielika 1.5B i LFM2.5 1.2B w swobodnej generacji i w prawdopodobieństwie odpowiedzi

<!-- liczba-spoza-wynikow: cały plik to protokół zapisany przed pomiarem, nie wyniki -->

Zapisany i zacommitowany PRZED pierwszą generacją pomiaru. Zmiana po pomiarze to nowy protokół (METODOLOGIA,
„Wspólny rdzeń”, p. 1); wynik policzony tym protokołem zostaje przy nim. Reguły pomiaru: METODOLOGIA.md oraz notatka
zespołu „Zasady raportowania benchmarków” (stan z 2026-11-02, §1, §4, §5, §7 i lekcje).

Pilot (45 poleceń, jedna próbka, ocena jednego agenta, bez protokołu) jest wyłącznie źródłem hipotez niżej. Żadna
jego liczba nie wchodzi do wyników.

## 0. Modele, sprzęt, rewizje

| klucz | model | rewizja HF | ładowanie |
|---|---|---|---|
| slayer | SlayerLab/Slayer1B-1.08 | ea0945b1 | `research/common/slayer_model.py` (commit 8b54700 tego repo), start id 0, `add_special_tokens=False` |
| bielik | speakleash/Bielik-1.5B-v3 | 4b250496 | transformers 5.2.2, BOS z tokenizera |
| lfm | LiquidAI/LFM2.5-1.2B-Base | 7453bca9 | transformers 5.2.2, BOS z tokenizera |

Wszystkie w float32 na Mac M5 Pro (MPS), torch 2.15.0, Python 3.12.2; jeden proces modelu naraz (`code/kolejka.sh`).
Wagi leżą poza repo; sha256 pliku wag, tokenizera, poleceń, przykładów i skryptów trafia do nagłówka każdego
surowego pliku wyników. Tokeny końca dokumentu (EOS): slayer {0}, bielik {2 `</s>`, 4 `<|im_end|>`},
lfm {2 `<|endoftext|>`, 7 `<|im_end|>`}.

Slayer 1.08 to checkpoint w trakcie serii (1.09 trenuje się dalej), a Bielik i LFM to modele po pełnym treningu.
Każdy wniosek mówi o checkpoincie 1.08, nie o „Slayerze” (lekcja ARC-Easy, 01.11).

## 1. Pytania badawcze i hipotezy

**P1.** W których kategoriach poleceń Slayer 1.08 różni się od Bielika 1.5B i od LFM2.5 1.2B w (a) poprawności
swobodnej generacji, (b) prawdopodobieństwie wzorcowej odpowiedzi (BPB)?
**P2.** Czy Slayer 1.08 ma swoiste wady generacji: brak naturalnego końca, powtórzenia, przecieki śladów rozumowania?
**P3.** Co z wyników wynika dla danych do dalszego treningu (wniosek w raporcie, oznaczony jako interpretacja).

### Reguła werdyktu (wspólna dla wszystkich hipotez)

Dla każdej pary modeli X−Y, metryki i kategorii: różnica parowana po poleceniach d_i (wartość polecenia = średnia po
3 seedach próbkowania; dla BPB jedna wartość deterministyczna), SE = sd(d_i)/√n (to jest SE klastrowane po poleceniu:
seedy w obrębie polecenia nie są niezależne), z = średnia(d)/SE. Werdykt z |z|: ≥ 3 „pewne”, 2–3 „prawdopodobne”,
< 2 „szum”; SE = 0 → „nierozstrzygalne”. Rodzina do poprawki Holma = jedna hipoteza × jedna para × jedna metryka po
wszystkich kategoriach, w których metryka jest zdefiniowana (zwykle m = 8); progi p jak dla |z| = 2 (0,0455) i
|z| = 3 (0,0027).

Hipoteza kierunkowa w danej kategorii jest:
- **potwierdzona**, gdy różnica ma przewidziany znak i po Holmie jest co najmniej „prawdopodobna”
  (siła = werdykt po Holmie);
- **obalona**, gdy różnica ma znak przeciwny i po Holmie jest co najmniej „prawdopodobna”;
- **nierozstrzygnięta** w pozostałych przypadkach (wynik pod progiem to nie „brak efektu”).

Hipoteza „łącznie” (wszystkie kategorie razem, n = liczba poleceń z metryką): ta sama reguła na różnicach po
poleceniach z całego zestawu, bez Holma (jedno porównanie na parę). Werdykt wiążący to werdykt per kategoria po
Holmie; wynik łączny jest uzupełnieniem. Bootstrap po poleceniach (10 000 losowań, seed 20261112, przedział
percentylowy 95%) podaję obok jako kontrolę wrażliwości; przy niezgodności znaku albo istotności z z raport to mówi,
a werdykt zostaje z z.

### Hipotezy z pilota

Hn.k = hipoteza n, porównanie k. S = Slayer 1.08, B = Bielik, L = LFM. Metryki z sekcji 4.

| id | twierdzenie (warunek potwierdzenia) | metryka | kategorie |
|---|---|---|---|
| H1.1, H1.2 | S kończy odpowiedź naturalnie rzadziej niż B (H1.1) i niż L (H1.2): S − Y < 0 | (c) odsetek naturalnych końców, szablon A, próbkowanie | wszystkie 8 |
| H1.3, H1.4 | Po zakończonej odpowiedzi ze znakiem nowej linii S daje EOS niższe log10 p niż B (H1.3) i L (H1.4) | (c2) log10 p(EOS) po „\n” | typy krótkie, 6 kategorii z nimi |
| H2.1, H2.2 | S powtarza się częściej niż B i L: udział powtórzonych 3-gramów S − Y > 0 | (d) rep3, próbkowanie | kategorie z poleceniami `otwarte` |
| H3.1, H3.2 | S ma niższą poprawność wiedzy niż B: S − B < 0 w poprawności (H3.1) i S − B > 0 w BPB (H3.2) | (a), (b) | pl_wiedza, wiedza_ogolna (rodzina Holma m = 2) |
| H4.1–H4.4 | S ma niższą poprawność w matematyce i rozumowaniu niż B (H4.1) i L (H4.2); BPB wzorca wyższe niż B (H4.3) i L (H4.4) | (a), (b) | matematyka, rozumowanie (m = 2) |
| H5.1, H5.2 | S ma niższy odsetek kodu przechodzącego testy niż B i L | (a) | kod (m = 1) |
| H6.1 | Polszczyzna: BPB S nie jest gorsze od B o więcej niż margines 0,05 bit/bajt — potwierdzona, gdy górna granica bootstrapowego CI95 różnicy S − B < 0,05; obalona, gdy dolna granica > 0,05 | (b) | pl_jezyk, tekst_techniczny (osobno, bez Holma: test równoważności) |
| H6.2 | Polszczyzna: BPB S niższe niż L: S − L < 0 | (b) | pl_jezyk, pl_wiedza, tekst_techniczny (m = 3) |
| H7 | S przecieka śladami rozumowania (`<think>`, `</think>`, `<|im_start|>`, `<|im_end|>` w tekście): odsetek S > 0 z dolną granicą bootstrapowego CI95 po poleceniach > 0, i S − Y > 0 („prawdopodobne” lub mocniej) dla Y = B, L | odsetek odpowiedzi z przeciekiem, wszystkie dekodowania szablonu A | łącznie |
| H8 | L pisze matematykę w formacie GSM8K (`<<a=b>>` albo linia `#### n`) częściej niż S i B: L − Y > 0 | odsetek odpowiedzi z formatem GSM8K | matematyka |
| H9.1, H9.2 | Sędziowie wolą B od S: odsetek wygranych B nad S > 0,5 (H9.1); L nad S > 0,5 (H9.2) | (e) | wszystkie polecenia `otwarte` łącznie (42); per kategoria opisowo |
| H10 | Angielski: BPB S wyższe niż L: S − L > 0 | (b) | angielski (m = 1) |

Dodatkowo bez hipotezy kierunkowej (opisowo, z werdyktem dla każdej pary): każda metryka (a)–(d) w każdej kategorii
dla wszystkich trzech par (S−B, S−L, B−L), z Holmem w rodzinie para × metryka. To jest mapa różnic dla P1; tylko
wiersze z tabeli hipotez są potwierdzające, reszta jest eksploracyjna i tak będzie oznaczona.

### Moc (MDE)

MDE ≈ (z_próg + 0,84) · SE różnicy. Przy n = 30 na kategorię i 8 kategoriach pod Holmem z_próg ≈ 2,73, więc
MDE ≈ 3,6 · SE. <!-- liczba-spoza-wynikow: kwantyl Holma m = 8 --> Dla poprawności binarnej uśrednionej po 3 seedach
SE różnicy po poleceniach wynosi od ok. 0,05 do 0,10, czyli MDE ok. 18–36 pkt procentowych na kategorię
<!-- liczba-spoza-wynikow: szacunek MDE z sd 0,3-0,55 przy n = 30 --> i ok. 7–12 pkt łącznie (n = 240). Test
poprawności per kategoria wykrywa więc tylko duże różnice; BPB (metryka ciągła, wysoki SNR) jest główną metryką dla
wiedzy (notatka, przegląd cytowań 30.10). MDE z faktycznego SE podam w raporcie obok każdego „szumu”.

## 2. Zestaw poleceń

- `dane/polecenia.jsonl`: 240 pozycji, 8 kategorii × 30; sha256
  `0f54e100fff2aeb18ae86f9060dd15608ee6b5ef6fb63a74932c40faf3e9f570`. <!-- liczba-spoza-wynikow: sha256 pliku -->
- `dane/shoty.jsonl`: 24 przykłady few-shot, 3 na kategorię, tematycznie rozłączne z poleceniami; sha256
  `b71c1bacdd125ac7df829f601079111958dbeb38070d157582b69bbfb3d1d3ce`. <!-- liczba-spoza-wynikow: sha256 pliku -->
- Kategorie i typy (liczba poleceń): <!-- liczba-spoza-wynikow: skład zestawu -->

  | kategoria | krotka | zdanie | liczba | kod | otwarte |
  |---|---|---|---|---|---|
  | pl_jezyk (polszczyzna: odmiana i korekta) | 12 | 12 | | | 6 |
  | pl_wiedza (wiedza o Polsce) | 30 | | | | |
  | wiedza_ogolna | 30 | | | | |
  | rozumowanie (logika) | 30 | | | | |
  | matematyka (zadania tekstowe) | | | 30 | | |
  | kod (Python) | | | | 30 | |
  | angielski | 16 | 8 | | | 6 |
  | tekst_techniczny (po polsku) | | | | | 30 |
- Typy: `krotka` (krótki fakt/forma; listy `akceptowane` ze wszystkimi formami fleksyjnymi i `zakazane`, jak PLCC),
  `zdanie` (korekta zdania; lista poprawnych wersji), `liczba` (zadanie tekstowe; liczba wzorcowa i wyrażenie,
  które ją liczy), `kod` (funkcja Pythona; testy jednostkowe ukryte przed modelem), `otwarte` (pisanie i tekst
  techniczny; 3–5 kryteriów oceny i wzorcowa odpowiedź).
- Trudność 1/2/3 po 1/3 w każdej kategorii (ocena autora, nie pomiar).
- **Autorstwo i licencja użycia.** Polecenia, przykłady i wzorce napisał od zera model Claude (Anthropic) 12.11.2026
  według `dane/SPEC.md` (spec pisania). Zestaw służy WYŁĄCZNIE DO OCENY: nie wolno go używać do treningu ani
  douczania żadnego modelu (warunki Anthropic dla treści generowanych przez Claude; METODOLOGIA, „Czystość
  benchmarku”). Zawyżenie wyniku modeli, które widziały teksty w stylu Claude, jest zagrożeniem trafności (sekcja 7).
- **Sprawdzenie zestawu przed pomiarem** (`code/zloz_zestaw.py`, tym samym kodem oceny co modele): każdy wzorzec
  weryfikowalny dostaje 1 od oceny automatycznej; `liczba` = wynik `obliczenie`; każdy wzorzec kodu przechodzi swoje
  testy w piaskownicy, a funkcja zwracająca None ich nie przechodzi.
- **Skażenie** (`code/skazenie.py`, wynik `wyniki/skazenie.json`): wspólne 13-gramy słów (i informacyjnie 8-gramy)
  polecenia + wzorca (+ testów) z GSM8K (train+test), ARC (Easy+Challenge, wszystkie splity), OpenBookQA
  (wszystkie splity), HumanEval (test) i MBPP (full). Wynik przed pomiarem: 0 z 240 pozycji ma wspólny 13-gram z którymkolwiek zbiorem (GSM8K 8792 rekordy, ARC 7787,
OBQA 5957, HumanEval 164, MBPP 500); przy 8-gramach 2 pozycje (`kod-15`, `kod-28`) dzielą wyłącznie ciągi
liczb i liter z danych testów (np. „1 2 3 4 5 1 2 3”), nie treść. <!-- liczba-spoza-wynikow: wynik skanu wyniki/skazenie.json -->
Rozumowanie (krótkie zagadki) i część poleceń mają mniej niż 13 słów, więc skan 13-gramów ich nie obejmuje. 13-gramy nie łapią
  tłumaczeń ani parafraz (notatka, „Dane”), więc wynik 0 nie wyklucza skażenia treścią.

## 3. Format promptu i dekodowanie

Prompt few-shot: 3 przykłady z `dane/shoty.jsonl` tej samej kategorii, w kolejności z pliku, potem polecenie.
Implementacja: `code/szablony.py` (testy w `code/test_rozmowy.py`).

**Szablon A (główny):**

```
Polecenie: <polecenie przykładu 1>
Odpowiedź:<sep><wzorzec przykładu 1>

… (przykłady 2 i 3)

Polecenie: <polecenie>
Odpowiedź:
```

`sep` = spacja dla typów krótkich, nowa linia dla `kod` i `otwarte`. Kategoria `angielski` ma etykiety `Task:` /
`Answer:`. Stop: napis `\nPolecenie:` (`\nTask:`).

**Szablon B (kontrola wrażliwości):** bloki `### Zadanie\n<polecenie>\n### Rozwiązanie\n<odpowiedź>`
(angielski: `### Problem` / `### Solution`), te same przykłady. Stop: napis `\n### `.

**Dekodowanie (identyczne dla wszystkich modeli, `code/generuj.py`):** szablon A: 3 próbki (temperatura 0,7, top-p
0,9; seedy 1, 2, 3) i greedy, w jednym batchu 4 wierszy tego samego promptu; szablon B: tylko greedy. Próbkowanie
na CPU z logitów float32: softmax(logity/T), sortowanie, odcięcie top-p (zostają tokeny, dla których skumulowane p
przed nimi ≤ 0,9), `torch.multinomial` z generatorem per wiersz o seedzie 1 000 003 · seed + numer pozycji.
<!-- liczba-spoza-wynikow: stała seeda --> Limit nowych tokenów: `krotka`/`zdanie` 48, `liczba` 160, `kod` 256,
`otwarte` 400. <!-- liczba-spoza-wynikow: limity tokenów --> Generacja wiersza kończy się na EOS, na napisie stopu
albo na limicie. Odpowiedź do oceny = tekst ucięty przed pierwszym napisem stopu. Te same limity w tokenach dają
różną liczbę bajtów przy różnych tokenizerach; liczba bajtów odpowiedzi trafia do wyników.

Próba dymna przed pełną kolejką (`code/dym.py`, po commicie tego protokołu, wynik poza tabelami): logity ścieżki z
KV cache wobec pełnego forwardu na 5 pozycjach, greedy batch 4 wobec batch 1 na 10 pozycjach, ręczny odczyt
wyrenderowanego promptu i odpowiedzi 3 pozycji (METODOLOGIA, p. 8). Zmiana protokołu po próbie dymnej idzie
osobnym commitem z opisem, przed pełną kolejką.

Odstępstwa świadome: batch 4 zamiast 1 (greedy w batchu może różnić się od greedy z batchem 1 szumem numerycznym
MPS; sprawdzam to na 10 pozycjach próby dymnej i podaję liczbę różnic); Slayer przez własny forward
`common/slayer_model.py`, nie przez oficjalny `load_slayer.py` (zgodność opisana w tamtym pliku i sprawdzana kontrolą
narzędzia, sekcja 6).

## 4. Metryki (ustalone przed pomiarem; kod `code/ocena.py`)

**(a) Poprawność automatyczna** na typach weryfikowalnych:
- `krotka`: pierwsza niepusta linia odpowiedzi po normalizacji (NFC, małe litery, interpunkcja → spacja) zawiera
  jako całą frazę któryś napis z `akceptowane` i żadnego z `zakazane`;
- `zdanie`: pierwsza niepusta linia po normalizacji równa któremuś napisowi z `akceptowane`;
- `liczba`: pierwsza liczba po ostatnim `Wynik:`, a bez znacznika ostatnia liczba odpowiedzi; poprawna przy
  |x − wzorzec| ≤ 0,005 <!-- liczba-spoza-wynikow: tolerancja --> (przecinek dziesiętny i spacje tysięcy
  rozpoznawane);
- `kod`: pierwszy blok ```` ```python ```` odpowiedzi (bez bloku — cała odpowiedź) + ukryte testy, w osobnym podprocesie
  `python -I` w pustym katalogu tymczasowym, `sandbox-exec` z zakazem sieci, limit 10 s; poprawny = kod wyjścia 0.
Wartość polecenia = średnia z 3 próbek (główna); greedy szablonu A i greedy szablonu B osobno (wtórne).

**(b) BPB wzorca** (`code/bpb.py`): −Σ log p(tokenów ciągu | prompt) / (ln 2 · bajty UTF-8 ciągu), ciąg = `sep` +
wzorzec, osobno w szablonie A (główny) i B. Podział kontekst/ciąg jak lm-eval `_encode_pair` (całość kodowana
razem, kontekst osobno); flaga, gdy tokenizer skleja granicę. Dla `otwarte` wzorzec to jedna z wielu dobrych
odpowiedzi, więc BPB tam jest wtórne. Normalizacja po bajtach, nie po tokenach (różne tokenizery); obok podaję NLL na
token i bajty na token każdego modelu w każdej kategorii (lekcja BLiMP o tokenizerach).

**(c) Naturalne zakończenie:** odpowiedź zakończona EOS albo napisem stopu przed limitem tokenów (szablon A,
próbki). **(c2) Sonda EOS:** p(EOS) jako następnego tokenu po tekście 0-shot `Pytanie: <polecenie>\nOdpowiedź:
<wzorzec>` (angielski `Question:`/`Answer:`), bez i z końcowym `\n`; metryka log10 p i ranga, typy krótkie.

**(d) Powtórzenia** na `otwarte`: udział 3-gramów słów (`\w+`, małe litery) występujących wcześniej w tej samej
odpowiedzi (rep3) i distinct-2; plus odsetek odpowiedzi z przeciekiem znaczników (H7) i z formatem GSM8K (H8) na
wszystkich typach.

**(e) Ślepa ocena parami** (`code/sedziowie.py`, instrukcja `dane/INSTRUKCJA_SEDZIEGO.md`): 42 polecenia `otwarte`
× 3 pary modeli = 126 par, odpowiedź z próbki seed 1 szablonu A, strona A/B i kolejność par losowane
(`random.Random(20261112)`), klucz poza paczką. Dwaj niezależni sędziowie (osobni agenci uruchamiani przez
orkiestratora, bez dostępu do klucza i do siebie nawzajem). Werdykt sędziego: A / B / remis (remis tylko, gdy nie da
się wskazać lepszej). Wynik pary z punktu widzenia modelu X: 1 wygrana, 0,5 remis, 0 przegrana; wartość polecenia =
średnia dwóch sędziów; odsetek wygranych X nad Y = średnia po poleceniach, SE po poleceniach, z wobec 0,5.
Zgodność: kappa Cohena na 3 klasach (po przełożeniu stron na tożsamość modeli). Przy kappa < 0,20 wynik sędziów
jest oznaczony jako niewiarygodny i hipotezy H9 są nierozstrzygnięte niezależnie od z.
<!-- liczba-spoza-wynikow: progi protokołu --> Sędziowie to także modele Claude (zagrożenie w sekcji 7).

## 5. Statystyka

Reguła werdyktu i Holm: sekcja 1. SE klastrowane po poleceniu (próbki jednego polecenia uśrednione przed
różnicą), różnice parowane (te same polecenia), bootstrap po poleceniach jako kontrola. Kontrola tokenizera: BPB
per bajt; obok NLL/token. Wrażliwość: dla każdej różnicy z tabeli hipotez podaję wynik z greedy A i z szablonu B;
twierdzenie, którego znak odwraca się w szablonie B, opisuję jako zależne od szablonu. Analizy dodane po pomiarze
oznaczam jako eksploracyjne. Remisy w ocenie automatycznej nie występują (ocena 0/1 bez porównania), w ocenie
sędziów reguła wyżej; liczba remisów idzie do raportu.

## 6. Kontrola narzędzia

`code/kontrola.py`: tym samym kodem logprob (`modele.logprob_ciagu`), który liczy BPB, liczę dla Slayer1B-1.08
ARC-Challenge test (n = 1172) i OpenBookQA test (n = 500), 0-shot, prompty z `EVALUATION.json` karty 1.08
(`protocol/task_protocols`), zbiory z tymi samymi rewizjami i sha256 parquetów co w karcie. Wartości referencyjne
(EVALUATION.json, `models/1.08/tasks`): ARC-C acc_norm 0,300341 i acc 0,271331; OBQA acc_norm 0,348 i acc 0,23.
<!-- liczba-spoza-wynikow: wartości referencyjne z EVALUATION.json karty 1.08 --> Warunek odtworzenia (METODOLOGIA,
etap B): |różnica| ≤ 0,02 dla każdej z czterech wartości. <!-- liczba-spoza-wynikow: próg etapu B --> Niespełniony →
pomiar BPB i oceny stoją do znalezienia przyczyny. Ta kontrola obejmuje ścieżkę Slayera; dla Bielika i LFM
sprawdzam zgodność `logprob_ciagu` z log p z pełnego forwardu transformers na 5 pozycjach (test spójności, nie
odtworzenie opublikowanej liczby — opublikowanych liczb tych modeli w tym ustawieniu nie mamy; oznaczone wprost).

## 7. Zagrożenia trafności (z góry)

1. **Skażenie formatem.** LFM w pilocie pisał matematykę w formacie GSM8K (`<<…>>`, `####`), więc mógł widzieć
   GSM8K albo dane w jego formacie; zestaw matematyki jest nowy i po polsku, ale format rozwiązania może pomagać.
   H8 mierzy to wprost. Skan 13-gramów nie wykrywa tłumaczeń.
2. **Claude jako autor poleceń i sędzia.** Wzorce mają styl Claude; model, który widział dużo tekstu w tym stylu
   (dane syntetyczne), dostaje niższe BPB. Sędziowie są modelami tej samej rodziny co autor wzorców i mogą
   preferować podobny styl. Nie da się tego usunąć w tym badaniu; raport podaje to przy każdym wyniku BPB `otwarte`
   i każdym wyniku sędziów.
3. **Różne tokenizery.** BPB per bajt, limity w tokenach dają różne długości w bajtach; raportuję bajty/token.
4. **Udział języków w danych.** Slayer ma ok. 17,5% angielskiego w tokenach, LFM jest głównie angielski i
   wielojęzyczny, Bielik polski. Różnica w kategorii angielskiej albo polskiej ma oczywiste wyjaśnienie zastępcze w
   składzie danych, nie w „jakości modelu” (notatka §7).
5. **Checkpoint w toku.** 1.08 to krok 1709 serii, 1.09 trenuje się dalej; Bielik i LFM są po pełnym treningu.
6. **Few-shot i szablon.** Jeden szablon główny i jeden wariant; wynik może zależeć od szablonu (sekcja 5).
7. **Mały n.** 30 poleceń na kategorię; MDE w sekcji 1.
8. **Ocena regułami.** Dopasowanie napisów może odrzucić poprawną odpowiedź w nietypowej formie albo przyjąć
   wymienioną obok poprawnej; reguły są te same dla wszystkich modeli.
9. **Deanonimizacja w ocenie sędziów.** Znaczniki typu `<think>` w odpowiedzi mogą zdradzić model; nie usuwam ich,
   bo są częścią jakości odpowiedzi.

## 8. Pliki

- `code/` — cały kod pomiaru i testy (`python -I code/test_rozmowy.py`), kolejka `code/kolejka.sh`.
- `dane/` — zestaw, spec pisania, instrukcja sędziego.
- `wyniki/surowe/*.jsonl.gz` — surowe wyniki per pozycja (generacje, BPB, kontrola), z nagłówkiem sha wejść.
- `wyniki/LICZBY.json` i raport — po ocenach sędziów, generowane skryptem z surowych wyników.
