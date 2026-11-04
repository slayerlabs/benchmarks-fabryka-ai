# WinoGrande: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”. Komenda i środowisko: [`RECIPE.md`](RECIPE.md).

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1`, zadanie `winogrande`. Lokalna kopia w `lm_eval_tasks/winogrande/` dokłada tylko `dataset_kwargs.revision`. Prompt, cel i metryka bez zmian wobec katalogu z instalacji. |
| dlaczego ten kod | Issue #27 każe liczyć zadaniem lm-eval `winogrande`. Praca nie publikuje kodu 0-shot dla modelu językowego bez dostrajania. Opublikowany wynik Pythii pochodzi z harnessu z 2022 (`versions.winogrande` = 0), nie z `0.4.9.1`. To jest kod wskazany przez repo, nie tamten plik bajt w bajt. |
| model kontrolny @ rewizja | `EleutherAI/pythia-1b-v0` @ `step143000`. Commit wag z metadanych pobrania: `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`. API HF potwierdza, że to `step143000`. |
| dlaczego ten model | Pierwszy z listy w sekcji „Model kontrolny etapu B”. Ma opublikowane `acc` 0,5375 na tym zadaniu. |
| zbiór @ rewizja, split, n | `allenai/winogrande`, `winogrande_xl` @ `01e74176c63542e6b0bcb004dcdea22d94fb67b5`, `validation`, n = 1267 |
| wynik (SE) | `acc` 0,5445935280189423 (690 z 1267), SE 0,013996485037729782 |
| wartość referencyjna i źródło | 0,5375. Plik Pythii v0 @ `a19eecb`, odczyt w karcie `ORIGINAL.md` |
| różnica | +0,007094, czyli +0,71 pkt |
| warunek odtworzenia | ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE. SE z karty 0,0140, więc 2 SE = 0,0280. Furtka 0,5095–0,5655 |
| werdykt | spełniony |

Zdanie werdyktu, Grzegorz Zawadzki, 2026-11-04. W pliku jedna poprawka wobec wiadomości: „graniacch” → „granicach”. Etykieta z metodologii przy |z| ≥ 3 to „pewne”, nie „pewny”. Tego słowa w zdaniu nie podmieniłem, bo „jest pewne” byłoby niegramatyczne.

Wartość wpadła w furtkę która wynosi 0.5095-0,5655. |z| wynioslo 3,18 co oznacza, że wynik jest pewny. Różnica wobec 0,5375 wynosi +0,71pkt, co jest szumem i akceptowalna w granicach furtki.
