# Protokół: Slayer 1B 1.09, krok 40 000, na 15 testach pełnego przebiegu 2026-11

Ustalony przed pierwszym wynikiem. Progów, wariantów i listy porównań nie zmieniamy po wynikach.
Etykieta wyniku: **„1.09, krok 40 000 (~61 mld), trening w toku, wynik wstępny”**. To checkpoint w trakcie
treningu (cel operacyjny 80 000 kroków), nie wersja przyjęta i nie następca 1.08.

## Pytanie

Jak checkpoint 1.09 z kroku 40 000 wypada wobec Slayera 1B 1.08 na tych samych 15 testach, tym samym kodem
i w tym samym środowisku co pełny przebieg 2026-11 (`research/results/full-run-2026-11/`).

## Modele

| etykieta | źródło | wagi |
|---|---|---|
| `slayer1b-1.09-k40000` | `SlayerLab/Slayer1B-1.09-checkpoints` @ `cff81fdcc05f0d91e9ba45b09fe78f769d7e0903`, plik `wagi_40000.pt` | sha256 `f83f7017872f7121f002bc77499c625304bd28e2c87fb4afaa0e3d445bd31881` (plik `SHA256SUMS` tej rewizji) |
| `slayer1b-1.08` | `SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c` | `weights_sha256` z `manifest.jsonl`: `1c510d9a59d3b9e62360d1db57e08fa450fb9b09df849df7f2eef132ea6715a4` |

- Etap treningu 1.09 w kroku 40 000: 18 863 257 682 + 40 000 × 1 048 576 − 114 627 128 ≈ 60,7 mld pozycji
  (wzór z `TRAINING_CONFIGURATION.md`, `SlayerLab/Slayer1B-1.09` @ `b25aec4ef6fb0c13717c5e5e27a426c572df54c6`).
  1.09 startuje z wag 1.08 @ `5f854a0c` (`--init-from`, nowy optymalizator).
- Wagi 1.09 idą tą samą drogą co checkpoint 1.07: konwersja `.pt` → `model.safetensors` poza runnerem
  (`research/slayer-1b/wygaszanie/konwertuj.py` albo równoważny kod z tego repo), `torch.load(..., weights_only=True)`,
  loader `slayer-ckpt` czyta `tools/ewaluacja/modele/slayer1b-1.09-k40000/model.safetensors`, a sha256 tego pliku
  trafia do `SUMY_WAG_CKPT` przed liczeniem.
- **Warunek startu:** architektura i tokenizer 1.09 równe 1.08 (20 warstw, szerokość 2048, słownik 32 768,
  tokenizer `0640d3bd`). Kształty wszystkich tensorów `wagi_40000.pt` porównane z wagami 1.08; każda różnica
  zatrzymuje pomiar przed wynajmem karty.

## Kod i środowisko

- Repo `slayerlabs/benchmarks-fabryka-ai`, gałąź `research/full-run-109-k40000` od `origin/main` @ `e051efe`.
  `research/common/ewaluuj.py` bez zmian względem przebiegu (sha w `manifest.jsonl`, pole `runner_sha256`).
- Runner `research/tools/ewaluacja/ewaluacja.py`, środowisko `lock` (`research/common/requirements.lock.txt`,
  lm_eval 0.4.9.1); EWoK własnym kodem testu (`ewok.py`), jak w przebiegu.
- float32, batch 1, pełne splity (`--probka pelna`), shoty jak w przebiegu (bez `--fewshot`), seed domyślny runnera.
- Jedna instancja vast.ai: RTX 4090 spoza CN (notatka `infrastruktura/wynajem-gpu-vast`, „Do czego które”),
  test 1 GB z HF po starcie. Obie etykiety liczone na tej samej instancji.

## Testy (15, jak w `manifest.jsonl` dla `slayer1b-1.08`)

| test | zadanie | metryka |
|---|---|---|
| ARC-Challenge | T02 | acc_norm |
| ARC-Easy | T51 | acc |
| BLiMP | T01 | acc |
| EWoK | T53 | ewok |
| HellaSwag | T05 | acc_norm |
| LAMBADA (OpenAI) | T17 | acc |
| MathQA | T19 | acc_norm |
| MedMCQA | T45 | acc |
| MultiBLiMP-PL | T04 | accuracy |
| PIQA | T06 | acc_norm |
| PubMedQA | T44 | acc |
| Social IQa | T46 | acc |
| WikiText-2 | T03 | byte_perplexity (SE i test na bits per byte) |
| WinoGrande | T07 | acc |
| WSC273 | T14 | acc |

## Kontrola narzędzia

Próbek per pytanie 1.08 z przebiegu nie ma w repo (paczka `eksport_glowny_pelny.tgz` leży poza nim), więc
porównanie parowane wymaga przeliczenia 1.08 na tej samej maszynie. 1.08 liczymy więc na wszystkich 15 testach;
każdy z nich jest jednocześnie kontrolą narzędzia.

- **Kontrola zgodna na teście:** n równe `manifest.jsonl` i |1.08 przeliczone − 1.08 z `manifest.jsonl`| ≤ 0,5 SE
  tego testu z `manifest.jsonl`. Raport podaje różnicę każdego testu, także zgodnej.
- **Kontrola niezgodna na teście:** werdykt porównania 1.08 → 1.09 na tym teście brzmi „nierozstrzygnięte
  (kontrola narzędzia)”, a liczby idą do raportu z tą adnotacją. Niezgodność na więcej niż 3 testach: cały wynik
  nierozstrzygnięty, raport mówi, co się rozjechało.
- Inna karta niż przebieg (RTX 5090) jest możliwym źródłem różnicy; raport nazywa ją wprost przy każdej niezgodności.

## Porównanie

- Δ = `slayer1b-1.09-k40000` − `slayer1b-1.08` (przeliczone na tej samej instancji), na tych samych pytaniach.
- SE Δ i statystyka tą samą metodą co `progresja.json` (`tools/ewaluacja/raport.py`, `porownaj`): parowane
  po pytaniach (z) albo po klastrach testu (t, df = k − 1): BLiMP po paradygmatach, WinoGrande po parach zdań,
  WSC273 po schematach, EWoK po szablonach; WikiText-2: Δ w byte perplexity, SE i t na bits per byte z dokumentem
  jako klastrem.
- Werdykt: |z| ≥ 3 „pewne”, 2–3 „prawdopodobne”, < 2 „szum”; t przez p przy tym samym progu.
- Poprawka Holma na rodzinę 15 porównań, m = 15 niezależnie od wyników (wiersze z SE = 0 i nieliczone też się liczą).
- Kierunek „lepiej”: wyżej dla accuracy, niżej dla byte perplexity.
- Wartości 1.08 w tabeli raportu: z `manifest.jsonl` przebiegu; przeliczone 1.08 służy tylko do Δ i kontroli.

## Warunki

- **Twierdzenie „1.09-k40000 lepszy od 1.08 na teście X”** stoi tylko przy Δ w kierunku „lepiej” i werdykcie
  „pewne” albo „prawdopodobne” po Holmie; „gorszy” symetrycznie. Reszta to „szum”, nie „brak różnicy”.
- **Główne twierdzenie raportu** to liczba testów lepszych, gorszych i w szumie po Holmie, z nazwami testów.
  Obala je: inny podział po przeliczeniu niezależnym kodem albo niezgodna kontrola narzędzia na teście z werdyktem.
- Porównanie dotyczy checkpointu w toku (ok. 60,7 mld pozycji, stały LR) z 1.08; nie mówi nic o modelu końcowym 1.09.
- Wartość 1,000 albo poniżej bazy losowej − 5 pkt to błąd kodu, nie wynik (sprawdzane na pełnych wynikach).

## Wykresy i raport

- Wyniki 1.09 w `research/results/full-run-2026-11/<test>/slayer1b-1.09-k40000/` w formacie reszty
  (`results.json`, `results_rozszerzone.json`, `scores-history-wiersz.csv`), wiersze w `manifest.jsonl`.
- Generator `tools/ewaluacja/raport.py`: wykres postępu wersji z parowanym porównaniem 1.08 → 1.09-k40000 i rankingi
  testów, 1.09 oznaczona na nich jako „w toku”. Animacja `przemiana-wersji.svg` i tabela CodeSOTA bez zmian.
- Ten katalog: protokół, `LICZBY.json` (jedyne źródło liczb raportu), `RAPORT.md` z generatora, kod, przeliczone
  wyniki 1.08 bez próbek, manifest sha256 surowych próbek.

## Budżet

Jedna instancja RTX 4090 spoza CN. Kolejka 30 par (2 modele × 15 testów) jednym procesem w tle. Limit 4 USD
i 6 h: bezpiecznik czasu i strażnik bezczynności na instancji (GPU < 5% przez 10 min przy pustej kolejce →
kopia wyników i zniszczenie) oraz lokalny timer `vastai destroy`. Na koniec zero instancji w
`vastai show instances` i koszt z `vastai show invoices`.

Zlecenie Ani 14.11.2026; zespół pomiaru: skill `zespol-benchmark`.

## Aneks przed pierwszym wynikiem (14.11.2026)

Dopisany przed wynajmem karty i przed jakimkolwiek wynikiem 1.09 na pełnym zbiorze. Ustala to, czego protokół wyżej
nie ustalał, i jedną zmianę decyzją Ani.

**Karta (zmiana, decyzja Ani 14.11 przed pomiarem).** Kryterium wyboru: najniższy szacowany koszt całego pomiaru
(cena/h × (start + pobranie wag + 15 testów 1.09 + przeliczenie 1.08)), przy różnicy do ok. 20% karta, która skończy
szybciej; spoza CN; po starcie pobranie 1 GB z HF w ok. 30 s, inaczej następna oferta; jedna instancja naraz. Zamiast
RTX 4090 bierzemy **RTX 5090** (oferta spoza CN o najniższej cenie/h w chwili wynajmu). Uzasadnienie z danych: pary
1.08 na RTX 5090 w `manifest.jsonl` to razem 5176 s przy 2 procesach na kartę; czasu RTX 4090 przy batch 1 w repo nie
ma (pomiar `results/central-run/times_rtx4090.jsonl` był z batch auto), a ewaluacja batch 1 modelu 1B w float32 czyta
całe wagi w każdym forwardzie, więc RTX 4090 (mniejsza przepustowość pamięci) jest wolniejsza; szacunek kosztu obu
kart wychodzi w granicy 20%, więc wygrywa szybsza. Druga korzyść: ta sama karta co pełny przebieg, więc kontrola
narzędzia (1.08 przeliczone − manifest) nie miesza się z różnicą sprzętu. Obraz `pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime`
(jak pomiar `bos-window-check/` na RTX 5090).

**Równoległość.** `ewaluacja.py licz ... --rownolegle 4`: tyle procesów, ile mieści 32 GB karty według szacunku runnera
(`szacunek_vram` z rozmiaru wag z zapasem na proces, budżet = pamięć karty minus zajęte i zapas `--zapas-vram`;
WikiText liczony sam). Każdy proces
liczy swoje pytania po kolei w batch 1, więc liczba procesów nie zmienia wyniku pytania; pełny przebieg miał 2.

**Konwersja wag.** `slayer-1b/wygaszanie/konwertuj.py` z `--sha256 f83f7017…`, wzorzec `SlayerLab/Slayer1B-1.08` @
`5f854a0c` (1.09 kontynuuje 1.08; ten sam config architektury i `tokenizer.json` sha256 `0640d3bd…`). Na Macu przed
wynajmem: `code/sprawdz_architekture.py` (202 tensory checkpointu = 201 tensorów 1.08 + `head.weight` wiązany z
`tok.weight`, wszystkie kształty równe, config architektury równy, różni się tylko `data_seed`), konwersja daje
`model.safetensors` sha256 `5d60d691f1ea87db4a900788ff253f2de55e75f9210c93e7e95f3b9f6c434591`, wpisane do
`SUMY_WAG_CKPT`. Na instancji ta sama konwersja (`code/kolejka.sh`); runner odmawia liczenia, gdy suma wyniku konwersji
jest inna.

**Przebieg na instancji.** `code/start_zdalny.sh` → `tools/przebieg_centralny.sh przygotuj <limit>` (bezpiecznik z
limitem 6 h od wynajmu, strażnik bezczynności, test 1 GB z HF, środowisko `lock`) → `code/kolejka.sh`: obie etykiety,
`--zadania gotowe` (15 testów z tabeli wyżej), `--probka pelna`, `--pobierz`, potem `ewaluacja.py eksport` z próbkami
per pytanie. Kod na instancji to `git archive` commitu, który zawiera ten aneks. EWoK: zbiór gated, na instancji nie
ma tokenu HF, więc plik `ewok-core-1.0` @ `34d912a6` jedzie z lokalnego cache HF (ta sama przypięta rewizja, którą czyta
`ewok.py`).

**Liczby.** `code/liczby_109.py` (z surowego eksportu, po sprawdzeniu sha256 każdego pliku wobec `probki_sha256.json`
zapisanego przed raportem) → `LICZBY.json` → `code/raport_md.py` → `RAPORT.md`. Holm: `statystyka.holm(ps, m=15)`;
wiersz bez p (SE = 0) liczy się do m i dostaje „nierozstrzygalne”. Kontrola narzędzia w skali pliku wyników
(MultiBLiMP w procentach, jak w manifeście). Kontrola sensu: `tools/kontrola_sensu.py` (`bledy_obserwacji`) na każdym
pełnym wyniku obu etykiet. Seed: domyślny `ewaluuj.py`/`ewok.py` (jak w przebiegu).

**Niezależne przeliczenie.** `code/przelicz_niezaleznie.py` liczy Δ i SE z plików próbek własnym kodem (bez importu
`raport.py`, `metryki.py` i `statystyka.py`); podział lepsze/gorsze/szum różny od `LICZBY.json` obala główne twierdzenie.
