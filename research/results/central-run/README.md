# Przebieg centralny: Slayer 1.06 i cztery modele odniesienia

Wyniki per model i zadanie leżą w katalogach `<benchmark>/<model>/` (`results.json`, `results_rozszerzone.json`,
próbki per pytanie w `probki/`). Wykres `scores.png` rysuje `tools/wykres_przebiegu.py`.

Slayer 1.06 to checkpoint z ok. 1/8 planowanego treningu, bez wygaszania LR (według autora modelu, stan z
01.11.2026). Pozostałe modele są po pełnym treningu, więc różnice mówią o tym checkpoincie, nie o gotowym Slayerze
ani o jego przepisie treningu.

## Jak czytać `scores.png`

- Słupek błędu to ±1 SE po pytaniach. Na BLiMP pytaniem jest para minimalna, a pary jednego paradygmatu dzielą
  szablon, więc ten SE opisuje tylko te pary.
- BLiMP: po parach różnice Slayera do Qwen3.5, LFM2.5 i EuroLLM wychodzą poza szum, ale po 67 paradygmatach
  (t, df = 66) każda różnica Slayera do czterech modeli to szum, a SE jest kilka razy większe niż słupek. Pięciu
  modeli na BLiMP nie da się uporządkować, więc wyróżnienie EuroLLM jako najlepszego modelu z pierwszej wersji
  wykresu nie ma oparcia. Kod wykresu nie wyróżnia już najlepszego modelu, gdy żadna różnica do Slayera nie wychodzi
  poza szum po paradygmatach.
- `scores.png` w repo jest jeszcze pierwszą wersją (z wyróżnieniem na BLiMP): nowej nie dało się wygenerować w
  środowisku tej poprawki, bo nie ma w nim matplotlib. Komenda:
  `python tools/wykres_przebiegu.py results/central-run results/central-run/scores.png`.
