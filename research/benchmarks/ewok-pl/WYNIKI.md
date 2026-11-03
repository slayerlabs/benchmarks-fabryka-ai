# EWoK-PL: wyniki Slayera 1B (3.11.2026, wersja 5: reguła autorów EWoK)

> **W skrócie.** Wszystkie 10 modeli przeliczyliśmy regułą kodu autorów EWoK (`../ewok/`, etap C): tokeny specjalne
> daje tokenizer, a logit pad jest wyłączony. Wcześniejsze wersje dawały każdemu modelowi BOS, a na gpt2-xl ten tryb
> różnił się od kodu autorów w 15% decyzji. Każdy werdykt podajemy w trzech odczytach: po szablonach (te rekordy),
> po parach pojęć (9 par PL) i po domenach (11 domen EN) jako klastrach, z Holmem na wszystkich kontrastach.
>
> - Na angielskim EWoK Slayer rośnie z **53,0 do 59,0%** (1.00 → 1.06, +6,0 pkt, SE 0,8 pkt), z werdyktem **pewnym
>   we wszystkich trzech odczytach**, także po Holmie.
> - Na polskim EWoK-PL zmiana wynosi **−0,1 pkt** (54,1 → 54,0, SE 2,2 pkt, szum). Na tych samych 625 rekordach po
>   angielsku jest +3,8 pkt (SE 2,0 pkt, szum), więc brak postępu po polsku nie jest rozstrzygnięty.
> - **Bielik-1.5B-v3** ma po polsku **66,0%**, +12,0 pkt nad Slayerem 1.06: pewne po szablonach, ale po 9 parach
>   pojęć szum (t = 2,26, p = 0,053).
> - LFM3-1.7B-Base ma po polsku 57,4%, Aster-0.5B(fp32) 54,6%. Żadna różnica PL − EN nie wychodzi poza szum.
> - EWoK-PL obejmuje na razie tylko domenę `agent-properties`.

Metoda, rewizje modeli i polecenia: [`README.md`](README.md). Wszystkie tabele: [`results/raport_ewok.md`](results/raport_ewok.md).
Poprzedni tryb (BOS dla każdego modelu) został w [`results/raport_ewok_bos.md`](results/raport_ewok_bos.md).

**Co się zmieniło w wersji 5.**
- **Reguła liczenia.** Liczymy regułą autorów. U Bielika to nic nie zmienia, bo jego tokenizer sam dokleja BOS
  (0 zmienionych decyzji). U Slayera, LFM3 i Astera zmienia się 10–25% decyzji. Średnia PL u LFM3 i Astera wychodzi
  taka sama jak przed zmianą, a EN625 u LFM3 spada z 66,6 do 59,3%. <!-- liczba-spoza-wynikow: raport_ewok_bos.json (tryb BOS) i porównanie plików per rekord -->
- **Wniosek, który upadł.** Spadek LFM3 z EN na PL, wcześniej −9,3 pkt i pewny, to teraz −1,8 pkt, szum. Był skutkiem <!-- liczba-spoza-wynikow: raport_ewok_bos.json, kontrast PL vs EN LFM3 w trybie BOS -->
  BOS dodanego LFM3 po angielsku.
- **Nowe pola w raporcie.** Doszły odczyty po parach pojęć i po domenach z Holmem, liczba remisów (0 we wszystkich
  przebiegach float32) i baza większościowa („nie dotyczy”, sekcja 1).
- **Kalibracja z pracą.** Zdjęliśmy zastrzeżenie „bez kalibracji z paperem”. Wynik gpt2-xl z pracy odtworzono kodem
  autorów, a nasz kod się z nim zgadza (`../ewok/REPRODUCTION.md`).

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

**Bazy.** Losowa wynosi 0,5. Większościowa nie dotyczy, bo nie ma opcji do wybrania. Model, który zawsze woli ten
sam kontekst albo to samo zdanie, dostaje dokładnie 0,5. Remisów log P nie było w żadnym przebiegu (float32).

**Szablony.** EWoK wypełnia każdy szablon kilkoma zestawami imion, obiektów i miejsc. Szablony
odtwarzamy z angielskiego oryginału (maskujemy słowa rzadkie w obrębie pary pojęć). 625 rekordów PL
daje 130 szablonów, w większości po 5 rekordów. Przedziały i p „po szablonach” losują całe szablony
i to one są miarodajne. Przedziały po rekordach są za wąskie.

## 2. Wyniki główne

Wynik EWoK w %, losowo 50. Kolumna „CI95” to przedział po szablonach. Reguła autorów, float32.

| model | PL (625) | CI95 | EN, te same 625 | EN pełny (4374) |
|---|---|---|---|---|
| **Bielik-1.5B-v3** | **66,0** | [61,6; 70,4] | 62,8 | **69,5** |
| LFM3-1.7B-Base | 57,4 | [54,2; 60,7] | 59,3 | 66,0 |
| Slayer1B-1.00 | 54,1 | [49,9; 58,3] | 52,6 | 53,0 |
| Slayer1B-1.01 | 53,8 | [49,8; 57,8] | 54,5 | 55,4 |
| Slayer1B-1.02 | 53,0 | [49,2; 56,8] | 53,4 | 56,2 |
| Slayer1B-1.03 | 55,4 | [51,8; 59,1] | 54,0 | 56,6 |
| Slayer1B-1.04 | 56,2 | [53,3; 59,3] | 55,5 | 57,4 |
| Slayer1B-1.05 | 54,8 | [51,3; 58,4] | 55,4 | 58,4 |
| **Slayer1B-1.06** | **54,0** | [50,1; 58,0] | 56,5 | 59,0 |
| Aster-0.5B(fp32) | 54,6 | [51,5; 57,8] | 51,7 | 50,8 |

EN pełny dla Slayera 1.06, Bielika i LFM3 to te same pliki co w `../ewok/`. Ścieżka EN nie jest monotoniczna, ale
żaden krok między kolejnymi wersjami nie wychodzi poza szum. CI obejmują tylko losowanie rekordów i szablonów, a
nie zmienność samego treningu.

## 3. Najważniejsze wnioski

Każdy wniosek ma trzy odczyty:
- **po szablonach:** z;
- **po parach pojęć:** t, k = 9 dla PL i EN625, k = 177 dla pełnego EN;
- **po domenach:** t, k = 11, tylko pełny EN.

Holm idzie na wszystkich 23 kontrastach trafności naraz. Werdykty w kolumnach „po parach” i „po domenach” są po
Holmie.

| twierdzenie | różnica | SE (szablony) | po szablonach | po parach | po domenach |
|---|---:|---:|---|---|---|
| Slayer 1.06 − 1.00, EN pełny | +6,0 pkt | 0,8 | z = 7,78, pewne | t = 7,06, pewne | t = 4,58, pewne |
| Slayer 1.06 − 1.00, EN625 | +3,8 pkt | 2,0 | z = 1,90, szum | t = 1,88, szum | — |
| Slayer 1.06 − 1.00, PL | −0,1 pkt | 2,2 | z = −0,04, szum | t = 0,72, szum | — |
| różnica różnic PL − EN625 (1.06 − 1.00) | −3,9 pkt | 2,6 | z = −1,51, szum | t = −0,74, szum | — |
| Bielik − Slayer 1.06, PL | +12,0 pkt | 2,1 | z = 5,82, pewne | t = 2,26, szum | — |
| LFM3 − Slayer 1.06, PL | +3,4 pkt | 2,1 | z = 1,62, szum | t = −0,39, szum | — |
| LFM3 PL − EN625 | −1,8 pkt | 1,7 | z = −1,05, szum | t = −1,43, szum | — |
| Aster − Slayer 1.06, PL | +0,6 pkt | 1,8 | z = 0,31, szum | t = −0,69, szum | — |

1. **Po angielsku Slayer rośnie, po polsku zmiany nie widać.** Wzrost na pełnym EN (+6,0 pkt) trzyma się we
   wszystkich odczytach: po szablonach, po 177 parach pojęć i po 11 domenach (p = 0,0010), także po Holmie. Na tych
   samych 625 rekordach, z których jest PL, przyrost po angielsku (+3,8 pkt), po polsku (−0,1 pkt) i różnica różnic
   (−3,9 pkt) to szum. Ten zestaw nie rozstrzyga, czy Slayer uczy się polskiego wolniej.
2. **Ciągła miara też tego nie rozstrzyga.** Margines mówi, o ile nat kontekst przesuwa zdanie we właściwą stronę.
   - Na PL rośnie o 0,113 nat (SE 0,119 nat, z = 0,94, szum).
   - Na EN625 rośnie o 0,116 nat (SE 0,066 nat, z = 1,75, szum).
   - Po parach pojęć oba przyrosty to też szum (t = 1,92 i t = 2,34, df = 8).
   Wcześniejsze zdanie „postęp widoczny także po polsku” nie miało SE i werdyktu. Z nimi to szum, więc je zdejmujemy.
3. **Bielik wygrywa po polsku, ale nie równo na wszystkich parach pojęć.** Ma +12,0 pkt nad Slayerem 1.06 (CI po
   szablonach +8,0…+16,1, pewne). Po 9 parach pojęć jako klastrach to szum (p = 0,053), więc przewaga opiera się na
   części par. Obie pary porównań Bielik trafia w 42% rekordów, Slayer w 19–23%.
4. **LFM3 po polsku nie odstaje od swojego angielskiego.** PL − EN625 = −1,8 pkt (szum). W trybie BOS wychodziło
   −9,3 pkt, ale tamten wynik brał się z BOS dodanego LFM3 po angielsku. Jego tokenizer sam BOS nie dokleja. U żadnego <!-- liczba-spoza-wynikow: raport_ewok_bos.json, kontrast PL vs EN LFM3 w trybie BOS -->
   modelu różnica PL − EN nie wychodzi poza szum w żadnym odczycie.
5. **Slayera ciągną w dół dwie pary pojęć**: „make more / less effort” (220 rekordów, PL 50) i „choose” (165, PL 49). <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
   Bez nich Slayer 1.06 ma po polsku 61,2%. Na parze effort Bielik (57) i LFM3 (56) są niewiele powyżej losowego. <!-- liczba-spoza-wynikow: średnia ważona 7 pozostałych par z wg_ConceptA i grupy wg_* (raport_ewok.json) -->
   To opis bez werdyktu: odczyt po parach w sekcji 3 nie pokazuje różnicy między parami.
6. **Slayer mocno trzyma się prioru zdania.** Przy dwóch zdaniach w tym samym kontekście Slayer po polsku w 81–86%
   rekordów wybiera to samo zdanie, cokolwiek mówi kontekst. Bielik robi tak w 75%, LFM3 w 81%, a Aster w 85%. <!-- liczba-spoza-wynikow: raport_ewok.json, staly_target per model -->
   Losowo wychodzi 50%. Reguła EWoK jest na to odporna, ale prior spycha w dół metrykę „oba”.
7. **Aster-0.5B(fp32) ma po polsku tyle co Slayer (+0,6 pkt, szum), a po angielsku jest przy losowym (50,8%).**

## 4. Czego Slayer 1.06 nie umie (EN, według domen)

| domena | n | Slayer 1.00 | **Slayer 1.06** | Bielik | LFM3 | Aster(fp32) |
|---|---|---|---|---|---|---|
| physical-relations | 415 | 50 | **50** [47,1; 52,7] 🔴 | 58 | 60 | 49 | <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
| physical-interactions | 280 | 53 | 55 | 62 | 62 | 52 |
| agent-properties | 1120 | 51 | 55 | 65 | 62 | 51 |
| social-relations | 785 | 50 | 57 | 68 | 63 | 50 |
| spatial-relations | 245 | 52 | 57 | 61 | 55 | 46 |
| material-properties | 124 | 51 | 60 | 55 | 58 | 52 |
| physical-dynamics | 75 | 57 | 61 | 69 | 71 | 57 |
| social-properties | 185 | 60 | 66 | 83 | 72 | 60 |
| quantitative-properties | 190 | 65 | 66 | 71 | 69 | 58 |
| material-dynamics | 780 | 53 | **67** 🟢 | 86 | 79 | 47 |
| social-interactions | 175 | 61 | 71 | 80 | 76 | 56 |

🔴 to przedział (po rekordach), w którym mieści się wynik losowy. 🟢 to przyrost od 1.00 o co najmniej 10 pkt.
Wartości per domena to opis bez werdyktu. Werdykt dla domen razem (Slayer 1.06 − 1.00) jest w sekcji 3, a różnice
Slayer 1.06 − model per domena z Holmem są w `../ewok/README.md`.

## 5. Polski i angielski według pary pojęć (te same rekordy)

| para pojęć | n | Bielik PL / EN | LFM3 PL / EN | Slayer 1.00 PL / EN | Slayer 1.06 PL / EN | Aster(fp32) PL / EN |
|---|---|---|---|---|---|---|
| make more / less effort | 220 | 57 / 62 | 56 / 56 | 52 / 49 | 50 / 53 | 49 / 49 | <!-- liczba-spoza-wynikow: raport_ewok.json, grupy wg_* (bramka pomija grupy EWoK) -->
| choose / – | 165 | 68 / 60 | 61 / 63 | 49 / 50 | 49 / 50 | 55 / 52 |
| intend / not intend | 70 | 79 / 69 | 62 / 59 | 61 / 56 | 56 / 64 | 58 / 49 |
| believe / doubt | 55 | 48 / 48 | 43 / 49 | 48 / 57 | 45 / 50 | 53 / 53 |
| make an effort / make no effort | 45 | 90 / 68 | 61 / 68 | 88 / 71 | 78 / 72 | 74 / 62 |
| hear / not hear | 30 | 83 / 85 | 62 / 60 | 47 / 48 | 82 / 75 | 57 / 48 |
| feel / not feel | 20 | 68 / 60 | 57 / 50 | 57 / 60 | 57 / 55 | 57 / 70 |
| believe / imagine | 10 | 70 / 70 | 55 / 70 | 40 / 40 | 85 / 65 | 50 / 40 |
| have no preference / prefer | 10 | 50 / 70 | 60 / 90 | 50 / 55 | 35 / 95 | 50 / 50 |

Połowa szerokości CI95 po rekordach wynosi ±4 pkt przy 220 rekordach i ±5–9 pkt przy 45. Przy 10 rekordach sięga
±20 pkt. Po szablonach przedziały są szersze: obie grupy po 10 rekordów to tylko 2 i 6 szablonów. Wartości dla
10–30 rekordów to sygnał do sprawdzenia, a nie wynik. Różnice PL − EN per para to opis. Werdykty (szum u wszystkich
modeli) są w sekcji 3.

## 6. Tłumaczenie: co wiemy, a czego nie

- **Wersja robocza.** EWoK-PL ma status `draft_review_required`, a 580 z 625 rekordów ma flagę przeglądu. Flagi
  oznaczają typ wnioskowania i są skorelowane z parami pojęć, ale nie pokrywają się z nimi 1:1. Nie mówią więc, czy
  tłumaczenie jest dobre. Jakość sprawdzi dopiero przegląd przez człowieka.
- **Kandydaci do przeglądu.** To rekordy, w których Bielik i LFM3 średnio różnią się między PL a EN o co najmniej
  0,5. Odniesieniem są modele z dolną granicą CI95 na pełnym EN > 60%. **37 rekordów jest trudniejszych po polsku,
  a 42 łatwiejszych**. Identyfikatory są w `raport_ewok.json`, pole `do_przegladu`. To kandydaci, a nie wykryte
  błędy.
- **Brakuje opisu procesu tłumaczenia**: kto tłumaczył, jakim narzędziem, jakie są zasady i polskie odpowiedniki par
  pojęć. Dopisze go autor tłumaczenia.

## 7. Ograniczenia

- **Jedna domena** (`agent-properties`, 9 par pojęć, 130 szablonów). Wniosków o fizyce czy przestrzeni po polsku z
  tego zestawu wyciągać nie można. Przy 9 parach odczyt po parach ma df = 8 i słabą moc.
- **Aster dokleja BOS i EOS.** W regule autorów EOS wchodzi do sumy zdania, a granica kontekstu przesuwa się o jeden
  token. Tak liczy kod autorów (`POLISH.md`, D2).
- **Bez skanu kontaminacji.** Dotyczyłaby tylko EN, bo EWoK-PL nie był publikowany. Jest więc konkurencyjnym
  wyjaśnieniem wzrostu Slayera na EN.
- **Jeden przebieg na model**, RTX 5060 Ti, float32. Kontrola między urządzeniami: niezrobiona.

## 8. Co dalej

1. Przetłumaczyć pozostałe domeny, zaczynając od `physical-relations`, `spatial-relations` i `material-dynamics`,
   czyli tam, gdzie EN pokazuje u Slayera najmniejszy albo największy postęp. Bez tego odczytu po domenach po polsku
   nie ma.
2. Przejrzeć pary „make more / less effort”, „choose” i „make an effort” oraz listy kandydatów z sekcji 6. Dopisać
   opis procesu tłumaczenia.
3. Dodać EWoK-PL do Space SlayerLab/Slayer1B-Benchmarks jako osobne zadanie z metryką `ewok` (%) i CI po szablonach.
