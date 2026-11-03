# BLiMP: odtworzenie (etap B)

**Etap B zrobiono kodem referencyjnym lm-eval na modelu kontrolnym `EleutherAI/pythia-1b-v0` @ `step143000`.**
Skryptów jiant z pracy nie uruchomiono. Protokół z warunkami zapisano przed przebiegiem:
[`LM_EVAL_PROTOCOL.md`](LM_EVAL_PROTOCOL.md). Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).

## Co uruchomiono

| element | wartość |
|---|---|
| nasz kod | `common/hipoteza_formatu.py licz --zadania blimp` (pusty kontekst, `" " + sentence`, dokładnie jeden nieoceniany token prefiksu, suma log-prawdopodobieństw, remis liczy się jako trafienie) |
| kod referencyjny | lm-eval 0.4.9.1 z PyPI, zadanie `blimp`, `--log_samples` (Slayer przez `common/slayer_lm.py`); między `6d2abda` (0.4.8) a 0.4.9.1 pliki zadania `blimp` się nie zmieniły |
| kod autorów (jiant) | nie uruchomiony |
| zbiór | `nyu-mll/blimp` @ `877fba0801ffb7cbd8c39c1ff314a46f053f6036`, wszystkie 67 paradygmatów, n = 67000 |
| model kontrolny | `EleutherAI/pythia-1b-v0` @ `step143000`, float32 |
| model porównawczy raportu | `EleutherAI/pythia-1b` (v1) @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`, float32 |
| sprzęt przebiegów P1-P4 | jedna instancja vast.ai, RTX 4090, CUDA 12.8, torch 2.8.0, TF32 wyłączone, batch 64 ([`RECIPE.md`](RECIPE.md)) |

## Kontrola: Pythia-1B v0, nasz kod, lm-eval i wartość opublikowana

| | trafność |
|---|---|
| wartość opublikowana (`pythia-1b-v0` @ `step143000`, stary harness) | 0,8234 (średnia z 67 wartości acc `blimp_*`) |
| lm-eval 0.4.9.1 (P2) | 0,8244, SE 0,0013, różnica 0,10 pkt |
| nasz kod (P1) | 0,8244, różnica 0,09 pkt |

Plik referencyjny: [`EleutherAI/pythia` `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`](https://github.com/EleutherAI/pythia/blob/a19eecb807ec2c79a39ebf18108816e6ffffc1d5/evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json).

| warunek protokołu | wynik | próg | werdykt |
|---|---|---|---|
| (a) lm-eval na v0 wobec wartości opublikowanej | 0,10 pkt | +-2 pkt | spełniony |
| (b) nasz kod wobec lm-eval, Pythia v0, ta sama decyzja na parze | 66998 z 67000 (99,997%), różnica trafności -0,003 pkt | >= 99% i <= 1 SE | spełniony |
| (c) nasz kod (plik w repo, MPS) wobec lm-eval, Slayer 1.06 (ten sam forward, patrz niżej) | 67000 z 67000, różnica 0 | >= 99% i <= 1 SE | spełniony |
| (d) nasz kod na GPU wobec lm-eval i wobec przebiegu MPS, Slayer 1.06 | 67000 z 67000 w obu | informacyjnie | - |

**(c) nie jest niezależną kontrolą forwardu Slayera.** Przebieg lm-eval P3 idzie przez `common/slayer_lm.py`, który
używa tego samego forwardu `slayer_model.Slayer` i tej samej reguły „zawsze jeden BOS” co nasz kod. Niezależne od
naszego kodu są tam tylko liczenie wyniku w HFLM (podział kontekst/ciąg dalszy, suma log-prawdopodobieństw, decyzja
`acc`) i obiekt tokenizera. (c) mówi więc, że nasze liczenie pary zgadza się z lm-eval na tym samym forwardzie.
Forward wobec oficjalnej klasy GPT z repo Slayera sprawdzają osobno `kontrola_forward.py` (sekcja niżej) i
`tests/test_lm_eval_slayer.py::test_forward_matches_official_reference` (zamrożone logity oficjalnego kodu na małym
losowym checkpoincie, bez wag i sieci). Dla nowej wersji Slayera ze zmienioną architekturą te logity trzeba
przed pomiarem zamrozić ponownie z jej kodu: `tests/make_slayer_reference.py`, pliki `*.py` i `config.json` z repo HF.

Dwie niezgodne pary w (b) to remisy co do szumu liczb zmiennoprzecinkowych: `npi_present_1/445` (lm-eval daje
obu zdaniom tę samą sumę) i `wh_vs_that_no_gap/990`. Największa |różnica| log-prawdopodobieństwa zdania między naszym
kodem a lm-eval to 0,00049 (Pythia) i 0,00014 (Slayer). Wszystkie liczby: `results/lm_eval_agreement.json`; surowe
wyjścia lm-eval z sumami SHA-256: `results/lm-eval/`.

Wartość opublikowaną policzył stary harness, który ocenia zdanie bez spacji na początku; lm-eval 0.4.9.1 i nasz kod
oceniają `" " + sentence`. Różnica 0,10 pkt mieści się w progu mimo tej zmiany.

Wagi v1 (`EleutherAI/pythia-1b`, model porównawczy raportu) dają naszym kodem 0,8207 wobec tej samej wartości
opublikowanej (-0,27 pkt). To tylko informacja: wartość opublikowana dotyczy v0, a katalogi wyników v1 w repo Pythii
nie mają BLiMP.

Wyniku referencyjnego z pracy (GPT-2-large, Tabela 3) nie liczono ponownie.

## Kontrola forwardu Slayera

Oficjalny model Slayera to własny kod w jego repo na HF (`load_slayer.py`); nasz forward w
`common/slayer_model.py` jest jego ponowną implementacją. `benchmarks/blimp/kontrola_forward.py` porównał go z
oficjalnym modelem `load_slayer.py` z repo `SlayerLab/Slayer1B-1.06` (CPU, float32, batch 1) na 400 zdaniach z 200
par panelu Space: średnia |różnica| 0,00018, a maksimum 0,00052-0,00058 w sumie log-prawdopodobieństwa na zdanie,
w 8 przebiegach (1 albo 6 wątków CPU, z ostatnim tokenem albo bez, suma w float32 albo float64); w żadnym
przebiegu żadna z par nie zmieniła wyniku (`results/kontrola_forward.json`). Kalibracji z METHOD.md (logity
równe bit w bit) nie zrobiono.

To sprawdza nasz forward Slayera wobec oficjalnego; nie jest to kontrola kodu oceny BLiMP.

## Kontrola wobec wartości ze Space (panel 200 par)

Space ocenia BLiMP (T01) dla Slayera 1.06 na panelu 200 par: 0,8408 (CI95 0,806-0,876). Panel odbudowano według
METHOD.md, sekcja 3, w obu odczytach identyfikatora źródła:

| identyfikator źródła w haszu | n | Slayer 1.06 | różnica do Space | w CI95 Space |
|---|---:|---:|---:|---|
| `pair_id` (odczyt z protokołu) | 200 | 0,7761 | -0,0647 | nie |
| SHA-256 kanonicznego wiersza | 200 | 0,8408 | 0,0000 | tak |

Werdykt według THRESHOLDS.md: panel nie jest identyczny (nie odtworzony); `source_id_digest` ze Space nie dał się
odtworzyć żadnym sprawdzonym formatem identyfikatora. Odczyt SHA-256 daje wartość Space co do wszystkich
wypisanych cyfr, więc to prawdopodobnie panel Space (wniosek z jednej wartości). Szczegóły:
[`results/BLIMP.md`](results/BLIMP.md), „Agreement with the Space”.

## Werdykt

| kontrola | werdykt |
|---|---|
| etap B: lm-eval na `pythia-1b-v0` wobec wartości opublikowanej (a) | spełniony, 0,10 pkt |
| zgodność naszego kodu z lm-eval na parach, Pythia v0 (b) | spełniona, 99,997% |
| zgodność liczenia pary z lm-eval na tym samym forwardzie Slayera 1.06 (c, bez kontroli forwardu) | spełniona, 100% |
| etap B kodem autorów (jiant) | nie zrobiony |
| nasz forward Slayera wobec oficjalnego | 0 zmienionych par z 200 |
| panel Space | nie odtworzony (odczyt z protokołu); odczyt SHA-256 równy |
