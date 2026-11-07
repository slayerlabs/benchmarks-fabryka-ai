# REGULA — LogiQA (T18)

Zapisano lokalnie 2026-11-04 11:35:33 (CET), w trakcie pomiaru panelu (start 11:33:13), przed jego wynikiem
(koniec 11:37:30) i przed startem pełnego splitu (11:37:40). Decyzja o kontroli nie zależy od wyniku Slayera.
Pierwotny wpis „przed pierwszym uruchomieniem modelu” był nieprawdziwy i został poprawiony. Dołączono do repo
6.11.2026 (PR #139).

## 1. Kontrola
Lista „Model kontrolny etapu B”:
1. EleutherAI/pythia-1b-v0 @ step143000: opublikowana wartość LogiQA acc_norm 0,2873 (SE 0,0177), acc 0,2258 (SE 0,0164), n=651. Baza większościowa 0,278, 2 SE = 0,0354. acc_norm 0,2873 leży mniej niż 2 SE nad bazą większościową, a acc 0,2258 leży pod bazą losową 0,25. Nie przechodzi. <!-- liczba-spoza-wynikow: wartości opublikowane przez autorów Pythii 1B v0, nie nasz pomiar -->
2. utter-project/EuroLLM-1.7B: karta modelu nie podaje wyniku na LogiQA; przeszukano model card (sekcje Results/General Benchmarks: ARC Challenge, Hellaswag; brak LogiQA) — brak opublikowanej wartości.
3. Inny model z opublikowanym wynikiem: przeszukano Open LLM Leaderboard v2 (LogiQA nie jest w jego zestawie) i tabelę w pracy Liu i in. 2020 (tylko wyniki własne, brak modelu do pobrania). Nie znaleziono.

Wniosek: **bez kontroli, wynik wstępny.** Miejsca przeszukane: plik wyników Pythii v0 (evals/pythia-v0), karta EuroLLM-1.7B, Open LLM Leaderboard v2, praca Liu i in. (arXiv 2007.08124) i repo autorów (tylko dane). Nie przeszukano: innych leaderboardów (np. HELM) i tabel w nowszych pracach; uznano, że wyczerpuje to listę z METODOLOGII.

## 2. Próg wstrzymania
Nie dotyczy — brak kontroli.

## 3. Slayer
- Wynik na próbce Space (200) i na pełnym splicie (651), metryka acc_norm z tasks_50.json.
- CI95 według METHOD.md (bootstrap percentylowy, 10 000 powtórzeń, seed 20261028).
- Float32, batch 1, NVIDIA_TF32_OVERRIDE=0.
