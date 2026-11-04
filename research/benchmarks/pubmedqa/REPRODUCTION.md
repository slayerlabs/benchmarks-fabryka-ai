# PubMedQA: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Wyniki: [`results/central-run/pubmedqa/`](../../results/central-run/pubmedqa/). Odczyt źródeł 2026-11-04.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1` (`common/requirements.lock.txt`), zadanie `pubmedqa`: repo bierze `doc_to_text` z `preprocess_pubmedqa.py` tej wersji i te same opcje i cel co `pubmedqa.yaml` (`common/zadania.py`, T44); zmienione tylko źródło danych (parquet przypięty w `ORIGINAL.md`) |
| dlaczego ten kod | Autorzy nie publikują kodu 0-shot dla modelu językowego (praca ocenia dostrajane klasyfikatory). Space wskazuje `lm_eval/tasks/pubmedqa/pubmedqa.yaml` (`tasks_50.json` T44), a katalog zadania ma te same bloby w `6d2abda4`, `v0.4.8` i `v0.4.9.1` (`ORIGINAL.md`, „Znane rozbieżności”). |
| model kontrolny @ rewizja | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | plik Pythii v0 (`EleutherAI/pythia` @ `a19eecb`, `evals/pythia-v0`: brak `pubmedqa`); karty 5 modeli przebiegu centralnego (Qwen3.5-0.8B-Base, LFM2.5-1.2B-Base, LFM3-1.7B-Base, EuroLLM-1.7B, Slayer 1.06): bez wyniku PubMedQA; `openlifescienceai/results` @ `62d7322cf11bf622399f7f54e5a7620ec6ef013d` (Open Medical-LLM Leaderboard, 0-shot): żadnego z 5 modeli; Space @ `2d3d73f`: `not_run`; issue [#97](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/97). |
| bez kontroli: opublikowane wyniki innych modeli (niepoliczone) | `openlifescienceai/results` ma 0-shot `pubmedqa` m.in. dla `TinyLlama/TinyLlama-1.1B-intermediate-step-1431k-3T` (plik `results_2024-05-24 17:53:20.359555.json`, float32). Rewizja modelu w pliku to `main`, wersja lm-eval niezapisana. Z decyzji dla przebiegu centralnego liczymy tylko Slayera i modele przebiegu, bez dodatkowych modeli kontrolnych, więc tej kontroli nie policzono. |
| bez kontroli: TinyLlama, wartość opublikowana | 0,614 (SE 0,0218); niesparowane z = (0,614 − 0,552) / 0,0218 = 2,84, czyli przeszłaby kolumnę „kontrola” typu. <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, results.pubmedqa acc,none i acc_stderr,none --> |
| bez kontroli: Pythia w tym samym źródle | `pythia-1b` 0,582 (z = 1,36) i `pythia-1.4b` 0,594 (z = 1,91) nie przechodzą b + 2 SE, więc nie są kontrolą. <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c; z niesparowane wobec b 0,552 --> |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | brak: repo woła zadanie lm-eval wprost (ten sam prompt, opcje i metryka), więc porównanie kodu autorów z kodem repo niczego nie sprawdza (METODOLOGIA, „Bez kontroli”). |
| bez kontroli: zgodność według kolumny „test zgodności” typu | N/A z tego samego powodu. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić | Kod autorów (`pubmedqa/pubmedqa`) to dostrajanie BioBERT, nie ocena 0-shot. |
| dlaczego ten model | Żaden model z listy „Model kontrolny etapu B” nie ma wyniku w ustawieniach przebiegu: Pythia v0 nie ma zadania, EuroLLM-1.7B nie podaje wyniku na karcie. Pierwszy przechodzący model z punktu 3 listy (TinyLlama) nie był liczony. |
| zbiór @ rewizja, split, n | `bigbio/pubmed_qa` @ `15578e80ef02c2c9636d33fdd7eb6b05b987ba60`, parquet `refs/convert/parquet` @ `13a7d15476092370cbabb6475390e7e69b74d2f2`, `pubmed_qa_labeled_fold0_source/test`, n = 500 |
| wynik (SE): Slayer 1.06 | 0,476 (238 z 500), SE A 0,0224 <!-- liczba-spoza-wynikow: results/central-run/pubmedqa/slayer1b-1.06/results_rozszerzone.json, dodatkowe.space.acc --> |
| wartość referencyjna i źródło | brak |
| różnica | brak |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,552, stała odpowiedź „zawsze `yes`”. Bez modelu kontrolnego; modele przebiegu centralnego wobec b (parowane po pytaniach) stoją w [`README.md`](README.md). Typ `mc` nie wymaga dodatkowego przebiegu. |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE; nie ma wartości referencyjnej, do której go przyłożyć. |
| werdykt | bez kontroli: nierozstrzygnięte. Wynik nie idzie do meta-oceny; do Space najwyżej jako wstępny według wyjątku z #97. |

## Slayer a Space

Kontrola nie sprawdza ładowania Slayera. Space @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` ma T44 w stanie
`not_run` dla Slayera 1.06 (i dla LFM2.5-1.2B-Base), więc porównania Slayera z panelem Space nie da się zrobić.

## Wynik Slayera pod bazą większościową

Slayer 1.06 ma 0,476, czyli 7,60 pkt pod b = 0,552 (SE parowane 0,0316, z = −2,41, prawdopodobne). <!-- liczba-spoza-wynikow: przeliczone z results/central-run/pubmedqa/slayer1b-1.06/probki -->
Rozkład jego predykcji (argmax `acc` z `probki/T44_space.jsonl.gz`):

| cel \ predykcja | `yes` | `no` | `maybe` |
|---|---:|---:|---:|
| `yes` (276) | 131 | 145 | 0 |
| `no` (169) | 62 | 107 | 0 |
| `maybe` (55) | 31 | 24 | 0 |

- Slayer nie wybiera stale jednej klasy: `no` w 276 z 500 (udział najczęstszej predykcji 0,552), `yes` w 224, `maybe` nigdy. <!-- liczba-spoza-wynikow: probki Slayera; 0,552 to też pole majority_prediction_share w results.json -->
- Wynik pod bazą bierze się z przechyłu w stronę `no`, choć w danych częściej pada `yes`: na pytaniach z celem `yes` trafia 131 z 276, na pytaniach z celem `no` 107 z 169.
- Udział najczęstszej predykcji 0,552 równa się bazie większościowej przypadkiem: Slayer mówi `no` 276 razy, a cel `yes` też występuje 276 razy. Pole `majority_prediction_share` w `results.json` to udział predykcji, nie baza. <!-- liczba-spoza-wynikow: probki Slayera i rozkład celu -->
- Żaden z 5 modeli przebiegu nie wybiera `maybe`; EuroLLM-1.7B też leży pod b (0,530), ale w granicach szumu (`README.md`). <!-- liczba-spoza-wynikow: results/central-run/pubmedqa/eurollm-1.7b/results.json -->
- Informacyjnie: `acc_mutual_info` Slayera wynosi 0,542, `acc_norm` 0,400 (`results_rozszerzone.json`). Metryką decyzyjną jest `acc`. <!-- liczba-spoza-wynikow: results/central-run/pubmedqa/slayer1b-1.06/results_rozszerzone.json -->
