# EWoK: Slayer 1.06, model kontrolny i pięć modeli odniesienia na pełnym zbiorze

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md): etap A to karta oryginału (`ORIGINAL.md`), etap B to
> odtworzenie opublikowanego wyniku kodem autorów (`REPRODUCTION.md`), etap C to nasz kod z testem zgodności, etap D
> to wersja polska tą samą metodą. Pojęcia (SE, werdykt, SNR): [słowniczek](../../METODOLOGIA.md#słowniczek).

EWoK (*Elements of World Knowledge*, Ivanova i in. 2024) sprawdza podstawową wiedzę o świecie z 11 domen. Rekord to
para minimalna 2×2: dwa konteksty C1, C2 i dwa zdania T1, T2, gdzie T1 pasuje do C1, a T2 do C2. Porównanie jest
trafione, gdy zdanie jest bardziej prawdopodobne po swoim kontekście niż po drugim. Wynik rekordu to średnia z dwóch
porównań. Baza losowa to 0,5. Liczymy na wszystkich 4374 rekordach `ewok-core-1.0` regułą kodu autorów:

- zapytanie `f"{context} {target}"` i kontekst tokenizowane z tokenami specjalnymi tokenizera, tak jak w `surprisal`
  (`add_special_tokens=True`);
- tokenizer, który sam dokleja BOS (Bielik, EuroLLM, LFM2.5), daje BOS przed kontekstem, a pozostałe (gpt2, Qwen3.5,
  LFM3, Slayer) nie dają żadnego;
- logit tokenu pad wyłączony przed softmaxem;
- wynik to suma log P zdania.

- Karta oryginału (etap A): [`ORIGINAL.md`](ORIGINAL.md)
- Odtworzenie kodem autorów na gpt2-xl (etap B) i zgodność naszego kodu (etap C): [`REPRODUCTION.md`](REPRODUCTION.md)
- Przepis (commity, modele, komendy, sprzęt): [`RECIPE.md`](RECIPE.md)
- Kod: [`ewok.py`](ewok.py) (`score` i `report`). Uruchomienie kodu autorów: [`reference/`](reference/).
- Liczby: [`results/ewok.json`](results/ewok.json) (modele i porównania),
  [`results/gpt2xl_comparison.json`](results/gpt2xl_comparison.json) (etapy B i C) i
  [`results/ewok_plain.json`](results/ewok_plain.json) (poprzednia reguła, bez tokenów specjalnych). Wyniki per
  rekord, bez tekstu: `results/<model>/ewok.jsonl.gz`.
- Testy: [`../../tests/test_ewok.py`](../../tests/test_ewok.py) (czyste funkcje, próbka syntetyczna) i
  [`../../tests/test_ewok_zgodnosc.py`](../../tests/test_ewok_zgodnosc.py) (zgodność z kodem autorów, 16 rekordów).
- Wersja polska: [`../ewok-pl/`](../ewok-pl/README.md). Liczy innym trybem (z BOS dla każdego modelu), więc jej liczb
  nie zestawiaj z tymi.

Materiały EWoK autorzy udostępniają tylko w zipach z hasłem i proszą, by nie publikować ich jawnym tekstem
(TERMS_OF_USE). W tym katalogu nie ma więc żadnego rekordu, tylko numery wierszy i liczby.

## Wyniki

Przebiegi z 2026-11-03, float32. n = 4374 rekordy, czyli 843 szablony. SE po szablonach i CI95 z bootstrapu po
szablonach: rekordy jednego szablonu (te same zdania z innymi imionami i obiektami) nie są niezależne. Remisów nie
było. Stały target to udział rekordów, w których model woli to samo zdanie po obu kontekstach. To odpowiednik
udziału najczęstszej predykcji.

| model @ rewizja | BOS od tokenizera | EWoK | SE (rekordy) | SE (szablony) | CI95 (szablony) | stały target |
|---|---|---:|---:|---:|---|---:|
| `speakleash/Bielik-1.5B-v3` @ `4b250496` | tak | 69,46% | 0,46 | 0,80 | 67,9–71,0 | 63,7% |
| `Qwen/Qwen3.5-0.8B-Base` @ `dc7cdfe2` | nie | 67,57% | 0,45 | 0,83 | 66,0–69,2 | 62,3% |
| `utter-project/EuroLLM-1.7B` @ `c730cd9b` | tak | 66,21% | 0,46 | 0,80 | 64,6–67,8 | 65,3% |
| `LiquidAI/LFM3-1.7B-Base` @ `545fc8f4` | nie | 65,96% | 0,46 | 0,77 | 64,5–67,5 | 68,3% |
| kontrola: `openai-community/gpt2-xl` @ `15ea56de` | nie | 65,36% | 0,45 | 0,82 | 63,8–67,0 | 66,0% |
| `LiquidAI/LFM2.5-1.2B-Base` @ `7453bca9` | tak | 61,29% | 0,44 | 0,68 | 60,0–62,6 | 68,4% |
| **`SlayerLab/Slayer1B-1.06` @ `ef81be58`** | nie | **58,97%** | 0,46 | 0,71 | 57,6–60,4 | 74,5% |

Slayer 1.06 minus model, różnica w parach na tych samych rekordach, w dwóch odczytach:

- **po szablonach:** te rekordy, SE z bootstrapu po 843 szablonach (SE K po szablonach nie da się policzyć z repo:
  id szablonu powstaje z tekstu rekordów, a tekstu EWoK nie publikujemy, TERMS_OF_USE);
- **po domenach:** 11 domen jako klastry, czyli średnia z 11 różnic domen, SE = sd / √11, t przy df = 10 i werdykt
  z p (progi |z| = 3 i 2). Ten odczyt pyta, czy różnica trzyma się dla innych domen, a nie tylko dla tych rekordów.
  Działa tak jak paradygmaty w `../blimp/`.
- **po Holmie:** p z wiersza (po szablonach z |z|, po domenach z t) poprawione metodą Holma w rodzinie sześciu
  porównań jednej kolumny; „tak” przy p Holma nie większym niż p dla |z| = 2, w nawiasie werdykt z p Holma (klucze
  `holm_by_template` i `holm_by_domain_clusters` w `results/ewok.json`, komenda `ewok.py holm`).

| model | po szablonach | SE | z | werdykt | po Holmie | po domenach | SE | t (df = 10) | p | werdykt | po Holmie | ustalone przed pomiarem |
|---|---:|---:|---:|---|---|---:|---:|---:|---:|---|---|---|
| gpt2-xl (model kontrolny) | −6,39 pkt | 0,78 | −8,15 | pewne | tak (pewne) | −5,67 pkt | 1,87 | −3,03 | 0,0126 | prawdopodobne | tak (prawdopodobne) | nie (eksploracyjne) |
| Bielik-1.5B-v3 | −10,48 pkt | 0,88 | −11,94 | pewne | tak (pewne) | −8,30 pkt | 1,96 | −4,23 | 0,0017 | pewne | tak (prawdopodobne) | nie (eksploracyjne) |
| Qwen3.5-0.8B-Base | −8,60 pkt | 0,85 | −10,09 | pewne | tak (pewne) | −6,94 pkt | 1,71 | −4,05 | 0,0023 | pewne | tak (prawdopodobne) | nie (eksploracyjne) |
| EuroLLM-1.7B | −7,24 pkt | 0,79 | −9,14 | pewne | tak (pewne) | −7,28 pkt | 1,63 | −4,47 | 0,0012 | pewne | tak (prawdopodobne) | nie (eksploracyjne) |
| LFM3-1.7B-Base | −6,98 pkt | 0,84 | −8,28 | pewne | tak (pewne) | −5,65 pkt | 1,38 | −4,11 | 0,0021 | pewne | tak (prawdopodobne) | nie (eksploracyjne) |
| LFM2.5-1.2B-Base | −2,32 pkt | 0,76 | −3,06 | pewne | tak (pewne) | −1,29 pkt | 1,21 | −1,06 | 0,3121 | szum | nie (szum) | nie (eksploracyjne) |

- **Odczyt po szablonach.** Na tych rekordach Slayer 1.06 jest wyraźnie (pewne) słabszy od modelu kontrolnego i od
  wszystkich pięciu modeli odniesienia, także po Holmie. Wobec LFM2.5 werdykt pewny leży na samym progu
  (z = −3,06). Po domenach i po Holmie żadne porównanie nie jest pewne: wobec pięciu modeli różnica jest
  prawdopodobna, a wobec LFM2.5 to szum (tabela wyżej), więc „słabszy od wszystkich” dotyczy tych szablonów, nie
  domen.
- **Stan treningu.** Slayer 1.06 to checkpoint z ok. 1/8 treningu, bez wygaszania LR. Wszystkie modele, z którymi
  go tu porównujemy, są po pełnym treningu, więc różnice mówią o tym checkpoincie, nie o gotowym Slayerze.
- **Odczyt po domenach.** Różnica do gpt2-xl jest tylko prawdopodobna (t = −3,03). Opiera się na kilku
  domenach z dużą różnicą, głównie społecznych (tabela niżej). Różnica do LFM2.5 to po domenach szum.
- **Stały target.** Slayer ma najwyższy udział stałego targetu (74,5%). Częściej niż inne modele wybiera to samo
  zdanie niezależnie od kontekstu, czyli idzie za priorem zdania, a nie za kontekstem. Bez porównania z wcześniejszymi
  checkpointami to hipoteza, nie wniosek.
- **Liczenie lokalne.** Pięć modeli odniesienia ma liczyć przebieg centralny. Te liczby policzyliśmy lokalnie, tym
  samym kodem, dla orientacji. Przebieg centralny ich nie zastępuje.

### Slayer 1.06 minus gpt2-xl po domenach

SE po szablonach wewnątrz domeny. Werdykt per domena z z = różnica / SE; „po Holmie” w rodzinie 11 domen tej tabeli
(klucz `domains.*.holm` w `results/ewok.json`), wniosek o tabeli opiera się na tej kolumnie.

| domena | n | szablony | Slayer 1.06 | gpt2-xl | różnica | SE | z | werdykt | po Holmie |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| agent-properties | 1120 | 208 | 55,4% | 60,0% | −4,55 pkt | 1,69 | −2,70 | prawdopodobne | nie (szum) |
| material-dynamics | 780 | 137 | 66,7% | 72,3% | −5,64 pkt | 1,47 | −3,84 | pewne | tak (pewne) |
| material-properties | 124 | 25 | 60,5% | 59,3% | +1,21 pkt | 4,20 | 0,29 | szum | nie (szum) |
| physical-dynamics | 75 | 15 | 61,3% | 66,0% | −4,67 pkt | 7,03 | −0,66 | szum | nie (szum) |
| physical-interactions | 280 | 60 | 55,0% | 54,6% | +0,36 pkt | 3,16 | 0,11 | szum | nie (szum) |
| physical-relations | 415 | 147 | 49,9% | 54,6% | −4,70 pkt | 2,24 | −2,10 | prawdopodobne | nie (szum) |
| quantitative-properties | 190 | 36 | 66,3% | 74,2% | −7,89 pkt | 3,60 | −2,20 | prawdopodobne | nie (szum) |
| social-interactions | 175 | 30 | 71,4% | 81,4% | −10,00 pkt | 3,61 | −2,77 | prawdopodobne | tak (prawdopodobne) |
| social-properties | 185 | 32 | 65,7% | 81,9% | −16,22 pkt | 3,66 | −4,43 | pewne | tak (pewne) |
| social-relations | 785 | 120 | 56,7% | 70,8% | −14,14 pkt | 1,70 | −8,33 | pewne | tak (pewne) |
| spatial-relations | 245 | 33 | 56,7% | 52,9% | +3,88 pkt | 2,75 | 1,41 | szum | nie (szum) |

Po Holmie zostają trzy różnice pewne (social-relations, social-properties, material-dynamics) i jedna
prawdopodobna (social-interactions, na samym progu); agent-properties, quantitative-properties i physical-relations
przechodzą w szum. W czterech domenach
(material-properties, physical-dynamics, physical-interactions, spatial-relations) różnica to szum, a Slayer ma w
nich wynik równy albo wyższy. Domeny są nierówne: od 75 do 1120 rekordów.

### Poprzednia reguła: bez tokenów specjalnych

Pierwsze przebiegi tego katalogu nie dawały BOS nigdy i nie wyłączały tokenu pad (`ewok.py score --rule plain`).
Dla modeli, których tokenizer sam dokleja BOS, to nie jest reguła autorów. Liczby z tamtych przebiegów
(`results/ewok_plain.json`), SE po szablonach:

| model | reguła `plain` | SE | reguła autorów | zmienione decyzje (z 8748) |
|---|---:|---:|---:|---:|
| LFM2.5-1.2B-Base | 54,76% | 0,78 | 61,29% | 3876 |
| EuroLLM-1.7B | 62,96% | 0,79 | 66,21% | 1650 |
| Bielik-1.5B-v3 | 69,01% | 0,79 | 69,46% | 1449 |

- Według reguły `plain` Slayer − LFM2.5 wynosiło +4,22 pkt (SE 0,86, z = 4,93, pewne). Reguła autorów odwraca znak.
  Liczba zmienionych decyzji pochodzi z porównania plików per rekord. Nie ma jej w `results/`.
- U modeli bez tokenów specjalnych zmienia się tylko maska pad: Slayer 8 decyzji, Qwen3.5, LFM3 i gpt2-xl 2 lub
  mniej. Wynik zostaje ten sam co do setnych części punktu.

### Model kontrolny wobec pracy (etap B)

Kod autorów na gpt2-xl daje u nas 65,47% (bf16, ustawienia autorów). Ich surowe wyniki z `data.zip` na tych samych
rekordach dają 65,59%, różnica mieści się w warunku ±2 pkt. Nasz kod regułą autorów w fp32 daje 65,36% i te same
decyzje co kod autorów w fp32 we wszystkich 8748 porównaniach. Szczegóły: [`REPRODUCTION.md`](REPRODUCTION.md).

## Ograniczenia

- Jeden przebieg na model (forward deterministyczny, bez próbkowania) na jednym GPU, RTX 5060 Ti. Kontrola między
  urządzeniami: niezrobiona.
- Środowisko naszego kodu to lokalne `.venv-gpu` z `transformers 5.19.0`, nie `common/requirements.lock.txt`.
  Tokeny specjalne biorą się z tokenizera w tej wersji. Kod autorów przypina `transformers 4.40.0`, w którym
  tokenizery LFM2.5, LFM3 i EuroLLM się nie ładują. Tam, gdzie oba się ładują (Bielik, Qwen3.5, gpt2-xl), doklejają
  te same tokeny.
- Slayera kod autorów nie załaduje (własny kod modelu). Reguła działa dla niego przez analogię: jego `tokenizer.json`
  nie dokleja tokenów specjalnych, a za pad bierzemy EOS `<|endoftext|>`, jak autorzy dla tokenizera bez pad.
- Ładowanie pięciu modeli HF sprawdził [`reference/check_loading.py`](reference/check_loading.py): bez brakujących i
  nieoczekiwanych kluczy, logity ścieżki scorera równe `model(ids).logits`. Wyniku tej kontroli nie zapisano do pliku.
  Slayer ładuje się przez `common/slayer_model.py`, sprawdzony wobec `load_slayer.py` (`../blimp/REPRODUCTION.md`).
- Szablony odtwarzamy heurystyką z `ewok.templates` (843). Autorzy nie publikują identyfikatora szablonu w
  `ewok-core-1.0`.
- Kontaminacja nie skanowana (kanarek EWoK w korpusie treningowym Slayera nie szukany).

## Co dodaje metodologia

Lista tego, czego ta praca jeszcze nie spełnia według [`METODOLOGIA.md`](../../METODOLOGIA.md). Każdy punkt to
osobne zadanie.

- [ ] Przebieg w środowisku z `common/requirements.lock.txt` (dziś `transformers 5.19.0` z `.venv-gpu`).
- [ ] Pięć modeli odniesienia z przebiegu centralnego zamiast przebiegu lokalnego.
- [ ] Zapis wyniku kontroli ładowania (`reference/check_loading.py --out`) dla każdego modelu.
- [ ] Skan kontaminacji: kanarek EWoK w korpusie treningowym Slayera.
- [ ] Wersja polska (etap D): przeliczenie `ewok-pl` regułą autorów i `POLISH.md`.
