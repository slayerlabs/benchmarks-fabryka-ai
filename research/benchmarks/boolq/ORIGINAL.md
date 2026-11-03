# BoolQ: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Odczyt
źródeł: 2026-11-03.

| pole | wartość |
|---|---|
| Co mierzy | Słowami autorów: pytania tak/nie, które powstają same, bez podpowiedzi i bez ograniczenia, oraz czytanie ze zrozumieniem, które wymaga wnioskowania podobnego do wynikania. |
| Źródła: praca | Clark, Lee, Chang, Kwiatkowski, Collins, Toutanova, „BoolQ: Exploring the Surprising Difficulty of Natural Yes/No Questions”, NAACL 2019, [arXiv:1905.10044](https://arxiv.org/abs/1905.10044) |
| Źródła: repo autorów | [`google-research-datasets/boolean-questions` @ `90af341`](https://github.com/google-research-datasets/boolean-questions/tree/90af34107399cc7a446b373dc4ee35b8001da7c2) |
| Źródła: lm-eval | Space: [`super_glue/boolq` @ `6d2abda4`](https://github.com/EleutherAI/lm-evaluation-harness/tree/6d2abda4fd171e68a8789330c4149e37c1ca0bda/lm_eval/tasks/super_glue/boolq); repo: ten sam katalog @ [`v0.4.9.1`](https://github.com/EleutherAI/lm-evaluation-harness/tree/v0.4.9.1/lm_eval/tasks/super_glue/boolq) |
| Źródła: zbiór HF | [`aps/super_glue` @ `3de24cf`](https://huggingface.co/datasets/aps/super_glue/tree/3de24cf8022e94f4ee4b9d55a6f539891524d646), konfiguracja `boolq` |
| Dane: split w pracy | train, dev i test. n train: 9427. <!-- liczba-spoza-wynikow: README autorów @ 90af341 --> |
| Dane: n dev | 3270. <!-- liczba-spoza-wynikow: README autorów @ 90af341 --> |
| Dane: n test | 3245, bez etykiet. <!-- liczba-spoza-wynikow: README autorów @ 90af341 --> |
| Dane: split w Space/repo | `validation`, pełny split 3270, a Space liczy panel 200. Test T10, metryka `acc`, 0-shot. <!-- liczba-spoza-wynikow: tasks_50.json Space, id T10; n z karty HF i z parquetu validation @ 3de24cf --> |
| Dane: licencja | licencja autorów: Creative Commons Share-Alike 3.0, link w README do CC BY-SA 3.0; tag HF: `other`; ukryte odpowiedzi w teście: tak (w parquetcie testu @ `3de24cf` wszystkie 3245 etykiet to −1) |
| Format zadania | Pytanie tak/nie plus ustęp z Wikipedii. Dwie odpowiedzi, bez liter. Autorzy traktują to jak klasyfikację pary tekstów, w stylu NLI. |
| Prompt | W pracy nie ma promptu modelu bazowego. Autorzy dostrajają klasyfikator (najlepsza metoda z abstraktu: BERT uczony na MultiNLI, potem na train BoolQ). lm-eval `default.yaml`, 0-shot: `{passage}\nQuestion: {question}?\nAnswer:`, potem `target_delimiter` (domyślnie jedna spacja) i opcja `no` albo `yes`. Indeks 0 to `no` (etykieta False), indeks 1 to `yes` (etykieta True). Żadne z 3270 pytań walidacji nie ma już znaku zapytania, więc szablon dokleja dokładnie jeden. |
| Ocena | Praca: trafność klasyfikatora tak/nie. lm-eval: `acc`, argmax log-prawdopodobieństwa kontynuacji ` no` albo ` yes`. Przy remisie wygrywa wcześniejsza opcja (`no`). Długości się nie normalizuje. `acc_norm` nie jest w pliku zadania. |
| Metryka decyzyjna | `acc` |
| Agregacja | Średnia po pytaniach, bez wag. YAML nie wpisuje agregacji; dla metryki `acc` harness bierze swoją domyślną, `mean`. |
| Bazy: losowa | 0,5. <!-- liczba-spoza-wynikow: 1/2, dwie opcje w każdym pytaniu --> |
| Bazy: liczność „tak” | 2033 z 3270 na walidacji @ `3de24cf`. <!-- liczba-spoza-wynikow: policzone z boolq/validation parquet --> |
| Bazy: większościowa | 0,6217 (zawsze „tak”). <!-- liczba-spoza-wynikow: 2033/3270 na walidacji @ 3de24cf --> |
| SNR: źródło | Tabela 3 pracy TinyLlama, [arXiv:2401.02385v2](https://arxiv.org/abs/2401.02385v2) (w v1 tabela 2 ma tylko cztery modele), 0-shot, lm-eval, kolumna `boolq`. Siedem modeli około 1–1,4B z jednego źródła: OPT-1.3B, Pythia-1.0B, Pythia-1.4B, TinyLlama v1.0, v1.1, v1.1 Math&code, v1.1 Chinese. Szerszego zakresu rozmiarów w tej tabeli nie ma, więc SNR skali porównania jest tym samym zestawem. |
| SNR: rozrzut | 2,66 pkt proc. (odchylenie std., ddof=1). <!-- liczba-spoza-wynikow: wyliczone z kolumny boolq tabeli 3 TinyLlama --> |
| SNR: SE | 0,860 pkt proc. dla n = 3270, √(p̄(1−p̄)/n), p̄ = 0,5918. Praca nie podaje n, ale wszystkie siedem wartości to k/3270 (każda × 32,7 daje liczbę całkowitą ±0,16), więc n = 3270. To n pełnej walidacji zadania harnessu, nie panelu 200. <!-- liczba-spoza-wynikow: wyliczone; n z parquetu validation @ 3de24cf --> |
| SNR: iloraz | 3,10. <!-- liczba-spoza-wynikow: rozrzut / SE pełnej walidacji --> |
| SNR: SE panel 200 | 3,48 pkt proc. przy tym samym p̄. <!-- liczba-spoza-wynikow: wyliczone dla n=200 --> |
| SNR: iloraz panel 200 | 0,77. Na panelu 200 Space rozrzut z tej tabeli ginie w SE. <!-- liczba-spoza-wynikow: rozrzut / SE panelu 200 --> |
| Wyniki referencyjne (odczyt 2026-11-03) | brak. Etap B idzie bez kontroli. Szukano: plik Pythii v0 `pythia-1b-0shot-global_step143000` (brak `boolq`; jest `wsc`, to SuperGLUE WSC, inny zbiór); karta `utter-project/EuroLLM-1.7B` (brak BoolQ); [Open LLM Leaderboard v2](https://huggingface.co/docs/leaderboards/open_llm_leaderboard/about) (sześć testów, BoolQ nie występuje); praca autorów (klasyfikator dostrajany, nie model bazowy do pobrania z protokołem 0-shot); pozostałe sześć modeli tabeli 3 TinyLlama (żaden nie leży ponad 2 SE nad bazą większościową, najwyżej Pythia-1.4B: 63,27, z = +1,30). <!-- liczba-spoza-wynikow: Zhang i in. 2024 v2, tabela 3; z wobec 0,6217, n = 3270 --> |
| Wynik informacyjny: autorzy | 80,4% wobec 90% ludzi i 62% bazy większościowej. Abstrakt nie podaje splitu. To nie jest kontrola etapu B. <!-- liczba-spoza-wynikow: abstrakt arXiv:1905.10044, odczyt 2026-11-03 --> |
| Wynik informacyjny: Pythia-1.0B | 57,83, 0-shot, kolumna `boolq` tabeli 3 TinyLlama. Rewizji praca nie podaje. Zadanie identyfikuje te wagi jako v1, nie `EleutherAI/pythia-1b-v0`. Nie do kontroli. <!-- liczba-spoza-wynikow: Zhang i in. 2024, tabela 3 --> |
| Pythia-1.0B wobec większościowej | różnica −4,34 pkt proc. <!-- liczba-spoza-wynikow: 57,83 minus 62,17, n założone 3270 --> |
| Pythia-1.0B: SE różnicy | 0,864 pkt proc., √(p(1−p)/3270), p = 0,5783. Baza jest stałą splitu, więc SE różnicy jest SE wyniku. <!-- liczba-spoza-wynikow: wyliczone --> |
| Pythia-1.0B: werdykt | z = −5,03, pewne: opublikowany wynik leży pod zawsze-„tak”. Nie odróżnia działającego kodu od stałej odpowiedzi „tak”. <!-- liczba-spoza-wynikow: różnica / SE --> |
| Train policy | `eval_only` dla `train`, `validation` i `test` |
| Decyzja treningowa | Słaby wynik znaczy, że wybór tak/nie po ustępie nie przebija odpowiedzi stałej „tak”. Nie mówi nic o polskim. Nie dodajemy pytań ani etykiet BoolQ do treningu. Ustępy są z Wikipedii, więc sam ustęp mógł być w pretreningu. To nie jest powód, żeby trenować na parach pytanie–etykieta. |
| Znane rozbieżności: lm-eval | Katalog `lm_eval/tasks/super_glue/boolq` jest identyczny w `6d2abda4` i w `v0.4.9.1`: `default.yaml` blob `1123761d…`, `seq2seq.yaml` blob `08211ec1…`, `t5-prompt.yaml` blob `b3ceb78d…`. Space używa `default.yaml` (T10, `definition` w `tasks_50.json`). Dwa pozostałe pliki to generacja, nie metryka decyzyjna. |
| Znane rozbieżności: zbiór | YAML ładuje `super_glue` / `boolq` bez rewizji. Ta karta przypina `aps/super_glue` @ `3de24cf`. |
| Znane rozbieżności: praca a lm-eval | Autorzy dostrajają model na train i liczą trafność klasyfikacji. lm-eval i Space liczą 0-shot log-prawdopodobieństwo słów `yes` i `no`. Tych liczb nie wolno zestawiać jako tego samego pomiaru. |
| Znane rozbieżności: kontaminacja | Pytania i ustępy są publiczne od 2019 roku. Ustępy pochodzą z Wikipedii. Korpusu Slayera nie skanowano. |
