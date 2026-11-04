# Social IQa (Space T46)

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md).

Krótka scena społeczna i pytanie o motywację, reakcję albo skutek; 3 odpowiedzi. lm-eval `0.4.9.1`, zadanie
`social_iqa`, 0-shot, split `validation`, metryka decyzyjna `acc`.

- [`ORIGINAL.md`](ORIGINAL.md): karta oryginału (etap A).
- [`REPRODUCTION.md`](REPRODUCTION.md): etap B, werdykt: bez kontroli: nierozstrzygnięte. Space nie ma wartości T46
  dla Slayera (`not_run`).
- Wyniki: [`results/central-run/social-iqa/`](../../results/central-run/social-iqa/) (przebieg centralny, RTX 4090).

## Wyniki

Pełny split, n = 1954. b = 0,3362 (stała odpowiedź „zawsze `answerC`”), baza losowa 1/3. Różnica wobec b parowana
po pytaniach.

| model | `acc` | n | SE A | najczęstsza predykcja | wynik − b | SE par. | z | werdykt |
|---|---:|---:|---:|---|---:|---:|---:|---|
| Slayer 1.06 | 0,3895 | 1954 | 0,0110 | 0,3480 | +5,32 pkt | 0,0153 | 3,47 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/slayer1b-1.06 (results.json, results_rozszerzone.json, probki) -->
| Qwen3.5-0.8B-Base | 0,4186 | 1954 | 0,0112 | 0,3362 | +8,24 pkt | 0,0153 | 5,38 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/qwen3.5-0.8b-base -->
| LFM2.5-1.2B-Base | 0,4284 | 1954 | 0,0112 | 0,3414 | +9,21 pkt | 0,0154 | 5,97 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/lfm2.5-1.2b-base -->
| LFM3-1.7B-Base | 0,4545 | 1954 | 0,0113 | 0,3383 | +11,82 pkt | 0,0156 | 7,59 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/lfm3-1.7b-base -->
| EuroLLM-1.7B | 0,4150 | 1954 | 0,0111 | 0,3408 | +7,88 pkt | 0,0155 | 5,08 | pewne | <!-- liczba-spoza-wynikow: results/central-run/social-iqa/eurollm-1.7b -->

Wszystkie modele rozkładają odpowiedzi prawie równo między trzy opcje; żaden nie powtarza jednej.
