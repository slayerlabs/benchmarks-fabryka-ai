# WSC273: Slayer 1.06 na T14

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Etap B to odtworzenie opublikowanego wyniku
> (`REPRODUCTION.md`). Kartę oryginału (`ORIGINAL.md`) dopisuje osobne zadanie po terminie testów Space.
> Pojęcia (Space, T01–T50, panel 200, SE, werdykt): [słowniczek](../../METODOLOGIA.md#słowniczek).

WSC273 to 273 pytania Winograd Schema Challenge. Model wybiera, do kogo odnosi się zaimek, między dwiema opcjami. <!-- liczba-spoza-wynikow: rozmiar splitu z karty zadania -->
lm-eval podstawia każdą opcję w miejsce zaimka i porównuje log-prawdopodobieństwo wspólnej kontynuacji. Metryka
decyzyjna to trafność (`acc`), a pytania są 0-shot.

- Protokół: [`PROTOCOL-space.md`](PROTOCOL-space.md). Tekst powstał przed pomiarem, ale protokół, próbka i wyniki
  weszły do repo jednym commitem, więc historia gita tej kolejności nie potwierdza.
- Odtworzenie (etap B): [`REPRODUCTION.md`](REPRODUCTION.md)
- Przepis (commity, modele, komendy, sprzęt): [`RECIPE.md`](RECIPE.md)
- Liczby: [`results/wsc273.json`](results/wsc273.json)

## Wyniki

| model | próbka | trafność | n | SE | CI95 (bootstrap) |
|---|---|---:|---:|---:|---|
| Slayer 1.06 | panel 200 (własny wariant próbki) | 0,605 | 200 | 0,0347 | 0,535-0,675 |
| Slayer 1.06 | pełny split | 0,590 | 273 | 0,0298 | 0,527-0,648 |
| `bloom-560m` (kontrola) | pełny split | 0,623 | 273 | 0,0294 | 0,564-0,681 |

Panel 200 to próbka według naszej, wcześniej zapisanej postaci kanonicznej dokumentu, a nie pewna próbka Space
(sekcja „Wrażliwość na tożsamość dokumentu”). Wiarygodniejsza liczba to pełny split, 0,590. Kontrola pochodzi spoza
listy źródeł `METODOLOGIA.md`, więc oba wyniki Slayera są wstępne ([`REPRODUCTION.md`](REPRODUCTION.md)).

Bazy:

| próbka | losowa | większościowa | udział najczęstszej predykcji Slayera | stała predykcja |
|---|---:|---:|---:|---|
| panel 200 | 0,500 | 0,520 | 0,555 | nie |
| pełny split | 0,500 | 0,502 | 0,535 | nie |

Slayer 1.06 wobec baz:

| próbka | baza | różnica | SE | test | werdykt | po Holmie |
|---|---|---:|---:|---|---|---|
| panel 200 | losowa | +10,5 pkt | 0,0347 | z = 3,03 | pewne | tak (prawdopodobne) |
| panel 200 | większościowa | +8,5 pkt | 0,0469 | z = 1,81 | szum | nie (szum) |
| pełny split | losowa | +9,0 pkt | 0,0298 | z = 3,01 | pewne | tak (prawdopodobne) |
| pełny split | większościowa | +8,8 pkt | 0,0440 | z = 1,997 | szum | nie (szum) |
| pełny split, SE K po schematach (wiążące) | losowa | +9,0 pkt | 0,0201 | t = 4,47, df 134 | pewne | tak (pewne) |
| pełny split, SE K po schematach (wiążące) | większościowa | +8,8 pkt | 0,0201 | t = 4,38, df 134 | pewne | tak (pewne) |

Model i stała odpowiedź odpowiadają na te same pytania, więc SE różnicy wobec bazy większościowej jest parowane
(METODOLOGIA, „b”). Wobec bazy losowej, czyli stałej, SE to SE trafności. „Po Holmie”: p z wiersza poprawione
metodą Holma w rodzinie sześciu wierszy tej tabeli (klucz `holm_bazy` w `results/wsc273.json`), „tak” przy p Holma
nie większym niż p dla |z| = 2, w nawiasie werdykt z p Holma.

**Wiąże odczyt po schematach: Slayer 1.06 jest ponad obiema bazami (t = 4,38 wobec większościowej, pewne).** Typ
`mc +klastry` z [tabeli typów](../../README.md#benchmarki-i-typy) liczy SE K po klastrach, a jednostka wynika z
budowy zbioru (pary schematów Winograda), nie z wyniku. Odczyt po pytaniach zostaje w tabeli informacyjnie.
WSC273 składa się ze schematów, czyli kolejnych zdań różniących się jednym-dwoma słowami, zwykle z przeciwnymi
odpowiedziami. Stała odpowiedź trafia w takim schemacie mniej więcej raz na parę, więc wariancja różnicy siedzi
w schematach, a SE po pytaniach ją zawyża. Zbiór nie ma id schematu. Schematy wyznaczamy z tekstu zdań
(`schematy` w `wsc273.py`): kolejne zdanie należy do schematu poprzedniego, gdy zbiory ich słów pokrywają się
w co najmniej 60% (Jaccard). Wychodzi 135 schematów: 133 pary, jeden schemat z 3 zdaniami (George, wiersze <!-- liczba-spoza-wynikow: próg grupowania, stała PROG_SCHEMATU -->
252-254) i jeden z 4 (Madonna, 267-270). Podział po kolejności wierszy (k // 2) rozjeżdża się na tych dwóch
schematach i dalej, więc go nie używamy. Wynik zależy od grupowania tylko w drugim miejscu: przy progu 50%
(134 schematy) i 70% (140) t wobec bazy większościowej to 4,40 i 4,13, czyli zawsze pewne. <!-- liczba-spoza-wynikow: progi grupowania; t z po_schematach_wrazliwosc_progu w results/wsc273.json -->

Panelu 200 nie przeliczamy po schematach: panel losuje pojedyncze zdania, więc część schematów jest w nim
niepełna i ani SE po pytaniach, ani SE po schematach nie opisuje go czysto; jego werdykty w tabeli są po pytaniach
i służą tylko zgodności ze Space.

Przebieg próbki zgadza się z podzbiorem przebiegu pełnego: największa różnica logliku to 0,0, liczba różnych `acc` to 0. <!-- liczba-spoza-wynikow: zgodność przebiegów z results/wsc273.json -->
Najdłuższe żądanie ma 48 tokenów, więc nic nie zostało obcięte. <!-- liczba-spoza-wynikow: wyjście evaluate -->

## Wrażliwość na tożsamość dokumentu

WSC273 nie ma identyfikatora, a `METHOD.md` nie publikuje postaci kanonicznej dokumentu. Próbka Space może więc być
inna niż nasza. Wartości tej samej reguły próbki przy różnych rozsądnych tożsamościach, jako podzbiory przebiegu
pełnego. Pierwsze trzy warianty zapisał protokół, pozostałe doszły po wyniku:

| tożsamość dokumentu | trafność | n | SE |
|---|---:|---:|---:|
| dokument po `process_docs` (wariant główny) | 0,605 | 200 | 0,0347 |
| dokument przed `process_docs` | 0,570 | 200 | 0,0351 |
| indeks wiersza | 0,565 | 200 | 0,0351 |
| dokument przed `process_docs`, bez `sort_keys` | 0,610 | 200 | 0,0346 |
| dokument po `process_docs`, bez `sort_keys` | 0,570 | 200 | 0,0351 |
| pola treści (`text`, `pronoun`, `pronoun_loc`, `options`, `label`) | 0,575 | 200 | 0,0350 |

Rozstęp tych sześciu wariantów to 4,5 pkt. Szerszy przegląd, 63 podzbiory pól z `text` i `options`, daje od 0,550 do <!-- ocena-bez-se: opis rozstępu, SE w tabeli powyżej --> <!-- liczba-spoza-wynikow: liczba podzbiorów, klucz podzbiory_pol.n -->
0,630, z medianą 0,590. Tyle mniej więcej daje samo losowanie 200 z 273 dokumentów: SD to 1,8 pkt wokół 0,590. Wariant <!-- liczba-spoza-wynikow: klucze podzbiory_pol i sd_podproby_200 w results/wsc273.json -->
główny, 0,605, leży w górnej części tego zakresu, więc nie jest pewną próbką Space. Różnice nie mają osobnego testu, bo
próbki w większości się pokrywają. Wynik pełnego splitu od tego wyboru nie zależy.
