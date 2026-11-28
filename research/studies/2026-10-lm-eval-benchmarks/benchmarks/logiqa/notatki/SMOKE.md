# Smoke test danych i promptu — LogiQA (T18)

Data: 2026-11-04. Zbiór: EleutherAI/logiqa, split test, rewizja c1eee1b2fd0ddc87777e36490f7ad54d0b97d141, gałąź refs/convert/parquet.

## Rozmiar i bazy
- n = 651
- baza losowa = 1/4 = 0,25
- najczęstsza poprawna pozycja: „d”, 181/651 = 0,2780 (zgodne z zadaniem) <!-- liczba-spoza-wynikow: 181 z rozkładu poprawnych policzonego w tym teście -->
- rozkład poprawnych: a 132, b 159, c 179, d 181 <!-- liczba-spoza-wynikow: rozkład poprawnych policzony w tym teście, nie trafia do results/logiqa.json -->

## Przykłady
Pokazano w całości: pierwszy (idx 0), ostatni (idx 650) i trzy losowe (idx 572, 598, 633) ze stałym ziarnem 20261028. Odpowiedź pasuje do pytania, brak pustych pól, dziwnych znaków, ucięć, duplikatów. Prompt zbudowany jak w lm-eval (utils_logiqa.doc_to_text): „Passage: …\nQuestion: …\nChoices:\nA. …\n…\nAnswer:”. Cel (target) to indeks poprawnej opcji 0–3. <!-- liczba-spoza-wynikow: indeksy wierszy użyte w smoke teście -->

## Dziwne rzeczy na całym splicie
Policzono: wszystkie 651 wierszy mają 4 opcje, label w {a,b,c,d}, brak pustych context/question/options. Nie stwierdzono duplikatów bajtowych wymagających ordinala.

## Wniosek
Dane i prompt mają sens. Można liczyć model.
