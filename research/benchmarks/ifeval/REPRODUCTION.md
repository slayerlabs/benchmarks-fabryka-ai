# IFEval: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md). Czego nie zapisano w chwili pomiaru, oznaczono „niezapisane”. Wersja angielska: [`REPRODUCTION.en.md`](REPRODUCTION.en.md).

Werdykt i zdanie recenzenta wypełnia recenzent przy scalaniu PR (jak w winogrande).

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1`, zadanie `ifeval` (protokół przebiegu centralnego `bench50-v0.3.1-fullB`, wpis `T36`). Kandydat kontroli liczył harness OLL v2 w hashu `a781a6b`, wersja zadania 2.0 (zadanie `leaderboard_ifeval`), więc to jest kod wskazany przez repo, nie tamten plik bajt w bajt. |
| dlaczego ten kod | Issue #40 i wpis T36 każą liczyć zadaniem lm-eval `ifeval`. Kandydat kontroli był liczony starszym harnessem (wersja zadania 2.0, przed commitem lm-eval `2de3688f`, który podniósł `leaderboard_ifeval` do 3.0 i zmienił tokenizer zdań NLTK z `punkt` na `punkt_tab`). Rozbieżności (5)-(7) z `ORIGINAL.md` (BOS, batch, wersja zadania) to pierwsze miejsca do sprawdzenia, gdy warunek nie przejdzie. |
| model kontrolny @ rewizja | `EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`, dtype float32, jeden wiodący BOS `<\|endoftext\|>` (id 0), dokładnie jeden |
| dlaczego ten model | Jedyny kandydat, którego przebieg OLL v2 spełnia punkt 3 karty w całości (rewizja, prompt, 0-shot, metryka, dekodowanie zachłanne, wersja kodu). Zob. `ORIGINAL.md`, wiersz „Kandydat kontroli etapu B”. |
| zbiór @ rewizja, split, n | `google/IFEval` @ `966cd89545d6b6acfd7638bc708b98261ca58e84`, `train`, n = 541. (Kandydat użył `wis-k/instruction-following-eval`, treść identyczna; zob. `ORIGINAL.md`, wiersz „Znane rozbieżności”.) |
| wynik (SE) | `prompt_level_strict_acc` 0,2033 (110 z 541), CI95 [0,1701; 0,2384] (paired bootstrap, 10000 powtórzeń, seed 20261028). SE A 0,017304 informacyjnie (liczone tu jako √(p(1−p)/n)). Przebieg kontrolny 0-BOS jest podany osobno w sekcji „Diagnostyka BOS” (jego CI95 to przybliżenie normalne, inna metoda). |
| wartość referencyjna i źródło | 0,168207 = 91 z 541. OLL v2, przebieg 2025-01-27, `EleutherAI/pythia-1b` @ `f73d7dcc`, float16, harness `a781a6b`, wersja zadania 2.0, zbiór `wis-k/instruction-following-eval`. Szczegóły per prompt są za bramką HF (403), więc porównanie nie może być parowane. |
| różnica | +0,035120, czyli +3,51 pkt. Ostrożne SE niezależne (górna granica: te same prompty, brak wyników per prompt wartości referencyjnej) √(0,017304² + 0,016082²) = 0,023623, z = 1,487, szum. |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0 (pusta odpowiedź, typ `ifeval`). Pythia − b = +0,2033, SE A 0,017304, z = 11,75, pewne, czyli wynik > b + 2 SE. Wyłącznie informacyjnie: predyktor „echo promptu” (135 z 541 = 0,249538) leży powyżej wyniku kontroli (różnica −0,046211 dla wartości referencyjnej, z = −1,82 niezależnie), więc sama kontrola b = 0 nie wyłapie błędu powtarzania promptu. Wyłapuje go warunek ±2 SE poniżej. <!-- liczba-spoza-wynikow: echo promptu i różnica wobec wartości referencyjnej, informacyjnie, wyliczenie 2026-11-16 --> |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, w granicach 2 SE. SE wartości referencyjnej 0,016082, więc 2 SE = 0,032163 > 0,02. Okno 0,168207 ± 0,032163 = [0,136; 0,200] (ok. 73,6 do 108,2 promptu z 541). Zapisany przed przebiegiem (karta `ORIGINAL.md`, wiersz „Kandydat: warunek odtworzenia”). <!-- liczba-spoza-wynikow: granice okna przeliczone na prompty z 0,168207 ± 0,032163 na 541 --> |
| werdykt | `[dla recenzenta]` (jedno z: spełniony / niespełniony / ...; wypełnia recenzent przy scalaniu, zob. „Fakty do zdania werdyktu” niżej) |

## Fakty do zdania werdyktu (to nie jest werdykt)

- Estymata punktowa 0,2033 = 110/541 leży ok. 2 prompty powyżej górnej granicy okna 0,200 (= 108,2 promptu). Formalnie warunek etapu B **nie jest spełniony o włos**. Nie wolno tego zapisać jako „spełniony”. <!-- liczba-spoza-wynikow: górna granica okna w promptach, przeliczenie z 0,200 na 541 -->
- CI95 kontroli [0,1701; 0,2384] zawiera wartość referencyjną 0,168 i pokrywa się z większością okna. Różnica wobec wartości referencyjnej jest statystycznie nie do odróżnienia od szumu (z = 1,487, ostrożnie, niezależnie).
- `ORIGINAL.md` wskazał z góry BOS jako podejrzanego nr 1 na wypadek niepowodzenia warunku: kandydat najpewniej liczył bez wiodącego BOS (`add_bos_token` domyślnie `False` w HFLM), przebieg repo używa dokładnie jednego. Przebieg kontrolny 0-BOS (0,1701 = 92/541, w oknie) jest zgodny z tym podejrzeniem, ale to diagnostyka: nie czyni warunku etapu B spełnionym po fakcie, bo warunek dotyczy przebiegu protokołowego z 1 BOS, który zostaje ok. 2 prompty poza oknem.

### Diagnostyka BOS (Pythia-1b, `prompt_level_strict_acc`, n = 541)

| silnik | 1 BOS | 0 BOS |
|---|---:|---:|
| CUDA (lm-eval) | 0,2033 (110/541) | 0,1701 (92/541) |
| MLX | 0,2107 (114/541) | 0,1793 (97/541) |

Metody CI95 różnią się między przebiegami CUDA. 1 BOS: [0,1701; 0,2384], paired bootstrap (10000 powtórzeń, seed 20261028). 0 BOS: [0,1384; 0,2017], przybliżenie normalne, nie bootstrap, więc to inna metoda niż w wierszu 1-BOS. Wartość 0,1701 pojawia się dwa razy przez zbieg okoliczności dwóch różnych wielkości: dolna granica CI przebiegu 1-BOS i estymata punktowa przebiegu 0-BOS (92/541). Obie są poprawne.

Test sparowany (McNemar, `prompt_level_strict_acc`, te same 541 promptów, z poprawką na ciągłość). Oba silniki dzielą te same prompty i te same wagi, więc to nie są niezależne powtórzenia: nie łącz p-wartości i nie czytaj tego jako „potwierdzone dwa razy”.

| silnik | 1 BOS | 0 BOS | niezgodne (pomógł / zaszkodził) | netto | chi2 (cc) | p |
|---|---|---|:---:|:---:|:---:|:---:|
| CUDA (lm-eval) | 0,2033 (110/541) | 0,1701 (92/541) | 68 (43 / 25) | +18 = +3,33 pkt | 4,250 | 0,039 | <!-- liczba-spoza-wynikow: McNemar z plików per prompt results/pythia-1b-1bos i -0bos, wyliczenie 2026-11-19 -->
| MLX | 0,2107 (114/541) | 0,1793 (97/541) | 75 (46 / 29) | +17 = +3,14 pkt | 3,413 | 0,065 | <!-- liczba-spoza-wynikow: McNemar MLX z BOS_PAIRED_TEST.md, przebieg eksploracyjny -->

Odczyt: znak i wielkość zgadzają się między silnikami (+3,3 i +3,1 pkt, BOS pomaga netto), przy czym z góry ustalony próg 3,841 jest przekroczony na CUDA (p = 0,039), a o włos niedosięgnięty na MLX (p = 0,065). BOS nie działa jednostronnie: na obu silnikach część promptów na nim traci (25 i 29). To diagnostyka kierunkowa, nie potwierdzenie. Źródło: CUDA per prompt z przebiegu na vast (2026-11-19, eksploracyjny/kontrolny), MLX z `BOS_PAIRED_TEST.md` (przebieg nocny, Mac, eksploracyjny). Liczby per prompt CUDA są w `results/pythia-1b-1bos/` i `results/pythia-1b-0bos/`. <!-- liczba-spoza-wynikow: netto McNemara w pkt i próg chi2, z plików per prompt results/pythia-1b-*bos -->

Relacja do wartości referencyjnej (91/541 = 0,168): liczba trafień 0-BOS CUDA (92/541 = 0,1701) jest zbieżna z liczbą trafień wartości referencyjnej (91/541). To zgodność dwóch liczb, nie test sparowany (wyniki per prompt wartości referencyjnej są za bramką HF), a wartość referencyjna różni się też float16, harnessem `a781a6b`, wersją zadania 2.0 i repozytorium zbioru. Nie dowodzi to, że wartość referencyjna była liczona bez BOS, a BOS nie jest wykazany jako cała przyczyna. Różnica 1-BOS wobec wartości referencyjnej została już zakwalifikowana wyżej jako szum (z = 1,487).

## Przewidywanie przed przebiegiem

Przed przebiegiem (`ORIGINAL.md`, etap A) oczekiwano, że kontrola Pythia-1b wpadnie w okno [0,136; 0,200]. Zapisano też z góry: gdyby warunek nie przeszedł, pierwszym podejrzanym jest wiodący BOS (kandydat najpewniej liczył bez BOS, różnice 5-7). Źródło: `ORIGINAL.md`, wiersze „Kandydat: warunek odtworzenia” i „Kandydat: BOS, batch i wersja zadania”.

## Zdanie recenzenta

`[dla recenzenta]`

---

Pola niezapisane w chwili pomiaru: wersja sterownika i liczba wątków hosta z RTX 5090: niezapisane.

Komenda i środowisko: [`RECIPE.md`](RECIPE.md) (lm_eval 0.4.9.1, transformers 4.57.6, torch 2.8.0+cu128, RTX 5090, batch 1, `max_gen_toks` 1280, zachłannie, 0-shot, bez szablonu czatu).
