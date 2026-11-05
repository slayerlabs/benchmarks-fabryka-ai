# Social IQa: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem
(REPRODUCTION.md)” i „Bez kontroli”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md). Wyniki:
[`results/central-run/social-iqa/`](../../results/central-run/social-iqa/).

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `v0.4.9.1`, zadanie `lm_eval/tasks/siqa/siqa.yaml` (blob `6e387a73a9e005520f426b9d097a10d433279ce2`). Ten sam plik leży w commicie Space `6d2abda4fd171e68a8789330c4149e37c1ca0bda` z tym samym blobem. Repo przepisuje z niego `doc_to_text`, `doc_to_choice`, `doc_to_target`, `target_delimiter` i metrykę do zadania `slayer_social_iqa` (`common/zadania.py`, T46, wariant `space`); zmienione jest tylko źródło danych (konwersja parquet zamiast skryptu ładującego). |
| dlaczego ten kod | Karta (`ORIGINAL.md`) wskazuje zadanie lm-eval `social_iqa`. Praca autorów nie publikuje kodu zero-shot modelu językowego — mierzy modele dostrajane klasyfikatorem na `[CLS]`, więc nie ma czego odtwarzać tym kodem. |
| model kontrolny @ rewizja (z sekcji „Model kontrolny etapu B”) albo „bez kontroli” | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | (1) `EleutherAI/pythia` @ `a19eecb`, plik `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json` — brak zadania `social_iqa` (ma `arc_challenge`, `arc_easy`, `lambada_openai`, `logiqa`, `piqa`, `sciq`, `winogrande`, `wsc`, 67 × `blimp_*`, 57 × `hendrycksTest-*`); żaden inny plik `evals/` w tym commicie nie ma `siqa` ani `social` w ścieżce; (2) karta `utter-project/EuroLLM-1.7B` — z testów ogólnych podaje tylko ARC Challenge i HellaSwag; (3) Open LLM Leaderboard v2 — test nie występuje na liście (IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro); (4) `results.json` Space @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` — T46 ma dwa wiersze, `LiquidAI/LFM2.5-1.2B-Base` i `SlayerLab/Slayer1B-1.06`, oba `state: not_run`, `value` i `ci95` puste; (5) tabela 2 pracy — wyniki fine-tuned (GPT, BERT-base, BERT-large), nie zero-shot. |
| bez kontroli: opublikowane wyniki innych modeli (niepoliczone) | MobileLLM ([arXiv:2402.14905v2](https://arxiv.org/abs/2402.14905v2), tabela 8, odczyt 2026-11-05): SIQA zero-shot dla modeli około 1 mld, m.in. Pythia-1B 43,3, TinyLlama-1.1B 43,9, OPT-1.3B 44,7. Praca nie podaje rewizji modelu, promptu, metryki ani wersji kodu, więc wynik nie spełnia punktu 3 listy i nie jest kontrolą; jest tylko rzędem wielkości dla modeli tej skali. <!-- liczba-spoza-wynikow: arXiv:2402.14905v2, tabela 8 --> |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | nie dotyczy: `slayer_social_iqa` ma prompt, opcje, cel i metrykę przepisane bez zmian z `siqa.yaml`, więc porównanie z zadaniem lm-eval sprawdzałoby to samo dwa razy (METODOLOGIA, „Bez kontroli”: „Gdy repo woła ten sam kod co implementacja referencyjna, zgodność niczego nie sprawdza”). Kodu autorów nie da się uruchomić na modelu bez dostrajania — praca trenuje klasyfikator na `[CLS]` na 33 410 przykładach. |
| bez kontroli: zgodność według kolumny „test zgodności” typu (np. co najmniej 99% zgodnych decyzji) | nie dotyczy z tego samego powodu. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić (zgodność sprawdza wtedy recenzent PR) | kod autorów to trening klasyfikatora na `[CLS]` (BERT/GPT), nie prompt zero-shot; nie da się go uruchomić na modelu przyczynowym bez dostrajania, a dostrajanie zmieniłoby to, co mierzymy. |
| dlaczego ten model (które modele z listy nie mają opublikowanego wyniku) | Pythia-1b-v0 nie ma Social IQa w pliku wyników, karta EuroLLM-1.7B nie podaje tego testu, a z punktu 3 listy żadne sprawdzone źródło nie podaje wyniku z ustawieniami (MobileLLM bez promptu i wersji kodu, Open LLM Leaderboard v2 bez testu). |
| zbiór @ rewizja, split, n | `allenai/social_i_qa`, skrypt `main` @ `8835ceb9141d7896d9d968634a9b21ae440e3ec5`, dane z `refs/convert/parquet` (stan gałęzi `537a2ec8ec565adc0b70b70752893e59e024df26`), split `validation`, n = 1954 |
| wynik (SE): Slayer 1.06 | `acc` 0,3895 (SE A 0,0110), n = 1954, przebieg centralny <!-- liczba-spoza-wynikow: results/central-run/social-iqa/slayer1b-1.06/results_rozszerzone.json --> |
| wartość referencyjna i źródło | brak |
| różnica | nie dotyczy (brak wartości referencyjnej) |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,3362 (stała odpowiedź „zawsze trzecia opcja”: 657 z 1954). Bez modelu kontrolnego; wszystkie pięć modeli przebiegu centralnego przechodzi b + 2 SE (różnica parowana po pytaniach, tabela w [`README.md`](README.md)), Slayer 1.06 z z = 3,47. Żaden model nie wybiera jednej opcji częściej niż w 35% pytań. Dodatkowy przebieg dla typu `mc` nie jest wymagany. <!-- liczba-spoza-wynikow: rozkład celu i predykcji z probki/ przebiegu centralnego --> |
| warunek odtworzenia | ±2 pkt w skali metryki; gdy 2 SE > 2 pkt, w granicach 2 SE. Przy braku wartości referencyjnej warunek nie ma czego spełnić. |
| werdykt | **bez kontroli: nierozstrzygnięte** — zgodnie z METODOLOGIA, „Bez kontroli”: żaden model z listy nie ma opublikowanego wyniku z ustawieniami, więc wynik nie idzie do tabeli CodeSOTA ani do meta-oceny. |

Gdy któreś źródło poda wynik zero-shot modelu z listy razem z promptem i wersją kodu, etap B uzupełnia się wpisem
modelu w `MODELE` (`tools/przebieg_centralny.sh`), przebiegiem i wierszem w tym pliku.

Pomiar wstępny autora PR (RTX 5060 Ti, przed przebiegiem centralnym) dał na pełnym splicie te same decyzje we
wszystkich 1954 pytaniach co przebieg centralny. Opis: [`RECIPE.md`](RECIPE.md), „Pomiar wstępny autora”. <!-- liczba-spoza-wynikow: porównanie results/slayer-1.06/social_iqa_full.jsonl.gz z probki/ przebiegu centralnego -->
