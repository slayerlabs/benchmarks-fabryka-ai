# REGULA — MathQA (T19)

Zapisano 2026-11-07, przed pierwszym uruchomieniem modelu na T19; commit tego pliku jest starszy niż commit
z wynikami. Decyzja o kontroli nie zależy od wyniku Slayera.

## 1. Kontrola

Lista „Model kontrolny etapu B” z METODOLOGII, po kolei:

1. **`EleutherAI/pythia-1b-v0` @ `step143000`** — plik wyników 0-shot zawiera tylko `arc_challenge`, `arc_easy`,
   `lambada_openai`, `logiqa`, `piqa`, `sciq`, `winogrande`, `wsc`, 67 zadań `blimp_*` i 57 zadań
   `hendrycksTest-*` (spis w METODOLOGII, „Model kontrolny etapu B”). **Brak MathQA.**
2. **`utter-project/EuroLLM-1.7B`** — karta modelu nie podaje wyniku na MathQA (sekcje z wynikami wymieniają inne
   benchmarki). Sprawdzone 2026-11-07.
3. **Opublikowany wynik dowolnego modelu, który da się pobrać**, z rewizją i ustawieniami (prompt, liczba
   przykładów, metryka, wersja kodu). Przeszukane 2026-11-07:
   - **Open LLM Leaderboard v2** — zestaw to IFEval, BBH, MATH Lvl 5, GPQA, MuSR i MMLU-Pro. Bez MathQA.
   - **Katalog wyników w repo lm-eval** — `EleutherAI/lm-evaluation-harness` @ `v0.4.9.1` nie ma katalogu
     `results/`. Bez wyników do odczytu.
   - **Praca autorów zbioru** (Amini i in., NAACL 2019, arXiv 1905.13319) i strona `math-qa.github.io` — wyniki
     własnych modeli autorów, bez wag do pobrania w rozumieniu listy.
   - **Zgłoszenie w lm-eval, issue #443** — LLaMA-7B, `acc` 0,2677 (SE 0,0081) i `acc_norm` 0,2787 (SE 0,0082); przy b = 0,2265 próg kontroli typu `mc` wynosi 0,2418 (b + 2 SE, SE = 0,0077), więc liczbowo by przeszło. <!-- liczba-spoza-wynikow: liczby z wątku zgłoszenia github.com/EleutherAI/lm-evaluation-harness/issues/443 i próg policzony dla n = 2985 -->
     **Odrzucone**: to wpis użytkownika w wątku zgłoszenia, bez rewizji modelu, bez wersji lm-eval i bez ustawień
     promptu, a wagi LLaMA-7B nie są swobodnie do pobrania. Punkt 3 listy wymaga rewizji i ustawień.
   - **Praca „EasyMath” (arXiv 2505.14852)** — ma kolumnę MathQA dla modeli 70M–3B w trybie 0-shot, ale opisuje
     MathQA jako zadanie z czterema opcjami (ma pięć) i nie podaje metryki ani wersji kodu. Odrzucone z tego
     samego powodu: brak ustawień.
   - **Agregatory w rodzaju `sota2.com`** — przepisują liczby z prac o kompresji modeli, bez rewizji i ustawień.
     Odrzucone.

Nie przeszukano: HELM, leaderboardów poszczególnych dostawców i tabel w pracach o modelach, które nie wymieniają
MathQA w abstrakcie. Uznano, że lista z METODOLOGII jest wyczerpana.

**Wniosek: bez kontroli, wynik wstępny.** Werdykt etapu B: „bez kontroli: nierozstrzygnięte”. Wynik nie idzie do
tabeli CodeSOTA ani do meta-oceny.

## 2. Próg wstrzymania

Nie dotyczy — brak kontroli. Rdzeń mówi wprost, że brak opublikowanego wyniku nie zatrzymuje pracy.

## 3. Slayer

- Wynik na panelu Space (200) i na pełnym splicie (2985), metryka decyzyjna `acc_norm` z `tasks_50.json`.
- CI95 według METHOD.md: bootstrap percentylowy, 10 000 powtórzeń, seed 20261028.
- Float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`.
- Bazy policzone ze splitu przed pomiarem: losowa 0,2000, większościowa 0,2265 (`c`, 676/2985).
