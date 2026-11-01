# Research: benchmarki modeli

Tu mierzymy modele i budujemy polskie benchmarki. Dziś mierzymy Slayera 1B. Obok niego liczymy pięć modeli
odniesienia (Qwen3.5-0.8B, LFM2.5-1.2B, Bielik-1.5B-v3, LFM3-1.7B, EuroLLM-1.7B) i model kontrolny etapu B. Później
dojdzie każdy następny model z Hugging Face. Rewizje i role modeli opisuje
[`METODOLOGIA.md`](METODOLOGIA.md#modele-kontrolny-i-odniesienia).

Każdy benchmark ma jeden katalog w `benchmarks/`. Kod wspólny dla wielu benchmarków leży w `common/`. Jak powstaje
benchmark (karta oryginału, odtworzenie, kod, wersja polska), opisuje [`METODOLOGIA.md`](METODOLOGIA.md). Kiedy
benchmark jest skończony, mówi sekcja [„Definicja „zrobione””](../README.md#definicja-zrobione) w README repo.
Wszystkie komendy niżej uruchamiasz w katalogu `research/`.

## Układ

| katalog albo plik | co tam jest |
|---|---|
| `METODOLOGIA.md` | jak powstaje benchmark: etapy A–D, karta zbioru, modele kontrolne i odniesienia, przepis, czystość |
| `BENCHMARKI_PL.md` | które benchmarki przetłumaczyć, a które napisać od zera po polsku |
| `benchmarks/<name>/` | kod, dokumentacja i wyniki jednego benchmarku: `README.md`, `ORIGINAL.md`, `REPRODUCTION.md`, `RECIPE.md`; wyniki per model w `results/<model>/` (surowe `.jsonl` lokalnie, `.jsonl.gz` do ~10 MB w repo), raporty zbiorcze w `results/*.json` i `*.md`; wersja polska w osobnym `benchmarks/<name>-pl/` z `POLISH.md` |
| `benchmarks/_template/` | od czego zacząć nowy benchmark |
| `analyses/<name>/` | analiza na wielu testach naraz, te same pliki co benchmark (dziś `answer-format/`: litery A/B/C/D a losowość) |
| `common/` | ładowanie modeli, wspólny format odpowiedzi, lista zadań (`zadania.py`), dane do testów (`tests/data/`), ewaluacja przez lm-eval |
| `tools/` | bramka liczb (`liczby.py`, `sprawdz_raporty.py`) |
| `results/` | `LICZBY.json` i `LICZBY.md`: wszystkie liczby raportów, wygenerowane przez bramkę liczb |
| `tests/` | testy kodu, bez sieci i bez wag |
| `slayer-1b/` | praca nad samym Slayerem 1B poza benchmarkami: `dane/`, `testy_danych_slayer/`, `wygaszanie/`, `tokenizer/`, `lab/`, `paczka_testerzy/` (komendy w ich README uruchamiasz w `research/slayer-1b/`) |

Dziś w repo są trzy benchmarki:

- [`benchmarks/ewok-pl/`](benchmarks/ewok-pl/README.md): EWoK po polsku i angielsku;
- [`benchmarks/blimp/`](benchmarks/blimp/README.md): BLiMP, pełny zbiór;
- [`benchmarks/wikitext-2/`](benchmarks/wikitext-2/README.md): perpleksja WikiText-2, mianownik jak w lm-eval.

Jest też jedna analiza: [`analyses/answer-format/`](analyses/answer-format/README.md). Testy z listy Space (ARC,
MMLU, SIQA, Belebele, MultiBLiMP i inne) liczy kod w `common/`. Opisuje go [`common/README.md`](common/README.md).

## Przygotowanie (raz)

Robisz to raz na komputer. Potrzebujesz dostępu do Hugging Face (HF) i kilku GB wolnego dysku. Kod działa na CPU,
choć wolno, albo na GPU z opcją `--device cuda`.

Przed pierwszym pobraniem:

- Załóż konto na HF i token do odczytu (Settings → Access Tokens na huggingface.co). Komenda `hf auth login` niżej
  poprosi o ten token.
- Model `speakleash/Bielik-1.5B-v3` wymaga zgody na warunki. Zaloguj się na
  [stronie modelu](https://huggingface.co/speakleash/Bielik-1.5B-v3) i zaakceptuj warunki przed pobraniem. Bez tego
  pobranie kończy się błędem 401/403.

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai
cd benchmarks-fabryka-ai/research
python3.12 -m venv .venv-eval
.venv-eval/bin/pip install -r common/requirements.lock.txt pytest
.venv-eval/bin/hf auth login
.venv-eval/bin/python common/pobierz_zbiory.py
.venv-eval/bin/hf download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir models/slayer-1.06
.venv-eval/bin/hf download EleutherAI/pythia-1b-v0 --revision step143000 --local-dir models/pythia-1b-v0
.venv-eval/bin/python common/slayer_lm.py --install
.venv-eval/bin/python tests/test_slayer_eval.py
```

Do benchmarku polskiego albo bez oryginału pobierz też model, który zna polski. Wcześniej zaakceptuj warunki Bielika.

```bash
.venv-eval/bin/hf download speakleash/Bielik-1.5B-v3 --revision 4b25049621bf3952a1fc9314c89773102eda0333 --local-dir models/bielik-1.5b-v3
```

`git clone` pobiera domyślną gałąź repo, czyli `main`. Od niej zakładasz swoją gałąź.

Wszystkie przebiegi liczysz w środowisku z `common/requirements.lock.txt` (lm-eval 0.4.9.1). Czym różni się ono od
lm-eval w Space, opisuje [`METODOLOGIA.md`](METODOLOGIA.md), sekcja „Wersja lm-eval”.
Lock ogranicza Pythona do 3.9–3.12: `numpy==2.0.2` i `scipy==1.13.1` wymagają co najmniej 3.9 i mają gotowe wheele
tylko do 3.12. Sprawdzone na 3.9.25 i 3.12.10. Pilnuje tego pierwsza linia locka,
`--only-binary numpy,scipy`: na 3.14 `pip install` od razu kończy się błędem `No matching distribution found for
numpy==2.0.2`.

`common/slayer_lm.py --install` uruchamiasz raz na venv i checkout. Zapisuje w venv ścieżkę tego `common/`.
Rejestruje model `slayer` tylko pod komendą `lm_eval`, nie pod `python -m lm_eval`.

`EleutherAI/pythia-1b-v0` @ `step143000` to pierwszy model z listy kontrolnej etapu B. Gdy nie ma opublikowanego
wyniku dla Twojego benchmarku, bierzesz następny model z listy (sekcja „Model kontrolny etapu B”). Wagi zostają w
`models/`, poza gitem (`.gitignore`).

## Uruchomienie

Benchmark z własnym katalogiem ma komendy w swoim `RECIPE.md`. Testy z wyborem odpowiedzi, które przeszły test
zgodności z oryginałem, liczy wspólny skrypt `common/hipoteza_formatu.py`. Ten sam kod liczy każdy model:

```bash
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/slayer-1.06 --zadania arc_c_cloze,arc_c_mc --wyjscie analyses/answer-format/results/1.06 --device cpu
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/pythia-1b-v0 --zadania arc_c_cloze,arc_c_mc --wyjscie analyses/answer-format/results/pythia-1b-v0 --device cpu
python analyses/answer-format/analiza_formatu.py --wyniki <dir>
```

- `licz` zapisuje jeden plik `<zadanie>.jsonl` na zadanie. Przerwane liczenie wznawia się od brakujących pytań.
- `analiza_formatu.py` czyta `<dir>/<model>/<zadanie>.jsonl` i zapisuje `<dir>/raport_formatu.json`. Raport podaje
  n, SE, bazy, rozkład odpowiedzi i porównanie modeli. Jeśli venv nie jest aktywny, uruchom skrypt przez
  `.venv-eval/bin/python` zamiast `python`.
- Slayera ładuje tylko `common/slayer_model.py`, bo jego `config.json` nie ma `model_type`. Inne modele ładuje
  transformers. Ten sam forward jest nakładką lm-eval `slayer` (po `--install` z przygotowania):

```bash
.venv-eval/bin/lm_eval --model slayer --model_args pretrained=models/slayer-1.06,dtype=float32 --include_path common/lm_eval_tasks --tasks arc_challenge --samples common/tests/data/arc_panel200.json --num_fewshot 0 --batch_size 1 --device cpu --seed 0,1234,1234,1234
```

Na czym opiera się poprawność nakładki i czym różni się od Space: [`common/RECIPE.md`](common/RECIPE.md). Na Windows komendy są w
`.venv-eval/Scripts/` zamiast `.venv-eval/bin/`.

## Testy kodu

Testy działają bez sieci i bez wag. Każdy kończy się kodem 0:

```bash
.venv-eval/bin/python tests/test_slayer_eval.py
.venv-eval/bin/python tests/test_lm_eval_slayer.py
.venv-eval/bin/python tests/test_testy_danych_slayer.py
.venv-eval/bin/python tests/test_ewok_pl.py
.venv-eval/bin/python tests/test_blimp.py
.venv-eval/bin/python tests/test_blimp_checkpoints.py
.venv-eval/bin/python tests/test_blimp_checkpoints_independent.py
.venv-eval/bin/python tests/test_wikitext_mianownik.py
.venv-eval/bin/python tests/test_liczby_raportow.py
```

Przed PR nie uruchamiasz wszystkich testów. Listę komend ma README repo, sekcja [„Przed PR”](../README.md#przed-pr).
To testy zmienionego benchmarku, `tests/test_liczby_raportow.py` i bramka liczb.

## Bramka liczb

Uruchom ją przed każdą zmianą raportu (README, `benchmarks/`, `analyses/`, `slayer-1b/lab/`, `slayer-1b/wygaszanie/`,
`slayer-1b/testy_danych_slayer/`, strona HTML):

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py [strona.html]
```

Kod różny od 0 znaczy, że raport ma liczbę spoza `results/LICZBY.json` albo ocenę różnicy bez SE i werdyktu. Liczby
benchmarku bramka bierze z `benchmarks/<name>/results/*.json` i sprawdza je w plikach tego benchmarku. Bramka liczb
to co innego niż warunek odtworzenia z etapu B metodologii.

## SE i werdykt

- **SE** (błąd standardowy): dla trafności p na n pytaniach SE = √(p(1−p)/n). Przedział 95% (CI95) to wynik plus minus
  około 2 SE. Space liczy CI95 bootstrapem (10 000 powtórzeń, seed 20261028).
- **Porównanie dwóch wyników:** liczysz różnicę, SE różnicy i z = różnica / SE. Gdy oba modele odpowiadały na te same
  pytania, SE różnicy jest parowane. Inaczej SE różnicy to √(SE₁² + SE₂²), co zawyża szum.
- **Werdykt** (jak w `tools/liczby.py`): |z| ≥ 3 „pewne”, 2–3 „prawdopodobne”, poniżej 2 „szum”. „Szum” znaczy, że
  pomiar nie rozstrzyga. Nie znaczy, że różnicy nie ma.

## Bazy: losowa i większościowa

- **Baza losowa:** wynik zgadywania (1/k przy k opcjach, połowa przy parach zdań).
- **Baza większościowa:** udział najczęstszej poprawnej odpowiedzi, czyli wynik stałej odpowiedzi, np. zawsze „tak”
  w BoolQ. Przy wyborze odpowiedzi liczysz ją po pozycji opcji, bo lm-eval punktuje indeks odpowiedzi. Podajesz
  dokładną wartość ze splitu (np. ze statystyk HF datasets-server), nie zaokrągloną z abstraktu.
- **Udział najczęstszej predykcji:** jaki odsetek odpowiedzi modelu to ta sama opcja. Małe modele w testach z literami
  często wybierają w kółko jedną literę. Wynik podany bez tych liczb wprowadza w błąd.

## Slayer 1B: wyniki testów (30.10.2026)

Slayer 1.06 to checkpoint w trakcie treningu (ok. jednej ósmej, bez wygaszania LR), a porównania niżej śledzą postęp.

- Litery A/B/C/D a losowość. Dlaczego Slayer 1.06 wypada losowo w testach z literami i co widać po treści odpowiedzi: [`analyses/answer-format/`](analyses/answer-format/README.md).
- BLiMP, pełny zbiór, Slayer 1.06 i Pythia-1B: [`benchmarks/blimp/`](benchmarks/blimp/README.md).
- WikiText-2. Po poprawce mianownika byte_ppl z tego repo jest zgodny ze Space: [`benchmarks/wikitext-2/`](benchmarks/wikitext-2/README.md).
- EWoK po polsku i angielsku, Slayer 1.00–1.06, Bielik 1.5B i LFM3 1.7B: [`benchmarks/ewok-pl/`](benchmarks/ewok-pl/README.md).
- Wygaszanie LR obniża loss o 0,047 nat bez zmiany trafności: [`slayer-1b/wygaszanie/README.md`](slayer-1b/wygaszanie/README.md).
