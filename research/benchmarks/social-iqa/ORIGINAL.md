# Social IQa: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpis brzmi „nieustalone” i podaje, gdzie szukano. Wszystkie źródła odczytano 2026-11-04.

| pole | wartość |
|---|---|
| Co mierzy | Zdrowy rozsądek w sytuacjach społecznych: „commonsense reasoning about social situations”, czyli motywacje, reakcje i skutki działań ludzi w codziennych sytuacjach. Model wybiera jedną z 3 odpowiedzi. |
| Źródła | praca: Sap, Rashkin, Chen, Le Bras, Choi, „Social IQa: Commonsense Reasoning about Social Interactions”, EMNLP-IJCNLP 2019, [arXiv:1904.09728](https://arxiv.org/abs/1904.09728); repo autorów: nieustalone (szukano: streszczenie arXiv, README zadania `siqa` w lm-eval, karta HF; autorzy publikują dane na stronie AI2, bez repo na GitHubie z kodem ewaluacji); zbiór HF: [`allenai/social_i_qa` @ `8835ceb9141d7896d9d968634a9b21ae440e3ec5`](https://huggingface.co/datasets/allenai/social_i_qa/tree/8835ceb9141d7896d9d968634a9b21ae440e3ec5) (tylko skrypt `social_i_qa.py`, blob `9a0ed84578b6b7ac3b9b0e67364e95e7346ee8ae`); dane czytane z `refs/convert/parquet`, `default/validation/0000.parquet` (blob `360f6b8ea281e327cdb42aea97c9932d237fc5ac` na `537a2ec8ec565adc0b70b70752893e59e024df26`, rewizji z dnia odczytu) |
| Dane: split w pracy | train, dev, test; ok. 38 tys. pytań łącznie. Karta HF @ `8835ceb9`: train 33410, validation 1954; splitu test w HF nie ma. n testu w pracy: nieustalone (nie czytano PDF). <!-- liczba-spoza-wynikow: 38 tys. ze streszczenia arXiv 1904.09728 --> |
| Dane: split w Space/repo | split: `validation` (T46 w `tasks_50.json` Space @ `2d3d73f`); n: 1954; repo liczy pełny split (`results/central-run/social-iqa/`), Space panel 200. |
| Dane: licencja | licencja autorów: nieustalone (karta HF @ `8835ceb9` bez tagu licencji; szukano też w README lm-eval); tag HF: brak (`tasks_50.json` T46: `declared_tags: ["unknown"]`, `data_gate: required_before_evaluation`); ukryte odpowiedzi w teście: tak (HF nie ma splitu test, test oceniał leaderboard AI2). |
| Typ testu | [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy), tabela „Testy Space według typu”, wiersz `mc` (T46). Wiersza `social-iqa` w tabeli benchmarków README jeszcze nie ma. |
| Format zadania i prompt | Wybór jednej z 3 opcji. Pola: `context`, `question`, `answerA`, `answerB`, `answerC`, `label` (`"1"`–`"3"`). lm-eval `social_iqa` (`siqa.yaml`), 0-shot: kontekst `Q: {context} {question}\nA:`, kontynuacja to `target_delimiter` (spacja) i pełny tekst opcji. Przykład (pierwszy wiersz `validation`, `label` = `"3"`): kontekst `Q: Tracy didn't go home that evening and resisted Riley's attacks. What does Tracy need to do before this?\nA:`, kontynuacja ` Find somewhere to go`. |
| Ocena | Praca: trafność modeli dostrajanych. lm-eval (`output_type: multiple_choice`): log-prawdopodobieństwo każdej kontynuacji, `acc` = argmax po sumie log P; YAML deklaruje tylko `acc`. Bez normalizacji tekstu. |
| Metryka decyzyjna | `acc` (`metric: acc,none` w `tasks_50.json` T46). `acc_norm` i `acc_mutual_info` repo liczy pomocniczo. |
| Agregacja i grupy | średnia po pytaniach, bez wag; bez grup. 24 konteksty mają po 2 pytania (48 z 1954 pytań); SE K Slayera po kontekstach 0,0111 wobec SE A 0,0110, więc test zostaje bez `+klastry`. <!-- liczba-spoza-wynikow: przeliczone z results/central-run/social-iqa/slayer1b-1.06/probki --> |
| Bazy | losowa: 1/3; stała odpowiedź: zawsze `answerC`, 657 z 1954 = 0,3362 (rozkład celu: A 643, B 654, C 657); b: 0,3362. |
| SNR: źródło | nieustalone: nie znaleziono źródła z wynikami 0-shot `social_iqa` dla co najmniej 3 modeli 0,4–3 mld. Szukano: pliki Pythii v0 (`EleutherAI/pythia` @ `a19eecb`, brak zadania), `openlifescienceai/results` (brak zadania), karty 5 modeli przebiegu, prace TinyLlama ([arXiv:2401.02385](https://arxiv.org/abs/2401.02385)) i DeltaNet ([arXiv:2406.06484](https://arxiv.org/abs/2406.06484)), bez SIQA. Niesprawdzone: Gated DeltaNet ([arXiv:2412.06464](https://arxiv.org/abs/2412.06464)), OLMo 2 (inny format, 5-shot). |
| SNR: rozrzut, SE, iloraz | nieustalone (brak źródła). Informacyjnie SE A dla n 1954 przy p = 0,4: 0,0111. <!-- liczba-spoza-wynikow: √(0,4·0,6/1954) --> |
| SNR: szum checkpointów | nieustalone (brak źródła). |
| MDE | pełny split: 2,79 pkt; panel 200: 8,71 pkt (jedno porównanie). SE różnicy: parowane Slayer 1.06 − LFM2.5-1.2B-Base, `acc`, z `probki/` przebiegu centralnego (0,0098 na 1954 pytaniach; panel przeskalowany √(1954/200)). <!-- liczba-spoza-wynikow: przeliczone z results/central-run/social-iqa/*/probki --> |
| Kontaminacja | znana: Space oznacza T46 dla Slayera 1.06 jako `contamination: flagged` (`results.json` Space @ `2d3d73f`). Dla modeli odniesienia nieznana. |
| Wyniki referencyjne (odczyt 2026-11-04) | brak: żaden model, który da się pobrać, nie ma znalezionego wyniku 0-shot w ustawieniach lm-eval `social_iqa`. Miejsca jak w polu „SNR: źródło” oraz issue [#97](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues/97). |
| Wyniki referencyjne: praca | modele dostrajane; ludzie mają wynik o ponad 20 pkt wyższy (streszczenie); inna metoda niż 0-shot. <!-- liczba-spoza-wynikow: streszczenie arXiv 1904.09728 --> |
| Wyniki referencyjne: Space | brak: T46 ma w Space @ `2d3d73f` stan `not_run` dla Slayera 1.06 i LFM2.5-1.2B-Base. |
| Train policy | `eval_only` dla `validation`. YAML ma `training_split: train` tylko jako źródło przykładów few-shot; liczymy 0-shot. |
| Decyzja treningowa | Niski `acc` znaczy, że model słabo wybiera najbardziej prawdopodobną reakcję albo motywację postaci w krótkiej scenie. Może wskazywać na mało narracji i dialogów w pretreningu. Wynik nie mówi o polszczyźnie. Nie wolno trenować na pytaniach Social IQa ani pisać danych na ich wzór. Różnica w pkt, która zmieniłaby decyzję: nieustalona, więc MDE jest informacyjne. |
| Znane rozbieżności | lista niżej |

## Znane rozbieżności

- **lm-eval `6d2abda4`, `v0.4.8` i `v0.4.9.1`** (katalog `lm_eval/tasks/siqa`): te same bloby we wszystkich trzech
  (`siqa.yaml` `6e387a73a9e005520f426b9d097a10d433279ce2`, `README.md` `ca58844b90079a607dd1a6a8a049106c26f57deb`).
  Space deklaruje `instrument: lm_eval_0.4.8`.
- **Szablon w repo:** `common/zadania.py` przepisuje szablon z `siqa.yaml` słowo w słowo (`doc_to_text`,
  `target_delimiter`, `doc_to_choice`, `doc_to_target`), zamiast wołać plik YAML.
- **Rewizja zbioru:** YAML ma `dataset_path: social_i_qa` (skrypt ładujący) bez rewizji. Repo czyta
  `refs/convert/parquet` bez przypiętego commitu, a `results_rozszerzone.json` nie zapisuje, który commit przeczytano.
  Rozkład celu z próbek (643/654/657, n 1954) zgadza się z liczbą wierszy karty HF.
- **Praca a lm-eval:** praca ocenia dostrajane modele; lm-eval i Space liczą 0-shot przez log-prawdopodobieństwo
  pełnego tekstu odpowiedzi.
