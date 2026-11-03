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

| próbka | baza | różnica | SE | test | werdykt |
|---|---|---:|---:|---|---|
| panel 200 | losowa | +10,5 pkt | 0,0347 | z = 3,03 | pewne |
| panel 200 | większościowa | +8,5 pkt | 0,0469 | z = 1,81 | szum |
| pełny split | losowa | +9,0 pkt | 0,0298 | z = 3,01 | pewne |
| pełny split | większościowa | +8,8 pkt | 0,0440 | z = 1,997 | szum |

Model i stała odpowiedź odpowiadają na te same pytania, więc SE różnicy wobec bazy większościowej jest parowane
(`research/README.md`, „SE i werdykt”). Wobec bazy losowej, czyli stałej, SE to SE trafności.

Nad bazą losową Slayer 1.06 leży tuż nad progiem „pewne” (|z| ≥ 3). Różnica wobec bazy większościowej to szum, na <!-- ocena-bez-se: opis progu werdyktu, SE w tabeli powyżej -->
obu próbkach.

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
