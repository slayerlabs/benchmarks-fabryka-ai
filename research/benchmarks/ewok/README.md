# EWoK: Slayer 1.06, model kontrolny i pięć modeli odniesienia na pełnym zbiorze

> Praca idzie według [`METODOLOGIA.md`](../../METODOLOGIA.md): etap A to karta oryginału (`ORIGINAL.md`), etap B to
> odtworzenie opublikowanego wyniku kodem autorów (`REPRODUCTION.md`), etap C to nasz kod z testem zgodności, etap D
> to wersja polska tą samą metodą. Pojęcia (SE, werdykt, SNR): [słowniczek](../../METODOLOGIA.md#słowniczek).

EWoK (*Elements of World Knowledge*, Ivanova i in. 2024) sprawdza podstawową wiedzę o świecie z 11 domen. Rekord to
para minimalna 2×2: dwa konteksty C1, C2 i dwa zdania T1, T2, gdzie T1 pasuje do C1, a T2 do C2. Porównanie jest
trafione, gdy zdanie jest bardziej prawdopodobne po swoim kontekście niż po drugim. Wynik rekordu to średnia z dwóch
porównań. Baza losowa to 0,5. Liczymy metodą autorów (bez BOS, `f"{context} {target}"`, suma log P zdania) na
wszystkich 4374 rekordach `ewok-core-1.0`.

- Karta oryginału (etap A): [`ORIGINAL.md`](ORIGINAL.md)
- Odtworzenie kodem autorów na gpt2-xl (etap B) i zgodność naszego kodu (etap C): [`REPRODUCTION.md`](REPRODUCTION.md)
- Przepis (commity, modele, komendy, sprzęt): [`RECIPE.md`](RECIPE.md)
- Kod: [`ewok.py`](ewok.py) (`score` i `report`). Uruchomienie kodu autorów: [`reference/`](reference/).
- Liczby: [`results/ewok.json`](results/ewok.json) (modele i porównania) i
  [`results/gpt2xl_comparison.json`](results/gpt2xl_comparison.json) (etapy B i C). Wyniki per rekord, bez tekstu:
  `results/<model>/ewok.jsonl.gz`.
- Testy: [`../../tests/test_ewok.py`](../../tests/test_ewok.py) (czyste funkcje, próbka syntetyczna) i
  [`../../tests/test_ewok_zgodnosc.py`](../../tests/test_ewok_zgodnosc.py) (zgodność z kodem autorów, 16 rekordów).
- Wersja polska: [`../ewok-pl/`](../ewok-pl/README.md). Liczy innym trybem (z BOS), więc jej liczb nie zestawiaj
  z tymi.

Materiały EWoK autorzy udostępniają tylko w zipach z hasłem i proszą, by nie publikować ich jawnym tekstem
(TERMS_OF_USE). W tym katalogu nie ma więc żadnego rekordu, tylko numery wierszy i liczby.

## Wyniki

Przebiegi z 2026-11-03, float32. n = 4374 rekordy, czyli 843 szablony. SE po szablonach i CI95 z bootstrapu po
szablonach: rekordy jednego szablonu (te same zdania z innymi imionami i obiektami) nie są niezależne. Remisów nie
było. Stały target to udział rekordów, w których model woli to samo zdanie po obu kontekstach. To odpowiednik
udziału najczęstszej predykcji.

| model @ rewizja | EWoK | SE (rekordy) | SE (szablony) | CI95 (szablony) | stały target |
|---|---:|---:|---:|---|---:|
| `speakleash/Bielik-1.5B-v3` @ `4b250496` | 69,01% | 0,46 | 0,79 | 67,5–70,6 | 64,3% |
| `Qwen/Qwen3.5-0.8B-Base` @ `dc7cdfe2` | 67,57% | 0,45 | 0,83 | 66,0–69,2 | 62,3% |
| `LiquidAI/LFM3-1.7B-Base` @ `545fc8f4` | 65,96% | 0,46 | 0,77 | 64,5–67,5 | 68,3% |
| kontrola: `openai-community/gpt2-xl` @ `15ea56de` | 65,36% | 0,45 | 0,82 | 63,8–67,0 | 66,0% |
| `utter-project/EuroLLM-1.7B` @ `c730cd9b` | 62,96% | 0,46 | 0,79 | 61,4–64,5 | 68,4% |
| **`SlayerLab/Slayer1B-1.06` @ `ef81be58`** | **58,97%** | 0,46 | 0,71 | 57,6–60,4 | 74,5% |
| `LiquidAI/LFM2.5-1.2B-Base` @ `7453bca9` | 54,76% | 0,48 | 0,78 | 53,2–56,3 | 72,7% |

Slayer 1.06 minus model. Różnica w parach na tych samych rekordach, SE po szablonach:

| model | Slayer − model | SE | z | werdykt | ustalone przed pomiarem |
|---|---:|---:|---:|---|---|
| gpt2-xl (model kontrolny) | −6,39 pkt | 0,78 pkt | −8,1 | pewne | nie (eksploracyjne) |
| Bielik-1.5B-v3 | −10,04 pkt | 0,84 pkt | −11,9 | pewne | nie (eksploracyjne) |
| Qwen3.5-0.8B-Base | −8,60 pkt | 0,85 pkt | −10,1 | pewne | nie (eksploracyjne) |
| LFM3-1.7B-Base | −6,98 pkt | 0,84 pkt | −8,3 | pewne | nie (eksploracyjne) |
| EuroLLM-1.7B | −3,99 pkt | 0,83 pkt | −4,8 | pewne | nie (eksploracyjne) |
| LFM2.5-1.2B-Base | +4,22 pkt | 0,86 pkt | 4,9 | pewne | nie (eksploracyjne) |

- Slayer 1.06 jest wyraźnie (z werdyktem pewnym) słabszy od modelu kontrolnego i od czterech z pięciu modeli
  odniesienia, a lepszy od LFM2.5-1.2B-Base.
- Slayer ma najwyższy udział stałego targetu (74,5%). Częściej niż inne modele wybiera to samo zdanie niezależnie od
  kontekstu, czyli idzie za priorem zdania, a nie za kontekstem.
- Pięć modeli odniesienia ma liczyć przebieg centralny. Te liczby policzyliśmy lokalnie, tym samym kodem, dla
  orientacji. Przebieg centralny ich nie zastępuje.

### Model kontrolny wobec pracy (etap B)

Kod autorów na gpt2-xl daje u nas 65,47% (bf16, ustawienia autorów). Ich surowe wyniki z `data.zip` na tych samych
rekordach dają 65,59%, różnica mieści się w warunku ±2 pkt. Nasz kod daje 65,36% i 99,98% decyzji zgodnych z kodem
autorów w fp32. Szczegóły: [`REPRODUCTION.md`](REPRODUCTION.md).

## Ograniczenia

- Jeden przebieg na model (forward deterministyczny, bez próbkowania) na jednym GPU, RTX 5060 Ti. Kontrola między
  urządzeniami: niezrobiona.
- Środowisko naszego kodu to lokalne `.venv-gpu` z `transformers 5.19.0`, nie `common/requirements.lock.txt`.
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
- [ ] Wersja polska (etap D): przeliczenie `ewok-pl` metodą autorów (bez BOS) i `POLISH.md`.
