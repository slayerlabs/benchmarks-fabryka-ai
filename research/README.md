# Research: benchmarki modeli

Tu mierzymy modele (dziś Slayer 1B, Pythia-1B, Bielik, LFM3; jutro każdy następny) i budujemy polskie benchmarki.
Każdy benchmark ma jeden katalog w `benchmarki/`, a kod wspólny dla wszystkich leży w `wspolne/`.
Wszystkie komendy niżej uruchamiasz w katalogu `research/`.

## Układ

| katalog | co tam jest |
|---|---|
| `benchmarki/<nazwa>/` | kod, raporty i wyniki jednego benchmarku; wyniki per model w `wyniki/<model>/`, raporty zbiorcze benchmarku w `wyniki/*.json` i `*.md` |
| `benchmarki/_wzor/` | od czego zacząć nowy benchmark: pytania karty oryginału i szablon `PRZEPIS.md` |
| `wspolne/` | ładowanie modeli, wspólny format odpowiedzi, lista zadań (`zadania.py`), dane do testów (`testy/dane/`), ewaluacja przez lm-eval |
| `narzedzia/` | bramka liczb (`liczby.py`, `sprawdz_raporty.py`) |
| `wyniki/` | liczby zbiorcze z wielu testów: `raport_formatu.json` (analiza formatu A/B/C/D na 16 zadaniach), `LICZBY.json` i `LICZBY.md` (wygenerowane przez bramkę) |
| `tests/` | testy kodu, bez sieci i bez wag |
| `slayer-1b/` | praca nad samym Slayerem 1B poza benchmarkami: `dane/`, `testy_danych_slayer/`, `wygaszanie/`, `tokenizer/`, `lab/`, `paczka_testerzy/` (komendy w ich README uruchamiasz w `research/slayer-1b/`) |

Benchmarki dziś: [`benchmarki/ewok-pl/`](benchmarki/ewok-pl/README.md) (EWoK po polsku i angielsku). Testy z listy Space (ARC, MMLU, SIQA, Belebele, MultiBLiMP i inne) liczy `wspolne/`; opis: [`wspolne/README.md`](wspolne/README.md).

## Przygotowanie (raz)

Raz na komputer, z siecią do Hugging Face (HF). Kilka GB dysku; działa na CPU (wolno) albo GPU (`--device cuda`).

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai
cd benchmarks-fabryka-ai/research
python3 -m venv .venv-eval
.venv-eval/bin/pip install -r wspolne/requirements.lock.txt pytest
.venv-eval/bin/python wspolne/pobierz_zbiory.py
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
.venv-eval/bin/python tests/test_liczby_raportow.py
```

## Bramka liczb

Przed każdą zmianą raportu (README, `benchmarki/`, `slayer-1b/lab/`, `slayer-1b/wygaszanie/`, `slayer-1b/testy_danych_slayer/`, strona HTML):

```bash
.venv-eval/bin/python narzedzia/liczby.py && .venv-eval/bin/python narzedzia/sprawdz_raporty.py [strona.html]
```

Kod ≠ 0 = liczba spoza `wyniki/LICZBY.json` albo ocena różnicy bez SE/werdyktu. Liczby benchmarku bramka bierze z `benchmarki/<nazwa>/wyniki/*.json` i sprawdza je w plikach tego benchmarku.

## Slayer 1B: wyniki testów (30.10.2026)

Slayer 1.06 wypada losowo w testach z literami A/B/C/D, bo za często wybiera „A” (83–94% odpowiedzi w testach angielskich, 63% w polskim Belebele), podobnie jak Pythia-1B, więc to cecha skali ~1B, nie brak wiedzy. Liczony po treści odpowiedzi model się uczy (ARC-C acc_norm 0,2176 → 0,2577 od 1.00 do 1.06), a wygaszanie LR obniża loss o 0,047 nat bez zmiany trafności.

### Co dalej

- Zadania dla chętnych (A1–A7 bez GPU, B1–B4 z GPU): [`slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md`](slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md).
- Ślepa paczka do A1 (`paczka_testerzy.zip`, poza repo): sha256 `da0edbd792d2c8074bda39d7232c628fcfbf60933278728afd6db9220c225303`; skąd go wziąć albo jak
  wygenerować dane samemu: [`slayer-1b/paczka_testerzy/INSTRUKCJA.md`](slayer-1b/paczka_testerzy/INSTRUKCJA.md).
