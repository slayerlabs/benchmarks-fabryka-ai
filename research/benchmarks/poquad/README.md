# PoQuAD (open book) (Space T31)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: krótki cytat z kontekstu odpowiadający na pytanie, generacja do 50 tokenów.

- Space: T31, typ `ciagla +pl` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `clarin-pl/poquad` @ `a60f228d836fbbf990d11b4590c60b3e7f2aec2d`, konfiguracja `poquad`, split `validation`, n = 5764.
- Metryka decyzyjna: `levenshtein (jak T30)`.
- Licencja (karta zbioru na przypiętej rewizji): cc-by-4.0.
- Definicja zadania: fork OpenPL `speakleash/lm-evaluation-harness` @ `21d0ea9c`; kopia YAML-a w `lm_eval_tasks/` (nagłówek z commitem źródła), `common/zadania.py` przypina rewizję zbioru.
- Przebieg centralny: podpięty (`T31` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

5-shot. Demonstracje losuje sampler lm-eval (seed 1234) ze splitu few-shot YAML-a; Space bierze je z rozłącznego banku wybranego hashem (METHOD.md), więc demonstracje różnią się od Space, dopóki `common/` nie ma banku Space. Repo z loading scriptem: dane z `refs/convert/parquet` @ `c76799436661006876ca3a2bf2ef2268b2179ac9`, split `validation` + `train` (demonstracje). Generacja jak T30.
