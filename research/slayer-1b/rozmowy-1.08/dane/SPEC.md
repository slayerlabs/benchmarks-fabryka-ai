# Specyfikacja zestawu poleceń (ocena trzech modeli bazowych ~1B)

Piszesz polecenia testowe do porównania trzech MODELI BAZOWYCH (nie czatowych) ok. 1-1,5 mld parametrów:
polskiego Slayer1B, Bielika 1.5B i LFM2.5 1.2B. Modele dostają polecenie w szablonie z 3 przykładami
(few-shot) i dopisują odpowiedź. Zestaw służy WYŁĄCZNIE do oceny, nigdy do treningu.

## Twarde reguły

1. **Wszystko od zera.** Nie kopiujesz ani nie parafrazujesz pytań z publicznych benchmarków (GSM8K, ARC,
   MMLU, HumanEval, MBPP, TriviaQA, PolQA, PLCC, LLMzSzŁ, BLiMP itd.). Wymyślasz własne treści, imiona,
   liczby, sytuacje. Nie używaj typowych fraz GSM8K („Natalia sprzedała spinki…”, „Janet's ducks…”).
2. **Jedna jednoznaczna odpowiedź** w poleceniach weryfikowalnych. Fakty stabilne (nie zmieniające się
   z roku na rok, bez „obecny prezydent”, bez rankingów i rekordów, które się zmieniają). Gdy nie masz
   pewności faktu — nie używaj go.
3. **Trudność dla modelu ~1B**: ok. 1/3 łatwe (`"trudnosc": 1`), 1/3 średnie (2), 1/3 trudniejsze (3).
   Za trudne dla wszystkich = efekt podłogi, test nic nie rozróżnia.
4. Odpowiedzi krótkich typów mieszczą się w JEDNEJ linii (bez znaku nowej linii).
5. Polskie znaki, poprawna ortografia i interpunkcja (polskie cudzysłowy „…” w treści są OK).
6. Przed oddaniem SAM sprawdzasz: kod — uruchamiasz wzorzec z testami w Pythonie (`python3`), matematyka —
   liczysz `obliczenie` w Pythonie i porównujesz z `liczba`; JSONL musi się parsować (`python3 -c` z
   `json.loads` dla każdej linii). Wynik sprawdzenia podajesz w raporcie.

## Format pliku: JSONL, jeden obiekt na linię

Pola wspólne:
- `id`: `<kat>-NN` (01..30), w pliku przykładów `shot-<kat>-N` (1..3)
- `kat`: kod kategorii
- `typ`: jeden z `krotka`, `zdanie`, `liczba`, `kod`, `otwarte`
- `trudnosc`: 1/2/3 (przykłady few-shot: 1)
- `polecenie`: treść polecenia, tak jak stoi po etykiecie „Polecenie:”. Bez etykiety. Może mieć kilka linii
  (np. kod, tekst do poprawy), ale zwykle jedna linia.
- `wzorzec`: odpowiedź wzorcowa DOKŁADNIE w stylu, w jakim model ma odpowiedzieć (to idzie też do przykładów
  few-shot i do pomiaru prawdopodobieństwa odpowiedzi). Krótkie typy: jedna linia, krótko, pełnym zdaniem albo
  samym słowem — spójnie w obrębie kategorii.

Pola per typ:
- `krotka` (krótki fakt/słowo/forma): `akceptowane` — lista WSZYSTKICH dopuszczalnych odpowiedzi jako
  krótkie napisy (różne formy fleksyjne, warianty zapisu, np. ["Mikołaj Kopernik", "Kopernik", "Kopernika",
  "Kopernikiem"]); `zakazane` — lista typowych błędnych odpowiedzi, których obecność w odpowiedzi modelu
  oznacza błąd (np. inne miasto, „nie” przy „tak”), może być pusta. Ocena: odpowiedź poprawna, gdy po
  normalizacji (małe litery, bez interpunkcji) pierwsza linia odpowiedzi zawiera któryś napis z
  `akceptowane` jako całe słowo/frazę i nie zawiera żadnego z `zakazane`. Dlatego `akceptowane` krótkie i
  rdzeniowe, a `zakazane` nie mogą zawierać się w poprawnej odpowiedzi (sprawdź to!).
- `zdanie` (korekta zdania): `akceptowane` — lista pełnych poprawnych wersji zdania (ocena: równość po
  normalizacji, więc podaj warianty, jeśli są dopuszczalne np. inny szyk). `wzorzec` = pierwsza z nich.
- `liczba`: `liczba` (int albo float), `obliczenie` (wyrażenie Pythona dające tę liczbę), `wzorzec` w JEDNEJ
  linii: krótkie rozumowanie i na końcu „Wynik: N” (np. „Kupił 3 · 4 = 12 jabłek, zostało 12 − 5 = 7. Wynik: 7”).
  Wynik liczbą całkowitą < 100 000 albo z jednym miejscem po przecinku; bez jednostek po „Wynik:”.
- `kod`: `polecenie` zawiera opis po polsku i w nowej linii blok:
  ```
  ```python
  def nazwa(arg):
      """docstring po polsku"""
  ```
  ```
  `funkcja`: nazwa funkcji; `wzorzec`: pełna funkcja w bloku ```python … ``` (sygnatura + docstring + ciało);
  `testy`: napis z 5-8 liniami `assert nazwa(...) == ...` (tylko biblioteka standardowa, bez I/O, bez sieci,
  bez losowości, szybkie). Testy NIE są pokazywane modelowi.
- `otwarte`: `kryteria` — lista 3-5 sprawdzalnych kryteriów oceny (treść merytoryczna, poprawność faktów,
  forma, język), `wzorzec` — przykładowa dobra odpowiedź (kilka zdań do ok. 150 słów).

## Kategorie (kod: liczba poleceń)

- `pl_jezyk` — polszczyzna: odmiana (przypadki, liczba mnoga, formy czasowników, stopniowanie) jako
  `krotka`, korekta zdań z 1-2 błędami (ortografia, fleksja, składnia, frazeologia) jako `zdanie`; razem 24
  weryfikowalne + 6 `otwarte` (krótkie pisanie użytkowe: e-mail, ogłoszenie, notatka, opis).
- `angielski` — po angielsku (polecenia i odpowiedzi po angielsku): gramatyka (formy czasowników, liczba
  mnoga, przyimki), słownictwo, proste fakty po angielsku, tłumaczenie pojedynczych słów/krótkich zwrotów
  PL→EN z jednoznaczną odpowiedzią; 24 weryfikowalne (`krotka` albo `zdanie`) + 6 `otwarte` (krótkie
  pisanie po angielsku).
- `pl_wiedza` — wiedza o Polsce: historia, geografia, kultura, literatura, instytucje, nauka; 30 `krotka`.
- `wiedza_ogolna` — wiedza ogólna o świecie (po polsku): nauka, geografia świata, historia świata, biologia,
  fizyka, technika; 30 `krotka`.
- `rozumowanie` — logika: sylogizmy, kolejność, dni tygodnia, relacje rodzinne, zagadki z jedną odpowiedzią,
  wnioskowanie z warunków (po polsku); 30 `krotka` (odpowiedź jednym słowem/krótką frazą: „tak”/„nie”,
  imię, dzień, kolor; przy tak/nie wpisz przeciwną odpowiedź do `zakazane`).
- `matematyka` — zadania tekstowe po polsku, 1-4 kroki rachunku (procenty, ułamki, czas, pieniądze,
  prędkość, proporcje); 30 `liczba`.
- `kod` — Python: małe funkcje (napisy, listy, słowniki, liczby, proste algorytmy); 30 `kod`.
- `tekst_techniczny` — tekst techniczny/analityczny po polsku: wyjaśnij pojęcie, porównaj dwie technologie,
  opisz procedurę, przeanalizuj krótką sytuację (IT, ekonomia, inżynieria, nauka); 30 `otwarte`.

Dodatkowo dla każdej kategorii osobny plik z 3 przykładami few-shot (`shot-<kat>-1..3`), w tym samym
formacie, łatwe, NIE pokrywające się tematem z poleceniami. W `pl_jezyk` i `angielski` przykłady: 2
weryfikowalne + 1 `otwarte` (krótkie, do 60 słów). W `tekst_techniczny` wzorce przykładów do 90 słów.
