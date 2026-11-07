# PubMedQA (T44)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Odpowiedź `yes`/`no`/`maybe` na pytanie badawcze z abstraktu PubMed. lm-eval `0.4.9.1`, zadanie `pubmedqa`, 0-shot,
split `test` (PQA-L), metryka decyzyjna `acc`.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, werdykt: bez kontroli: nierozstrzygnięte.
- [`RECIPE.md`](RECIPE.md): przepis przebiegu centralnego.
- Wyniki: [`results/central-run/pubmedqa/`](../../results/central-run/pubmedqa/) (przebieg centralny, RTX 4090).
- Liczby raportu: [`results/pubmedqa.json`](results/pubmedqa.json), zebrane z przebiegu przez
  [`zbierz_wyniki.py`](zbierz_wyniki.py).
- Smoke test danych i promptu: [`notatki/SMOKE.md`](notatki/SMOKE.md).

## Wyniki

Pełny split, n = 500. b = 0,552 (stała odpowiedź „zawsze `yes`”), baza losowa 1/3. Różnica wobec b parowana po
pytaniach.

| model | `acc` | n | SE A | najczęstsza predykcja | wynik − b | SE par. | z | werdykt |
|---|---:|---:|---:|---|---:|---:|---:|---|
| Slayer 1.06 | 0,4760 | 500 | 0,0224 | `no` 0,552 | −7,60 pkt | 0,0316 | −2,41 | prawdopodobne (pod b) |
| Qwen3.5-0.8B-Base | 0,6760 | 500 | 0,0210 | `yes` 0,826 | +12,40 pkt | 0,0173 | 7,19 | pewne |
| LFM2.5-1.2B-Base | 0,6380 | 500 | 0,0215 | `yes` 0,658 | +8,60 pkt | 0,0245 | 3,52 | pewne |
| LFM3-1.7B-Base | 0,5940 | 500 | 0,0220 | `yes` 0,946 | +4,20 pkt | 0,0098 | 4,27 | pewne |
| EuroLLM-1.7B | 0,5300 | 500 | 0,0223 | `no` 0,692 | −2,20 pkt | 0,0351 | −0,63 | szum |

**Kontaminacja.** Wiersz Slayera 1.06 wyżej to wynik na teście ze znaną kontaminacją: Space oznacza dla niego T44
jako `contamination: flagged` (rdzeń, punkt 10; [`ORIGINAL.md`](ORIGINAL.md), pole „Kontaminacja”). Dla czterech
modeli odniesienia stan to `unscanned`. Zbiór jest publiczny od 2019 roku, a abstrakty PubMed są częste w korpusach
pretreningu, więc niska trafność nie jest tu dowodem braku kontaminacji, a wysoka nie byłaby dowodem wiedzy.

Żaden model nie wybiera `maybe`. Slayer 1.06 leży pod bazą większościową, ale nie przez stałą odpowiedź: przechyla
się w stronę `no`, gdy w danych przeważa `yes` (macierz pomyłek w `REPRODUCTION.md`). LFM3-1.7B-Base przechodzi b,
choć w 94,6% pytań mówi `yes`. Skąd te dwie rzeczy się biorą i co z nich wynika dla wyniku:
[`REPRODUCTION.md`, „Werdykt sprawdzenia”](REPRODUCTION.md#werdykt-sprawdzenia).
