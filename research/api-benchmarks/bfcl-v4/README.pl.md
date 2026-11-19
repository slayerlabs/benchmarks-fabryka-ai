# BFCL V4

Wersja angielska: [README.md](README.md).

Czy model poprawnie wywołuje funkcje: wybiera właściwą funkcję (albo żadną), wypełnia jej argumenty, wywołuje kilka
równolegle lub po kolei i utrzymuje stan w zadaniach wieloetapowych i z pamięcią. Harness sprawdza wywołania
względem wzorca (zgodność AST, stan po wykonaniu albo odpowiedzi z pamięci), bez modelu-sędziego.

- Ranking i metoda: [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)
- Harness: [ShishirPatil/gorilla](https://github.com/ShishirPatil/gorilla) @ `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`,
  `berkeley-function-call-leaderboard` (`bfcl generate`, `bfcl evaluate`)
- Dane: dołączone do harnessu, `bfcl_eval/data` @ ten sam commit. 20 nazwanych kategorii testów, 4906 ocenianych
  zadań (całe V4 poza `web_search`, zob. Odstępstwa)
- Metryka: Overall Acc harnessu (`score/data_overall.csv`), podawane tu jako `score: null`, bo wymaga `web_search`;
  pięć wyników grup liczonych przez harness jest w `other_metrics` (zob. Wyniki)
- Ustawienia: tryb wywoływania funkcji (`bielik-FC`: natywne wywołania narzędzi przez parser narzędzi vLLM),
  domyślna temperatura BFCL 0.001, bez limitu wyjścia poza kontekstem 32 768 tokenów, 1 próba (karta LFM3-1.7B:
  "greedy decoding, up to 32,768 output tokens") <!-- liczba-spoza-wynikow: dosłowny cytat karty LFM3, separator tysięcy -->
- Dodatkowe usługi: brak (zadania wieloetapowe i z pamięcią działają lokalnie w harnessie)

## Wyniki

| model | score | stderr | n | data |
|---|---|---|---|---|
| Bielik 11B v3.1, własny vLLM (`bielik-11b-v3.1-vllm`) | null | | 4906 | 2026-11-19 |
| Slayer 1B, krok 60000 (`slayer1b-60000`) | null | | 0 | 2026-11-19 |
| LFM3-1.7B, karta modelu | 71.39 | | | |

Wyniki grup harnessu dla Bielika (procent, w nawiasie błąd standardowy, SE):

| non-live AST | live AST | irrelevance | relevance | multi-turn | memory | Overall, dolna granica |
|---|---|---|---|---|---|---|
| 85.50 (1.18) | 72.91 (1.21) | 75.68 (1.57) | 93.75 (6.05) | 5.62 (0.81) | 16.56 (1.70) | 28.41 (0.48) |

**Overall, dolna granica** to Overall Acc samego harnessu z `web_search` liczonym jako 0, bo tak jego wzór
traktuje brakującą kategorię. Nie da się jej porównać z 71.39 i nie jest wynikiem.

Wyniki poszczególnych kategorii są w `categories` w `results/bielik-11b-v3.1-vllm.json`, a każdy wiersz `.jsonl.gz`
to jedno zadanie: `task_id`, `category`, `score` (0/1), `error_type` harnessu dla zadań niezaliczonych i surowy
`output`.

## Odstępstwa

- **`web_search` nie jest uruchamiany, więc nie ma wyniku Overall.** Jego dwie kategorie (`web_search_base`,
  `web_search_no_snippet`, po 100 zadań) wywołują rzeczywiste API wyszukiwarki, które wymaga klucza (SerpAPI).
  Overall Acc w BFCL to 10% non-live + 10% live + 10% irrelevance + 30% multi-turn + 40% agentic, gdzie agentic =
  średnia(web search, memory) (`bfcl_eval/eval_checker/eval_runner_helper.py`), a brakująca kategoria liczy się
  jako 0. Bez web search Overall straciłby połowę wagi agentic, więc zostawiamy `score` jako null i podajemy wyniki
  grup.
- **Własny vLLM, nie API fabryka.ai.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) jest serwowany przez vLLM 0.34.0 na wynajętym GPU (NVIDIA
  RTX 6000 Ada Generation), z parserami wywołań narzędzi i rozumowania z
  [speakleash/bielik-tools](https://github.com/speakleash/bielik-tools) @ `2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09`
  (`vllm.sh`). Działa z domyślnymi ustawieniami szablonu czatu, w tym z promptem systemowym dostawcy, z datą
  ustawioną na 2026-11-18. To konfiguracja wierszy `-vllm` benchmarku IFEval (#313), a nie wiersza API: w IFEval
  oba różniły się o około 5 punktów.
- **Model jest dopisany do tabeli modeli harnessu.** BFCL nie ma wpisu dla Bielika. `run.sh` dopisuje jeden wpis
  (`model_config_bielik.py`): `bielik-FC`, handler zgodny z OpenAI, tryb wywoływania funkcji, standardowa opcja
  harnessu dla modeli, w których nazwach funkcji nie może być kropek. Poza tym nic w harnessie się nie zmienia.
- **Temperatura 0.01 zamiast 0.001 w BFCL.** BFCL wysyła 0.001 (swoją domyślną, prawie greedy, także we własnym
  rankingu); vLLM 0.34 podnosi każdą temperaturę poniżej 0.01 do 0.01 i zapisuje to w logu.
- **Zapytania idą w partiach.** Harness wysyła 16 zapytań naraz, a vLLM łączy je w partie. Wyjścia greedy przy
  partiach mogą się nieznacznie różnić od dekodowania pojedynczo. Ten sam serwer vLLM obsługiwał w trakcie tego
  biegu także inne benchmarki, więc skład partii się zmieniał.
- **Jeden dodatkowy pakiet.** `qwen-agent`, zależność harnessu, importuje `soundfile` bez deklarowania go;
  `run.sh` instaluje `soundfile==0.13.1`.
- **Błędy standardowe (SE).** Dla wyników grup: sqrt(sum w^2 p (1 - p) / n) po kategoriach, z wagami grupy z harnessu.
  Zakłada to niezależność zadań, a zadania wieloetapowe zbudowane na tym samym scenariuszu nie są w pełni
  niezależne, więc błąd multi-turn jest nieco za mały.
- **Przygotowanie pamięci.** Kategorie memory najpierw generują 37 rozmów przygotowawczych na backend (111
  łącznie), które wypełniają pamięć; harness ich nie ocenia, `summarize.py` też nie.
- **17 zadań wieloetapowych przekroczyło kontekst.** W `multi_turn_long_context` 17 z 200 rozmów urosło ponad
  kontekst 32 768 tokenów i vLLM odrzucił kolejne zapytanie (HTTP 400, "maximum context length"). Harness ocenia je
  jako niezaliczone, my też, w pełnym N; są wypisane w `context_window_exceeded` w
  `results/bielik-11b-v3.1-vllm.json`. Żadne inne zapytanie nie zakończyło się błędem.
- **Slayer nie może uruchomić benchmarku.** Slayer 1B to model bazowy bez szablonu czatu i formatu wywołań
  narzędzi; serwer odrzuca zapytania z narzędziami (HTTP 400), więc żadne poprawne składniowo wywołanie nie jest
  możliwe. `results/slayer1b-60000.json` ma `score: null` z tym powodem.

## Jak powtórzyć

```bash
HF_TOKEN=hf_... bash vllm.sh                # jedno GPU z co najmniej 48 GB; serwuje na 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # w drugiej powłoce
bash run.sh slayer1b-60000                  # zapisuje wynik null
```

`--limit 5` uruchamia pierwsze 5 zadań każdej kategorii (z rozmowami przygotowującymi pamięć) i zapisuje do
`out/limit/`. `BASE_URL` kieruje `run.sh` na inny endpoint, który serwuje model jako `bielik`. `summarize.py`
zatrzymuje się, jeśli któreś zadanie nie ma odpowiedzi modelu z innego powodu niż limit kontekstu (`Error during
inference`, np. zerwane połączenie), bo harness oceniłby je jako złe wywołanie: najpierw powtórz te ID przez
`bfcl generate --run-ids --allow-overwrite`.
