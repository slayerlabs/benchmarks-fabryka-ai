# Testy danych na Slayer 1B (udział EN, jakość PL) — progi zapisane PRZED treningiem

Zapisane 30.10.2026, przed wynajmem kart, przed przygotowaniem danych na instancji i przed jakimkolwiek
wynikiem. Po zobaczeniu wyników progów, metryk, agregatów ani listy testów nie zmieniamy.

**Zmiana 30.10.2026 po dwóch recenzjach planu (przed wynajmem, przed jakimkolwiek pomiarem):**
test 1 rozstrzyga BPB (heldout EN i poprawna odpowiedź), nie trafność; „bez kosztu PL” wymaga górnej
granicy 95% CI poniżej tolerancji ustalonej niżej; szuflada sprawdza także werdykty „szkodzi” i
potwierdza tylko ruchem w kierunku werdyktu; wszystkie ramiona z liniowym wygaszaniem LR na K
krokach; czwarte ramię C2 (C z inną kolejnością dokumentów) mierzy szum kolejności; K = 120 → 100,
żeby 4 ramiona zmieściły się w 10 $.

## Pytania

- **Test 1 (udział EN):** czy podniesienie udziału EN z 10% do 25% (te same źródła: fineweb-edu + finemath
  z `shared/en.parquet`) poprawia modelowanie angielskiego i poprawnych odpowiedzi ARC-E, MMLU i SIQA
  BEZ kosztu dla polskiego?
- **Test 2 (jakość PL):** czy zastąpienie webu HPLT v3 (pakiet `pack-07`) tą samą liczbą tokenów
  z FineWeb2-HQ `pol_Latn` (`epfml/FineWeb2-HQ`, ODC-By, górne 10% FineWeb2 wg klasyfikatora
  na osadzeniach XLM-R) obniża BPB polskiego tekstu spoza obu źródeł webowych i poprawia polskie testy?

## Ramiona (4; kontrola i ramię szumu wspólne dla obu testów)

| ramię | web | core | legal | EN | kolejność dokumentów |
|---|---|---|---|---|---|
| **C** (kontrola, mieszanka Arka, scenariusz B) | 63% HPLT pack-07 | 19% | 8% | 10% | klucz k1 |
| **C2** (szum kolejności) | jak C (te same dokumenty) | | | | klucz k2 |
| **E25** | 52,5% HPLT pack-07 | 15,83% | 6,67% | 25% | klucz k1 |
| **PLHQ** | 63% FineWeb2-HQ pol | 19% | 8% | 10% | klucz k1 |

E25 zabiera 15 pp z PL proporcjonalnie (web:core:legal zostaje 63:19:8), więc jedyną zmianą jest udział EN.

Wspólne dla ramion:
- Start: `SlayerLab/Slayer1B-1.06-checkpoints/ckpt_13848.pt` (wagi + stan Muon/AdamW) przez `--resume`
  z `<out-dir>/ckpt.pt`. Log każdego ramienia MUSI zawierać `RESUME @ 13848`; model do ewaluacji
  powstaje wyłącznie z końcowego `ckpt.pt` (plik, nie dowiązanie) o kroku == 13848 + K, a
  `porownaj_ramion.py` odmawia, gdy krok w wynikach heldoutu albo ewaluacji jest inny.
- Trener `train_gpt_ref_r23.py` (1.06, rewizja ef81be58) z łatką `wygaszanie/latka_trenera.py`, flagi
  jak w przebiegu wygaszania (`ramie.sh` na instancji 58351985): batch 256 × 4096 z `--grad-accum 128`,
  `--dtype uint16`, `--data-seed 20261023`, `--sampler random`, Muon, architektura z 1.06.
- **LR: liniowo od 6e-4 w kroku 13848 do 0 w kroku 13848 + K** (`WYGASZANIE_SCHED=liniowa`,
  `WYGASZANIE_START=13848`), identycznie we wszystkich ramionach. Harmonogram jest stały między
  ramionami, więc różnice ramion to dalej efekt danych.
- Dane: `dane_ramion.py`, seed 20261030. Każdy plik źródłowy ma własną, deterministyczną pulę
  dokumentów; ramię bierze jej PREFIKS. C, C2 i PLHQ mają identyczne dokumenty core/legal/en; E25 ma
  podzbiór dokumentów PL z C i nadzbiór dokumentów EN z C. Kolejność dokumentu w `train.bin` wyznacza
  klucz z (seed kolejności, treść dokumentu): wspólne dokumenty C, E25 i PLHQ stoją w tym samym porządku
  względnym. `train.bin` ma we wszystkich ramionach tę samą długość (1,28 × tokeny treningu, 135 mln
  przy K = 100). Sampler losuje okna z całego pliku, więc te same batche nie są możliwe; resztkowy
  szum kolejności mierzy C2.
- Dekontaminacja: dokumenty z 13-gramem słów wspólnym z którymkolwiek testem (główne i szuflada,
  w tym arkusze CKE z LLMzSzŁ) usuwane ze WSZYSTKICH pul przed tokenizacją.
- Dedup PLHQ wobec HPLT: szkic próbkowanych 13-gramów (hash % 16 == 0) ze WSZYSTKICH 8 pakietów webu
  `slayer-pl-8x3b` (Arek mógł widzieć każdy). Dokument FineWeb2-HQ z ≥ 50% próbek w szkicu wypada.
  Dokument z < 4 próbkami (krótszy niż ok. 70 słów) zostaje i jest liczony jako `ok_niesprawdzony`.

## K i budżet

- **K = 100 kroków** (104,9 mln tokenów na ramię, 0,72% treningu Arka do kroku 13848).
- Reguła, gdy rozbieg wypadnie inaczej (zapis w README przed treningiem ramion):
  K = min(100, ⌊(L − P − E) / 2 / s_krok⌋ − 7), gdzie L = limit bezpiecznika (39 600 s), P = czas do
  startu rundy 1, E = 6300 s na ewaluację po rundzie 2 i pakowanie, s_krok = zmierzony czas kroku,
  7 kroków ≈ start trenera (wczytanie checkpointu, kompilacja). **K < 70 = nie trenujemy.**
- Limit kosztu ≤ 10 $ za partię. Bezpiecznik `po 39600` (11 h × 0,85 $/h = 9,35 $ maksymalnie).

## Metryki

**Loss i BPB heldoutu** (`heldout_bpb.py`): wspólny heldout dla wszystkich ramion i baz (13800, 13848),
okna 4096 tokenów w obrębie komponentu, fp32. BPB = suma straty / (ln 2 · bajty UTF-8 celów okna).
Komponenty: `web_hplt`, `web_hq`, `core`, `legal`, `en:<source_id>`. Jeżeli `shared/en.parquet` nie ma
kolumny `source_id` (sprawdzane na instancji, `statystyki.json` → `en_komponenty`), EN jest jednym
komponentem `en:brak` i raport per źródło EN odpada; agregat EN liczy się tak samo.
Agregaty (wagi stałe, z mieszanki kontroli):
- **PL_neutralny** = core 19 : legal 8 (polski spoza obu źródeł webowych, oba ramiona trenują na nim tak samo);
- **PL_mix** = web_hplt 63 : core 19 : legal 8;
- **PL_hplt**, **PL_hq** (pojedyncze komponenty, raportowane jako krzyżowe, nie decydują);
- **EN** = komponenty `en:*`, wagi wg liczby okien.

SE(Δ) i 95% CI (percentyle 2,5 i 97,5) z bootstrapu 10 000, parowanego (te same okna dla obu modeli),
warstwowanego po komponentach, seed 20261028.

**Szum:** Z2 = |BPB(ckpt_13800) − BPB(ckpt_13848)| (trajektoria) i **Zk = |BPB(C2) − BPB(C)|** (kolejność
danych przy tym samym składzie i harmonogramie; to wprost rozkład zerowy różnicy dwóch ramion, jedna
próbka). Szum = max(Z2, Zk) na danym agregacie.

**Próg loss:** „spadek”/„wzrost”, gdy |Δ| > 2·SE(Δ) ORAZ |Δ| ≥ max(3·szum, 1% BPB kontroli). Inaczej
„nierozstrzygnięte” (nie „brak efektu”).

**Benchmarki** (`ewal_ramion.py`, scorer `common/hipoteza_formatu.py`, wiersz na pytanie). Metryka
decydująca to **BPB poprawnej odpowiedzi** (−loglik poprawnej / (ln 2 · bajty), niżej = lepiej): przy
1B trafność stoi w miejscu, gdy model wyraźnie się poprawia (1.03 → 1.06 na ARC-C cloze: acc_norm
Δ = +0,0017, SE 0,0106; BPB poprawnej Δ = −0,084, SE 0,0056). Trafność (acc_norm, dla liter i par acc)
tylko raportujemy, poza MultiBLiMP (para minimalna: acc jest miarą zadania).

| zadanie | język | shoty | decyduje |
|---|---|---|---|
| ARC-Easy test, cloze | EN | 0 | BPB poprawnej |
| MMLU test (`cais/mmlu` all), cloze | EN | 5 (dev przedmiotu, jak lm-eval) | BPB poprawnej |
| Social IQa validation, cloze | EN | 0 | BPB poprawnej |
| Belebele `pol_Latn`, cloze | PL | 0 | BPB poprawnej |
| MultiBLiMP `pol` | PL | — (para minimalna) | acc |
| ARC-Challenge cloze, Belebele litery | EN / PL | 0 | tylko raport |

Ruch testu: |Δ| > 2·SE(Δ) (parowany bootstrap po pytaniach, 10 000, seed 20261028) ORAZ |Δ| > 2·Zk
tego zadania (|C2 − C| na tej samej metryce). Inaczej 0.

## Werdykty (liczy `porownaj_ramion.py --K 100`, zapis w `werdykt_glowny.json`)

**Test 1, E25 vs C:**
- **EN pomaga** = „spadek” BPB na agregacie EN ORAZ BPB poprawnej w dół w co najmniej 2 z 3 zadań
  (ARC-E, MMLU-5shot, SIQA) ORAZ żadne z nich w górę.
- **Koszt PL:**
  - „jest”: „wzrost” BPB PL_mix albo Belebele-PL (BPB poprawnej) / MultiBLiMP-PL (acc) istotnie gorzej;
  - „brak”: **górna granica 95% CI Δ BPB PL_mix < tolerancja = 1% BPB kontroli na PL_mix** i żaden test
    PL gorzej. Uzasadnienie tolerancji: to ta sama wielkość, którą w całym planie uznajemy za najmniejszy
    efekt praktyczny (próg „spadek”/„wzrost”), więc koszt PL mniejszy niż najmniejszy zysk, który
    w ogóle zgłaszamy, uznajemy za pomijalny. Ustalona przed pomiarem; jeśli 95% CI okaże się szersze niż
    tolerancja, wynik brzmi „koszt PL nierozstrzygnięty”, a tolerancji nie poszerzamy;
  - inaczej „nierozstrzygnięty” (brak wykrycia to NIE brak kosztu).
- Werdykty: **„EN pomaga bez kosztu PL”**, **„EN pomaga kosztem PL”**, **„EN pomaga, koszt PL
  nierozstrzygnięty”**, **„EN szkodzi EN”** (spadek któregoś z testów EN albo wzrost BPB EN),
  **„szkodzi PL bez zysku EN”**, inaczej **„nierozstrzygnięte”**.

**Test 2, PLHQ vs C:**
- loss = werdykt na **PL_neutralny**; testy PL = Belebele-PL (BPB poprawnej), MultiBLiMP-PL (acc).
- **„PL-HQ pomaga (loss i testy)”**: spadek BPB PL_neutralny, co najmniej jeden test PL lepiej, żaden gorzej.
- **„PL-HQ obniża loss PL”**: spadek BPB PL_neutralny, testy PL w szumie.
- **„PL-HQ szkodzi”**: wzrost BPB PL_neutralny albo test PL gorzej bez spadku loss.
- inaczej **„nierozstrzygnięte”**. PL_hplt i PL_hq raportujemy osobno (krzyż oczekiwany, nie decyduje).

## Szuflada testów niewidzianych (BETR)

Testy, których nie oglądamy przed werdyktem głównym: **HellaSwag** val i **PIQA** val (EN, cloze),
**Global-MMLU `pl`** (5-shot cloze z dev) i **LLMzSzŁ** (egzaminy CKE 2002-2024, cloze) (PL). Metryka jak
w testach głównych: BPB poprawnej, ruch przy |Δ| > 2·SE (C2 nie ma ewaluacji szuflady, więc bez Zk).
Liczone na instancji do osobnego katalogu i archiwum, pobierane na komputer lokalny nierozpakowane;
`porownaj_ramion.py --szuflada` odmawia bez `werdykt_glowny.json` i zapisuje jego sha256.

Kierunek oczekiwany wynika z werdyktu, osobno dla języka: test 1 EN (+1 przy „pomaga”, −1 przy „szkodzi
EN”), test 1 PL (0 przy „bez kosztu”, −1 przy „kosztem PL” i „szkodzi PL”), test 2 PL (+1 przy „pomaga”/
„obniża”, −1 przy „szkodzi”). Status:
- **potwierdzony**: co najmniej jeden test szuflady w tym języku rusza się w oczekiwanym kierunku i żaden
  przeciwnie (dotyczy też werdyktów „szkodzi”);
- **sprzeczny**: któryś rusza się przeciwnie (dla kierunku 0: któryś gorzej);
- **niepotwierdzony (szuflada w szumie)**: nic się nie rusza — sam brak sprzeczności nie potwierdza;
- dla kierunku 0 bez pogorszenia: **zgodny (brak pogorszenia)**.

## Czy wniosek się skaluje (co powie o 11B, a czego nie)

Cel: przepis danych na model większy niż 1B, docelowo lepszy od Bielika 11B. Ten test to krótka
(K = 100 kroków, 105 mln tokenów) końcowa faza treningu z wygaszaniem LR na zmienionej mieszance,
startująca z modelu po pełnej epoce na mieszance Arka.

**Co faktycznie mierzymy:** efekt składu danych **w fazie wygaszania** (annealingu). To ten sam typ
eksperymentu, którym duże laby oceniają jakość źródeł danych przed dołożeniem ich do mieszanki: krótki
anneal na badanej mieszance, porównanie z annealem na mieszance bazowej. Wygaszanie wzmacnia wpływ
ostatnio widzianych danych, więc różnice między ramionami są większe niż przy stałym LR na tej samej
liczbie kroków (i dlatego zmieniliśmy stały LR na wygaszanie po recenzji).

**Powie (z zastrzeżeniem):**
- **Czy dane nadają się do fazy końcowej większego modelu.** Kierunek efektu źródła w annealu i ranking
  źródeł zwykle utrzymują się między skalami, a ciągłe metryki (BPB, BPB poprawnej) przewidują ten
  ranking lepiej niż trafność przy 1B (DataDecide, Magnusson i in. 2025; w naszym labie niezweryfikowane).
- **Koszt PL przy większym udziale EN jako górne oszacowanie** dla tej fazy: interferencja języków
  rośnie, gdy model ma mało pojemności, więc szkoda PL przy 1B jest raczej większa niż przy 11B.

**Nie powie:**
- **Jaki skład ma mieć CAŁY trening 11B.** Faza końcowa mierzy świeże dane na gotowym modelu, nie skład
  całego pretreningu: 25% EN przez cały trening działa inaczej niż 25% EN w ostatnich 0,7% kroków
  (inna liczba powtórzeń, inna pojemność wolna na wiedzę).
- **Optymalnego udziału EN dla 11B.** Gu i in. 2025 (arXiv 2505.18091): przejścia fazowe w przyswajaniu
  wiedzy, krytyczny udział danych bogatych w wiedzę zależy potęgowo od rozmiaru modelu. Brak zysku przy
  1B nie wyklucza zysku przy 11B i odwrotnie.
- **Efektu „świeżości” oddzielonego od jakości** dla PLHQ: FineWeb2-HQ po dedupie jest dla modelu nowy,
  pack-07 mógł być widziany. Dlatego decyduje PL_neutralny, nie PL_hq.
- **Porównania z Bielikiem 11B**: inny tokenizer, start i skala danych. Porównujemy przepisy, nie modele.
- **Testów MC przy 1B** jako wiedzy: blisko losowej, dlatego decyduje BPB poprawnej odpowiedzi.

**Reguła przeniesienia na większy model:** wniosek idzie do przepisu (fazy końcowej) 11B tylko, gdy
(1) werdykt rozstrzygający przechodzi progi, (2) szuflada „potwierdzony” (dla „bez kosztu PL”: „zgodny”).
Każdy inny wynik idzie do rejestru jako obserwacja 1B z nazwanym ograniczeniem, nie jako przepis.

## Zakłócenia znane z góry

- **Powtórki:** nie wiemy, które dokumenty pack-07, core, legal i en Arek już widział (1 epoka do kroku
  13848). Wszystkie ramiona mają to samo zakłócenie w core/legal.
- **Dedup przybliżony:** szkic 1/16 13-gramów; dokumenty krótsze niż ok. 70 słów nie są sprawdzane.
  Udział usuniętych i niesprawdzonych z `statystyki.json` raportujemy obok wyniku.
- **MultiBLiMP i MMLU:** zdania i pytania krótsze niż 13 słów nie dają 13-gramów, więc nie filtrują danych.
- **Zk z jednej próbki:** jedna para C/C2 to jedna obserwacja szumu kolejności; próg 3·szum i 2·Zk na
  benchmarkach jest dlatego konserwatywny, ale sam Zk może przypadkiem wyjść mały.
- **Sprzęt:** 1 karta na ramię z akumulacją gradientu zamiast 8× L40S (jak w wygaszaniu).
- **Wariant „zagęszczony” EN (2505.18091) i finepdfs-edu `pol_Latn`:** poza tą partią (budżet; PDF to inny
  gatunek niż web, mierzyłby gatunek razem z jakością).
