# PIQA (T06)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Slayer 1.06 na PIQA według [`PROTOCOL.md`](PROTOCOL.md), z kontrolą Pythia-1B v0 (zadanie #16). Etapy A–C: #57.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): odtworzenie (etap B), werdykt: spełniony. Pythia-1B v0 `acc_norm` 0,7095
  wobec opublikowanego 0,7051, `acc` 0,7051 wobec 0,7040, oba w granicach 2 SE (2,13 pkt). <!-- liczba-spoza-wynikow: wartości z results/piqa.json, klucz control; 2,13 pkt to 2 × SE z pliku Pythii v0 -->
- [`PROTOCOL.md`](PROTOCOL.md): wariant, panel, bazy, próg kontroli i tezy, zacommitowane przed pierwszym surowym
  wynikiem.
- [`results/PIQA.md`](results/PIQA.md): raport wygenerowany z `results/piqa.json`.
- [`RECIPE.md`](RECIPE.md): jeden wpis na każdy wynik.
- [`SPACE_METHOD.md`](SPACE_METHOD.md): wyciąg z opisu metody Space i jego wpisu T06, informacyjnie: ustawienia
  testu wyznaczają karta i `PROTOCOL.md`, nie ten plik.
- `piqa.py`: `fetch`, `score`, `report`; `instance.sh`: to samo na GPU z vast.ai.
- `results/raw/`: jedna linia na pytanie (log-prawdopodobieństwo każdej opcji, wybory, poprawna odpowiedź, id
  źródła), sha256 w `SHA256SUMS`.
- Test: `tests/test_piqa.py` (logika na atrapach, niezależne przeliczenie z surowych plików).
