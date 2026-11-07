# MathQA (T19)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Mierzy: zadania tekstowe z matematyki, 5 odpowiedzi.

- Test T19, typ `mc` ([README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy)).
- Zbiór: `allenai/math_qa` @ `c4f1cc784c04c4957b50c97858f23893b633eea6`, konfiguracja `default`, split `test`, n = 2985.
- Metryka decyzyjna: `acc_norm`.
- Licencja (karta zbioru na przypiętej rewizji): apache-2.0.
- Definicja zadania: lm-eval `6d2abda4` ([METODOLOGIA, „Wersja lm-eval”](../../METODOLOGIA.md#wersja-lm-eval)); przebieg liczy lm-eval 0.4.9.1 (`lock`) i 0.4.13 (`new`) z promptem przepisanym w `common/zadania.py`.
- Przebieg centralny: podpięty (`T19` w `common/zadania.py` i `KATALOGI` w `tools/przebieg_centralny.sh`); przepis w [`RECIPE.md`](RECIPE.md).

Repo z loading scriptem: dane z `refs/convert/parquet` @ `fafb9f7ee5b9ec4da9499f9c4177a4c91389f2d6`. Opcje z `mathqa/utils.py`.

Pliki:

- [`PROTOCOL-space.md`](PROTOCOL-space.md): protokół ustalony przed pomiarem — dane, wzory, bazy, kontrola.
- [`notatki/REGULA.md`](notatki/REGULA.md): decyzja o kontroli z listą przeszukanych miejsc.
- [`notatki/SMOKE.md`](notatki/SMOKE.md): smoke test danych i promptu przed pomiarem.
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, wynik wobec baz i rozbiór metryki.
- [`RECIPE.md`](RECIPE.md): przepisy przebiegów.
- Wyniki: [`results/slayer-1.06/`](results/slayer-1.06/); liczby raportu w
  [`results/mathqa.json`](results/mathqa.json), zbierane przez [`zbierz_wyniki.py`](zbierz_wyniki.py).

## Wynik

Slayer 1.06, pomiar autora protokołem Space z 7.11.2026 (RTX 5080). Metryka decyzyjna `acc_norm`, 0-shot.
Baza losowa 0,2000, baza większościowa b = 0,2265 (najczęstsza poprawna litera `c`, 676 z 2985). Różnica wobec b
parowana po pytaniach.

| przebieg | `acc_norm` | n | SE A | najczęstsza pred. | wobec b | SE par | z | werdykt |
|---|---:|---:|---:|---|---:|---:|---:|---|
| pełny split | 0,2188 | 2985 | 0,0076 | `a` 0,2436 | −0,77 pkt | 0,0109 | −0,71 | szum |
| panel 200 | 0,1800 | 200 | 0,0272 | `a` 0,2700 | −9,00 pkt | 0,0432 | −2,08 | prawdopodobne (pod b panelu) |

Wiersz panelu porównuje się z bazą większościową **tego panelu** (0,2700), bo rozkład poprawnych liter w panelu
jest inny niż w całym splicie. Werdykt liczymy na pełnym splicie.

Slayer 1.06 nie odróżnia się od bazy większościowej, więc wynik nie świadczy o umiejętności rozwiązywania zadań.
Nad bazą losową stoi o +1,88 pkt (SE parowane 0,0076, z = 2,48, prawdopodobne). Czemu `acc_norm` jest tu metryką
kłopotliwą i czemu panel wyszedł niżej niż pełny split:
[`REPRODUCTION.md`](REPRODUCTION.md).

**Kontrola:** brak. Żaden model z listy „Model kontrolny etapu B” nie ma opublikowanego wyniku na MathQA z rewizją
i ustawieniami, więc werdykt etapu B brzmi „bez kontroli: nierozstrzygnięte”, a wynik jest wstępny i nie wchodzi do
tabeli CodeSOTA ani do meta-oceny.

**Kontaminacja:** `unscanned` dla Slayera 1.06 (pole `contamination` w `results_rozszerzone.json`); Space oznacza
T19 dla Slayera 1.06 jako `flagged`, bez `hit_rate` ([`ORIGINAL.md`](ORIGINAL.md), pole „Kontaminacja”), a własnego
skanu nie robiliśmy.
