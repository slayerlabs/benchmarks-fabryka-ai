# MedMCQA (T45)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Pytania z egzaminów medycznych, 4 opcje, odpowiedź literą. lm-eval `0.4.9.1`, zadanie `medmcqa`, 0-shot, split
`validation`, metryka decyzyjna `acc`.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, werdykt: bez kontroli: nierozstrzygnięte. Slayer 1.06 wybiera
  `A` w prawie każdym pytaniu, więc jego wynik jest do sprawdzenia.
- [`RECIPE.md`](RECIPE.md): przepis przebiegu centralnego.
- Wyniki: [`results/central-run/medmcqa/`](../../results/central-run/medmcqa/) (przebieg centralny, RTX 4090).

## Wyniki

Pełny split, n = 4183. b = 0,3223 (stała odpowiedź „zawsze `A`”), baza losowa 0,25. Różnica wobec b parowana po
pytaniach. <!-- liczba-spoza-wynikow: rozkład celu z probki/ przebiegu centralnego -->

| model | `acc` | n | SE A | najczęstsza predykcja | wynik − b | SE par. | z | werdykt |
|---|---:|---:|---:|---|---:|---:|---:|---|
| Slayer 1.06 | 0,3160 | 4183 | 0,0072 | `A` 0,9331 | −0,62 pkt | 0,0030 | −2,04 | prawdopodobne (pod b) | <!-- liczba-spoza-wynikow: results/central-run/medmcqa/slayer1b-1.06 (results.json, results_rozszerzone.json, probki) -->
| Qwen3.5-0.8B-Base | 0,4026 | 4183 | 0,0076 | `D` 0,3251 | +8,03 pkt | 0,0108 | 7,45 | pewne | <!-- liczba-spoza-wynikow: results/central-run/medmcqa/qwen3.5-0.8b-base -->
| LFM2.5-1.2B-Base | 0,4059 | 4183 | 0,0076 | `C` 0,2998 | +8,37 pkt | 0,0106 | 7,87 | pewne | <!-- liczba-spoza-wynikow: results/central-run/medmcqa/lfm2.5-1.2b-base -->
| LFM3-1.7B-Base | 0,3782 | 4183 | 0,0075 | `D` 0,2670 | +5,59 pkt | 0,0110 | 5,10 | pewne | <!-- liczba-spoza-wynikow: results/central-run/medmcqa/lfm3-1.7b-base -->
| EuroLLM-1.7B | 0,2582 | 4183 | 0,0068 | `B` 0,6290 | −6,41 pkt | 0,0109 | −5,86 | pewne (pod b) | <!-- liczba-spoza-wynikow: results/central-run/medmcqa/eurollm-1.7b -->

Slayer 1.06 odpowiada `A` w 93,3% pytań, więc jego wynik to w praktyce stała odpowiedź. <!-- liczba-spoza-wynikow: probki przebiegu centralnego -->
EuroLLM-1.7B leży przy bazie losowej (z = 1,21 wobec 0,25, szum) i pod b, bo w 62,9% pytań wybiera `B`. <!-- liczba-spoza-wynikow: probki przebiegu centralnego -->
Space (panel 200, informacyjnie: nie kontrola ani wzorzec) ma dla Slayera 0,245 wobec 0,3160 w repo (`REPRODUCTION.md`, „Slayer w Space”). <!-- liczba-spoza-wynikow: 0,245 z results.json Space @ 2d3d73f -->
