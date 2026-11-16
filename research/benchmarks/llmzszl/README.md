# LLMzSzŁ (T37)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: wiedzę z polskich egzaminów państwowych (CKE, 2002–2024), pytania jednokrotnego wyboru, 4 odpowiedzi.

- Test T37, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)), 0-shot, metryka `acc`.
- Zbiór: `amu-cai/llmzszl-dataset` @ `9c11d52a415147f1e2c44038a9d4d4155f064e1a`, plik `llmzszl-test.jsonl`, split `test`
  (18 821 pytań).
- Licencja: karta zbioru nie ma tagu licencji. Space dopuszcza tylko wewnętrzną ewaluację i eksport agregatów.
- Kontaminacja: Space notuje znane pokrycie z danymi treningowymi i wymaga audytu po rewizji i ID pytań.
- **Kolumna informacyjna.** Wynik T37 nie wchodzi do werdyktów ani porównań, dopóki nie ma licencji i audytu
  kontaminacji.

## Przebieg centralny

Wpis `T37` w `common/zadania.py` i `T37:llmzszl` w `KATALOGI` (`tools/przebieg_centralny.sh`). Prompt, ocenę literami
i metrykę ustala karta oryginału [`ORIGINAL.md`](ORIGINAL.md) (szablon z pracy, rozdz. 3.2; lm-eval go nie ma).
Definicja zadania to kopia pliku Space T37 z `slayerlabs/Probierz` w
[`lm_eval_tasks/llmzszl/llmzszl.yaml`](lm_eval_tasks/llmzszl/llmzszl.yaml), bajty pod nagłówkiem bez zmian. Wszystkie
18 821 wierszy idą do oceny, także 6 z 5 albo 6 odpowiedziami (prompt pokazuje A–D, złota jest zawsze w A–D; karta,
„Znane rozbieżności: dane”). Test: `tests/test_llmzszl.py`. Brakuje etapu B: „bez kontroli”, kontrola z wiersza `+pl`
(karta, „Kandydat kontroli etapu B”).
