# EWoK-PL: ewaluacja wiedzy o świecie po polsku

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md): etap A to karta oryginału (`ORIGINAL.md`), etap B to
> odtworzenie opublikowanego wyniku kodem autorów (`REPRODUCTION.md`), etap D to wersja polska tą samą metodą
> (`POLISH.md`). Ten katalog powstał przed metodologią i nie ma jeszcze tych plików (zadanie #34). Przepis każdego
> wyniku: [`RECIPE.md`](RECIPE.md). Pojęcia (Space, SE, werdykt, CI95): [słowniczek](../../METODOLOGIA.md#słowniczek).

Mierzymy, czy modele wiedzą, co wynika z prostych sytuacji (EWoK, *Elements of World Knowledge*), po
polsku i po angielsku na tych samych rekordach. Stan na 2.11.2026: 10 modeli, czyli Slayer 1B 1.00–1.06,
Bielik-1.5B-v3, LFM3-1.7B-Base i Aster-0.5B(fp32). Zestaw polski to 625 roboczych rekordów z domeny
`agent-properties`.

**Wyniki i wnioski: [`WYNIKI.md`](WYNIKI.md).** Wszystkie tabele z CI i kontrastami:
[`results/raport_ewok.md`](results/raport_ewok.md), dane: [`results/raport_ewok.json`](results/raport_ewok.json).

| model | PL (625) | EN pełny (4374) |
|---|---|---|
| Bielik-1.5B-v3 | 66,0 | 69,5 |
| LFM3-1.7B-Base | 57,4 | 69,7 |
| Slayer1B-1.06 | 55,4 | 58,9 |
| Aster-0.5B(fp32) | 54,6 | 50,7 |
| Slayer1B-1.00 | 54,4 | 53,1 |

Wynik EWoK w %, losowo 50. Pozostałe wersje Slayera i przedziały są w `WYNIKI.md`.

## Pliki

| plik | co robi |
|---|---|
| `ewok.py` | `licz`: logliki 2×2 per rekord dla jednego modelu; `analiza`: oceny, CI, kontrasty, raport |
| `WYNIKI.md` | podsumowanie dla zespołu i Arka |
| `results/raport_ewok.{json,md}` | pełny raport (w repo) |
| `results/<model>/{pl,en}.jsonl` | surowe logliki per rekord, bez tekstu (lokalnie, `.gitignore`) |
| `research/tests/test_ewok_pl.py` | 14 testów czystych funkcji, bez wag i bez danych |

## Protokół

Jest zgodny z paperem EWoK (Ivanova i in. 2024, [arXiv:2405.09605](https://arxiv.org/abs/2405.09605)), tryb LOGPROBS.

- **Rekord:** C1, C2, T1, T2. T1 pasuje do C1, a T2 do C2. Liczymy `log P(T | C)` jako sumę logprob tokenów
  `" " + T` po kontekście `C`.
- **Reguła główna (target stały):** `s1 = [P(T1|C1) > P(T1|C2)]`, `s2 = [P(T2|C2) > P(T2|C1)]`,
  `wynik = (s1+s2)/2`. Losowo wychodzi 50%, remis liczy się jako pudło. Po obu stronach porównania
  jest ten sam napis T, więc prior litery i długości odpowiedzi (główny problem z
  [analizy formatu odpowiedzi](../../analyses/answer-format/README.md)) się tu nie pojawia.
- **Scorer:** `common/hipoteza_formatu.py` (`para`, `licz_logliki`, forward `slayer_model.py` dla
  Slayera). Pary kodujemy jak w lm-eval. Wszystkie modele dostają jeden BOS przed kontekstem
  (METHOD.md Space). Bez szablonu czatu.
- **Precyzja: float32 dla wszystkich modeli.** Wagi ładujemy z `dtype=torch.float32`. Aster ma
  w repo HF osobny wariant fp32 (`fp32/`, 2,08 GB) i to jego używamy, stąd nazwa `Aster-0.5B(fp32)`.
  Główne wagi Astera są w bf16.
- **Modele HF:** ładujemy przez `AutoModelForCausalLM` (LFM3 i Aster z `trust_remote_code`, kod modelu z
  repo autora, przypięta rewizja). Sprawdziliśmy, że ścieżka scorera daje te same logity co `model(ids)`:
  - Bielik i LFM3: `glowa(ukryte) == logits` (max |Δ| = 0);
  - Aster: osobna ścieżka (`bez_bazy`), max |Δ| = 1e-5. Batch z prawym paddingiem daje to samo co
    pojedyncze wywołania.

  Aster nie ma osobnego modelu bazowego, a domyślne `logits_to_keep=1` zwraca logity tylko ostatniej
  pozycji, dlatego liczymy dla niego pełne logity z `logits_to_keep=0, use_cache=False`.
- **Czy modele są dobrze załadowane** (sprawdzone 2.11.2026):
  - **Slayer:** nasz forward (`slayer_model.py`) porównany z referencją z repo modelu (`load_slayer.py` +
    `train_gpt_ref_r23.py`) dla 1.00 i 1.06. Max |Δ logit| = 1,6e-5, a na 120 rekordach EWoK-PL max
    |Δ loglik| = 6e-5 i żaden rekord nie dostał innej oceny.
  - **Aster:** brak brakujących i nieoczekiwanych kluczy przy ładowaniu. Bufory RoPE z checkpointu są
    identyczne ze świeżo policzonymi (Δ = 0), a `lm_head` jest związany z embeddingami. Wagi fp32 i główne
    bf16 dają tę samą perplexity. Na krótkich tekstach Aster ma po polsku 0,48–0,81 bita na bajt <!-- liczba-spoza-wynikow: jednorazowa kontrola ładowania 2.11.2026 (4 krótkie teksty), nie wynik benchmarku -->
    (Bielik 0,52–1,11, Slayer 1.06 0,55–0,86) i generuje spójny polski tekst. Po angielsku ma 2,17 bita <!-- liczba-spoza-wynikow: jednorazowa kontrola ładowania 2.11.2026 (4 krótkie teksty), nie wynik benchmarku -->
    na bajt (Bielik 0,92), co pasuje do jego losowego wyniku na EWoK EN. Słaby angielski Astera to więc <!-- liczba-spoza-wynikow: jednorazowa kontrola ładowania 2.11.2026 (4 krótkie teksty), nie wynik benchmarku -->
    cecha modelu, a nie błąd ładowania.
- **Niepewność:** CI95 z bootstrapu (10 000 powtórzeń, seed 20261028). Kontrasty liczymy sparowanym
  testem permutacyjnym.
  - **Po szablonach:** każdą wielkość podajemy po rekordach i po szablonach, miarodajna jest ta druga.
    EWoK wypełnia szablon kilkoma zestawami imion i obiektów, więc rekordy jednego szablonu nie są
    niezależne. Szablon odtwarzamy z EN (`szablony()`): w obrębie (para pojęć, domena) słowa obecne
    w mniej niż 30% rekordów maskujemy jako wypełnienia. Daje to 130 szablonów na 625 rekordów PL,
    zwykle po 5. Bootstrap losuje całe szablony, a test permutacyjny zmienia znak różnicy dla
    całego szablonu naraz.
  - **Korekta Holma:** w każdej rodzinie kontrastów (`p_holm_po_szablonach`) i na wszystkich
    kontrastach naraz (`p_holm_wszystkie_po_szablonach`, 23 testy). Za istotne w `WYNIKI.md` uznajemy
    tylko to, co przeżywa tę drugą korektę. <!-- ocena-bez-se: opis reguły, nie porównanie -->
- **Kontrasty:** PL vs EN na tych samych `source_id`, kolejne wersje Slayera, Slayer 1.06 vs 1.00 (PL,
  EN625, EN), różnica różnic (PL 1.06 − PL 1.00) − (EN 1.06 − EN 1.00) per rekord, inne modele vs Slayer 1.06.
- **Diagnostyki:**
  - `oba`: obie pary trafione. 25% tylko przy niezależnych porównaniach, prior zdania spycha tę metrykę niżej.
  - `kontekst_staly`: T1 vs T2 przy tym samym C, wrażliwe na prior zdania.
  - `kontekst_staly_pmi`: to samo po odjęciu `log P(T)`.
  - `staly_target`: udział rekordów, w których model przy obu kontekstach woli to samo zdanie
    (odpowiednik stałej litery A; remis T1 = T2 to brak wyboru).
  - `margines`: o ile nat kontekst przesuwa zdanie we właściwą stronę.
- **Lista do przeglądu tłumaczenia:** rekordy z |EN − PL| ≥ 0,5, uśrednione po modelach, które po
  angielsku wyraźnie coś umieją (dolna granica CI95 na pełnym EN > 60%; dziś Bielik i LFM3). Lista
  idzie w obie strony: trudniejsze i łatwiejsze po polsku.

| model | rewizja HF | wagi |
|---|---|---|
| SlayerLab/Slayer1B-1.00 … 1.06 | 43e7ca20, 727b5f5e, bf7117b9, fee113ef, 09aa8abf, 21a05bc5, **ef81be58** (= Space) | fp32 (natywnie) |
| speakleash/Bielik-1.5B-v3 | 4b250496 | bf16 → fp32 przy ładowaniu |
| LiquidAI/LFM3-1.7B-Base | 545fc8f4 (wersja Base, bo loglik liczymy bez czatu) | bf16 → fp32 przy ładowaniu |
| OrisTeam/Aster-0.5B | 97691358, podkatalog `fp32/` | fp32 (wariant z repo) |
| ewok-core/ewok-core-1.0 (EN, gated) | 34d912a6 | — |

## Dane

- **PL:** `ewok-pl-complete-0001-0625.zip` (poza repo, hasło jak w oryginale EWoK, TERMS_OF_USE).
  Skrypt czyta plik prosto z zipa. W repo nie ma tekstu rekordów ani ich pochodnych, tylko id i liczby.
- **EN:** `ewok-core/ewok-core-1.0` z HF (wymaga akceptacji warunków), przypięta rewizja.
- **Tłumaczenie:** wersja robocza (`draft_review_required`). *Opis procesu tłumaczenia (kto, czym, zasady,
  polskie odpowiedniki par pojęć) dopisze autor tłumaczenia.*

## Uruchomienie

```bash
# jeden model: PL z zipa + pełny EN (domyślnie --dane pl,en), float32
python benchmarks/ewok-pl/ewok.py licz --model models/Slayer1B-1.06 --zip ewok-pl-complete-0001-0625.zip \
  --wyjscie benchmarks/ewok-pl/results/Slayer1B-1.06
# Aster: wariant fp32 z podkatalogu repo HF, nazwa katalogu wyników z dopiskiem (fp32)
python benchmarks/ewok-pl/ewok.py licz --model models/Aster-0.5B/fp32 --zip ewok-pl-complete-0001-0625.zip \
  --wyjscie "benchmarks/ewok-pl/results/Aster-0.5B(fp32)"
# raport ze wszystkich katalogów w benchmarks/ewok-pl/results/
python benchmarks/ewok-pl/ewok.py analiza --wyniki benchmarks/ewok-pl/results --zip ewok-pl-complete-0001-0625.zip
python tests/test_ewok_pl.py
```

Czas na RTX 5060 Ti (16 GB), PL + pełny EN w float32: ok. 7 min dla modeli 1–1,7B i ok. 2 min dla Astera.
