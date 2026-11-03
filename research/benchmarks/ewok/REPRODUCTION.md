# EWoK: odtworzenie (etap B) i zgodność naszego kodu (etap C)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcje „B” i „C”. Karta oryginału:
[`ORIGINAL.md`](ORIGINAL.md). Liczby: [`results/gpt2xl_comparison.json`](results/gpt2xl_comparison.json)
(`reference/compare.py`). Przepis: [`RECIPE.md`](RECIPE.md). Przebiegi z 2026-11-03.

Wszystkie trafności niżej liczymy na tych samych 4374 rekordach `ewok-core-1.0` (zbiór z tabeli pracy). SE jest po
rekordach. Po szablonach byłoby około 2 razy większe (`README.md`).

## Etap B: kod autorów

| | wartość |
|---|---|
| kod referencyjny @ commit | `ewok-core/ewok-paper` @ `9e40d30e242925866ee50448f80a13bcdf971318`: `ewok.evaluate.model.Model` i `Evaluator._evaluate_logprobs` bez zmian, wołane przez [`reference/run_authors.py`](reference/run_authors.py). Scorer: `surprisal` @ `366b074e3efb1e4d83ae8242013880c5e15851da`, `transformers 4.40.0` jak w `requirements.txt` autorów. torch 2.10.0+cu130 zamiast 2.1.0, bo 2.1.0 nie obsługuje RTX 50xx. Pakiet `outlines` (tylko tryby choice i likert) podstawiony pustym modułem. Środowisko: [`reference/requirements-ref.txt`](reference/requirements-ref.txt) |
| dlaczego ten kod | to kod, którym autorzy policzyli tabelę pracy (`scripts/run_eval_dataset.sh`) |
| model kontrolny @ rewizja | `openai-community/gpt2-xl` @ `15ea56dee5df4983c59b2538573817e1667135e2` (w pracy `gpt2-xl`), domyślne bf16 autorów, batch 1 |
| dlaczego ten model | Pythia v0 i EuroLLM nie mają opublikowanego wyniku EWoK. gpt2-xl to model z tabeli pracy (punkt 3 listy; nie najmniejszy, `phi-1_5` ma 1,3B) i jest wyraźnie nad bazą: 0,656 przy SE 0,007 <!-- liczba-spoza-wynikow: tabela pracy; SE = √(0,656·0,344/4374) --> |
| zbiór @ rewizja, split, n | 5 wersji z `analyses/data.zip` (`outputs_20240429/dataset/ewok1.0`), czyli 4555 rekordów. Ocena na 4374 z nich, które tworzą `ewok-core-1.0` @ `34d912a608066c92e2990a0328ffc3bd9a716042` (łączone po czwórce C1, C2, T1, T2) <!-- liczba-spoza-wynikow: 5 × 911 rekordów z data.zip --> |
| wynik (SE) | 65,47% (SE 0,45 pkt). Wersje 0–4: 66,32 / 64,97 / 65,95 / 65,71 / 64,40. Ten sam kod w fp32: 65,36% (SE 0,45 pkt) |
| wartość referencyjna i źródło | tabela pracy: 0,656, zakres 0,646–0,663 (`analyses/tables/ 20240429 _mean_accuracy_allmodels.tex`). Surowe wyniki autorów z `data.zip` na tych samych 4374 rekordach: 65,59% (SE 0,45 pkt), wersje 0–4: 65,95 / 65,29 / 65,81 / 66,34 / 64,57 <!-- liczba-spoza-wynikow: 0,656 i 0,646–0,663 z tabeli pracy --> |
| różnica | data.zip − nasz przebieg kodu autorów: +0,12 pkt (SE 0,14 pkt, szum). Tabela pracy − nasz przebieg: +0,1 pkt <!-- liczba-spoza-wynikow: 65,6 (tabela pracy) − 65,47 --> |
| warunek odtworzenia | ±2 pkt (2 SE = 0,9 pkt < 2 pkt) <!-- liczba-spoza-wynikow: 2 × 0,45 pkt --> |
| werdykt | **spełniony** |

**Skąd 0,656 w tabeli pracy.** Surowe wyniki gpt2-xl w `data.zip` dają na wszystkich 911 rekordach wersji średnio <!-- liczba-spoza-wynikow: data.zip -->
0,6515. Analiza autorów (`inspect_results.Rmd`) przed uśrednieniem usuwa duplikaty i rekordy oflagowane po <!-- liczba-spoza-wynikow: data.zip, wszystkie rekordy wersji -->
badaniu z ludźmi. Zostaje 875 rekordów na wersję (874 w wersji 2), razem 4374. Dokładnie te rekordy są w <!-- liczba-spoza-wynikow: ewok-core-1.0.parquet i data.zip -->
`ewok-core-1.0` na HF. Średnia surowych wyników na nich to 65,59%, czyli 0,656 z tabeli.

**Precyzja i sprzęt.** Kod autorów w bf16 na naszym GPU jest deterministyczny: dwa przebiegi dały identyczne log P.
Z wynikami autorów (bf16, ich GPU) zgadza się jednak tylko w 98,15% decyzji (162 z 8748 różne). Średnia
|Δ log P| = 0,056, max 0,40. Ten sam kod w fp32 zgadza się z naszym bf16 w 98,53% decyzji. W bf16 decyzje zależą
więc od sprzętu i precyzji. Trafność się nie zmienia, różnica to szum. Dlatego zgodność per rekord (etap C)
sprawdzamy w float32, wobec kodu autorów w fp32.

## Etap C: nasz kod (`ewok.py`) a kod autorów

Nasz kod to własna implementacja. `common/hipoteza_formatu.py` koduje parę jak lm-eval, a regułę ma `ewok.evaluate`.
Zgodnie z METODOLOGIA.md wolno go używać po teście zgodności: ten sam model i te same rekordy, wynik w granicach SE,
≥ 99% zgodnych decyzji. Decyzja to znak log P(T1|C1) − log P(T1|C2) i log P(T2|C2) − log P(T2|C1), po dwie na rekord,
razem 8748.

| nasz tryb (`ewok.py score`) | trafność (SE) | różnica do kodu autorów fp32 | zgodne decyzje z kodem autorów fp32 | z kodem autorów bf16 (nasz GPU) | z `data.zip` |
|---|---|---|---|---|---|
| domyślny: bez BOS, float32 (jak kod autorów) | 65,36% (0,45) | 0,00 pkt (SE 0,02 pkt, szum) | **99,98%** (2 z 8748 różne) | 98,53% | 98,40% |
| `--bos`: BOS przed kontekstem, float32 (tak liczy `ewok-pl`) | 66,02% (0,46) | autorzy − nasz: −0,65 pkt (SE 0,37 pkt, szum) | 85,45% (1273 z 8748 różne) | 85,20% | 84,89% |
| bez BOS, bf16, batch 1 (`reference/ours_bf16.py`, ustawienia autorów) | 65,48% (0,45) | autorzy − nasz: −0,11 pkt (SE 0,12 pkt, szum) | 98,70% | 98,30% | 97,98% |

- **Bez BOS.** Tryb domyślny w float32 daje prawie te same log P co kod autorów w fp32: |Δ log P| średnio 0,004 i
  najwyżej 0,044. Tyle wnosi inna wersja transformers i batch z paddingiem zamiast batcha 1. Dwie różne decyzje to
  porównania, w których kontekst prawie nie zmienia log P.
- **BOS.** Kod autorów nie daje BOS (`use_bos_token=False`). Pierwszy token kontekstu nie ma więc niczego przed
  sobą, a reszta kontekstu jest warunkowana inaczej niż w trybie `--bos`. Na trafność wpływa to słabo: 66,02% wobec
  65,47% u autorów, w granicach ±2 pkt. Zmienia jednak 15% pojedynczych decyzji (|Δ log P| średnio 1,49).
- **bf16.** Nasz kod w ustawieniach autorów (bez BOS, bf16, batch 1) ma 65,48% wobec 65,47% kodu autorów w bf16 i
  98,30% zgodnych decyzji. To ten sam szum bf16 co między kodem autorów u nas a ich `data.zip` (98,15%). Liczymy więc
  w fp32, gdzie zgodność jest pełna.
- **Remisy.** W float32 żaden tryb nie miał remisu. Kod autorów w bf16 miał 3 remisy, `data.zip` 4. Remis to jedyne
  miejsce, gdzie reguły się różnią: u autorów 0,5, u nas 0.
- **Test zgodności:** [`../../tests/test_ewok_zgodnosc.py`](../../tests/test_ewok_zgodnosc.py), 16 rekordów
  wylosowanych seedem 20261103. Plik `common/tests/data/ewok_zgodnosc.json` trzyma numery wierszy i log P z kodu
  autorów (fp32) oraz z trybu domyślnego, bez tekstu. Część z przeliczeniem modelu uruchamia się, gdy gpt2-xl i zbiór
  są w lokalnym cache HF.

| warunek etapu C | tryb domyślny (bez BOS) | tryb `--bos` |
|---|---|---|
| wynik w granicach SE od kodu autorów | tak (0,00 pkt) | nie (0,65 pkt > SE 0,45 pkt) |
| ≥ 99% zgodnych decyzji | tak (99,98%) | nie (85,45%) |
| werdykt | **spełniony**: wolno liczyć EWoK naszym kodem | **niespełniony**: to „dodatkowy sposób liczenia”, nie metoda oryginału |

Wyniki `ewok-pl` policzono z BOS, czyli trybem `--bos`. Metodą autorów trzeba je przeliczyć bez BOS (etap D).
