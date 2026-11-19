# AutomationBench (public)

Wersja angielska: [README.md](README.md).

Czy agent wykonuje wieloetapowe procesy biznesowe w symulowanych usługach (CRM, e-mail, Slack, arkusze, kalendarze,
zgłoszenia): znajduje właściwe endpointy API narzędziem wyszukiwania, wywołuje je przez HTTP i jest oceniany po
końcowym stanie usług na podstawie asercji, bez modelu-sędziego.

- Harness: [zapier/AutomationBench](https://github.com/zapier/AutomationBench) @
  `4a8e1061254004d9dac807054eed33fad7d1ff14` (`auto-bench`, wersja benchmarku 1.0.6)
- Dane: dołączone do harnessu, sześć publicznych domen (sales, marketing, operations, support, finance, hr), 600
  zadań (cały zbiór publiczny; domena `simple` to kontrola użycia narzędzi i nie wchodzi do wyniku)
- Metryka: odsetek zaliczonych (zadanie jest zaliczone tylko wtedy, gdy przechodzą wszystkie oceniane asercje);
  średni wynik częściowy i liczby asercji w `other_metrics`
- Ustawienia: zestaw narzędzi `api` (domyślny w harnessie), do 50 kroków na zadanie, 1 próba. Bielik: temperatura
  0.6, top_p 0.95, bez limitu wyjścia poza kontekstem (karta LFM3-1.7B: "up to 50 turns")
- Dodatkowe usługi: brak (usługi są symulowane w harnessie)

## Wyniki

| model | score | stderr | n | data |
|---|---|---|---|---|
| Bielik 11B v3.1, własny vLLM (`bielik-11b-v3.1-vllm`) | 0.00 | 0.00 | 600 | 2026-11-19 |
| Slayer 1B, krok 60000 (`slayer1b-60000`) | null | | 0 | 2026-11-19 |
| LFM3-1.7B, karta modelu | 41.29 | | | |

Bielik nie zalicza żadnego zadania ani żadnej z 5729 ocenianych asercji. Harness zapisuje też 3883 asercje, które
spełniłby bezczynny agent (np. "no email sent to X"); oznacza je jako `excluded` i ich nie ocenia, więc model, który
nic nie robi, ma wynik 0. Środowisko działa: wywołania podłączonej usługi się udają. Porażki są po stronie modelu:
`api_search` często dostaje prośbę o jeden wynik (`top_k: 1`) i zwraca niezwiązany endpoint, a z 1618 wywołań
narzędzi model wykonuje 351 do usług niepodłączonych do zadania (401), 484 do nieznanych endpointów (404) i 150 z
niepoprawnymi argumentami JSON (400); 235 z 600 zadań kończy się odpowiedzią tekstową bez żadnego wywołania
narzędzia. Jako kontrola dodatnia: ten sam serwer i te same ustawienia zaliczają 15 z 200 zadań (7.5%) w domenie
`simple` harnessu (`--domains simple`: Salesforce 8, HubSpot 2, Mailchimp 2, Jira 3); 5 przebiegów harness przerwał,
bo model nie zwrócił ani tekstu, ani wywołania narzędzia, i liczą się one jako porażki. Harness i jego narzędzia
działają więc z tym modelem, a 0/600 to wynik modelu na zadaniach publicznych.

Każdy wiersz `results/<model-id>.jsonl.gz` zawiera id i nazwę zadania, wynik 0/1, wynik częściowy, typ każdej
asercji z flagami passed/excluded, liczby kroków i wywołań narzędzi oraz `output`: całą rozmowę bez promptu
systemowego (wiadomości modelu, wywołania narzędzi i ich wyniki).

## Odstępstwa

- **Własny vLLM, nie API fabryka.ai.** Bielik 11B v3.1 Instruct
  ([speakleash/Bielik-11B-v3.1-Instruct](https://huggingface.co/speakleash/Bielik-11B-v3.1-Instruct) @
  `d6e755d356ad418d0f0e30b8c428db267415ddb9`, bfloat16) jest serwowany przez vLLM 0.34.0 na wynajętym GPU (NVIDIA
  RTX 6000 Ada Generation), z parserami wywołań narzędzi i rozumowania z
  [speakleash/bielik-tools](https://github.com/speakleash/bielik-tools) @ `2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09`
  (`vllm.sh`) i z domyślnymi ustawieniami szablonu czatu, w tym z promptem systemowym dostawcy, z datą ustawioną na
  2026-11-18. To konfiguracja wierszy `-vllm` benchmarku IFEval (#313), a nie wiersza API.
- **Jeden seed dla wszystkich zapytań.** Każde zapytanie ma ten sam `seed` (20261119); żadne zadanie nie skończyło
  się pustą odpowiedzią.
- **Wywołania narzędzi zostawione w tekście.** W 10 z 600 zadań ostatnia wiadomość modelu zawiera wywołanie
  narzędzia zapisane jako tekst, którego parser narzędzi vLLM nie zamienił na wywołanie; harness traktuje ją jako
  odpowiedź końcową.
- **Data.** Symulowane usługi działają według rzeczywistego zegara (2026-11-19), a szablon czatu podaje modelowi
  2026-11-18.
- **Zapytania idą w partiach.** 16 zadań naraz; ten sam serwer vLLM obsługiwał w trakcie biegu także inne
  benchmarki.
- **Slayer nie może uruchomić benchmarku.** Slayer 1B to model bazowy bez szablonu czatu i formatu wywołań
  narzędzi; serwer odrzuca zapytania z narzędziami (HTTP 400), więc żadne poprawne składniowo wywołanie nie jest
  możliwe.

## Jak powtórzyć

```bash
HF_TOKEN=hf_... bash vllm.sh                # jedno GPU z co najmniej 48 GB; serwuje na 127.0.0.1:8000
bash run.sh bielik-11b-v3.1-vllm            # w drugiej powłoce
DOMAINS=simple bash run.sh bielik-11b-v3.1-vllm   # kontrola użycia narzędzi z harnessu (200 zadań, bez oceny)
bash run.sh slayer1b-60000                  # zapisuje wynik null
```

`--limit 5` uruchamia tylko pierwsze 5 zadań i zapisuje do `out/limit/`. `BASE_URL` kieruje `run.sh` na inny
endpoint, który serwuje model jako `bielik`.
