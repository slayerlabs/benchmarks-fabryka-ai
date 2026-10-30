# Odrzucone zbiory danych

Te zbiory zostały już sprawdzone i **odpadają z treningu**. Lista jest po to, żeby nikt nie sprawdzał
ich drugi raz. Wracają tylko z nowym faktem (np. zgodą licencjodawcy). Użyte i kandydaci:
[`REJESTR_DATASETOW.md`](REJESTR_DATASETOW.md).

Kolumna **do testów**: „tak” znaczy, że zbiór nie nadaje się do treningu, ale można na nim oceniać
model (to pytania z benchmarku albo zbudowane z nich, więc trening na nich zawyżałby wynik).

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
