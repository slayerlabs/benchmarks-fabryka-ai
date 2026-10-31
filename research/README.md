# Research: benchmarki modeli

Tu mierzymy modele (dziś Slayer 1B, Pythia-1B, Bielik, LFM3; jutro każdy następny) i budujemy polskie benchmarki.
Każdy benchmark ma jeden katalog w `benchmarks/`, a kod wspólny dla wszystkich leży w `common/`.
Wszystkie komendy niżej uruchamiasz w katalogu `research/`.

## Układ

| katalog | co tam jest |
|---|---|
| `benchmarks/<nazwa>/` | kod, dokumentacja i wyniki jednego benchmarku: `README.md`, karta oryginału `ORIGINAL.md`, odtworzenie `REPRODUCTION.md`, przepis `RECIPE.md`; wyniki per model w `results/<model>/`, raporty zbiorcze w `results/*.json` i `*.md` |
| `benchmarks/_template/` | od czego zacząć nowy benchmark: pola karty oryginału i szablon `RECIPE.md` |
| `analyses/<nazwa>/` | analiza przekrojowa na wielu testach, te same pliki co benchmark (dziś `answer-format/`: litery A/B/C/D a losowość) |
| `common/` | ładowanie modeli, wspólny format odpowiedzi, lista zadań (`zadania.py`), dane do testów (`tests/data/`), ewaluacja przez lm-eval |
| `tools/` | bramka liczb (`liczby.py`, `sprawdz_raporty.py`) |
| `results/` | `LICZBY.json` i `LICZBY.md`: wszystkie liczby raportów, wygenerowane przez bramkę |
| `tests/` | testy kodu, bez sieci i bez wag |
| `slayer-1b/` | praca nad samym Slayerem 1B poza benchmarkami: `dane/`, `testy_danych_slayer/`, `wygaszanie/`, `tokenizer/`, `lab/`, `paczka_testerzy/` (komendy w ich README uruchamiasz w `research/slayer-1b/`) |

Benchmarki dziś: [`benchmarks/ewok-pl/`](benchmarks/ewok-pl/README.md) (EWoK po polsku i angielsku), [`benchmarks/blimp/`](benchmarks/blimp/README.md) (BLiMP, pełny zbiór), [`benchmarks/wikitext-2/`](benchmarks/wikitext-2/README.md) (perpleksja WikiText-2, mianownik jak w lm-eval). Analizy: [`analyses/answer-format/`](analyses/answer-format/README.md). Testy z listy Space (ARC, MMLU, SIQA, Belebele, MultiBLiMP i inne) liczy `common/`; opis: [`common/README.md`](common/README.md).

## Przygotowanie (raz)

Raz na komputer, z siecią do Hugging Face (HF). Kilka GB dysku; działa na CPU (wolno) albo GPU (`--device cuda`).

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai
cd benchmarks-fabryka-ai/research
python3 -m venv .venv-eval
.venv-eval/bin/pip install -r common/requirements.lock.txt pytest
.venv-eval/bin/python common/pobierz_zbiory.py
.venv-eval/bin/huggingface-cli download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir models/slayer-1.06
.venv-eval/bin/huggingface-cli download EleutherAI/pythia-1b --revision f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2 --local-dir models/pythia-1b
.venv-eval/bin/python tests/test_slayer_eval.py
```

## Testy kodu

Bez sieci i bez wag, każdy kończy się kodem 0:

```bash
.venv-eval/bin/python tests/test_slayer_eval.py
.venv-eval/bin/python tests/test_testy_danych_slayer.py
.venv-eval/bin/python tests/test_ewok_pl.py
.venv-eval/bin/python tests/test_blimp.py
.venv-eval/bin/python tests/test_wikitext_mianownik.py
.venv-eval/bin/python tests/test_liczby_raportow.py
```

## Bramka liczb

Przed każdą zmianą raportu (README, `benchmarks/`, `analyses/`, `slayer-1b/lab/`, `slayer-1b/wygaszanie/`, `slayer-1b/testy_danych_slayer/`, strona HTML):

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py [strona.html]
```

Kod ≠ 0 = liczba spoza `results/LICZBY.json` albo ocena różnicy bez SE/werdyktu. Liczby benchmarku bramka bierze z `benchmarks/<nazwa>/results/*.json` i sprawdza je w plikach tego benchmarku.

## Slayer 1B: wyniki testów (30.10.2026)

- Litery A/B/C/D a losowość (dlaczego Slayer 1.06 wypada losowo w testach z literami i co widać po treści odpowiedzi): [`analyses/answer-format/`](analyses/answer-format/README.md).
- BLiMP, pełny zbiór, Slayer 1.06 i Pythia-1B: [`benchmarks/blimp/`](benchmarks/blimp/README.md).
- WikiText-2: nasz byte_ppl zgodny ze Space po poprawce mianownika: [`benchmarks/wikitext-2/`](benchmarks/wikitext-2/README.md).
- Wygaszanie LR obniża loss o 0,047 nat bez zmiany trafności: [`slayer-1b/wygaszanie/README.md`](slayer-1b/wygaszanie/README.md).

### Co dalej

- Zadania dla chętnych (A1–A7 bez GPU, B1–B4 z GPU): [`slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md`](slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md).
- Ślepa paczka do A1 (`paczka_testerzy.zip`, poza repo): sha256 `da0edbd792d2c8074bda39d7232c628fcfbf60933278728afd6db9220c225303`; skąd go wziąć albo jak
  wygenerować dane samemu: [`slayer-1b/paczka_testerzy/INSTRUKCJA.md`](slayer-1b/paczka_testerzy/INSTRUKCJA.md).
