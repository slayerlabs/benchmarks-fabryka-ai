# LLMzSzŁ (T37)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: wiedzę z polskich egzaminów państwowych (CKE, 2002–2024), pytania jednokrotnego wyboru, 4 odpowiedzi.

- Test T37, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)), 0-shot, metryka `acc`.
- Zbiór: `amu-cai/llmzszl-dataset` @ `9c11d52a415147f1e2c44038a9d4d4155f064e1a`, plik `llmzszl-test.jsonl`.
- Licencja: karta zbioru nie ma tagu licencji. Space dopuszcza tylko wewnętrzną ewaluację i eksport agregatów.
- Kontaminacja: Space notuje znane pokrycie z danymi treningowymi i wymaga audytu po rewizji i ID pytań.
- **Kolumna informacyjna.** Wynik T37 nie wchodzi do werdyktów ani porównań, dopóki nie ma licencji i audytu
  kontaminacji.

## Przebieg centralny: niepodpięty

T37 nie ma promptu: ani zbiór, ani lm-eval nie dają szablonu z separatorem, formatem odpowiedzi (litera czy treść) i
polami zbioru, więc T37 nie ma wpisu w `common/zadania.py` ani w `KATALOGI`.

Do podpięcia potrzebna jest karta benchmarku (`DATASET.md` albo `POLISH.md`) z własnym protokołem: prompt, separator,
format odpowiedzi i metryka.
