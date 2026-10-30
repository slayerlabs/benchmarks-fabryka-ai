# EWoK-PL: wyniki

Wynik EWoK w % (losowo 50). CI95: bootstrap po rekordach oraz po szablonach (rekordy jednego szablonu nie są niezależne, ten przedział jest właściwy). `oba` = obie pary trafione (25 tylko przy niezależnych porównaniach).

| model | PL ewok (n=625) | PL CI po szablonach | PL oba | EN te same 625 | EN pełny (4374) | PL stały target | EN stały target |
|---|---|---|---|---|---|---|---|
| Bielik-1.5B-v3 | 66.0 [63.4, 68.5] | [61.6, 70.4] | 42.4 [38.4, 46.2] | 62.8 [60.6, 65.1] | 69.5 [68.6, 70.3] | 75.4 [71.8, 78.7] | 63.7 [62.3, 65.1] |
| LFM3-1.7B-Base | 57.4 [55.0, 59.8] | [53.5, 61.3] | 27.0 [23.7, 30.6] | 66.6 [64.2, 69.1] | 69.7 [68.8, 70.6] | 73.6 [70.1, 77.1] | 56.4 [55.0, 57.9] |
| Slayer1B-1.00 | 54.4 [52.0, 56.8] | [50.2, 58.6] | 23.5 [20.3, 27.0] | 51.3 [49.3, 53.4] | 53.1 [52.3, 54.0] | 81.1 [77.9, 84.2] | 77.4 [76.2, 78.6] |
| Slayer1B-1.01 | 53.0 [50.6, 55.3] | [49.0, 57.0] | 21.3 [18.1, 24.5] | 53.5 [51.4, 55.8] | 55.5 [54.7, 56.4] | 80.3 [77.1, 83.4] | 74.2 [72.9, 75.4] |
| Slayer1B-1.02 | 54.4 [52.1, 56.7] | [50.3, 58.5] | 22.6 [19.4, 25.9] | 52.8 [50.6, 55.0] | 57.1 [56.2, 57.9] | 83.7 [80.8, 86.6] | 76.3 [75.1, 77.6] |
| Slayer1B-1.03 | 54.6 [52.3, 56.9] | [50.8, 58.3] | 21.1 [17.9, 24.5] | 52.0 [49.8, 54.1] | 55.8 [54.9, 56.7] | 81.1 [78.1, 84.2] | 75.9 [74.6, 77.2] |
| Slayer1B-1.04 | 56.4 [54.3, 58.5] | [53.4, 59.5] | 21.1 [18.1, 24.3] | 56.0 [53.7, 58.2] | 57.4 [56.6, 58.3] | 85.0 [82.1, 87.7] | 75.6 [74.3, 76.9] |
| Slayer1B-1.05 | 55.6 [53.3, 57.8] | [52.3, 59.0] | 22.6 [19.2, 25.9] | 57.0 [54.8, 59.1] | 58.8 [57.9, 59.7] | 83.4 [80.5, 86.2] | 69.8 [68.4, 71.2] |
| Slayer1B-1.06 | 55.4 [53.0, 57.8] | [51.6, 59.3] | 25.1 [21.8, 28.5] | 56.2 [54.0, 58.5] | 58.9 [58.0, 59.8] | 83.7 [80.8, 86.6] | 74.6 [73.3, 75.9] |

## PL wg pary pojęć

| grupa | n | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|
| believe / doubt | 55 | 48 | 42 | 50 | 50 | 48 | 51 | 53 | 48 | 47 |
| believe / imagine | 10 | 70 | 50 | 50 | 40 | 55 | 60 | 70 | 70 | 75 |
| choose / - | 165 | 68 | 62 | 48 | 52 | 52 | 53 | 54 | 53 | 51 |
| feel / not feel | 20 | 68 | 58 | 60 | 55 | 68 | 65 | 68 | 60 | 58 |
| have no preference / prefer | 10 | 50 | 65 | 50 | 35 | 50 | 55 | 45 | 40 | 40 |
| hear / not hear | 30 | 83 | 75 | 48 | 53 | 58 | 52 | 70 | 78 | 85 |
| intend / not intend | 70 | 79 | 61 | 64 | 61 | 56 | 63 | 64 | 64 | 65 |
| make an effort / make no effort | 45 | 90 | 54 | 87 | 72 | 70 | 72 | 76 | 80 | 77 |
| make more effort / make less effort | 220 | 58 | 55 | 51 | 49 | 52 | 50 | 50 | 48 | 49 |

## EN, te same 625 rekordów, wg pary pojęć

| grupa | n | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|
| believe / doubt | 55 | 48 | 52 | 55 | 59 | 46 | 53 | 46 | 48 | 48 |
| believe / imagine | 10 | 70 | 50 | 40 | 65 | 60 | 60 | 60 | 65 | 75 |
| choose / - | 165 | 60 | 65 | 49 | 50 | 48 | 48 | 53 | 53 | 51 |
| feel / not feel | 20 | 60 | 53 | 63 | 53 | 48 | 50 | 65 | 60 | 48 |
| have no preference / prefer | 10 | 70 | 80 | 50 | 65 | 60 | 55 | 65 | 60 | 85 |
| hear / not hear | 30 | 85 | 83 | 52 | 47 | 60 | 57 | 63 | 70 | 73 |
| intend / not intend | 70 | 69 | 71 | 54 | 56 | 58 | 56 | 65 | 66 | 67 |
| make an effort / make no effort | 45 | 68 | 79 | 59 | 70 | 68 | 69 | 70 | 74 | 74 |
| make more effort / make less effort | 220 | 63 | 67 | 50 | 50 | 52 | 49 | 52 | 53 | 51 |

## EN pełny wg domeny

| grupa | n | Bielik-1.5B-v3 | LFM3-1.7B-Base | Slayer1B-1.00 | Slayer1B-1.01 | Slayer1B-1.02 | Slayer1B-1.03 | Slayer1B-1.04 | Slayer1B-1.05 | Slayer1B-1.06 |
|---|---|---|---|---|---|---|---|---|---|---|
| agent-properties | 1120 | 65 | 68 | 51 | 52 | 52 | 51 | 55 | 56 | 55 |
| material-dynamics | 780 | 86 | 84 | 53 | 58 | 66 | 61 | 60 | 64 | 67 |
| material-properties | 124 | 55 | 58 | 54 | 51 | 58 | 51 | 56 | 59 | 57 |
| physical-dynamics | 75 | 69 | 75 | 59 | 63 | 58 | 63 | 66 | 62 | 61 |
| physical-interactions | 280 | 62 | 61 | 52 | 53 | 54 | 53 | 51 | 55 | 54 |
| physical-relations | 415 | 58 | 58 | 50 | 49 | 51 | 49 | 51 | 51 | 51 |
| quantitative-properties | 190 | 71 | 66 | 63 | 67 | 69 | 66 | 66 | 69 | 67 |
| social-interactions | 175 | 80 | 84 | 69 | 69 | 74 | 72 | 72 | 71 | 72 |
| social-properties | 185 | 83 | 77 | 58 | 68 | 61 | 68 | 65 | 64 | 68 |
| social-relations | 785 | 68 | 67 | 51 | 52 | 51 | 53 | 56 | 57 | 57 |
| spatial-relations | 245 | 61 | 61 | 54 | 59 | 58 | 56 | 57 | 57 | 55 |

## Kontrasty (różnica punktów ewok ×100, sparowany test permutacyjny, Holm w rodzinie)

| rodzina | A | B | n | A−B | CI95 po rekordach | CI95 po szablonach | p | p po szablonach | p_holm po szablonach |
|---|---|---|---|---|---|---|---|---|---|
| PL vs EN | Bielik-1.5B-v3 PL | Bielik-1.5B-v3 EN | 625 | +3.2 | [+0.6, +5.8] | [-0.2, +6.7] | 0.0171 | 0.0890 | 0.6229 |
| PL vs EN | LFM3-1.7B-Base PL | LFM3-1.7B-Base EN | 625 | -9.3 | [-11.8, -6.6] | [-13.4, -5.2] | 0.0001 | 0.0001 | 0.0009 |
| PL vs EN | Slayer1B-1.00 PL | Slayer1B-1.00 EN | 625 | +3.1 | [+1.0, +5.3] | [+0.2, +6.2] | 0.0055 | 0.0536 | 0.4288 |
| PL vs EN | Slayer1B-1.01 PL | Slayer1B-1.01 EN | 625 | -0.6 | [-3.1, +1.9] | [-4.3, +3.0] | 0.7124 | 0.7923 | 1.0000 |
| PL vs EN | Slayer1B-1.02 PL | Slayer1B-1.02 EN | 625 | +1.6 | [-1.1, +4.2] | [-2.6, +5.7] | 0.2715 | 0.4714 | 1.0000 |
| PL vs EN | Slayer1B-1.03 PL | Slayer1B-1.03 EN | 625 | +2.6 | [-0.2, +5.3] | [-1.5, +6.5] | 0.0698 | 0.2349 | 1.0000 |
| PL vs EN | Slayer1B-1.04 PL | Slayer1B-1.04 EN | 625 | +0.4 | [-2.3, +3.2] | [-3.6, +4.1] | 0.8264 | 0.8754 | 1.0000 |
| PL vs EN | Slayer1B-1.05 PL | Slayer1B-1.05 EN | 625 | -1.4 | [-4.0, +1.3] | [-5.1, +2.4] | 0.3427 | 0.5089 | 1.0000 |
| PL vs EN | Slayer1B-1.06 PL | Slayer1B-1.06 EN | 625 | -0.9 | [-3.8, +1.9] | [-5.1, +3.3] | 0.5780 | 0.7125 | 1.0000 |
| Slayer kolejne | Slayer1B-1.01 | Slayer1B-1.00 | 625 | -1.4 | [-3.4, +0.6] | [-3.9, +1.0] | 0.1899 | 0.2896 | 1.0000 |
| Slayer kolejne | Slayer1B-1.02 | Slayer1B-1.01 | 625 | +1.4 | [-0.8, +3.7] | [-1.6, +4.6] | 0.2368 | 0.3984 | 1.0000 |
| Slayer kolejne | Slayer1B-1.03 | Slayer1B-1.02 | 625 | +0.2 | [-2.1, +2.4] | [-2.5, +2.8] | 0.9433 | 0.9510 | 1.0000 |
| Slayer kolejne | Slayer1B-1.04 | Slayer1B-1.03 | 625 | +1.8 | [-0.6, +4.2] | [-1.3, +5.0] | 0.1443 | 0.2772 | 1.0000 |
| Slayer kolejne | Slayer1B-1.05 | Slayer1B-1.04 | 625 | -0.8 | [-2.9, +1.2] | [-2.9, +1.4] | 0.4925 | 0.5098 | 1.0000 |
| Slayer kolejne | Slayer1B-1.06 | Slayer1B-1.05 | 625 | -0.2 | [-2.3, +1.8] | [-2.5, +2.1] | 0.8758 | 0.8920 | 1.0000 |
| Slayer 1.06 vs 1.00 (pl) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | +1.0 | [-1.9, +3.8] | [-3.6, +5.5] | 0.5480 | 0.7074 | 0.7074 |
| Slayer 1.06 vs 1.00 (en625) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | +5.0 | [+2.2, +7.6] | [+0.9, +9.0] | 0.0006 | 0.0201 | 0.0201 |
| Slayer 1.06 vs 1.00 (en) | Slayer1B-1.06 | Slayer1B-1.00 | 4374 | +5.7 | [+4.7, +6.8] | [+4.2, +7.3] | 0.0001 | 0.0001 | 0.0001 |
| Slayer 1.06 vs 1.00: PL − EN625 (różnica różnic) | Slayer1B-1.06 | Slayer1B-1.00 | 625 | -4.0 | [-7.4, -0.6] | [-8.9, +0.9] | 0.0226 | 0.1284 | 0.1284 |
| Inne vs Slayer 1.06 (pl) | Bielik-1.5B-v3 | Slayer1B-1.06 | 625 | +10.6 | [+7.8, +13.4] | [+6.4, +14.8] | 0.0001 | 0.0001 | 0.0002 |
| Inne vs Slayer 1.06 (pl) | LFM3-1.7B-Base | Slayer1B-1.06 | 625 | +2.0 | [-0.9, +5.0] | [-2.8, +6.6] | 0.2018 | 0.4361 | 0.4361 |

## Do przeglądu tłumaczenia, trudniejsze po pl: 51 rekordów (|EN − PL| ≥ 0.5 średnio po Bielik-1.5B-v3, LFM3-1.7B-Base)

ewok-pl-0010, ewok-pl-0021, ewok-pl-0025, ewok-pl-0029, ewok-pl-0031, ewok-pl-0067, ewok-pl-0080, ewok-pl-0081, ewok-pl-0094, ewok-pl-0113, ewok-pl-0116, ewok-pl-0129, ewok-pl-0171, ewok-pl-0179, ewok-pl-0194, ewok-pl-0197, ewok-pl-0210, ewok-pl-0224, ewok-pl-0234, ewok-pl-0251, ewok-pl-0260, ewok-pl-0287, ewok-pl-0322, ewok-pl-0356, ewok-pl-0400, ewok-pl-0404, ewok-pl-0407, ewok-pl-0410, ewok-pl-0430, ewok-pl-0432, ewok-pl-0454, ewok-pl-0470, ewok-pl-0471, ewok-pl-0489, ewok-pl-0492, ewok-pl-0494, ewok-pl-0510, ewok-pl-0513, ewok-pl-0514, ewok-pl-0516, ewok-pl-0521, ewok-pl-0532, ewok-pl-0534, ewok-pl-0536, ewok-pl-0538, ewok-pl-0558, ewok-pl-0560, ewok-pl-0578, ewok-pl-0605, ewok-pl-0607, ewok-pl-0617

## Do przeglądu tłumaczenia, latwiejsze po pl: 30 rekordów (|EN − PL| ≥ 0.5 średnio po Bielik-1.5B-v3, LFM3-1.7B-Base)

ewok-pl-0018, ewok-pl-0033, ewok-pl-0096, ewok-pl-0104, ewok-pl-0107, ewok-pl-0114, ewok-pl-0118, ewok-pl-0135, ewok-pl-0138, ewok-pl-0157, ewok-pl-0159, ewok-pl-0193, ewok-pl-0202, ewok-pl-0223, ewok-pl-0236, ewok-pl-0248, ewok-pl-0249, ewok-pl-0264, ewok-pl-0306, ewok-pl-0307, ewok-pl-0314, ewok-pl-0328, ewok-pl-0340, ewok-pl-0352, ewok-pl-0357, ewok-pl-0363, ewok-pl-0379, ewok-pl-0438, ewok-pl-0526, ewok-pl-0581
