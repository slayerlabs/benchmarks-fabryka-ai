# Rejestr datasetów: użyte i kandydaci

Jedno miejsce na pytanie „czy ten zbiór już był?” przy pracy nad danymi Slayera 1B.

Zasady wpisu:

- **status**: `użyty` (jest w treningu któregoś modelu), `kandydat` (czeka na test), `wstrzymany`
  (czeka na wyjaśnienie). Odrzucone stoją osobno, w sekcji 4.
- **licencja**: tak, jak podaje karta zbioru; „niesprawdzone” znaczy, że nikt jej nie potwierdził u
  źródła.
- **data**: dzień decyzji (dla `użyty`: dzień zapisu w manifeście).
- Kandydat przechodzi na `użyty` dopiero po teście z progiem z góry (protokół: `wygaszanie/PROGI.md`).

## 1. Slayer 1B — `SlayerLab/slayer-pl-8x3b` (użyte przez Arka)

Proporcje scenariusza B z karty zbioru (tak samo w `wygaszanie/dane.py`). Skład komponentów z karty;
licencje per komponent nie były sprawdzane u źródła.

| nazwa HF/URL | licencja | status | powód | data |
|---|---|---|---|---|
| `SlayerLab/slayer-pl-8x3b` → `web` (HPLT v3 PL, top WDS, pakiety `pack-NN`) | wg karty zbioru; HPLT publikuje jako CC0 z procedurą usuwania (niesprawdzone) | użyty | 63% tokenów Slayera 1.06; nakłada się z FineWeb2/FineWeb2-HQ pol, więc każdy kandydat z Common Crawl wymaga dedupu wobec HPLT | 2026-10-30 |
| `SlayerLab/slayer-pl-8x3b` → `core` / `core_sa` (wikipedia, wikibooks, wikivoyage, wikisource, polqa, govpl, wolne_lektury) | CC-BY / CC-BY-SA (per źródło) | użyty | 19%; polqa w rdzeniu kontaminuje test PolQA (7/200 pytań bez trafień); govpl może zawierać dane wrażliwe: karta [polish-dynaword](https://huggingface.co/datasets/SlayerLab/polish-dynaword) mówi, że filtry nie usuwają w pełni danych osobowych, a przebieg PII (NERGAL) dopiero w v0.2.7; do tego czasu obowiązują datasheety poszczególnych źródeł (do przeczytania) | 2026-10-30 |
| `SlayerLab/slayer-pl-8x3b` → `legal` / `legal_sa` (eurlex, parliamentary, dziennik_ustaw, govpl) | CC-BY-4.0 / PD / CC-BY-SA (govpl), wg `dataset.json` | użyty | 8%; dane wrażliwe jak przy `core` (brak przebiegu PII przed v0.2.7 polish-dynaword); wg karty eurlex ma licencję `LicenseRef-EU-Reuse-Policy` (nie CC-BY-4.0), a parliamentary zostawia tylko oficjalnych mówców, interpelacje wstrzymane do v0.2.7 | 2026-10-30 |
| `SlayerLab/slayer-pl-8x3b` → `en` | ODC-BY (wg karty) | użyty | 10%; wg `dataset.json` zbioru to fineweb-edu + finemath (ODC-BY), 2,40 mld tok.; dekontaminacja opisana tylko dla web i tylko wobec 8tags/polemo2; wg Arka (30.10) wobec ARC była na pewno, wobec MMLU nie jest pewien, do sprawdzenia (zadanie A2) | 2026-10-30 |

## 2. Kandydaci

| nazwa HF/URL | licencja | status | powód | data |
|---|---|---|---|---|
| `epfml/FineWeb2-HQ` (`pol_Latn`) | ODC-BY | kandydat | rozumowanie naukowe i wiedza (ARC-C, MMLU, LLMzSzŁ); ~13-20 mld tok.; wymaga dedupu wobec HPLT i 13-gramów wobec arkuszy CKE | 2026-10-30 |
| `HuggingFaceFW/fineweb-edu` (próg ≥4) | ODC-BY | użyty w Slayerze | już jest w 10% EN Slayera (`dataset.json`); nowy kandydat tylko jako wyższy udział albo ostrzejszy próg, nie jako nowe źródło | 2026-10-30 |
| `HuggingFaceTB/smollm-corpus` → `cosmopedia-v2` | ODC-BY | kandydat | syntetyczne podręczniki EN (Mixtral), ~28 mld tok. (niesprawdzone); karta v2 nie podaje dekontaminacji, ryzyko halucynacji i monotonnego stylu | 2026-10-30 |
| `common-pile/pubmed` | CC BY / CC BY-SA / CC0 (tylko te rekordy) | kandydat | wiedza medyczna (MedMCQA, PubMedQA); abstrakty testu PubMedQA wyciąć 13-gramami; przed użyciem skan PII medycznego (np. Philter, Presidio), bo karta nic o tym nie mówi; niski priorytet przy 1B | 2026-10-30 |
| `allenai/soda` | CC BY 4.0 | kandydat | dialogi i intencje (Social IQa, PoLEMo2); wysokie ryzyko kontaminacji: SODA i SIQA powstały z ATOMIC, ocena transferu na innym zbiorze | 2026-10-30 |
| Pakiet podręczników PL: `polish-dynaword` → `wikibooks` + `open_agh_chemistry` + ZPE | CC-BY/CC-BY-SA; ZPE niepotwierdzona (licencja per zasób) | kandydat | wiedza szkolna PL; wikibooks już użyty (tylko podniesienie wagi); ZPE dopiero po potwierdzeniu licencji i dedupie wobec LLMzSzŁ (zadania CKE); zakazu trenowania AI jak u OpenStax nie znaleziono: Wikibooks (warunki Wikimedia) i Open AGH (CC BY-SA 3.0/4.0, wersję wyjaśnić) bez klauzuli, regulamin ZPE bez wzmianki o AI/TDM, ale ogranicza użycie do celów edukacyjnych (§3 ust. 4); licencje pojedynczych zasobów ZPE, strony podręczników AGH i robots.txt/TDMRep niesprawdzone | 2026-10-30 |
| `SlayerLab/polish-dynaword` → `biblioteka_nauki` (podzbiór medyczny / akademicki) | per rekord | kandydat | wiedza akademicka i medyczna PL; sprawdzić, czy już jest w `core` Slayera | 2026-10-30 |
| Wiktionary PL (definicje + przykłady) | CC-BY-SA (niesprawdzone) | kandydat | znaczenie słowa (WiC); dopiero po kalibracji formatu, bo stałe predykcje WiC to format | 2026-10-30 |

## 3. Kandydaci z przeglądu 30.10

| nazwa HF/URL | licencja | status | powód | data |
|---|---|---|---|---|
| `HuggingFaceFW/finepdfs-edu` (`pol_Latn`) | ODC-BY | kandydat | edukacyjne PDF-y PL; rozmiar części PL do policzenia; dedup wobec arkuszy CKE i HPLT | 2026-10-30 |
| `Helsinki-NLP/fineweb-edu-translated` (pol) | ODC-BY | kandydat | MT tych samych dokumentów co EN fineweb-edu w Slayerze (wiedza ta sama, nowy tylko język) | 2026-10-30 |
| `Helsinki-NLP/nemotron-cc-translated` (pol) | niejasna: API CC0, upstream NVIDIA | wstrzymany | licencja do wyjaśnienia przed użyciem | 2026-10-30 |
| `PleIAs/SYNTH` | CC-BY-4.0 | kandydat | format QA + rozumowanie: ryzyko formatu, sprawdzić, czy zawiera MCQ | 2026-10-30 |
| `SKocur/polish-pre1918-corpus` | CC0 | kandydat | OCR; różnorodność polszczyzny | 2026-10-30 |
| `demelin/moral_stories` | MIT | kandydat | mały, pokrewny SIQA: ostrożnie (kontaminacja, format) | 2026-10-30 |
| `openbmb/Ultra-FineWeb` (EN) | Apache-2.0 | kandydat | filtrowany web EN; bez wariantu L3 | 2026-10-30 |

## 4. Odrzucone

Te zbiory zostały już sprawdzone i **odpadają z treningu**; lista jest po to, żeby nikt nie sprawdzał
ich drugi raz. Wracają tylko z nowym faktem (np. zgodą licencjodawcy). Kolumna **do testów**: „tak”
znaczy, że można na nim oceniać model (to pytania z benchmarku albo zbudowane z nich, więc trening
na nich zawyżałby wynik).

| zbiór | powód odrzucenia z treningu | do testów | data |
|---|---|---|---|
| OpenStax Polska (Fizyka t.1-3, Psychologia, Mikro/Makroekonomia) | strona zastrzega zakaz trenowania AI bez zgody OpenStax Poland | nie | 2026-10-30 |
| `joelniklaus/Multi_Legal_Pile` | licencja niekomercyjna (CC-BY-NC-SA-4.0, części NC); część PL (MARCELL, CC0) do osobnego sprawdzenia | nie | 2026-10-30 |
| `MegaScience/TextbookReasoning` | licencja niekomercyjna (CC-BY-NC-SA-4.0) | nie | 2026-10-30 |
| `speakleash/PES-2018-2022` | egzaminy specjalizacyjne lekarzy | tak | 2026-10-30 |
| `NASK-PIB/Reassess-Polish-Medical-Exams` | polskie egzaminy medyczne | tak | 2026-10-30 |
| `Gregniuki/polish-medical-cot-PES` | zbudowany z pytań PES | tak (ostrożnie: pochodna PES) | 2026-10-30 |
| Global-MMLU | tłumaczone pytania MMLU | tak | 2026-10-30 |
| exams | pytania egzaminacyjne | tak | 2026-10-30 |
| Lots-of-LoRAs task579-581, task384, task385 | zbudowane z pytań SIQA | tak (ostrożnie: pochodna SIQA) | 2026-10-30 |
| Zbiory benchmarków w formacie pytanie-litera (ARC, MMLU, SIQA, PubMedQA, arkusze CKE), także tłumaczone | uczą formatu testu, nie wiedzy | tak | 2026-10-30 |
| Dane NLI w formacie zadania (RTE/CB/ANLI-podobne) | stałe predykcje na tych testach to bariera formatu, nie brak danych | tak | 2026-10-30 |
