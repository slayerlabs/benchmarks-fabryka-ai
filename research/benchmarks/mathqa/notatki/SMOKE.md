# Smoke test danych i promptu — MathQA (T19)

Zrobiony 2026-11-07 o 17:17, czyli **przed pomiarem** (panel ruszył o 17:35:24), na tych samych bajtach, których
użył pomiar: parquet z `refs/convert/parquet` @ `fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6` zbioru
`allenai/math_qa` @ `c4f1cc784c04c4957b50c97858f23893b633eea6`, konfiguracja `default`, split `test`. Odczyt bez
modelu i bez karty, samym `datasets`.

## Rozmiar i bazy

- n = 2985, zgodnie z kartą w [`README.md`](../README.md).
- Kolumny: `Problem`, `Rationale`, `options`, `correct`, `annotated_formula`, `linear_formula`, `category`.
- Rozkład poprawnej odpowiedzi: `a` 614, `b` 605, `c` 676, `d` 628, `e` 462.
- Baza losowa: 1/5 = 0,2000 (pięć opcji).
- Baza większościowa: najczęstsza poprawna litera `c`, 676 z 2985, czyli 0,2265.

## Co policzone na całym splicie

- 0 pustych pól `Problem` i `options`.
- 0 wartości `correct` poza `a`–`e`.
- 0 duplikatów treści pytania, więc ordinal nie jest potrzebny.
- Najdłuższe `Problem` ma 628 znaków, czyli daleko pod oknem 4096 tokenów — żadne pytanie nie traci treści przez
  przycinanie.

## Pięć dokumentów

Pierwszy (idx 0), ostatni (idx 2984) i trzy losowe (idx 2288, 2532, 2823) ze stałym ziarnem 20261028. Id to indeks
wiersza w splicie, bo wpis `T19` nie ma `pole_id`. <!-- liczba-spoza-wynikow: indeksy wierszy użyte w smoke teście -->

| idx | pytanie (skrót) | opcje | correct |
|---|---|---|---|
| 0 | a shopkeeper sold an article offering a discount of 5 % … | 38 / 27.675 / 30 / data inadequate / none of these | `a` |
| 2288 | if an integer n is to be chosen at random from the integers 1 to 96 … | 1 / 4, 3 / 8, 1 / 2, 5 / 8, 3 / 4 | `d` |
| 2532 | find the l . c . m of 15 , 18 , 28 and 30 . | 1800 / 1260 / 1460 / 1600 / 960 | `b` |
| 2823 | find the simple interest on $ 10000 at 6 % per annum for 12 months ? | $ 410 / $ 500 / $ 600 / $ 710 / $ 1000 | `c` |
| 2984 | 4 shepherds were watching over the flocks … | 2 / 3 / 4 / 5 / 6 | `b` |

Co się zgadzało w każdym z pięciu:

- Prompt powstaje jak w YAML-u lm-evala: `Question: {{Problem}}` + nowa linia + `Answer:`, separator odpowiedzi
  domyślny.
- Opcje to pięć **tekstów odpowiedzi**, nie liter, wycinanych z pola `options` przez `utils.doc_to_choice`.
  Różnią się długością w każdym z pięciu pytań — stąd uwaga o `acc_norm` w [`REPRODUCTION.md`](../REPRODUCTION.md).
- `correct` jest literą, a cel liczy się jako jej pozycja w `['a','b','c','d','e']`.
- Treść pytania zgadza się z opcjami, brak ucięć i znaków zastępczych.

## Wniosek

Dane i prompt mają sens, można liczyć model.
