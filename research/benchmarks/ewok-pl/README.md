# EWoK-PL: ewaluacja wiedzy o świecie po polsku

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Etapy A–C (karta oryginału, wynik gpt2-xl z pracy
> odtworzony kodem autorów, test zgodności naszego kodu) są w [`../ewok/`](../ewok/README.md). Etap D (wersja polska)
> jest w [`POLISH.md`](POLISH.md). Od wersji 5 wyniki liczymy regułą kodu autorów z `../ewok/ewok.py` (etap C
> tam): tokeny specjalne daje tokenizer, logit pad jest wyłączony. Wcześniejszy tryb, BOS dla każdego modelu, na
> gpt2-xl różnił się od kodu autorów w 15% decyzji. Jego wyniki zostały w `results/raport_ewok_bos.*`. Przepis każdego
> wyniku: [`RECIPE.md`](RECIPE.md). Pojęcia
> (Space, SE, werdykt, CI95): [słowniczek](../../METODOLOGIA.md#słowniczek).

Mierzymy, czy modele wiedzą, co wynika z prostych sytuacji (EWoK, *Elements of World Knowledge*), po
polsku i po angielsku na tych samych rekordach. Stan na 3.11.2026: 10 modeli, czyli Slayer 1B 1.00–1.06,
Bielik-1.5B-v3, LFM3-1.7B-Base i Aster-0.5B(fp32). Zestaw polski to 625 roboczych rekordów z domeny
`agent-properties`.

**Wyniki i wnioski: [`WYNIKI.md`](WYNIKI.md).** Wszystkie tabele z CI i kontrastami:
[`results/raport_ewok.md`](results/raport_ewok.md), dane: [`results/raport_ewok.json`](results/raport_ewok.json).

| model | PL (625) | EN pełny (4374) |
|---|---|---|
| Bielik-1.5B-v3 | 66,0 | 69,5 |
| LFM3-1.7B-Base | 57,4 | 66,0 |
| Aster-0.5B(fp32) | 54,6 | 50,8 |
| Slayer1B-1.00 | 54,1 | 53,0 |
| Slayer1B-1.06 | 54,0 | 59,0 |

Wynik EWoK w %, losowo 50, reguła autorów. Pozostałe wersje Slayera, przedziały i werdykty (po szablonach, po parach
pojęć i po domenach) są w `WYNIKI.md`. Slayer 1.06 to checkpoint z ok. 1/8 treningu, bez wygaszania LR, a pozostałe
modele w tabeli są po pełnym treningu, więc różnice mówią o tym checkpoincie, nie o gotowym Slayerze.

## Pliki

| plik | co robi |
|---|---|
| `ewok.py` | `licz`: logliki 2×2 per rekord dla jednego modelu (domyślnie `--regula autorow` z `../ewok/ewok.py`; `--regula bos`: BOS dla każdego modelu); `analiza`: oceny, CI, kontrasty z odczytem po parach pojęć i domenach, raport |
| `POLISH.md` | etap D: tłumaczenie czy od zera, mapowanie metody, dwie kontrole |
| `WYNIKI.md` | podsumowanie dla zespołu i Arka |
| `results/raport_ewok.{json,md}` | pełny raport, reguła autorów (w repo) |
| `results/raport_ewok_bos.{json,md}` | archiwalny raport wersji 4, tryb BOS dla każdego modelu (w repo, do porównania). Nie jest bieżącym wynikiem; jak `../ewok/results/ewok_plain.json` zostaje w puli bramki liczb, a każda liczba z niego w tekście ma znacznik `liczba-spoza-wynikow` |
| `results/<model>/{pl,en}.jsonl.gz` | logliki per rekord, bez tekstu (w repo; surowe `.jsonl` lokalnie, `.gitignore`). `analiza` czyta `.gz`, gdy nie ma surowego pliku |
| `research/tests/test_ewok_pl.py` | 17 testów czystych funkcji, bez wag i bez danych |

## Protokół

Jest zgodny z paperem EWoK (Ivanova i in. 2024, [arXiv:2405.09605](https://arxiv.org/abs/2405.09605)), tryb LOGPROBS.

- **Rekord:** C1, C2, T1, T2. T1 pasuje do C1, a T2 do C2. Liczymy `log P(T | C)` jako sumę logprob tokenów
  `" " + T` po kontekście `C`.
- **Reguła główna (target stały):** `s1 = [P(T1|C1) > P(T1|C2)]`, `s2 = [P(T2|C2) > P(T2|C1)]`,
  `wynik = (s1+s2)/2`. Losowo wychodzi 50%, remis liczy się jako pudło. Po obu stronach porównania
  jest ten sam napis T, więc prior litery i długości odpowiedzi (główny problem z
  [analizy formatu odpowiedzi](../../analyses/answer-format/README.md)) się tu nie pojawia.
- **Scorer:** reguła autorów z `../ewok/ewok.py` (`authors_pair`, `logliks`; forward `slayer_model.py` dla
  Slayera). Zapytanie `f"{C} {T}"` i kontekst tokenizujemy z tokenami specjalnymi tokenizera, jak `surprisal`. BOS
  dostają więc tylko modele, których tokenizer go dokleja (Bielik, Aster). Aster dokleja też EOS, który w tej regule
  wchodzi do sumy zdania. Logit pad jest wyłączony przed softmaxem. Bez szablonu czatu. Tryb `--regula bos` (jeden
  BOS dla każdego modelu, METHOD.md Space, przez `common/hipoteza_formatu.py`) to dodatkowy sposób liczenia.
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
    całego szablonu naraz. SE po szablonach na 625 rekordach PL jest większe niż w oryginale na 4374
    rekordach (`../ewok/README.md`), więc według wiersza `+pl` [tabeli typów](../../METODOLOGIA.md#typy-testów)
    EWoK-PL wchodzi do meta-oceny jako kolumna informacyjna.
  - **Po parach pojęć i po domenach:** pary pojęć (9 w PL) i domeny (11 w EN) jako klastry: średnia z różnic
    grup, SE = sd / √k, t przy df = k − 1 (`po_parach`, `po_domenach`), jak paradygmaty w `../blimp/`.
  - **Korekta Holma:** w każdej rodzinie kontrastów (`p_holm_po_szablonach`), na wszystkich kontrastach
    trafności naraz (`p_holm_wszystkie_po_szablonach`, 23 testy) i osobno dla odczytu po parach i po domenach
    (`p_holm_wszystkie`, `werdykt_po_holmie`). Za istotne w `WYNIKI.md` uznajemy tylko to, co przeżywa korektę
    na wszystkich kontrastach. <!-- ocena-bez-se: opis reguły, nie porównanie -->
  - **Remisy i bazy:** liczba remisów per model i zbiór (`remisy`, w float32 zero), baza losowa 0,5, baza
    większościowa nie dotyczy (`protokol`).
- **Kontrasty:** PL vs EN na tych samych `source_id`, kolejne wersje Slayera, Slayer 1.06 vs 1.00 (PL,
  EN625, EN), różnica różnic (PL 1.06 − PL 1.00) − (EN 1.06 − EN 1.00) per rekord, inne modele vs Slayer 1.06
  i margines Slayera 1.06 vs 1.00 (PL, EN625; osobna rodzina, poza Holmem trafności).
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
# jeden model: PL z zipa + pełny EN (domyślnie --dane pl,en), float32, reguła autorów (domyślne --regula autorow)
python benchmarks/ewok-pl/ewok.py licz --model models/Slayer1B-1.06 --zip ewok-pl-complete-0001-0625.zip \
  --wyjscie benchmarks/ewok-pl/results/Slayer1B-1.06
# Aster: wariant fp32 z podkatalogu repo HF, nazwa katalogu wyników z dopiskiem (fp32)
python benchmarks/ewok-pl/ewok.py licz --model models/Aster-0.5B/fp32 --zip ewok-pl-complete-0001-0625.zip \
  --wyjscie "benchmarks/ewok-pl/results/Aster-0.5B(fp32)"
# raport ze wszystkich katalogów w benchmarks/ewok-pl/results/
python benchmarks/ewok-pl/ewok.py analiza --wyniki benchmarks/ewok-pl/results --zip ewok-pl-complete-0001-0625.zip
python tests/test_ewok_pl.py
```

Czas na RTX 5060 Ti (16 GB), PL + pełny EN w float32, `--batch 8`: ok. 4–5 min na model (przebieg 3.11.2026).
