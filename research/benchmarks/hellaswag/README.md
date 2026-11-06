# HellaSwag (Space T05)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Wybór najbardziej prawdopodobnego dalszego ciągu spośród czterech. Metryka decyzyjna to `acc_norm`.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału.
- [`REPRODUCTION.md`](REPRODUCTION.md): odtworzenie EuroLLM 10-shot i porównanie ze Slayerem.
- [`results/HELLASWAG.md`](results/HELLASWAG.md): liczby wygenerowane z surowych plików.
- [`RECIPE.md`](RECIPE.md): jeden wpis na każdy wynik i smoke test promptów.
- `hellaswag.py`: punktacja, `fetch`, `score`, `report`. `instance.sh`: to samo na GPU z vast.ai.
- `results/raw/`: jedna linia na pytanie, sha256 w `SHA256SUMS`.
- Test: `tests/test_hellaswag.py`, bez sieci i bez wag.

EuroLLM 10-shot, n = 10042: `acc_norm` 0,6074 (SE 0,0049). Karta modelu: 0,6057. Różnica 0,0017, warunek ±0,02 spełniony.

Slayer 1.06, ten sam kod i te same pytania: `acc_norm` 0,3953 (SE 0,0049). Wobec EuroLLM różnica −0,2121, SE 0,0045, z = −46,83, pewne. Baza losowa 0,25. Baza większościowa 0,2573.
