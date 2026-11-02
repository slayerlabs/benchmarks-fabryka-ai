# Wzór nowego benchmarku

Skopiuj ten katalog do `benchmarks/<name>/` (małe litery, myślnik, np. `blimp`) i wypełnij pliki. Procedurę i
znaczenie pól opisuje [`../../METODOLOGIA.md`](../../METODOLOGIA.md). Kiedy benchmark jest skończony, mówi
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

W tym katalogu są wzory plików `ORIGINAL.md`, `REPRODUCTION.md`, `RECIPE.md`, `DATASET.md` i `POLISH.md`. Po
skopiowaniu usuń te, które nie dotyczą Twojego benchmarku.

Analiza na wielu benchmarkach naraz ma te same pliki w `analyses/<name>/`. Gotowe przykłady to
[`../blimp/`](../blimp/README.md), [`../wikitext-2/`](../wikitext-2/README.md) i
[`../../analyses/answer-format/`](../../analyses/answer-format/README.md). `../ewok-pl/` nie jest wzorem wersji
polskiej. Powstał przed metodologią i jest uzupełniany w zadaniu
[#34](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/34).

Dokumenty piszesz po polsku. Nazwy katalogów, plików i kod piszesz po angielsku.
