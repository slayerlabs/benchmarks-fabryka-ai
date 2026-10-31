# Wzór nowego benchmarku

Skopiuj ten katalog do `benchmarks/<name>/` (małe litery, myślnik, np. `ewok-pl`) i wypełnij pliki. Procedura i
znaczenie pól: [`../../METODOLOGIA.md`](../../METODOLOGIA.md). Kiedy benchmark jest skończony:
[README repo, „Definicja „zrobione””](../../../README.md#definicja-zrobione).

```
benchmarks/<name>/
  README.md          co mierzy, metryka decyzyjna, wyniki z n, SE i werdyktem (ten plik zastąp swoim)
  ORIGINAL.md        etap A: karta oryginału
  REPRODUCTION.md    etap B: wynik referencyjny odtworzony oryginalnym kodem i warunek odtworzenia
  RECIPE.md          przepis na każdy wynik
  DATASET.md         tylko benchmark bez oryginału: karta zbioru zamiast ORIGINAL.md i REPRODUCTION.md
  POLISH.md          tylko wersja polska: etap D
  <code>.py          kod benchmarku; wspólny kod importuje z ../../common
  results/
    <report>.json    liczby zbiorcze; bramka liczb czyta je sama
    <model>/         wyniki jednego modelu per pytanie (lokalnie, nie w repo: .gitignore)
```

Analiza na wielu benchmarkach naraz ma te same pliki w `analyses/<name>/`. Przykłady: [`../blimp/`](../blimp/README.md),
[`../wikitext-2/`](../wikitext-2/README.md), [`../../analyses/answer-format/`](../../analyses/answer-format/README.md).

Dokumenty piszesz po polsku, nazwy katalogów, plików i kod po angielsku.
