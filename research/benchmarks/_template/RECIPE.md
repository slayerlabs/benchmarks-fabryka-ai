# <Benchmark>: przepis

Każdy wynik w repo ma tu jeden wpis. Dotyczy to też przebiegu kontrolnego z etapu B. Z samego przepisu ktoś inny za
dwa tygodnie ma odtworzyć ten sam wynik. Czego nie zapisano, wpisz jako „niezapisane”. Nie zgaduj.

## <model>

- Commit kodu: commit, na którym policzono wynik (PR z wynikiem scalasz merge commitem, squash usuwa ten hash z `main`)
- Środowisko: `common/requirements.lock.txt`; transformers <wersja>@<commit, jeśli z gita>; lm-eval <wersja albo commit>
- Model: <repo HF>@<rewizja>
- Zbiór: <repo HF albo plik>@<rewizja albo sha256>
- Komenda (w `research/`): `<dokładna komenda>`
- Seed: <seed>
- Precyzja: <float32 / bfloat16>
- Sprzęt: <CPU / GPU, model>
- Data: <RRRR-MM-DD>
- Smoke test: <id 5–10 przykładów przeczytanych ręcznie przed pełnym przebiegiem, w teście z podtestami z różnych podtestów; przy każdym sprawdzeniu (prompt, opcje, cel, odpowiedź albo logprob, dane wejściowe) co sprawdzono i czy się zgadzało>
- Wynik: `results/<plik>.json`, klucz <klucz>
