# Protokół Space: MathQA (T19) dla Slayera 1.06

Ustalony **przed pomiarem**: plik wchodzi do repo commitem na gałęzi `research/mathqa`, zanim model policzy
cokolwiek na T19. Dowodem czasu jest `git log` — commit tego pliku jest starszy niż commit z wynikami (rdzeń,
punkt 1). Korekty po wyniku trafiają do osobnej sekcji na końcu pliku, bez zmieniania zapisów wyżej.

## Dane

- Zbiór: `allenai/math_qa` @ `c4f1cc784c04c4957b50c97858f23893b633eea6`, konfiguracja `default`, split `test`,
  n = 2985 (wpis `T19` w `common/zadania.py`, zgodny z kartą w [`README.md`](README.md)).
- Bajty: parquet z `refs/convert/parquet` @ `fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6`. YAML zadania lm-eval ma
  `dataset_path: math_qa` **bez przypiętej rewizji**, więc sam czytałby skrypt ładujący z `main`; repo tego nie robi
  i bierze przypięty parquet (`_zrodlo` w `common/zadania.py`). Dlatego wynik nie zależy od tego, co w repozytorium
  zbioru zmieni się później.
- Kolumny: `Problem`, `Rationale`, `options`, `correct`, `annotated_formula`, `linear_formula`, `category`.
- Czystość splitu, policzona przed pomiarem: 0 pustych `Problem` i `options`, 0 celów poza `a`–`e`, 0 duplikatów
  treści pytania, najdłuższe `Problem` 628 znaków (mieści się w oknie 4096 tokenów z zapasem).
- Licencja karty zbioru na przypiętej rewizji: apache-2.0.

## Zadanie

- Katalog `lm_eval/tasks/mathqa` jest **identyczny** w `6d2abda4` (0.4.8) i `v0.4.9.1`, blob w blob:
  `README.md` `6e7e3dbda409256afdd7493ee7862a0268eb9933`, `mathqa.yaml` `23fc01d2e9d27c95fb7f742084aa4b6a938ae7ca`,
  `utils.py` `d44fb440bef9c3adcfe353d6028fe1531c7a77ed`. Nie ma więc rozbieżności między wersją z METODOLOGII
  a wersją z locka.
- Prompt: `Question: {{Problem}}\nAnswer:`, separator odpowiedzi domyślny (spacja).
- Opcje: `utils.doc_to_choice` wycina z pola `options` pięć **tekstów odpowiedzi**, nie liter — na przykład
  `38`, `27.675`, `30`, `data inadequate`, `none of these`.
- Cel: `['a', 'b', 'c', 'd', 'e'].index(correct)`.
- Metryka decyzyjna: `acc_norm`, 0-shot. Opcje różnią się długością (liczba obok zdania w rodzaju „none of these”),
  więc normalizacja po znakach jest tu istotna; `acc` i `acc_pmi` idą obok jako pomocnicze.

## Model

`SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, ładowany przez `common/slayer_lm.py`
(wagi lokalnie w `models/slayer-1.06`, zweryfikowane plikiem `SHA256SUMS`).

## Tożsamość dokumentu

Wpis `T19` nie ma `pole_id`, więc `common/ewaluuj.py` bierze jako `source_id` indeks wiersza (0..2984). Panel Space
powstaje z SHA-256 klucza `20261028|mathqa|mathqa|id dokumentu` (METHOD.md §3, „Ustawienia przebiegu centralnego”
w METODOLOGII), więc jeśli Space liczy id dokumentu inaczej niż po indeksie wiersza, **nasz panel 200 nie musi być
panelem Space**. Wyniku pełnego splitu to nie dotyczy. Ten sam zapis stoi w protokole LogiQA (T18).

## Próbka

`min(200, 2985)` = 200 dokumentów do panelu oraz pełny split 2985. Model liczy osobny przebieg panelu i osobny
pełnego splitu; panel ma być podzbiorem pełnego i po pomiarze sprawdzamy to przez różnicę loglik i `acc_norm`
na wspólnych pytaniach.

## Wzory

- Wartość = średnia `acc_norm`; SE = s/√n; CI95 bootstrap percentylowy, 10 000 powtórzeń, seed 20261028 (METHOD.md).
- Baza losowa: 1/5 = 0,2000 (pięć opcji).
- Baza większościowa (b): udział najczęstszej poprawnej litery, `c` 676/2985 = **0,2265**. Rozkład celu na splicie:
  `a` 614, `b` 605, `c` 676, `d` 628, `e` 462.
- Porównanie z bazami parowane po pytaniach, werdykt z progów rdzenia, punkt 4.
- Float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`.

## Kontrola

**Bez kontroli, wynik wstępny.** Rozbiór w [`notatki/REGULA.md`](notatki/REGULA.md); decyzja zapadła przed pomiarem
i nie zależy od wyniku Slayera. Werdykt etapu B brzmi „bez kontroli: nierozstrzygnięte”, więc wynik nie idzie do
tabeli CodeSOTA ani do meta-oceny, a do Space trafia jako wstępny.

## Wynik (Slayer 1.06)

Do uzupełnienia po pomiarze, osobnym commitem: `acc_norm` z n, SE i CI95 dla panelu i pełnego splitu, `acc` i
`acc_pmi` obok, porównanie z bazą losową i większościową z SE parowanym i werdyktem, udział najczęstszej predykcji.

## Czasy

Do uzupełnienia po pomiarze: czas panelu i pełnego splitu, liczba żądań, sprzęt i środowisko.

## Korekty
