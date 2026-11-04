# Social IQa: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem
(REPRODUCTION.md)” i „Bez kontroli”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md).

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `v0.4.9.1`, zadanie `lm_eval/tasks/siqa/siqa.yaml` (blob `6e387a73a9e005520f426b9d097a10d433279ce2`). Ten sam plik leży w commicie Space `6d2abda4fd171e68a8789330c4149e37c1ca0bda` z tym samym blobem, więc Space i nasze środowisko wołają identyczne `doc_to_text`, `doc_to_choice`, `doc_to_target`, `target_delimiter` i metrykę. |
| dlaczego ten kod | Issue #17 każe liczyć wynik protokołem Space, a Space wskazuje to zadanie (`tasks_50.json`, `definition: lm_eval/tasks/siqa/siqa.yaml`). Praca autorów nie publikuje kodu zero-shot modelu językowego — mierzy modele dostrajane klasyfikatorem na `[CLS]`, więc nie ma czego odtwarzać tym kodem. |
| model kontrolny @ rewizja (z sekcji „Model kontrolny etapu B”) albo „bez kontroli” | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | (1) `EleutherAI/pythia` @ `a19eecb`, plik `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json` — brak zadania `social_iqa` (ma `arc_challenge`, `arc_easy`, `lambada_openai`, `logiqa`, `piqa`, `sciq`, `winogrande`, `wsc`, 67 × `blimp_*`, 57 × `hendrycksTest-*`); (2) karta `utter-project/EuroLLM-1.7B` — Social IQa stoi w tabeli GAPERON bez czystej liczby zero-shot do odtworzenia; (3) Open LLM Leaderboard v2 — test nie występuje na liście (IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro); (4) `results.json` Space @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` — dla T46 nie ma żadnego modelu; (5) tabela 2 pracy — wyniki fine-tuned (GPT, BERT-base, BERT-large), nie zero-shot. |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | nie dotyczy: repo woła wprost zadanie lm-eval, więc nie ma drugiej implementacji do porównania (METODOLOGIA, „Bez kontroli”: „Gdy repo woła ten sam kod co implementacja referencyjna, zgodność niczego nie sprawdza”). Kodu autorów nie da się uruchomić na modelu bez dostrajania — praca trenuje klasyfikator na `[CLS]` na 33 410 przykładach. |
| bez kontroli: zgodność według kolumny „test zgodności” typu (np. co najmniej 99% zgodnych decyzji) | nie dotyczy z tego samego powodu: porównywalibyśmy to samo zadanie lm-eval z samym sobą. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić (zgodność sprawdza wtedy recenzent PR) | kod autorów to trening klasyfikatora na `[CLS]` (BERT/GPT), nie prompt zero-shot; nie da się go uruchomić na modelu przyczynowym bez dostrajania, a dostrajanie zmieniłoby to, co mierzymy. |
| dlaczego ten model (które modele z listy nie mają opublikowanego wyniku) | Pythia-1b-v0 nie ma Social IQa w pliku wyników, EuroLLM-1.7B ma tylko wpis w tabeli GAPERON bez liczby, a pozostałe pozycje listy (Opus/Sonnet, Open LLM Leaderboard) nie zawierają tego testu. Żaden model z listy nie spełnia warunku „opublikowany wynik na tym benchmarku”. |
| zbiór @ rewizja, split, n | `allenai/social_i_qa`, skrypt `main` @ `8835ceb9141d7896d9d968634a9b21ae440e3ec5`, dane z `refs/convert/parquet` (stan gałęzi `537a2ec8ec565adc0b70b70752893e59e024df26`), split `validation`, n = 1954 |
| wynik (SE) | `acc` 0,3895 (SE A 0,0110), n = 1954, CI95 0,3680–0,4115; panel Space 200: `acc` 0,39 (SE A 0,0346), n = 200 |
| wartość referencyjna i źródło | brak |
| różnica | nie dotyczy (brak wartości referencyjnej) |
| kontrola odróżnia działający kod od zepsuty (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,3362 na pełnym splicie (stała odpowiedź: 657 z 1954) i 0,405 na panelu 200 (81 z 200). Pełny split: wynik − b = +4,82 SE, czyli pewnie powyżej b. Panel 200: wynik − b = −0,43 SE, czyli szum — stała odpowiedź bije model. Dodatkowy przebieg dla typu `mc` nie jest wymagany. <!-- liczba-spoza-wynikow: różnice w SE policzone z results/social_iqa.json --> |
| warunek odtworzenia | ±2 pkt w skali metryki; gdy 2 SE > 2 pkt, w granicach 2 SE. Przy braku wartości referencyjnej warunek nie ma czego spełnić. |
| werdykt | **bez kontroli: nierozstrzygnięte** — zgodnie z METODOLOGIA, „Bez kontroli”: repo woła to samo zadanie lm-eval, a żaden model kontrolny nie ma opublikowanego wyniku, więc wynik nie idzie do Space ani do meta-oceny. Wynik modelu zostaje jako pomiar wstępny w tym repo. |

Wynik Slayera 1.06 jest policzony tym samym zadaniem, które wskazuje Space, więc nie ma tu rozbieżności implementacji
do zmierzenia — brakuje tylko modelu z opublikowaną liczbą. Gdy taki model się pojawi (albo ktoś zdejmie warunek
liczby zero-shot), etap B uzupełnia się jednym przebiegiem i wpisem w tym pliku.
