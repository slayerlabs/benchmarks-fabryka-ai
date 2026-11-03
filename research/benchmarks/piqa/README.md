# PIQA (Space T06)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Slayer 1.06 na PIQA według protokołu Space, z kontrolą Pythia-1B v0 (zadanie #16). Karta oryginału (etap A) i
etapy B–C idą w #57.

- [`PROTOCOL.md`](PROTOCOL.md): wariant, panel, bazy, próg kontroli i tezy, zacommitowane przed pierwszym surowym
  wynikiem.
- [`results/PIQA.md`](results/PIQA.md): raport wygenerowany z `results/piqa.json`.
- [`RECIPE.md`](RECIPE.md): jeden wpis na każdy wynik.
- [`SPACE_METHOD.md`](SPACE_METHOD.md): wyciąg z METHOD.md Space i wpis T06 z tasks_50.json w użytej rewizji
  Space.
- `piqa.py`: `fetch`, `score`, `report`; `instance.sh`: to samo na GPU z vast.ai.
- `results/raw/`: jedna linia na pytanie (log-prawdopodobieństwo każdej opcji, wybory, poprawna odpowiedź, id
  źródła), sha256 w `SHA256SUMS`.
- Test: `tests/test_piqa.py` (logika na atrapach, niezależne przeliczenie z surowych plików).
