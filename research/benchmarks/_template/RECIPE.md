# <Benchmark>: przepis

Każdy wynik w repo ma tu jeden wpis. Dotyczy to też przebiegu kontrolnego z etapu B. Z samego przepisu ktoś inny za
dwa tygodnie ma odtworzyć ten sam wynik. Czego nie zapisano, wpisz jako „niezapisane”. Nie zgaduj.

## <model>

- Commit kodu: commit z `main`, od którego wychodzi gałąź PR, plus kod z tego PR (hash z gałęzi roboczej znika po spłaszczeniu historii)
- Środowisko: `common/requirements.lock.txt`; transformers <wersja>@<commit, jeśli z gita>; lm-eval <wersja albo commit>
- Model: <repo HF>@<rewizja>
- Zbiór: <repo HF albo plik>@<rewizja albo sha256>
- Komenda (w `research/`): `<dokładna komenda>`
- Seed: <seed>
- Precyzja: <float32 / bfloat16>
- Sprzęt: <CPU / GPU, model>
- Data: <RRRR-MM-DD>
- Wynik: `results/<plik>.json`, klucz <klucz>
