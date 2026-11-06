# Protokół Space: LogiQA (T18) dla Slayera 1.06

Pierwszy zapis potwierdzony commitem 4a80f06 (2026-11-04 11:46:35 CET), po pomiarze (panel 11:33:13–11:37:30, pełny split 11:37:40–11:43:59); wcześniejszej godziny powstania pliku nie da się ustalić. Korekty po wyniku trafiają do osobnej sekcji na końcu pliku.

## Dane
- Zbiór: `EleutherAI/logiqa` @ `c1eee1b2fd0ddc87777e36490f7ad54d0b97d141` (rewizja z `tasks_50.json`), split test, n = 651.
- Bajty: `logiqa/test/0000.parquet` z `refs/convert/parquet` @ `fcd80241270118cd52c96dc517dc38804025f3f5`, sha256 `86f8a453cf23670e394960054d2bafc20e672bc39518b5de31fde6826e56cf9e` (skrypt ładujący nie działa w `datasets` 3.6.0 bez `trust_remote_code`).
- Zadanie: katalog `lm_eval/tasks/logiqa` w `6d2abda4` i `v0.4.9.1` różni się tylko `dataset_kwargs.trust_remote_code`; `utils_logiqa.py` identyczny (blob `utils.py` w repo). Metryka główna `acc_norm`, 0-shot, 4 opcje.
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`.
- Kontrola: brak (patrz niżej) — wynik wstępny.

## Tożsamość dokumentu
Brak natywnego id. `common/ewaluuj.py` używa indeksu wiersza (0..650) jako `source_id`, bo wpis T18 nie ma `pole_id`. Space może używać SHA-256 dokumentu kanonicznego; panel nasz może się różnić od panelu Space. Pełny split ma 651 pytań i nie zależy od tej postaci.

## Próbka
`min(200, 651)` = 200 dokumentów według `common/metryki.ranking_panel("logiqa", "logiqa", [0..650])`, lista z pliku `panel200` (ewaluuj). Model liczy osobny przebieg próbki i osobny pełnego splitu; wynik próbki ma być podzbiorem przebiegu pełnego (sprawdzone: max różnica loglik 0,0, brak różnic acc).

## Wzory
- Wartość = średnia `acc_norm`, SE = s/√n, CI95 bootstrap percentylowy (10 000 powtórzeń, seed 20261028).
- Bazy: losowa 0,25; większościowa = udział najczęstszej poprawnej pozycji („d”, 181/651 = 0,278).
- Float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`.

## Kontrola
Brak modelu kontrolnego z opublikowanym wynikiem:
- `EleutherAI/pythia-1b-v0` @ `step143000`: opublikowane acc 0,2258 (< 0,25), acc_norm 0,2873; nie przechodzi bazy większościowej o 2 SE (2 SE = 0,0354). <!-- liczba-spoza-wynikow: wynik Pythii 1B v0 opublikowany przez autorów, nie nasz pomiar -->
- `utter-project/EuroLLM-1.7B`: karta modelu nie podaje wyniku na LogiQA.
- Open LLM Leaderboard v2 nie zawiera LogiQA; praca Liu i in. (2020) i repo autorów mają tylko dane.
Wynik: **bez kontroli, wynik wstępny.**

## Wynik (Slayer 1.06)
- panel Space: acc_norm 0,260 (n=200, SE 0,0311, CI95 0,200–0,325)
- pełny split: acc_norm 0,2673 (n=651, SE 0,0174, CI95 0,2335–0,3011)
- acc: panel 0,185, pełny 0,2012; acc_pmi: panel 0,320, pełny 0,3134 <!-- liczba-spoza-wynikow: acc i acc_pmi z tabeli przebiegu; LICZBY.json zbiera metrykę decyzyjną acc_norm -->
- wobec bazy losowej: panel +1,0 pkt (z 0,32, szum), pełny +1,7 pkt (z 0,996, szum)
- wobec bazy większościowej: panel −4,0 pkt (z −0,82, szum), pełny −1,1 pkt (z −0,41, szum)

## Czasy
- panel200: ok. 5 min? (log: 1600 żądań), pełny: ok. 6 min (5208 żądań). Sprzęt: RTX 5050 (8 GB), WSL2 Ubuntu.

## Korekty
- 6.11.2026: nagłówek zmieniony z „Ustalony przed pomiarem”: jedyny dowód czasu to commit `4a80f06` (11:46:35), już po obu pomiarach; decyzje i wyniki w środku bez zmian.
