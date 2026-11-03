# EWoK-PL: wyniki Slayera 1B (2.11.2026, wersja 4: doszedł Aster-0.5B(fp32))

> **W skrócie.** Na angielskim EWoK wynik Slayera rośnie z **53,1 do 58,9%** (1.00 → 1.06, p < 0,001,
> także po korekcie na wszystkie testy). Na polskim EWoK-PL przyrost wynosi **1,0 pkt** (54,4 → 55,4)
> i mieści się w szumie. Na tych samych 625 rekordach po angielsku Slayer zyskuje **+5,0 pkt** (p = 0,02
> po szablonach, ale 0,40 po korekcie Holma na wszystkich 23 kontrastach). Wybór domeny tłumaczy więc
> niski poziom wyniku, a **brak postępu po polsku jest sygnałem, ale nie rozstrzygniętym**. Bielik-1.5B-v3
> ma po polsku **66,0%**, LFM3-1.7B-Base **57,4%**, a Aster-0.5B(fp32) **54,6%**, czyli tyle co Slayer,
> przy losowym wyniku po angielsku (50,7%). EWoK-PL obejmuje na razie tylko domenę `agent-properties`.
>
> Po korekcie na wszystkie testy istotne zostają **trzy wyniki**, każdy z werdyktem „pewne” (SE po szablonach; z i werdykty w raport_ewok.json):
> wzrost Slayera na pełnym EN (+5,7 pkt, SE 0,8 pkt), przewaga Bielika nad Slayerem po polsku
> (+10,6 pkt, SE 2,1 pkt) i spadek LFM3 z EN na PL (−9,3 pkt, SE 2,1 pkt).

Metoda, rewizje modeli i polecenia: [`README.md`](README.md). Wszystkie tabele: [`results/raport_ewok.md`](results/raport_ewok.md).

**Co się zmieniło po recenzji.** Poprawiłem wniosek o domenie i trzy błędy faktu (znak różnicy
LFM3 − Slayer, „wszystkie modele losowe” na parze effort, zakres „stałego targetu”). Doszły CI i p
**po szablonach**: rekordy EWoK to około 5 wypełnień jednego szablonu, więc nie są niezależne. Doszły
też różnica różnic PL − EN, tabela PL vs EN według par i lista przeglądu w obie strony, liczona bez
Slayera. Zaokrąglenia połówek idą teraz w górę (57,5 → 58). W wersji 3 doszły: Holm na wszystkich
kontrastach naraz (`p_holm_wszystkie_po_szablonach`), poprawka o flagach (nie pokrywają się z parami
1:1), odwrotny kierunek LFM3 na „make an effort”, „stały target” na EN625 i dokładne szerokości CI
dla małych grup. W wersji 4 doszedł **Aster-0.5B(fp32)** (OrisTeam/Aster-0.5B, wariant fp32 z repo HF).
Lista przeglądu bierze teraz za odniesienie modele z dolną granicą CI na pełnym EN > 60%, a nie
„wszystko poza Slayerem”, żeby losowy po angielsku Aster nie tłumił sygnału. Dziś to nadal Bielik i LFM3.

---

## 1. Co mierzy EWoK

Każdy rekord to dwa konteksty i dwa zdania. Model ma uznać, że zdanie 1 pasuje do kontekstu 1,
a zdanie 2 do kontekstu 2.

| | treść |
|---|---|
| C1 | Ola widzi kota **w środku**. |
| C2 | Ola widzi kota **na zewnątrz**. |
| T1 | Ola **uważa**, że kot jest w środku. |
| T2 | Ola **wątpi**, że kot jest w środku. |

*(Przykład jest zmyślony i pokazuje sam format. Treści EWoK-PL nie publikujemy.)*

Za każdą parę, w której model woli właściwy kontekst dla danego zdania, dostaje pół punktu, czyli
za rekord 0, 0,5 albo 1. Losowo wychodzi 50%. To samo zdanie stoi po obu stronach porównania, więc
**preferencja litery „A” i długość odpowiedzi nie wpływają na wynik**.

**Szablony.** EWoK wypełnia każdy szablon kilkoma zestawami imion, obiektów i miejsc. Szablony
odtwarzamy z angielskiego oryginału (maskujemy słowa rzadkie w obrębie pary pojęć). 625 rekordów PL
daje 130 szablonów, w większości po 5 rekordów. Przedziały i p „po szablonach” losują całe szablony
i to one są miarodajne. Przedziały po rekordach są za wąskie.

## 2. Wyniki główne

Wynik EWoK w %, losowo 50. Kolumna „CI95” to przedział po szablonach.

| model | PL (625) | CI95 | EN, te same 625 | EN pełny (4374) |
|---|---|---|---|---|
| **Bielik-1.5B-v3** | **66,0** | [61,6; 70,4] | 62,8 | 69,5 |
| **LFM3-1.7B-Base** | 57,4 | [53,5; 61,3] | **66,6** | **69,7** |
| Slayer1B-1.00 | 54,4 | [50,2; 58,6] | 51,3 | 53,1 |
| Slayer1B-1.01 | 53,0 | [49,0; 57,0] | 53,5 | 55,5 |
| Slayer1B-1.02 | 54,4 | [50,3; 58,5] | 52,8 | 57,1 |
| Slayer1B-1.03 | 54,6 | [50,8; 58,3] | 52,0 | 55,8 |
| Slayer1B-1.04 | 56,4 | [53,4; 59,5] | 56,0 | 57,4 |
| Slayer1B-1.05 | 55,6 | [52,3; 59,0] | 57,0 | 58,8 |
| **Slayer1B-1.06** | **55,4** | [51,6; 59,3] | 56,2 | 58,9 |
| Aster-0.5B(fp32) | 54,6 | [51,9; 57,5] | 51,1 | 50,7 |

```
Slayer 1B, 1.00 → 1.06       (1 blok = 1 pkt ponad losowe 50)
EN pełny (4374)   53,1 ███▏        →  58,9 ████████▉     +5,7 pkt, p < 0,001
EN, te same 625   51,3 █▎          →  56,2 ██████▏       +5,0 pkt, p = 0,02 (0,40 po Holmie na wszystkich)
PL (625)          54,4 ████▍       →  55,4 █████▍        +1,0 pkt, p = 0,71
Bielik PL 66,0 · LFM3 PL 57,4 · Aster(fp32) PL 54,6
```

Ścieżka EN nie jest monotoniczna (1.03 spada względem 1.02). CI obejmują tylko losowanie rekordów
i szablonów, nie zmienność samego treningu.

## 3. Najważniejsze wnioski

1. **Po angielsku Slayer rośnie, po polsku przyrost mieści się w szumie.** Na pełnym EN jest
   +5,7 pkt (CI95 po szablonach +4,2…+7,3), na EN625 +5,0 pkt (SE 2,1 pkt, prawdopodobne; p = 0,02, ale po Holmie na
   wszystkich 23 kontrastach p = 0,40), a na PL +1,0 pkt (SE 2,3 pkt, szum). Różnica różnic (przyrost PL − przyrost EN na tych samych rekordach) wynosi
   −4,0 pkt. Po rekordach jest istotna (p = 0,02), ale **po szablonach już nie** (SE 2,5 pkt, szum;
   CI −8,9…+0,9, p = 0,13).
   Brak postępu po polsku może więc wynikać z tłumaczenia, z wolniejszej nauki polskiego albo
   z szumu. Ten zestaw tego nie rozstrzyga. Ciągła miara idzie w tę samą stronę: margines logprob
   (o ile kontekst przesuwa zdanie we właściwą stronę) rośnie podobnie w obu językach,
   +0,11 nat na PL i +0,14 nat na EN625. Postęp jest więc widoczny także po polsku, tylko za słaby,
   żeby zmienić decyzje modelu.
2. **Bielik wyraźnie wygrywa po polsku**: +10,6 pkt nad Slayerem 1.06 (SE 2,1 pkt, pewne;
   CI +6,4…+14,8).
   Obie pary trafia w 42% rekordów, Slayer w 21–25%.
3. **LFM3 nie jest po polsku istotnie lepszy od Slayera**: +2,0 pkt (SE 2,4 pkt, szum), choć po
   angielsku ma 69,7%. Na tych samych rekordach traci po polsku 9,3 pkt względem angielskiego
   (SE 2,1 pkt, pewne; jedyna różnica PL − EN, która przeżywa korektę Holma), co jest śladem
   słabego polskiego. U Bielika (+3,2 pkt, SE 1,8 pkt, szum) i Slayera różnica PL − EN po
   szablonach jest nieistotna. Wartości punktowe leżą od −1,4 do
   +3,2 pkt (to rozrzut wartości, a nie CI), a dolne granice CI po szablonach schodzą do −5,1.
4. **Slayera ciągną w dół dwie pary pojęć**: „make more / less effort” (220 rekordów) i „choose” (165).
   Na obu jest losowy we wszystkich wersjach (48–54). Bez nich Slayer 1.06 ma 64,4%. <!-- liczba-spoza-wynikow: średnia ważona 7 pozostałych par z wg_ConceptA (raport_ewok.json) -->
   Na parze effort
   Bielik (58) i LFM3 (55) są tylko trochę powyżej losowego, ale po angielsku na tych samych rekordach
   mają 63 i 67. Oprócz trudności pary może tu działać tłumaczenie.
5. **Tłumaczenie zmienia trudność w obie strony, i to różnie dla różnych modeli.** „Make an effort /
   make no effort” (45 rekordów) jest po polsku wyraźnie łatwiejsza dla Bielika (90 wobec 68 po
   angielsku) i Slayera 1.00 (87 wobec 59), a trudniejsza dla LFM3 (54 wobec 79). Różnica PL − EN
   Slayera 1.00 (+3,1 pkt, SE 1,5 pkt, prawdopodobne; po Holmie nieistotna) w około
   2,0 pkt pochodzi z tej jednej pary. <!-- ocena-bez-se: rozkład różnicy na pary, SE różnicy podane wyżej --> „Believe / doubt” jest losowa u Bielika (48 w obu
   językach) i większości wersji Slayera, z wyjątkiem Slayera 1.01 po angielsku (59,1 [53,6; 64,5]). <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
   Problem leży więc głównie w samej parze, nie w tłumaczeniu. LFM3 ma na niej po polsku 41,8 [34,5; 49,1], <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
   czyli poniżej losowego w przedziale po rekordach. Na 11 szablonach to słaby dowód.
6. **Slayer mocno trzyma się prioru zdania.** Gdy porównać dwa zdania w tym samym kontekście, Slayer
   po polsku w 80–85% rekordów wybiera to samo zdanie, cokolwiek mówi kontekst. Bielik robi tak w 75%,
   LFM3 w 74%, a losowo wychodzi 50%. Po angielsku Slayer ma 75–82% na tych samych 625 rekordach
   i 70–77% na pełnym EN. To odpowiednik „zawsze A” z testów
   z literami. Reguła EWoK jest na to odporna. Prior spycha jednak w dół metrykę „oba”: Slayer 1.01,
   1.03 i 1.04 mają ją poniżej 25% (górna granica CI95 po rekordach ≤ 24,5), więc 25% nie jest dla niej
   prawdziwym poziomem losowym. <!-- ocena-bez-se: porównanie z poziomem losowym przez CI95, nie różnica modeli -->
7. **Aster-0.5B(fp32) ma po polsku tyle co Slayer, ale po angielsku nic nie umie.** PL 54,6 (CI po
   szablonach 51,9…57,5), czyli −0,7 pkt wobec Slayera 1.06 (p = 0,72). Na pełnym EN ma 50,7%,
   a na dwóch domenach jest wręcz poniżej losowego: `material-dynamics` 46,0 [44,2; 47,8] i <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
   `spatial-relations` 44,7 [40,0; 49,4]. <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
   Różnica PL − EN wynosi +3,5 pkt (SE 1,6 pkt, prawdopodobne) i nie przeżywa korekty Holma. Prior zdania jest u niego najsilniejszy ze wszystkich modeli (stały target 85% po
   polsku, 79% na pełnym EN), a „oba” wynosi 19,5% [16,5; 22,7]. Z par pojęć po polsku wyróżnia się
   „make an effort” (74) i „choose” (56). Na parze effort jest losowy (50), jak Slayer.

## 4. Czego Slayer 1.06 nie umie (EN, według domen)

| domena | n | Slayer 1.00 | **Slayer 1.06** | Bielik | LFM3 | Aster(fp32) |
|---|---|---|---|---|---|---|
| physical-relations | 415 | 50 | **51** [48,1; 54,1] 🔴 | 58 | 58 | 49 |
| physical-interactions | 280 | 52 | **54** | 62 | 61 | 52 |
| agent-properties | 1120 | 51 | **55** [53,2; 57,0] | 65 | 68 | 51 | <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
| spatial-relations | 245 | 54 | **55** | 61 | 61 | 45 ⬇ |
| material-properties | 124 | 54 | 57 | 55 | 58 | 50 |
| social-relations | 785 | 51 | 57 | 68 | 67 | 51 |
| physical-dynamics | 75 | 59 | 61 | 69 | 75 | 60 |
| quantitative-properties | 190 | 63 | 67 | 71 | 66 | 60 |
| material-dynamics | 780 | 53 | **67** 🟢 | 86 | 84 | 46 ⬇ |
| social-properties | 185 | 58 | **68** 🟢 | 83 | 77 | 60 |
| social-interactions | 175 | 69 | 72 | 80 | 84 | 55 |

🔴 to przedział, w którym mieści się wynik losowy. 🟢 to przyrost od 1.00 o co najmniej 10 pkt.
⬇ to CI95 w całości poniżej 50 (Aster). Przedziały są tu po rekordach.

Najsłabsze u Slayera są **relacje fizyczne i przestrzenne**. Losowa jest tylko `physical-relations`,
reszta jest słaba, ale powyżej losowego. U Bielika najsłabsza jest `material-properties` (55).
Największy postęp Slayer zrobił w `material-dynamics` (53 → 67) i `social-properties` (58 → 68).

## 5. Polski i angielski według pary pojęć (te same rekordy)

| para pojęć | n | Bielik PL / EN | LFM3 PL / EN | Slayer 1.00 PL / EN | Slayer 1.06 PL / EN | Aster(fp32) PL / EN |
|---|---|---|---|---|---|---|
| make more / less effort | 220 | 58 / 63 | 55 / 67 | 51 / 50 | 49 / 51 | 50 / 48 |
| choose / – | 165 | 68 / 60 | 62 / 65 | 48 / 49 | 51 / 51 | 56 / 52 |
| intend / not intend | 70 | 79 / 69 | 61 / 71 | 64 / 54 | 65 / 67 | 61 / 46 |
| believe / doubt | 55 | 48 / 48 | 42 / 52 | 50 / 55 | 47 / 48 | 48 / 55 |
| make an effort / make no effort | 45 | **90 / 68** | 54 / 79 | **87 / 59** | 77 / 74 | 74 / 66 |
| hear / not hear | 30 | 83 / 85 | 75 / 83 | 48 / 52 | 85 / 73 | 52 / 47 |
| feel / not feel | 20 | 68 / 60 | 58 / 53 | 60 / 63 | 58 / 48 | 53 / 58 |
| believe / imagine | 10 | 70 / 70 | 50 / 50 | 50 / 40 | 75 / 75 | 50 / 35 |
| have no preference / prefer | 10 | 50 / 70 | 65 / 80 | 50 / 50 | 40 / 85 | 60 / 60 |

Połowa szerokości CI95 po rekordach wynosi ±4 pkt przy 220 rekordach i ±5–9 pkt przy 45. Przy
10 rekordach waha się od ±0 do ±20 pkt. ±0 to przedział zdegenerowany, gdy wszystkie rekordy grupy
mają ten sam wynik, a nie pewność. Po szablonach są szersze: obie grupy po 10 rekordów to tylko 2 i 6 szablonów, a „make more /
less effort” to 51 szablonów. Wartości dla
10–30 rekordów to sygnał do sprawdzenia, a nie wynik.

## 6. Tłumaczenie: co wiemy, a czego nie

- EWoK-PL to **wersja robocza** (`draft_review_required`). 580 z 625 rekordów ma flagę przeglądu.
  Flagi oznaczają **typ wnioskowania** i są skorelowane z parami pojęć, ale nie pokrywają się z nimi 1:1.
  Na przykład `intent_from_action_review` (70 rekordów) to 55 rekordów „intend” i 15 „make an effort”
  (Bielik 75,0 na fladze wobec 79,3 na parze), a `effort_preference_inference_review` (250) to 220 <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
  „make more effort” i 30 „make an effort”. Flagi nie mówią więc, czy tłumaczenie jest dobre. 45 rekordów
  bez flagi nie wypada lepiej (Bielik 53,3 [44,4; 62,2]). Jakość sprawdzi dopiero przegląd przez człowieka. <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
- **Kandydaci do przeglądu.** To rekordy, w których Bielik i LFM3 średnio różnią się między PL a EN
  o co najmniej 0,5. Odniesieniem są tylko modele z dolną granicą CI95 na pełnym EN > 60%. Slayer i Aster
  są po angielsku blisko losowego i tłumiłyby sygnał. Lista idzie w obie strony:
  **51 rekordów jest trudniejszych po polsku, a 30 łatwiejszych**. Identyfikatory są w
  `raport_ewok.json` → `do_przegladu`. Pierwsza lista jest zawyżona przez słaby polski LFM3. To
  kandydaci, a nie wykryte błędy. Poprzednia wersja raportu podawała 3 rekordy, ale filtr opierał się
  wtedy głównie na Slayerze.
- **Brakuje opisu procesu tłumaczenia**: kto tłumaczył, jakim narzędziem, jakie są zasady i polskie
  odpowiedniki par pojęć. Dopisze go autor tłumaczenia. Bez tego żadnego zdania o jakości tłumaczenia
  nie da się w pełni ocenić.

## 7. Ograniczenia

- **Jedna domena** (`agent-properties`, 9 par pojęć, 130 szablonów). Wniosków o fizyce czy przestrzeni
  po polsku z tego zestawu wyciągać nie można.
- **Bez kalibracji z paperem.** Nie uruchomiliśmy tym kodem modeli z papieru EWoK (np. gpt2-xl,
  phi-1.5), więc nie wiemy, czy ewaluator odtwarza ich liczby. Scorer przeszedł test 0 w `common`
  (Pythia/Qwen vs lm-eval), a regułę punktacji sprawdzają testy (`research/tests/test_ewok_pl.py`).
- **Bez skanu kontaminacji.** Dotyczyłaby ona tylko EN, bo EWoK-PL nie był publikowany. Jest więc
  konkurencyjnym wyjaśnieniem zarówno wzrostu Slayera na EN, jak i spadku PL − EN u LFM3. Oryginalny
  EWoK jest szyfrowany właśnie przeciw kontaminacji, ale tego nie sprawdzaliśmy.

## 8. Co dalej

1. Przetłumaczyć pozostałe domeny, zaczynając od `physical-relations`, `spatial-relations`
   i `material-dynamics`, czyli tam, gdzie EN pokazuje u Slayera najmniejszy albo największy postęp.
2. Przejrzeć pary „make more / less effort”, „choose” i „make an effort” oraz listy kandydatów z §6.
   Dopisać do README opis procesu tłumaczenia.
3. Etapy A i B metodologii (zadanie #34): karta oryginału EWoK i odtworzenie wyniku z pracy na modelu z
   opublikowanym wynikiem (np. gpt2-xl, phi-1.5), potem `POLISH.md`.
4. Dodać EWoK-PL do Space SlayerLab/Slayer1B-Benchmarks jako osobne zadanie z metryką `ewok` (%)
   i CI po szablonach.
