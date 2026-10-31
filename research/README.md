# Research: benchmarki modeli

Tu mierzymy modele (dziś mierzony Slayer 1B, pięć modeli odniesienia: Qwen3.5-0.8B, LFM2.5-1.2B, Bielik-1.5B-v3,
LFM3-1.7B, EuroLLM-1.7B, oraz model kontrolny etapu B; jutro każdy następny model z Hugging Face) i budujemy polskie
benchmarki. Rewizje i role modeli: [`METODOLOGIA.md`](METODOLOGIA.md#modele-kontrolny-i-odniesienia).
Każdy benchmark ma jeden katalog w `benchmarks/`, a kod wspólny dla wielu benchmarków leży w `common/`.
Jak powstaje benchmark (karta oryginału, odtworzenie, kod, wersja polska): [`METODOLOGIA.md`](METODOLOGIA.md).
Kiedy jest skończony: [„Definicja „zrobione””](../README.md#definicja-zrobione) w README repo.
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

Benchmarki dziś: [`benchmarks/ewok-pl/`](benchmarks/ewok-pl/README.md) (EWoK po polsku i angielsku),
[`benchmarks/blimp/`](benchmarks/blimp/README.md) (BLiMP, pełny zbiór), [`benchmarks/wikitext-2/`](benchmarks/wikitext-2/README.md)
(perpleksja WikiText-2, mianownik jak w lm-eval). Analizy: [`analyses/answer-format/`](analyses/answer-format/README.md).
Testy z listy Space (ARC, MMLU, SIQA, Belebele, MultiBLiMP i inne) liczy `common/`; opis: [`common/README.md`](common/README.md).

## Przygotowanie (raz)

Raz na komputer, z siecią do Hugging Face (HF). Kilka GB dysku; działa na CPU (wolno) albo GPU (`--device cuda`).

Przed pierwszym pobraniem:

- załóż konto na HF i token do odczytu (Settings → Access Tokens na huggingface.co); `hf auth login` niżej pyta o ten
  token;
- `speakleash/Bielik-1.5B-v3` jest za bramką zgody: zaloguj się na
  [stronie modelu](https://huggingface.co/speakleash/Bielik-1.5B-v3) i zaakceptuj warunki, zanim go pobierzesz
  (bez tego pobranie kończy się błędem 401/403).

```bash
git clone https://github.com/slayerlabs/benchmarks-fabryka-ai
cd benchmarks-fabryka-ai/research
python3 -m venv .venv-eval
.venv-eval/bin/pip install -r common/requirements.lock.txt pytest
.venv-eval/bin/hf auth login
.venv-eval/bin/python common/pobierz_zbiory.py
.venv-eval/bin/hf download SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --local-dir models/slayer-1.06
.venv-eval/bin/hf download EleutherAI/pythia-1b-v0 --revision step143000 --local-dir models/pythia-1b-v0
.venv-eval/bin/python tests/test_slayer_eval.py
```

Do benchmarku polskiego albo bez oryginału pobierz też model, który zna polski (po akceptacji warunków Bielika):

```bash
.venv-eval/bin/hf download speakleash/Bielik-1.5B-v3 --revision 4b25049621bf3952a1fc9314c89773102eda0333 --local-dir models/bielik-1.5b-v3
```

`git clone` bierze gałąź `main`. Środowisko z `common/requirements.lock.txt` (lm-eval 0.4.9.1) obowiązuje we wszystkich
przebiegach; czym różni się od lm-eval w Space: [`METODOLOGIA.md`](METODOLOGIA.md), sekcja „Wersja lm-eval”.
`EleutherAI/pythia-1b-v0` @ `step143000` to pierwszy model z listy kontrolnej etapu B; gdy nie ma opublikowanego
wyniku dla Twojego benchmarku, bierzesz następny z listy (sekcja „Model kontrolny etapu B”). Wagi zostają w `models/`,
poza gitem (`.gitignore`).

## Uruchomienie

Benchmark z własnym katalogiem ma komendy w swoim `RECIPE.md`. Testy z wyborem odpowiedzi, które przeszły test zgodności
z oryginałem, liczy wspólny `common/hipoteza_formatu.py`; ten sam kod liczy każdy model:

```bash
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/slayer-1.06 --zadania arc_c_cloze,arc_c_mc --wyjscie analyses/answer-format/results/1.06 --device cpu
.venv-eval/bin/python common/hipoteza_formatu.py licz --model models/pythia-1b-v0 --zadania arc_c_cloze,arc_c_mc --wyjscie analyses/answer-format/results/pythia-1b-v0 --device cpu
python analyses/answer-format/analiza_formatu.py --wyniki <dir>
```

- `licz` zapisuje plik `<zadanie>.jsonl` na zadanie; przerwane liczenie wznawia się od brakujących pytań.
- `analiza_formatu.py` czyta `<dir>/<model>/<zadanie>.jsonl` i zapisuje `<dir>/raport_formatu.json`: n, SE, bazy,
  rozkład odpowiedzi i porównanie modeli (z `.venv-eval/bin/python` zamiast `python`, jeśli venv nie jest aktywny).
- Slayera ładuje tylko `common/slayer_model.py` (jego `config.json` nie ma `model_type`); inne modele ładuje
  transformers.

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

Przed PR nie uruchamiasz wszystkich: lista komend jest w README repo, sekcja
[„Przed PR”](../README.md#przed-pr) (testy zmienionego benchmarku, `tests/test_liczby_raportow.py` i bramka liczb).

## Bramka liczb

Przed każdą zmianą raportu (README, `benchmarks/`, `analyses/`, `slayer-1b/lab/`, `slayer-1b/wygaszanie/`,
`slayer-1b/testy_danych_slayer/`, strona HTML):

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py [strona.html]
```

Kod ≠ 0 = liczba spoza `results/LICZBY.json` albo ocena różnicy bez SE i werdyktu. Liczby benchmarku bramka bierze z
`benchmarks/<name>/results/*.json` i sprawdza je w plikach tego benchmarku. Bramka liczb to co innego niż warunek
odtworzenia z etapu B metodologii.

## SE i werdykt

- **SE** (błąd standardowy): dla trafności p na n pytaniach SE = √(p(1−p)/n). Przedział 95% (CI95) to wynik plus minus
  około 2 SE. Space liczy CI95 bootstrapem (10 000 powtórzeń, seed 20261028).
- **Porównanie dwóch wyników:** różnica, SE różnicy (parowane, gdy oba modele odpowiadały na te same pytania; inaczej
  √(SE₁² + SE₂²), co zawyża szum), z = różnica / SE.
- **Werdykt** (jak w `tools/liczby.py`): |z| ≥ 3 „pewne”, 2–3 „prawdopodobne”, poniżej 2 „szum”. „Szum” znaczy, że
  pomiar nie rozstrzyga, a nie że różnicy nie ma.

## Bazy: losowa i większościowa

- **Baza losowa:** wynik zgadywania (1/k przy k opcjach, połowa przy parach zdań).
- **Baza większościowa:** wynik stałej odpowiedzi „najczęstsza klasa”, np. zawsze „tak” w BoolQ; tylko dla testów o
  stałym zbiorze klas.
- **Udział najczęstszej predykcji:** jaki odsetek odpowiedzi modelu to ta sama opcja. Małe modele w testach z literami
  często wybierają jedną literę, więc wynik bez tych liczb myli.

## Slayer 1B: wyniki testów (30.10.2026)

- Litery A/B/C/D a losowość (dlaczego Slayer 1.06 wypada losowo w testach z literami i co widać po treści odpowiedzi): [`analyses/answer-format/`](analyses/answer-format/README.md).
- BLiMP, pełny zbiór, Slayer 1.06 i Pythia-1B: [`benchmarks/blimp/`](benchmarks/blimp/README.md).
- WikiText-2: byte_ppl z tego repo zgodny ze Space po poprawce mianownika: [`benchmarks/wikitext-2/`](benchmarks/wikitext-2/README.md).
- Wygaszanie LR obniża loss o 0,047 nat bez zmiany trafności: [`slayer-1b/wygaszanie/README.md`](slayer-1b/wygaszanie/README.md).

### Co dalej

- Zadania dla chętnych (A1–A7 bez GPU, B1–B4 z GPU): [`slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md`](slayer-1b/lab/DLA_ARKA_I_CHETNYCH.md).
- Ślepa paczka do A1 (`paczka_testerzy.zip`, poza repo): sha256 `da0edbd792d2c8074bda39d7232c628fcfbf60933278728afd6db9220c225303`; skąd go wziąć albo jak
  wygenerować dane samemu: [`slayer-1b/paczka_testerzy/INSTRUKCJA.md`](slayer-1b/paczka_testerzy/INSTRUKCJA.md).
