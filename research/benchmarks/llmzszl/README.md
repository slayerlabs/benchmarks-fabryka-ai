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

Prompt, ocenę literami i metrykę ustala karta oryginału [`ORIGINAL.md`](ORIGINAL.md) (szablon z pracy, rozdz. 3.2;
lm-eval go nie ma). T37 nie ma jeszcze wpisu w `common/zadania.py` ani w `KATALOGI`: do podpięcia potrzebna jest kopia
YAML-a w `lm_eval_tasks/`, wpis w obu listach, test `tests/test_llmzszl.py` i kontrola z wiersza `+pl` (etap B „bez
kontroli”, bo opublikowane wyniki nie mają rewizji ani ustawień).
