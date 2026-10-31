# Wzór nowego benchmarku

Skopiuj ten katalog do `benchmarks/<name>/` (małe litery, myślnik, np. `blimp`) i wypełnij pliki. Procedura i
znaczenie pól: [`../../METODOLOGIA.md`](../../METODOLOGIA.md). Kiedy benchmark jest skończony:
[README repo, „Definicja „zrobione””](../../../README.md#definicja-zrobione).

```
benchmarks/<name>/
  README.md          co mierzy, metryka decyzyjna, wyniki z n, SE i werdyktem (ten plik zastąp swoim)
  ORIGINAL.md        etap A: karta oryginału
  REPRODUCTION.md    etap B: wynik referencyjny odtworzony oryginalnym kodem i warunek odtworzenia
  RECIPE.md          przepis na każdy wynik
  DATASET.md         tylko benchmark bez oryginału: karta zbioru zamiast ORIGINAL.md i REPRODUCTION.md
  <code>.py          kod benchmarku; wspólny kod importuje z ../../common
  results/
    <report>.json    liczby zbiorcze; bramka liczb czyta je sama
    <model>/         wyniki jednego modelu per pytanie: surowe .jsonl lokalnie (.gitignore), .jsonl.gz do ~10 MB w repo

benchmarks/<name>-pl/   wersja polska (etap D), osobny katalog
  README.md, RECIPE.md, kod, results/   jak wyżej
  POLISH.md          etap D: decyzja tłumaczenie czy od zera, mapowanie metody, dwie kontrole; wskazuje ../<name>/
```

Wzory plików w tym katalogu: `ORIGINAL.md`, `REPRODUCTION.md`, `RECIPE.md`, `DATASET.md`, `POLISH.md`; po skopiowaniu
usuń te, które nie dotyczą Twojego benchmarku.

Analiza na wielu benchmarkach naraz ma te same pliki w `analyses/<name>/`. Przykłady: [`../blimp/`](../blimp/README.md),
[`../wikitext-2/`](../wikitext-2/README.md), [`../../analyses/answer-format/`](../../analyses/answer-format/README.md).
`../ewok-pl/` nie jest wzorem wersji polskiej: to katalog sprzed metodologii, uzupełniany w zadaniu
[#34](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/34).

Dokumenty piszesz po polsku, nazwy katalogów, plików i kod po angielsku.
