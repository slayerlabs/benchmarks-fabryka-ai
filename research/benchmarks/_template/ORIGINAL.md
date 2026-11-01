# <Benchmark>: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpisz „nieustalone” z listą przeszukanych miejsc. Benchmark bez oryginału nie ma tego
pliku ani `REPRODUCTION.md`. Usuń oba i wypełnij `DATASET.md` (sekcja „Benchmark bez oryginału: karta zbioru
(DATASET.md)”).

Każdą liczbę spoza `results/LICZBY.json`, w każdym polu (n, bazy, SNR, wyniki referencyjne), oznacz na końcu jej
linii znacznikiem `<!-- liczba-spoza-wynikow: skąd jest liczba -->`, inaczej bramka liczb
(`tools/sprawdz_raporty.py`) ją odrzuci. Jedna linia niesie jeden wynik. Pole z kilkoma wynikami rozpisz na kilka
wierszy tabeli albo na listę, jedna pozycja na linię. Przykład: `benchmarks/wikitext-2/ORIGINAL.md`.

| pole | wartość |
|---|---|
| Co mierzy | |
| Źródła | praca: ; repo autorów @ commit: ; zbiór HF @ rewizja: |
| Dane | split w pracy: ; n: ; split w Space/repo: ; n: ; pełny split albo panel 200: ; licencja: ; ukryte odpowiedzi w teście: tak/nie |
| Format zadania | |
| Prompt | szablon z pracy albo kodu; gdy praca nie ma promptu modelu językowego (modele dostrajane): szablon z implementacji Space/lm-eval z separatorem celu (`target_delimiter`, domyślnie spacja) i pełnym ocenianym tekstem jednej opcji |
| Ocena | |
| Metryka decyzyjna | |
| Agregacja | |
| Bazy | losowa: ; większościowa (udział najczęstszej poprawnej odpowiedzi, przy wyborze odpowiedzi najczęstszej pozycji opcji, dokładnie ze splitu): |
| SNR | z opublikowanych wyników kilku modeli z jednego źródła (np. tabela w pracy, `evals/pythia-v0` w repo `EleutherAI/pythia`); rozrzut wyników (odchylenie std.) między modelami/checkpointami: ; typowe SE dla n pełnego splitu: ; SNR = rozrzut / SE: ; modele i źródło: |
| Wyniki referencyjne (odczyt RRRR-MM-DD) | model @ rewizja → wynik, źródło. Gdy po sprawdzeniu miejsc z METODOLOGIA.md („Model kontrolny etapu B”) żaden model, który da się pobrać, nie ma opublikowanego wyniku: „brak” i lista przeszukanych miejsc (etap B idzie wtedy jako „bez kontroli”) |
| Train policy | `eval_only` dla wszystkich splitów (domyślnie) albo `train_allowed`: które splity, issue z decyzją |
| Decyzja treningowa | |
| Znane rozbieżności | w tym katalog zadania lm-eval w `6d2abda4` wobec `v0.4.9.1` (hashe blobów) i rewizja zbioru (METODOLOGIA.md, „Wersja lm-eval”) |
