# Research: benchmarki modeli

Tu mierzymy modele i budujemy polskie benchmarki. Dziś mierzymy Slayera 1B. Obok niego liczymy pięć modeli
odniesienia (Qwen3.5-0.8B, LFM2.5-1.2B, Bielik-1.5B-v3, LFM3-1.7B, EuroLLM-1.7B) i model kontrolny etapu B. Później
dojdzie każdy następny model z Hugging Face. Rewizje i role modeli opisuje
[`METODOLOGIA.md`](METODOLOGIA.md#modele-kontrolny-i-odniesienia).

Każdy benchmark ma jeden katalog w `benchmarks/`. Kod wspólny dla wielu benchmarków leży w `common/`. Jak powstaje
benchmark (karta oryginału, odtworzenie, kod, wersja polska), opisuje [`METODOLOGIA.md`](METODOLOGIA.md). Kiedy
benchmark jest skończony, mówi sekcja [„Definicja „zrobione””](METODOLOGIA.md#definicja-zrobione) w METODOLOGII.
Wszystkie komendy niżej uruchamiasz w katalogu `research/`.

## Układ

| katalog albo plik | co tam jest |
|---|---|
| `METODOLOGIA.md` | wspólny rdzeń reguł, tabela typów testów, etapy A–D, modele, przepis, następna wersja Slayera |
| `LEADERBOARD.md` | zasady meta-oceny i rankingu modeli |
| `BENCHMARKI_PL.md` | które benchmarki przetłumaczyć, a które napisać od zera po polsku |
| `benchmarks/<name>/` | kod, dokumentacja i wyniki jednego benchmarku: `README.md`, `ORIGINAL.md`, `REPRODUCTION.md`, `RECIPE.md`; wyniki per model w `results/<model>/` (surowe `.jsonl` lokalnie, `.jsonl.gz` do ~10 MB w repo), raporty zbiorcze w `results/*.json` i `*.md`; wersja polska w osobnym `benchmarks/<name>-pl/` z `POLISH.md` |
| `benchmarks/_template/` | od czego zacząć nowy benchmark |
| `analyses/<name>/` | analiza na wielu testach naraz, te same pliki co benchmark (dziś `answer-format/`: litery A/B/C/D a losowość) |
| `common/` | ładowanie modeli, wspólny format odpowiedzi, lista zadań (`zadania.py`), dane do testów (`tests/data/`), ewaluacja przez lm-eval |
| `tools/` | bramka liczb (`liczby.py`, `sprawdz_raporty.py`), przebieg centralny (`przebieg_centralny.sh`, `kontrola_sensu.py`) |
| `results/` | `LICZBY.json` i `LICZBY.md`: wszystkie liczby raportów, wygenerowane przez bramkę liczb; `central-run/`: wyniki przebiegu centralnego |
| `tests/` | testy kodu, bez sieci i bez wag |
| `slayer-1b/` | praca nad samym Slayerem 1B poza benchmarkami: `dane/` (spis zbiorów: [`REJESTR_DATASETOW.md`](slayer-1b/dane/REJESTR_DATASETOW.md)), `testy_danych_slayer/`, `wygaszanie/`, `tokenizer/`, `lab/`, `paczka_testerzy/` (komendy w ich README uruchamiasz w `research/slayer-1b/`) |

Jest też jedna analiza: [`analyses/answer-format/`](analyses/answer-format/README.md). Testy z listy Space liczy kod
w `common/`, opisany w [`common/README.md`](common/README.md).

## Benchmarki i typy

Typ to wiersz tabeli typów z [METODOLOGII](METODOLOGIA.md#typy-testów); określa skalę, bazy, SE, wiążący werdykt,
kontrolę i test zgodności. Kolumna „przebieg” mówi, czy benchmark liczy przebieg centralny
([METODOLOGIA, „Następna wersja Slayera”](METODOLOGIA.md#następna-wersja-slayera)).

| katalog | Space | typ | grupy | przebieg | wczesny sygnał (informacyjnie) |
|---|---|---|---|---|---|
| [`arc-easy`](benchmarks/arc-easy/ORIGINAL.md) | | `mc-k` | | nie | tak |
| [`blimp`](benchmarks/blimp/README.md) | T01 | `para +klastry` | klastry: paradygmaty; zjawiska informacyjnie | T01 | tak |
| [`blimp-supplement`](benchmarks/blimp-supplement/ORIGINAL.md) | | `para +warstwy` | warstwy: podzadania, średnia bez wag (karta nie pokazuje, że podzadanie to jeden szablon) | nie | nieustalone |
| [`boolq`](benchmarks/boolq/ORIGINAL.md) | T10 | `mc +klastry` | klastry: wspólny ustęp (3270 pytań, 2938 ustępów, 578 pytań dzieli ustęp, do 9 na ustęp) | nie | nieustalone |
| [`ewok`](benchmarks/ewok/README.md) | | `para +klastry` | klastry: szablony; domeny informacyjnie | nie, własny kod | nieustalone |
| [`ewok-pl`](benchmarks/ewok-pl/README.md) | | `para +klastry +pl` | klastry: szablony; domeny informacyjnie | nie, własny kod | nieustalone |
| [`hellaswag`](benchmarks/hellaswag/ORIGINAL.md) | T05 | `mc` | | nie | nieustalone |
| [`lambada`](benchmarks/lambada/ORIGINAL.md) | T17 | `cloze` | | nie | tak |
| [`openbookqa`](benchmarks/openbookqa/ORIGINAL.md) | T08 | `mc` | | nie | nieustalone |
| [`piqa`](benchmarks/piqa/README.md) | T06 | `mc` | | nie, własny kod | tak |
| [`sciq`](benchmarks/sciq/ORIGINAL.md) | T09 | `poz` | | nie | tak |
| [`uncheatable-eval`](benchmarks/uncheatable-eval/ORIGINAL.md) | | `ppl +warstwy` | kategorie, średnia bez wag | nie | nieustalone |
| [`wikitext-2`](benchmarks/wikitext-2/README.md) | T03 | `ppl` | | T03 | nieustalone |
| [`winogrande`](benchmarks/winogrande/README.md) | T07 | `mc +klastry` | klastry: pary bliźniacze | nie | nie |
| [`wsc273`](benchmarks/wsc273/README.md) | T14 | `mc +klastry` | klastry: pary schematów | nie, własny kod | nieustalone |

Wczesny sygnał (kryterium w METODOLOGII) policzono z publicznych plików zero-shot 15 checkpointów
[`pythia-1b-v0`](https://github.com/EleutherAI/pythia/tree/main/evals/pythia-v0/pythia-1b/zero-shot); karta przejmuje
wartość dopiero z własnym przeliczeniem. Plik Pythii nie ma zadań HellaSwag, BoolQ, OpenBookQA, EWoK, BLiMP
Supplement, UncheatableEval ani WikiText-2, a jego `wsc` to inny zbiór niż WSC273, stąd „nieustalone”.

Testy Space (`tasks_50.json`) według typu:

| typ | testy Space |
|---|---|
| `mc` | T05–T08, T10–T16, T18–T21, T40, T44–T46, T48 (T07 i T14 z `+klastry`); polskie (`+pl`): T22–T24, T26, T29, T37 |
| `mc +warstwy` | T32 MMLU (57 przedmiotów) |
| `mc-k` | T02 ARC-Challenge |
| `poz` | T09 SciQ |
| `para` | T01 BLiMP (`+klastry`), T04 MultiBLiMP (`+proc +pl`) |
| `cloze` | T17 LAMBADA |
| `ppl` | T03 WikiText-2 |
| `gen` | T33 GSM8K, T34 MATH (`+warstwy`), T42 NQ, T43 TriviaQA, T47 BBH (`+warstwy`) |
| `ifeval` | T36 IFEval |
| `f1-korpus` | T25 DYK (`+klastry`: 1029 wierszy do 264 pytań), T27 PSC, T28 CBD (wszystkie `+pl`) |
| `ciagla` | T30 PolQA, T31 PoQuAD (Levenshtein, `+pl`), T38 SQuAD2 (`+proc`, b i kontrola na HasAns), T39 DROP, T41 CoQA, T50 ReCoRD |
| `masa` | T35 TruthfulQA MC2 |
| `mcc` | T49 CoLA |

## Przygotowanie (raz)

Do samej karty oryginału (etap A) wystarczą `git clone` i `python3`, bo bramka liczb używa tylko biblioteki
standardowej. Resztę przygotowania robisz od etapu B.

Robisz to raz na komputer. Potrzebujesz Pythona 3.9–3.12, dostępu do Hugging Face (HF) i kilku GB wolnego dysku. Kod
działa na CPU, choć wolno, albo na GPU z opcją `--device cuda`.

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
lm-eval w Space, opisuje [`METODOLOGIA.md`](METODOLOGIA.md), sekcja „Wersja lm-eval”. Na Pythonie nowszym niż 3.12
`pip install` kończy się błędem `No matching distribution found for numpy==2.0.2`.

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
.venv-eval/bin/python tests/test_ewok.py
.venv-eval/bin/python tests/test_ewok_zgodnosc.py
.venv-eval/bin/python tests/test_blimp.py
.venv-eval/bin/python tests/test_blimp_checkpoints.py
.venv-eval/bin/python tests/test_blimp_checkpoints_independent.py
.venv-eval/bin/python tests/test_blimp_zgodnosc.py
.venv-eval/bin/python tests/test_wikitext_mianownik.py
.venv-eval/bin/python -m pytest tests/test_wsc273.py
.venv-eval/bin/python -m pytest tests/test_piqa.py
.venv-eval/bin/python -m pytest tests/test_przebieg_centralny.py
.venv-eval/bin/python tests/test_liczby_raportow.py
.venv-eval/bin/python tests/test_statystyka.py
.venv-eval/bin/python tests/test_straznik_i_kontrola.py
.venv-eval/bin/python tests/test_arc_easy_snr.py
.venv-eval/bin/python tests/test_winogrande.py
.venv-eval/bin/python tests/test_winogrande_przelicz.py
```

Testy BLiMP to `tests/test_blimp*.py` oraz `tests/test_lm_eval_slayer.py`. Testy BLiMP podmieniają model, więc błąd w
`common/slayer_model.py` łapie dopiero `test_lm_eval_slayer.py`: `test_forward_matches_official_reference` łapie
forward (wariant RoPE, skala logitów), a testy `loglikelihood` łapią dodatkowy token w `encode`.

Gdy sprawdzasz, czy test łapie celowo zepsuty kod ewaluacji (mutację), przed każdą mutacją usuwasz katalogi
`__pycache__` albo ustawiasz `PYTHONPYCACHEPREFIX` na katalog tymczasowy, bo stary plik `.pyc` może zostać wczytany
zamiast zmienionego kodu i mutacja fałszywie „przeżywa” (`python -B` tylko nie zapisuje nowych `.pyc`, istniejące
dalej czyta).

Przed PR nie uruchamiasz wszystkich testów. Listę komend ma CONTRIBUTING, sekcja [„Przed PR”](../CONTRIBUTING.md#przed-pr).
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

Werdykt (progi |z| w `tools/liczby.py`), Holm i MDE opisuje
[METODOLOGIA, „Wspólny rdzeń”](METODOLOGIA.md#wspólny-rdzeń), a metodę SE każdego typu testu (analityczne, bootstrap,
warstwowe, po klastrach) kolumna „SE” w [„Typach testów”](METODOLOGIA.md#typy-testów). Space liczy CI95 bootstrapem
(10 000 powtórzeń, seed 20261028).

## Bazy: losowa i większościowa

Bazę losową, stałą odpowiedź (bazę większościową albo jej zamiennik), b i udział najczęstszej predykcji dla każdego
typu testu definiuje [METODOLOGIA, „Typy testów”](METODOLOGIA.md#typy-testów).
