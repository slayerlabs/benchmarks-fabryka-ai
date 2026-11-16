# <Benchmark>: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpisz „nieustalone” z listą przeszukanych miejsc. Benchmark bez oryginału nie ma tego
pliku ani `REPRODUCTION.md`. Usuń oba i wypełnij `DATASET.md` (sekcja „Benchmark bez oryginału: karta zbioru
(DATASET.md)”).

Każdą liczbę spoza `results/LICZBY.json`, w każdym polu (n, bazy, SNR, wyniki referencyjne), oznacz na końcu jej
linii znacznikiem `<!-- liczba-spoza-wynikow: skąd jest liczba -->`, inaczej bramka liczb
(`tools/sprawdz_raporty.py`) ją odrzuci. Jedna linia ze znacznikiem ma jedno źródło. Pole z wynikami z kilku źródeł
(kilka modeli, plików, przeliczeń) rozpisz na kilka wierszy tabeli albo na listę, jedno źródło na linię, każde ze
swoim znacznikiem. Znacznik zwalnia z bramki całą linię, więc liczby pod nim sprawdza tylko recenzent. Przykład: `benchmarks/winogrande/ORIGINAL.md` (nie ma jeszcze pól „Typ testu” i „SNR: szum checkpointów”).

| pole | wartość |
|---|---|
| Co mierzy | |
| Źródła | praca: ; repo autorów @ commit: ; zbiór HF @ rewizja: |
| Dane: split w pracy | split: ; n: |
| Dane: split w Space/repo | split: ; n: ; pełny split albo panel 200: |
| Dane: licencja | licencja autorów: ; tag HF: ; ukryte odpowiedzi w teście: tak/nie |
| Typ testu | link do wiersza testu w [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy) (typ stoi tylko tam): |
| Format zadania i prompt | szablon z pracy albo kodu; gdy praca nie ma promptu modelu językowego (modele dostrajane): szablon z implementacji Space/lm-eval z separatorem celu (`target_delimiter`, domyślnie spacja) i pełnym ocenianym tekstem jednej opcji |
| Ocena | |
| Metryka decyzyjna | |
| Agregacja i grupy | średnia po pytaniach czy po podtestach, wagi: ; poziomy grup i poziom, który wiąże werdykt: |
| Bazy | losowa: ; stała odpowiedź (kolumna typu, dokładnie ze splitu): ; b: |
| SNR: źródło | panel z METODOLOGII („Panel SNR”); do przebiegu, który obejmie test, w polach SNR wpisz „po przebiegu centralnym”; modele i commit przebiegu: |
| SNR: rozrzut | odchylenie std. wyników modeli panelu: |
| SNR: SE | SE jednego wyniku dla n pełnego splitu, metodą z kolumny „SE” typu: |
| SNR: iloraz | rozrzut / SE: ; przedział 95%: ; najmniejszy bez jednego modelu panelu: |
| SNR: szum checkpointów | odchylenie std. 5 ostatnich checkpointów jednego modelu (źródło) albo „nieustalone”: |
| MDE | panel 200: ; pełny split: ; SE różnicy wzięte z: |
| Kontaminacja | sprawdzona: metoda, odsetek / znana: źródło / nieznana |
| Wyniki referencyjne (odczyt RRRR-MM-DD) | model @ rewizja → wynik, źródło. Gdy po sprawdzeniu miejsc z METODOLOGIA.md („Model kontrolny etapu B”) żaden model, który da się pobrać, nie ma opublikowanego wyniku: „brak” i lista przeszukanych miejsc (etap B idzie wtedy jako „bez kontroli”). Każdy model z `results/` lm-eval @ `afbf8e66` (komenda pod tabelą) i z cytowanej tabeli, który da się pobrać, osobno |
| Train policy | `eval_only` dla wszystkich splitów (domyślnie) albo `train_allowed`: które splity, issue z decyzją |
| Decyzja treningowa | |
| Znane rozbieżności | w tym katalog zadania lm-eval w `6d2abda4` wobec `v0.4.9.1` (hashe blobów) i rewizja zbioru (METODOLOGIA.md, „Wersja lm-eval”) |

Hashe blobów katalogu zadania daje komenda uruchomiona raz z `ref=6d2abda4` i raz z `ref=v0.4.9.1`; podkatalog z
innym hashem otwierasz tą samą komendą:

```bash
gh api 'repos/EleutherAI/lm-evaluation-harness/contents/lm_eval/tasks/<katalog>?ref=<tag>' --jq '.[] | "\(.sha) \(.name)"'
```

Pliki wyników z katalogu `results/` lm-eval @ `afbf8e66` (pole „Wyniki referencyjne”) daje `git grep` po nazwie
zadania w tamtej wersji; plik otwierasz przez `git show afbf8e66:<ścieżka>` (wynik, SE, `num_fewshot`, `model_args`):

```bash
git clone --no-checkout https://github.com/EleutherAI/lm-evaluation-harness
git -C lm-evaluation-harness grep -l '"<zadanie>"' afbf8e66 -- results/
```
