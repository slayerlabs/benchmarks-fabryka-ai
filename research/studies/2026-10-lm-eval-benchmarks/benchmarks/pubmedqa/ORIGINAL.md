# PubMedQA: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpis brzmi „nieustalone” i podaje, gdzie szukano. Wszystkie źródła odczytano 2026-11-04.

| pole | wartość |
|---|---|
| Co mierzy | Odpowiadanie na pytania badawcze z biomedycyny na podstawie abstraktu: „answer research questions with yes/no/maybe … using the corresponding abstracts”. Kontekst to abstrakt bez wniosków, więc odpowiedź wymaga rozumowania nad treścią, często ilościową. |
| Źródła | praca: Jin, Dhingra, Liu, Cohen, Lu, „PubMedQA: A Dataset for Biomedical Research Question Answering”, EMNLP-IJCNLP 2019, [arXiv:1909.06146](https://arxiv.org/abs/1909.06146); repo autorów: [`pubmedqa/pubmedqa` @ `1cbae8e92f72f20c8d3747cbb3bf5bc53554d997`](https://github.com/pubmedqa/pubmedqa/tree/1cbae8e92f72f20c8d3747cbb3bf5bc53554d997); zbiór HF: [`bigbio/pubmed_qa` @ `15578e80ef02c2c9636d33fdd7eb6b05b987ba60`](https://huggingface.co/datasets/bigbio/pubmed_qa/tree/15578e80ef02c2c9636d33fdd7eb6b05b987ba60) (skrypt `pubmed_qa.py`, test z pliku autorów `pqal_test_set.json`); dane czytane z `refs/convert/parquet` @ `13a7d15476092370cbabb6475390e7e69b74d2f2`, `pubmed_qa_labeled_fold0_source/test/0000.parquet` (blob LFS `90cad3833e6de31072fb504e00e0fdb842788db8`) |
| Dane: split w pracy | PQA-L: 1000 pytań z etykietami ekspertów; test 500, pozostałe 500 w 10-krotnej walidacji krzyżowej (konfiguracje `fold0`–`fold9` w `bigbio/pubmed_qa`). Poza tym PQA-U (61,2 tys., bez etykiet) i PQA-A (211,3 tys., etykiety automatyczne). <!-- liczba-spoza-wynikow: Jin i in. 2019, streszczenie arXiv 1909.06146 --> |
| Dane: split w repo | split: `test` konfiguracji `pubmed_qa_labeled_fold0_source` (test PQA-L z pracy; YAML lm-eval `pubmedqa`: `test_split: test`); n: 500; przebieg centralny liczy pełny split (`results/central-run/pubmedqa/`). Informacyjnie: Space liczy panel `min(200, N)`. |
| Dane: licencja | licencja autorów: MIT (repo `pubmedqa/pubmedqa`); tag HF: `license:mit` (`bigbio/pubmed_qa` @ `15578e80`); ukryte odpowiedzi w teście: nie (test PQA-L ma etykiety w pliku autorów i w parquet HF). |
| Typ testu | [README, „Benchmarki i typy”](../../README.md#benchmarki-i-typy), wiersz `pubmedqa` |
| Format zadania i prompt | Wybór jednej z 3 odpowiedzi (`yes`, `no`, `maybe`). Pola: `QUESTION`, `CONTEXTS` (lista akapitów abstraktu bez wniosków), `LONG_ANSWER` (wnioski, w prompcie nie występują), `final_decision`. Praca nie ma promptu modelu językowego (modele dostrajane, BioBERT). lm-eval `pubmedqa` (`preprocess_pubmedqa.py`), 0-shot: kontekst `Abstract: {CONTEXTS złączone "\n"}\nQuestion: {QUESTION}\nAnswer:`, kontynuacja to `target_delimiter` (spacja) i słowo opcji: ` yes`, ` no` albo ` maybe`. Przykład (pierwszy wiersz `test`, cel `yes`): pytanie `Is anorectal endosonography valuable in dyschesia?`, kontynuacja ` yes`. |
| Ocena | Praca: trafność i macro-F1. lm-eval (`output_type: multiple_choice`): log-prawdopodobieństwo każdej z 3 kontynuacji, `acc` = argmax po sumie log P; YAML deklaruje tylko `acc`. Bez normalizacji tekstu odpowiedzi. |
| Metryka decyzyjna | `acc`: trafność, jak w pracy; jedyna metryka YAML-a lm-eval `pubmedqa`. `acc_norm` i `acc_mutual_info` repo liczy pomocniczo. |
| Agregacja i grupy | średnia po pytaniach, bez wag; bez grup. |
| Bazy | losowa: 1/3; stała odpowiedź: zawsze `yes`, 276 z 500 = 0,552 (rozkład celu: `yes` 276, `no` 169, `maybe` 55, z `probki/` przebiegu centralnego); b: 0,552. Praca podaje tę samą bazę większościową, 55,2%. <!-- liczba-spoza-wynikow: rozkład celu z results/central-run/pubmedqa/*/probki; 55,2% ze streszczenia arXiv 1909.06146 --> |
| SNR: źródło | Open Medical-LLM Leaderboard, pliki [`openlifescienceai/results` @ `62d7322cf11bf622399f7f54e5a7620ec6ef013d`](https://huggingface.co/datasets/openlifescienceai/results/tree/62d7322cf11bf622399f7f54e5a7620ec6ef013d/EleutherAI), 0-shot (`src/about.py` Space leaderboardu: „All results … zero-shot”). Wzięto tylko Pythię bez `-deduped` (1b, 1.4b, 2.8b; 410m w źródle nie ma). Innych modeli 0,4–3 mld z tego źródła (m.in. TinyLlama-1.1B, gpt-neo-2.7B, opt-2.7b, gemma-2b) nie wliczono. <!-- liczba-spoza-wynikow: rozmiary modeli w nazwach --> |
| SNR: 1b | 0,582 (SE 0,0221) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, EleutherAI/pythia-1b, results.pubmedqa --> |
| SNR: 1.4b | 0,594 (SE 0,0220) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, EleutherAI/pythia-1.4b --> |
| SNR: 2.8b | 0,640 (SE 0,0215) <!-- liczba-spoza-wynikow: openlifescienceai/results @ 62d7322c, EleutherAI/pythia-2.8b --> |
| SNR: rozrzut | odchylenie std. `acc` 3 modeli (ddof=1): 0,0306 (ddof=0: 0,0250). <!-- liczba-spoza-wynikow: 3 pliki Pythii w openlifescienceai/results @ 62d7322c --> |
| SNR: SE | SE A dla n 500: √(p̄(1−p̄)/n) = 0,0219, p̄ = 0,6053. <!-- liczba-spoza-wynikow: 3 pliki Pythii w openlifescienceai/results @ 62d7322c --> |
| SNR: iloraz | 1,40, poniżej progu 2. <!-- liczba-spoza-wynikow: 3 pliki Pythii w openlifescienceai/results @ 62d7322c --> |
| SNR: szum checkpointów | nieustalone: źródło ma tylko końcowe checkpointy; pliki Pythii v0 nie mają `pubmedqa`. |
| MDE | pełny split: 7,32 pkt; panel 200: 11,58 pkt (jedno porównanie, z_próg 2). SE różnicy: parowane Slayer 1.06 − LFM2.5-1.2B-Base, `acc`, z `probki/` przebiegu centralnego (0,0258 na 500 pytaniach; panel przeskalowany √(500/200)). <!-- liczba-spoza-wynikow: przeliczone z results/central-run/pubmedqa/*/probki, wzór z METODOLOGIA.md --> |
| Kontaminacja | znana: Space oznacza T44 dla Slayera 1.06 jako `contamination: flagged` (`results.json` Space @ `2d3d73f`). Dla modeli odniesienia nieznana (`unscanned` w `results.json` przebiegu). |
| Wyniki referencyjne (odczyt 2026-11-04) | Żaden z 5 modeli przebiegu centralnego nie ma opublikowanego wyniku 0-shot (karty modeli, plik Pythii v0, `openlifescienceai/results`). Opublikowane wyniki 0-shot innych modeli: `openlifescienceai/results` @ `62d7322c` (rewizja modelu w plikach: `main`, wersja lm-eval niezapisana). Lista w `REPRODUCTION.md`. |
| Wyniki referencyjne: praca | BioBERT (wieloetapowe dostrajanie) 68,1%, człowiek 78,0%. Inna metoda niż 0-shot, nie służy jako kontrola. <!-- liczba-spoza-wynikow: streszczenie arXiv 1909.06146 --> |
| Wyniki referencyjne: Space | brak: T44 ma w Space @ `2d3d73f` stan `not_run` dla Slayera 1.06 i dla LFM2.5-1.2B-Base. |
| Train policy | `eval_only`: żaden split PQA-L nie trafia do treningu. YAML ma `training_split: train` tylko jako źródło przykładów few-shot; liczymy 0-shot. |
| Decyzja treningowa | Niski `acc` znaczy, że model nie wyciąga z abstraktu odpowiedzi tak/nie/może. Wynik pod bazą większościową nie mówi o wiedzy medycznej, tylko o tym, że model myli kierunek odpowiedzi (`REPRODUCTION.md`, rozkład predykcji). Żaden z 5 modeli nie wybiera `maybe`, więc test nie mierzy rozpoznawania niepewności. Nie wolno trenować na PQA-L. Różnica w pkt, która zmieniłaby decyzję: nieustalona, więc MDE jest informacyjne. |
| Znane rozbieżności | lista niżej |

## Znane rozbieżności

- **lm-eval `6d2abda4`, `v0.4.8` i `v0.4.9.1`** (katalog `lm_eval/tasks/pubmedqa`): te same bloby we wszystkich
  trzech (`pubmedqa.yaml` `47de2fa0980a0a45facbab4416c80373e91e08d5`, `preprocess_pubmedqa.py`
  `0dccf9408a12ad5b1a0874ae9b8b0155e1db7ebf`, `README.md` `c738dd2af65eecaee764cbeaf6a74aea308a0547`). Space
  deklaruje `instrument: lm_eval_0.4.8`, repo ma przypięty `0.4.9.1`.
- **Źródło danych:** YAML czyta `bigbio/pubmed_qa` skryptem ładującym, bez rewizji. Repo czyta parquet
  `refs/convert/parquet` @ `13a7d154` przypięty w `common/zadania.py`, ten sam split `test` konfiguracji `fold0_source`.
  Test PQA-L jest wspólny dla wszystkich foldów.
- **Praca a lm-eval:** praca ocenia dostrajane klasyfikatory i podaje też macro-F1; lm-eval i Space liczą 0-shot,
  tylko `acc`, przez log-prawdopodobieństwo słowa odpowiedzi.
- **Kontaminacja:** zbiór jest publiczny od 2019 roku, abstrakty PubMed są powszechne w korpusach pretreningu.
