# Slayer 1B 1.09, krok 40 000 (~61 mld), trening w toku, wynik wstępny: porównanie z 1.08 na 15 testach

<!-- Plik wygenerowany przez code/raport_md.py z LICZBY.json. Nie edytuj ręcznie. -->

Etykieta: **1.09, krok 40 000 (~61 mld), trening w toku, wynik wstępny**. Checkpoint w trakcie treningu, nie wersja przyjęta i nie następca 1.08; porównanie nie mówi nic o modelu końcowym 1.09. Protokół: [`PROTOKOL.md`](PROTOKOL.md).

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

## Środowisko

- batch: 1
- commit_kodu: b99f72a
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

- Kod na instancji to git archive commitu b99f72a (protokół z aneksem). Kod analizy liczby_109.py, raport_md.py i przelicz_niezaleznie.py zacommitowany w 88719f1 przed pierwszym wynikiem; liczby_109.py i tools/ewaluacja/raport.py liczą bez zmian od 88719f1.
- Po wyniku (kod pisany przed pierwszym wynikiem, ale niezacommitowany, przepadł przy awarii Maca i został napisany od nowa): dolacz_wyniki.py, sprawdz_raport.py, mutacje.py, diagnoza_acc_norm.py, w przelicz_niezaleznie.py kontrola narzędzia liczona od nowa z próbek i porównanie p Holma, w raport_md.py opis plików i werdykt po Holmie przy nazwie testu w liście głównego twierdzenia (strażnik liczb, reguła b), w tools/ewaluacja/raport.py jeden wiersz opisu plików. Progi, warianty i lista porównań bez zmian.
- Pole runner_sha256 różni się od pełnego przebiegu (suma całego katalogu research/common, nie samego ewaluuj.py): ewaluuj.py jest bajt w bajt ten sam, a jedyna zmiana w research/common między przebiegiem (51c5e31) a pomiarem (b99f72a) to klastry testu T27 (PSC) w zadania.py, spoza 15 testów tego pomiaru.
- Przeliczenie niezależne (przelicz_niezaleznie.py) kończy się kodem 1 wyłącznie na HellaSwag: liczy acc_norm z pola próbki lm_eval, a runner (metryki.oceny_mc) dzieli loglik przez długość kontynuacji bez wiodących spacji; definicje rozchodzą się na pytaniach, których kontynuacja ma kilka wiodących spacji (code/diagnoza_acc_norm.py, diagnoza_acc_norm.json). Podział lepsze/gorsze/szum i wszystkie werdykty po Holmie są w obu definicjach te same, więc główne twierdzenie nie jest obalone; liczby w raporcie są w definicji runnera, tej samej co pełny przebieg i manifest 1.08.
- Kolejka na instancji liczyła 4 procesy na kartę (aneks), pełny przebieg 2; każdy proces liczy w batch 1, więc liczba procesów nie zmienia wyniku pytania.
- Protokół nie mówi o czasy.jsonl przebiegu: dolacz_wyniki.py dopisuje do niego wiersze ewaluacji 1.09, tak jak do manifest.jsonl; pełne czasy obu etykiet leżą w eksport/czasy.jsonl.

## Niepoliczone (NOT RUN)

- Ranking z 1.08 jako modelem eksperymentalnym (PR 196) nie jest w tej gałęzi; wykresy rankingów pokazują 1.09 w toku obok ostatniej przyjętej wersji Slayera (1.07), bez 1.08.
- Kontrola na znanym modelu spoza Slayera: protokół jej nie przewiduje; kontrolą narzędzia jest 1.08 przeliczone wobec pełnego przebiegu.

## Pliki

- surowe wyniki: paczka eksportu `eksport_k109.tgz` (sha256 `6da5db6650220f45c19064ba89614ba18ac43f9f6e0c772462fbf29416ec257e`); jej pliki leżą w repo (próbki, trace i podsumowania jako gzip), sumy każdego pliku przed kompresją i po niej w [`probki_sha256.json`](probki_sha256.json) (sha256 `3183fbca4a9e60fced1b80a0ffbc16b5abb0704d3bd2b4138c53ece761e640a4`)
- `manifest.jsonl` przebiegu: sha256 `ff7df4efcfdd90449fb545f05a1c81dc8ab5761cee003c38d99db5abca7c92ee`
- `wyniki/<test>/slayer1b-1.08/`: 1.08 przeliczone; 1.09 w `../<test>/slayer1b-1.09-k40000/`; `eksport/`: manifest, środowisko i czasy z instancji; `logi/`: logi par
- `code/`: konwersja i sprawdzenie architektury, kolejka na instancji, `dolacz_wyniki.py`, `liczby_109.py`, `raport_md.py`, `przelicz_niezaleznie.py`, `sprawdz_raport.py`, `mutacje.py`
- odtworzenie każdej liczby z plików repo: [`ODTWORZENIE.md`](ODTWORZENIE.md)
