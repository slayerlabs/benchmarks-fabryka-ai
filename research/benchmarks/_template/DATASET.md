# <Benchmark>: karta zbioru (benchmark bez oryginału)

Znaczenie pól: [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „Benchmark bez oryginału: karta zbioru (DATASET.md)”.
Ten plik zastępuje `ORIGINAL.md` i `REPRODUCTION.md`: usuń je. Czego nie da się ustalić, wpisz „nieustalone” z tym,
gdzie szukałeś.

| pole | wartość |
|---|---|
| Co mierzy | umiejętność: ; metoda przejęta od (benchmark, jeśli jest): |
| Jak powstał | źródło tekstów: ; daty: ; narzędzia: ; kryteria doboru: ; licencja: |
| Kto pisał i kto sprawdzał | autor (nick GitHub): ; sprawdzał: ; co i na ilu przykładach: |
| Jawna próbka | plik w repo: ; n (około 10% zbioru): |
| Ukryta reszta | gdzie leży: ; kto ją trzyma: ; jak poprosić o przebieg: |
| Jak liczyć | metryka decyzyjna: ; prompt: ; ocena: ; agregacja: ; n: ; oczekiwane SE: |
| Bazy | losowa: ; większościowa: |
| SNR | rozrzut wyników (odchylenie std.) między modelami/checkpointami: ; typowe SE: ; SNR = rozrzut / SE: ; modele: |
| Train policy | `eval_only` / `decon_only` / `train_allowed` (które splity) |
| Decyzja treningowa | |

## Kontrola

| | wartość |
|---|---|
| model, który zna polski @ rewizja | `speakleash/Bielik-1.5B-v3` albo `utter-project/EuroLLM-1.7B` (rewizje: METODOLOGIA.md, „Pięć modeli odniesienia”) |
| wynik (SE), n | |
| baza (losowa albo większościowa, wyższa) | |
| różnica od bazy w SE | |
| werdykt | wyraźnie powyżej bazy (różnica > 2 SE) / na poziomie bazy (stop) |

Komenda i środowisko: wpis w [`RECIPE.md`](RECIPE.md).
