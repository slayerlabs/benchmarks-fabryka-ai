# Odrzucone zbiory danych

Zbiory sprawdzone i odrzucone, żeby nikt nie sprawdzał ich drugi raz. Wracają tylko z nowym faktem
(np. zgodą licencjodawcy). Użyte i kandydaci: [`REJESTR_DATASETOW.md`](REJESTR_DATASETOW.md).

**Dane testowe** znaczy: zbiór służy do oceny modelu (pytania z benchmarku albo zbudowane z nich),
więc trening na nim zawyża wynik zamiast uczyć.

| zbiór | powód | data |
|---|---|---|
| OpenStax Polska (Fizyka t.1-3, Psychologia, Mikro/Makroekonomia) | strona zastrzega zakaz trenowania AI bez zgody OpenStax Poland | 2026-10-30 |
| `joelniklaus/Multi_Legal_Pile` | licencja niekomercyjna (CC-BY-NC-SA-4.0, części NC); część PL (MARCELL, CC0) do osobnego sprawdzenia | 2026-10-30 |
| `MegaScience/TextbookReasoning` | licencja niekomercyjna (CC-BY-NC-SA-4.0) | 2026-10-30 |
| `speakleash/PES-2018-2022` | dane testowe (egzaminy specjalizacyjne lekarzy) | 2026-10-30 |
| `NASK-PIB/Reassess-Polish-Medical-Exams` | dane testowe (polskie egzaminy medyczne) | 2026-10-30 |
| `Gregniuki/polish-medical-cot-PES` | dane testowe (zbudowane z pytań PES) | 2026-10-30 |
| Global-MMLU | dane testowe (tłumaczone pytania MMLU) | 2026-10-30 |
| exams | dane testowe (pytania egzaminacyjne) | 2026-10-30 |
| Lots-of-LoRAs task579-581, task384, task385 | dane testowe (zbudowane z pytań SIQA) | 2026-10-30 |
| Zbiory benchmarków w formacie pytanie-litera (ARC, MMLU, SIQA, PubMedQA, arkusze CKE), także tłumaczone | dane testowe; uczą formatu testu, nie wiedzy | 2026-10-30 |
| Dane NLI w formacie zadania (RTE/CB/ANLI-podobne) | stałe predykcje na tych testach to bariera formatu, nie brak danych | 2026-10-30 |
