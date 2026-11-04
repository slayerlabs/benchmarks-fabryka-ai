# Stan benchmarków

Jedna lista wszystkich benchmarków: co jest gotowe do tabeli na
[CodeSOTA „Under 1B”](https://beta.codesota.com/sub-1b), czemu brakuje niewiele, co ma tylko kartę oryginału, czego
nikt nie zaczął i które wyniki trzeba policzyć jeszcze raz. Stan na **4.11.2026**, z `main` i otwartych issues.

Kiedy benchmark jest skończony, mówi [METODOLOGIA, „Definicja „zrobione””](METODOLOGIA.md#definicja-zrobione). Kiedy
wchodzi do rankingu, mówi [LEADERBOARD.md, „Który test wchodzi”](LEADERBOARD.md#który-test-wchodzi). Typy i bazy:
[README, „Benchmarki i typy”](README.md#benchmarki-i-typy).

**Zmieniasz stan benchmarku (scalony PR, nowy wynik, nowe zastrzeżenie)? Przestaw jego wiersz w tym pliku w tym samym
PR.**

Skrót kolumn: **A** karta oryginału `ORIGINAL.md`, **B** odtworzenie `REPRODUCTION.md`, **C** kod i test w `tests/`,
**wynik** to wynik Slayera 1.06 w katalogu `results/`. ✓ jest, ✗ brak, ~ jest z zastrzeżeniem.

## Na skróty

| stan | ile | benchmarki |
|---|---|---|
| [✅ gotowe do tabeli](#gotowe-do-tabeli) | 3 | BLiMP (do sprawdzenia), EWoK, WinoGrande |
| [🟡 małe braki](#małe-braki) | 5 | EWoK-PL, PIQA, WSC273, WikiText-2, ARC-Easy |
| [📄 tylko karta oryginału](#tylko-karta-oryginału) | 8 | ARC-Challenge, BLiMP Supplement, BoolQ, HellaSwag, LAMBADA, OpenBookQA, SciQ, UncheatableEval |
| [🔨 w toku, bez katalogu](#w-toku-bez-katalogu) | 2 | LogiQA, MATH |
| [⬜ niezaczęte, z zadaniem](#niezaczęte-z-zadaniem) | 39 | karty #104–#138, testy Space bez wyniku, held-out |
| [⬜ niezaczęte, bez zadania](#niezaczęte-bez-zadania) | 27 | pozycje katalogu CodeSOTA bez issue i bez katalogu |
| [⚠️ wyniki do sprawdzenia](#wyniki-do-sprawdzenia) | 6 | BLiMP, MultiBLiMP, WSC273, WikiText-2, EWoK-PL, katalog CodeSOTA |

## Gotowe do tabeli

Spełniony warunek odtworzenia (etap B), kod z testem i wynik Slayera 1.06 obok modelu kontrolnego.

| benchmark | Space | A | B | C | wynik | co jeszcze |
|---|---|---|---|---|---|---|
| [BLiMP](benchmarks/blimp/README.md) | T01 | ✓ | ~ | ✓ | ✓ | ⚠️ [do ponownego policzenia](#blimp), do tabeli dopiero po sprawdzeniu; B spełniony przez lm-eval, kodem autorów (jiant) nie zrobiony, panel Space nie odtworzony |
| [EWoK](benchmarks/ewok/README.md) | | ✓ | ✓ | ✓ | ✓ | brak; wynik też dla pięciu modeli odniesienia |
| [WinoGrande](benchmarks/winogrande/REPRODUCTION.md) | T07 | ✓ | ✓ | ✓ | ✓ | katalog nie ma `README.md` z wynikiem; Slayer nie odróżnia się od stałej odpowiedzi (szum) |

## Małe braki

| benchmark | Space | A | B | C | wynik | czego brakuje | zadanie |
|---|---|---|---|---|---|---|---|
| [EWoK-PL](benchmarks/ewok-pl/README.md) | | `POLISH.md` ✓ | — | ✓ | ✓ | przetłumaczona 1 domena z 11; tłumaczenie bez przeglądu człowieka (`draft_review_required`) | |
| [PIQA](benchmarks/piqa/README.md) | T06 | ✗ | ✗ | ✓ | ✓ | liczona protokołem Space w wyjątku do 8.11; karta i odtworzenie | #57, #97 |
| [WSC273](benchmarks/wsc273/README.md) | T14 | ✗ | ~ | ✓ | ~ | karta; model kontrolny spoza listy źródeł METODOLOGII, więc wynik wstępny | #108, #97 |
| [WikiText-2](benchmarks/wikitext-2/README.md) | T03 | ✓ | ~ | ✓ | ~ | wspólny próg zgodności dla perpleksji; bez niego werdykt B jest nierozstrzygalny. Typ `ppl` idzie do osobnej kolumny, nie do meta-oceny | #15, #41 |
| [ARC-Easy](benchmarks/arc-easy/ORIGINAL.md) | | ✓ | ✗ | ✗ | ✗ | odtworzenie, kod, wynik; jest już SNR i bazy | #23 |

## Tylko karta oryginału

Jest `ORIGINAL.md`, nie ma odtworzenia, kodu ani wyniku. Następny krok to etap B.

| benchmark | Space | zadanie |
|---|---|---|
| [ARC-Challenge](benchmarks/arc-challenge/ORIGINAL.md) | T02 | #29, #49 |
| [BLiMP Supplement](benchmarks/blimp-supplement/ORIGINAL.md) | | #33 |
| [BoolQ](benchmarks/boolq/ORIGINAL.md) | T10 | #26 |
| [HellaSwag](benchmarks/hellaswag/ORIGINAL.md) | T05 | #24 |
| [LAMBADA](benchmarks/lambada/ORIGINAL.md) | T17 | #32 |
| [OpenBookQA](benchmarks/openbookqa/ORIGINAL.md) | T08 | #31 |
| [SciQ](benchmarks/sciq/ORIGINAL.md) | T09 | #30 |
| [UncheatableEval](benchmarks/uncheatable-eval/ORIGINAL.md) | | #35 |

## W toku, bez katalogu

| benchmark | Space | stan | zadanie |
|---|---|---|---|
| LogiQA | T18 | PR #139 (draft): wynik wstępny protokołem Space | #19, #97 |
| MATH | T34 | PR #141 (draft): karta oryginału | #125 |

## Niezaczęte, z zadaniem

Weź zadanie z [tablicy](https://github.com/orgs/slayerlabs/projects/10) i przypisz się. Karty z etykietą
`good first issue` nadają się na start.

**Karta oryginału (etap A):** COPA #105, CommitmentBank #106, WiC #107, RTE #109, ANLI #110, PROST #111, SST-2 #112,
PolEmo 2.0 #113, 8TAGS #114, Belebele PL #115, DYK #116, PPC #117, PSC #118, CBD #119, NKJP-NER #120, PolQA #121,
PoQuAD #122, MMLU #123, GSM8K #124, TruthfulQA #126, LLMzSzŁ #127, SQuAD 2.0 #128, DROP #129, RACE #130, CoQA #131,
NQ-Open #132, TriviaQA #133, MedMCQA #134, BIG-Bench Hard #135, PAWS #136, CoLA #137, ReCoRD #138, MultiBLiMP PL #104.

**Testy Space bez wyniku Slayera 1.06** (wyjątek #97 do 8.11): MathQA #28, PubMedQA #20, Social IQa #17, IFEval #40.

**Held-out:** NLL EN/PL/kod #22, część z kodem źródłowym #42.

## Niezaczęte, bez zadania

Pozycje [katalogu CodeSOTA](https://beta.codesota.com/api/sub1b/benchmarks) (`sub1b-catalog-v1`), dla których repo
nie ma katalogu ani issue. Zanim zaczniesz, załóż issue.

| grupa katalogu | benchmarki |
|---|---|
| liquid-reference | GPQA, GPQA Diamond, MMLU-Pro, IFBench, Multi-IF, MGSM, MMMLU, CaseReportBench, BFCL v3, BFCL v4, τ²-Bench Telecom, τ²-Bench Retail |
| math-reasoning | GSM-Symbolic, SVAMP, AIME 2025 |
| coding | HumanEval, HumanEval+, MBPP, MBPP+, LiveCodeBench |
| reading-context | RULER, LongBench v2 |
| trust-preference-multilingual | SimpleQA, WildBench, AlpacaEval 2.0 LC, MT-Bench |
| reasoning | ARC-AGI-1 |

## Wyniki do sprawdzenia

Wynik z tej listy nie idzie do tabeli, dopóki ktoś go nie sprawdzi i nie przestawi wiersza.

### BLiMP

Zgłoszenie z zespołu: wszystkie wyniki wychodzą około 80%, co wygląda podejrzanie. Policzyć jeszcze raz, drugą osobą,
na innym sprzęcie (ścieżka „recenzja i przeliczenie”, [CONTRIBUTING](../CONTRIBUTING.md)).

Co już jest w repo, żeby nie zaczynać od zera:

- [BLIMP.md](benchmarks/blimp/results/BLIMP.md): Slayer 1.06 i Pythia-1B są blisko siebie, a model kontrolny
  Pythia-1B v0 zgadza się z opublikowaną wartością i z lm-eval prawie na każdej parze.
- [CHECKPOINTS.md](benchmarks/blimp/results/CHECKPOINTS.md): checkpointy Slayera 1.00–1.06 rosną mało, wszystkie leżą
  w wąskim przedziale.

Co sprawdzić: wyniki per paradygmat (czy któryś stoi na 50% albo 100%, czy wzór paradygmatów u Slayera przypomina
Pythię), czy liczba z naszego kodu zgadza się z wynikiem lm-eval policzonym niezależnie, czy płaski przebieg
checkpointów nie bierze się z tego samego wejścia (te same wagi, ten sam plik wyników).

### MultiBLiMP (część polska)

W [analizie formatu odpowiedzi](analyses/answer-format/README.md) Slayer ma wynik bliski 100%, wyraźnie ponad Pythią.
Sprawdzić, czy zbiór nie jest w danych treningowych Slayera, zanim wynik pójdzie dalej. Karta: #104; wyciek danych:
#36.

### WSC273

Kontrola na `bloom-560m` mieści się w progu, ale pochodzi spoza listy źródeł METODOLOGII, a panel 200 i pełny split
dają różne liczby. Oba wyniki Slayera są wstępne ([REPRODUCTION.md](benchmarks/wsc273/REPRODUCTION.md)).

### WikiText-2

Wynik zgadza się ze Space, ale bez progu dla perpleksji werdykt etapu B jest nierozstrzygalny (#41, #15).

### EWoK-PL

Kontrole D3 spełnione, ale tłumaczenie obejmuje jedną domenę i czeka na przegląd człowieka
([POLISH.md](benchmarks/ewok-pl/POLISH.md)). Wynik jest wynikiem tej domeny, nie całego EWoK.

### Katalog CodeSOTA a repo

Statusy w katalogu nie zgadzają się z repo: ARC-Easy ma `full`, ARC-Challenge, HellaSwag, OpenBookQA i BoolQ mają
`pilot`, GSM8K i HumanEval `adapter_ready`, a w repo te testy mają najwyżej kartę oryginału. BLiMP, EWoK i WinoGrande,
gotowe w repo, mają `planned`. Ustalić, kto prowadzi katalog i skąd bierze statusy.
