# MathQA (T19): etap B

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md), etap B.

Decyzja o kontroli zapadła przed pomiarem i stoi w [`notatki/REGULA.md`](notatki/REGULA.md), a progi, bazy i wzory
w [`PROTOCOL-space.md`](PROTOCOL-space.md). Ten plik dopisuje wynik.

| pole | wartość |
|---|---|
| kontrola | **bez kontroli** — żaden model z listy „Model kontrolny etapu B” nie ma opublikowanego wyniku na MathQA z rewizją i ustawieniami ([`notatki/REGULA.md`](notatki/REGULA.md)) |
| werdykt etapu B | bez kontroli: nierozstrzygnięte; wynik wstępny, poza tabelą CodeSOTA i poza meta-oceną |
| test zgodności | nie dotyczy: repo woła prompt i wybory zadania lm-eval `mathqa` wprost (METODOLOGIA, sekcja C) |
| wynik (SE): Slayer 1.06 | pełny split `acc_norm` 0,2188 (n = 2985), SE A 0,0076, CI95 [0,2037; 0,2338] |
| panel Space (200) | `acc_norm` 0,1800, SE A 0,0272, CI95 [0,1300; 0,2350] |

## Wynik wobec baz

Pełny split, porównania parowane po pytaniach:

| porównanie | różnica | SE parowane | z | werdykt |
|---|---:|---:|---:|---|
| `acc_norm` wobec bazy losowej 0,2000 | +1,88 pkt | 0,0076 | 2,48 | prawdopodobne |
| `acc_norm` wobec bazy większościowej 0,2265 | −0,77 pkt | 0,0109 | −0,71 | szum |

Czyli Slayer 1.06 stoi nieco nad poziomem losowym, ale **nie odróżnia się od bazy większościowej**: od stałej
odpowiedzi „zawsze litera `c`” dzieli go szum. Kolumna „Kontrola” typu `mc` wymaga wyniku ponad b o 2 SE, czego ten
wynik nie spełnia, więc nie świadczy o umiejętności rozwiązywania zadań matematycznych. Metryki pomocnicze dają ten
sam obraz: `acc` 0,2198, `acc_pmi` 0,2402, BPB poprawnej odpowiedzi 3,598.

Rozkład predykcji na pełnym splicie: `a` 727, `b` 547, `c` 522, `d` 485, `e` 704, czyli udział najczęstszej
predykcji 0,2436. Model nie wybiera stale jednej pozycji, więc wynik nie jest artefaktem stałej odpowiedzi.

## Panel wobec pełnego splitu

Panel 200 dał `acc_norm` 0,1800, pełny split 0,2188. Panel jest **dokładnym podzbiorem** pełnego przebiegu:
200 wspólnych pytań, największa różnica log P równa 0,0 i zero pytań z inną wartością `acc_norm`, a średnia
`acc_norm` tych 200 pytań w przebiegu pełnym też wynosi 0,1800. Różnica między panelem a pełnym splitem bierze się
więc wyłącznie z doboru pytań, nie z przebiegu: przy SE panelu 0,0272 mieści się w szumie.

Panel ma też własny rozkład celu, inny niż cały split: najczęstsza poprawna litera to `c` w 54 z 200 pytań, czyli
baza większościowa panelu wynosi 0,2700. Wobec niej panel leży −9,00 pkt (SE parowane 0,0432, z = −2,08,
prawdopodobne). Werdykt liczymy na pełnym splicie, zgodnie z METODOLOGIĄ.

Zastrzeżenie o tożsamości dokumentu z [`PROTOCOL-space.md`](PROTOCOL-space.md) zostaje w mocy: wpis T19 nie ma
`pole_id`, więc panel powstał po indeksie wiersza i nie musi być tym samym panelem, który liczy Space. Wyniku
pełnego splitu to nie dotyczy.

## Dlaczego `acc_norm` nie mierzy tu tego, co się wydaje

`acc_norm` dzieli sumę log P kontynuacji przez liczbę jej znaków. Log P są ujemne, więc dzielenie przez mniejszą
liczbę znaków daje wartość **bardziej** ujemną: metryka systematycznie przekłada opcje dłuższe nad krótsze. W MathQA
opcje to teksty odpowiedzi o bardzo różnej długości — obok siebie stoją `38`, `1 / 4` i `none of these` — więc ten
efekt ma tu realną siłę.

Widać go w liczbach. Na pełnym splicie średnia długość opcji wynosi 4,32 znaku, a średnia długość opcji wybranej
przez `acc_norm` 4,93. Wśród 430 pytań, w których jedna opcja jest krótsza od wszystkich pozostałych, `acc_norm`
wybiera tę najkrótszą 32 razy, czyli w 0,0744 pytań, przy 0,2000 oczekiwanych z losowania. Dane same takiej
skrzywienia nie mają: poprawna odpowiedź jest tą jedyną najkrótszą w 93 z tych 430 pytań, czyli w 0,2163, a więc
mniej więcej tyle, ile wychodzi z losowania.

To nie jest usterka przebiegu ani ładowania modelu: `acc_norm` odtwarza się co do pytania z zapisanych log P
podzielonych przez liczbę znaków kontynuacji bez wiodącej spacji, we wszystkich 2985 pytaniach. Metryka decyzyjna
`acc_norm` pochodzi z `tasks_50.json` i tego nie zmieniamy — ale przy czytaniu wyniku T19 warto pamiętać, że część
jego wariancji pochodzi z długości tekstu odpowiedzi, a nie z matematyki.

## Co to znaczy dla wniosków

Wynik mówi tyle, że model nie przechodzi bazy większościowej. Nie mówi nic o umiejętnościach matematycznych i nie
nadaje się do porównań między wersjami Slayera, dopóki różnica nie przekroczy progu z karty. Pełny rozbiór, w tym
decyzja treningowa i SNR, należy do karty oryginału, która powstaje w osobnym zadaniu (#28, „Co zrobić”, punkt 7).
