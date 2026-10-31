# BLiMP: Slayer 1.06 i Pythia-1B na pełnym zbiorze

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md): etap A to karta oryginału (`ORIGINAL.md`), etap B to
> odtworzenie opublikowanego wyniku kodem autorów (`REPRODUCTION.md`), etap D to wersja polska tą samą metodą.
> Pojęcia (Space, T01–T50, panel 200, SE, werdykt): [słowniczek](../../METODOLOGIA.md#słowniczek).

BLiMP (Warstadt i in. 2020) sprawdza gramatykę angielską na 67 paradygmatach x 1000 par minimalnych: para jest
trafiona, gdy model daje zdaniu poprawnemu wyższe log-prawdopodobieństwo. Poziom losowy to 0,5. Space liczy ten
test (T01) na panelu 200 par; tutaj oba modele liczone są na wszystkich 67 000.

- Karta oryginału (etap A): [`ORIGINAL.md`](ORIGINAL.md)
- Odtworzenie (etap B, nie zrobione kodem autorów): [`REPRODUCTION.md`](REPRODUCTION.md)
- Przepis (commity, modele, komendy, sprzęt): [`RECIPE.md`](RECIPE.md)
- Pełny raport ze wszystkimi tabelami (generowany, nie edytować; po angielsku): [`results/BLIMP.md`](results/BLIMP.md)
- Progi zapisane przed pomiarem: [`THRESHOLDS.md`](THRESHOLDS.md)

## Wyniki

| model | trafność | n | SE | CI95 (bootstrap, warstwowy) |
|---|---:|---:|---:|---|
| Slayer 1.06 | 0,7921 | 67000 | 0,0014 | 0,7892-0,7949 |
| Pythia-1B | 0,8207 | 67000 | 0,0013 | 0,8181-0,8233 |

Slayer 1.06 minus Pythia-1B, trzy odczyty:

| odczyt | różnica | SE | test | werdykt | ustalone przed pomiarem |
|---|---:|---:|---|---|---|
| te 67 000 par (w parach) | -2,87 pkt | 0,16 pkt | z = -18,11 | pewne | tak |
| paradygmaty jako klastry (k = 67, df = 66) | -2,87 pkt | 0,87 pkt | t = -3,30, p = 0,0016 | pewne | nie (eksploracyjne) |
| na token (log-prawdopodobieństwo / liczba tokenów) | -3,09 pkt | 0,17 pkt | z = -17,76 | pewne | nie (eksploracyjne) |

- Na tych parach Pythia-1B ma przewagę z werdyktem pewnym (z = -18,11). Uogólniony na inne paradygmaty werdykt
  też jest pewny (t = -3,30), Pythia ma przewagę w 56 z 67 paradygmatów, ale bez 2 paradygmatów o największej
  różnicy spada do prawdopodobnego (t = -2,91, p = 0,0049), więc opiera się częściowo na kilku paradygmatach.
- Tokenizery się różnią (Slayer tnie te zdania na 1,18x tyle tokenów); na token różnica zostaje pewna
  (z = -17,76).

### Zjawiska z werdyktem pewnym

Z 12 zjawisk różnica jest pewna na parach w 9 (we wszystkich 9 na korzyść Pythii-1B),
prawdopodobna w elipsie (z = -2,68) i szum w efektach wysp (z = -1,17) oraz kwantyfikatorach (z = 1,89). Po
paradygmatach (eksploracyjnie, wymaga k >= 3) pewne jest tylko jedno zjawisko:

| zjawisko | paradygmaty | Slayer 1.06 | Pythia-1B | różnica | SE w parach | z w parach | t po paradygmatach | werdykt pary / paradygmaty |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| argument structure | 9 | 0,785 | 0,836 | -5,2 pkt | 0,42 pkt | z = -12,22 | t = -4,68 | pewne / pewne |
| determiner noun agreement | 8 | 0,930 | 0,951 | -2,1 pkt | 0,29 pkt | z = -7,11 | t = -3,79 | pewne / prawdopodobne |
| subject verb agreement | 6 | 0,844 | 0,883 | -3,9 pkt | 0,51 pkt | z = -7,64 | t = -4,91 | pewne / prawdopodobne |

Pozostałe zjawiska z werdyktem pewnym na parach (anaphor agreement, binding, control raising, filler gap
dependency, irregular forms, npi licensing) po paradygmatach to szum albo nierozstrzygalne: różnica jest
prawdziwa dla tych par z werdyktem pewnym, ale nie pokazano, że trzyma się dla innych paradygmatów zjawiska.
Per paradygmat (n = 1000 każdy): na parach Slayer prowadzi z werdyktem pewnym w 7, Pythia w 34, szum w 18;
poprawka Holma zostawia 37 różnic. Największe pewne różnice na korzyść Slayera to sentential_subject_island
(23,7 pkt, z = 11,63) i principle_A_reconstruction (15,7 pkt, z = 9,44); na korzyść Pythii tough_vs_raising_1
(-16,5 pkt, z = -12,10) i principle_A_domain_3 (-15,0 pkt, z = -7,32). Kolejność zależy od miary (korelacja
Spearmana 0,77 między różnicami sumowanymi a liczonymi na token), patrz pełny raport.

Przewaga Pythii leży w parach, które różnią się słowem albo jego formą: z od -18,12 do -23,18 (pewne) we
wszystkich trzech odczytach „tych samych słów”. Odczyt to sposób rozstrzygania, czy zdanie poprawne i błędne
składają się z tych samych słów (tylko w innej kolejności): małe litery bez interpunkcji, surowy tekst dzielony na
spacjach albo słowa i interpunkcja jako osobne jednostki; szczegóły w [`results/BLIMP.md`](results/BLIMP.md),
sekcja o tokenizerze i słownictwie („tokenizer and vocabulary”). Dla par z tymi samymi słowami w innej kolejności werdykt zmienia
znak razem z definicją (z od -2,53 do 2,32), więc tam nie ma wniosku (eksploracyjnie).

### Panel Space 200 par a pełny zbiór

Wartość Space dla Slayera 1.06 to 0,8408 (CI95 0,806-0,876, n = 200). Space wybiera 200 par
po haszu SHA-256 z identyfikatorem pary w środku ([`METHOD.md`](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/main/METHOD.md),
sekcja 3), ale nie mówi dokładnie, jaki to identyfikator. Panel odbudowany z identyfikatorem `pair_id` (pole
identyfikatora pary w zbiorze BLiMP, odczyt z protokołu) daje 0,7761, poza CI95 Space: panel nie odtworzony. Panel
odbudowany z haszem całego wiersza zbioru zapisanego w ustalonej postaci („hasz kanonicznego wiersza”) daje dokładnie
0,8408, więc to prawdopodobnie panel Space (wniosek z jednej wartości). Szczegóły: [`results/BLIMP.md`](results/BLIMP.md),
sekcja „Agreement with the Space (panel of 200)”. To panel szczęśliwy: tylko 3,3% losowych
paneli o tym samym podziale daje Slayerowi tę wartość albo wyższą. Wartość z pełnego zbioru 0,7921 leży poza
CI95 Space. Używaj pełnego zbioru.

### Pythia-1B wobec opublikowanej wartości (nie kontrola etapu B)

Nasza Pythia-1B 0,8207 wobec 0,8234 opublikowanego dla `EleutherAI/pythia-1b-v0` @ `step143000`: różnica
-0,27 pkt, w granicach +-2 pkt. Inne wagi i starszy harness, więc to zakres kontrolny, nie odtworzenie
([`REPRODUCTION.md`](REPRODUCTION.md)).

## Ograniczenia

- Batch 64 na Apple MPS zamiast batch 1: tylko 11 (Slayer) i 10 (Pythia) z 67 000 par ma oba zdania bliżej
  siebie niż szum liczb zmiennoprzecinkowych między CPU a MPS.
- Forward Slayera to ponowna implementacja; wobec oficjalnego forwardu 0 z 200 par zmieniło wynik.
- Kontaminacja nie skanowana (brak dostępu do korpusu treningowego Slayera; Pile dla Pythii też nie skanowany).

## Co dodaje metodologia

Lista tego, czego ta praca jeszcze nie spełnia według [`METODOLOGIA.md`](../../METODOLOGIA.md); każdy punkt to osobne
zadanie do wzięcia.

- [ ] Etap B z kodem referencyjnym: lm-eval `blimp` @ `6d2abda4fd171e68a8789330c4149e37c1ca0bda` (albo skrypty
      jiant autorów) i nasz kod oceny na tych samych wagach, `EleutherAI/pythia-1b-v0` @ `step143000`,
      porównane z opublikowaną wartością Pythii v0; dziś kontrola porównuje wagi v1 z wagami v0.
- [ ] Test zgodności `tests/test_blimp_zgodnosc.py`: 10-20 par z zapisanymi wynikami kodu referencyjnego,
      zgodność per para >= 99%, bez sieci (dziś `tests/test_blimp.py` testuje tylko czyste funkcje).
- [ ] Pięć modeli odniesienia (`Qwen/Qwen3.5-0.8B-Base`, `LiquidAI/LFM2.5-1.2B-Base`,
      `speakleash/Bielik-1.5B-v3`, `LiquidAI/LFM3-1.7B-Base`, `utter-project/EuroLLM-1.7B`) na pełnym zbiorze.
- [ ] Brakujące pola przepisu: dokładny sprzęt (chip), wersja Pythona w głównym przebiegu, sha256 plików zbioru,
      transformers przypięty do commitu.
- [ ] Kalibracja forwardu Slayera z [`METHOD.md`](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks/blob/main/METHOD.md) (logity równe bit w bit), nie zrobiona.
- [ ] Skan kontaminacji dla obu modeli.
- [ ] Wersja polska (etap D): BLiMP to test zjawisk językowych, więc osoba z Polski pisze nowe pary od
      zera na zjawiskach polszczyzny, bez tłumaczenia i parafrazy angielskich par.
