# BLiMP Supplement (T52)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: wiedzę językową spoza BLiMP (dialog, pary pytanie–odpowiedź, inwersja w pytaniach, hiperonimia) na parach minimalnych z BabyLM.

- Test T52, typ `para +warstwy` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: 5 plików `supplement_filtered/*.jsonl` z OSF `ad7qg`, każdy przypięty SHA-256 (OSF nie ma rewizji; sumy w `ORIGINAL.md`, „Dane: pliki”, i w `pliki_osf` wpisu `T52`), czytane jak `json`, split `train`, n = 5218 par. <!-- liczba-spoza-wynikow: ORIGINAL.md, pole „Dane: split w pracy” -->
- Metryka decyzyjna: `acc`, średnia bez wag z 5 podzadań; trafności podzadań pomocnicze.
- Licencja: nieustalone (`ORIGINAL.md`, „Dane: licencja”).
- Definicja zadania: lm-eval tego zadania nie ma; szablon autorów (`_template_yaml` z `babylm/evaluation-pipeline-2024` @ `d680c28`: pusty kontekst, `" " + zdanie`, cel = zdanie poprawne) przepisany w `common/zadania.py`; przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`).
- Przebieg centralny: podpięty (`T52` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).
- Etap B (`REPRODUCTION.md`): jeszcze go nie ma. Kandydat na kontrolę z karty, `babylm/babyllama-10m-2024` @ `073b4258651a7a6268fc48e708cdbad6a20bddab`, nie jest w `MODELE` (`ORIGINAL.md`, „Wyniki referencyjne”).
- Test: `tests/test_blimp_supplement.py`.

Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).
