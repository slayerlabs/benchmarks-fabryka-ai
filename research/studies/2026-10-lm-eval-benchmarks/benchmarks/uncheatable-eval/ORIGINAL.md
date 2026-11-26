# UncheatableEval: karta oryginału (etap A)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „A. Karta oryginału (ORIGINAL.md)”. Gdy
czegoś nie da się ustalić, wpis brzmi „nieustalone” i podaje, gdzie szukano. Wszystkie odczyty: 2026-11-02.

UncheatableEval nie ma stałego zbioru. Autorzy co kilka miesięcy publikują nowe wydanie danych (na HF zbiory
`Jellyfish042/UncheatableEval-RRRR-MM`), a wyniki z różnych wydań nie są porównywalne. Ta karta opisuje jedno
wydanie: **`Jellyfish042/UncheatableEval-2026-07`** (teksty z 1–25 lipca 2026). To wydanie liczy praca autorów i ono
jest najnowsze w kolekcji HF w dniu odczytu. Metryka to BPB (bity na bajt), nie trafność.

## Co mierzy

Słowami autorów: „how well pretrained language models predict newly published text” (praca, sekcja 1). Model
traktuje się jak bezstratny kompresor: im mniej bitów potrzeba na zakodowanie świeżego tekstu (z ostatnich tygodni
przed wydaniem), tym lepiej model przewiduje tekst. Benchmark jest przeznaczony tylko dla modeli bazowych (README
repo: „designed to evaluate base models only”).

## Źródła

- Praca: Tan, Li, Shen, „Uncheatable Eval: Dynamic Compression-Based Evaluation of Language Models”, 2026,
  [arXiv:2609.27510v1](https://arxiv.org/abs/2609.27510) (23.09.2026, licencja CC BY 4.0). Czytana wersja HTML v1.
- Repo autorów @ commit: [`Jellyfish042/uncheatable_eval` @ `d2f07ae`](https://github.com/Jellyfish042/uncheatable_eval/tree/d2f07ae34241f0b409b7704f2da447778afbc9aa)
  (`d2f07ae34241f0b409b7704f2da447778afbc9aa`, 24.09.2026, licencja MIT). Ocena: `evaluator.py`, `eval_single.py`,
  `eval_multi.py`, `bos_mode_finder.py`; zbieranie tekstów: `crawlers/` (Scrapy: `ao3.py`, `arxiv.py`, `bbc.py`,
  `biorxiv.py`, `github.py`, `wikipedia.py`) i `crawlers/post_process.py`.
- Leaderboard: Space [`Jellyfish042/UncheatableEval`](https://huggingface.co/spaces/Jellyfish042/UncheatableEval/tree/778e3f1cd0b6483683b1ac040b7a5dd822a237c2)
  @ `778e3f1cd0b6483683b1ac040b7a5dd822a237c2` (31.10.2026). Tabela liczona w `data_manager.py` i `app.py` z plików
  wyników `data/2026-07/<model>-UncheatableEval-2026-07-<kategoria>-<data>.json`, które zapisuje `evaluator.py`.
- Zbiór HF @ rewizja: [`Jellyfish042/UncheatableEval-2026-07` @ `6588953`](https://huggingface.co/datasets/Jellyfish042/UncheatableEval-2026-07/tree/65889535d56aa38d448ce7e07b08e6e36c031545)
  (`65889535d56aa38d448ce7e07b08e6e36c031545`, 6.08.2026). Wcześniejsza rewizja tego samego wydania:
  `a2f82b681d155e73f84c9cb9dca5bde3a32ebb56` (27.07.2026); różnicę opisują „Dane” i „Znane rozbieżności”.
  Kolekcja wydań: [Jellyfish042/uncheatableeval](https://huggingface.co/collections/Jellyfish042/uncheatableeval).
- lm-eval: zadania `uncheatable_eval` nie ma ani w `6d2abda4`, ani w `v0.4.9.1` (pole „Znane rozbieżności”).

## Dane

### Split w pracy

- split: `test` wydania lipcowego 2026, 14 kategorii po 500 tekstów, razem 7000 tekstów (praca, sekcja 4.1). <!-- liczba-spoza-wynikow: Tan i in. 2026, sekcja 4.1, odczyt 2026-11-02 -->
- Praca nie liczy kategorii `ao3_nonenglish` (fikcja nieangielska), choć jest ona w zbiorze.
- Każdy tekst przycięto tak, by miał najwyżej 3584 tokeny w każdym z ośmiu tokenizerów (sekcja 4.1); listy tych tokenizerów praca nie podaje. <!-- liczba-spoza-wynikow: Tan i in. 2026, sekcja 4.1, odczyt 2026-11-02 -->

### Split w Space/repo

To wydanie nie jest w Space Slayera (nie ma go wśród 50 testów), więc „Space” znaczy tu leaderboard autorów.

- split: `test`, jedyny split zbioru; n w rewizji `6588953`: 7500 tekstów, 15 kategorii po 500 (HF datasets-server, `/statistics`). <!-- liczba-spoza-wynikow: datasets-server /statistics UncheatableEval-2026-07, odczyt 2026-11-02 -->
- Pełny split albo panel 200: pełny split; kod autorów liczy każdy tekst kategorii, bez próbkowania.
- Leaderboard liczy średnią z 14 kolumn: domyślnie odznacza `ao3 nonenglish` (`app.py`, `default_visible_columns`), więc zestaw kategorii jest ten sam co w pracy.
- Oceniane pole to `content` (tekst przycięty); `untruncated_content` jest tylko w danych (`evaluator.py`, `load_data_smart`).

Kategorie, źródła i daty tekstów w rewizji `6588953` (pole `date`, najwcześniejsza i najpóźniejsza; datasets-server
`/filter` po kategorii i dacie). Etykieta w nawiasie to skrót z tabeli 1 pracy. W każdej kategorii jest 500 tekstów.

| kategoria | źródło | daty tekstów |
|---|---|---|
| `ao3_english` (EF) | Archive of Our Own, fikcja angielska | 2026-07-18 – 2026-07-25 |
| `ao3_nonenglish` (poza pracą) | Archive of Our Own, fikcja nieangielska | 2026-07-02 – 2026-07-25 |
| `bbc_news` (News) | BBC News | 2026-07-22 – 2026-07-25 |
| `wikipedia_english` (EE) | Wikipedia angielska | 2026-07-10 – 2026-07-21 |
| `wikipedia_nonenglish` (NEE) | Wikipedie nieangielskie, próbkowanie zrównoważone po językach | 2026-07-01 – 2026-07-18 |
| `biorxiv_all` (Bio) | bioRxiv | 2026-07-01 – 2026-07-17 |
| `arxiv_cs` (CS) | arXiv, informatyka | 2026-07-07 – 2026-07-23 |
| `arxiv_math` (Math) | arXiv, matematyka | 2026-07-01 – 2026-07-23 |
| `arxiv_physics` (Phys) | arXiv, fizyka | 2026-07-03 – 2026-07-23 |
| `arxiv_other` (Sci-O) | arXiv, pozostałe dziedziny | 2026-07-01 – 2026-07-23 |
| `github_cpp` (C++) | GitHub, pliki C++ | 2026-07-03 – 2026-07-25 |
| `github_javascript` (JS) | GitHub, pliki JavaScript | 2026-07-01 – 2026-07-25 |
| `github_markdown` (MD) | GitHub, pliki Markdown | 2026-07-02 – 2026-07-25 |
| `github_python` (Py) | GitHub, pliki Python | 2026-07-04 – 2026-07-25 |
| `github_other` (Other) | GitHub, pliki w innych językach | 2026-07-01 – 2026-07-25 |

Obróbka tekstów (praca, sekcja 3.1): filtry jakości (za krótkie teksty, anomalie znaków), usuwanie bliskich
duplikatów (MinHash LSH), normalizacja Unicode NFC, przycięcie do wspólnego budżetu tokenów.

### Licencja

- licencja autorów: kod MIT (`LICENSE` w repo); licencji zbioru autorzy nie podają (karta zbioru ma tylko
  `dataset_info`, bez tekstu). Teksty pochodzą z serwisów o różnych licencjach (AO3, BBC, Wikipedia, arXiv,
  bioRxiv, publiczne repo GitHub); licencji poszczególnych tekstów nie sprawdzaliśmy.
- tag HF: brak (szukano w `cardData` API HF i w `README.md` zbioru @ `6588953`).
- ukryte odpowiedzi w teście: nie dotyczy, nie ma odpowiedzi. Cały tekst jest publiczny (kolumna `url` wskazuje źródło).

## Format zadania

Perpleksja (kompresja) całego dokumentu. Bez pytania, bez opcji, bez generacji.

## Prompt

Brak promptu. 0-shot. Model dostaje sam tekst `content`, tokenizowany bez tokenów specjalnych
(`add_special_tokens=False`), poprzedzony jednym tokenem startu zależnym od modelu (`bos_mode`, `evaluator.py`):
`add_default_bos` (token BOS tokenizera), `add_default_eos` (token EOS) albo `add_newline_token` (token „\n”);
warianty `replace_with_*` podmieniają pierwszy token tekstu. Tryb wybiera się dla każdego modelu skryptem
`bos_mode_finder.py`; README ostrzega, że BOS tokenizera nie zawsze jest właściwy. Przykłady z repo:
`Qwen/Qwen3-0.6B-Base` → `add_default_eos`, `HuggingFaceTB/SmolLM2-1.7B` → `add_newline_token`
(`eval_single.py`, `eval_multi.py` i pliki wyników leaderboardu).

Tekst dłuższy niż `chunk_size` = 4000 tokenów jest cięty na rozłączne okna; każde okno dostaje od nowa token startu i nie widzi poprzedniego okna. Przy tekstach przyciętych do 3584 tokenów w ośmiu tokenizerach cięcie zachodzi rzadko (tylko przy tokenizerach spoza tych ośmiu). <!-- liczba-spoza-wynikow: chunk_size w evaluator.py @ d2f07ae i limit tokenów z pracy, sekcja 4.1, odczyt 2026-11-02 -->

## Ocena

- Dla każdego tekstu: suma NLL wszystkich tokenów tekstu (strata tokenu startu nie wchodzi), w nats,
  `F.cross_entropy` na logitach rzutowanych do `bfloat16` (`calculate_log_sum`).
- Dla kategorii: `neg_log_prob_sum` = średnia NLL na tekst, `avg bytes` = średnia liczba bajtów UTF-8 tekstu.
  BPB = `neg_log_prob_sum / avg bytes / ln 2`, czyli suma NLL / suma bajtów / ln 2 (ważenie bajtami, praca, wzór 4).
- CR (compression rate, w procentach) = BPB / 8 × 100, czyli BPB × 12,5. Praca i domyślny widok leaderboardu <!-- liczba-spoza-wynikow: przelicznik CR = BPB / 8 × 100 z evaluator.py @ d2f07ae -->
  podają CR; leaderboard pokazuje też BPB i BPC (bity na znak) z tych samych plików (`data_manager.py`).
- Mianownik to bajty UTF-8 oryginalnego tekstu `content`, więc wyniki modeli o różnych tokenizerach są porównywalne.
- Normalizacji tekstu przy ocenie nie ma (NFC jest w przygotowaniu danych).
- Ustawienia przebiegów leaderboardu (pola plików wyników): `batch_size` 1, `enable_chunking` true,
  `torch_dtype` bfloat16, `attn_implementation` `flash_attention_2` (dla Qwen3-0.6B-Base i SmolLM2-1.7B).

## Metryka decyzyjna

**BPB całości**: średnia arytmetyczna nieważona BPB z 14 kategorii pracy (bez `ao3_nonenglish`), na wydaniu
2026-07. To wiersz „Overall” pracy podzielony przez 12,5 i kolumna „Average” leaderboardu przy metryce BPB z <!-- liczba-spoza-wynikow: przelicznik CR = BPB / 8 × 100 z evaluator.py @ d2f07ae -->
domyślnym zestawem kolumn. Niżej znaczy lepiej. BPB kategorii, CR i BPC są pomocnicze.

## Agregacja

- W kategorii: ważenie bajtami (suma NLL / suma bajtów), długie teksty ważą więcej.
- Między kategoriami: średnia nieważona, każda kategoria waży tyle samo (praca, sekcja 3.2: „unweighted arithmetic
  mean of the category rates”). Leaderboard robi to samo (`filtered_df[cols_for_average].mean(axis=1).round(3)`)
  i zaokrągla średnią do 3 miejsc.
- Wyjątek w pracy: analizy skalowania (sekcja 4.4) sumują NLL i bajty ze wszystkich kategorii, zanim liczą CR.
- Gdy model ma dwa pliki wyników tej samej kategorii, leaderboard je uśrednia (`pivot_table`, domyślnie `mean`);
  w wydaniu 2026-07 dotyczy to `Qwen2.5-7B`, `Qwen3.5-4B-Base` i `rwkv7a-g1d-0.1b`.

## Bazy

- losowa: dla BPB nie ma bazy zgadywania. Punktem odniesienia jest zapis bez modelu, 8 bitów na bajt (CR 100%, praca, wzór 3). Model jednostajny po słowniku zależy od tokenizera; nieustalone (praca i repo go nie podają). <!-- liczba-spoza-wynikow: definicja CR w pracy Tan i in. 2026, wzór 3 -->
- większościowa: nie dotyczy (nie ma odpowiedzi do wyboru).

## SNR

- źródło: tabela 5 pracy (dodatek A, 80 modeli, CR „Overall” na wydaniu lipcowym 2026); modele: 18 modeli z
  kolumną „Params.” od 0,5 do 2,0 mld (RWKV7-G1J-1.5B, Spark-X2.5-1.7B-Base, Qwen3.5-2B-Base, Qwen3-1.7B-Base,
  Qwen2.5-1.5B, Youtu-LLM-2B-Base, Falcon-H1-1.5B-Deep-Base, Llama-3.2-1B, Falcon-H1-1.5B-Base, SmolLM2-1.7B,
  stablelm-2-1_6b, Qwen3.5-0.8B-Base, MiniCPM5-1B-Base, Qwen3-0.6B-Base, gemma-3-1b-pt, RWKV7-G1D-0.4B,
  Qwen2.5-0.5B, Falcon-H1-0.5B-Base).
- rozrzut: odchylenie std. CR „Overall” między tymi 18 modelami (ddof=1) = 0,596 pkt CR. <!-- liczba-spoza-wynikow: policzone z tabeli 5 pracy Tan i in. 2026, odczyt 2026-11-02 -->
- rozrzut w BPB (ten sam rozrzut podzielony przez 12,5) = 0,0477. <!-- liczba-spoza-wynikow: policzone z tabeli 5 pracy Tan i in. 2026, odczyt 2026-11-02 -->
- SE: nieustalone. SE wymaga BPB pojedynczych tekstów, a nikt ich nie publikuje: pliki wyników leaderboardu mają
  tylko średnie kategorii (`track_single_sample_compression_rate` = false), praca nie podaje SE ani przedziałów,
  repo nie ma wyników per tekst (szukano w pracy, w `data/2026-07/` Space @ `778e3f1` i w repo @ `d2f07ae`).
  Etap B może je policzyć z własnego przebiegu (`track_single_sample_compression_rate=True`).
- iloraz: nieustalone, bo brak SE.

## Wyniki referencyjne (odczyt 2026-11-02)

Wydanie: `Jellyfish042/UncheatableEval-2026-07`. Leaderboard: Space `Jellyfish042/UncheatableEval` @ `778e3f1`,
okres „2026-07”, metryka „Bits Per Byte (BPB)”, domyślne kolumny (14, bez `ao3 nonenglish`). Pliki wyników nie
zapisują rewizji modelu (tylko `model_name_or_path`). Rewizja przy modelu niżej to pełny SHA commita `main` odczytany
z API HF (`/api/models/<model>/revision/main`) 2026-11-02: rewizja z dnia odczytu, nie potwierdzona rewizja
przebiegu. Ostatni commit `main` obu modeli jest starszy niż przebiegi leaderboardu (sierpień 2026), co tę rewizję
uprawdopodabnia, ale jej nie dowodzi.

- `Qwen/Qwen3-0.6B-Base` @ `da87bfb608c14b7cf20ba1ce41287e8de496c0cd` (rewizja z dnia odczytu, nie potwierdzona rewizja przebiegu; commit z 26.07.2025, licencja apache-2.0, bez bramki) → BPB całości 0,697 (leaderboard, kolumna „Average”). <!-- liczba-spoza-wynikow: Space Jellyfish042/UncheatableEval @ 778e3f1, data/2026-07, 14 plików Qwen3-0.6B-Base, odczyt 2026-11-02 -->
- Ten sam model w pracy: CR „Overall” 8,72% (tabela 5), czyli BPB 0,6976, zgodne z leaderboardem. <!-- liczba-spoza-wynikow: Tan i in. 2026, tabela 5, odczyt 2026-11-02 -->
- Ustawienia tego wyniku: `bos_mode` `add_default_eos`, `chunk_size` 4000, bfloat16, 0-shot, kod `evaluator.py`; przebiegi z 5–6.08.2026. <!-- liczba-spoza-wynikow: pola plików wyników Qwen3-0.6B-Base w data/2026-07 Space @ 778e3f1, odczyt 2026-11-02 -->
- `HuggingFaceTB/SmolLM2-1.7B` @ `effd688a12921b4cc83e3312b6feb579f70f9c71` (rewizja z dnia odczytu, nie potwierdzona rewizja przebiegu; commit z 6.02.2025, licencja apache-2.0, bez bramki) → BPB całości 0,673 (leaderboard). <!-- liczba-spoza-wynikow: Space Jellyfish042/UncheatableEval @ 778e3f1, data/2026-07, 14 plików SmolLM2-1.7B, odczyt 2026-11-02 -->
- Ten sam model w pracy: CR „Overall” 8,41% (tabela 5); `bos_mode` `add_newline_token`. <!-- liczba-spoza-wynikow: Tan i in. 2026, tabela 5, odczyt 2026-11-02 -->
- `EleutherAI/pythia-1b-v0` @ `step143000` (model kontrolny metodologii): brak wyniku; nie ma go ani w tabeli 5
  pracy, ani w `data/2026-07/` leaderboardu, a plik wyników Pythii v0 nie ma tego zadania.
  `utter-project/EuroLLM-1.7B`: też brak w tabeli 5 i w `data/2026-07/`; jego karty modelu pod tym kątem nie
  czytaliśmy (METODOLOGIA wymienia z niej tylko ARC-Challenge i HellaSwag). Dlatego wynik referencyjny bierzemy z punktu 3 listy („Model kontrolny etapu B”).

Warunek „kontrola odróżnia działający kod od zepsutego” (ponad 2 SE od bazy) jest sformułowany dla trafności; dla
BPB nie ma bazy zgadywania, a SE jest nieustalone (pole SNR). Próg zgodności dla BPB zapisuje etap B
(METODOLOGIA, „Próg dla perpleksji i BPB”). Uwaga dla etapu B: kategoria `wikipedia_english` w obu wynikach referencyjnych pochodzi z wersji tekstów, której
nie ma w żadnej rewizji zbioru na HF (pole „Znane rozbieżności”).

## Train policy

`eval_only`: żaden tekst wydania (`test`, jedyny split) nie trafia do treningu. Zbioru wolno użyć do dekontaminacji.
Benchmark ma sens tylko dla tekstów nowszych niż dane treningowe modelu, więc przy treningu Slayera na danych z
lipca 2026 albo nowszych to wydanie przestaje mierzyć uogólnianie.

## Decyzja treningowa

Wysokie BPB w kategorii znaczy, że model słabo przewiduje świeży tekst tego rodzaju (np. kod, prace naukowe,
nieangielska Wikipedia). Może wskazywać, których domen brakuje w danych pretreningu. Nie wolno z niego wnioskować o
umiejętnościach po dostrajaniu (benchmark mierzy tylko modele bazowe), o rozumowaniu ani o języku polskim (polski
jest najwyżej w części `wikipedia_nonenglish` i `ao3_nonenglish`, których składu języków nie sprawdzaliśmy). Nie
jest też powodem, żeby trenować na tych tekstach: wtedy wynik przestaje cokolwiek mierzyć. BPB porównuje się tylko
na tym samym wydaniu i tej samej rewizji zbioru.

## Znane rozbieżności

- **lm-eval**: katalogu `lm_eval/tasks/uncheatable_eval` nie ma w `6d2abda4` ani w `v0.4.9.1` (lista katalogów
  `lm_eval/tasks` przez API GitHub w obu wersjach), więc nie ma hashy blobów do porównania. Zadanie dodał później
  commit [`a966806`](https://github.com/EleutherAI/lm-evaluation-harness/commit/a966806e4d297615a3d1d58be55de3c0e2dc915d)
  (28.08.2026, „Add Uncheatable Eval (#3442)”), 286 commitów po `v0.4.9.1`. Różni się od kodu autorów:
  - grupa `uncheatable_eval` łączy 15 kategorii, z `ao3_nonenglish`, średnią ważoną rozmiarem (`weight_by_size: true`), a autorzy liczą średnią nieważoną z 14; <!-- liczba-spoza-wynikow: uncheatable_eval.yaml @ a966806 i praca, sekcja 3.2, odczyt 2026-11-02 -->
  - `loglikelihood_rolling` (`lm_eval/models/huggingface.py` @ `a966806`, `get_rolling_token_windows` z `context_len=1`) tnie tekst na okna o długości kontekstu modelu, a każde kolejne okno warunkuje jednym ostatnim tokenem poprzedniego; autorzy tną na rozłączne okna 4000 tokenów i każde zaczynają tokenem startu; <!-- liczba-spoza-wynikow: evaluator.py @ d2f07ae, odczyt 2026-11-02 -->
  - token startu pierwszego okna to w lm-eval `prefix_token_id` modelu (da się go podać w `model_args`), a u autorów token z `bos_mode`; przy innym tokenie startu BPB wychodzi inne;
  - YAML nie przypina rewizji zbioru (`dataset_path` bez `revision`).
  Etap B ma więc liczyć kodem autorów; lm-eval na `a966806` może służyć tylko jako druga implementacja.
- **Dwie rewizje zbioru, różna liczba kategorii**: rewizja `a2f82b6` (27.07.2026) ma 7000 tekstów w 14 kategoriach, bez `wikipedia_english`; rewizja `6588953` (6.08.2026) dokłada `wikipedia_english` i ma 7500 tekstów. <!-- liczba-spoza-wynikow: pliki parquet obu rewizji pobrane 2026-11-02, liczone pyarrow -->
- **Wersja `wikipedia_english` w wynikach nie jest na HF**: w `data/2026-07/` leaderboardu 82 przebiegi z 6.08.2026 (w tym Qwen3-0.6B-Base i SmolLM2-1.7B) mają w `wikipedia_english` 500 tekstów o średnio 3133,736 bajtu, a 28 przebiegów od 31.08.2026 ma 3263,522 bajtu. <!-- liczba-spoza-wynikow: pole avg bytes plików wikipedia_english w data/2026-07 Space @ 778e3f1, odczyt 2026-11-02 -->
  Rewizja `6588953` na HF ma w tej kategorii średnio 3263,522 bajtu (datasets-server `/filter`, 500 wierszy), więc odpowiada nowszym przebiegom. Kolumna EE pracy dla Qwen3-0.6B-Base (10,30) zgadza się z wersją 3133,736, której nie opublikowano. <!-- liczba-spoza-wynikow: datasets-server /filter i tabela 5 pracy, odczyt 2026-11-02 -->
  Skutek: „Average” leaderboardu miesza dwie wersje tej kategorii między modelami, a etap B nie odtworzy dokładnie
  kolumny EE i średniej z pracy. Pozostałe 14 kategorii (13 z pracy i `ao3_nonenglish`) ma w obu rewizjach HF ten
  sam tekst (porównany hash posortowanych tekstów każdej kategorii) i te same średnie liczby bajtów co w plikach
  wyników.
- Pliki zbioru pobrane 2026-11-02 (poza repo, w `bench-team/pobrane/`), SHA-256 zgodne z `lfs.oid` w API HF:
  `a2f82b6` → `7f9fc695ac2b4e3b7afc7fd4a7e783b5cb88f52cc469e7ddbcc766ee20fbb2ff`, `6588953` →
  `cfe75a73a1e647ecbec7d0fa41f15017843ce4263d4640cec81f43d22ae03e1b`.
- **README repo**: wykres „~14B models” pokazuje plik `assets/7b_cr.png` (ten sam co „~7B”); README i `about.md`
  odsyłają do `show_results_v2.ipynb`, a w repo jest tylko `show_results.ipynb`. Domyślne `bos_mode` w
  `EvaluationConfig` to `add_default_bos`, a przykłady w README używają `add_default_eos`.
- **Odczyt `bfloat16`**: strata liczona jest na logitach rzutowanych do `bfloat16` (wersja `float()` jest
  zakomentowana), więc inna precyzja w etapie B może dać nieco inne BPB.
- **Kontaminacja**: autorzy piszą wprost, że świeżość tekstu nie gwarantuje braku kontaminacji (praca, sekcja 6), a
  ryzyko rośnie z wiekiem wydania. Teksty są publiczne od lipca 2026. Daty `date` w części kategorii (arXiv,
  bioRxiv, AO3) mają tylko dzień, bez godziny. Korpusu treningowego Slayera nie skanowano pod kątem tych tekstów.
- UncheatableEval nie jest wśród 50 testów Space Slayera.
