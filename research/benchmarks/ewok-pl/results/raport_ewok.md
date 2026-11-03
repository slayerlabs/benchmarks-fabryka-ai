# EWoK-PL: wyniki

Wynik EWoK w % (losowo 50). CI95: bootstrap po rekordach oraz po szablonach (rekordy jednego szablonu nie są niezależne, ten przedział jest właściwy). `oba` = obie pary trafione (25 tylko przy niezależnych porównaniach).

| model | PL ewok (n=625) | PL CI po szablonach | PL oba | EN te same 625 | EN pełny (4374) | PL stały target | EN stały target |
|---|---|---|---|---|---|---|---|
| Aster-0.5B(fp32) | 54.6 [52.4, 56.8] | [51.5, 57.8] | 21.0 [17.9, 24.2] | 51.7 [49.6, 53.8] | 50.8 [49.9, 51.7] | 85.4 [82.7, 88.2] | 80.0 [78.8, 81.2] |
| Bielik-1.5B-v3 | 66.0 [63.4, 68.5] | [61.6, 70.4] | 42.4 [38.4, 46.2] | 62.8 [60.6, 65.1] | 69.5 [68.6, 70.3] | 75.4 [71.8, 78.7] | 63.7 [62.3, 65.1] |
| LFM3-1.7B-Base | 57.4 [55.3, 59.6] | [54.2, 60.7] | 23.8 [20.6, 27.2] | 59.3 [56.9, 61.7] | 66.0 [65.1, 66.9] | 80.5 [77.3, 83.5] | 68.3 [66.9, 69.7] |
| Slayer1B-1.00 | 54.1 [51.7, 56.6] | [49.9, 58.3] | 23.0 [19.8, 26.4] | 52.6 [50.4, 54.9] | 53.0 [52.1, 53.9] | 82.2 [79.2, 85.3] | 77.3 [76.1, 78.5] |
| Slayer1B-1.01 | 53.8 [51.4, 56.1] | [49.8, 57.8] | 22.1 [18.9, 25.3] | 54.5 [52.4, 56.6] | 55.4 [54.5, 56.3] | 83.4 [80.5, 86.2] | 77.4 [76.1, 78.6] |
| Slayer1B-1.02 | 53.0 [50.7, 55.2] | [49.2, 56.8] | 18.9 [15.8, 22.1] | 53.4 [51.1, 55.6] | 56.2 [55.3, 57.1] | 84.3 [81.4, 87.0] | 75.5 [74.2, 76.8] |
| Slayer1B-1.03 | 55.4 [53.2, 57.7] | [51.8, 59.1] | 22.2 [18.9, 25.6] | 54.0 [51.9, 56.1] | 56.6 [55.7, 57.5] | 81.4 [78.4, 84.5] | 75.7 [74.4, 77.0] |
| Slayer1B-1.04 | 56.2 [54.1, 58.4] | [53.3, 59.3] | 21.9 [18.6, 25.3] | 55.5 [53.4, 57.7] | 57.4 [56.5, 58.3] | 86.2 [83.5, 88.8] | 77.1 [75.8, 78.3] |
| Slayer1B-1.05 | 54.8 [52.6, 57.0] | [51.3, 58.4] | 21.8 [18.6, 25.0] | 55.4 [53.2, 57.7] | 58.4 [57.5, 59.3] | 84.0 [81.1, 86.7] | 72.5 [71.1, 73.8] |
| Slayer1B-1.06 | 54.0 [51.7, 56.4] | [50.1, 58.0] | 22.7 [19.5, 26.1] | 56.5 [54.2, 58.7] | 59.0 [58.1, 59.9] | 81.9 [79.0, 85.0] | 74.5 [73.2, 75.8] |

## PL wg pary pojęć

| grupa | n | Aster-0.5B(fp32) | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| believe / doubt | 55 | 53 | 48 | 43 | 48 | 49 | 47 | 50 | 49 | 49 | 45 |
| believe / imagine | 10 | 50 | 70 | 55 | 40 | 55 | 50 | 70 | 65 | 75 | 85 |
| choose / - | 165 | 55 | 68 | 61 | 49 | 52 | 50 | 52 | 55 | 53 | 49 |
| feel / not feel | 20 | 58 | 68 | 58 | 58 | 55 | 63 | 63 | 63 | 63 | 58 |
| have no preference / prefer | 10 | 50 | 50 | 60 | 50 | 40 | 50 | 55 | 45 | 45 | 35 |
| hear / not hear | 30 | 57 | 83 | 62 | 47 | 55 | 53 | 63 | 68 | 75 | 82 |
| intend / not intend | 70 | 58 | 79 | 62 | 61 | 59 | 59 | 63 | 64 | 61 | 56 |
| make an effort / make no effort | 45 | 74 | 90 | 61 | 88 | 78 | 71 | 73 | 74 | 79 | 78 |
| make more effort / make less effort | 220 | 49 | 58 | 56 | 52 | 50 | 50 | 51 | 51 | 47 | 50 |

## EN, te same 625 rekordów, wg pary pojęć

| grupa | n | Aster-0.5B(fp32) | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| believe / doubt | 55 | 53 | 48 | 49 | 57 | 56 | 49 | 50 | 46 | 49 | 50 |
| believe / imagine | 10 | 40 | 70 | 70 | 40 | 60 | 55 | 55 | 70 | 50 | 65 |
| choose / - | 165 | 52 | 60 | 63 | 50 | 51 | 49 | 49 | 52 | 52 | 50 |
| feel / not feel | 20 | 70 | 60 | 50 | 60 | 53 | 45 | 55 | 58 | 55 | 55 |
| have no preference / prefer | 10 | 50 | 70 | 90 | 55 | 75 | 60 | 60 | 80 | 65 | 95 |
| hear / not hear | 30 | 48 | 85 | 60 | 48 | 53 | 63 | 65 | 67 | 77 | 75 |
| intend / not intend | 70 | 49 | 69 | 59 | 56 | 58 | 60 | 61 | 61 | 59 | 64 |
| make an effort / make no effort | 45 | 62 | 68 | 68 | 71 | 78 | 74 | 76 | 71 | 72 | 72 |
| make more effort / make less effort | 220 | 49 | 63 | 56 | 49 | 50 | 50 | 50 | 52 | 53 | 53 |

## EN pełny wg domeny

| grupa | n | Aster-0.5B(fp32) | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| agent-properties | 1120 | 51 | 65 | 62 | 51 | 53 | 52 | 53 | 55 | 55 | 55 |
| material-dynamics | 780 | 47 | 86 | 79 | 53 | 60 | 62 | 62 | 61 | 63 | 67 |
| material-properties | 124 | 52 | 55 | 58 | 51 | 52 | 57 | 54 | 59 | 60 | 60 |
| physical-dynamics | 75 | 57 | 69 | 71 | 57 | 52 | 61 | 61 | 63 | 61 | 61 |
| physical-interactions | 280 | 52 | 62 | 62 | 53 | 51 | 53 | 53 | 50 | 56 | 55 |
| physical-relations | 415 | 49 | 58 | 60 | 50 | 50 | 50 | 50 | 52 | 52 | 50 |
| quantitative-properties | 190 | 58 | 71 | 69 | 65 | 71 | 68 | 68 | 64 | 67 | 66 |
| social-interactions | 175 | 56 | 80 | 76 | 61 | 67 | 70 | 73 | 69 | 70 | 71 |
| social-properties | 185 | 60 | 83 | 72 | 60 | 61 | 62 | 68 | 68 | 65 | 66 |
| social-relations | 785 | 50 | 68 | 63 | 50 | 52 | 51 | 52 | 55 | 56 | 57 |
| spatial-relations | 245 | 46 | 61 | 55 | 52 | 56 | 59 | 57 | 59 | 59 | 57 |

## Kontrasty (różnica ×100: punkty ewok, a dla marginesu nat; sparowany test permutacyjny; Holm w rodzinie i na wszystkich kontrastach trafności naraz; pary pojęć i domeny jako klastry, t przy df = k − 1)

| rodzina | A | B | n | A−B | CI95 po szablonach | z po szablonach | werdykt po szablonach | p_holm wszystkie | po parach: t (k), p_holm, werdykt po Holmie | po domenach: t (k), p_holm, werdykt po Holmie |
|---|---|---|---|---|---|---|---|---|---|---|
| PL vs EN | Aster-0.5B(fp32) PL | Aster-0.5B(fp32) EN | 625 | +2.9 | [-0.8, +6.6] | +1.51 | szum | 1.0000 | +1.32 (9), 1.0000, szum | — |
| PL vs EN | Bielik-1.5B-v3 PL | Bielik-1.5B-v3 EN | 625 | +3.2 | [-0.2, +6.7] | +1.81 | szum | 1.0000 | +0.64 (9), 1.0000, szum | — |
| PL vs EN | LFM3-1.7B-Base PL | LFM3-1.7B-Base EN | 625 | -1.8 | [-5.2, +1.6] | -1.05 | szum | 1.0000 | -1.43 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.00 PL | Slayer1B-1.00 EN | 625 | +1.4 | [-1.2, +4.2] | +1.05 | szum | 1.0000 | +0.24 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.01 PL | Slayer1B-1.01 EN | 625 | -0.7 | [-4.1, +2.4] | -0.43 | szum | 1.0000 | -1.16 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.02 PL | Slayer1B-1.02 EN | 625 | -0.4 | [-5.0, +4.1] | -0.17 | szum | 1.0000 | -0.52 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.03 PL | Slayer1B-1.03 EN | 625 | +1.4 | [-2.7, +5.5] | +0.68 | szum | 1.0000 | +1.09 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.04 PL | Slayer1B-1.04 EN | 625 | +0.7 | [-3.1, +4.4] | +0.38 | szum | 1.0000 | -0.61 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.05 PL | Slayer1B-1.05 EN | 625 | -0.6 | [-4.7, +3.4] | -0.31 | szum | 1.0000 | +0.43 (9), 1.0000, szum | — |
| PL vs EN | Slayer1B-1.06 PL | Slayer1B-1.06 EN | 625 | -2.5 | [-6.9, +1.8] | -1.12 | szum | 1.0000 | -0.63 (9), 1.0000, szum | — |
| Slayer kolejne | Slayer1B-1.01 | Slayer1B-1.00 | 625 | -0.3 | [-2.9, +2.2] | -0.25 | szum | 1.0000 | +0.01 (9), 1.0000, szum | — |
| Slayer kolejne | Slayer1B-1.02 | Slayer1B-1.01 | 625 | -0.8 | [-3.5, +2.0] | -0.57 | szum | 1.0000 | +0.05 (9), 1.0000, szum | — |
| Slayer kolejne | Slayer1B-1.03 | Slayer1B-1.02 | 625 | +2.5 | [-0.1, +5.0] | +1.94 | szum | 1.0000 | +2.48 (9), 0.8444, szum | — |
| Slayer kolejne | Slayer1B-1.04 | Slayer1B-1.03 | 625 | +0.8 | [-2.1, +3.7] | +0.53 | szum | 1.0000 | -0.49 (9), 1.0000, szum | — |
| Slayer kolejne | Slayer1B-1.05 | Slayer1B-1.04 | 625 | -1.4 | [-4.1, +1.3] | -1.06 | szum | 1.0000 | +0.88 (9), 1.0000, szum | — |
| Slayer kolejne | Slayer1B-1.06 | Slayer1B-1.05 | 625 | -0.8 | [-3.2, +1.6] | -0.66 | szum | 1.0000 | -0.47 (9), 1.0000, szum | — |
| Slayer 1.06 vs 1.00 (pl) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | -0.1 | [-4.4, +4.3] | -0.04 | szum | 1.0000 | +0.72 (9), 1.0000, szum | — |
| Slayer 1.06 vs 1.00 (en625) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | +3.8 | [-0.2, +7.8] | +1.90 | szum | 1.0000 | +1.88 (9), 1.0000, szum | — |
| Slayer 1.06 vs 1.00 (en) | Slayer1B-1.06 | Slayer1B-1.00 | 4374 | +6.0 | [+4.5, +7.6] | +7.78 | pewne | 0.0023 | +7.06 (177), 0.0000, pewne | +4.58 (11), 0.0010, pewne |
| Slayer 1.06 vs 1.00: PL − EN625 (różnica różnic) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | -3.9 | [-9.1, +1.1] | -1.51 | szum | 1.0000 | -0.74 (9), 1.0000, szum | — |
| Slayer 1.06 vs 1.00, margines (pl) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | +11.3 | [-12.7, +34.9] | +0.94 | szum | — | +1.92 (9), nan, szum | — |
| Slayer 1.06 vs 1.00, margines (en625) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | +11.6 | [-1.6, +24.3] | +1.75 | szum | — | +2.34 (9), nan, szum | — |
| Inne vs Slayer 1.06 (pl) | Aster-0.5B(fp32) | Slayer1B-1.06 | 625 | +0.6 | [-2.9, +4.1] | +0.31 | szum | 1.0000 | -0.69 (9), 1.0000, szum | — |
| Inne vs Slayer 1.06 (pl) | Bielik-1.5B-v3 | Slayer1B-1.06 | 625 | +12.0 | [+8.0, +16.1] | +5.82 | pewne | 0.0023 | +2.26 (9), 1.0000, szum | — |
| Inne vs Slayer 1.06 (pl) | LFM3-1.7B-Base | Slayer1B-1.06 | 625 | +3.4 | [-0.8, +7.6] | +1.62 | szum | 1.0000 | -0.39 (9), 1.0000, szum | — |

## Do przeglądu tłumaczenia, trudniejsze po pl: 37 rekordów (|EN − PL| ≥ 0.5 średnio po Bielik-1.5B-v3, LFM3-1.7B-Base)

ewok-pl-0010, ewok-pl-0029, ewok-pl-0060, ewok-pl-0064, ewok-pl-0070, ewok-pl-0080, ewok-pl-0094, ewok-pl-0113, ewok-pl-0116, ewok-pl-0129, ewok-pl-0153, ewok-pl-0158, ewok-pl-0171, ewok-pl-0179, ewok-pl-0194, ewok-pl-0210, ewok-pl-0224, ewok-pl-0233, ewok-pl-0251, ewok-pl-0253, ewok-pl-0260, ewok-pl-0287, ewok-pl-0344, ewok-pl-0356, ewok-pl-0421, ewok-pl-0432, ewok-pl-0441, ewok-pl-0454, ewok-pl-0471, ewok-pl-0510, ewok-pl-0513, ewok-pl-0514, ewok-pl-0521, ewok-pl-0532, ewok-pl-0596, ewok-pl-0605, ewok-pl-0617

## Do przeglądu tłumaczenia, latwiejsze po pl: 42 rekordów (|EN − PL| ≥ 0.5 średnio po Bielik-1.5B-v3, LFM3-1.7B-Base)

ewok-pl-0057, ewok-pl-0066, ewok-pl-0071, ewok-pl-0074, ewok-pl-0096, ewok-pl-0097, ewok-pl-0104, ewok-pl-0107, ewok-pl-0138, ewok-pl-0139, ewok-pl-0143, ewok-pl-0157, ewok-pl-0159, ewok-pl-0163, ewok-pl-0180, ewok-pl-0185, ewok-pl-0189, ewok-pl-0193, ewok-pl-0202, ewok-pl-0203, ewok-pl-0209, ewok-pl-0223, ewok-pl-0236, ewok-pl-0242, ewok-pl-0249, ewok-pl-0264, ewok-pl-0292, ewok-pl-0294, ewok-pl-0307, ewok-pl-0312, ewok-pl-0326, ewok-pl-0340, ewok-pl-0349, ewok-pl-0352, ewok-pl-0379, ewok-pl-0399, ewok-pl-0409, ewok-pl-0415, ewok-pl-0438, ewok-pl-0479, ewok-pl-0526, ewok-pl-0582
