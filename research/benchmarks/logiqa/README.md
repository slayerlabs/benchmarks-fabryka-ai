# LogiQA (T18)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: rozumowanie logiczne z egzaminów, 4 odpowiedzi.

- Test T18, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `EleutherAI/logiqa` @ `c1eee1b2fd0ddc87777e36490f7ad54d0b97d141`, konfiguracja `logiqa`, split `test`, n = 651.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T18` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Repo z loading scriptem: dane z `refs/convert/parquet` @ `fcd80241270118cd52c96dc517dc38804025f3f5`. Prompt z `logiqa/utils_logiqa.py`.

## Pomiar Slayera 1.06 protokołem Space (wyjątek #97)

Wynik LogiQA Slayera 1.06 policzony protokołem Space, wynik wstępny (bez kontroli).

- Protokół: [`PROTOCOL-space.md`](PROTOCOL-space.md)
- Przepis: [`RECIPE.md`](RECIPE.md), sekcja „Pomiar autora (protokół Space, #97)”
- Wynik: [`results/logiqa.json`](results/logiqa.json)
- Surowe wyniki: `results/slayer-1.06/panel200/probki/T18_space.jsonl`, `results/slayer-1.06/pelna/probki/T18_space.jsonl`

Slayer 1.06: acc_norm 0,260 (panel, n=200) / 0,2673 (pełny, n=651). Bazy: losowa 0,25, większościowa 0,278 (181/651, najczęstsza poprawna „d”) — policzona z danych, bo ten przebieg liczył się, gdy wpis `T18` miał `klasy_stale=False` i przebieg tej bazy nie liczył (teraz `True`, liczy). Bez kontroli. Refs #19.
