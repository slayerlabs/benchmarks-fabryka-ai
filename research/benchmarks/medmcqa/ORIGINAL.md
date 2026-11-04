# MedMCQA: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpis brzmi „nieustalone” i podaje, gdzie szukano. Wszystkie źródła odczytano 2026-11-04.

| pole | wartość |
|---|---|
| Co mierzy | Wiedzę medyczną na poziomie egzaminów wstępnych na studia podyplomowe w Indiach (AIIMS, NEET PG): pytania wielokrotnego wyboru z 21 przedmiotów medycznych i ok. 2,4 tys. tematów. <!-- liczba-spoza-wynikow: streszczenie arXiv 2203.14371 --> |
| Źródła | praca: Pal, Umapathi, Sankarasubbu, „MedMCQA: A Large-scale Multi-Subject Multi-Choice Dataset for Medical domain Question Answering”, CHIL 2022, [arXiv:2203.14371](https://arxiv.org/abs/2203.14371); repo autorów: [`MedMCQA/MedMCQA` @ `c59ef14ca1990266c4107c7864b45a20fd93e5e0`](https://github.com/MedMCQA/MedMCQA/tree/c59ef14ca1990266c4107c7864b45a20fd93e5e0); zbiór HF: [`openlifescienceai/medmcqa` @ `91c6572c454088bf71b679ad90aa8dffcd0d5868`](https://huggingface.co/datasets/openlifescienceai/medmcqa/tree/91c6572c454088bf71b679ad90aa8dffcd0d5868) |
| Dane: split w pracy | train, dev, test; n według karty HF @ `91c6572c`: train 182822, validation 4183, test 6150. |
| Dane: split w repo | split: `validation` (dev z pracy; test ma ukryte odpowiedzi; YAML lm-eval `medmcqa`: `test_split: validation`); n: 4183; przebieg centralny liczy pełny split (`results/central-run/medmcqa/`). Informacyjnie: Space liczy panel 200. |
| Dane: licencja | licencja autorów: MIT (repo `MedMCQA/MedMCQA`); tag HF: `license:apache-2.0`; ukryte odpowiedzi w teście: tak (`analyses/answer-format/ORIGINAL.md`, tabela zbiorów). |
| Typ testu | [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy), wiersz `medmcqa` |
| Format zadania i prompt | Wybór jednej z 4 opcji. Pola: `id`, `question`, `opa`–`opd`, `cop` (0–3), `choice_type`, `exp`, `subject_name`, `topic_name`. Praca nie ma promptu modelu językowego (modele dostrajane). lm-eval `medmcqa` (`utils_medmcqa.py`), 0-shot, format liter: kontekst `Question: {question}\nChoices:\nA. {opa}\nB. {opb}\nC. {opc}\nD. {opd}\nAnswer:`, kontynuacja to spacja i litera (` A`…` D`). Przykład (pierwszy wiersz `validation`, `cop` = 0): `Question: Which of the following is not true for myelinated nerve fibers:\nChoices:\nA. Impulse through myelinated fibers is slower than non-myelinated fibers\n…\nAnswer:`, kontynuacja ` A`. |
| Ocena | lm-eval (`output_type: multiple_choice`): log-prawdopodobieństwo każdej litery, `acc` = argmax po sumie log P; `acc_norm` dzieli przez długość litery, więc przy jednoznakowych opcjach równa się `acc` (w `results_rozszerzone.json` obie wartości są identyczne). Bez normalizacji tekstu. |
| Metryka decyzyjna | `acc`: trafność, jak w pracy; pierwsza metryka YAML-a lm-eval `medmcqa` (`acc_norm` przy opcjach-literach jest jej równa). Wariant cloze (`Question: {question}\nAnswer:` + treść opcji) repo liczy obok, informacyjnie. |
| Agregacja i grupy | średnia po pytaniach, bez wag; bez grup (przedmioty są polem, nie podtestem lm-eval). |
| Bazy | losowa: 0,25; stała odpowiedź: zawsze `A`, 1348 z 4183 = 0,3223 (rozkład celu: A 1348, B 1085, C 925, D 825); b: 0,3223. <!-- liczba-spoza-wynikow: rozkład celu z results/central-run/medmcqa/*/probki --> |
| SNR: źródło | Open Medical-LLM Leaderboard, pliki [`openlifescienceai/results` @ `62d7322cf11bf622399f7f54e5a7620ec6ef013d`](https://huggingface.co/datasets/openlifescienceai/results/tree/62d7322cf11bf622399f7f54e5a7620ec6ef013d/EleutherAI), 0-shot. Wzięto tylko Pythię bez `-deduped` (1b, 1.4b, 2.8b); innych modeli 0,4–3 mld z tego źródła nie wliczono. |
| SNR: 1b | 0,3163 (SE 0,0072) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, EleutherAI/pythia-1b, results.medmcqa --> |
| SNR: 1.4b | 0,3146 (SE 0,0072) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, EleutherAI/pythia-1.4b --> |
| SNR: 2.8b | 0,2716 (SE 0,0069) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, EleutherAI/pythia-2.8b --> |
| SNR: rozrzut | odchylenie std. `acc` 3 modeli (ddof=1): 0,0253 (ddof=0: 0,0207). <!-- liczba-spoza-wynikow: 3 pliki Pythii w openlifescienceai/results @ 62d7322c --> |
| SNR: SE | SE A dla n 4183: 0,0071, p̄ = 0,3008. <!-- liczba-spoza-wynikow: 3 pliki Pythii w openlifescienceai/results @ 62d7322c --> |
| SNR: iloraz | 3,57, ponad progiem 2. Wszystkie trzy wyniki leżą przy albo pod b (0,3223), więc rozrzut opisuje raczej preferencję litery niż wiedzę medyczną. <!-- liczba-spoza-wynikow: 3 pliki Pythii w openlifescienceai/results @ 62d7322c --> |
| SNR: szum checkpointów | nieustalone: źródło ma tylko końcowe checkpointy; pliki Pythii v0 nie mają `medmcqa`. |
| MDE | pełny split: 3,02 pkt; panel 200: 13,83 pkt (jedno porównanie). SE różnicy: parowane Slayer 1.06 − LFM2.5-1.2B-Base, `acc`, z `probki/` przebiegu centralnego (0,0106 na 4183 pytaniach; panel przeskalowany √(4183/200)). <!-- liczba-spoza-wynikow: przeliczone z results/central-run/medmcqa/*/probki --> |
| Kontaminacja | znana: Space oznacza T45 dla Slayera 1.06 jako `contamination: flagged`, `hit_rate` 0,045 na panelu (191 z 200 pytań bez trafienia). Dla modeli odniesienia nieznana. <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f --> |
| Wyniki referencyjne (odczyt 2026-11-04) | Żaden z 5 modeli przebiegu centralnego nie ma opublikowanego wyniku 0-shot (karty modeli, plik Pythii v0, `openlifescienceai/results`). Opublikowane wyniki 0-shot innych modeli: `openlifescienceai/results` @ `62d7322c`; lista w `REPRODUCTION.md`. |
| Wyniki referencyjne: praca | modele dostrajane na train; inna metoda niż 0-shot, liczb nie przepisano. |
| Wyniki referencyjne: Space | Space @ `2d3d73f`, panel 200: Slayer 1.06 0,245 (CI95 0,185–0,305), LFM2.5-1.2B-Base 0,405 (CI95 0,340–0,475). Porównanie w `REPRODUCTION.md`. <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f --> |
| Train policy | `eval_only` dla `validation` i `test`. YAML ma `training_split: train` tylko jako źródło przykładów few-shot; liczymy 0-shot. Zbioru wolno użyć do dekontaminacji (`should_decontaminate: true`, zapytanie to `question`). |
| Decyzja treningowa | Wynik w formacie liter mierzy łącznie wiedzę i umiejętność odpowiadania literą. Model, który wybiera prawie zawsze tę samą literę, dostaje udział tej litery wśród poprawnych odpowiedzi; taki wynik nie mówi nic o wiedzy medycznej (`REPRODUCTION.md`). Nie wolno trenować na pytaniach MedMCQA. Różnica w pkt, która zmieniłaby decyzję: nieustalona, więc MDE jest informacyjne. |
| Znane rozbieżności | lista niżej |

## Znane rozbieżności

- **lm-eval `6d2abda4`, `v0.4.8` i `v0.4.9.1`** (katalog `lm_eval/tasks/medmcqa`): te same bloby we wszystkich
  trzech (`medmcqa.yaml` `8fb1c7cdba4983d8ccb509491f699d9be0afa17e`, `utils_medmcqa.py`
  `8ce7e6beece511dccdfe94790456711ee7e93eab`). Space deklaruje `instrument: lm_eval_0.4.8`.
- **Źródło danych:** YAML ma `dataset_path: medmcqa` bez rewizji; repo czyta `openlifescienceai/medmcqa` @ `91c6572c`
  (rewizja przypięta w `common/zadania.py`).
- **Praca a lm-eval:** praca ocenia modele dostrajane; lm-eval i Space liczą 0-shot przez literę odpowiedzi. Pytania
  z `choice_type: multi` mają w zbiorze jedną poprawną literę (`cop`), więc lm-eval ocenia je jak pytania z jedną
  odpowiedzią.
- **Panel Space:** panel z `ranking_panel` repo na polu `id` daje `source_id_digest`
  `9d70111917825b92ee405f6ae00decde09f218a413ba98038d497dc3552e0c34`, a Space ma
  `42a9f00f0e8d3f1379b0c2ed8123a7fd7421b1789f19e048da83efdf4e3e5974`. Panelu Space nie da się więc odtworzyć z
  pewnością.
