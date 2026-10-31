# Wzór nowego benchmarku

Nowy benchmark dostaje jeden katalog `benchmarks/<nazwa>/` (małe litery, myślnik, np. `ewok-pl`):

```
benchmarks/<nazwa>/
  README.md          co mierzy, wyniki z n, SE i werdyktem, sekcja „Co dodaje metodologia”
  ORIGINAL.md        karta oryginału (etap A, pola niżej)
  REPRODUCTION.md    etap B: wynik referencyjny odtworzony oryginalnym kodem
  RECIPE.md          przepis na każdy wynik (wzór niżej)
  <kod>.py           kod benchmarku; wspólny kod importuje z ../../common
  results/
    <raport>.json    liczby zbiorcze benchmarku; bramka liczb czyta je sama
    <raport>.md
    <model>/         wyniki jednego modelu (pliki per pytanie)
```

Analiza przekrojowa na wielu benchmarkach (nie osobny benchmark) ma te same pliki w `analyses/<nazwa>/`,
a `ORIGINAL.md` opisuje analizę i testy, na których stoi. Przykłady: [`../blimp/`](../blimp/README.md),
[`../wikitext-2/`](../wikitext-2/README.md), [`../../analyses/answer-format/`](../../analyses/answer-format/README.md).

Dokumenty piszemy po polsku, nazwy katalogów, plików i kod po angielsku.

Pełna metodologia: https://github.com/LoIlita/test-slayer/blob/main/METODOLOGIA.md

## Karta oryginału (`ORIGINAL.md`)

Przeczytaj pracę i kod autorów. Wypełnij każde pole; czego nie da się ustalić, wpisz „nieustalone” z tym, gdzie szukałeś.

| pole | co wpisać |
|---|---|
| Co mierzy | umiejętność, jednym zdaniem, słowami autorów |
| Źródła | praca (arXiv/ACL), repo autorów z commitem, karta zbioru na HF z rewizją |
| Dane | split używany do wyników w pracy, n, licencja, czy split testowy ma ukryte odpowiedzi |
| Format zadania | wybór z k opcji, para zdań, uzupełnienie, generacja, perpleksja |
| Prompt | dokładny szablon z pracy albo kodu (separatory, spacje, etykiety odpowiedzi), liczba przykładów w prompcie i skąd są brane |
| Ocena | metryka (acc, acc_norm, exact match, F1, perpleksja, BPB) i sposób jej liczenia: po czym normalizowana jest długość (znaki, bajty, tokeny), jak normalizowany jest tekst odpowiedzi |
| Agregacja | średnia po pytaniach czy po kategoriach/paradygmatach, wagi |
| Wyniki referencyjne | co najmniej jeden opublikowany wynik modelu, który da się pobrać (model, liczba, tabela w pracy albo plik wyników) |
| Znane rozbieżności | czym różnią się popularne implementacje (np. zadanie lm-eval) od kodu autorów, znane błędy w danych, kontaminacja |

## Przepis (`RECIPE.md`)

Każdy wynik ma przepis. Z samego przepisu ktoś inny za dwa tygodnie odtwarza ten sam wynik.
Czego nie zapisano, wpisz „niezapisane”, nie zgaduj.

```markdown
## <benchmark>, <model>

- Commit kodu: <sha>
- Środowisko: <lockfile, np. common/requirements.lock.txt>; transformers <wersja>@<commit>
- Model: <repo HF>@<rewizja>
- Zbiór: <repo HF albo plik>@<rewizja albo sha256>
- Komenda (w research/): <dokładna komenda>
- Seed: <seed>
- Precyzja: <float32 / bfloat16>
- Sprzęt: <CPU / GPU, model>
- Data: <RRRR-MM-DD>
```
