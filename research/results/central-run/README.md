# Przebieg centralny: Slayer 1.06 i cztery modele odniesienia

Wyniki per model i zadanie leżą w katalogach `<benchmark>/<model>/` (`results.json`, `results_rozszerzone.json`,
próbki per pytanie w `probki/`). Wykres `scores.png` rysuje `tools/wykres_przebiegu.py`.

Slayer 1.06 to checkpoint z ok. 1/8 planowanego treningu, bez wygaszania LR (według autora modelu, stan z
01.11.2026). Pozostałe modele są po pełnym treningu, więc różnice mówią o tym checkpoincie, nie o gotowym Slayerze
ani o jego przepisie treningu.

## Jak czytać `scores.png`

- Słupek błędu to ±1 SE wyniku z `results_rozszerzone.json`. Na BLiMP (`para +klastry`) to od 07.11 SE K po 67
  paradygmatach (0,018–0,023), a nie SE po parach (0,0015–0,0016), które zostało w polu `se_a`: pary jednego
  paradygmatu dzielą szablon. Przeliczenie z próbek bez modelu robi `tools/podsumuj_ponownie.py`; dodało też
  bazę stałej odpowiedzi Social IQa (0,3362) i porównanie z b (`wobec_b`) w każdym teście MC. <!-- liczba-spoza-wynikow: results_rozszerzone.json BLiMP i Social IQa przed i po podsumuj_ponownie.py -->
- Wszystkie wyniki tego katalogu policzył 03.11 kod sprzed zmian z 04.11 (limit 4096 tokenów z BOS, budżet loglik
  jak HFLM), więc są do przeliczenia w przebiegu Slayera 1.07. <!-- liczba-spoza-wynikow: daty commitów 592c8af i 3ba8ae3 -->
- BLiMP: po parach różnice Slayera do Qwen3.5, LFM2.5 i EuroLLM wychodzą poza szum, ale po 67 paradygmatach
  (t, df = 66) każda różnica Slayera do czterech modeli to szum, a SE jest kilka razy większe niż słupek. Pięciu
  modeli na BLiMP nie da się uporządkować, więc wyróżnienie EuroLLM jako najlepszego modelu z pierwszej wersji
  wykresu nie ma oparcia. Kod wykresu nie wyróżnia już najlepszego modelu, gdy żadna różnica do Slayera nie wychodzi
  poza szum po paradygmatach.
- `scores.png` w repo jest jeszcze pierwszą wersją (z wyróżnieniem na BLiMP): nowej nie dało się wygenerować w
  środowisku tej poprawki, bo nie ma w nim matplotlib. Komenda:
  `python tools/wykres_przebiegu.py results/central-run results/central-run/scores.png`.
