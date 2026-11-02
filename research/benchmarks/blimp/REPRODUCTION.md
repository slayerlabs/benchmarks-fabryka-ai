# BLiMP: odtworzenie (etap B)

**Etapu B nie zrobiono kodem autorów.** W tym repo nie ma przebiegu skryptów jiant z pracy ani przebiegu zadania
lm-eval `blimp` z przypiętego commitu. Jest nasz własny kod oceny na dwóch modelach i dwie kontrole tego kodu,
opisane niżej. Karta oryginału: [`ORIGINAL.md`](ORIGINAL.md).

## Co uruchomiono

| element | wartość |
|---|---|
| kod | nasz kod oceny `common/hipoteza_formatu.py licz --zadania blimp` (odtworzone kodowanie par z lm-eval: pusty kontekst, `" " + sentence`, dokładnie jeden nieoceniany token prefiksu, suma log-prawdopodobieństw, remis liczy się jako trafienie) |
| kod autorów (jiant) | nie uruchomiony |
| lm-eval `blimp` @ `6d2abda4fd171e68a8789330c4149e37c1ca0bda` | nie uruchomiony |
| zbiór | `nyu-mll/blimp` @ `877fba0801ffb7cbd8c39c1ff314a46f053f6036`, wszystkie 67 paradygmatów, n = 67000 |
| model porównawczy (nie kontrola etapu B, ta wymaga `pythia-1b-v0` @ `step143000`) | `EleutherAI/pythia-1b` (v1) @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`, float32 |

## Zakres kontrolny: Pythia-1B v1 wobec opublikowanej wartości v0 (nie kontrola etapu B)

| | wartość |
|---|---|
| nasza Pythia-1B (v1, nasz kod oceny) | 0,8207, n = 67000, SE 0,0013 |
| wartość referencyjna (`pythia-1b-v0` @ `step143000`, stary harness) | 0,8234 (średnia z 67 wartości acc `blimp_*`) |
| różnica | -0,27 pkt |
| reguła | +-2 pkt |
| werdykt | w granicach |

Plik referencyjny: [`EleutherAI/pythia` `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`](https://github.com/EleutherAI/pythia/blob/a19eecb807ec2c79a39ebf18108816e6ffffc1d5/evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json).

**Ograniczenie: to zakres kontrolny, nie etap B.** Wartość referencyjna dotyczy innego modelu i innego kodu
oceny:

1. **Inne wagi.** Wartość referencyjna to `EleutherAI/pythia-1b-v0` @ `step143000` (wagi sprzed ponownego
   treningu Pythii). Nasz przebieg użył `EleutherAI/pythia-1b` (v1) @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2`.
   Katalogi wyników v1 w repo Pythii nie mają BLiMP i nie znaleziono innej opublikowanej wartości BLiMP dla
   `EleutherAI/pythia-1b`.
2. **Inny kod oceny.** Wartość referencyjną policzył stary harness lm-eval, który ocenia zdanie bez spacji na
   początku; nasz kod ocenia `" " + sentence`, tak jak lm-eval w `6d2abda`.

Różnica -0,27 pkt miesza więc model i kod. Wynik w granicach +-2 pkt mówi, że kod oceny nie jest rażąco błędny,
a nie, że odtwarza oryginał. Właściwy etap B wymaga naszego kodu i kodu referencyjnego na tych samych wagach
(`pythia-1b-v0` @ `step143000`), patrz lista zadań w [`README.md`](README.md).

Wyniku referencyjnego z pracy (GPT-2-large, Tabela 3) też nie liczono ponownie.

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
| etap B kodem autorów albo lm-eval na modelu referencyjnym | nie zrobiony |
| nasza Pythia-1B (v1) wobec opublikowanej wartości `pythia-1b-v0` | w granicach +-2 pkt (tylko zakres kontrolny) |
| nasz forward Slayera wobec oficjalnego | 0 zmienionych par z 200 |
| panel Space | nie odtworzony (odczyt z protokołu); odczyt SHA-256 równy |
