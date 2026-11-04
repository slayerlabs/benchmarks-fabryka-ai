# LLMzSzŁ (Space T37)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: wiedzę z polskich egzaminów państwowych (CKE, 2002–2024), pytania jednokrotnego wyboru, 4 odpowiedzi.

- Space: T37, typ `mc +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)), 0-shot, metryka `acc`.
- Zbiór: `amu-cai/llmzszl-dataset` @ `9c11d52a415147f1e2c44038a9d4d4155f064e1a`, plik `llmzszl-test.jsonl`.
- Licencja: karta zbioru nie ma tagu licencji. Space dopuszcza tylko wewnętrzną ewaluację i eksport agregatów.
- Kontaminacja: Space notuje znane pokrycie z danymi treningowymi i wymaga audytu po rewizji i ID pytań.
- **Kolumna informacyjna.** Wynik T37 nie wchodzi do werdyktów ani porównań, dopóki nie ma licencji i audytu
  kontaminacji.

## Przebieg centralny: niepodpięty

Space liczy T37 z własnego pliku `tasks/llmzszl.yaml` (`entrypoint_kind: local_yaml`, `instrument: n05_static_yaml`
w `tasks_50.json`). Tego pliku Space nie publikuje, a `METHOD.md` i `tasks_50.json` nie podają promptu, separatora,
formatu odpowiedzi (litera czy treść) ani pól zbioru użytych w szablonie. Odtworzony YAML byłby nowym protokołem, nie
protokołem Space, więc T37 nie ma wpisu w `common/zadania.py` ani w `KATALOGI`.

Do podpięcia potrzebny jest plik `tasks/llmzszl.yaml` ze Space (albo jego treść) na rewizji, którą Space liczył.
