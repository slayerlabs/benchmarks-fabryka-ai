# EWoK-PL: wyniki

Wynik EWoK w % (losowo 50), CI95 bootstrap. `oba` = obie pary trafione (losowo 25).

| model | PL ewok (n=625) | PL oba | EN te same 625 | EN pełny (4374) | PL kontekst stały | PL stały target |
|---|---|---|---|---|---|---|
| Bielik-1.5B-v3 | 66.0 [63.4, 68.5] | 42.4 [38.4, 46.2] | 62.8 [60.6, 65.1] | 69.5 [68.6, 70.3] | 58.2 [56.3, 60.0] | 75.4 [71.8, 78.7] |
| LFM3-1.7B-Base | 57.4 [55.0, 59.8] | 27.0 [23.7, 30.6] | 66.6 [64.2, 69.1] | 69.7 [68.8, 70.6] | 57.6 [55.7, 59.5] | 73.6 [70.1, 77.1] |
| Slayer1B-1.00 | 54.4 [52.0, 56.8] | 23.5 [20.3, 27.0] | 51.3 [49.3, 53.4] | 53.1 [52.3, 54.0] | 52.6 [50.9, 54.2] | 81.1 [77.9, 84.2] |
| Slayer1B-1.01 | 53.0 [50.6, 55.3] | 21.3 [18.1, 24.5] | 53.5 [51.4, 55.8] | 55.5 [54.7, 56.4] | 52.3 [50.6, 54.0] | 80.3 [77.1, 83.4] |
| Slayer1B-1.02 | 54.4 [52.1, 56.7] | 22.6 [19.4, 25.9] | 52.8 [50.6, 55.0] | 57.1 [56.2, 57.9] | 52.6 [51.0, 54.1] | 83.7 [80.8, 86.6] |
| Slayer1B-1.03 | 54.6 [52.3, 56.9] | 21.1 [17.9, 24.5] | 52.0 [49.8, 54.1] | 55.8 [54.9, 56.7] | 53.2 [51.5, 54.9] | 81.1 [78.1, 84.2] |
| Slayer1B-1.04 | 56.4 [54.3, 58.5] | 21.1 [18.1, 24.3] | 56.0 [53.7, 58.2] | 57.4 [56.6, 58.3] | 52.7 [51.2, 54.2] | 85.0 [82.1, 87.7] |
| Slayer1B-1.05 | 55.6 [53.3, 57.8] | 22.6 [19.2, 25.9] | 57.0 [54.8, 59.1] | 58.8 [57.9, 59.7] | 54.0 [52.4, 55.6] | 83.4 [80.5, 86.2] |
| Slayer1B-1.06 | 55.4 [53.0, 57.8] | 25.1 [21.8, 28.5] | 56.2 [54.0, 58.5] | 58.9 [58.0, 59.8] | 53.4 [51.8, 55.0] | 83.7 [80.8, 86.6] |

## PL wg pary pojęć

| para | n | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|
| believe / doubt | 55 | 48 | 42 | 50 | 50 | 48 | 51 | 53 | 48 | 47 |
| believe / imagine | 10 | 70 | 50 | 50 | 40 | 55 | 60 | 70 | 70 | 75 |
| choose / - | 165 | 68 | 62 | 48 | 52 | 52 | 53 | 54 | 53 | 51 |
| feel / not feel | 20 | 68 | 57 | 60 | 55 | 68 | 65 | 68 | 60 | 57 |
| have no preference / prefer | 10 | 50 | 65 | 50 | 35 | 50 | 55 | 45 | 40 | 40 |
| hear / not hear | 30 | 83 | 75 | 48 | 53 | 58 | 52 | 70 | 78 | 85 |
| intend / not intend | 70 | 79 | 61 | 64 | 61 | 56 | 63 | 64 | 64 | 65 |
| make an effort / make no effort | 45 | 90 | 54 | 87 | 72 | 70 | 72 | 76 | 80 | 77 |
| make more effort / make less effort | 220 | 57 | 55 | 51 | 49 | 52 | 50 | 50 | 48 | 49 |

## EN pełny wg domeny (tło: gdzie model nie ma wiedzy)

| domena | n | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|
| agent-properties | 1120 | 65 | 68 | 51 | 52 | 52 | 51 | 55 | 56 | 55 |
| material-dynamics | 780 | 86 | 84 | 53 | 58 | 66 | 61 | 60 | 64 | 67 |
| material-properties | 124 | 55 | 58 | 54 | 51 | 58 | 51 | 56 | 59 | 57 |
| physical-dynamics | 75 | 69 | 75 | 59 | 63 | 58 | 63 | 66 | 62 | 61 |
| physical-interactions | 280 | 62 | 61 | 52 | 53 | 54 | 52 | 51 | 55 | 54 |
| physical-relations | 415 | 58 | 58 | 50 | 49 | 51 | 49 | 51 | 51 | 51 |
| quantitative-properties | 190 | 71 | 66 | 63 | 67 | 69 | 66 | 66 | 69 | 67 |
| social-interactions | 175 | 80 | 84 | 69 | 69 | 74 | 72 | 72 | 71 | 72 |
| social-properties | 185 | 83 | 77 | 58 | 68 | 61 | 68 | 65 | 64 | 68 |
| social-relations | 785 | 68 | 67 | 51 | 52 | 51 | 53 | 56 | 57 | 57 |
| spatial-relations | 245 | 61 | 61 | 54 | 59 | 58 | 56 | 57 | 57 | 55 |

## Kontrasty (różnica punktów ewok ×100, sparowany test permutacyjny, Holm w rodzinie)

| rodzina | A | B | n | A−B | CI95 | p | p_holm |
|---|---|---|---|---|---|---|---|
| PL vs EN | Bielik-1.5B-v3 PL | Bielik-1.5B-v3 EN | 625 | +3.2 | [+0.6, +5.8] | 0.0171 | 0.1197 |
| PL vs EN | LFM3-1.7B-Base PL | LFM3-1.7B-Base EN | 625 | -9.3 | [-11.8, -6.6] | 0.0001 | 0.0009 |
| PL vs EN | Slayer1B-1.00 PL | Slayer1B-1.00 EN | 625 | +3.1 | [+1.0, +5.3] | 0.0055 | 0.0440 |
| PL vs EN | Slayer1B-1.01 PL | Slayer1B-1.01 EN | 625 | -0.6 | [-3.1, +1.9] | 0.7124 | 1.0000 |
| PL vs EN | Slayer1B-1.02 PL | Slayer1B-1.02 EN | 625 | +1.6 | [-1.1, +4.2] | 0.2715 | 1.0000 |
| PL vs EN | Slayer1B-1.03 PL | Slayer1B-1.03 EN | 625 | +2.6 | [-0.2, +5.3] | 0.0698 | 0.4188 |
| PL vs EN | Slayer1B-1.04 PL | Slayer1B-1.04 EN | 625 | +0.4 | [-2.3, +3.2] | 0.8264 | 1.0000 |
| PL vs EN | Slayer1B-1.05 PL | Slayer1B-1.05 EN | 625 | -1.4 | [-4.0, +1.3] | 0.3427 | 1.0000 |
| PL vs EN | Slayer1B-1.06 PL | Slayer1B-1.06 EN | 625 | -0.9 | [-3.8, +1.9] | 0.5780 | 1.0000 |
| Slayer kolejne | Slayer1B-1.01 | Slayer1B-1.00 | 625 | -1.4 | [-3.4, +0.6] | 0.1899 | 0.9494 |
| Slayer kolejne | Slayer1B-1.02 | Slayer1B-1.01 | 625 | +1.4 | [-0.8, +3.7] | 0.2368 | 0.9494 |
| Slayer kolejne | Slayer1B-1.03 | Slayer1B-1.02 | 625 | +0.2 | [-2.1, +2.4] | 0.9433 | 1.0000 |
| Slayer kolejne | Slayer1B-1.04 | Slayer1B-1.03 | 625 | +1.8 | [-0.6, +4.2] | 0.1443 | 0.8657 |
| Slayer kolejne | Slayer1B-1.05 | Slayer1B-1.04 | 625 | -0.8 | [-2.9, +1.2] | 0.4925 | 1.0000 |
| Slayer kolejne | Slayer1B-1.06 | Slayer1B-1.05 | 625 | -0.2 | [-2.3, +1.8] | 0.8758 | 1.0000 |
| Slayer 1.06 vs 1.00 (pl) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | +1.0 | [-1.9, +3.8] | 0.5480 | 0.5480 |
| Slayer 1.06 vs 1.00 (en) | Slayer1B-1.06 | Slayer1B-1.00 | 4374 | +5.7 | [+4.7, +6.8] | 0.0001 | 0.0001 |
| Slayer vs inne | Slayer1B-1.06 | Bielik-1.5B-v3 | 625 | -10.6 | [-13.4, -7.8] | 0.0001 | 0.0002 |
| Slayer vs inne | Slayer1B-1.06 | LFM3-1.7B-Base | 625 | -2.0 | [-5.0, +0.9] | 0.2018 | 0.2018 |

## Do przeglądu tłumaczenia: 3 rekordów (EN − PL ≥ 0,5 średnio po modelach)

ewok-pl-0141, ewok-pl-0149, ewok-pl-0171
