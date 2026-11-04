# WinoGrande: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md).

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1`, zadanie `winogrande`. Lokalna kopia w `lm_eval_tasks/winogrande/` dokłada tylko `dataset_kwargs.revision`. Prompt, cel i metryka bez zmian wobec katalogu z instalacji. |
| dlaczego ten kod | Issue #27 każe liczyć zadaniem lm-eval `winogrande`. Praca nie publikuje kodu 0-shot dla modelu językowego bez dostrajania. Opublikowany wynik Pythii pochodzi z harnessu z 2022 (`versions.winogrande` = 0), nie z `0.4.9.1`. To jest kod wskazany przez repo, nie tamten plik bajt w bajt. |
| model kontrolny @ rewizja | `EleutherAI/pythia-1b-v0` @ `step143000`. Commit wag z metadanych pobrania: `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`. API HF potwierdza, że to `step143000`. |
| dlaczego ten model | Pierwszy z listy w sekcji „Model kontrolny etapu B”. Ma opublikowane `acc` 0,5375 na tym zadaniu. |
| zbiór @ rewizja, split, n | `allenai/winogrande`, `winogrande_xl` @ `01e74176c63542e6b0bcb004dcdea22d94fb67b5`, `validation`, n = 1267 |
| wynik (SE) | `acc` 0,5446 (690 z 1267), SE K 0,012548 po klastrach (k = 983: 284 pary bliźniacze i 699 pojedynczych zdań, typ `mc +klastry`). SE A 0,013996 informacyjnie |
| wartość referencyjna i źródło | 0,5375. Plik Pythii v0 @ `a19eecb`, odczyt w karcie `ORIGINAL.md` |
| różnica | +0,007094, czyli +0,71 pkt. SE K 0,012548, t = 0,565 (df = 982), szum |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | b = 0,5043, stała odpowiedź „zawsze opcja 2” (639 z 1267). Pythia minus ten predyktor, parowane po pytaniach: +4,03 pkt, SE K 0,015915, t = 2,529 (df = 982), prawdopodobne, czyli wynik > b + 2 SE. SE A informacyjnie: 0,019129, z = 2,104. Slayer minus ten sam predyktor: +1,74 pkt, SE K 0,016249, t = 1,069 (df = 982), szum; SE A 0,019812, z = 0,876 |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE. SE z karty 0,0140, więc 2 SE = 0,0280. Furtka 0,5095–0,5655 |
| werdykt | spełniony |

Zdanie werdyktu, Grzegorz Zawadzki, 2026-11-04. W pliku jedna poprawka wobec wiadomości: „graniacch” → „granicach”. Zdanie o |z| zmienione w recenzji PR: tamto z liczyło Pythię wobec 0,5, a b typu `mc` to stała odpowiedź „zawsze opcja 2”, porównana parami po pytaniach, z SE K. Do sprawdzenia przez autora.

Wartość wpadła w furtkę która wynosi 0.5095-0,5655. Wobec stałej odpowiedzi „zawsze opcja 2” (b = 0,5043) Pythia ma +4,03 pkt, t = 2,529 (df = 982), co oznacza, że wynik jest prawdopodobnie powyżej b. Różnica wobec 0,5375 wynosi +0,71pkt, co jest szumem i akceptowalna w granicach furtki.

Zdanie o panelu Space, Grzegorz Zawadzki, 2026-11-04. W pliku jedna poprawka: „przykladach” → „przykładach”. 0,55 jest ze Space, nie z naszego pliku. <!-- liczba-spoza-wynikow: results.json Space T07 @ 2d3d73f, panel 200 -->

Różnica 0,55 a 0,5217. To nie jest ta sama próbka, bo była liczona na 200 i 1267 przykładach. <!-- liczba-spoza-wynikow: 0,55 ze Space T07, panel 200; 0,5217 jest w results/winogrande.json -->
