# Social IQa: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Wyniki: [`results/central-run/social-iqa/`](../../results/central-run/social-iqa/). Odczyt źródeł 2026-11-04.

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1` (`common/requirements.lock.txt`), zadanie `social_iqa` (`lm_eval/tasks/siqa/siqa.yaml`): repo powtarza jego szablon, opcje i cel (`common/zadania.py`, T46); zmienione tylko źródło danych (parquet HF) |
| dlaczego ten kod | Autorzy nie publikują kodu 0-shot dla modelu językowego. Karta (`ORIGINAL.md`) wskazuje zadanie lm-eval `lm_eval/tasks/siqa/siqa.yaml`, a katalog zadania ma te same bloby w `6d2abda4`, `v0.4.8` i `v0.4.9.1` (`ORIGINAL.md`). |
| model kontrolny @ rewizja | bez kontroli |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | plik Pythii v0 (`EleutherAI/pythia` @ `a19eecb`: brak `social_iqa`); karty 5 modeli przebiegu centralnego: bez wyniku Social IQa; `openlifescienceai/results` @ `62d7322c`: brak zadania; prace TinyLlama ([arXiv:2401.02385](https://arxiv.org/abs/2401.02385)) i DeltaNet ([arXiv:2406.06484](https://arxiv.org/abs/2406.06484)): bez SIQA; Space @ `2d3d73f`: `not_run`; issue [#97](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/97). Niesprawdzone: Gated DeltaNet ([arXiv:2412.06464](https://arxiv.org/abs/2412.06464)), Llama i Llama 2 (własny prompt, wagi z bramką), OLMo 2 (OLMES, 5-shot). |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | brak: repo liczy zadanie lm-eval (szablon przepisany 1:1 z `siqa.yaml`), więc porównanie kodu niczego nie sprawdza (METODOLOGIA, „Bez kontroli”). |
| bez kontroli: zgodność według kolumny „test zgodności” typu | N/A z tego samego powodu. |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić | Kodu ewaluacji autorów nie znaleziono (`ORIGINAL.md`, „Źródła”). |
| dlaczego ten model | Żaden model z listy „Model kontrolny etapu B” (Pythia v0, EuroLLM-1.7B, dowolny model z opublikowanym wynikiem) nie ma znalezionego wyniku. |
| zbiór @ rewizja, split, n | `allenai/social_i_qa` @ `8835ceb9141d7896d9d968634a9b21ae440e3ec5`, parquet `refs/convert/parquet` (commit nieprzypięty, `537a2ec8` w dniu odczytu), `validation`, n = 1954 |
| wynik (SE): Slayer 1.06 | 0,3895, SE A 0,0110 <!-- liczba-spoza-wynikow: results/central-run/social-iqa/slayer1b-1.06/results_rozszerzone.json, dodatkowe.space.acc --> |
| wartość referencyjna i źródło | brak |
| różnica | brak |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,3362, stała odpowiedź „zawsze `answerC`”. Bez modelu kontrolnego; wszystkie 5 modeli przebiegu centralnego przechodzi b + 2 SE (parowane, [`README.md`](README.md)), co wyklucza kod, który ocenia losowo, ale nie zastępuje odtworzenia. Typ `mc` nie wymaga dodatkowego przebiegu. |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE; nie ma wartości referencyjnej, do której go przyłożyć. |
| werdykt | bez kontroli: nierozstrzygnięte. Wynik nie idzie do meta-oceny; do Space najwyżej jako wstępny według wyjątku z #97. |

## Slayer: ładowanie i rozkład predykcji

Kontrola nie sprawdza ładowania Slayera; sprawdzają je testy kodu Slayera
([METODOLOGIA, „Model kontrolny etapu B”](../../METODOLOGIA.md#model-kontrolny-etapu-b)). Informacyjnie: Space @
`2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9` ma T46 w stanie `not_run` dla Slayera 1.06 (i dla LFM2.5-1.2B-Base).

Rozkład predykcji Slayera jest równy: najczęstsza opcja w 0,3480 pytań, przy rozkładzie celu 643/654/657. <!-- liczba-spoza-wynikow: probki/T46_space.jsonl.gz Slayera -->
