# Social IQa (T46)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Typ testu: [`mc`](../../README.md#benchmarki-i-typy).

Social IQa sprawdza rozumienie sytuacji społecznych: model dostaje scenkę i pytanie o motywację, reakcję
emocjonalną albo następne działanie bohatera, a wybiera jedną z trzech odpowiedzi. lm-eval `0.4.9.1`, zadanie
`social_iqa` (prompt przepisany do `slayer_social_iqa` w `common/zadania.py`), 0-shot, split `validation`, metryka
decyzyjna `acc`.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, werdykt: bez kontroli: nierozstrzygnięte.
- [`RECIPE.md`](RECIPE.md): przepis przebiegu centralnego i pomiar wstępny autora.
- Wyniki: [`results/central-run/social-iqa/`](../../results/central-run/social-iqa/) (przebieg centralny, RTX 4090).
- Test: `tests/test_social_iqa.py`.

## Wyniki

Wyniki przebiegu centralnego z 03.11 policzył kod sprzed zmian z 04.11 (limit 4096 tokenów z BOS, budżet loglik jak HFLM), więc są do przeliczenia w przebiegu Slayera 1.07; bazy, SE i porównanie z b przeliczono 07.11 z próbek per pytanie bez modelu (`tools/podsumuj_ponownie.py`). <!-- liczba-spoza-wynikow: daty commitów 592c8af i 3ba8ae3 -->

Pełny split, n = 1954. b = 0,3362 (stała odpowiedź „zawsze trzecia opcja”, 657 z 1954), baza losowa 0,3333.
Różnica wobec b parowana po pytaniach. <!-- liczba-spoza-wynikow: rozkład celu z probki/ przebiegu centralnego -->

| model | `acc` | n | SE A | najczęstsza predykcja | wynik − b | SE par. | z | werdykt |
|---|---:|---:|---:|---|---:|---:|---:|---|
| Slayer 1.06 | 0,3895 | 1954 | 0,0110 | opcja 2: 0,3480 | +5,32 pkt | 0,0153 | 3,47 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/slayer1b-1.06 (results_rozszerzone.json, probki) -->
| Qwen3.5-0.8B-Base | 0,4186 | 1954 | 0,0112 | opcja 2: 0,3362 | +8,24 pkt | 0,0153 | 5,38 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/qwen3.5-0.8b-base -->
| LFM2.5-1.2B-Base | 0,4284 | 1954 | 0,0112 | opcja 3: 0,3414 | +9,21 pkt | 0,0154 | 5,97 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/lfm2.5-1.2b-base -->
| LFM3-1.7B-Base | 0,4545 | 1954 | 0,0113 | opcja 3: 0,3383 | +11,82 pkt | 0,0156 | 7,59 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/lfm3-1.7b-base -->
| EuroLLM-1.7B | 0,4150 | 1954 | 0,0111 | opcja 3: 0,3408 | +7,88 pkt | 0,0155 | 5,08 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/eurollm-1.7b -->

Wszystkie modele rozkładają odpowiedzi prawie równo na trzy opcje, więc żaden wynik nie jest stałą odpowiedzią.
Slayer 1.06 jest nad b i pod czterema modelami odniesienia.
Najbliższy jest EuroLLM-1.7B, o 2,56 pkt wyżej, a różnica parowana po pytaniach ma z = −2,81, więc ta przewaga jest prawdopodobna, nie pewna; przewagi Qwen3.5-0.8B-Base (2,92 pkt, z = −3,03), LFM2.5-1.2B-Base (z = −3,97) i LFM3-1.7B-Base (z = −7,07) są pewne. <!-- liczba-spoza-wynikow: results/central-run/social-iqa, probki/T46_space.jsonl.gz, różnice parowane po pytaniach -->

Modele odniesienia mieszczą się w przedziale, który MobileLLM podaje dla modeli około 1 mld (42–45, bez promptu
i wersji kodu, więc tylko rząd wielkości; `REPRODUCTION.md`). <!-- liczba-spoza-wynikow: arXiv:2402.14905v2, tabela 8 -->

## Kontrola

**Bez kontroli: nierozstrzygnięte.** Żaden model z listy „Model kontrolny etapu B” nie ma opublikowanego wyniku
zero-shot na Social IQa z promptem i wersją kodu: Pythia-1b-v0 nie ma tego testu w pliku wyników, karta
EuroLLM-1.7B go nie podaje, Open LLM Leaderboard v2 go nie zawiera, a praca podaje tylko wyniki fine-tuned. Wynik nie
idzie do tabeli CodeSOTA ani do meta-oceny. Szczegóły i miejsca szukania: [`REPRODUCTION.md`](REPRODUCTION.md).

## Pomiar wstępny autora (poza tabelą)

Przed przebiegiem centralnym autor PR policzył Slayera 1.06 na własnej karcie (RTX 5060 Ti), na panelu Space 200 i na
pełnym splicie. To nie jest wynik przebiegu: METODOLOGIA każe liczyć wszystkie modele przebiegiem centralnym, więc
liczby z tego pomiaru nie idą do tabeli wyżej ani do CodeSOTA. Na pełnym splicie pomiar dał te same decyzje we
wszystkich 1954 pytaniach co przebieg centralny. Pliki: [`results/social_iqa.json`](results/social_iqa.json), <!-- liczba-spoza-wynikow: porównanie results/slayer-1.06/social_iqa_full.jsonl.gz z probki/ przebiegu centralnego -->
[`results/slayer-1.06/`](results/slayer-1.06/) (per pytanie), skrypt [`zbierz_wyniki.py`](zbierz_wyniki.py); komenda
i środowisko: [`RECIPE.md`](RECIPE.md), „Pomiar wstępny autora”.

Panel 200 nie jest wyrównany klasowo: trzecia opcja jest poprawna w 81 z 200 pytań, więc stała odpowiedź daje tam
0,405, a Slayer 0,39 (z −0,43, szum). Werdykt o umiejętności opiera się na pełnym splicie (METODOLOGIA, „Space i
panel 200”). <!-- liczba-spoza-wynikow: rozkład gold i z z results/social_iqa.json -->
