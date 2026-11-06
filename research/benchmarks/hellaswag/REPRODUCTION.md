# HellaSwag: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”.
Liczby przebiegu są w [`results/HELLASWAG.md`](results/HELLASWAG.md).

| | wartość |
|---|---|
| kod referencyjny @ commit | lm-eval `0.4.9.1`, zadanie `hellaswag`. Repo autorów `rowanz/hellaswag` zwraca HTTP 451. |
| dlaczego ten kod | Karta wskazuje lm-eval. Prompt i metryki są te same co w commicie Space `6d2abda4` (`ORIGINAL.md`). |
| model kontrolny @ rewizja | `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` |
| dlaczego ten model | Pythia-1B v0 nie ma opublikowanego HellaSwag. EuroLLM jest drugi na liście kontroli i karta podaje jego wynik po angielsku. |
| zbiór @ rewizja, split, n | `Rowan/hellaswag` @ `218ec52e09a7e7462a5400043bb9a69a41d06b76`, `validation`, 10042 pytań. 10-shot bierze przykłady ze splitu `train` tej samej rewizji. |
| wynik (SE) | `acc_norm` 0,6074 (SE 0,0049). `acc` 0,4534 jest obok i nie wchodzi do warunku. |
| wartość referencyjna i źródło | 0,6057, HellaSwag po angielsku, karta modelu EuroLLM. Metryka i 10-shot: `ORIGINAL.md`. |
| różnica | 0,0017 |
| kontrola odróżnia działający kod od zepsutego | baza losowa 0,25, baza większościowa 0,2573. EuroLLM wobec bazy większościowej: różnica 0,3501, SE 0,0065, z = 53,63, pewne. |
| warunek odtworzenia | ±2 pkt, czyli 0,02. 2 SE naszego wyniku to 0,0097, więc zostaje 0,02. |
| werdykt | spełniony |

Slayer 1.06 policzony tym samym kodem, też 10-shot, na tych samych 10042 pytaniach: `acc_norm` 0,3953 (SE 0,0049). Slayer minus EuroLLM: różnica −0,2121, SE 0,0045, z = −46,83, pewne. Udział najczęstszej odpowiedzi: EuroLLM 0,2521, Slayer 0,2548. Żaden nie stoi na jednej opcji.

Slayer 0-shot na panelu 200 (klucz `20261028|hellaswag|hellaswag|<source_id>` z `tasks_50.json`, T05): `acc_norm` 0,4350 (SE 0,0351). Space podaje 0,365. Różnica 0,0700, 2 SE panelu 0,0701. Różnica jest mniejsza od 2 SE, na samej granicy. Cały split 0-shot ma 0,3938, więc panel nie jest kopią średniej ze wszystkich pytań, ale nie mamy listy id Space, żeby sprawdzić zgodność dokumentu po dokumencie.

Komenda i środowisko: [`RECIPE.md`](RECIPE.md).
