# <Benchmark>: przepis

Jeden wpis na każdy wynik w repo, także na przebieg kontrolny z etapu B. Z samego przepisu ktoś inny za dwa tygodnie
odtwarza ten sam wynik. Czego nie zapisano, wpisz „niezapisane”, nie zgaduj.

## <model>

- Commit kodu: <sha>
- Środowisko: `common/requirements.lock.txt`; transformers <wersja>@<commit, jeśli z gita>; lm-eval <wersja albo commit>
- Model: <repo HF>@<rewizja>
- Zbiór: <repo HF albo plik>@<rewizja albo sha256>
- Komenda (w `research/`): `<dokładna komenda>`
- Seed: <seed>
- Precyzja: <float32 / bfloat16>
- Sprzęt: <CPU / GPU, model>
- Data: <RRRR-MM-DD>
- Wynik: `results/<plik>.json`, klucz <klucz>
