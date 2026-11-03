# PIQA (Space T06): protokół zapisany PRZED pomiarem

Tłumaczenie z angielskiego 2026-11-03, treść bez zmian; oryginał: commit 20e0129.

Zapisany 2026-11-01 dla zadania #16, zanim policzono jakiekolwiek log-likelihood PIQA dla Slayera 1.06 albo
Pythii-1B v0. Zacommitowany w gałęzi `research/piqa-slayer106` przed commitem z surowymi wynikami. Wariantu, progów i
tez niżej nie zmieniamy po zobaczeniu wyników. Wszystko, co dodane po pomiarze, raport oznacza jako
„eksploracyjne”.

Decyzja, której służy ten wynik: T06 w Space przestaje być `not_run` dla Slayera 1.06 (METODOLOGIA.md, „Wyjątek: 7
testów Space do 8.11”). Co już wiadomo: nic o Slayerze na PIQA; Pythia-1B v0 ma opublikowaną wartość.

## Co jest mierzone

- Dane: `ybisk/piqa` @ `2e8ac2dffd59bac8c3c6714948f4c551a0848bb0` (rewizja z `tasks_50.json` Space, wpis T06;
  to także czubek `main` z 2026-11-01). Repo ma skrypt ładujący, więc, jak mówi sekcja 8 METHOD.md, dane są
  czytane z automatycznie skonwertowanego parquetu: `refs/convert/parquet` @ `142c51238b3ca2bc61e9a075913871b8b600e8e1`,
  plik `plain_text/validation/0000.parquet`, sha256 `40e1677bba609c8801deacc171d76f3e24c083f365c95a1cbda7520c923dfea2`,
  1838 wierszy, kolumny `goal`, `sol1`, `sol2`, `label`. Żaden skrypt ładujący nie jest uruchamiany.
- Split `validation`, 0-shot, 2 opcje.
- Zadanie: `lm_eval/tasks/piqa/piqa.yaml`. Blob różni się między commitem Space `6d2abda4`
  (`1a34cc6670bffba45b9a2c3613cca7a60b37bb36`) a `v0.4.9.1` (`b147daea44b3bf3cd8f795be37dd3522f88afa3a`) tylko
  `dataset_path` (`piqa` wobec `baber/piqa`) i `dataset_kwargs: trust_remote_code: true` w `6d2abda4`;
  `README.md` to ten sam blob (`e0d7d05d99fee62fed27374e5cf9f2daee9032b8`). Prompt `"Question: {{goal}}\nAnswer:"`,
  opcje `[sol1, sol2]`, cel `label`, separator celu `" "`, metryki `acc` i `acc_norm` są identyczne.
  `piqa.py` przekazuje tę konfigurację do lm-eval 0.4.9.1 (lockfile `common/requirements.lock.txt`) z parquetem
  wyżej jako `dataset_path: parquet`. Dlatego `--tasks piqa` nigdy nie jest używane: czytałoby `baber/piqa`.
- Ustawienia jak w sekcji 2 METHOD.md: float32, batch 1, bez szablonu czatu, seedy (0, 1234, 1234, 1234). Wejścia są
  daleko poniżej 4096 tokenów. BOS: Slayer przez wrapper `slayer` z `common/slayer_lm.py` (#44), jeden BOS przed
  każdym żądaniem, jak w Space. Pythia przez `HFLM` z konwencją własnego tokenizera (BOS nie jest dodawany), jak
  harness z 2022 roku, który dał opublikowaną wartość.
- Modele: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`;
  kontrola `EleutherAI/pythia-1b-v0` @ `step143000`.
- Metryka główna: `acc_norm` (tasks_50.json T06). Raportowane także, bez użycia w żadnej tezie: `acc`, BPB
  poprawnej odpowiedzi, udział predykcji opcji 1. Format literowy (MC) nie jest liczony: protokół Space ocenia PIQA
  jako cloze, a pozostałe formaty należą do etapów A–C (#57).

## Panel (próbka Space) i pełny split

- Panel: `min(200, 1838)` = 200 wierszy, rosnący SHA-256 z `20261028|piqa|piqa|<source id>` (METHOD.md, sekcja 3;
  `benchmark_id` i `task` z tasks_50.json). Wiersze PIQA nie mają natywnego id, więc id źródła to SHA-256
  wiersza kanonicznego (JSON z posortowanymi kluczami, separatory `,` i `:`, UTF-8, cztery kolumny parquetu). Split
  walidacyjny nie ma wierszy identycznych bajtowo (1838 różnych), więc ordinal nie jest potrzebny. Space nie ma
  wartości T06 ani `source_id_digest` dla żadnego modelu, więc panelu nie da się sprawdzić względem Space; raport
  podaje skrót naszych id źródeł.
- Pełny split: wszystkie 1838 wierszy (`fullB` w METHOD.md). Oba pochodzą z jednego pełnego przebiegu (batch 1,
  każde pytanie oceniane niezależnie), panel jest podzbiorem.
- Dla każdego modelu i części: wartość, n, SE (odchylenie standardowe z próby / sqrt n), CI95 z bootstrapu
  percentylowego, 10 000 powtórzeń, seed 20261028 (METHOD.md, sekcja 5).

## Bazy

- Losowa: 0,5.
- Większościowa: udział najczęstszej poprawnej opcji na tych samych pytaniach (pełny split: 928/1838 dla opcji 2,
  policzone z parquetu przed jakimkolwiek przebiegiem modelu).
- Udział najczęstszej predykcji modelu (sprawdzenie stałej predykcji).

## Kontrola (próg ustalony tutaj)

- Opublikowana: Pythia-1B v0 step143000, acc 0,7040, acc_norm 0,7051, n 1838, z
  `EleutherAI/pythia@a19eecb807ec2c79a39ebf18108816e6ffffc1d5`,
  `evals/pythia-v0/pythia-1b/zero-shot/pythia-1b-0shot-global_step143000_eval_results_11-28-2022-15-14-35.json`
  (lm-eval z 2022 roku, piqa w wersji 0, przebieg NeoX w fp16).
- Rozróżnia: 0,7051 leży daleko ponad 2 SE (SE 0,0106) nad bazą losową 0,5 i większościową 0,5049.
- Zaliczona, gdy nasza Pythia na pełnym splicie mieści się w tolerancji dla OBU metryk, acc i acc_norm. Tolerancja =
  max(2 pkt, 2 × opublikowane SE) = 2,13 pkt dla acc i 2,13 pkt dla acc_norm (tu 2 SE > 2 pkt). <!-- liczba-spoza-wynikow: próg protokołu ustalony przed pomiarem -->
- Poza tolerancją: stop, żadna wartość Slayera nie wychodzi, chybienie idzie jako komentarz do #16.

## Tezy i jak się je obala

- Werdykty: z = różnica / SE; |z| ≥ 3 „pewne”, 2–3 „prawdopodobne”, < 2 „szum”.
- C1 (główna): acc_norm Slayera 1.06 na pełnym splicie jest ponad bazą losową. Obalona, gdy z = (wartość − 0,5) /
  SE < 3. Ten sam test raportowany wobec bazy większościowej, a oba także na panelu (panel z n 200 rozstrzyga tylko
  różnice rzędu 7 pkt).
- C2: Slayer 1.06 minus Pythia-1B v0, acc_norm, te same pytania, SE parowane (odchylenie standardowe różnic per
  pytanie / sqrt n), na pełnym splicie i na panelu. Kierunku nie zakładamy z góry; werdykt raportujemy taki, jaki
  wyjdzie. Pewna różnica nie wskazuje swojej przyczyny: Slayer to checkpoint z około 1/8 planu, bez wygaszania LR, z
  około 10% angielskiego w danych.
- Space oznacza T06 dla Slayera 1.06 jako skażony (`contamination: flagged`, potwierdzenie
  `bc6c168cf6ef35bce80b70f3bf582853526b558cb7f37e30101e35f3c2342de7`). Nie mamy korpusu treningowego, więc nie
  możemy policzyć wartości bez trafień; nasze liczby są na pełnej próbce i raport to mówi.

## Porównanie GPU (koszt, nie wyniki)

Ten sam przebieg Pythii na pełnym splicie na 2–3 typach GPU. Zapisujemy: cenę za godzinę przed wynajmem, czasy
przygotowania, pobierania i liczenia, koszt. Wyniki główne to przebieg na pierwszym GPU; powtórzenia raportują tylko,
ile decyzji acc_norm różni się od niego i największą różnicę log-prawdopodobieństwa.
