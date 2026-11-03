# EWoK po polsku: wersja polska (etap D)

Procedurę i znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „D. Wersja polska (POLISH.md)”.

Oryginał: [`../ewok/`](../ewok/README.md). Tam są karta oryginału ([`ORIGINAL.md`](../ewok/ORIGINAL.md)) i
odtworzenie z porównaniem kodu ([`REPRODUCTION.md`](../ewok/REPRODUCTION.md)), czyli etapy A–C.

Ten katalog powstał przed metodologią (zadanie #34). Plik dopisuje etap D do pracy, która już istniała.

## D1. Przetłumaczyć czy napisać od zera

| | wartość |
|---|---|
| próbka 50 przykładów (jak losowana, seed) | `random.seed(20261103); random.sample(rekordy, 50)` z 625 rekordów PL. Oznaczał Claude (asystent AI) 2026-11-03. Autor tłumaczenia powinien to sprawdzić |
| niezależne od kraju i języka / uniwersalne / lokalne i kulturowe / językowe | 0 / 50 / 0 / 0 |
| uzasadnienie | Wszystkie 625 rekordów to domena `agent-properties`: postrzeganie (słyszeć, czuć), przekonania, intencje, wybór według preferencji, kosztu i wysiłku. To psychologia potoczna, wspólna dla kultur. Żaden rekord nie pyta o fakt z USA ani o zjawisko języka angielskiego. Imiona i część przedmiotów tłumaczenie zamieniło na polskie |
| decyzja | tłumaczenie |
| usunięte przykłady i powód | brak. Zbiór obejmuje rekordy `source_id` 0–624, czyli pierwsze 625 z 4374 rekordów `ewok-core-1.0` (tylko domena `agent-properties`). Pozostałych 10 domen jeszcze nie przetłumaczono |

## D2. Mapowanie metody

| element | decyzja |
|---|---|
| Metryka i agregacja | bez zmian: reguła LOGPROBS (target stały), średnia po rekordach. Dwie zmiany. (1) Remis log P liczymy jako 0, autorzy jako 0,5. W naszych przebiegach float32 remisów nie było (`../ewok/REPRODUCTION.md`). (2) Autorzy uśredniają najpierw każdą z 5 wersji zbioru, potem wersje. 625 rekordów PL to fragment zbioru z wieloma wersjami naraz, więc liczymy jedną średnią po rekordach. CI liczymy po szablonach (`README.md`, „Niepewność”) |
| Liczba opcji, liczba przykładów w prompcie | bez zmian: para 2×2, 0-shot |
| Normalizacja długości | bez zmian: brak. Po obu stronach porównania jest ten sam napis T, więc długość się skraca |
| Prompt | bez zmian w napisie: `C + " " + T`, jak `f"{context} {target}"` u autorów. **Zmiana: BOS.** Wersja 4 wyników (`results/raport_ewok_bos.json`) dawała jeden BOS przed kontekstem każdemu modelowi (METHOD.md Space). Wersja 5 (`results/raport_ewok.json`) liczy regułą autorów. Kod autorów daje BOS tylko wtedy, gdy dokleja go tokenizer (`add_special_tokens=True`), i wyłącza logit pad przed softmaxem. Na gpt2-xl tryb z BOS zmienia 15% decyzji, choć trafność prawie nie (`../ewok/REPRODUCTION.md`). Regułę autorów ma `../ewok/ewok.py --rule authors`, a `ewok.py licz` z tego katalogu woła ją domyślnie (`--regula autorow`). Tokenizery Bielika i Astera je doklejają: Bielik BOS, Aster BOS i EOS. U Astera EOS na końcu zapytania wchodzi w regule autorów do sumy zdania, a granica kontekstu przesuwa się o jeden token. Tak liczy kod autorów, ale trzeba to opisać przy wyniku |
| Precyzja | zmiana: float32 zamiast domyślnego bf16 autorów. W bf16 decyzje zależą od sprzętu i kolejności działań (`../ewok/REPRODUCTION.md`) |
| Dane (kto tłumaczył, jakim narzędziem, kto sprawdził próbkę, ile przykładów) | *dopisze autor tłumaczenia.* Plik ma status `draft_review_required` dla wszystkich 625 rekordów, a 580 z nich ma flagę przeglądu (np. `effort_preference_inference_review`). Listę rekordów do przeglądu (|EN − PL| ≥ 0,5) daje `analiza`, zob. `README.md` |
| Kontaminacja | nie sprawdzana. Polski zbiór nie jest w sieci jawnym tekstem (zip z hasłem, TERMS_OF_USE EWoK). Oryginał ma kanarki, a korpusu treningowego Slayera pod ich kątem nie skanowaliśmy |

## D3. Dwie kontrole przed pierwszym wynikiem

| | wartość |
|---|---|
| 1. kod wersji polskiej na danych oryginalnych | gpt2-xl na `ewok-core-1.0` (4374 rekordy), wyniki w `../ewok/REPRODUCTION.md`. Reguła autorów (`../ewok/ewok.py score`): 65,36% wobec 65,36% kodu autorów w fp32 i 65,47% w bf16 (etap B), 100% zgodnych decyzji. Reguła `plain` (bez tokenów specjalnych, `../ewok/ewok.py --rule plain`): 99,98%, ale na gpt2-xl nie widać różnicy z tokenami specjalnymi, bo jego tokenizer ich nie dokleja. Tryb domyślny (z BOS), którym liczono wyniki PL: 66,02%, w granicach ±2 pkt, ale tylko 85,45% zgodnych decyzji, poniżej progu 99% | <!-- liczba-spoza-wynikow: gpt2-xl na EWoK EN, benchmarks/ewok/results/gpt2xl_comparison.json (inna pula bramki) -->
| 2. bazy polskiego zbioru | losowa 0,5. Większościowa nie dotyczy: model, który zawsze woli ten sam kontekst albo to samo zdanie, dostaje dokładnie 0,5 |
| 2. model, który zna polski | `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333`: 66,0% EWoK, SE 2,3 pkt po szablonach (`raport_ewok.json`, `modele/Bielik-1.5B-v3/pl/ewok_po_szablonach`). To 7,0 SE nad bazą 0,5 <!-- liczba-spoza-wynikow: (66,0 − 50) / 2,27, policzone z raport_ewok.json --> |
| werdykt | Obie kontrole są spełnione. Wyniki w `raport_ewok.json` (wersja 5) liczy reguła autorów z `../ewok/ewok.py`, ta sama, która na gpt2-xl daje 100% decyzji zgodnych z kodem autorów. Wcześniejsze wyniki trybem z BOS dla każdego modelu są w `raport_ewok_bos.json` jako „dodatkowy sposób liczenia” z METODOLOGIA.md (etap C) |

Komendę i środowisko zapisujesz w [`RECIPE.md`](RECIPE.md).
