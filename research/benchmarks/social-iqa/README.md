# Social IQa (T46): Slayer 1.06, bez kontroli

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md). Typ testu: [`mc`](../../README.md#benchmarki-i-typy).

Social IQa sprawdza rozumienie sytuacji społecznych: model dostaje scenkę i pytanie o motywację, reakcję
emocjonalną albo następne działanie bohatera, a wybiera jedną z trzech odpowiedzi. Poziom losowy to 0,3333.
Space liczy ten test (T46) jako `multiple_choice`: log-prawdopodobieństwo każdej odpowiedzi, wybór najwyższego.

- Karta oryginału (etap A): [`ORIGINAL.md`](ORIGINAL.md)
- Odtworzenie (etap B): [`REPRODUCTION.md`](REPRODUCTION.md) — „bez kontroli: nierozstrzygnięte”
- Przepis (środowisko, komendy, smoke test): [`RECIPE.md`](RECIPE.md)
- Liczby zbiorcze: [`results/social_iqa.json`](results/social_iqa.json); wyniki per pytanie:
  [`results/slayer-1.06/social_iqa.jsonl.gz`](results/slayer-1.06/social_iqa.jsonl.gz) (panel) i
  [`results/slayer-1.06/social_iqa_full.jsonl.gz`](results/slayer-1.06/social_iqa_full.jsonl.gz) (pełny split)
- Skrypt, który składa plik liczb z wyjść `common/ewaluuj.py`: [`zbierz_wyniki.py`](zbierz_wyniki.py)

## Wyniki

| model | próbka | acc | n | SE | CI95 (bootstrap) |
|---|---|---:|---:|---:|---|
| Slayer 1.06 | panel Space 200 | 0,39 | 200 | 0,0346 | 0,32–0,46 |
| Slayer 1.06 | pełny split | 0,3895 | 1954 | 0,0110 | 0,3680–0,4115 |

Metryki pomocnicze (ten sam wybór odpowiedzi, inny sposób oceny):

| próbka | acc_norm | acc_pmi | BPB poprawnej |
|---|---:|---:|---:|
| panel Space 200 | 0,435 | 0,36 | 1,939 |
| pełny split | 0,424 | 0,375 | 1,945 |

## Bazy i werdykt

| próbka | baza losowa | stała odpowiedź (b) | acc − b | z | udział najczęstszej predykcji |
|---|---:|---:|---:|---:|---:|
| panel Space 200 | 0,3333 | 0,405 | −0,015 | −0,43 | 0,345 | <!-- liczba-spoza-wynikow: „acc − b” i „z” policzone z results/social_iqa.json -->
| pełny split | 0,3333 | 0,3362 | 0,0533 | 4,82 | 0,348 | <!-- liczba-spoza-wynikow: „acc − b” i „z” policzone z results/social_iqa.json -->

Na pełnym splicie wynik jest pewnie nad bazą losową i nad stałą odpowiedzią (z 5,09 wobec losowej i 4,82 wobec <!-- liczba-spoza-wynikow: z policzone z results/social_iqa.json -->
stałej), ale panel 200 tego nie potwierdza: etykieta „zawsze trzecia opcja” daje tam 0,405, czyli o 1,5 pkt więcej <!-- liczba-spoza-wynikow: różnica policzona z results/social_iqa.json -->
niż model, a różnica jest szumem (z −0,43). Panel 200 nie jest próbką wyrównaną klasowo — w pełnym splicie
poprawna odpowiedź na pozycji 3 to 657 z 1954 przypadków, a w panelu 81 z 200 — więc przy panelu trzeba czytać obie
bazy, a werdykt o umiejętności opierać na pełnym splicie (METODOLOGIA, „Space i panel 200”).
<!-- liczba-spoza-wynikow: z, różnica w pkt i rozkład gold policzone z results/social_iqa.json -->

## Kontrola

**Bez kontroli: nierozstrzygnięte.** Żaden model, który da się pobrać, nie ma opublikowanego wyniku zero-shot na Social IQa: Pythia-1b-v0
nie ma tego testu w pliku wyników, karta EuroLLM-1.7B podaje go w tabeli GAPERON bez czystej liczby, Open LLM
Leaderboard v2 nie zawiera tego testu, a `results.json` Space ma dla T46 dwa wiersze (`LiquidAI/LFM2.5-1.2B-Base` i `SlayerLab/Slayer1B-1.06`), oba `not_run` bez wartości. Praca podaje tylko wyniki
fine-tuned (BERT-large 64,5 na teście), więc nie spełniają warunku modelu kontrolnego etapu B. <!-- liczba-spoza-wynikow: Sap i in. 2019, tabela 2 (wynik fine-tuned) -->
Repo woła wprost zadanie lm-eval, które wskazuje Space, więc test zgodności implementacji niczego by nie sprawdził
(METODOLOGIA, „Bez kontroli”). Zgodnie z tą sekcją wynik nie idzie do Space ani do meta-oceny — zostaje w repo jako
pomiar wstępny. Szczegóły i miejsca szukania: [`REPRODUCTION.md`](REPRODUCTION.md).

Kontrola z tabeli typu (`wynik > b + 2 SE`) przechodzi na pełnym splicie i nie przechodzi na panelu 200 — to nie jest
brak kontroli, o którym wyżej, tylko warunek ważności pomiaru na próbce.
