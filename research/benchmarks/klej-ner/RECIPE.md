# KLEJ NKJP-NER (T29): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `allegro/klej-nkjp-ner@bfae4047738b985bc2ad533d339dd89c3f7de00d` (wpis `T29` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie modele z `MODELE` i wszystkie zadania (lista etykiet wymaga `POMIN` z pominiętymi modelami); dla tego zadania woła `common/ewaluuj.py --zadania T29 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T29 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/klej-ner/<model>/results.json`

## Kontrola etapu B (`+pl`): model znający polski

Model i warunek zapisuje [`REPRODUCTION.md`](REPRODUCTION.md). Wyników jeszcze nie ma: wpis dostaje commit, sprzęt i datę po przebiegu centralnym.

- Model: `speakleash/Bielik-11B-v3.1-Instruct` @ `d6e755d356ad418d0f0e30b8c428db267415ddb9` (etykieta `bielik-11b-v3.1-instruct`, blok modeli porównawczych w `MODELE`), bez modelu zapasowego: gdy przebieg go pominie (repo z bramką zgody na HF), werdykt brzmi „bez kontroli: nierozstrzygnięte”. Liczy wszystkie zadania przebiegu, bez osobnego wpisu w `TESTY_MODELU`.
- Środowisko: `lock` (lm-eval 0.4.9.1, `common/requirements.lock.txt`), precyzja bfloat16 (pole `dtype` w wyniku).
- Zbiór: `allegro/klej-nkjp-ner@bfae4047738b985bc2ad533d339dd89c3f7de00d` (wpis `T29` w `common/zadania.py`), split `test`, n = 2058, 5-shot z banku przykładów. <!-- liczba-spoza-wynikow: wpis T29 w common/zadania.py i test.csv @ bfae4047 -->
- Komenda (w `research/`): linia przebiegu `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T29 ' | grep bielik-11b-v3.1-instruct`, czyli `common/ewaluuj.py --model hf --repo speakleash/Bielik-11B-v3.1-Instruct --revision d6e755d356ad418d0f0e30b8c428db267415ddb9 --model_path /workspace/modele/bielik-11b-v3.1-instruct --zadania T29 --probka pelna --device cuda --batch 1 --eval_gpu <GPU> --etykieta bielik-11b-v3.1-instruct --wyjscie /workspace/wyniki/klej-ner/bielik-11b-v3.1-instruct --dtype bfloat16` (nazwę GPU i katalog wag, przy kilku GPU z sufiksem `.gpu<N>`, ustawia przebieg).
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Commit kodu, sprzęt, data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/klej-ner/bielik-11b-v3.1-instruct/results.json` i próbki per pytanie w `probki/`; kontrola: `wobec_b` w `results_rozszerzone.json` (`common/ewaluuj.wobec_b`, czyli `tools/statystyka.wobec_stalej` na wynikach per pytanie z klastrami `sentence`, dodatnia różnica i t ≥ 2, `REPRODUCTION.md`), a wyniki pod b + 2 SE wypisuje `tools/kontrola_sensu.py` jako „at baseline level”.

## Smoke test przed przebiegiem

Wyrenderowane 2026-11-18 funkcjami repo, bez wag: `zadania.konfiguracje("T29", "hf")`, `ewaluuj.zbuduj_zadania`, `ewaluuj.ustaw_bank` dla pełnego splitu (członek `None`, więc klucz banku to `meta["task"]`, jak w linii 560 `common/ewaluuj.py`), potem `fewshot_context` lm-eval 0.4.9.1. Logprobu modelu nie ma, bo wag nie ładowano. Indeksy są od 0; pytania testu to pierwsze, ostatnie i trzy wylosowane `random.Random(0)` z pozostałych.

Bank (`train`, 15 794 wiersze): indeksy 5534, 830, 6003, 9774, 11354, złoto kolejno `time`, `placeName`, `noEntity`, `persName`, `persName`; dwa ostatnie wiersze to identyczne zdanie „Linko !”. Każde pytanie dostaje te same demonstracje w tej samej kolejności (prefiks kontekstu identyczny w pięciu pytaniach niżej). Demonstracja to prompt, spacja i nazwa rodzaju jednostki, demonstracje rozdziela `\n\n`; prompt pytania kończy się `Rodzaj:` bez spacji, a sześć kontynuacji to spacja i nazwa (`target_delimiter` spacja): ` Brak nazwanej jednostki`, ` Nazwa miejsca`, ` Nazwa osoby`, ` Nazwa organizacji`, ` Czas`, ` Nazwa geograficzna`. Długości opcji w znakach (do `acc_norm`): 23, 13, 11, 17, 4, 18. <!-- liczba-spoza-wynikow: ewaluuj.ustaw_bank i fewshot_context na test.csv i train.csv @ bfae4047, 2026-11-18 -->

- 0: krótkie zdanie o przychodni, która „dotkliwie odczuła” brak czegoś; `target` `noEntity`, czyli indeks 0 „Brak nazwanej jednostki”. Etykieta pasuje do treści (w zdaniu nie ma nazwy własnej). <!-- liczba-spoza-wynikow: test.csv @ bfae4047, wiersz 0 -->
- 2057: krótka wypowiedź z wykrzyknieniem i cudzysłowem w środku zdania; `noEntity`, indeks 0. Pasuje; to żywy przykład obserwacji o cudzysłowach z akapitu niżej. <!-- liczba-spoza-wynikow: test.csv @ bfae4047, wiersz 2057 -->
- 166: dłuższa wypowiedź o kompetentnych ludziach „w Platformie” i koalicji; `orgName`, indeks 3. Pasuje: platforma występuje w zdaniu jako nazwa organizacji. <!-- liczba-spoza-wynikow: test.csv @ bfae4047, wiersz 166 -->
- 1578: zdanie o zmianach w przepisach: spis substancji niebezpiecznych w magazynach, wspomniany „Kodeks pracy”; `placeName`, indeks 1. W NKJP tytuły aktów prawnych bywają etykietowane `placeName`, więc etykieta pasuje do wytycznych korpusu. <!-- liczba-spoza-wynikow: test.csv @ bfae4047, wiersz 1578 -->
- 1723: zdanie o entuzjastach wojny domowej organizujących obozy „w nim”; `placeName`, indeks 1. Miejsce wskazuje zaimek odnoszący się do kontekstu spoza zdania, więc złoto nie wynika z samego tekstu pytania; to cecha konstrukcji KLEJ (klasyfikacja typu encji ze zdania z kontekstu), nie błąd renderowania. <!-- liczba-spoza-wynikow: test.csv @ bfae4047, wiersz 1723 -->

Na całym splicie `test`: 2058 pytań, 0 pustych zdań, rozkład `target` 705 `placeName`, 500 `noEntity`, 372 `persName`, 237 `orgName`, 143 `time`, 101 `geogName`; każda etykieta należy do sześciu z YAML-a. Jest 2050 unikalnych zdań i 5 grup identycznych tekstów (13 wierszy: „TCZEW .” ×5 oraz po 2 wiersze w czterech innych grupach), etykiety zgodne w każdej grupie; to klastry `sentence` typu `mc +klastry +pl` (karta, „Agregacja i grupy”). 114 zdań ma `"` w środku, a szablon opakowuje zdanie w `"..."` bez escapowania, więc cudzysłowy zdania mieszają się z cudzysłowami szablonu (karta, „Znane rozbieżności”) — obserwacja, dane niepoprawione; 10 zdań testu (11 wierszy) występuje też w `train`, wszystkie `noEntity` (karta, „Kontaminacja”). Najdłuższe wejście (BOS, prompt z 5 demonstracjami, najdłuższa opcja) ma 926 tokenów Pythii (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5`, pytanie 1870), mediana 748, najkrótsze 716, więc żadne nie przekracza 4096 i `ewaluuj.ogranicz_kontekst` nie zdejmie demonstracji. Tokenizatora modelu kontrolnego (Bielik-11B-v3.1-Instruct, repo z bramką) nie liczono. <!-- liczba-spoza-wynikow: test.csv i train.csv @ bfae4047 oraz tokenizator Pythii @ f3f1b6d5, wyliczenie 2026-11-18 -->
