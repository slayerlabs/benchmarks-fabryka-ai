# Belebele-PL: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpis brzmi „nieustalone” i podaje, gdzie szukano. Wszystkie źródła odczytano 2026-11-05.

| pole | wartość |
|---|---|
| Co mierzy | Słowami autorów: „multiple-choice machine reading comprehension (MRC)”; każde pytanie opiera się na krótkim fragmencie z FLORES-200 i ma cztery odpowiedzi, z których jedna jest poprawna. Pytania mają odróżniać modele o różnym poziomie ogólnego rozumienia języka. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, abstrakt i sekcja 3 --> |
| Źródła | praca: Bandarkar, Liang, Muller, Artetxe, Shukla, Husa, Goyal, Krishnan, Zettlemoyer, Khabsa, „The Belebele Benchmark: a Parallel Reading Comprehension Dataset in 122 Language Variants”, ACL 2024, [arXiv:2308.16884v2](https://arxiv.org/abs/2308.16884v2); repo autorów @ commit: [`facebookresearch/belebele` @ `918890beb2290a8d3ef2d7a90369925959e1bacf`](https://github.com/facebookresearch/belebele/tree/918890beb2290a8d3ef2d7a90369925959e1bacf); zbiór HF @ rewizja: [`facebook/belebele` @ `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`](https://huggingface.co/datasets/facebook/belebele/tree/7899cdfa4e1e0d733fd77c848e2c273cb1d32be2), konfiguracja `pol_Latn`. <!-- liczba-spoza-wynikow: tytuł pracy i rewizje z arXiv, GitHub i HF API, odczyt 2026-11-05 --> |
| Dane: split w pracy | split: `test`; n: 900 pytań na wariant językowy; autorzy przeznaczają Belebele wyłącznie do testu, bez treningu i walidacji. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, sekcje 3.4–3.5 i README repo autorów @ 918890b --> |
| Dane: budowa | 488 unikalnych fragmentów FLORES-200, po 1–2 pytania na fragment; 4 opcje i dokładnie 1 poprawna; 109 800 wierszy w 122 wariantach językowych. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, tabela 1 i sekcja 3.5; README repo autorów @ 918890b --> |
| Dane: split w Space/repo | split: `test`; n: 900 (plik `data/pol_Latn.jsonl` @ `7899cdfa`); pełny split centralny: 895 ocenianych, bo 5 dokumentów banku demonstracji wypada z oceny (`benchmarks/belebele-pl/README.md`); panel 200 wybierany skrótem SHA-256 z `METHOD.md` Space @ `2d3d73f`. <!-- liczba-spoza-wynikow: plik pol_Latn.jsonl @ 7899cdfa, odczyt 2026-11-05; README belebele-pl; tasks_50.json i METHOD.md Space @ 2d3d73f5 --> |
| Dane: licencja | licencja autorów: CC-BY-SA-4.0 (plik `LICENSE_CC-BY-SA4.0` w repo @ 918890b); tag HF: `cc-by-sa-4.0`; ukryte odpowiedzi w teście: nie, `correct_answer_num` jest w pliku. Osobny angielski zbiór treningowy autorów (ok. 68 tys. przykładów z RACE, SciQ, MultiRC, MCTest, MCScript2.0 i ReClor) ma inną licencję i nie jest częścią Belebele. <!-- liczba-spoza-wynikow: karta HF facebook/belebele @ 7899cdfa; README repo autorów @ 918890b; sekcje 3.4 i A.2 pracy --> |
| Typ testu | [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy), wiersz `belebele-pl` (`mc +pl`) |
| Format zadania i prompt | Wybór jednej z 4 opcji. 5-shot: 5 demonstracji z banku wybieranego hashem z dokumentów splitu `test`; każde pytanie dostaje te same 5 w tej samej kolejności, demonstracje są oddzielone pustą linią, a dokument użyty jako demonstracja nie jest oceniany (`common/ewaluuj.py`, `ustaw_bank`). Szablon OpenPL z YAML-a `belebele_mc.yaml`: `Fragment: "{{flores_passage}}"\nPytanie: "{{question}}"\nMożliwe odpowiedzi:\nA - {{mc_answer1}}\nB - {{mc_answer2}}\nC - {{mc_answer3}}\nD - {{mc_answer4}}\nPrawidłowa odpowiedź:`; `doc_to_choice` = `["A", "B", "C", "D"]`; `doc_to_target` = indeks `correct_answer_num` w `["1", "2", "3", "4"]`; `target_delimiter` = spacja, więc oceniana kontynuacja to `" A"`…`" D"` (litera, nie treść odpowiedzi). Przykład renderowania: sekcja „Przykład promptu” niżej. <!-- liczba-spoza-wynikow: belebele_mc.yaml @ 21d0ea9c; README belebele-pl; METODOLOGIA, „Przykłady few-shot” --> |
| Ocena | lm-eval `output_type: multiple_choice`: `acc` = argmax sumy log-prawdopodobieństw kontynuacji-litery; bez normalizacji długości; przy remisie wygrywa wcześniejsza opcja. `acc_norm` dzieli przez `len()` napisu opcji z `doc_to_choice`, czyli `"A"`…`"D"` (1 znak, bez spacji z `target_delimiter`), a nie przez długość kontynuacji w bajtach; wszystkie opcje mają tę samą długość, więc `acc_norm` = `acc`. <!-- liczba-spoza-wynikow: belebele_mc.yaml @ 21d0ea9c; lm-eval v0.4.9.1, lm_eval/api/task.py, process_results: completion_len = [len(i) for i in doc["choices"]] --> |
| Metryka decyzyjna | `acc` (pole `metric` w `tasks_50.json` Space: `acc,none`; wpis `T24` w `common/zadania.py`: `acc,none`). `acc_norm` jest pomocnicza i równa `acc`. <!-- liczba-spoza-wynikow: tasks_50.json Space @ 2d3d73f5; common/zadania.py --> |
| Agregacja i grupy | Średnia po pytaniach; brak podtestów i grup; jeden poziom werdyktu (cały test). |
| Bazy: losowa | 0,25 (cztery równe opcje w każdym pytaniu). <!-- liczba-spoza-wynikow: belebele_mc.yaml @ 21d0ea9c, 4 opcje; METODOLOGIA, typ mc --> |
| Bazy: stała odpowiedź | zawsze pozycja `B` (indeks 1): 251 z 900 = 0,2789; rozkład poprawnej odpowiedzi: A 206, B 251, C 246, D 197. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, policzone 2026-11-05 --> |
| Bazy: b | 0,2789 (większa z bazy losowej 0,25 i stałej odpowiedzi 0,2789). <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, policzone 2026-11-05 --> |
| SNR: źródło | po przebiegu centralnym (panel modeli przebiegu centralnego) |
| SNR: rozrzut | po przebiegu centralnym |
| SNR: SE | po przebiegu centralnym |
| SNR: iloraz | po przebiegu centralnym |
| SNR: szum checkpointów | nieustalone. Szukano: `evals/pythia-v0`, `evals/pythia-v1`, `evals/bias-evals`, `evals/bloom`, `evals/opt` i `evals/csv` w [`EleutherAI/pythia` @ `main`](https://github.com/EleutherAI/pythia) — żaden plik nie ma zadania Belebele; tabela 5 i dodatek A.7 pracy — tylko końcowe wyniki bez per-checkpoint; karty HF `FacebookAI/xlm-roberta-large`, `microsoft/infoxlm-large` i `facebook/xlm-v-base` — brak wyników per checkpoint. Nie przeszukano: innych leaderboardów i cytowań pracy. |
| MDE | pełny split: 6,7 pkt (n = 895); panel 200: 14,2 pkt. SE różnicy wzięte z `√2 · SE` pojedynczego wyniku przy p = 0,5 (największa wariancja), bo nie ma modelu kontrolnego z wynikami per pytanie: SE = 0,0167 dla n = 895 i 0,0354 dla n = 200; MDE = (2 + 0,84) · √2 · SE. <!-- liczba-spoza-wynikow: wyliczone z n = 895 i 200, wzór MDE z METODOLOGIA, rdzeń punkt 5 --> |
| Kontaminacja | nieznana: własnego skanu korpusu Slayera ani modeli odniesienia pod kątem Belebele nie robiono; Space @ `2d3d73f` oznacza T24 dla `SlayerLab/Slayer1B-1.06` jako `clean` (receipt sha256 `bc6c168cf6ef35bce80b70f3bf582853526b558cb7f37e30101e35f3c2342de7`), a dla `LiquidAI/LFM2.5-1.2B-Base` jako `unknown`. <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f5, observations T24 --> |
| Kandydat kontroli etapu B: Qwen2-1.5B | `Qwen/Qwen2-1.5B` @ `8a16abf2848eda07cc5253dec660bf1ce007ad7a` (bfloat16) → `acc` 0,5656 (56,5556%), 5-shot, `polish_belebele_mc`, `facebook/belebele` `pol_Latn`, split `test`, n = 900; źródło: odczyt z działającej aplikacji 2026-11-05, plik `all_data.json` pobrany przyciskiem eksportu, SHA-256 `7c6d37383543e9606cb16c167bcf6c71b82246aad63b328ab991de1069d55b66`; wyników nie da się przypiąć do rewizji, bo zbiór wyników jest prywatny (Space @ `0d30867d1c291d42812b5f9c51988dd33d1b5145` przypina tylko kod aplikacji, a aplikacja pobiera wyniki z `speakleash/open_pl_llm_leaderboard_results`, HTTP 401), wiersz `Qwen2-1.5B`, kolumna `belebele_mc`. Protokół: fork `speakleash/lm-evaluation-harness` @ `21d0ea9c` (branch `polish4`), `lm_eval --tasks polish_mc --num_fewshot 5`; to ten sam YAML `belebele_mc.yaml`. Model bazowy bez szablonu czatu, 1,5 mld parametrów, dostępny na HF. Demonstracje: `first_n` z YAML-a forka (5 pierwszych dokumentów testu); repo w przebiegu centralnym bierze bank hashowy, więc dobór demonstracji się różni, ale szablon, zadanie, split, metryka i 5-shot są te same. Wynik jest powyżej b + 2 SE. To kandydat z tym samym szablonem, ale innymi demonstracjami niż przebieg centralny (sekcja „Znane rozbieżności”, punkt „Kandydat kontroli”); nie mierzono go w tym repo. <!-- liczba-spoza-wynikow: Open PL LLM Leaderboard @ 0d30867d, all_data.json pobrany 2026-11-05, wiersz Qwen/Qwen2-1.5B, n_shot 5; model sha z HF API --> |
| Wyniki referencyjne (odczyt 2026-11-05): Falcon-40B | `tiiuae/falcon-40b` @ `05ab2ee8d6b593bdbab17d728de5c028a7a94d83` → `acc` 0,599, 5-shot, `pol_Latn`, n = 900, średnia z 3 przebiegów; źródło: [arXiv:2308.16884v2, tabela 7](https://arxiv.org/abs/2308.16884v2), wiersz `pol_Latn` na s. 772 (PDF s. 24). To **nie** jest kandydat zgodny z protokołem karty: praca używa promptu `P:/Q:/A:`, a nie polskiego promptu OpenPL, i modelu 40 mld parametrów; wynik jest tylko referencją. Dosłowny wiersz i nagłówek: sekcja „Notatka: tabela 7 pracy”. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, tabela 7, s. 772; rewizja Falcon-40B z HF API, odczyt 2026-11-05 --> |
| Wyniki referencyjne: Llama-2-70B | `meta-llama/Llama-2-70b-hf` @ `3aba440b59558f995867ba6e1f58f21d0336b5bb` → `acc` 0,792, 5-shot, `pol_Latn`, n = 900, średnia z 3 przebiegów; źródło: tabela 7 pracy, wiersz `pol_Latn` na s. 772 (PDF s. 24). Model jest gated na HF i ma inny prompt niż karta, więc to tylko referencja, nie kandydat kontroli. Dosłowny wiersz i nagłówek: sekcja „Notatka: tabela 7 pracy”. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, tabela 7, s. 772; rewizja Llama-2-70B z HF API, odczyt 2026-11-05 --> |
| Wyniki referencyjne: XLM-R large | `FacebookAI/xlm-roberta-large` @ `c23d21b0620b635a76227c604d44e43a9f0ee389` → `acc` 0,674, `pol_Latn`, `finetune in English`, n = 900; źródło: tabela 5 pracy. Wynik dotyczy modelu po dostrojeniu (autorzy nie publikują wag po dostrojeniu), więc nie jest gotową kontrolą 5-shot; to tylko referencja. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, tabela 5; rewizja XLM-R large z HF API, odczyt 2026-11-05 --> |
| Train policy | `eval_only`: split `test` nie trafia do treningu. Osobny angielski zbiór treningowy (RACE, SciQ, MultiRC, MCTest, MCScript2.0, ReClor) nie jest częścią Belebele i nie jest używany w przebiegu centralnym. Zbioru wolno użyć do dekontaminacji (`should_decontaminate: true`, zapytanie to `question`). |
| Decyzja treningowa | Niski `acc` znaczy, że model słabo czyta polski fragment i wybiera jedną z czterech liter; nie mówi nic o wiedzy encyklopedycznej, generowaniu ani innych językach. Wysoki wynik może pochodzić z preferencji pozycji litery (stała `B` daje 0,2789) albo z kontaminacji, więc sam wynik nie dowodzi rozumienia. Różnica w pkt, która zmieniłaby decyzję: nieustalona, więc MDE jest informacyjne. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, policzone 2026-11-05 --> |
| Znane rozbieżności | lista niżej |

## Przykład promptu

Pierwszy wiersz `data/pol_Latn.jsonl` @ `7899cdfa` (`correct_answer_num` = `"1"`, więc poprawna jest `A`). <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, odczyt 2026-11-05 -->
Przed pytaniem jest 5 demonstracji z banku; poniżej skrócony zapis, bo każda demonstracja ma ten sam szablon i własny fragment. <!-- liczba-spoza-wynikow: belebele_mc.yaml @ 21d0ea9c i README belebele-pl, protokół 5-shot -->

```text
Fragment: "Zadbaj o to, aby Twoja ręka była jak najbardziej rozluźniona, prawidłowo trafiając we wszystkie nuty – postaraj się też nie robić zbędnych ruchów palcami. Tym sposobem unikniesz przemęczenia. Pamiętaj, że nie musisz naciskać klawiszy mocniej, aby dźwięk był głośniejszy, jak to jest w przypadku fortepianu. Aby uzyskać większą głośność, grając na akordeonie, należy poruszać miechami z większym naciskiem lub większą szybkością."
Pytanie: "Czego zgodnie z fragmentem nie można uważać za dokładną wskazówkę umożliwiającą granie na akordeonie?"
Możliwe odpowiedzi:
A - Aby zwiększyć głośność, naciskaj klawisze z większą siłą
B - Ogranicz do minimum niepotrzebne ruchy, aby zachować kondycję
C - Pamiętaj, aby uderzać w przyciski rozluźnioną dłonią
D - Zwiększ prędkość operowania mieszkami, aby zwiększyć głośność
Prawidłowa odpowiedź:
```

Oceniane kontynuacje: `" A"` (poprawna, indeks 0), `" B"`, `" C"`, `" D"`. Pierwszy wiersz ma `link`
`https://en.wikibooks.org/wiki/Accordion/Right_hand` i `question_number` 1; `link` nie jest unikalny, unikalna jest para
`link` + `question_number`. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, odczyt 2026-11-05 -->

## Model kontrolny etapu B: szukanie

Kandydat: `Qwen/Qwen2-1.5B` @ `8a16abf2848eda07cc5253dec660bf1ce007ad7a`, bfloat16, 5-shot,
`polish_belebele_mc`, `acc` 56,5556% (0,5656), n = 900. <!-- liczba-spoza-wynikow: Open PL LLM Leaderboard @ 0d30867d, all_data.json pobrany 2026-11-05, wiersz Qwen/Qwen2-1.5B, n_shot 5 --> Źródło wyniku: odczyt z działającej aplikacji 2026-11-05,
plik `all_data.json` pobrany przyciskiem eksportu, SHA-256 `7c6d37383543e9606cb16c167bcf6c71b82246aad63b328ab991de1069d55b66`;
wyników nie da się przypiąć do rewizji, bo zbiór wyników jest prywatny. Space @ `0d30867d1c291d42812b5f9c51988dd33d1b5145`
przypina tylko kod aplikacji; aplikacja pobiera wyniki przy starcie z `speakleash/open_pl_llm_leaderboard_results`
(HTTP 401), a `all_data.json` nie istnieje w tej rewizji — jest tylko w działającej aplikacji. Dla wiersza
`Qwen2-1.5B` plik ma `n_shot` = `5` i `belebele_mc` = `56.55555555555556`. Leaderboard opisuje protokół jako `polish_mc` z `--num_fewshot 5`
(`src/about.py`, sekcja „Reproducibility”; `calc_avg.py`, `task9a` = `polish_belebele_mc`), a fork
`speakleash/lm-evaluation-harness` ma branch `polish4` na commicie `21d0ea9c`, z którego karta bierze YAML `belebele_mc.yaml`; commit, na którym
leaderboard policzył ten wiersz, nie jest podany w źródle (sekcja „Znane rozbieżności”, punkt „Kandydat kontroli”).
Model jest bazowy (bez szablonu czatu), 1,5 mld parametrów i nie jest żadnym z pięciu modeli odniesienia. Szablon jest
ten sam co w karcie, demonstracje inne; nie był mierzony w tym repo.

Szukano:
- `EleutherAI/pythia-1b-v0` @ `step143000` (METODOLOGIA, „Model kontrolny etapu B”, punkt 1): plik 0-shot z 132 zadań (arc, lambada, piqa, sciq, winogrande, wsc, 67 BLiMP i 57 hendrycksTest) nie ma Belebele; żaden plik w katalogu `evals` repo `EleutherAI/pythia` nie ma zadania Belebele. <!-- liczba-spoza-wynikow: plik Pythii v0 @ a19eecb, odczyt 2026-11-05 -->
- `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` (METODOLOGIA, punkt 2): karta modelu nie podaje wyniku Belebele. <!-- liczba-spoza-wynikow: karta EuroLLM-1.7B @ c730cd9, odczyt 2026-11-05 -->
- Open PL LLM Leaderboard: tabela `all_data.json`/`output.csv`, `src/about.py`, `calc_avg.py`, README Space.
  Wiersze 5-shot dla modeli do 2 mld:
  - `Qwen/Qwen2-1.5B` 56,5556. <!-- liczba-spoza-wynikow: Open PL LLM Leaderboard @ 0d30867d, all_data.json pobrany 2026-11-05 -->
  - `Qwen/Qwen2-1.5B-Instruct` 58,3333. <!-- liczba-spoza-wynikow: Open PL LLM Leaderboard @ 0d30867d, all_data.json pobrany 2026-11-05 -->
  - `Qwen/Qwen2.5-1.5B` 64,3333. <!-- liczba-spoza-wynikow: Open PL LLM Leaderboard @ 0d30867d, all_data.json pobrany 2026-11-05 -->
  - `google/gemma-3n-E2B-it` 77,5556. <!-- liczba-spoza-wynikow: Open PL LLM Leaderboard @ 0d30867d, all_data.json pobrany 2026-11-05 -->
  Kandydat wybrany: `Qwen2-1.5B`, bo ma jawny `Model sha` i jest modelem bazowym.
- `speakleash/open_pl_llm_leaderboard_results` (surowe pliki wyników) — API zwraca HTTP 401 (repozytorium prywatne);
  Space @ `0d30867d` przypina tylko kod aplikacji, a `all_data.json` nie istnieje w tej rewizji (tylko w działającej
  aplikacji); nie ma publicznego JSON-a z tym wierszem.
- PoLEJ (`polej.azurro.pl`) — ma kolumnę Belebele PL, ale opis mówi 0-shot i `greedy_until`, więc to inny protokół
  niż karta.
- Tabela 7 pracy i karty HF `tiiuae/falcon-40b`, `meta-llama/Llama-2-70b-hf`, `FacebookAI/xlm-roberta-large`,
  `microsoft/infoxlm-large`, `facebook/xlm-v-base` — wyniki 5-shot w pracy mają prompt `P:/Q:/A:` i modele
  od 7 do 70 mld (Llama 1 7B–65B, Llama 2 70B, Falcon 40B), a XLM-R/InfoXLM/XLM-V są dotrenowane na angielskim, nie liczone 5-shot. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, tabele 2 i 7, odczyt 2026-11-05 -->
- `codesota.com/benchmark/open-pl-llm-leaderboard` — strona nie ma wyników; `github.com/chrisociepa/polish-open-llm-leaderboard`
  to stary leaderboard 0-shot.

Nie przeszukano: kanału Discord SpeakLeash, prywatnych wyników poza publiczną tabelą, innych leaderboardów i cytowań
pracy pod kątem wyników `polish_belebele_mc`.

## Notatka: tabela 7 pracy

Nagłówek tabeli 7 (s. 771, PDF s. 23), w kolejności kolumn (zapis z HTML-a pracy; w PDF małe kapitaliki rozbijają `LLAMA`/`FALCON`):

```text
Evaluation Zero-Shot for Instructed Models 5-shot In-Context Learning Translate-Train-All
Model Name GPT3.5-turbo Llama-2-chat Llama 2 Llama 1 Falcon XLM-V
Size/Variant 70B 70B 65B 40B large
```

Wiersz `pol_Latn` (s. 772, PDF s. 24), dosłownie:

```text
pol_Latn 74.7 61.7 79.2 67.0 59.9 72.1
```

Kolumny w kolejności: GPT3.5-turbo 74,7; Llama-2-chat 61,7; Llama 2 79,2; Llama 1 67,0; Falcon 59,9; XLM-V 72,1. <!-- liczba-spoza-wynikow: ACL PDF 2024.acl-long.44, tabela 7, wiersz pol_Latn, s. 772, odczyt 2026-11-05 -->
Podpis tabeli: „Table 7: Results on LLMs, with comparison to full finetuning on XLM-V” (s. 773). Źródło: ACL PDF
`2024.acl-long.44`, odczyt 2026-11-05. <!-- liczba-spoza-wynikow: ACL PDF 2024.acl-long.44, tabela 7, s. 771-773, odczyt 2026-11-05 -->

## Znane rozbieżności

- **Katalog zadania w forku OpenPL** [`speakleash/lm-evaluation-harness` @ `21d0ea9cf4fd6153dfff4d84d6ad0aab5488f302`](https://github.com/speakleash/lm-evaluation-harness/tree/21d0ea9cf4fd6153dfff4d84d6ad0aab5488f302/lm_eval/tasks/polish_belebele):
  `README.md` blob `a100b52a73c5c1b0bd723c9ceb490f85c02507d2`, `belebele_mc.yaml` blob
  `d14ea8d9206a56b682769a4e54ef4a5882da6e2c`, `belebele_regex.yaml` blob
  `0d65e06fde5162fda65b8cf36f70aa4f44f16078`. Katalogu `lm_eval/tasks/polish_belebele` **nie ma** w
  EleutherAI lm-eval `6d2abda4` ani w `v0.4.9.1`; jest tylko angielski katalog `lm_eval/tasks/belebele`, identyczny w
  obu wersjach (m.in. `_default_template_yaml` blob `c32b310ba86091f627c7ec5717fd7cb4f69a46f2`,
  `belebele_pol_Latn.yaml` blob `295d5e75c0bc5d2eee3821a33273733351cc9cf0`, `README.md` blob
  `e08e63e8a11b563dad771f8ee99a1da167e55016`). <!-- liczba-spoza-wynikow: git tree speakleash/lm-evaluation-harness @ 21d0ea9c i EleutherAI/lm-evaluation-harness @ 6d2abda4 i v0.4.9.1, odczyt 2026-11-05 -->
- **Prompt pracy a prompt OpenPL**: praca w 5-shot używa szablonu `P: <passage>\nQ: <question>\nA: <mc answer 1>\nB: <mc answer 2>\nC: <mc answer 3>\nD: <mc answer 4>\nAnswer: <Correct answer letter>`, demonstracji z angielskiego zbioru treningowego i średniej z 3 przebiegów. YAML `belebele_mc.yaml` używa polskich etykiet `Fragment:`, `Pytanie:`, `Możliwe odpowiedzi:`, `A -`…`D -`, `Prawidłowa odpowiedź:`; demonstracje bierze z polskiego splitu `test` (bank hashowy), a przebieg jest deterministyczny, bez uśredniania 3 przebiegów. Ocena liter jest ta sama: wybierana jest litera `A`–`D`. <!-- liczba-spoza-wynikow: Bandarkar i in. 2023, A.4.2 i tabela 7; belebele_mc.yaml @ 21d0ea9c; README belebele-pl -->
- **Zbiór**: `polish_belebele_mc` w YAML nie przypina rewizji; `common/zadania.py` i `tasks_50.json` Space przypinają `facebook/belebele` @ `7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, więc karta też. <!-- liczba-spoza-wynikow: common/zadania.py; tasks_50.json Space @ 2d3d73f5; YAML @ 21d0ea9c -->
- **Dane, smoke test**: 824 z 900 wierszy (412 fragmentów po 2 pytania) dzieli `link` z drugim pytaniem, ale para `link` + `question_number` jest unikalna; 488 fragmentów, z tego 412 ma 2 pytania, a 76 ma 1 pytanie. 3 pytania mają dwie identyczne opcje (indeksy od 0: 401, 431, 779; w pliku linie 402, 432, 780); w dwóch z nich (indeksy 401 i 431) duplikatem jest opcja poprawna, więc pytanie ma dwa równie dobre wybory. 105 opcji ma biały znak na końcu (w 98 pytaniach), a 1 opcja ma biały znak na początku (w osobnym pytaniu); łącznie 106 opcji w 99 pytaniach. 0 pól jest pustych i 0 pytań ma identyczny tekst. Pytanie o indeksie 401 (linia 402) ma powtórzone „ile osób”. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, policzone 2026-11-05: 105 końcowych + 1 początkowy = 106 opcji; 98 pytań z końcowym + 1 z początkowym = 99 pytań; indeksy wierszy od 0 -->
- **Pełny split centralny**: 900 wierszy w pliku, ale bank 5 demonstracji jest wybierany z całego splitu i jego dokumenty wypadają z oceny, więc ocenianych jest 895; Space liczy panel 200 i ocenia 200. <!-- liczba-spoza-wynikow: README belebele-pl; common/ewaluuj.py, wybor_probki i wykluczone; results.json Space @ 2d3d73f5 -->
- **Kandydat kontroli (Qwen2-1.5B) a przebieg centralny**: wynik leaderboardu policzono demonstracjami `first_n` z YAML-a forka (5 pierwszych dokumentów testu, oceniane też, n = 900), a przebieg centralny bierze bank hashowy i ocenia 895 dokumentów; README `belebele-pl` mówi, że wynik nie jest porównywalny wprost z liczbą forka. Inne demonstracje mogą same przesunąć wynik modelu 1,5 mld, więc w etapie B różnica z wynikiem referencyjnym nie musi znaczyć błędu kodu. <!-- liczba-spoza-wynikow: README belebele-pl; belebele_mc.yaml @ 21d0ea9c, fewshot_config first_n -->
- **Kandydat kontroli: commit harnessu**: leaderboard nie podaje commitu forka dla wiersza `Qwen2-1.5B`; `21d0ea9c` to obecna głowa brancha `polish4`, przyjęta, a nie odczytana ze źródła. Historia `belebele_mc.yaml` w forku ma dwa commity: `bc61568e` (2024-03-10, dodanie) i `0bea4239` (2024-08-13, tylko `dataset_name`/`fewshot_split`/`test_split` pod nowy układ zbioru HF); szablon promptu, opcje i cel są w obu takie same. <!-- liczba-spoza-wynikow: gh api commits speakleash/lm-evaluation-harness @ 21d0ea9c, ścieżka lm_eval/tasks/polish_belebele/belebele_mc.yaml, odczyt 2026-11-05 -->
- **`acc_norm`**: YAML ma `acc` i `acc_norm`; lm-eval v0.4.9.1 w `process_results` dzieli przez `len()` napisu opcji z `doc_to_choice` (`"A"`–`"D"`, 1 znak, bez `target_delimiter`), a nie przez długość kontynuacji w bajtach. Wszystkie opcje mają tę samą długość, więc `acc_norm` = `acc`; Space raportuje tylko `acc`. <!-- liczba-spoza-wynikow: belebele_mc.yaml @ 21d0ea9c; lm-eval v0.4.9.1, process_results: completion_len = [len(i) for i in doc["choices"]] -->
- **Space**: T24 dla `LiquidAI/LFM2.5-1.2B-Base` ma na panelu 200 0,300 (CI95 0,240–0,365), a dla `SlayerLab/Slayer1B-1.06` 0,300 (CI95 0,235–0,365); werdykt `inconclusive`. To przykład, nie wynik referencyjny ani kontrola. <!-- liczba-spoza-wynikow: results.json Space @ 2d3d73f5, observations i contrasts T24 -->
