# Rejestr datasetów: użyte i kandydaci

Jedno miejsce na pytanie „czy ten zbiór już był?” przy pracy nad danymi Slayera 1B.

Zasady wpisu:

- **status**: `użyty` (jest w treningu któregoś modelu), `kandydat` (czeka na test), `wstrzymany`
  (czeka na wyjaśnienie). Odrzucone stoją osobno, w sekcji 4.
- **licencja**: tak, jak podaje karta zbioru; „niesprawdzone” znaczy, że nikt jej nie potwierdził u
  źródła.
- **data**: dzień decyzji (dla `użyty`: dzień zapisu w manifeście).
- Kandydat przechodzi na `użyty` dopiero po teście z progiem z góry (protokół: `wygaszanie/PROGI.md`).

## 1. Slayer 1B — `SlayerLab/slayer-pl-8x3b`

Proporcje scenariusza B z karty zbioru (tak samo w `wygaszanie/dane.py`). Tabela niżej to wpisy z 30.10 (skład z
karty). Licencje u źródła, rozbite na składniki, są w podsekcjach 1.1–1.5 (sprawdzone 2026-11-04, zadanie A4).

| nazwa HF/URL | licencja | status | powód | data |
|---|---|---|---|---|
| `SlayerLab/slayer-pl-8x3b` → `web` (HPLT v3 PL, top WDS, pakiety `pack-NN`) | wg karty zbioru CC0-1.0; u źródła CC0 HPLT obejmuje tylko opakowanie, nie teksty stron (1.2) | użyty | 63% tokenów Slayera 1.06; nakłada się z FineWeb2/FineWeb2-HQ pol, więc każdy kandydat z Common Crawl wymaga dedupu wobec HPLT | 2026-10-30 |
| `SlayerLab/slayer-pl-8x3b` → `core` / `core_sa` (wikipedia, wikibooks, wikivoyage, wikisource, polqa, govpl, wolne_lektury) | CC-BY / CC-BY-SA (per źródło); w danych są też `polish_news`, `elka_pl_news` (apache-2.0, u źródła nieustalone), `poquad`, `wikinews`, `eltec_pol`, `1000_novels`, `biblioteka_nauki` (1.2) | użyty | 19%; polqa w rdzeniu kontaminuje test PolQA (7/200 pytań bez trafień); govpl może zawierać dane wrażliwe: karta [polish-dynaword](https://huggingface.co/datasets/SlayerLab/polish-dynaword) mówi, że filtry nie usuwają w pełni danych osobowych, a przebieg PII (NERGAL) dopiero w v0.2.7; do tego czasu obowiązują datasheety poszczególnych źródeł (do przeczytania) | 2026-10-30 |
| `SlayerLab/slayer-pl-8x3b` → `legal` / `legal_sa` (eurlex, parliamentary, dziennik_ustaw, govpl) | CC-BY-4.0 / PD / CC-BY-SA (govpl), wg `dataset.json`; u źródła eurlex to polityka ponownego wykorzystania KE, nie CC-BY-4.0 dla aktów (1.2) | użyty | 8%; dane wrażliwe jak przy `core` (brak przebiegu PII przed v0.2.7 polish-dynaword); wg karty eurlex ma licencję `LicenseRef-EU-Reuse-Policy` (nie CC-BY-4.0), a parliamentary zostawia tylko oficjalnych mówców, interpelacje wstrzymane do v0.2.7 | 2026-10-30 |
| `SlayerLab/slayer-pl-8x3b` → `en` | ODC-BY (wg karty), u źródła potwierdzone dla fineweb-edu; finemath z `dataset.json` w danych nie ma (1.2) | użyty | 10%; wg `dataset.json` zbioru to fineweb-edu + finemath (ODC-BY), 2,40 mld tok.; dekontaminacja opisana tylko dla web i tylko wobec 8tags/polemo2; wobec ARC była, wobec MMLU niepewne, do sprawdzenia (zadanie A2) | 2026-10-30 |

### 1.1 Co sprawdzono i jak (A4, 2026-11-04)

To przegląd źródeł, nie opinia prawna. Nikt w tym repo nie jest prawnikiem, a wnioski niżej mówią, co piszą
źródła, nie jak oceniłby je sąd.

- Zbiór: [`SlayerLab/slayer-pl-8x3b` @ `d50df04`][s-tree]; gałąź `main` zbioru wskazuje dziś na ten sam commit.
- Lista składników: [`dataset.json`][s-dataset], [`shared/manifest.json`][s-shared], `pack-00/manifest.json` …
  `pack-07/manifest.json` (wszystkie osiem przeczytane; każdy podaje tylko `web` z licencją CC0-1.0 i odsyłacze do
  `shared/`), [karta `README.md`][s-readme], `card.yaml`, `pii-check.json`.
- Manifesty nie mówią, z jakich źródeł składają się partycje `shared/`. Skład odczytano z samych danych: kolumny
  `source_id`, `license`, `provenance` przez [`/rows` datasets-server][rows-ex] (eksport parquet ma te same rozmiary
  plików co oryginały). Każde źródło leży w jednym ciągłym bloku wierszy; granice bloków znalezione z dokładnością do
  jednego wiersza (jedna granica, koniec `wikisource`, z ciągłości numeracji `document_id`, bo `/rows` zwracał tam
  błąd). Liczby wierszy per źródło sumują się dokładnie do `wiersze` z manifestu i do `rozklad_rejestrow`.
  Zapisano tylko metadane, bez treści dokumentów.
- `license` sprawdzono w odczytanych wierszach każdego bloku (od kilku do kilkuset na blok), nie w każdym wierszu.
  W żadnym odczytanym bloku nie było dwóch różnych wartości `license`.
- Licencji u źródła szukano na stronach źródeł, w kartach HF (link z commitem) i w kartach `polish-dynaword`
  (link z commitem [`cc80dd9`][d-readme], gałąź `main` z 2026-11-04). Tag YAML karty HF zapisano osobno od tego, co
  mówi źródło. Strony spoza HF: data odczytu 2026-11-04.
- Liczby tokenów są tylko w manifestach i tylko per partycja (`core`, `core_sa`, `legal`, `legal_sa`, `en`, `web`).
  Tokenów per źródło zbiór nie podaje; nie liczono ich (bez pobierania parquetów).

### 1.2 Składniki → licencja u źródła

Kolumny: składnik (`source_id` w danych), część, licencja u źródła (krótki cytat, link), deklaracja (kolumna
`license` w danych; `dataset.json`; karta), czy się zgadzają, uwagi (SA = ta sama licencja dla utworów zależnych,
BY = uznanie autorstwa, NC = bez użytku komercyjnego, AI = klauzula o trenowaniu/TDM; dane osobowe), liczba wierszy
w zbiorze (dokładna, z granic bloków).

| składnik | część | licencja u źródła | deklaracja | zgodne? | uwagi | wiersze |
|---|---|---|---|---|---|---|
| `hplt_v3_pl` (HPLT v3 PL, WDS) | `web` (pack-00 … pack-07) | [HPLT v3.0][hplt]: „We do not own any of the text from which these text data has been extracted”; „We license the actual packaging of these text data under the Creative Commons CC0 license”; [karta HF][hplt-hf] `license: cc0-1.0` | `CC0-1.0`; `dataset.json`: `web: CC0-1.0`; karta: „Warstwa web: CC0-1.0” | rozbieżne co do zakresu: CC0 obejmuje opakowanie, prawa do tekstów stron nieustalone | brak SA/BY/NC; HPLT odsyła do dyrektywy 2019/790 (wyjątek TDM i opt-out) i RODO; usuwanie na żądanie: e-mail `hplt-datasets@ufal.mff.cuni.cz`, „removing the affected sources from the next release”, czyli dopiero w następnym wydaniu HPLT, nie w naszej kopii; `polish-dynaword` wycofał HPLT: „Licence unverified: HPLT's CC0 covers its packaging, not the crawled pages” ([README][d-readme]) | 11289649 <!-- liczba-spoza-wynikow: suma web_wiersze z pack-00…07/manifest.json -->|
| `wolne_lektury_full` | `core` | [Wolne Lektury, prawa][wl-prawa]: „Wszystkie utwory w bibliotece znajdują się w domenie publicznej bądź są udostępnione na jednej z wolnych licencji” | `public-domain` (cały blok); `dataset.json` go nie wymienia | rozbieżne: jedna etykieta PD, a biblioteka ma też utwory na Licencji Wolnej Sztuki i CC BY-SA ([CHANGELOG `polish-dynaword`][d-changelog], v0.2.6: etykiety per książka) | możliwe SA/LWS w partycji „permissive”; skąd pobrano blok (`provenance` = `wolne_lektury_full`): nieustalone | 5318 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `1000_novels` (dwa bloki: `provenance` `1000_novels` i `dynaword`) | `core` | u źródła nieustalone; `polish-dynaword` wycofał źródło 2026-10-17: „no row records the edition its text follows, so a protected preface, abridgement or editor's corrections cannot be ruled out” ([README][d-readme]) | `CC-BY-4.0`; `dataset.json` go nie wymienia | nieustalone | ryzyko praw do wydania (przedmowy, skróty, korekty redakcji) | 1984 <!-- liczba-spoza-wynikow: granice obu bloków w /rows, A4 -->|
| `eltec_pol` | `core` | [ELTeC-pol][eltec]: „All texts included in this collection are in the public domain.” | `CC-BY-4.0` | rozbieżne, ale etykieta jest ostrzejsza niż źródło | brak SA/NC | 100 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `polish_news` (artykuły tvp.info) | `core` | TVP S.A.: nieustalone (miejsca w 1.4); [karta `WiktorS/polish-news`][pn-hf]: `license: apache-2.0`, „articles obtained from polish news site tvp.info.pl”; karta nie wspomina zgody TVP | `apache-2.0`; ani `dataset.json`, ani karta zbioru go nie wymieniają | nieustalone: apache-2.0 to deklaracja autora scrapera, nie TVP | pełne artykuły prasowe: [ustawa][upapp] art. 4 wyłącza spod ochrony tylko „proste informacje prasowe”; [robots.txt tvp.info][tvp-robots] bez wpisów dla botów AI, `/.well-known/tdmrep.json` 404; teksty z nazwiskami osób | 246601 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `elka_pl_news` (artykuły elka.pl) | `core` | Radio Elka Sp. z o.o.: nieustalone (miejsca w 1.4); [karta `winterkitsune/elka-pl-news`][elka-hf]: `license: apache-2.0`, „scraped news articles from polish, regional news site https://elka.pl” | `apache-2.0`; `dataset.json` go nie wymienia | nieustalone: jak `polish_news` | lokalne wiadomości (policja, wypadki) z nazwiskami osób prywatnych | 85234 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `wikinews` | `core` | [pl.wikinews, Prawa autorskie][wn]: „Skrót: CC-BY 2.5”; `polish-dynaword` v0.2.6 etykietuje CC BY 2.5 albo 4.0 per rekord ([README][d-readme]) | `CC-BY-2.5` | zgodne co do rodzaju; wersja per rekord nieustalona | BY | 22941 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `poquad` | `core` | u źródła nieustalone; [karta `clarin-pl/poquad`][poquad-hf] ma tylko YAML `license: cc-by-4.0` i zdanie „PoQuaD dataset”, bez opisu źródła kontekstów | `CC-BY-4.0` | nieustalone (jest tylko deklaracja karty) | BY; jeśli konteksty pochodzą z Wikipedii, to także SA (nieustalone) | 13038 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `wikibooks` | `core_sa` | [Wikimedia Terms of Use][wm-tou], §7: „you agree to license the modified or added content under CC BY-SA 4.0 or later”; uznanie autorstwa „Through hyperlink (where possible) or URL to the page” | `CC-BY-SA-3.0`; `dataset.json`: CC-BY-SA | zgodne co do rodzaju (BY-SA); wersja per rekord nieustalona | SA, BY; blok spoza `polish-dynaword` (`provenance` = `wikibooks`), więc bez jego późniejszego przeglądu praw | 8746 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `wikivoyage` | `core_sa` | jak `wikibooks` ([ToU][wm-tou]) | `CC-BY-SA-3.0`; `dataset.json`: CC-BY-SA | zgodne co do rodzaju; wersja nieustalona | SA, BY; `polish-dynaword` v0.2.6 wyłączył strony z `{{Atrybucja}}` (tekst z Wikitravel), ten blok jest spoza `polish-dynaword` i takiego filtra nie miał (nieustalone, czy je zawiera) | 7743 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `wikipedia` | `core_sa` | jak `wikibooks` ([ToU][wm-tou]) | `CC-BY-SA-3.0`; `provenance` `dynaword` | zgodne co do rodzaju; `polish-dynaword` v0.2.6 etykietuje 3.0, 4.0 albo oba per rekord i usunął strony z oznaczeniem naruszenia praw; tu jest starszy zrzut SpeakLeash bez tych zmian ([CHANGELOG][d-changelog]) | SA, BY; karta `polish-dynaword`: w ręcznej próbie część stron miała tekst skopiowany z utworów chronionych ([README][d-readme], „Copied text in Wikipedia”) | 1171665 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `wolne_lektury` | `core_sa` | [Wolne Lektury, zasady][wl-zasady]: „Twój utwór musi być opublikowany na tej samej licencji, co oryginał tj. CC BY-SA lub Licencja Wolnej Sztuki.” | `CC-BY-SA-4.0` (cały blok); `provenance` `dynaword` | rozbieżne: `polish-dynaword` nazywa tę jednolitą etykietę błędną („which is wrong”); per dokument: domena publiczna, LAL 1.3, CC BY-SA 3.0 PL/3.0/4.0 ([README][d-readme]) | SA i copyleft LWS (LWS ma własne warunki, §2.3 i §4 wg karty `polish-dynaword`) | 6141 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `wikisource` | `core_sa` | [Wikiźródła, prawa autorskie][ws]: teksty chronione muszą mieć licencję „(musi być zgodna z CC BY-SA 4.0)”, licencja jest per tekst | `CC-BY-SA-3.0`; `provenance` `dynaword` | rozbieżne: `polish-dynaword` wycofał źródło 2026-10-05, bo jednolita etykieta „also covered in-copyright post-war imprints that carry their own per-page licences” ([README][d-readme]) | SA, BY, GFDL per tekst; teksty chronione bez wymaganej atrybucji | 631941 <!-- liczba-spoza-wynikow: granice bloku w /rows (koniec z ciągłości document_id), A4 -->|
| `biblioteka_nauki` | `core_sa` | [datasheet `polish-dynaword`][d-bn]: licencja per dokument z API Biblioteki Nauki, CC BY albo CC BY-SA; „The upstream collection includes all-rights-reserved items, so a per-item gate is mandatory” | `CC-BY/CC-BY-SA` (jedna etykieta na blok) | rozbieżne: rodzaj i wersja per rekord utracone; po przeglądzie z października `polish-dynaword` odrzucił rekordy z wydrukowaną licencją NC/ND, przedruki i rekordy starsze niż wersja licencji ([datasheet][d-bn]); tu są wiersze sprzed tego przeglądu | SA dla części rekordów; NC/ND w części tekstów wg datasheetu | 41985 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `polqa` | `core_sa` | [karta `ipipan/polqa`][polqa-hf]: `license: cc-by-sa-4.0`; „The evidence passages come from the Polish Wikipedia (March 2022 snapshot)” | `CC-BY-SA-4.0`; `dataset.json`: CC-BY-SA | zgodne (pasaże z Wikipedii, BY-SA); licencja pytań (PolEval, teleturnieje) nieustalona | SA, BY; kontaminacja testu PolQA (wiersz w tabeli wyżej) | 6335823 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `fineweb-edu` (sample-100BT) | `en` | [karta `HuggingFaceFW/fineweb-edu`][fwe]: „released under the Open Data Commons Attribution License (ODC-By) v1.0 … also subject to CommonCrawl's Terms of Use” | `ODC-BY`; `dataset.json`: „fineweb-edu ODC-BY”, „finemath ODC-BY” | zgodne dla fineweb-edu; **finemath zadeklarowany, a w danych go nie ma**: cała partycja `en` to `fineweb-edu` ([karta finemath][fm], też ODC-By) | BY (ODC-By); Terms of Use Common Crawl nieotwarte; prawa do tekstów stron jak przy HPLT | 2384000 <!-- liczba-spoza-wynikow: shared/manifest.json, en.parquet wiersze -->|
| `eurlex` | `legal` | nota EUR-Lex: nieustalone (miejsca w 1.4); [decyzja 2011/833/UE][d833] (kopia lawplayer.com, nie tekst urzędowy) art. 6 ust. 2: „(a) the obligation for the reuser to acknowledge the source of the documents; (b) the obligation not to distort the original meaning or message”; art. 2 ust. 2 lit. b wyłącza dokumenty z prawami osób trzecich; [KE o decyzji z 2019][ec2019]: „CC BY 4.0 for all content” | `CC-BY-4.0`; `dataset.json`: „eurlex CC-BY-4.0”; karta `polish-dynaword` dziś: `LicenseRef-EU-Reuse-Policy` | rozbieżne: `polish-dynaword` zmienił etykietę, bo nota EUR-Lex „grants CC BY 4.0 only for consolidated texts and editorial content, not the acts themselves, and excludes third-party material”, i usunął dokumenty z materiałem osób trzecich ([README][d-readme]); tu jest wersja sprzed tych zmian | BY (wskazanie źródła), zakaz zniekształcania sensu; o utworach zależnych decyzja 2011/833 nie ma osobnej klauzuli (art. 8 ust. 2 i art. 9 ust. 3 dotyczą tylko adaptacji robionych przez Komisję); art. 4 odsyła do ochrony danych osobowych | 105539 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `parliamentary` | `legal` | [Polish Parliamentary Corpus][ppc]: „The parliamentary data is public domain. The corpus annotations are available on CC-BY (attribution) licence.”; [ustawa][upapp] art. 4: „2) urzędowe dokumenty, materiały, znaki i symbole” | `public-domain`; `dataset.json`: „parliamentary PD” | zgodne co do statusu tekstów; anotacje PPC na CC-BY | wersja sprzed przebudowy v0.2.6: bez filtra „only official speakers”, a interpelacje Sejmu `polish-dynaword` wstrzymał do v0.2.7, bo „a typical one is a named person's case” ([CHANGELOG][d-changelog]); czy ten blok je zawiera: nieustalone | 139586 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `dziennik_ustaw` | `legal` | [ustawa][upapp] art. 4: „1) akty normatywne lub ich urzędowe projekty”; nota o ponownym wykorzystaniu na [dziennikustaw.gov.pl][du]: nieustalone | `public-domain`; `dataset.json`: „dziennik_ustaw PD” | zgodne | brak SA/BY/NC | 16898 <!-- liczba-spoza-wynikow: granice bloku w /rows, A4 -->|
| `govpl` | `legal_sa` | [gov.pl, prawa autorskie][govpl]: „Treści tekstowe publikowane w serwisie (z wyłączeniem treści audiowizualnych), są udostępniane na licencji typu Creative Commons: uznanie autorstwa - na tych samych warunkach 4.0 (CC BY-SA 4.0).”; utwory osób trzecich: „Ich wykorzystanie przez internautów wymaga zgody właścicieli tych materiałów.” | `CC-BY-SA-4.0`; `dataset.json`: „govpl CC-BY-SA” | zgodne z dzisiejszą stopką, ale wcześniej stopka była NC-ND: archiwalne kopie [z 2023-12-22][govpl-wb2023] i [z 2025-01-06][govpl-wb2025] mają w stopce „Wszystkie treści publikowane w serwisie są udostępniane na licencji Creative Commons: uznanie autorstwa - użycie niekomercyjne - bez utworów zależnych 3.0 Polska (CC BY-NC-ND 3.0 PL), o ile nie jest to stwierdzone inaczej.”, a treść tej strony w obu kopiach: „Korzystanie przez użytkowników z materiałów urzędowych opublikowanych w serwisie Gov.pl nie wymaga zgody Ministra Cyfryzacji.”; granice okresu NC-ND (2022-08-19 – 2025-12-12) i wcześniejsze CC BY 3.0 PL znam tylko z [datasheetu `polish-dynaword`][d-govpl], nie z kopii, które otworzyłem; datasheet: objęcie starszych tekstów dzisiejszą ofertą „is our reading; it is not certain” | SA, BY; możliwe NC/ND dla tekstów z okresu stopki NC-ND; tu jest pełna wersja v0.2.2–v0.2.5, z przedrukami PAP, innymi tekstami osób trzecich i komunikatami prokuratur, które v0.2.6 usuwa („personal data about offences, GDPR Art. 10”) | 88190 <!-- liczba-spoza-wynikow: shared/manifest.json, legal_sa.parquet wiersze -->|

Wersja `polish-dynaword` w `slayer-pl-8x3b`: kolumna `provenance` mówi tylko `dynaword` albo
`polish-dynaword/<źródło>`, bez wersji, więc wersja nie jest zapisana w danych. Z liczb wierszy wynika v0.2.4 albo
v0.2.5 (`main` między 2026-08-07 a 2026-08-28):

- `govpl` ma tyle wierszy, ile wydania v0.2.2–v0.2.5 (88 190, [CHANGELOG][d-changelog]); <!-- liczba-spoza-wynikow: CHANGELOG polish-dynaword, v0.2.2 -->
- `biblioteka_nauki` weszła do wydania w v0.2.4;
- `wikisource` i stary zrzut `wikipedia` zniknęły w v0.2.6;
- commit zbioru jest z 2026-08-28, a v0.2.5 wyszło 2026-08-14.

Tagi v0.2.0–v0.2.5 skasowano 2026-10-22, a pliki wycofanych źródeł usunięto z magazynu HF, więc tej wersji nie da się
już pobrać ani porównać. Każda wersja przed v0.2.7 jest sprzed przebiegu PII NERGAL. Karta `polish-dynaword`
([README][d-readme], „Personal & sensitive data”): „The corpus can also hold personal data about private persons,
which our filters do not fully remove” oraz „v0.2.6 ships before the NERGAL pass”. Dla `govpl` i `parliamentary`
działały więc tylko filtry samych źródeł.

### 1.3 Tokeny i udziały

Tokeny cl100k z manifestów zbioru, per partycja (per źródło zbiór ich nie podaje):

- `web` (osiem pakietów razem): 15 120 001 641 tok. <!-- liczba-spoza-wynikow: dataset.json, realizacja.web_tokeny_cl100k -->
- `core`: 162 205 785 tok. <!-- liczba-spoza-wynikow: shared/manifest.json, core.parquet -->
- `core_sa`: 3 546 606 209 tok. <!-- liczba-spoza-wynikow: shared/manifest.json, core_sa.parquet -->
- `legal`: 1 920 115 782 tok. <!-- liczba-spoza-wynikow: shared/manifest.json, legal.parquet -->
- `legal_sa` (tylko `govpl`): 80 666 129 tok. <!-- liczba-spoza-wynikow: shared/manifest.json, legal_sa.parquet -->
- `en` (tylko `fineweb-edu`): 2 401 565 319 tok. <!-- liczba-spoza-wynikow: shared/manifest.json, en.parquet -->
- razem fizycznie: 23 231 160 865 tok. <!-- liczba-spoza-wynikow: dataset.json, realizacja.backbone_fizyczny_tokeny_cl100k -->

Uwaga do `core` i `core_sa`: manifest pisze „tokeny rdzenia prorata po wierszach”, więc podział tokenów rdzenia
między te dwie partycje to szacunek producenta z liczby wierszy, nie pomiar. W `core` przeważają długie artykuły
newsowe, w `core_sa` krótkie pasaże `polqa`, więc rzeczywisty podział może się różnić; do przeliczenia tiktokenem.

Udział partycji share-alike (`core_sa` + `legal_sa`) w tokenach:

- fizycznie, w całym zbiorze: 15,61% <!-- liczba-spoza-wynikow: (3546606209+80666129)/23231160865, z manifestów -->
- w treningu jednego pakietu: 18,49% <!-- liczba-spoza-wynikow: wagi 0,19 i 0,08 z pack-XX/manifest.json, podział wewnątrz grupy proporcjonalnie do tokenów partycji (założenie, nieustalone) -->

Druga liczba zakłada, że wewnątrz grup `rdzen` i `legal` (wagi z `pack-XX/manifest.json`) próbkuje się
proporcjonalnie do tokenów partycji; manifesty tego nie mówią.

Wiersze per wartość kolumny `license` (pełne dane, wszystkie wiersze, z granic bloków; nie tokeny):

- `CC0-1.0`: 11 289 649 wierszy <!-- liczba-spoza-wynikow: granice bloków w /rows, A4 -->
- `CC-BY-SA-4.0`: 6 430 154 wierszy <!-- liczba-spoza-wynikow: wolne_lektury+polqa+govpl, granice bloków, A4 -->
- `ODC-BY`: 2 384 000 wierszy <!-- liczba-spoza-wynikow: granice bloków w /rows, A4 -->
- `CC-BY-SA-3.0`: 1 820 095 wierszy <!-- liczba-spoza-wynikow: wikibooks+wikivoyage+wikipedia+wikisource, granice bloków, A4 -->
- `apache-2.0`: 331 835 wierszy <!-- liczba-spoza-wynikow: polish_news+elka_pl_news, granice bloków, A4 -->
- `public-domain`: 161 802 wierszy <!-- liczba-spoza-wynikow: wolne_lektury_full+parliamentary+dziennik_ustaw, granice bloków, A4 -->
- `CC-BY-4.0`: 120 661 wierszy <!-- liczba-spoza-wynikow: 1000_novels+eltec_pol+poquad+eurlex, granice bloków, A4 -->
- `CC-BY/CC-BY-SA`: 41 985 wierszy <!-- liczba-spoza-wynikow: biblioteka_nauki, granice bloków, A4 -->
- `CC-BY-2.5`: 22 941 wierszy <!-- liczba-spoza-wynikow: wikinews, granice bloków, A4 -->

Składniki CC-BY-SA (wg kolumny `license`) z tokenami, o ile da się je podać:

- `govpl`: cała partycja `legal_sa`, 80 666 129 tok. <!-- liczba-spoza-wynikow: shared/manifest.json, legal_sa.parquet -->
- `wikipedia`, `wikisource`, `wolne_lektury`, `biblioteka_nauki` (część), `polqa`, `wikibooks`, `wikivoyage`: razem
  partycja `core_sa`, tokenów per źródło zbiór nie podaje (nieustalone). Dla orientacji karta `polish-dynaword` podaje
  dla tych samych źródeł w v0.2.5 (liczby wierszy tu różnią się od nich o mniej niż jeden procent):
  - `wikisource`: 801 947 427 tok. <!-- liczba-spoza-wynikow: CHANGELOG polish-dynaword, wikisource v0.2.0-v0.2.5 -->
  - `wikipedia`: 707,2 mln tok. <!-- liczba-spoza-wynikow: README polish-dynaword, Changes since v0.2.5, wikipedia v0.2.5 -->
  - `biblioteka_nauki`: 673,5 mln tok. <!-- liczba-spoza-wynikow: README polish-dynaword, Changes since v0.2.5, biblioteka_nauki v0.2.5 -->
  - `polqa`, `wolne_lektury`, `wikibooks`, `wikivoyage`: nieustalone.

`polish-dynaword` ma licencję per dokument w kolumnie `license`. Udział tokenów grup licencji policzono na pełnych
danych dzisiejszego v0.2.6 (wszystkie źródła) z tabeli „Sources” [karty][d-readme]. Karta zaokrągla tokeny do
dziesiątych części miliona, a suma zgadza się z jej totalem. To nie jest wersja użyta w `slayer-pl-8x3b`, tylko obraz źródła dziś:

- `LicenseRef-EU-Reuse-Policy` (eurlex): 35,1% <!-- liczba-spoza-wynikow: tabela Sources karty polish-dynaword @cc80dd9, 2333,0/6645,3 mln -->
- CC BY-SA (Wikimedia, govpl, nonsa i małe źródła BY-SA): 26,8% <!-- liczba-spoza-wynikow: tabela Sources karty polish-dynaword @cc80dd9, 1780,7/6645,3 mln -->
- domena publiczna, dokumenty urzędowe: 26,6% <!-- liczba-spoza-wynikow: tabela Sources karty polish-dynaword @cc80dd9, 1768,1/6645,3 mln -->
- licencja per rekord (biblioteka_nauki, wolne_lektury, open_icm_pl): 10,3% <!-- liczba-spoza-wynikow: tabela Sources karty polish-dynaword @cc80dd9, 683,0/6645,3 mln -->
- CC BY (eltec_pol, wikinews, global_voices, nkjp1m, studia_bas): 0,6% <!-- liczba-spoza-wynikow: tabela Sources karty polish-dynaword @cc80dd9, 40,9/6645,3 mln -->
- `ted_pl` („TED notice status, no licence granted”): 0,6% <!-- liczba-spoza-wynikow: tabela Sources karty polish-dynaword @cc80dd9, 39,6/6645,3 mln -->

W `biblioteka_nauki` (v0.2.6) datasheet podaje rekordy, nie tokeny:

- CC BY: 25 705 rekordów <!-- liczba-spoza-wynikow: datasheet biblioteka_nauki polish-dynaword @cc80dd9 -->
- CC BY-SA: 12 138 rekordów <!-- liczba-spoza-wynikow: datasheet biblioteka_nauki polish-dynaword @cc80dd9 -->

Próbka danych osobowych z `pii-check.json` zbioru (wzorce, próbka 20 000 wierszy na plik): <!-- liczba-spoza-wynikow: pii-check.json, pole probka -->

- `core_sa`, trafienia `pesel_like`: 336 <!-- liczba-spoza-wynikow: pii-check.json, shared/core_sa.parquet -->
- `legal`, trafienia `pesel_like`: 116 <!-- liczba-spoza-wynikow: pii-check.json, shared/legal.parquet -->
- `legal_sa` (govpl), trafienia `pesel_like`: 27 <!-- liczba-spoza-wynikow: pii-check.json, shared/legal_sa.parquet -->

### 1.4 Nieustalone: gdzie szukano i czego nie przeszukano

- `polish_news` (TVP S.A.): otwarto [kartę `WiktorS/polish-news`][pn-hf], [robots.txt tvp.info][tvp-robots],
  `https://www.tvp.pl/robots.txt`; `https://www.tvp.info/regulamin`, `https://www.tvp.pl/regulamin`,
  `https://www.tvp.info/4519628/regulamin` i `https://www.tvp.info/.well-known/tdmrep.json` dały 404;
  `https://www.tvp.info/` i `https://vod.tvp.pl/pomoc/strona/regulamin` nie wyrenderowały treści. Nie przeszukano:
  regulaminu tvp.pl w przeglądarce z JS, polityki prywatności TVP, repozytorium scrapera `WiktorSob/scraper-tvp`.
- `elka_pl_news` (Radio Elka): otwarto [kartę `winterkitsune/elka-pl-news`][elka-hf] i stronę główną `https://elka.pl/`
  (stopka: „Regulamin ogłoszeń”, „Polityka prywatności”, „O nadawcy”, bez noty o licencji treści);
  `https://elka.pl/regulamin` dał 404. Nie przeszukano: podstron „O nadawcy” i „Redakcja - kontakt”, robots.txt
  elka.pl (nie odczytał się).
- `1000_novels`: wyszukiwanie zbiorów HF `1000_novels` puste; README i CHANGELOG `polish-dynaword` (tylko opis
  wycofania). Nie przeszukano: Hub PR #1, #49, #55, #65, #124 `polish-dynaword`.
- `poquad`: [karta `clarin-pl/poquad`][poquad-hf] (sama metadana). Nie przeszukano: artykułu ICADL 2022 (DOI z
  karty), strony CLARIN-PL.
- Nota prawna EUR-Lex i polska wersja decyzji 2011/833/UE: `https://eur-lex.europa.eu/content/legal-notice/legal-notice.html`
  (także `?locale=pl`), `https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32011D0833`,
  `…CELEX:32019D1655`, `https://eur-lex.europa.eu/eli/dec/2011/833/oj/pol` i `/eng` blokują automatyczne pobieranie;
  tekst decyzji przeczytano tylko w [kopii lawplayer.com][d833]. Numer decyzji z 2019 (C(2019) 1655) nieustalony.
  Pomocniczo: [nota prawna commission.europa.eu][ec-notice] („licensed under the Creative Commons Attribution 4.0
  International (CC BY 4.0) licence”, z wyłączeniem utworów osób trzecich), która nie jest notą EUR-Lex.
- Dziennik Ustaw: [dziennikustaw.gov.pl][du] bez noty o ponownym wykorzystaniu; ISAP zwrócił stronę anty-botową,
  art. 4 ustawy przeczytano w [tekście pierwotnym z API Sejmu][upapp] (nie w tekście jednolitym DU/2025/24).
- Terms of Use Common Crawl (dla `fineweb-edu`): nie otwierano.
- Prawa do tekstów stron w HPLT i fineweb-edu: z natury nieustalone (te zbiory nie udzielają licencji na teksty).
- Wersja `polish-dynaword` (v0.2.4 albo v0.2.5): w danych nie zapisana, tagi skasowane (1.2).

### 1.5 Wniosek

- **SA.** CC-BY-SA mają: cała partycja `core_sa` (`wikipedia`, `wikisource`, `wikibooks`, `wikivoyage`,
  `wolne_lektury`, `polqa`, część `biblioteka_nauki`) i `legal_sa` (`govpl`). Możliwe są też ukryte SA lub LWS w
  partycji „permissive”: `wolne_lektury_full` (jedna etykieta PD) i `poquad` (źródło kontekstów nieustalone). Czy SA
  dotyczy wag modelu, jest prawnie nierozstrzygnięte. Karta `polish-dynaword` ([README][d-readme], „Training models on
  this dataset”): „training a model does not by itself make the model adapted material of the training texts … this
  has not been tested in court”, a Creative Commons zaleca udostępnianie modelu na tej samej licencji, zastrzegając,
  że to „will almost certainly lead to overcompliance”. Najostrożniej: albo model na CC BY-SA 4.0 z atrybucją
  źródeł, albo trening bez partycji `*_sa` i bez składników z rozbieżną albo nieustaloną licencją. Wybór należy do
  zespołu, nie do tego przeglądu.
- **NC i AI.** Wprost zakazu trenowania AI nie ma żadne otwarte źródło. NC/ND może dotyczyć: tekstów `govpl` z
  okresu stopki CC BY-NC-ND 3.0 PL (stopka potwierdzona w kopiach Wayback z 2023-12-22 i 2025-01-06; dla
  materiałów urzędowych ta sama strona mówi, że korzystanie nie wymaga zgody), części rekordów `biblioteka_nauki` z wydrukowaną licencją NC/ND (w wersji sprzed
  przeglądu `polish-dynaword`). HPLT i fineweb-edu odsyłają do dyrektywy 2019/790 i warunków Common Crawl, a
  zastrzeżenia opt-out pojedynczych stron nie były sprawdzane.
- **Najwyższe ryzyko praw autorskich.** `polish_news` i `elka_pl_news` (artykuły prasowe, apache-2.0 tylko od autora
  scrapera, nie od wydawcy) oraz `wikisource` i `1000_novels` (wycofane przez `polish-dynaword` po audycie praw).
  Do tego rozbieżne etykiety: `eurlex` (CC-BY-4.0 zamiast polityki KE), `wolne_lektury`, `biblioteka_nauki`.
- **Dane osobowe.** `govpl` w tej wersji zawiera komunikaty prokuratur (dane o przestępstwach, RODO art. 10), które
  v0.2.6 usuwa. `parliamentary` może zawierać interpelacje z danymi osób prywatnych. `elka_pl_news` i `polish_news`
  opisują zdarzenia z nazwiskami. Żadna część nie przeszła NERGAL. Karta zbioru: „Pełny audyt danych osobowych
  pozostaje po stronie odbiorcy”.
- **Nieustalone.** Licencja u źródła: `polish_news`, `elka_pl_news`, `1000_novels`, `poquad`; teksty HPLT i
  fineweb-edu; dokładna wersja `polish-dynaword`; tokeny per źródło (do policzenia na parquetach).

To przegląd źródeł, nie opinia prawna.

[s-tree]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/tree/d50df04a6ad46876fa559a87cca5d3e2a96e7098
[s-dataset]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/blob/d50df04a6ad46876fa559a87cca5d3e2a96e7098/dataset.json
[s-shared]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/blob/d50df04a6ad46876fa559a87cca5d3e2a96e7098/shared/manifest.json
[s-readme]: https://huggingface.co/datasets/SlayerLab/slayer-pl-8x3b/blob/d50df04a6ad46876fa559a87cca5d3e2a96e7098/README.md
[rows-ex]: https://datasets-server.huggingface.co/rows?dataset=SlayerLab/slayer-pl-8x3b&config=default&split=train&offset=11297051&length=1
[d-readme]: https://huggingface.co/datasets/SlayerLab/polish-dynaword/blob/cc80dd9ae30203a54cf669f402f25754d964cf3c/README.md
[d-changelog]: https://huggingface.co/datasets/SlayerLab/polish-dynaword/blob/cc80dd9ae30203a54cf669f402f25754d964cf3c/CHANGELOG.md
[d-bn]: https://huggingface.co/datasets/SlayerLab/polish-dynaword/blob/cc80dd9ae30203a54cf669f402f25754d964cf3c/data/biblioteka_nauki/biblioteka_nauki.md
[d-govpl]: https://huggingface.co/datasets/SlayerLab/polish-dynaword/blob/cc80dd9ae30203a54cf669f402f25754d964cf3c/data/govpl/govpl.md
[hplt]: https://hplt-project.org/datasets/v3.0
[hplt-hf]: https://huggingface.co/datasets/HPLT/HPLT3.0/blob/3394d6ba8dae4da834e3b11771daf95028a960b1/README.md
[wl-prawa]: https://wolnelektury.pl/info/prawa/
[wl-zasady]: https://wolnelektury.pl/info/zasady-wykorzystania/
[eltec]: https://github.com/COST-ELTeC/ELTeC-pol
[pn-hf]: https://huggingface.co/datasets/WiktorS/polish-news/blob/2e3abfe7d3fbdfe02fab92a9980fca42cac3838c/README.md
[tvp-robots]: https://www.tvp.info/robots.txt
[elka-hf]: https://huggingface.co/datasets/winterkitsune/elka-pl-news/blob/cdb943d633f244d3d1c85b7a53888276496b0b20/README.md
[wn]: https://pl.wikinews.org/wiki/Wikinews:Prawa_autorskie
[poquad-hf]: https://huggingface.co/datasets/clarin-pl/poquad/blob/a60f228d836fbbf990d11b4590c60b3e7f2aec2d/README.md
[wm-tou]: https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use
[ws]: https://pl.wikisource.org/wiki/Wikiźródła:Prawa_autorskie
[polqa-hf]: https://huggingface.co/datasets/ipipan/polqa/blob/d78d036ef08ab3b9f4d85a2893f4d3a0c95a6f37/README.md
[fwe]: https://huggingface.co/datasets/HuggingFaceFW/fineweb-edu/blob/87f09149ef4734204d70ed1d046ddc9ca3f2b8f9/README.md
[fm]: https://huggingface.co/datasets/HuggingFaceTB/finemath/blob/e92b25a616738fe95dc186b64dfb19f9c8525594/README.md
[d833]: https://lawplayer.com/eu/act/32011D0833
[ec2019]: https://digital-strategy.ec.europa.eu/en/news/rules-reuse-commission-information
[ec-notice]: https://commission.europa.eu/legal-notice_en
[ppc]: https://clip.ipipan.waw.pl/PPC
[upapp]: https://api.sejm.gov.pl/eli/acts/DU/1994/83/text.html
[du]: https://dziennikustaw.gov.pl/
[govpl]: https://www.gov.pl/web/gov/prawa-autorskie
[govpl-wb2023]: https://web.archive.org/web/20231222201211/https://www.gov.pl/web/gov/prawa-autorskie
[govpl-wb2025]: https://web.archive.org/web/20250106034539/https://www.gov.pl/web/gov/prawa-autorskie

## 2. Kandydaci

| nazwa HF/URL | licencja | status | powód | data |
|---|---|---|---|---|
| `epfml/FineWeb2-HQ` (`pol_Latn`) | ODC-BY | kandydat | rozumowanie naukowe i wiedza (ARC-C, MMLU, LLMzSzŁ); ~13-20 mld tok.; wymaga dedupu wobec HPLT i 13-gramów wobec arkuszy CKE | 2026-10-30 |
| `HuggingFaceFW/fineweb-edu` (próg ≥4) | ODC-BY | użyty w Slayerze | już jest w 10% EN Slayera (`dataset.json`); nowy kandydat tylko jako wyższy udział albo ostrzejszy próg, nie jako nowe źródło | 2026-10-30 |
| `HuggingFaceTB/smollm-corpus` → `cosmopedia-v2` | ODC-BY | kandydat | syntetyczne podręczniki EN (Mixtral), ~28 mld tok. (niesprawdzone); karta v2 nie podaje dekontaminacji, ryzyko halucynacji i monotonnego stylu | 2026-10-30 |
| `common-pile/pubmed` | CC BY / CC BY-SA / CC0 (tylko te rekordy) | kandydat | wiedza medyczna (MedMCQA, PubMedQA); abstrakty testu PubMedQA wyciąć 13-gramami; przed użyciem skan PII medycznego (np. Philter, Presidio), bo karta nic o tym nie mówi; niski priorytet przy 1B | 2026-10-30 |
| `allenai/soda` | CC BY 4.0 | kandydat | dialogi i intencje (Social IQa, PoLEMo2); wysokie ryzyko kontaminacji: SODA i SIQA powstały z ATOMIC, ocena transferu na innym zbiorze | 2026-10-30 |
| Pakiet podręczników PL: `polish-dynaword` → `wikibooks` + `open_agh_chemistry` + ZPE | CC-BY/CC-BY-SA; ZPE niepotwierdzona (licencja per zasób) | kandydat | wiedza szkolna PL; wikibooks już użyty (tylko podniesienie wagi); ZPE dopiero po potwierdzeniu licencji i dedupie wobec LLMzSzŁ (zadania CKE); zakazu trenowania AI jak u OpenStax nie znaleziono: Wikibooks (warunki Wikimedia) i Open AGH (CC BY-SA 3.0/4.0, wersję wyjaśnić) bez klauzuli, regulamin ZPE bez wzmianki o AI/TDM, ale ogranicza użycie do celów edukacyjnych (§3 ust. 4); licencje pojedynczych zasobów ZPE, strony podręczników AGH i robots.txt/TDMRep niesprawdzone | 2026-10-30 |
| `SlayerLab/polish-dynaword` → `biblioteka_nauki` (podzbiór medyczny / akademicki) | per rekord | kandydat | wiedza akademicka i medyczna PL; sprawdzić, czy już jest w `core` Slayera | 2026-10-30 |
| Wiktionary PL (definicje + przykłady) | CC-BY-SA (niesprawdzone) | kandydat | znaczenie słowa (WiC); dopiero po kalibracji formatu, bo stałe predykcje WiC to format | 2026-10-30 |

## 3. Kandydaci z przeglądu 30.10

| nazwa HF/URL | licencja | status | powód | data |
|---|---|---|---|---|
| `HuggingFaceFW/finepdfs-edu` (`pol_Latn`) | ODC-BY | kandydat | edukacyjne PDF-y PL; rozmiar części PL do policzenia; dedup wobec arkuszy CKE i HPLT | 2026-10-30 |
| `Helsinki-NLP/fineweb-edu-translated` (pol) | ODC-BY | kandydat | MT tych samych dokumentów co EN fineweb-edu w Slayerze (wiedza ta sama, nowy tylko język) | 2026-10-30 |
| `Helsinki-NLP/nemotron-cc-translated` (pol) | niejasna: API CC0, upstream NVIDIA | wstrzymany | licencja do wyjaśnienia przed użyciem | 2026-10-30 |
| `PleIAs/SYNTH` | CC-BY-4.0 | kandydat | format QA + rozumowanie: ryzyko formatu, sprawdzić, czy zawiera MCQ | 2026-10-30 |
| `SKocur/polish-pre1918-corpus` | CC0 | kandydat | OCR; różnorodność polszczyzny | 2026-10-30 |
| `demelin/moral_stories` | MIT | kandydat | mały, pokrewny SIQA: ostrożnie (kontaminacja, format) | 2026-10-30 |
| `openbmb/Ultra-FineWeb` (EN) | Apache-2.0 | kandydat | filtrowany web EN; bez wariantu L3 | 2026-10-30 |

## 4. Odrzucone

Sprawdzone i wykluczone z treningu; „do testów: tak” znaczy, że można na nich oceniać model.

| zbiór | powód odrzucenia z treningu | do testów | data |
|---|---|---|---|
| OpenStax Polska (Fizyka t.1-3, Psychologia, Mikro/Makroekonomia) | strona zastrzega zakaz trenowania AI bez zgody OpenStax Poland | nie | 2026-10-30 |
| `joelniklaus/Multi_Legal_Pile` | licencja niekomercyjna (CC-BY-NC-SA-4.0, części NC); część PL (MARCELL, CC0) do osobnego sprawdzenia | nie | 2026-10-30 |
| `MegaScience/TextbookReasoning` | licencja niekomercyjna (CC-BY-NC-SA-4.0) | nie | 2026-10-30 |
| `speakleash/PES-2018-2022` | egzaminy specjalizacyjne lekarzy | tak | 2026-10-30 |
| `NASK-PIB/Reassess-Polish-Medical-Exams` | polskie egzaminy medyczne | tak | 2026-10-30 |
| `Gregniuki/polish-medical-cot-PES` | zbudowany z pytań PES | tak (ostrożnie: pochodna PES) | 2026-10-30 |
| Global-MMLU | tłumaczone pytania MMLU | tak | 2026-10-30 |
| exams | pytania egzaminacyjne | tak | 2026-10-30 |
| Lots-of-LoRAs task579-581, task384, task385 | zbudowane z pytań SIQA | tak (ostrożnie: pochodna SIQA) | 2026-10-30 |
| Zbiory benchmarków w formacie pytanie-litera (ARC, MMLU, SIQA, PubMedQA, arkusze CKE), także tłumaczone | uczą formatu testu, nie wiedzy | tak | 2026-10-30 |
| Dane NLI w formacie zadania (RTE/CB/ANLI-podobne) | stałe predykcje na tych testach to bariera formatu, nie brak danych | tak | 2026-10-30 |
