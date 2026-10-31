# Wzór nowego benchmarku

Nowy benchmark dostaje katalog `benchmarki/<nazwa>/` (małe litery, myślnik, np. `ewok-pl`):

```
benchmarki/<nazwa>/
  README.md        co mierzy, metoda, komendy (uruchamiane w research/)
  ORYGINAL.md      karta oryginału (pytania niżej)
  <kod>.py         kod benchmarku; wspólny kod importuje z ../../wspolne
  wyniki/
    <raport>.json  liczby zbiorcze benchmarku; bramka liczb czyta je sama
    <raport>.md
    <model>/       wyniki jednego modelu + PRZEPIS.md
```

Pełna metodologia: https://github.com/LoIlita/test-slayer/blob/main/METODOLOGIA.md

## Karta oryginału (`ORYGINAL.md`)

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

## Przepis (`wyniki/<model>/PRZEPIS.md`)

Przy każdym wyniku leży `PRZEPIS.md`. Z samego przepisu ktoś inny za dwa tygodnie odtwarza ten sam wynik.

```markdown
# Przepis: <benchmark>, <model>

- Commit kodu: <sha>
- Środowisko: <lockfile, np. wspolne/requirements.lock.txt>; transformers <wersja>@<commit>
- Model: <repo HF>@<rewizja>
- Zbiór: <repo HF albo plik>@<rewizja albo sha256>
- Komenda (w research/): <dokładna komenda>
- Seed: <seed>
- Precyzja: <float32 / bfloat16>
- Sprzęt: <CPU / GPU, model>
- Data: <RRRR-MM-DD>
```
