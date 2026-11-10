# Czyszczenie zbiorów danych: techniki i kontrola

Przepis na budowę i czyszczenie zbiorów do pretreningu małych modeli, dla ludzi i agentów. Powstał z kontroli dwóch korpusów: polskiego (PDF-y, tłumaczone rozumowania, książki, dokumenty urzędowe) i angielskiego (książki z domeny publicznej, wiki, podręczniki). Liczby pochodzą z tych kontroli. Docelowo dokument przejdzie do repo ze zbiorami.

Jak korzystać: przeczytaj [zasadę główną](#zasada-główna), idź [kolejnością kroków](#kolejność-kroków), przed publikacją przejdź [listę kontroli](#co-musi-być-sprawdzone), a każdą nową wadę dopisz do [rejestru](#rejestr-wad).

## Zasada główna

**Wadliwy dokument usuń w całości i usuń całą klasę takich dokumentów. Nie łataj przykładów.**
Reguła pisana pod ostatnie znalezisko przepuszcza tę samą wadę w innym zapisie. Runda usunęła 2 938 dokumentów, a następna kontrola zgłosiła te same klasy (ISO-8859-2, UTF-8 czytane jako cp1250). Kolejne rundy kosztują więcej niż kilka procent tokenów.

## Kolejność kroków

1. Zapisz listę źródeł oraz licencję, autora i rewizję per wiersz, zanim cokolwiek stokenizujesz. Bez autora albo licencji tekst nie wchodzi.
2. Ustal listę baz i testów do porównania przed dedupem, nie po nim.
3. Normalizacja znaków: NFC, ligatury, miękkie łączniki, odzyskanie akapitów. Bez NFKC na całości.
4. Filtry jakości, znaków i danych osobowych na całej puli. Kwotę tokenów licz dopiero po nich, inaczej późne usunięcia zmieniają skład.
5. Cięcie długich dokumentów.
6. Dedup i 13-gramy wobec testów **po ostatnim kroku zmieniającym tekst**. Dedup przed cięciem książek przepuścił 7 identycznych i 32 bliskie kopie z jednej książki. Maskowanie też tworzy duplikaty.
7. Po tym kroku już tylko usuwanie całych wierszy.
8. Manifest, atrybucję i kartę generuj z gotowego pliku, nie pisz ręcznie.

## Techniki i parametry

| Co | Technika | Parametry, od których zacząć |
|---|---|---|
| Identyczne | hash tekstu po normalizacji (NFKC, casefold, zwinięcie białych znaków) | próg 0 par |
| Bliskie kopie | MinHash LSH na 5-gramach słów, potem dokładny Jaccard | 128 funkcji, pasma 32x4, J >= 0,8 |
| Rodziny wydań książek | autor i tytuł plus MinHash, zostaje najczystsze wydanie | 112 funkcji, pasma 14x8, J >= 0,75 |
| Powtórzone fragmenty | podciągi wspólne | od 50 słów albo 500 bajtów |
| Pokrycie z bazami | MinHash i szkic 13-gramów | `hash % 16 == 0`, udział >= 0,5, min. 4 próbki |
| Przecieki testów | 13-gramy słów, każde trafienie usuwa wiersz | krótsze odpowiedzi tylko licz; n-gramy nie łapią parafraz |
| Zepsute znaki | próby odwrócenia przekodowań plus leksykon | cp1250, cp1252, latin1, latin2, cp852, mac_roman, koi8_r, cp437, cp866, także podwójnie |
| Formułki | częstość linii i akapitów w całym korpusie | akapit od 5 słów w co najmniej 5 dokumentach |
| Dane osobowe | wzorce z sumą kontrolną, filtr klasy dokumentu, NER | PL: NERGAL, EN: Presidio albo spaCy |
| Walidacja | podział po rodzinie dzieła | `sha1(rodzina) % 200 == 0` |

## Znaki

- Od pierwszej wersji jeden ogólny detektor. Sam `ftfy` i U+FFFD nie wystarczą: kontrola znalazła 0 trafień ftfy i kilkaset dokumentów z popsutymi literami.
- Osobno: `?` albo `Ŝ` zamiast polskiej litery, rozłożone diakrytyki (NFD), glify obcego pisma w środku słowa, ligatury z PDF-ów.
- Progi ustal na ręcznym przeglądzie 100 najgorszych dokumentów i sprawdź na czystej próbce. `ftfy.badness` rośnie z długością tekstu, więc licz na 1 mln znaków.

## Dane osobowe

- Regexy nie wystarczą. Łapią telefony i e-maile, ale listy chrztów, zmarłych, ofiarodawców, klas szkolnych i adresy bez „ul.” przechodziły przez kolejne kontrole.
- Filtruj klasę dokumentu: gazetki parafialne, ogłoszenia duszpasterskie, wykazy imienne, tabele osób. Do tego NER na tekście końcowym na całym pliku, nie na próbce.
- Najlepszy sygnał list: wiele wierszy „imię nazwisko + data” w jednym dokumencie.
- W fikcji odróżniaj postacie od osób realnych. Osoby realne siedzą w przedmowach, stopkach i załącznikach, więc te miejsca skanuj osobno.
- Numery z sumą kontrolną (PESEL, NRB) waliduj, inaczej fałszywe trafienia zasłonią prawdziwe. Wyjątki, np. syntetyczne e-maile w kodzie, zapisz przed kontrolą.

## Książki i PDF-y

- Końce książek to śmieci: katalogi wydawców z cenami („2s. 6d., cloth”, „crown 8vo”), reklamy, spisy treści, indeksy. Przeszły przez filtry i wyszły dopiero w losowej próbce 20 fragmentów. Potrzebny detektor gęstości wierszy katalogowych.
- Filtry webowe (interpunkcja końca linii, krótkie linie, duplikaty linii) wycinają poezję, dialogi i twardo łamany tekst. Nie stosuj ich do książek bez sprawdzenia.
- Formułki usuwaj po częstości: „Conflict of Interest” stało w 3 036 dokumentach mimo reguły. Przed złożeniem pliku przeczytaj 200 najczęstszych linii i akapitów.
- Do fikcji wybieraj źródła tekstowe zamiast OCR i PDF.

## Licencje

- Licencja rozdziału albo platformy to nie licencja tomu ani treści. Przy czystych metadanych 416 książek miało w tekście deklarację NC, ND albo SA dla całego tomu.
- **Sprawdzaj licencję przed usuwaniem formułek.** Usunięcie stopek kasuje dowód licencji.
- Domena publiczna: miarą jest UE/PL. Autor i tłumacz zmarli najpóźniej w 1955, sam status „public domain in the USA” nie wystarcza.
- CC BY-SA trzymaj w osobnym configu. Zakres ShareAlike na wagach modelu jest nierozstrzygnięty.
- Tokeny bez licencji utworu (wyjątek TDM, dokumenty urzędowe) policz i podaj w karcie osobno. W jednym ze zbiorów było to 74%.

## Co musi być sprawdzone

Przed każdą publikacją, na całym pliku, przez osobnego agenta bez wiedzy o budowie i bez wglądu w jej skrypty. Progi zapisz przed przebiegiem i nie zmieniaj ich po wynikach. BLOCKED i NOT RUN to nie PASS.

| Punkt | Warunek zaliczenia |
|---|---|
| Znaki | 0 dokumentów z U+FFFD, sterującymi C0/C1 (poza `\t\n\r`) i popsutymi literami; detektor z czułością >= 95% na wstrzykniętych przykładach i FP <= 1% |
| Powtórki | 0 identycznych; < 0,5% dokumentów w parach bliskich; < 0,5% trafień w bazy na próbie 10 tys.; pełna lista baz na dysku |
| Przecieki testów | 13-gramy wobec wszystkich testów, które model ma zdawać; test nie do pobrania to BLOCKED |
| Licencje | każdy wiersz z dozwoloną licencją i atrybucją; deklaracje sprawdzone też w tekście; udział tokenów bez licencji utworu podany |
| Dane osobowe | 0 każdej klasy, wzorce na całym pliku, filtr klas, NER i ręczne czytanie 200 dokumentów o najwyższym ryzyku |
| Jakość tekstów | czytanie 50 losowych dokumentów z zapisanym ziarnem, więcej niż 2 bezsensowne to FAIL; przegląd 200 najczęstszych linii; człowiek czyta własną losową próbkę |
| Manifest i karta | wiersze, tokeny i sha256 zgodne z plikiem; każde zdanie karty sprawdzone wobec pliku; zero ścieżek lokalnych |

Dodatkowo: testuj detektory na wstrzykniętych błędach (100 duplikatów, 100 zepsutych tekstów) i na czystej próbce. Publikuj tylko po PASS dla sha256 tego samego pliku, bo plik raz wgrany zostaje w historii repo i ktoś zdąży go pobrać.

## Jak nie powtarzać błędów

Każda wada znaleziona po filtrach (przez kontrolę albo człowieka) ma dać trzy rzeczy, zanim zamkniesz zbiór:

1. Usunięcie całej klasy, nie przykładu.
2. Ogólny detektor albo punkt kontroli, z testem na wstrzykniętym przykładzie, tu w katalogu.
3. Wiersz w [rejestrze wad](#rejestr-wad).

Przy każdym zbiorze zapisz: liczbę rund kontroli do PASS, czas od startu do PASS i wady znalezione dopiero przez człowieka. Te liczby mają maleć z każdym zbiorem, a jeśli rosną, to detektory są za wąskie.

## Rejestr wad

| Wada | Jak przeszła | Co ją łapie |
|---|---|---|
| Przekodowania w innych zapisach | reguły pod ostatni przykład | ogólny detektor przekodowań |
| Listy osób z datami, adresy bez „ul.” | same regexy | filtr klasy dokumentu, NER na całym pliku |
| Kopie z jednej książki | dedup przed cięciem | dedup po ostatniej zmianie tekstu |
| Formułka w 3 036 dokumentach | reguła na znany zapis | częstość linii, czytanie najczęstszych |
| NC/ND/SA tomu w książkach | sprawdzane same metadane | deklaracje w tekście przed usunięciem stopek |
| Katalogi wydawców na końcu książek | brak detektora, znalazł człowiek | gęstość wierszy katalogowych |
| Karta obiecuje filtry, których plik nie spełnia | karta pisana ręcznie | karta z pliku, zdanie po zdaniu wobec pliku |
| Porównanie z niepełnymi bazami | brak części baz na dysku | lista baz przed dedupem, braki to BLOCKED |

## Wspólne skrypty

Skrypty budowy i kontroli dojdą do tego katalogu po przejściu kontroli angielskiego korpusu, żeby trafiły tu tylko sprawdzone:

- `build`: kroki w kolejności z tego dokumentu, każdy z logiem liczby wierszy i tokenów per źródło i powód usunięcia.
- `control`: osobne wejście, progi z pliku, wynik PASS, FAIL albo BLOCKED per punkt, lista id z powodem.
- `release`: odmawia wysyłki bez PASS dla tego sha256 i bez karty wygenerowanej z pliku.
