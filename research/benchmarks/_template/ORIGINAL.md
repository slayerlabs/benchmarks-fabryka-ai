# <Benchmark>: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpisz „nieustalone” z listą przeszukanych miejsc. Benchmark bez oryginału nie ma tego
pliku ani `REPRODUCTION.md`. Usuń oba i wypełnij `DATASET.md` (sekcja „Benchmark bez oryginału: karta zbioru
(DATASET.md)”).

Każdą liczbę spoza `results/LICZBY.json`, w każdym polu (n, bazy, SNR, wyniki referencyjne), oznacz na końcu jej
linii znacznikiem `<!-- liczba-spoza-wynikow: skąd jest liczba -->`, inaczej bramka liczb
(`tools/sprawdz_raporty.py`) ją odrzuci. Jedna linia niesie jeden wynik. Pole z kilkoma wynikami rozpisz na kilka
wierszy tabeli albo na listę, jedna pozycja na linię. Przykład: `benchmarks/arc-easy/ORIGINAL.md`.

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
| SNR: źródło | opublikowane wyniki modeli od 400 mln do 3 mld parametrów, z końca treningu, z jednego źródła (np. tabela w pracy, `evals/pythia-v0` w repo `EleutherAI/pythia`), bez mierzonego modelu i modeli odniesienia, a gdy jest ich mniej niż 3, wszystkich modeli źródła; modele i źródło: |
| SNR: rozrzut | odchylenie std. wyników między modelami: |
| SNR: SE | SE jednego wyniku dla n pełnego splitu, metodą z kolumny „SE” typu: |
| SNR: iloraz | rozrzut / SE: |
| SNR: szum checkpointów | odchylenie std. 5 ostatnich checkpointów jednego modelu (źródło) albo „nieustalone”: |
| MDE | panel 200: ; pełny split: ; SE różnicy wzięte z: |
| Kontaminacja | sprawdzona: metoda, odsetek / znana: źródło / nieznana |
| Wyniki referencyjne (odczyt RRRR-MM-DD) | model @ rewizja → wynik, źródło. Gdy po sprawdzeniu miejsc z METODOLOGIA.md („Model kontrolny etapu B”) żaden model, który da się pobrać, nie ma opublikowanego wyniku: „brak” i lista przeszukanych miejsc (etap B idzie wtedy jako „bez kontroli”) |
| Train policy | `eval_only` dla wszystkich splitów (domyślnie) albo `train_allowed`: które splity, issue z decyzją |
| Decyzja treningowa | |
| Znane rozbieżności | w tym katalog zadania lm-eval w `6d2abda4` wobec `v0.4.9.1` (hashe blobów) i rewizja zbioru (METODOLOGIA.md, „Wersja lm-eval”) |

Hashe blobów katalogu zadania daje komenda uruchomiona raz z `ref=6d2abda4` i raz z `ref=v0.4.9.1`; podkatalog z
innym hashem otwierasz tą samą komendą:

```bash
gh api 'repos/EleutherAI/lm-evaluation-harness/contents/lm_eval/tasks/<katalog>?ref=<tag>' --jq '.[] | "\(.sha) \(.name)"'
```
