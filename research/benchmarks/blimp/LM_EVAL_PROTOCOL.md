# BLiMP: kontrola Pythia-1B v0 i zgodność z lm-eval (protokół zapisany przed pomiarem)

Zapisany 2026-11-03, zanim na tej gałęzi policzono jakiekolwiek log-prawdopodobieństwo Pythii-1B v0 albo przebieg
lm-eval `blimp`. Commit z tym plikiem poprzedza commit surowych wyników. Progów nie zmieniamy po zobaczeniu wyników.
Zadanie: [#25](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/25). Reguły: `METODOLOGIA.md`, etapy B i C,
sekcja „Model kontrolny etapu B”.

## Po co

Dotychczasowa kontrola liczyła wagi Pythii v1 (`EleutherAI/pythia-1b` @ `f73d7dc`) naszym kodem i porównywała je z
wartością opublikowaną dla v0. Kodu referencyjnego nie uruchomiono. Ten pomiar liczy model kontrolny z METODOLOGII
kodem referencyjnym (lm-eval) i naszym kodem na tej samej karcie, a do tego sprawdza lm-eval na Slayerze 1.06.

## Co liczymy

| przebieg | model | kod | wynik |
|---|---|---|---|
| P1 | `EleutherAI/pythia-1b-v0` @ `step143000` (sha `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`) | nasz: `common/hipoteza_formatu.py licz --zadania blimp` | `results/pythia-1b-v0/blimp.jsonl.gz` |
| P2 | jak P1 | lm-eval 0.4.9.1, zadanie `blimp`, `--log_samples` | `results/lm-eval/pythia-1b-v0.jsonl.gz` |
| P3 | `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` | lm-eval 0.4.9.1, zadanie `blimp`, model `slayer` z `common/slayer_lm.py`, `--log_samples` | `results/lm-eval/slayer-1.06.jsonl.gz` |
| P4 (informacyjny) | jak P3 | nasz kod, ta sama karta | `results/gpu-check/slayer-1.06.jsonl.gz` |

- Zbiór: wszystkie 67 paradygmatów x 1000 par. Nasz kod czyta `nyu-mll/blimp` @
  `877fba0801ffb7cbd8c39c1ff314a46f053f6036`. lm-eval ładuje `blimp` z HF bez przypiętej rewizji; 03.11 gałąź `main`
  zbioru to ten sam commit `877fba0` (API HF). Na instancji zapisujemy rewizję, którą `datasets` faktycznie pobrał.
- Precyzja float32, `NVIDIA_TF32_OVERRIDE=0`, batch 64 w obu kodach (jak przebieg Slayera w repo), urządzenie
  `cuda`. Seedy lm-eval domyślne: python 0, numpy 1234, torch 1234, fewshot 1234 (0-shot, bez losowania).
- Sprzęt: jedna instancja vast.ai (RTX 4090), wszystkie przebiegi po kolei na tej samej karcie.
- Środowisko: `common/requirements.lock.txt` w venv z `--system-site-packages` na obrazie
  `pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime` (jak PIQA).
- Skrypt instancji: `benchmarks/blimp/lm_eval_instance.sh`. Porównanie: `benchmarks/blimp/lm_eval_compare.py`.

## Decyzje per para

- lm-eval: pole `acc` próbki z `--log_samples` (argmax po `[sentence_good, sentence_bad]`, remis wybiera pierwsze
  zdanie, czyli trafienie).
- Nasz kod: `blimp.trafienie_pary` (remis i 7 par z identycznymi zdaniami liczą się jako trafienie).
- Para jest zgodna, gdy obie decyzje są równe. Zgodność = liczba zgodnych par / 67 000. Pary niezgodne wypisujemy z
  różnicą log-prawdopodobieństw obu kodów.
- Trafność obu kodów: średnia z 67 paradygmatów (= średnia par), SE warstwowe po paradygmatach (`blimp.se_warstwowe`).

## Warunki

| | co | próg | źródło progu |
|---|---|---|---|
| (a) | P2 (lm-eval, Pythia v0) wobec opublikowanej wartości 0,8234328 (średnia 67 `blimp_*` acc, plik Pythii v0 @ `a19eecb`) | \|różnica\| ≤ 2 pkt, a gdy 2 SE > 2 pkt, ≤ 2 SE | METODOLOGIA, warunek odtworzenia (etap B) |
| (b) | P1 wobec P2 (nasz kod wobec lm-eval, Pythia v0) | zgodność decyzji ≥ 99% i \|różnica trafności\| ≤ 1 SE wyniku lm-eval | METODOLOGIA, etap C |
| (c) | `results/1.06/blimp.jsonl.gz` (nasz kod, MPS, wynik w repo) wobec P3 (lm-eval, Slayer 1.06) | jak (b) | METODOLOGIA, etap C |
| (d) | P4 wobec P3 i wobec `results/1.06/blimp.jsonl.gz` | bez progu, tylko opis: rozdziela różnicę kodu od różnicy sprzętu, gdy (c) nie przejdzie | — |

Wartość opublikowaną policzył stary harness, który ocenia zdanie bez spacji na początku; lm-eval 0.4.9.1 ocenia
`" " + zdanie`. Tę różnicę kodu zapisujemy w `REPRODUCTION.md` obok wyniku (a), nie zmieniamy przez nią progu.

Kontrola sensu na pełnych wynikach: trafność 1,000 albo poniżej 0,45 to błąd kodu, nie wynik.

## Gdy warunek nie przejdzie

Nie dobieramy wariantu po wyniku (inny batch, BOS, spacja). Wynik idzie do `REPRODUCTION.md` jako niezgodny.
Przyczynę szukamy na zapisanych log-prawdopodobieństwach (pary niezgodne, długości w tokenach, różnica na zdanie).
Poprawka kodu to osobny commit z opisem; nowy przebieg na karcie tylko wtedy, gdy zapisanych danych nie da się
rozstrzygnąć, i dopiero po zgodzie.

## Test zgodności (etap C)

`tests/test_blimp_zgodnosc.py` z próbką `tests/dane/blimp_zgodnosc.json` (pary o indeksach 0 i 500 z każdego z 67
paradygmatów i 7 par z identycznymi zdaniami, dla Pythii v0 i Slayera 1.06): log-prawdopodobieństwa i decyzje lm-eval
z P2 i P3, nasze z P1 i z pliku Slayera w repo, tokeny wejścia lm-eval. Test działa bez sieci i bez wag.
