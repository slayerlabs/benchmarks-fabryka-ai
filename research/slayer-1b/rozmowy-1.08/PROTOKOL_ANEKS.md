# Aneks do protokołu: jakość poleceń, rzetelność, trafność zewnętrzna, kontrola wzorców, moc

<!-- liczba-spoza-wynikow: cały plik to aneks protokołu zapisany przed odczytem metryk, nie wyniki -->

Dopisek orkiestratora (pytanie Ani: skąd wiemy, że pytania są dobre i że wynik coś mówi). Zacommitowany w trakcie
kolejki generacji, ZANIM przeczytałam jakąkolwiek metrykę porównania modeli. Do chwili tego commitu czytałam
wyłącznie: wynik kontroli narzędzia (sekcja 6 protokołu: ARC-C i OBQA Slayera 1.08 wobec EVALUATION.json) i trzy
przykłady próby dymnej `code/dym.py` (po 3 pozycje × 3 modele, czytane ręcznie zgodnie z METODOLOGIĄ p. 8, bez
liczenia metryk). Analizy niżej nie zmieniają hipotez ani progów z `PROTOKOL.md`; są dodatkowymi analizami
z góry ustalonymi (nie eksploracyjnymi). Kod: `code/jakosc.py` (pisany po tym aneksie, przed odczytem wyników).

## A1. Jakość pozycji (typy weryfikowalne, 198 poleceń)

- **Trudność** polecenia i: p_i = odsetek poprawnych ze wszystkich 9 prób (3 modele × 3 seedy, szablon A). Obok
  p_i greedy (3 próby).
- **Moc rozróżniania** polecenia: zakres średnich modeli R_i = max_m p_im − min_m p_im, gdzie p_im = średnia
  modelu m po 3 seedach. Polecenie **rozróżnia modele**, gdy R_i ≥ 2/3 (np. jeden model 3/3, inny ≤ 1/3).
- Listy osobno: polecenia „zawsze dobrze” (9/9 poprawnych) i „zawsze źle” (0/9), per kategoria; dla nich podaję
  też wynik greedy A i B.
- Per kategoria: liczba poleceń rozróżniających, „zawsze dobrze”, „zawsze źle” i reszta. Liczba rozróżniających
  idzie do raportu przy każdej kategorii obok werdyktu.
- Dla BPB (wszystkie 240): rozrzut polecenia = odchylenie standardowe BPB trzech modeli; opisowo.

## A2. Rzetelność

- **Zgodność między seedami:** dla każdego modelu i kategorii korelacja Pearsona wyników 0/1 per polecenie między
  parami seedów (s1–s2, s1–s3, s2–s3), średnia z trzech par; obok odsetek poleceń z tym samym wynikiem we wszystkich
  3 seedach. Korelacja nieokreślona (stały wynik) → „nieokreślona”.
- **Zgodność szablonów:** korelacja Pearsona i Spearmana per polecenie między szablonem A i B: BPB (wszystkie typy)
  i poprawność greedy A wobec greedy B (typy weryfikowalne), per model i kategoria.
- **SNR kategorii** (jak „Signal and Noise”, arXiv 2508.13144): sygnał = wariancja między modelami średniej
  poprawności kategorii (3 średnie, próbkowanie A); szum = średnia po modelach wariancji między seedami średniej
  kategorii (3 seedy). SNR = sygnał / szum. Dla BPB, które jest deterministyczne, szum = średnia po modelach
  wariancji między szablonami A i B średniego BPB kategorii; tę wersję oznaczam jako SNR względem szablonu, nie
  seeda. Kategorie z SNR < 1 opisuję jako takie, w których różnice modeli nie wychodzą ponad szum.

## A3. Trafność zewnętrzna

Porównanie rankingu i różnic trzech modeli w każdej kategorii z ich wynikami w przebiegu centralnym fabryki
`research/results/full-run-2026-11/` (w tym repo, stan commitu `8b54700`; katalogi modeli `slayer1b-1.08`,
`bielik-1.5b-v3`, `lfm2.5-1.2b-base`), metryka decyzyjna każdego testu z README tamtego przebiegu.
`research/results/central-run/` nie ma Slayera 1.08 ani Bielika 1.5B (tylko Slayer 1.06 i LFM), więc z niego
biorę wyłącznie to, czego nie ma w full-run, i zapisuję wersję.

Dopasowanie ustalone z góry:

| kategoria | testy przebiegu centralnego | uwaga |
|---|---|---|
| pl_jezyk | MultiBLiMP-PL | gramatyka polska, pary minimalne |
| pl_wiedza | NOT RUN | brak testu wiedzy o Polsce dla wszystkich trzech modeli; MMLU-PL jest tylko w EVALUATION.json Slayera |
| wiedza_ogolna | ARC-Easy, ARC-Challenge | wiedza szkolna EN |
| rozumowanie | WinoGrande, WSC273 | rozumowanie zdroworozsądkowe EN (inny typ niż nasze zagadki logiczne) |
| matematyka | MathQA | matematyka słowna EN, wybór opcji |
| kod | NOT RUN | brak testu kodu w przebiegu centralnym |
| angielski | BLiMP, LAMBADA | gramatyka i modelowanie języka EN |
| tekst_techniczny | NOT RUN | brak polskiego testu tekstu ciągłego dla trzech modeli (WikiText-2 jest angielski) |

Miary: (i) ranking trzech modeli po naszej metryce (poprawność A, a dla kategorii bez niej BPB A, gdzie niższe =
lepsze) i po teście centralnym; zgodność tau Kendalla (przy 3 modelach możliwe tylko −1, −1/3, 1/3, 1);
(ii) zgodność znaków trzech różnic par (S−B, S−L, B−L) i zgodność werdyktów, gdy obie strony mają SE. Przy trzech
modelach to porównanie jest opisowe: nie ma testu istotności zgodności rankingów, a różne formaty (generacja vs
log-likelihood wyboru) mogą dawać różne rankingi przy tych samych umiejętnościach. Każdy brak wyniku w przebiegu
centralnym oznaczam NOT RUN z nazwą brakującej pary model × test.

## A4. Kontrola wzorców

Losowa próba 10% poleceń weryfikowalnych: 20 z 198, warstwowo po kategoriach (proporcjonalnie, reszty
zaokrąglone do największych), `random.Random(20261112)`, plik `dane/kontrola_wzorcow.jsonl` (polecenie, wzorzec,
listy dopuszczalnych i zakazanych odpowiedzi, liczba, testy) i instrukcja `dane/INSTRUKCJA_KONTROLI_WZORCOW.md`.
Sprawdza je osobny agent bez dostępu do wyników modeli. Werdykt per pozycja: wzorzec poprawny / błędny /
niejednoznaczny, oraz czy listy akceptowane/zakazane mogą odrzucić poprawną albo przyjąć błędną odpowiedź.
Reguła z góry: pozycje z werdyktem „błędny” albo „niejednoznaczny” wypadają z analiz potwierdzających (z
podaniem liczby i wpływu na każdy werdykt), a odsetek błędnych w próbie z przedziałem (Clopper-Pearson 95%)
oszacowuje odsetek błędnych wzorców w całym zestawie i idzie do raportu.

## A5. Moc: najmniejsza wykrywalna różnica (2 SE) przy n = 30

Różnica wykrywalna na progu „prawdopodobne” to 2 · SE różnicy parowanej, SE = sd(d_i)/√30. Z góry:

| metryka | sd(d_i) założone | 2 SE |
|---|---|---|
| poprawność (średnia 3 seedów), wariant pesymistyczny | 1,0 (maksimum dla d w [−1, 1]) | 0,365 |
| poprawność, wariant typowy | 0,5 | 0,183 |
| poprawność, wariant optymistyczny | 0,3 | 0,110 |
| odsetek wygranych w ocenie sędziów, n = 42 | 0,5 (maksimum dla [0, 1]) | 0,154 |

Pod Holmem przy 8 kategoriach próg „prawdopodobne” to |z| ≈ 2,73, więc wykrywalna różnica rośnie 1,37 raza. Dla
BPB nie znam sd(d_i) przed pomiarem; raport podaje 2 SE z danych dla każdej kategorii i każdej pary, a paper mówi
wprost, jaka najmniejsza różnica była w zasięgu pomiaru w każdej kategorii.
