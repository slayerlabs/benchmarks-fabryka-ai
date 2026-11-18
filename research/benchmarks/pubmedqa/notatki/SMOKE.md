# Smoke test danych i promptu — PubMedQA (T44)

Data: 2026-11-07. Zbiór: `bigbio/pubmed_qa`, konfiguracja `pubmed_qa_labeled_fold0_source`, split `test`, rewizja
`15578e80ef02c2c9636d33fdd7eb6b05b987ba60`, dane z gałęzi `refs/convert/parquet` @
`13a7d15476092370cbabb6475390e7e69b74d2f2`.

**Kiedy, czym i czego to nie zastępuje.** Odczyt zrobiony po przebiegu centralnym (3.11.2026), z jego próbek
leżących w repo (`results/central-run/pubmedqa/slayer1b-1.06/probki/T44_space.jsonl.gz`), bez sieci, bez wag i bez
GPU — autor PR nie liczy na karcie ([METODOLOGIA, „Definicja „zrobione””](../../../METODOLOGIA.md#definicja-zrobione)).
Smoke testem przed samym przebiegiem był `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę
model × zadanie), czyli mniej niż 5–10 przykładów z rdzenia, punkt 8, i bez zapisu id. Ta notatka ten zapis
uzupełnia: te same rzeczy sprawdzone ręcznie na 5 dokumentach i na całym splicie, ale już na wynikach, nie przed
nimi. Jeśli recenzja uzna to za niewystarczające, brakuje przebiegu z `proba_cpu` na 5–10 pytaniach T44 przed
następnym pomiarem.

## Rozmiar i bazy

- n = 500 (pełny split `test`, czyli test PQA-L z pracy)
- baza losowa = 1/3 (trzy klasy: `yes`, `no`, `maybe`)
- rozkład celu (`final_decision`): `yes` 276, `no` 169, `maybe` 55
- stała odpowiedź „zawsze `yes`” = 276 z 500 = 0,552, czyli b; zgodne z bazą większościową podaną w pracy

## Przykłady

Pokazane w całości: pierwszy (idx 0), ostatni (idx 499) i trzy losowe (idx 286, 317, 498) ze stałym ziarnem
20261028. Id to indeks dokumentu w splicie (`doc_id` w próbkach). <!-- liczba-spoza-wynikow: indeksy wierszy użyte w smoke teście -->

| idx | pytanie (skrót) | akapitów `CONTEXTS` | cel | log P ` yes` / ` no` / ` maybe` | trafienie |
|---|---|---:|---|---|---|
| 0 | Is anorectal endosonography valuable in dyschesia? | 3 | `yes` | −8,96 / −9,53 / −16,15 | tak | <!-- liczba-spoza-wynikow: probki Slayera, doc_id 0 -->
| 286 | Sub-classification of low-grade cerebellar astrocytoma: is it clinically meaningful? | 3 | `no` | −11,54 / −10,44 / −16,31 | tak | <!-- liczba-spoza-wynikow: probki Slayera, doc_id 286 -->
| 317 | Should temperature be monitorized during kidney allograft preservation? | 3 | `no` | −8,96 / −9,67 / −13,58 | nie | <!-- liczba-spoza-wynikow: probki Slayera, doc_id 317 -->
| 498 | Are there mental health differences between francophone and non-francophone populations…? | 3 | `maybe` | −8,15 / −8,37 / −15,13 | nie | <!-- liczba-spoza-wynikow: probki Slayera, doc_id 498 -->
| 499 | Outcome Feedback within Emergency Medicine Training Programs… | 3 | `maybe` | −11,77 / −10,88 / −16,73 | nie | <!-- liczba-spoza-wynikow: probki Slayera, doc_id 499 -->

Co się zgadzało w każdym z pięciu:

- Prompt zbudowany jak w lm-eval (`preprocess_pubmedqa.doc_to_text`): `Abstract: ` + akapity `CONTEXTS` złączone
  znakiem nowej linii + `\nQuestion: ` + `QUESTION` + `\nAnswer:`. Odpowiedź pasuje do pytania.
- Trzy kontynuacje w kolejności ` yes`, ` no`, ` maybe`, każda ze spacją na początku (`target_delimiter`).
- Cel podany tekstem (`final_decision`), nie indeksem; mapowanie tekst → indeks opcji zgodne z wyborem metryki.
- `LONG_ANSWER` (wnioski autorów) nie pojawia się w prompcie w żadnym z pięciu.
- Brak pustych pól, ucięć i dziwnych znaków.

## Co policzone na całym splicie

- 500 z 500 promptów jest znak w znak szablonem lm-eval; 0 wycieków `LONG_ANSWER`.
- 0 pustych `QUESTION` i `CONTEXTS`; 0 celów poza klasami `yes`/`no`/`maybe`.
- 0 duplikatów promptu, więc ordinal nie jest potrzebny.
- Najdłuższy prompt ma 2718 znaków, czyli daleko pod oknem modelu (4096 tokenów), więc żadne pytanie nie traci
  treści przez przycinanie. <!-- liczba-spoza-wynikow: długość promptu policzona w tym teście -->

## Wniosek

Dane i prompt mają sens, mapowanie odpowiedzi też. Oba zachowania, które postawiły T44 na „do sprawdzenia” — brak
predykcji `maybe` i wynik Slayera pod b — widać już na tych pięciu przykładach: ` maybe` ma najniższe log P w każdym
z nich, a na idx 317 i 498 model wybiera klasę z wyższym priorem, nie z kontekstu. Rozbiór w
[`REPRODUCTION.md`, „Werdykt sprawdzenia”](../REPRODUCTION.md#werdykt-sprawdzenia).
