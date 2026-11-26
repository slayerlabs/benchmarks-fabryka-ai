# Slayer 1B 1.09, krok 40 000 (~67 mld tokenów), trening w toku, wynik wstępny: porównanie z 1.08 na 15 testach

<!-- Plik wygenerowany przez code/raport_md.py z LICZBY.json. Nie edytuj ręcznie. -->

Etykieta: **1.09, krok 40 000 (~67 mld tokenów), trening w toku, wynik wstępny**. Checkpoint w trakcie treningu, kontynuacja 1.08, jeszcze nie wydana wersja; porównanie nie mówi nic o modelu końcowym 1.09. Protokół: [`PROTOKOL.md`](PROTOKOL.md).

## Główne twierdzenie

Po Holmie (m = 15) Slayer 1B 1.09 z kroku 40 000 jest lepszy od 1.08 na 9 z 15 testów, gorszy na 0, w szumie na 6, nierozstrzygnięty na 0.

- lepszy: ARC-Challenge (pewne po Holmie); ARC-Easy (pewne po Holmie); EWoK (pewne po Holmie); HellaSwag (pewne po Holmie); LAMBADA (pewne po Holmie); PIQA (pewne po Holmie); PubMedQA (pewne po Holmie); WikiText-2 (pewne po Holmie); WinoGrande (prawdopodobne po Holmie)
- gorszy: żaden
- szum: BLiMP, MathQA, MedMCQA, MultiBLiMP-PL, Social IQa, WSC273
- nierozstrzygnięty: żaden

Obalenie: inny podział lepsze/gorsze/szum po przeliczeniu niezależnym kodem z tych samych próbek albo niezgodna kontrola narzędzia na teście z werdyktem. „Szum” znaczy różnicę poniżej progu, nie brak różnicy.

## Tabela

Δ = 1.09 k40000 − 1.08 przeliczone na tej samej karcie, na tych samych pytaniach. SE Δ parowane po pytaniach (z) albo po klastrach testu (t, df = k − 1): BLiMP po paradygmatach, WinoGrande po parach zdań, WSC273 po schematach, EWoK po szablonach. WikiText-2: Δ w byte perplexity (niżej = lepiej), SE i statystyka na bits per byte z dokumentem jako klastrem. Werdykt: |z| ≥ 3 pewne, 2–3 prawdopodobne, < 2 szum; t przez p. Holm: m = 15. Kolumna 1.08 to wartość z `manifest.jsonl` przebiegu.

| test | n | 1.08 (manifest) ± SE | 1.09 k40000 ± SE | Δ | SE Δ | statystyka | werdykt | p Holma | po Holmie | wynik |
|---|---:|---:|---:|---:|---:|---|---|---:|---|---|
| ARC-Challenge | 1172 | 0,3003 ± 0,0134 | 0,3498 ± 0,0139 | +0,0495 | 0,0116 | z = 4,26 | pewne | 0,0002 | tak (pewne) | lepszy (pewne) |
| ARC-Easy | 2376 | 0,5838 ± 0,0101 | 0,6662 ± 0,0097 | +0,0825 | 0,0089 | z = 9,26 | pewne | 0,0000 | tak (pewne) | lepszy (pewne) |
| BLiMP | 67000 | 0,8047 ± 0,0213 | 0,8148 ± 0,0214 | +0,0101 | 0,0054 | t = 1,86, df = 66 | szum | 0,3378 | nie (szum) | szum |
| EWoK | 4374 | 0,5990 ± 0,0075 | 0,6278 ± 0,0080 | +0,0288 | 0,0067 | t = 4,27, df = 842 | pewne | 0,0002 | tak (pewne) | lepszy (pewne) |
| HellaSwag | 10042 | 0,4341 ± 0,0049 | 0,5280 ± 0,0050 | +0,0939 | 0,0036 | z = 26,25 | pewne | 0,0000 | tak (pewne) | lepszy (pewne) |
| LAMBADA | 5153 | 0,4013 ± 0,0068 | 0,4537 ± 0,0069 | +0,0524 | 0,0060 | z = 8,74 | pewne | 0,0000 | tak (pewne) | lepszy (pewne) |
| MathQA | 2985 | 0,2281 ± 0,0077 | 0,2251 ± 0,0076 | −0,0030 | 0,0069 | z = −0,44 | szum | 1,0000 | nie (szum) | szum |
| MedMCQA | 4183 | 0,3122 ± 0,0072 | 0,3005 ± 0,0071 | −0,0117 | 0,0052 | z = −2,25 | prawdopodobne | 0,1469 | nie (szum) | szum |
| MultiBLiMP-PL | 3272 | 0,9875 ± 0,0019 | 0,9856 ± 0,0021 | −0,0018 | 0,0023 | z = −0,79 | szum | 1,0000 | nie (szum) | szum |
| PIQA | 1838 | 0,6621 ± 0,0110 | 0,7122 ± 0,0106 | +0,0501 | 0,0084 | z = 5,94 | pewne | 0,0000 | tak (pewne) | lepszy (pewne) |
| PubMedQA | 500 | 0,4340 ± 0,0222 | 0,5620 ± 0,0222 | +0,1280 | 0,0217 | z = 5,89 | pewne | 0,0000 | tak (pewne) | lepszy (pewne) |
| Social IQa | 1954 | 0,3966 ± 0,0111 | 0,4089 ± 0,0111 | +0,0123 | 0,0073 | z = 1,68 | szum | 0,3710 | nie (szum) | szum |
| WikiText-2 | 62 | 1,780 ± 0,0149 | 1,702 ± 0,0156 | −0,078 | 0,0035 bpb | t = −18,23, df = 61 | pewne | 0,0000 | tak (pewne) | lepszy (pewne) |
| WinoGrande | 1267 | 0,5367 ± 0,0127 | 0,5770 ± 0,0128 | +0,0403 | 0,0147 | t = 2,74, df = 982 | prawdopodobne | 0,0437 | tak (prawdopodobne) | lepszy (prawdopodobne) |
| WSC273 | 273 | 0,6154 ± 0,0221 | 0,6374 ± 0,0241 | +0,0220 | 0,0238 | t = 0,93, df = 134 | szum | 1,0000 | nie (szum) | szum |

## Kontrola narzędzia

1.08 przeliczone tu wobec 1.08 z `manifest.jsonl` przebiegu (karta RTX 5090). Zgodna: to samo n i |różnica| ≤ 0,5 SE testu z manifestu.

| test | 1.08 manifest | 1.08 przeliczone | różnica | w SE | n równe | kontrola |
|---|---:|---:|---:|---:|---|---|
| ARC-Challenge | 0,300341 | 0,300341 | 0,000000 | 0,00 | tak | zgodna |
| ARC-Easy | 0,583754 | 0,583754 | 0,000000 | 0,00 | tak | zgodna |
| BLiMP | 0,804731 | 0,804731 | 0,000000 | 0,00 | tak | zgodna |
| EWoK | 0,598994 | 0,598994 | 0,000000 | 0,00 | tak | zgodna |
| HellaSwag | 0,434077 | 0,434077 | 0,000000 | 0,00 | tak | zgodna |
| LAMBADA | 0,401320 | 0,401320 | 0,000000 | 0,00 | tak | zgodna |
| MathQA | 0,228141 | 0,228141 | 0,000000 | 0,00 | tak | zgodna |
| MedMCQA | 0,312216 | 0,312216 | 0,000000 | 0,00 | tak | zgodna |
| MultiBLiMP-PL | 0,987469 | 0,987469 | 0,000000 | 0,00 | tak | zgodna |
| PIQA | 0,662133 | 0,662133 | 0,000000 | 0,00 | tak | zgodna |
| PubMedQA | 0,434000 | 0,434000 | 0,000000 | 0,00 | tak | zgodna |
| Social IQa | 0,396622 | 0,396622 | 0,000000 | 0,00 | tak | zgodna |
| WikiText-2 | 1,780216 | 1,780216 | 0,000000 | 0,00 | tak | zgodna |
| WinoGrande | 0,536701 | 0,536701 | 0,000000 | 0,00 | tak | zgodna |
| WSC273 | 0,615385 | 0,615385 | 0,000000 | 0,00 | tak | zgodna |

## Bazy i kontrola sensu

| test | metryka | bazy | 1.08 przeliczone ± SE | kontrola sensu 1.09 | kontrola sensu 1.08 |
|---|---|---|---:|---|---|
| ARC-Challenge | acc_norm | losowa 0,2502, większościowa 0,2654 | 0,3003 ± 0,0134 | ok | ok |
| ARC-Easy | acc | losowa 0,2502, większościowa 0,2664 | 0,5838 ± 0,0101 | ok | ok |
| BLiMP | acc | losowa 0,5000 | 0,8047 ± 0,0213 | ok | ok |
| EWoK | ewok | losowa 0,5000 | 0,5990 ± 0,0075 | ok | ok |
| HellaSwag | acc_norm | losowa 0,2500, większościowa 0,2573 | 0,4341 ± 0,0049 | ok | ok |
| LAMBADA | acc | losowa 0,0000, większościowa 0,0031 | 0,4013 ± 0,0068 | ok | ok |
| MathQA | acc_norm | losowa 0,2000, większościowa 0,2265 | 0,2281 ± 0,0077 | ok | ok |
| MedMCQA | acc | losowa 0,2500, większościowa 0,3223 | 0,3122 ± 0,0072 | ok | ok |
| MultiBLiMP-PL | acc | losowa 0,5000 | 0,9875 ± 0,0019 | ok | ok |
| PIQA | acc_norm | losowa 0,5000, większościowa 0,5049 | 0,6621 ± 0,0110 | ok | ok |
| PubMedQA | acc | losowa 0,3333, większościowa 0,5520 | 0,4340 ± 0,0222 | ok | ok |
| Social IQa | acc | losowa 0,3333, większościowa 0,3362 | 0,3966 ± 0,0111 | ok | ok |
| WikiText-2 | byte_perplexity | nie dotyczy | 1,780 ± 0,0149 | ok | ok |
| WinoGrande | acc | losowa 0,5000, większościowa 0,5043 | 0,5367 ± 0,0127 | ok | ok |
| WSC273 | acc | losowa 0,5000, większościowa 0,5018 | 0,6154 ± 0,0221 | ok | ok |

## Analizy eksploracyjne (po wyniku)

Dopisane po pierwszym wyniku, na żądanie weryfikacji; nie były ustalone w protokole i nie zmieniają głównego twierdzenia ani werdyktów tabeli. Werdykty niżej są opisowe, bez korekty na wielokrotne testowanie, chyba że kolumna mówi inaczej. Ustalone przed pomiarem było tylko to, co stoi w sekcjach wyżej.

### Remisy

Reguła (stan runnera, zapisany po wyniku w aneksie protokołu): argmax z pierwszym indeksem (metryki.argmax runnera); EWoK: remis T1 = T2 liczony jako brak wyboru (ewok.evaluate). Remis to pytanie, w którym najwyższy wynik reguły wyboru ma więcej niż jedna opcja; „z poprawną” to remis obejmujący poprawną opcję (liczony jako trafienie, gdy poprawna ma najniższy indeks).

| test | n | remisy 1.09 | z poprawną 1.09 | remisy 1.08 | z poprawną 1.08 | pytania ze zdublowaną opcją |
|---|---:|---:|---:|---:|---:|---:|
| ARC-Challenge | 1172 | 0 | 0 | 0 | 0 | 0 |
| ARC-Easy | 2376 | 0 | 0 | 0 | 0 | 0 |
| BLiMP | 67000 | 7 | 7 | 7 | 7 | 7 |
| EWoK | 4374 | 0 | – | 0 | – | – |
| HellaSwag | 10042 | 0 | 0 | 0 | 0 | 0 |
| MathQA | 2985 | 13 | 4 | 13 | 5 | 49 |
| MedMCQA | 4183 | 0 | 0 | 0 | 0 | 0 |
| MultiBLiMP-PL | 3272 | 0 | 0 | 0 | 0 | 0 |
| PIQA | 1838 | 0 | 0 | 0 | 0 | 0 |
| PubMedQA | 500 | 0 | 0 | 0 | 0 | 0 |
| Social IQa | 1954 | 2 | 0 | 2 | 0 | 5 |
| WinoGrande | 1267 | 0 | 0 | 0 | 0 | 0 |
| WSC273 | 273 | 0 | 0 | 0 | 0 | 0 |

### ARC-Challenge: dwie definicje acc_norm

Runner (`metryki.oceny_mc`, definicja pełnego przebiegu i manifestu 1.08) dzieli loglik przez długość kontynuacji bez wiodących spacji; lm_eval (pole próbki) przez długość wyboru. Na ARC-Challenge rozchodzą się na 0 pytaniach 1.09 i 0 pytaniach 1.08.

| definicja | 1.08 | 1.09 k40000 | Δ | SE Δ | statystyka | werdykt |
|---|---:|---:|---:|---:|---|---|
| runner (tabela wyżej) | 0,300341 | 0,349829 | +0,049488 | 0,0116 | z = 4,26 | pewne |
| lm_eval | 0,300341 | 0,349829 | +0,049488 | 0,0116 | z = 4,26 | pewne |

Werdykt po Holmie w definicji lm_eval (pełny Holm w rodzinie 15 porównań protokołu, z tym p w miejscu p runnera): pewne (p Holma 0,0002); w definicji runnera pewne (p Holma 0,0002). Wynik testu się nie zmienia.

### HellaSwag: dwie definicje acc_norm

Runner (`metryki.oceny_mc`, definicja pełnego przebiegu i manifestu 1.08) dzieli loglik przez długość kontynuacji bez wiodących spacji; lm_eval (pole próbki) przez długość wyboru. Na HellaSwag rozchodzą się na 23 pytaniach 1.09 i 23 pytaniach 1.08.

| definicja | 1.08 | 1.09 k40000 | Δ | SE Δ | statystyka | werdykt |
|---|---:|---:|---:|---:|---|---|
| runner (tabela wyżej) | 0,434077 | 0,527982 | +0,093906 | 0,0036 | z = 26,25 | pewne |
| lm_eval | 0,433977 | 0,528082 | +0,094105 | 0,0036 | z = 26,23 | pewne |

Werdykt po Holmie w definicji lm_eval (pełny Holm w rodzinie 15 porównań protokołu, z tym p w miejscu p runnera): pewne (p Holma 0,0000); w definicji runnera pewne (p Holma 0,0000). Wynik testu się nie zmienia.

### MathQA: dwie definicje acc_norm

Runner (`metryki.oceny_mc`, definicja pełnego przebiegu i manifestu 1.08) dzieli loglik przez długość kontynuacji bez wiodących spacji; lm_eval (pole próbki) przez długość wyboru. Na MathQA rozchodzą się na 0 pytaniach 1.09 i 0 pytaniach 1.08.

| definicja | 1.08 | 1.09 k40000 | Δ | SE Δ | statystyka | werdykt |
|---|---:|---:|---:|---:|---|---|
| runner (tabela wyżej) | 0,228141 | 0,225126 | −0,003015 | 0,0069 | z = −0,44 | szum |
| lm_eval | 0,228141 | 0,225126 | −0,003015 | 0,0069 | z = −0,44 | szum |

Werdykt po Holmie w definicji lm_eval (pełny Holm w rodzinie 15 porównań protokołu, z tym p w miejscu p runnera): szum (p Holma 1,0000); w definicji runnera szum (p Holma 1,0000). Wynik testu się nie zmienia.

### PIQA: dwie definicje acc_norm

Runner (`metryki.oceny_mc`, definicja pełnego przebiegu i manifestu 1.08) dzieli loglik przez długość kontynuacji bez wiodących spacji; lm_eval (pole próbki) przez długość wyboru. Na PIQA rozchodzą się na 0 pytaniach 1.09 i 0 pytaniach 1.08.

| definicja | 1.08 | 1.09 k40000 | Δ | SE Δ | statystyka | werdykt |
|---|---:|---:|---:|---:|---|---|
| runner (tabela wyżej) | 0,662133 | 0,712187 | +0,050054 | 0,0084 | z = 5,94 | pewne |
| lm_eval | 0,662133 | 0,712187 | +0,050054 | 0,0084 | z = 5,94 | pewne |

Werdykt po Holmie w definicji lm_eval (pełny Holm w rodzinie 15 porównań protokołu, z tym p w miejscu p runnera): pewne (p Holma 0,0000); w definicji runnera pewne (p Holma 0,0000). Wynik testu się nie zmienia.

### Rozbicie zadań złożonych

Wartość grupy z przedziałem Walda ±1,96 SE przyciętym do [0; 1]; Δ parowane (z), Holm w obrębie rozbicia (m = liczba grup). SE każdej grupy liczone z pozycji traktowanych jako niezależne (pary BLiMP i MultiBLiMP-PL, rekordy EWoK), bez klastrów: w EWoK rekordy jednego szablonu są skorelowane, a porównanie główne liczy SE po szablonach, więc tu SE jest zaniżone, a werdykty grup za mocne. <!-- liczba-spoza-wynikow: 1,96 to kwantyl rozkładu normalnego, nie wynik -->

<details>
<summary><b>BLiMP</b> po polu `UID`, k = 67 (po Holmie pewne: 15, prawdopodobne: 5, szum: 47)</summary>

| grupa | n | 1.08 [CI95] | 1.09 k40000 [CI95] | Δ | SE Δ | z | werdykt | p Holma | po Holmie |
|---|---:|---:|---:|---:|---:|---|---|---:|---|
| adjunct_island | 1000 | 0,8560 [0,8342; 0,8778] | 0,8750 [0,8545; 0,8955] | +0,0190 | 0,0119 | z = 1,59 | szum | 1,0000 | nie (szum) |
| anaphor_gender_agreement | 1000 | 0,9860 [0,9787; 0,9933] | 0,9740 [0,9641; 0,9839] | −0,0120 | 0,0042 | z = −2,84 | prawdopodobne | 0,1950 | nie (szum) |
| anaphor_number_agreement | 1000 | 0,9940 [0,9892; 0,9988] | 0,9940 [0,9892; 0,9988] | 0,0000 | 0,0020 | z = 0,00 | szum | 1,0000 | nie (szum) |
| animate_subject_passive | 1000 | 0,7540 [0,7273; 0,7807] | 0,7690 [0,7429; 0,7951] | +0,0150 | 0,0110 | z = 1,36 | szum | 1,0000 | nie (szum) |
| animate_subject_trans | 1000 | 0,8100 [0,7857; 0,8343] | 0,8480 [0,8257; 0,8703] | +0,0380 | 0,0108 | z = 3,52 | pewne | 0,0222 | tak (prawdopodobne) |
| causative | 1000 | 0,7480 [0,7211; 0,7749] | 0,7490 [0,7221; 0,7759] | +0,0010 | 0,0140 | z = 0,07 | szum | 1,0000 | nie (szum) |
| complex_NP_island | 1000 | 0,5470 [0,5161; 0,5779] | 0,5620 [0,5312; 0,5928] | +0,0150 | 0,0172 | z = 0,87 | szum | 1,0000 | nie (szum) |
| coordinate_structure_constraint_complex_left_branch | 1000 | 0,7680 [0,7418; 0,7942] | 0,7280 [0,7004; 0,7556] | −0,0400 | 0,0131 | z = −3,06 | pewne | 0,1028 | nie (szum) |
| coordinate_structure_constraint_object_extraction | 1000 | 0,8220 [0,7983; 0,8457] | 0,8260 [0,8025; 0,8495] | +0,0040 | 0,0108 | z = 0,37 | szum | 1,0000 | nie (szum) |
| determiner_noun_agreement_1 | 1000 | 0,9810 [0,9725; 0,9895] | 0,9930 [0,9878; 0,9982] | +0,0120 | 0,0040 | z = 3,01 | pewne | 0,1142 | nie (szum) |
| determiner_noun_agreement_2 | 1000 | 0,9770 [0,9677; 0,9863] | 0,9780 [0,9689; 0,9871] | +0,0010 | 0,0062 | z = 0,16 | szum | 1,0000 | nie (szum) |
| determiner_noun_agreement_irregular_1 | 1000 | 0,9430 [0,9286; 0,9574] | 0,9240 [0,9076; 0,9404] | −0,0190 | 0,0074 | z = −2,57 | prawdopodobne | 0,4078 | nie (szum) |
| determiner_noun_agreement_irregular_2 | 1000 | 0,9510 [0,9376; 0,9644] | 0,9450 [0,9309; 0,9591] | −0,0060 | 0,0080 | z = −0,75 | szum | 1,0000 | nie (szum) |
| determiner_noun_agreement_with_adj_2 | 1000 | 0,9330 [0,9175; 0,9485] | 0,9480 [0,9342; 0,9618] | +0,0150 | 0,0078 | z = 1,92 | szum | 1,0000 | nie (szum) |
| determiner_noun_agreement_with_adj_irregular_1 | 1000 | 0,9130 [0,8955; 0,9305] | 0,9280 [0,9120; 0,9440] | +0,0150 | 0,0084 | z = 1,78 | szum | 1,0000 | nie (szum) |
| determiner_noun_agreement_with_adj_irregular_2 | 1000 | 0,9250 [0,9087; 0,9413] | 0,9180 [0,9010; 0,9350] | −0,0070 | 0,0088 | z = −0,80 | szum | 1,0000 | nie (szum) |
| determiner_noun_agreement_with_adjective_1 | 1000 | 0,9510 [0,9376; 0,9644] | 0,9750 [0,9653; 0,9847] | +0,0240 | 0,0061 | z = 3,92 | pewne | 0,0046 | tak (prawdopodobne) |
| distractor_agreement_relational_noun | 1000 | 0,8590 [0,8374; 0,8806] | 0,8490 [0,8268; 0,8712] | −0,0100 | 0,0127 | z = −0,79 | szum | 1,0000 | nie (szum) |
| distractor_agreement_relative_clause | 1000 | 0,7490 [0,7221; 0,7759] | 0,7430 [0,7159; 0,7701] | −0,0060 | 0,0154 | z = −0,39 | szum | 1,0000 | nie (szum) |
| drop_argument | 1000 | 0,7750 [0,7491; 0,8009] | 0,7720 [0,7460; 0,7980] | −0,0030 | 0,0120 | z = −0,25 | szum | 1,0000 | nie (szum) |
| ellipsis_n_bar_1 | 1000 | 0,8370 [0,8141; 0,8599] | 0,8780 [0,8577; 0,8983] | +0,0410 | 0,0121 | z = 3,40 | pewne | 0,0338 | tak (prawdopodobne) |
| ellipsis_n_bar_2 | 1000 | 0,9000 [0,8814; 0,9186] | 0,9070 [0,8890; 0,9250] | +0,0070 | 0,0094 | z = 0,74 | szum | 1,0000 | nie (szum) |
| existential_there_object_raising | 1000 | 0,8410 [0,8183; 0,8637] | 0,8930 [0,8738; 0,9122] | +0,0520 | 0,0114 | z = 4,57 | pewne | 0,0003 | tak (pewne) |
| existential_there_quantifiers_1 | 1000 | 0,9630 [0,9513; 0,9747] | 0,9840 [0,9762; 0,9918] | +0,0210 | 0,0048 | z = 4,42 | pewne | 0,0005 | tak (pewne) |
| existential_there_quantifiers_2 | 1000 | 0,2040 [0,1790; 0,2290] | 0,1690 [0,1458; 0,1922] | −0,0350 | 0,0157 | z = −2,23 | prawdopodobne | 0,9492 | nie (szum) |
| existential_there_subject_raising | 1000 | 0,8610 [0,8395; 0,8825] | 0,8660 [0,8449; 0,8871] | +0,0050 | 0,0096 | z = 0,52 | szum | 1,0000 | nie (szum) |
| expletive_it_object_raising | 1000 | 0,8080 [0,7836; 0,8324] | 0,8040 [0,7794; 0,8286] | −0,0040 | 0,0111 | z = −0,36 | szum | 1,0000 | nie (szum) |
| inchoative | 1000 | 0,6910 [0,6623; 0,7197] | 0,6880 [0,6593; 0,7167] | −0,0030 | 0,0136 | z = −0,22 | szum | 1,0000 | nie (szum) |
| intransitive | 1000 | 0,7940 [0,7689; 0,8191] | 0,8040 [0,7794; 0,8286] | +0,0100 | 0,0116 | z = 0,86 | szum | 1,0000 | nie (szum) |
| irregular_past_participle_adjectives | 1000 | 0,9080 [0,8901; 0,9259] | 0,9790 [0,9701; 0,9879] | +0,0710 | 0,0096 | z = 7,40 | pewne | 0,0000 | tak (pewne) |
| irregular_past_participle_verbs | 1000 | 0,8150 [0,7909; 0,8391] | 0,8700 [0,8491; 0,8909] | +0,0550 | 0,0119 | z = 4,61 | pewne | 0,0002 | tak (pewne) |
| irregular_plural_subject_verb_agreement_1 | 1000 | 0,9090 [0,8912; 0,9268] | 0,9200 [0,9032; 0,9368] | +0,0110 | 0,0093 | z = 1,18 | szum | 1,0000 | nie (szum) |
| irregular_plural_subject_verb_agreement_2 | 1000 | 0,9100 [0,8923; 0,9277] | 0,9240 [0,9076; 0,9404] | +0,0140 | 0,0092 | z = 1,53 | szum | 1,0000 | nie (szum) |
| left_branch_island_echo_question | 1000 | 0,4230 [0,3924; 0,4536] | 0,4970 [0,4660; 0,5280] | +0,0740 | 0,0160 | z = 4,62 | pewne | 0,0002 | tak (pewne) |
| left_branch_island_simple_question | 1000 | 0,8160 [0,7920; 0,8400] | 0,8150 [0,7909; 0,8391] | −0,0010 | 0,0137 | z = −0,07 | szum | 1,0000 | nie (szum) |
| matrix_question_npi_licensor_present | 1000 | 0,5590 [0,5282; 0,5898] | 0,5380 [0,5071; 0,5689] | −0,0210 | 0,0153 | z = −1,37 | szum | 1,0000 | nie (szum) |
| npi_present_1 | 1000 | 0,6710 [0,6419; 0,7001] | 0,6780 [0,6490; 0,7070] | +0,0070 | 0,0144 | z = 0,49 | szum | 1,0000 | nie (szum) |
| npi_present_2 | 1000 | 0,6290 [0,5990; 0,6590] | 0,6950 [0,6664; 0,7236] | +0,0660 | 0,0150 | z = 4,41 | pewne | 0,0005 | tak (pewne) |
| only_npi_licensor_present | 1000 | 0,9860 [0,9787; 0,9933] | 0,9400 [0,9253; 0,9547] | −0,0460 | 0,0080 | z = −5,75 | pewne | 0,0000 | tak (pewne) |
| only_npi_scope | 1000 | 0,8770 [0,8566; 0,8974] | 0,8140 [0,7899; 0,8381] | −0,0630 | 0,0133 | z = −4,73 | pewne | 0,0001 | tak (pewne) |
| passive_1 | 1000 | 0,8920 [0,8728; 0,9112] | 0,9100 [0,8923; 0,9277] | +0,0180 | 0,0099 | z = 1,82 | szum | 1,0000 | nie (szum) |
| passive_2 | 1000 | 0,8900 [0,8706; 0,9094] | 0,8990 [0,8803; 0,9177] | +0,0090 | 0,0096 | z = 0,93 | szum | 1,0000 | nie (szum) |
| principle_A_c_command | 1000 | 0,7330 [0,7056; 0,7604] | 0,6890 [0,6603; 0,7177] | −0,0440 | 0,0130 | z = −3,37 | pewne | 0,0365 | tak (prawdopodobne) |
| principle_A_case_1 | 1000 | 0,9980 [0,9952; 1,0000] | 1,0000 [1,0000; 1,0000] | +0,0020 | 0,0014 | z = 1,41 | szum | 1,0000 | nie (szum) |
| principle_A_case_2 | 1000 | 0,9390 [0,9242; 0,9538] | 0,9490 [0,9354; 0,9626] | +0,0100 | 0,0087 | z = 1,15 | szum | 1,0000 | nie (szum) |
| principle_A_domain_1 | 1000 | 0,9860 [0,9787; 0,9933] | 0,9870 [0,9800; 0,9940] | +0,0010 | 0,0039 | z = 0,26 | szum | 1,0000 | nie (szum) |
| principle_A_domain_2 | 1000 | 0,7720 [0,7460; 0,7980] | 0,8060 [0,7815; 0,8305] | +0,0340 | 0,0130 | z = 2,62 | prawdopodobne | 0,3655 | nie (szum) |
| principle_A_domain_3 | 1000 | 0,5930 [0,5625; 0,6235] | 0,6360 [0,6062; 0,6658] | +0,0430 | 0,0183 | z = 2,35 | prawdopodobne | 0,7368 | nie (szum) |
| principle_A_reconstruction | 1000 | 0,3480 [0,3185; 0,3775] | 0,4580 [0,4271; 0,4889] | +0,1100 | 0,0154 | z = 7,16 | pewne | 0,0000 | tak (pewne) |
| regular_plural_subject_verb_agreement_1 | 1000 | 0,8860 [0,8663; 0,9057] | 0,9440 [0,9297; 0,9583] | +0,0580 | 0,0096 | z = 6,02 | pewne | 0,0000 | tak (pewne) |
| regular_plural_subject_verb_agreement_2 | 1000 | 0,8970 [0,8782; 0,9158] | 0,9270 [0,9109; 0,9431] | +0,0300 | 0,0090 | z = 3,33 | pewne | 0,0417 | tak (prawdopodobne) |
| sentential_negation_npi_licensor_present | 1000 | 0,9770 [0,9677; 0,9863] | 0,9850 [0,9775; 0,9925] | +0,0080 | 0,0049 | z = 1,63 | szum | 1,0000 | nie (szum) |
| sentential_negation_npi_scope | 1000 | 0,6760 [0,6470; 0,7050] | 0,7770 [0,7512; 0,8028] | +0,1010 | 0,0150 | z = 6,73 | pewne | 0,0000 | tak (pewne) |
| sentential_subject_island | 1000 | 0,5860 [0,5555; 0,6165] | 0,4640 [0,4331; 0,4949] | −0,1220 | 0,0183 | z = −6,68 | pewne | 0,0000 | tak (pewne) |
| superlative_quantifiers_1 | 1000 | 0,6770 [0,6480; 0,7060] | 0,8590 [0,8374; 0,8806] | +0,1820 | 0,0170 | z = 10,70 | pewne | 0,0000 | tak (pewne) |
| superlative_quantifiers_2 | 1000 | 0,9200 [0,9032; 0,9368] | 0,9210 [0,9043; 0,9377] | +0,0010 | 0,0101 | z = 0,10 | szum | 1,0000 | nie (szum) |
| tough_vs_raising_1 | 1000 | 0,6630 [0,6337; 0,6923] | 0,6260 [0,5960; 0,6560] | −0,0370 | 0,0122 | z = −3,02 | pewne | 0,1125 | nie (szum) |
| tough_vs_raising_2 | 1000 | 0,8950 [0,8760; 0,9140] | 0,8960 [0,8771; 0,9149] | +0,0010 | 0,0098 | z = 0,10 | szum | 1,0000 | nie (szum) |
| transitive | 1000 | 0,8370 [0,8141; 0,8599] | 0,8690 [0,8481; 0,8899] | +0,0320 | 0,0119 | z = 2,69 | prawdopodobne | 0,2967 | nie (szum) |
| wh_island | 1000 | 0,7880 [0,7627; 0,8133] | 0,6980 [0,6695; 0,7265] | −0,0900 | 0,0150 | z = −5,99 | pewne | 0,0000 | tak (pewne) |
| wh_questions_object_gap | 1000 | 0,8110 [0,7867; 0,8353] | 0,8370 [0,8141; 0,8599] | +0,0260 | 0,0129 | z = 2,01 | prawdopodobne | 1,0000 | nie (szum) |
| wh_questions_subject_gap | 1000 | 0,8960 [0,8771; 0,9149] | 0,9290 [0,9131; 0,9449] | +0,0330 | 0,0108 | z = 3,06 | pewne | 0,1028 | nie (szum) |
| wh_questions_subject_gap_long_distance | 1000 | 0,8560 [0,8342; 0,8778] | 0,8760 [0,8556; 0,8964] | +0,0200 | 0,0126 | z = 1,59 | szum | 1,0000 | nie (szum) |
| wh_vs_that_no_gap | 1000 | 0,9720 [0,9618; 0,9822] | 0,9600 [0,9478; 0,9722] | −0,0120 | 0,0058 | z = −2,06 | prawdopodobne | 1,0000 | nie (szum) |
| wh_vs_that_no_gap_long_distance | 1000 | 0,9720 [0,9618; 0,9822] | 0,9590 [0,9467; 0,9713] | −0,0130 | 0,0070 | z = −1,86 | szum | 1,0000 | nie (szum) |
| wh_vs_that_with_gap | 1000 | 0,5250 [0,4940; 0,5560] | 0,4490 [0,4182; 0,4798] | −0,0760 | 0,0151 | z = −5,03 | pewne | 0,0000 | tak (pewne) |
| wh_vs_that_with_gap_long_distance | 1000 | 0,2880 [0,2599; 0,3161] | 0,3210 [0,2920; 0,3500] | +0,0330 | 0,0142 | z = 2,32 | prawdopodobne | 0,7704 | nie (szum) |

</details>

<details>
<summary><b>EWoK</b> po polu `Domain`, k = 11 (po Holmie pewne: 2, szum: 9)</summary>

| grupa | n | 1.08 [CI95] | 1.09 k40000 [CI95] | Δ | SE Δ | z | werdykt | p Holma | po Holmie |
|---|---:|---:|---:|---:|---:|---|---|---:|---|
| agent-properties | 1120 | 0,5379 [0,5210; 0,5549] | 0,5795 [0,5629; 0,5960] | +0,0415 | 0,0102 | z = 4,08 | pewne | 0,0005 | tak (pewne) |
| material-dynamics | 780 | 0,6936 [0,6740; 0,7132] | 0,7231 [0,7043; 0,7418] | +0,0295 | 0,0121 | z = 2,44 | prawdopodobne | 0,1326 | nie (szum) |
| material-properties | 124 | 0,5524 [0,5191; 0,5857] | 0,5444 [0,5088; 0,5799] | −0,0081 | 0,0222 | z = −0,36 | szum | 1,0000 | nie (szum) |
| physical-dynamics | 75 | 0,6400 [0,5856; 0,6944] | 0,6267 [0,5676; 0,6858] | −0,0133 | 0,0355 | z = −0,38 | szum | 1,0000 | nie (szum) |
| physical-interactions | 280 | 0,5500 [0,5169; 0,5831] | 0,5964 [0,5636; 0,6292] | +0,0464 | 0,0199 | z = 2,33 | prawdopodobne | 0,1370 | nie (szum) |
| physical-relations | 415 | 0,5470 [0,5152; 0,5788] | 0,5494 [0,5198; 0,5790] | +0,0024 | 0,0180 | z = 0,13 | szum | 1,0000 | nie (szum) |
| quantitative-properties | 190 | 0,6605 [0,6168; 0,7042] | 0,6711 [0,6307; 0,7114] | +0,0105 | 0,0197 | z = 0,53 | szum | 1,0000 | nie (szum) |
| social-interactions | 175 | 0,6943 [0,6540; 0,7346] | 0,8000 [0,7636; 0,8364] | +0,1057 | 0,0197 | z = 5,37 | pewne | 0,0000 | tak (pewne) |
| social-properties | 185 | 0,6946 [0,6528; 0,7364] | 0,7027 [0,6562; 0,7492] | +0,0081 | 0,0228 | z = 0,36 | szum | 1,0000 | nie (szum) |
| social-relations | 785 | 0,5847 [0,5627; 0,6067] | 0,6000 [0,5800; 0,6200] | +0,0153 | 0,0125 | z = 1,22 | szum | 1,0000 | nie (szum) |
| spatial-relations | 245 | 0,5898 [0,5420; 0,6376] | 0,6327 [0,5843; 0,6810] | +0,0429 | 0,0177 | z = 2,42 | prawdopodobne | 0,1326 | nie (szum) |

</details>

<details>
<summary><b>MultiBLiMP-PL</b> po polu `phenomenon`, k = 3 (po Holmie szum: 3)</summary>

| grupa | n | 1.08 [CI95] | 1.09 k40000 [CI95] | Δ | SE Δ | z | werdykt | p Holma | po Holmie |
|---|---:|---:|---:|---:|---:|---|---|---:|---|
| SV-# | 736 | 0,9769 [0,9660; 0,9878] | 0,9796 [0,9694; 0,9898] | +0,0027 | 0,0054 | z = 0,50 | szum | 1,0000 | nie (szum) |
| SV-G | 1216 | 0,9893 [0,9835; 0,9951] | 0,9877 [0,9815; 0,9939] | −0,0016 | 0,0039 | z = −0,43 | szum | 1,0000 | nie (szum) |
| SV-P | 1320 | 0,9917 [0,9868; 0,9966] | 0,9871 [0,9810; 0,9932] | −0,0045 | 0,0034 | z = −1,34 | szum | 0,5387 | nie (szum) |

</details>

### Formaty odpowiedzi i rozkład wyborów

Każdy plik próbek testu (space: format pełnego przebiegu; mc: litera; cloze: treść odpowiedzi). BPB poprawnej odpowiedzi: niżej = lepiej. Wybory według metryki testu, obok rozkład poprawnych pozycji. SE Δ w tej tabeli jest parowane po pozycjach bez klastrów, więc dla BLiMP, WinoGrande i WSC273 (protokół: SE po klastrach) werdykt tu jest za mocny i nie zastępuje tabeli protokołu.

| test | wariant | n | acc 1.08 · 1.09 | acc_norm 1.08 · 1.09 | BPB poprawnej 1.08 · 1.09 | Δ acc (z, werdykt) | Δ acc_norm (z, werdykt) |
|---|---|---:|---:|---:|---:|---|---|
| ARC-Challenge | mc | 1172 | 0,2304 · 0,2415 | 0,2304 · 0,2415 | 1,9325 · 1,3240 | +0,0111 (z = 0,71, szum) | +0,0111 (z = 0,71, szum) |
| ARC-Challenge | space | 1172 | 0,2713 · 0,3276 | 0,3003 · 0,3498 | 1,3230 · 1,1284 | +0,0563 (z = 4,78, pewne) | +0,0495 (z = 4,26, pewne) |
| ARC-Easy | space | 2376 | 0,5838 · 0,6662 | 0,5189 · 0,6166 | 1,3025 · 1,0458 | +0,0825 (z = 9,26, pewne) | +0,0976 (z = 11,27, pewne) |
| BLiMP | space | 67000 | 0,8047 · 0,8148 | 0,7479 · 0,7640 | 2,3040 · 2,2726 | +0,0101 (z = 7,08, pewne) | +0,0161 (z = 11,49, pewne) |
| HellaSwag | space | 10042 | 0,3509 · 0,4173 | 0,4341 · 0,5280 | 0,8979 · 0,8339 | +0,0664 (z = 22,66, pewne) | +0,0939 (z = 26,25, pewne) |
| MathQA | space | 2985 | 0,2338 · 0,2328 | 0,2281 · 0,2251 | 3,3023 · 2,7470 | −0,0010 (z = −0,14, szum) | −0,0030 (z = −0,44, szum) |
| MedMCQA | cloze | 4183 | 0,2269 · 0,2515 | 0,2761 · 0,2871 | 1,6779 · 1,4557 | +0,0246 (z = 4,22, pewne) | +0,0110 (z = 1,86, szum) |
| MedMCQA | space | 4183 | 0,3122 · 0,3005 | 0,3122 · 0,3005 | 2,0468 · 1,4928 | −0,0117 (z = −2,25, prawdopodobne) | −0,0117 (z = −2,25, prawdopodobne) |
| MultiBLiMP-PL | space | 3272 | 0,9875 · 0,9856 | 0,9762 · 0,9685 | 1,4625 · 1,4965 | −0,0018 (z = −0,79, szum) | −0,0076 (z = −2,54, prawdopodobne) |
| PIQA | space | 1838 | 0,6817 · 0,7046 | 0,6621 · 0,7122 | 1,2166 · 1,1173 | +0,0229 (z = 2,93, prawdopodobne) | +0,0501 (z = 5,94, pewne) |
| PubMedQA | space | 500 | 0,4340 · 0,5620 | 0,2320 · 0,3300 | 3,6863 · 3,6474 | +0,1280 (z = 5,89, pewne) | +0,0980 (z = 4,80, pewne) |
| Social IQa | space | 1954 | 0,3966 · 0,4089 | 0,4299 · 0,4345 | 1,8624 · 1,7456 | +0,0123 (z = 1,68, szum) | +0,0046 (z = 0,68, szum) |
| WinoGrande | space | 1267 | 0,5367 · 0,5770 | 0,5367 · 0,5770 | 1,2671 · 1,2171 | +0,0403 (z = 2,61, prawdopodobne) | +0,0403 (z = 2,61, prawdopodobne) |
| WSC273 | space | 273 | 0,6154 · 0,6374 | 0,6154 · 0,6374 | 2,2749 · 2,5647 | +0,0220 (z = 0,68, szum) | +0,0220 (z = 0,68, szum) |

| test | wariant | poprawne pozycje | wybrane 1.08 | wybrane 1.09 k40000 |
|---|---|---|---|---|
| ARC-Challenge | mc | A:266 B:311 C:310 D:285 | A:1112 B:50 C:6 D:4 | A:406 B:377 C:342 D:47 |
| ARC-Challenge | space | A:266 B:311 C:310 D:285 | A:260 B:276 C:279 D:356 E:1 | A:260 B:289 C:294 D:327 E:2 |
| ARC-Easy | space | A:596 B:585 C:633 D:561 E:1 | A:781 B:599 C:519 D:476 E:1 | A:766 B:605 C:530 D:475 |
| BLiMP | space | A:67000 | A:53917 B:13083 | A:54592 B:12408 |
| HellaSwag | space | A:2515 B:2485 C:2584 D:2458 | A:2546 B:2466 C:2507 D:2523 | A:2533 B:2449 C:2546 D:2514 |
| MathQA | space | A:614 B:605 C:676 D:628 E:462 | A:710 B:568 C:516 D:521 E:670 | A:709 B:578 C:535 D:505 E:658 |
| MedMCQA | cloze | A:1348 B:1085 C:925 D:825 | A:1183 B:962 C:924 D:1114 | A:1238 B:948 C:923 D:1074 |
| MedMCQA | space | A:1348 B:1085 C:925 D:825 | A:3988 B:118 C:39 D:38 | A:3288 B:175 C:440 D:280 |
| MultiBLiMP-PL | space | A:3272 | A:3231 B:41 | A:3225 B:47 |
| PIQA | space | A:910 B:928 | A:913 B:925 | A:903 B:935 |
| PubMedQA | space | A:276 B:169 C:55 | A:133 B:367 | A:214 B:286 |
| Social IQa | space | A:643 B:654 C:657 | A:650 B:652 C:652 | A:641 B:655 C:658 |
| WinoGrande | space | A:628 B:639 | A:633 B:634 | A:628 B:639 |
| WSC273 | space | A:137 B:136 | A:142 B:131 | A:138 B:135 |

### Wobec bazy (stała odpowiedź albo losowa)

`wobec_b` z plików wyników runnera: b = wyższa z bazy losowej i stałej odpowiedzi; przy stałej odpowiedzi porównanie parowane z jej wynikami per pytanie.

| test | b | baza | 1.08 − b (statystyka, werdykt) | 1.09 − b (statystyka, werdykt) |
|---|---:|---|---|---|
| ARC-Challenge | 0,2654 | stala odpowiedz | +0,0350 (z = 1,84, szum) | +0,0845 (z = 4,38, pewne) |
| ARC-Easy | 0,2664 | stala odpowiedz | +0,3173 (z = 22,72, pewne) | +0,3998 (z = 29,17, pewne) |
| BLiMP | 0,5000 | losowa | +0,3047 (t = 14,33, df = 66, pewne) | +0,3148 (t = 14,69, df = 66, pewne) |
| HellaSwag | 0,2573 | stala odpowiedz | +0,1768 (z = 26,76, pewne) | +0,2707 (z = 41,04, pewne) |
| MathQA | 0,2265 | stala odpowiedz | +0,0017 (z = 0,15, szum) | −0,0013 (z = −0,12, szum) |
| MedMCQA | 0,3223 | stala odpowiedz | −0,0100 (z = −3,78, pewne) | −0,0218 (z = −4,18, pewne) |
| MultiBLiMP-PL | 0,5000 | losowa | +0,4875 (z = 250,63, pewne) | +0,4856 (z = 233,43, pewne) |
| PIQA | 0,5049 | stala odpowiedz | +0,1572 (z = 9,81, pewne) | +0,2073 (z = 13,27, pewne) |
| PubMedQA | 0,5520 | stala odpowiedz | −0,1180 (z = −3,26, pewne) | +0,0100 (z = 0,31, szum) |
| Social IQa | 0,3362 | stala odpowiedz | +0,0604 (z = 3,94, pewne) | +0,0727 (z = 4,71, pewne) |
| WinoGrande | 0,5043 | stala odpowiedz | +0,0324 (t = 1,97, df = 982, szum) | +0,0726 (t = 4,38, df = 982, pewne) |
| WSC273 | 0,5018 | stala odpowiedz | +0,1136 (t = 5,14, df = 134, pewne) | +0,1355 (t = 5,61, df = 134, pewne) |

### Wrażliwość werdyktów „prawdopodobne” po Holmie

- WinoGrande: p Holma 0,0437 przy progu 0,0455. Zamiana 1 wygranej 1.09 na remis (najbardziej wpływowej) daje werdykt szum. Test McNemara na pozycjach (wygrane 1.09: 218, wygrane 1.08: 167): p 0,0107, po Holmie w rodzinie protokołu (to p w miejscu p testu) 0,0751, czyli szum. Werdykt protokołu (SE po parach zdań) zostaje, ale jest na granicy progu.

## Środowisko

- batch: 1
- commit_kodu: b99f72a (deklaracja: git archive bez .git, srodowisko.json eksportu bez commitu; dowody pośrednie w odstępstwach)
- cuda: 12.9
- datasets: 3.6.0
- gpu_nvidia_smi: NVIDIA GeForce RTX 5090, 32607 MiB, 580.95.05
- karta: RTX 5090 (vast.ai)
- lm_eval: 0.4.9.1
- platforma: Linux-5.15.0-191-generic-x86_64-with-glibc2.35
- precyzja: float32, TF32 wyłączony
- python: 3.11.13
- seed: domyślny ewaluuj.py i ewok.py
- torch: 2.8.0+cu129
- transformers: 4.57.6

## Odstępstwa od protokołu

- Commit kodu na instancji jest deklaracją, nie zapisem: srodowisko.json eksportu ma puste pole fabryka_commit, a logi instancji mówią „not a git repository”, bo kod przyszedł jako git archive bez katalogu .git. Deklarowany commit to b99f72a (komenda git archive w zapisie sesji pomiaru). Dowody pośrednie: runner_sha256 w eksporcie to suma research/common commitu b99f72a (ta sama w 88719f1), a suma wag po konwersji to wpis 1.09 w SUMY_WAG_CKPT dodany w b99f72a, z którym runner odmawia innych wag. Odstępstwo przepuszczone decyzją Ani 14.11.2026.
- Protokół wskazał jako dowód niezmienionego runnera pole runner_sha256 manifestu, a to pole się różni od pełnego przebiegu: jest sumą całego katalogu research/common, nie samego ewaluuj.py. ewaluuj.py jest bajt w bajt ten sam; jedyna zmiana w research/common między przebiegiem (51c5e31) a pomiarem to klastry testu T27 (PSC) w zadania.py, spoza 15 testów. Wpływ na wynik: brak; 1.08 przeliczone ma te same sumy results_sha256 co pełny przebieg na 15 z 15 testów i te same sumy każdego pliku próbek i trace (19 z 19). Odstępstwo przepuszczone decyzją Ani 14.11.2026.
- Kod analizy liczby_109.py (funkcja zbuduj), raport_md.py i przelicz_niezaleznie.py zacommitowany w 88719f1 przed pierwszym wynikiem; tools/ewaluacja/raport.py liczy bez zmian od 88719f1.
- Po wyniku (runda poprawek 1): przelicz_niezaleznie.py liczy acc_norm własnym kodem w definicji runnera i pełnego przebiegu (wcześniej brał pole lm_eval i rozjeżdżał się na HellaSwag), sprawdza sha256 wejść i przelicza remisy; liczby_109.py dopisuje do LICZBY.json analizy eksploracyjne (eksploracja_109.py), bez zmiany zbuduj; raport_md.py dostał sekcje eksploracyjne, problemy i werdykt przy nazwie testu w głównym twierdzeniu; sprawdz_raport.py porównuje raport bajt w bajt z generatorem i sprawdza sekcję 1.09 README. Wcześniej, też po wyniku, bo kod pisany przed pierwszym wynikiem przepadł niezacommitowany: dolacz_wyniki.py, sprawdz_raport.py, mutacje.py. Progi, warianty, metryki i lista porównań bez zmian.
- Regułę remisu (pierwszy indeks przy remisie, jak metryki.argmax runnera; EWoK: remis to brak wyboru) i liczby remisów dopisano po wyniku jako zapis stanu, nie zmianę; liczby w sekcji Remisy.
- Na HellaSwag runner i pełny przebieg liczą acc_norm inaczej niż lm_eval (długość kontynuacji bez wiodących spacji wobec długości wyboru). Tabela protokołu jest w definicji runnera, bo w niej jest manifest 1.08; wartości w definicji lm_eval i ich werdykt stoją w sekcji eksploracyjnej. Werdykt po Holmie jest w obu definicjach ten sam. Odstępstwo przepuszczone decyzją Ani 14.11.2026.
- Start 1.09: TRAINING_CONFIGURATION.md repo SlayerLab/Slayer1B-1.09 @ b25aec4e opisuje porzucony pierwszy start od losowych wag (START=zero, bez --init-from, do kroku 450) i obecny przebieg, który bierze wagi 1.08 @ 5f854a0c przez --init-from z nowym optymalizatorem; osiem checkpointów z samymi wagami (kroki 5 000–40 000) należy do tego przebiegu. Protokół („1.09 startuje z wag 1.08”) zgadza się z tym dokumentem; nazwy pliku wagi_40000.pt dokument nie wymienia.
- Kolejka na instancji liczyła 4 procesy na kartę (aneks), pełny przebieg 2; każdy proces liczy w batch 1, więc liczba procesów nie zmienia wyniku pytania.
- Protokół nie mówi o czasy.jsonl przebiegu: dolacz_wyniki.py dopisuje do niego wiersze ewaluacji 1.09, tak jak do manifest.jsonl; pełne czasy obu etykiet leżą w eksport/czasy.jsonl.

## Problemy poza tym pomiarem

- Runner (research/common/metryki.py, oceny_mc) liczy acc_norm z długością kontynuacji bez wiodących spacji, a jego opis mówi „jak w lm-eval”, które liczy długość wyboru. Na HellaSwag daje to inną wartość w całym pełnym przebiegu 2026-11, nie tylko tutaj; do osobnego zadania (decyzja, którą definicję przyjąć, i przeliczenie przebiegu).
- tests/test_lm_eval_slayer.py::test_ewaluuj_model_id_without_repo jest czerwony na tej gałęzi (AttributeError: Namespace bez atrybutu dtype w ewaluuj.py); poza zakresem tego pomiaru.

## Niepoliczone (NOT RUN)

- Nierozstrzygnięte: przeliczenie niezależne nie sprawdza werdyktu rozbić eksploracyjnych przy tym samym p Holma (mutacja `porownaj_rozbicie` → `if False` przechodzi, 58 passed) — test: zmieniony `werdykt_holm` grupy przy tym samym `p_holm` ma dać kod ≠ 0; zadanie wiedza #4187. Werdykty rozbić przeliczył niezależnie weryfikator liczb (zgodne).
- Ranking z 1.08 jako modelem eksperymentalnym (PR 196) nie jest w tej gałęzi; wykresy rankingów pokazują 1.09 w toku obok ostatniej przyjętej wersji Slayera (1.07), bez 1.08.
- Kontrola na znanym modelu spoza Slayera: protokół jej nie przewiduje; kontrolą narzędzia jest 1.08 przeliczone wobec pełnego przebiegu.

## Pliki

- surowe wyniki: paczka eksportu `eksport_k109.tgz` (sha256 `6da5db6650220f45c19064ba89614ba18ac43f9f6e0c772462fbf29416ec257e`); jej pliki leżą w repo (próbki, trace i podsumowania jako gzip), sumy każdego pliku przed kompresją i po niej w [`probki_sha256.json`](probki_sha256.json) (sha256 `93be9211dcf2e26737b870cb7d620d2d32b40f85777dec2c8e8ad714310068be`)
- `manifest.jsonl` przebiegu: sha256 `ff7df4efcfdd90449fb545f05a1c81dc8ab5761cee003c38d99db5abca7c92ee`
- `wyniki/<test>/slayer1b-1.08/`: 1.08 przeliczone; 1.09 w `../<test>/slayer1b-1.09-k40000/`; `eksport/`: manifest, środowisko i czasy z instancji; `logi/`: logi par
- `code/`: konwersja i sprawdzenie architektury, kolejka na instancji, `dolacz_wyniki.py`, `liczby_109.py`, `raport_md.py`, `przelicz_niezaleznie.py`, `sprawdz_raport.py`, `mutacje.py`
- odtworzenie każdej liczby z plików repo: [`ODTWORZENIE.md`](ODTWORZENIE.md)
