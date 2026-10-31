# <Benchmark>: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpisz „nieustalone” i dopisz, gdzie szukałeś. Benchmark bez oryginału nie ma tego pliku
ani `REPRODUCTION.md`. Usuń oba i wypełnij `DATASET.md` (sekcja „Benchmark bez oryginału: karta zbioru
(DATASET.md)”).

| pole | wartość |
|---|---|
| Co mierzy | |
| Źródła | praca: ; repo autorów @ commit: ; zbiór HF @ rewizja: |
| Dane | split: ; n: ; licencja: ; ukryte odpowiedzi w teście: tak/nie |
| Format zadania | |
| Prompt | |
| Ocena | |
| Metryka decyzyjna | |
| Agregacja | |
| Bazy | losowa: ; większościowa: |
| SNR | z opublikowanych wyników albo „nieustalone”; rozrzut wyników (odchylenie std.) między modelami/checkpointami: ; typowe SE: ; SNR = rozrzut / SE: ; modele: |
| Wyniki referencyjne (odczyt RRRR-MM-DD) | model @ rewizja → wynik, źródło. Liczbę, której nie ma w `results/LICZBY.json` (np. wynik z pracy), oznacz na końcu tej samej linii znacznikiem `<!-- liczba-spoza-wynikow: skąd jest liczba -->`, inaczej bramka liczb (`tools/sprawdz_raporty.py`) ją odrzuci; przykład: `benchmarks/wikitext-2/ORIGINAL.md`. Gdy żaden model, który da się pobrać, nie ma opublikowanego wyniku: „brak” i miejsca, w których szukano (etap B idzie wtedy jako „bez kontroli”) |
| Train policy | `eval_only` / `decon_only` / `train_allowed` (które splity) |
| Decyzja treningowa | |
| Znane rozbieżności | w tym plik zadania lm-eval w `6d2abda4` wobec 0.4.9.1 (METODOLOGIA.md, „Wersja lm-eval”) |
