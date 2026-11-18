# COPA: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem
(REPRODUCTION.md)”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md). Wyniki po przebiegu:
`results/central-run/copa/` (katalog powstanie przy przebiegu). Kandydat kontroli i liczby są w
[`ORIGINAL.md`](ORIGINAL.md), odczyt katalogu `results/` lm-eval 2026-11-18.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `v0.4.9.1`, zadanie `lm_eval/tasks/super_glue/copa`: `default.yaml` blob `9e2d1a2f05bc0b9615e27115881b6eadd5e6eb38`, `utils.py` blob `3afc868eb486c47c51b0036ce955502bc377c9c4`. Te same bloby leżą w commicie Space `6d2abda4fd171e68a8789330c4149e37c1ca0bda`. Przebieg bierze `doc_to_text`, `doc_to_target` i `doc_to_choice` z zainstalowanego `utils.py` (`common/zadania.py`, T11, wariant `space`, zadanie `slayer_copa`). Metryka decyzyjna: `acc`. |
| dlaczego ten kod | Karta wskazuje zadanie lm-eval `super_glue/copa`. Autorzy COPA nie publikują kodu zero-shot modelu językowego: systemy Dice i PMI liczą asocjacje między słowami premisy i alternatywy. |
| model kontrolny @ rewizja (z sekcji „Model kontrolny etapu B”) albo „bez kontroli” | `bigscience/bloom-1b7` @ `258ce6c9fe66893de0218d9e6a322947987c8349` (rewizja z daty). Jest w `MODELE` (etykieta `bloom-1b7`), a T11 jest na jego liście w `TESTY_MODELU` (`tools/przebieg_centralny.sh`; METODOLOGIA, „Modele kontrolne etapu B w przebiegu”). Zapas: `facebook/xglm-2.9B` @ `33c659ae27de09c0a54123d3902dac48cbb8592a` (karta, wiersz XGLM-2.9B). |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | nie dotyczy: kontrola jest. Pythia-1B v0 i EuroLLM-1.7B tego wyniku nie mają; lista pozostałych plików `results/` i powodów odrzucenia jest w karcie. |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | nie dotyczy. `slayer_copa` bierze `doc_to_text`, `doc_to_target` i `doc_to_choice` z `super_glue/copa/utils.py`. Porównanie z zadaniem lm-eval 0.4 sprawdzałoby ten sam kod dwa razy. Opublikowany wynik jest ze starego harnessu (jedna spacja, wiersz karty „Znane rozbieżności: jedna spacja”), więc zgodność z tamtym plikiem sprawdza przebieg tego modelu, nie test na sucho. |
| bez kontroli: zgodność według kolumny „test zgodności” typu (np. co najmniej 99% zgodnych decyzji) | nie dotyczy z tego samego powodu. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić (zgodność sprawdza wtedy recenzent PR) | Kod autorów COPA to asocjacje słów (Dice, PMI), nie prompt. Kontrola etapu B bierze opublikowany wynik lm-eval, nie ten kod. |
| dlaczego ten model (które modele z listy nie mają opublikowanego wyniku) | Pythia-1B v0 nie ma `copa`. Karta EuroLLM-1.7B tego testu nie podaje. Z katalogu `results/` @ `afbf8e66` próg wobec b = 0,55 przechodzą pozostali poza BLOOM-560M (z = 1,23). Rewizja z daty, czyli pliki wag niezmienione od pierwszego commitu z wagami do 2023-05-06, wstaje dla BLOOM-1b7 i XGLM-2.9B. Punkt 3 nie ustala kolejności między nimi; BLOOM-1b7 ma już wiersz w `MODELE` (kontrola SQuAD 2.0, RACE i CoQA w tej samej rewizji), więc przebieg dokłada tylko T11. |
| zbiór @ rewizja, split, n | `aps/super_glue` @ `3de24cf8022e94f4ee4b9d55a6f539891524d646`, konfiguracja `copa`, split `validation`, n = 100 |
| wynik (SE): Slayer 1.06 | po przebiegu centralnym. Katalog `results/central-run/copa/` jeszcze nie ma wyników. |
| wartość referencyjna i źródło | `acc` 0,70 (70/100), `acc_stderr` 0,046056618647183814, n = 100. Plik [`results/bloom/bloom-1b7/bloom-1b7_common_sense_reasoning_0-shot.json`](https://github.com/EleutherAI/lm-evaluation-harness/blob/afbf8e6639c86490cc086eb949eac89b55ce58ab/results/bloom/bloom-1b7/bloom-1b7_common_sense_reasoning_0-shot.json) w lm-eval @ `afbf8e6639c86490cc086eb949eac89b55ce58ab`, zadanie `copa` wersji 0, `num_fewshot` 0. <!-- liczba-spoza-wynikow: lm-eval @ afbf8e66, bloom-1b7_common_sense_reasoning_0-shot.json --> |
| różnica | po przebiegu BLOOM-1b7 kodem repo. Do tego czasu nie ma czego odejmować. |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,55. Opublikowane 0,70 przechodzi próg „wynik > b + 2 SE”: z = (0,70 − 0,55) / √(0,70·0,30/100) = 3,27, pewne. Porównanie przebiegu repo z b dopisuje się, gdy są wyniki per pytanie. Dodatkowy przebieg dla typu `mc` nie jest wymagany. <!-- liczba-spoza-wynikow: acc z pliku BLOOM-1b7 @ afbf8e66; b z ORIGINAL.md, wiersz „Bazy: b” --> |
| warunek odtworzenia | \|różnica\| ≤ 0,02; gdy 2 SE różnicy > 0,02, \|różnica\| ≤ 2 SE. SE różnicy policzy przebieg. |
| werdykt | **czeka na przebieg centralny**. Werdykt etapu B powstaje po przebiegu BLOOM-1b7 kodem repo na T11 (METODOLOGIA, „Kto liczy które modele”). Do tego czasu wynik nie idzie do tabeli CodeSOTA ani do meta-oceny. |

Model kontrolny to `bigscience/bloom-1b7` @ `258ce6c9fe66893de0218d9e6a322947987c8349`. Werdykt etapu B czeka, aż przebieg centralny policzy go na T11 kodem repo.
