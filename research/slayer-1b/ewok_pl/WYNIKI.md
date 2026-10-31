# EWoK-PL: wyniki Slayera 1B (30.10.2026)

> **W skrócie.** Na polskim EWoK-PL Slayer 1.06 ma **55,4%** przy losowych 50% i od wersji 1.00 nie
> poprawia się istotnie (+1,0 pkt, SE 1,4 pkt, szum). Na angielskim EWoK ten sam model rośnie z **53,1% do 58,9%** (p < 0,001), więc
> wiedza o świecie przybywa, a polski zestaw tego jeszcze nie pokazuje. Bielik-1.5B-v3 ma po polsku
> **66,0%**, a LFM3-1.7B-Base **57,4%**. EWoK-PL obejmuje na razie tylko jedną domenę (`agent-properties`).

Metoda, rewizje modeli i polecenia do uruchomienia: [`README.md`](README.md). Wszystkie tabele z CI95: [`../wyniki_ewok/raport_ewok.md`](../wyniki_ewok/raport_ewok.md).

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

*(Przykład jest zmyślony, żeby pokazać sam format. Treści EWoK-PL nie publikujemy.)*

Za każdą parę, w której model woli właściwy kontekst, dostaje pół punktu, więc za rekord może mieć
0, 0,5 albo 1. Losowo wychodzi 50%. To samo zdanie stoi po obu stronach porównania, dlatego
**preferencja litery „A” i długość odpowiedzi nie mają wpływu na wynik**. Odpada więc problem, który
zaniżał Slayera w testach z literami A/B/C/D.

## 2. Wyniki główne

Wynik EWoK w % (losowo 50), w nawiasie CI95. „Oba” to rekordy z obiema trafionymi parami (losowo 25).

| model | PL (625) | PL „oba” | EN, te same 625 | EN pełny (4374) |
|---|---|---|---|---|
| **Bielik-1.5B-v3** | **66,0** [63,4; 68,5] | **42,4** | 62,8 | 69,5 |
| **LFM3-1.7B-Base** | 57,4 [55,0; 59,8] | 27,0 | **66,6** | **69,7** |
| Slayer1B-1.00 | 54,4 [52,0; 56,8] | 23,5 | 51,3 | 53,1 |
| Slayer1B-1.01 | 53,0 [50,6; 55,3] | 21,3 | 53,5 | 55,5 |
| Slayer1B-1.02 | 54,4 [52,1; 56,7] | 22,6 | 52,8 | 57,1 |
| Slayer1B-1.03 | 54,6 [52,3; 56,9] | 21,1 | 52,0 | 55,8 |
| Slayer1B-1.04 | 56,4 [54,3; 58,5] | 21,1 | 56,0 | 57,4 |
| Slayer1B-1.05 | 55,6 [53,3; 57,8] | 22,6 | 57,0 | 58,8 |
| **Slayer1B-1.06** | **55,4** [53,0; 57,8] | 25,1 | 56,2 | 58,9 |

```
EN pełny (4374), Slayer 1B po wersjach   (1 blok = 1 pkt ponad losowe 50)
1.00  53,1  ███▏
1.01  55,5  █████▌
1.02  57,1  ███████
1.03  55,8  █████▊
1.04  57,4  ███████▍
1.05  58,8  ████████▊
1.06  58,9  ████████▉
Bielik 69,5 / LFM3 69,7  (dla porównania)
```

## 3. Najważniejsze wnioski

1. **Slayer uczy się wiedzy o świecie, ale widać to tylko po angielsku.** Między 1.06 a 1.00 jest
   +5,7 pkt na EN (CI95 +4,7…+6,8, p < 0,001) i +1,0 pkt na PL (p = 0,55, w granicach szumu).
   Te same 625 rekordów po angielsku też dają Slayerowi tylko 51–57%, więc płaski wynik PL bierze
   się z wyboru domeny, a nie z tłumaczenia.
2. **Bielik wyraźnie wygrywa po polsku** (+10,6 pkt nad Slayerem 1.06, p < 0,001), a w 42% rekordów
   trafia obie pary. Slayer trafia je w 25%, czyli na poziomie losowym.
3. **LFM3 nie jest po polsku lepszy od Slayera** (−2,0 pkt, SE 1,5 pkt, p = 0,20, szum), choć po angielsku ma 69,7%.
   Na tych samych rekordach po polsku traci 9,3 pkt względem angielskiego (p < 0,001), co jest śladem
   słabego polskiego. Bielik i Slayer po polsku nie tracą: różnica PL − EN mieści się u nich
   w przedziale −1,4…+3,2 pkt.
4. **Jedna para pojęć ciągnie wynik w dół.** „Make more / less effort” to 220 z 625 rekordów, a wszystkie
   modele są na niej losowe (Bielik 57, LFM3 55, Slayer 48–52). Prawdopodobnie jest po prostu trudna
   (wnioskowanie o wysiłku z preferencji), ale warto ją przejrzeć przy kolejnej wersji tłumaczenia.
5. **Slayer mocno trzyma się prioru zdania.** Gdy porównać dwa zdania w tym samym kontekście, Slayer
   w 81–85% rekordów wybiera to samo zdanie, cokolwiek mówi kontekst (Bielik 75%, LFM3 74%). To
   odpowiednik „zawsze A” z testów z literami. Reguła EWoK jest na to odporna, dlatego jest metryką główną.

## 4. Czego Slayer 1.06 nie umie (EN, według domen)

| domena | n | Slayer 1.00 | **Slayer 1.06** | Bielik | LFM3 |
|---|---|---|---|---|---|
| physical-relations | 415 | 50 | **51** 🔴 | 58 | 58 |
| physical-interactions | 280 | 52 | **54** 🔴 | 62 | 61 |
| spatial-relations | 245 | 54 | **55** 🔴 | 61 | 61 |
| agent-properties | 1120 | 51 | **55** 🔴 | 65 | 68 |
| material-properties | 124 | 54 | 57 | 55 | 58 |
| social-relations | 785 | 51 | 57 | 68 | 67 |
| physical-dynamics | 75 | 59 | 61 | 69 | 75 |
| quantitative-properties | 190 | 63 | 67 | 71 | 66 |
| material-dynamics | 780 | 53 | **67** 🟢 | 86 | 84 |
| social-properties | 185 | 58 | **68** 🟢 | 83 | 77 |
| social-interactions | 175 | 69 | 72 | 80 | 84 |

🔴 to poziom bliski losowemu (≤ 55%). 🟢 to największy przyrost od 1.00 (+10 pkt i więcej).
Najsłabsze są **relacje fizyczne i przestrzenne**. Tam nawet Bielik i LFM3 nie przekraczają 62%.
Największy postęp Slayer zrobił w **dynamice materiałów** (53 → 67) i **cechach społecznych**.

## 5. Polski zestaw: wyniki według pary pojęć

| para pojęć | n | Bielik | LFM3 | Slayer 1.00 | Slayer 1.06 |
|---|---|---|---|---|---|
| make more / less effort | 220 | 57 | 55 | 51 | 49 |
| choose / – | 165 | 68 | 62 | 48 | 51 |
| intend / not intend | 70 | 79 | 61 | 64 | 65 |
| believe / doubt | 55 | 48 | 42 | 50 | 47 |
| make an effort / make no effort | 45 | 90 | 54 | 87 | 77 |
| hear / not hear | 30 | 83 | 75 | 48 | **85** |
| feel / not feel | 20 | 68 | 57 | 60 | 57 |
| believe / imagine | 10 | 70 | 50 | 50 | 75 |
| have no preference / prefer | 10 | 50 | 65 | 50 | 40 |

Przy grupach poniżej ~50 rekordów CI95 ma szerokość ±10–15 pkt. Wartości dla 10–30 rekordów to
sygnał do sprawdzenia, a nie wynik.

## 6. Ograniczenia

- **To wersja robocza tłumaczenia** (`draft_review_required`): 580/625 rekordów ma flagę przeglądu.
  Rekordy bez flagi nie wypadają lepiej, więc flagi nie tłumaczą słabych wyników.
- **Jest tylko jedna domena** (`agent-properties`, 9 par pojęć). Wniosków o fizyce czy przestrzeni
  po polsku z tego zestawu wyciągać nie można.
- Tylko 3 rekordy wyglądają na możliwe błędy tłumaczenia, bo modele radzą sobie z nimi po angielsku,
  a po polsku nie: **ewok-pl-0141, 0149, 0171**.
- Liczb nie porównywaliśmy z paperem EWoK, bo nie ma w nim tych modeli. Kontaminacji nie skanowaliśmy.

## 7. Co dalej

1. Przetłumaczyć pozostałe domeny EWoK (w pierwszej kolejności `physical-relations`, `spatial-relations`
   i `material-dynamics`). Dopiero wtedy PL pokaże to samo, co EN.
2. Przejrzeć parę „make more / less effort” i 3 rekordy z listy wyżej.
3. Dodać EWoK-PL do Space SlayerLab/Slayer1B-Benchmarks jako osobne zadanie z metryką `ewok` (%).
