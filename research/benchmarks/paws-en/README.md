# PAWS (EN) (T48)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: czy dwa zdania o prawie tych samych słowach są parafrazą.

- Test T48, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `google-research-datasets/paws-x` @ `4cd8187c404bda33cb1f62b49b001115862acf37`, konfiguracja `en`, split `test`, n = 2000.
- Metryka decyzyjna: `acc`.
- Licencja (karta zbioru na przypiętej rewizji): other.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T48` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Prompt jak w `6d2abda4`: pusty kontekst, separator " ", bez `process_docs`. lm-eval 0.4.9.1 dodaje `process_docs_paraphrases` i `target_delimiter: ""`, co zmienia prompt; dlatego config jest przepisany, nie wzięty z zainstalowanego lm-eval (test `tests/test_zadania_konfiguracja.py`).
