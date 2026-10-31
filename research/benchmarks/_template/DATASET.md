# <Benchmark>: karta zbioru (benchmark bez oryginału)

Znaczenie pól opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „Benchmark bez oryginału: karta zbioru
(DATASET.md)”. Ten plik zastępuje `ORIGINAL.md` i `REPRODUCTION.md`, więc tamte dwa usuń. Gdy czegoś nie da się
ustalić, wpisz „nieustalone” i dopisz, gdzie szukałeś.

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

Zbiór liczony przez NLL albo BPB nie ma bazy losowej. Zamiast tabeli wyżej wypełnij tę (METODOLOGIA.md, sekcja
„Benchmark bez oryginału: karta zbioru (DATASET.md)”):

| | wartość |
|---|---|
| model, który zna język zbioru @ rewizja | `speakleash/Bielik-1.5B-v3` albo `utter-project/EuroLLM-1.7B` (rewizje: METODOLOGIA.md, „Pięć modeli odniesienia”) |
| model bez języka zbioru @ rewizja | `EleutherAI/pythia-1b-v0` @ `step143000` |
| BPB obu modeli, n dokumentów | |
| różnica BPB w SE (SE bootstrapem po dokumentach) | |
| werdykt | model znający język ma BPB niższe o co najmniej 2 SE / nie (stop) |

Komendę i środowisko zapisujesz w [`RECIPE.md`](RECIPE.md).
