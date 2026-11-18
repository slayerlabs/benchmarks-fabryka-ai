# COPA: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem
(REPRODUCTION.md)” i „Bez kontroli”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md). Wyniki po przebiegu:
`results/central-run/copa/` (katalog powstanie przy przebiegu). Ustalenia poniżej biorą się z
[`ORIGINAL.md`](ORIGINAL.md); źródła karty odczytano 2026-11-05. Ten plik nie jest nowym przeglądem tych źródeł.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `v0.4.9.1`, zadanie `lm_eval/tasks/super_glue/copa`: `default.yaml` blob `9e2d1a2f05bc0b9615e27115881b6eadd5e6eb38`, `utils.py` blob `3afc868eb486c47c51b0036ce955502bc377c9c4`. Te same bloby leżą w commicie Space `6d2abda4fd171e68a8789330c4149e37c1ca0bda`. Przebieg bierze `doc_to_text`, `doc_to_target` i `doc_to_choice` z zainstalowanego `utils.py` (`common/zadania.py`, T11, wariant `space`, zadanie `slayer_copa`). Metryka decyzyjna: `acc`. |
| dlaczego ten kod | Karta wskazuje zadanie lm-eval `super_glue/copa`. Autorzy COPA nie publikują kodu zero-shot modelu językowego: systemy Dice i PMI liczą asocjacje między słowami premisy i alternatywy. |
| model kontrolny @ rewizja (z sekcji „Model kontrolny etapu B”) albo „bez kontroli” | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | Z karty, wiersz „Wyniki referencyjne (odczyt 2026-11-05)”. (1) `EleutherAI/pythia` @ `a19eecb`, `evals/pythia-v0` i `evals/pythia-v1`: żadna ścieżka nie zawiera `copa`, a otwarty plik `pythia-1b-0shot-global_step143000` ma `arc_challenge`, `arc_easy`, `lambada_openai`, `logiqa`, `piqa`, `sciq`, `winogrande`, `wsc` oraz grupy `blimp_*` i `hendrycksTest-*`. (2) Karta `utter-project/EuroLLM-1.7B` @ `c730cd9`: z testów ogólnych tylko ARC-Challenge i HellaSwag. (3) Open LLM Leaderboard v1 i v2: COPA nie ma w zestawie. (4) HELM: COPA tylko w SEA-HELM, nie w angielskim SuperGLUE. (5) `bigscience/evaluation-results` @ `9e59fee55eef474310846d06a0fab238602a32d8`: BLOOM ma `copa` 0-shot, ale promptami promptsource (`best_option`, `cause_effect`, `C1 or C2?`), nie szablonem lm-eval `because`/`therefore`. (6) Karta `allenai/OLMo-1B` @ `344d48f`: tabela podaje `copa` dla kilku modeli około 1B, liczona ewaluacją OLMo, bez promptu, liczby przykładów i wersji kodu. (7) Karty Salamandry: `copa` jest, ale 5-shot (wiersz informacyjny karty), więc nie jest kontrolą przebiegu 0-shot T11. (8) Tabele TinyLlama, MobileLLM i SmolLM2: brak COPA. (9) Praca COPA i SuperGLUE: wyniki systemów asocjacyjnych albo dostrajanych, nie modeli bazowych 0-shot. |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | nie dotyczy: `slayer_copa` dostaje `doc_to_text`, `doc_to_target` i `doc_to_choice` wprost z `super_glue/copa/utils.py`, więc porównanie z zadaniem lm-eval sprawdzałoby ten sam kod dwa razy (METODOLOGIA, „Bez kontroli”). |
| bez kontroli: zgodność według kolumny „test zgodności” typu (np. co najmniej 99% zgodnych decyzji) | nie dotyczy z tego samego powodu. Kolumna typu `mc` wymaga co najmniej 99% zgodnych wyborów, gdy implementacja repo różni się od kodu referencyjnego. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić (zgodność sprawdza wtedy recenzent PR) | Kod autorów to asocjacje słów (Dice, PMI), nie prompt modelu przyczynowego. Tabeli SuperGLUE też nie da się policzyć tym przebiegiem: to BERT dostrajany na `train`, a T11 jest 0-shot na `validation`. |
| dlaczego ten model (które modele z listy nie mają opublikowanego wyniku) | Żaden model z listy „Model kontrolny etapu B” nie ma opublikowanego wyniku 0-shot na splicie `validation` (ostatnie 100 pytań oryginalnego dev, identyfikatory 401–500) w szablonie `because`/`therefore`. Pythia-1b-v0 nie ma `copa` w pliku wyników, karta EuroLLM-1.7B tego testu nie podaje, a pozostałe źródła z wiersza wyżej mają inny prompt, inny shot albo protokół, którego nie da się porównać. |
| zbiór @ rewizja, split, n | `aps/super_glue` @ `3de24cf8022e94f4ee4b9d55a6f539891524d646`, konfiguracja `copa`, split `validation`, n = 100 |
| wynik (SE): Slayer 1.06 | po przebiegu centralnym. Katalog `results/central-run/copa/` jeszcze nie ma wyników (karta, pole „SNR: źródło”). |
| wartość referencyjna i źródło | brak |
| różnica | nie dotyczy (brak wartości referencyjnej) |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,55 (stała odpowiedź: pierwsza opcja, 55 z 100 pytań `validation`). Porównanie wyniku z b + 2 SE wpisuje się po przebiegu centralnym, bo wyników per pytanie jeszcze nie ma. Dodatkowy przebieg dla typu `mc` nie jest wymagany. <!-- liczba-spoza-wynikow: benchmarks/copa/ORIGINAL.md, wiersz „Bazy: b”; parquet copa/validation @ 3de24cf --> |
| warunek odtworzenia | ±2 pkt w skali metryki; gdy 2 SE > 2 pkt, w granicach 2 SE. Przy braku wartości referencyjnej warunek nie ma czego spełnić. |
| werdykt | **bez kontroli: nierozstrzygnięte**. Żaden model z listy nie ma opublikowanego wyniku z tym promptem i splicem, a repo woła kod referencyjny wprost, więc zgodność niczego nie sprawdza. Wynik nie idzie do tabeli CodeSOTA ani do meta-oceny. |

Gdy któreś źródło poda wynik 0-shot modelu z listy razem z promptem i wersją kodu, etap B uzupełnia się wpisem
modelu w `MODELE` (`tools/przebieg_centralny.sh`), przebiegiem i wierszem w tym pliku.
