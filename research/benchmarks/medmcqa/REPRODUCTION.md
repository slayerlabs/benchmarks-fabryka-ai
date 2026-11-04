# MedMCQA: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Wyniki: [`results/central-run/medmcqa/`](../../results/central-run/medmcqa/). Odczyt źródeł 2026-11-04.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1` (`common/requirements.lock.txt`), zadanie `medmcqa`: repo bierze `doc_to_text` z `utils_medmcqa.py` tej wersji, opcje `A`–`D` i cel `cop` jak `medmcqa.yaml` (`common/zadania.py`, T45, wariant `space`); zmienione tylko źródło danych (przypięta rewizja HF) |
| dlaczego ten kod | Autorzy nie publikują kodu 0-shot dla modelu językowego. Karta (`ORIGINAL.md`) wskazuje zadanie lm-eval `lm_eval/tasks/medmcqa/medmcqa.yaml`, a katalog zadania ma te same bloby w `6d2abda4`, `v0.4.8` i `v0.4.9.1` (`ORIGINAL.md`). |
| model kontrolny @ rewizja | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | plik Pythii v0 (`EleutherAI/pythia` @ `a19eecb`: brak `medmcqa`); karty 5 modeli przebiegu centralnego: bez wyniku MedMCQA; `openlifescienceai/results` @ `62d7322cf11bf622399f7f54e5a7620ec6ef013d` (Open Medical-LLM Leaderboard, 0-shot): żadnego z 5 modeli. |
| bez kontroli: opublikowane wyniki innych modeli (niepoliczone) | W `openlifescienceai/results` sprawdzone modele 1–3 mld (`pythia-1b`, `pythia-1b-deduped`, `pythia-1.4b`, `pythia-2.8b`, `pythia-2.8b-deduped`, TinyLlama-1.1B 3T, gpt-neo-2.7B) leżą pod b, więc nie przechodzą kolumny „kontrola”. Pierwszy przechodzący model wśród sprawdzonych to `Qwen/Qwen1.5-7B` (plik `results_2024-05-16 15:05:03.974764.json`, rewizja modelu `main`); pozostałych z 210 plików źródła nie przeglądano. Z decyzji dla przebiegu centralnego dodatkowych modeli kontrolnych nie liczymy. |
| bez kontroli: Qwen1.5-7B, wartość opublikowana | 0,5023 (SE 0,0077) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, results.medmcqa acc,none --> |
| bez kontroli: TinyLlama-1.1B 3T, wartość opublikowana | 0,2658 (SE 0,0068), pod b <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, results.medmcqa acc,none --> |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | brak: repo woła zadanie lm-eval wprost (ten sam prompt, litery i metryka), więc porównanie kodu niczego nie sprawdza (METODOLOGIA, „Bez kontroli”). |
| bez kontroli: zgodność według kolumny „test zgodności” typu | N/A z tego samego powodu. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić | Kod autorów (`MedMCQA/MedMCQA`) to dostrajanie modeli, nie ocena 0-shot. |
| dlaczego ten model | Pythia v0 nie ma zadania, EuroLLM-1.7B nie podaje wyniku na karcie; z punktu 3 listy pierwszy przechodzący wśród sprawdzonych to model 7B, którego nie liczono. |
| zbiór @ rewizja, split, n | `openlifescienceai/medmcqa` @ `91c6572c454088bf71b679ad90aa8dffcd0d5868`, `validation`, n = 4183 |
| wynik (SE): Slayer 1.06 | 0,3160, SE A 0,0072 |
| wartość referencyjna i źródło | brak |
| różnica | brak |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,3223, stała odpowiedź „zawsze `A`”. Bez modelu kontrolnego; modele przebiegu centralnego wobec b (parowane) stoją w [`README.md`](README.md): Qwen3.5-0.8B-Base, LFM2.5-1.2B-Base i LFM3-1.7B-Base przechodzą b + 2 SE, Slayer 1.06 i EuroLLM-1.7B nie. |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE; nie ma wartości referencyjnej, do której go przyłożyć. |
| werdykt | bez kontroli: nierozstrzygnięte. Wynik nie idzie do meta-oceny. MedMCQA nie należy do wyjątku z #97 (Space ma już wartość T45). |

## Slayer w Space (informacyjnie: nie kontrola ani wzorzec)

Space @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` ma T45 dla Slayera 1.06: 0,245 na panelu 200 (CI95 0,185–0,305, udział najczęstszej predykcji 0,88). Repo ma 0,3160 na pełnym splicie. <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f -->
Ładowania Slayera ta wartość nie sprawdza
([METODOLOGIA, „Model kontrolny etapu B”](../../METODOLOGIA.md#model-kontrolny-etapu-b)), a panelu Space nie odtworzono
(`ORIGINAL.md`, „Panel Space”), więc liczby niżej porównują różne pytania.

- Pełny split repo minus panel Space: +7,10 pkt. 2 SE panelu (SE A 0,0304) to 6,08 pkt, więc różnica wychodzi poza próg, ale pytania są inne. Ostrożne SE √(SE² + SE_panel²) = 0,0312, z = 2,27, prawdopodobne. <!-- liczba-spoza-wynikow: SE panelu z wartości Space 0,245 i n 200; SE pełnego splitu z results_rozszerzone.json -->
- Na panelu wybranym kodem repo Slayer ma 0,310 i wybiera `A` w 191 z 200 pytań; Space podaje udział najczęstszej predykcji 0,88, repo na pełnym splicie 0,9331. <!-- liczba-spoza-wynikow: panel repo przeliczony z probki/T45_space.jsonl.gz; 0,88 z results.json Space -->
- Ten sam przebieg daje LFM2.5-1.2B-Base 0,4059 na pełnym splicie, wobec 0,405 w Space (różnica 0,09 pkt). <!-- liczba-spoza-wynikow: results/central-run/medmcqa/lfm2.5-1.2b-base/results.json; 0,405 z results.json Space -->
- Podejrzany sam w sobie jest wynik Slayera, nie różnica wobec Space: na pełnym splicie Slayer wybiera `A` w 93,3% pytań, więc jego `acc` to w praktyce stała odpowiedź (sekcja „Wyniki przy bazie”). Do sprawdzenia przed wysłaniem wyniku T45 do Space. <!-- liczba-spoza-wynikow: probki Slayera w results/central-run/medmcqa -->

## Wyniki przy bazie

- Slayer 1.06 wybiera `A` w 3903 z 4183 pytań (udział 0,9331), a `A` jest poprawne w 1348. Jego 0,3160 to prawie dokładnie stała odpowiedź „zawsze `A`” (0,3223): różnica −0,62 pkt, SE parowane 0,0030, z = −2,04, prawdopodobne. To samo opisuje `analyses/answer-format/README.md` (test T1). <!-- liczba-spoza-wynikow: probki Slayera w results/central-run/medmcqa -->
- EuroLLM-1.7B ma 0,2582, przy bazie losowej 0,25 (z = 1,21, szum) i 6,41 pkt pod b (SE parowane 0,0109, z = −5,86, pewne). Wybiera `B` w 2631 z 4183 pytań (udział 0,6290), a `B` jest poprawne w 1085. W wariancie cloze (`results_rozszerzone.json`, `dodatkowe.cloze`) ma `acc_norm` 0,3091; to wynik informacyjny, metryką decyzyjną jest `acc` w formacie liter. <!-- liczba-spoza-wynikow: results/central-run/medmcqa/eurollm-1.7b (results_rozszerzone.json, probki) -->
