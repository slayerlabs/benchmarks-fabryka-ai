# <Benchmark>: odtworzenie (etap B)

Procedurę opisuje [METODOLOGIA.md](../../METODOLOGIA.md), sekcja „B. Odtworzenie wyniku oryginalnym kodem (REPRODUCTION.md)”.

| | wartość |
|---|---|
| kod referencyjny @ commit | |
| dlaczego ten kod | |
| model kontrolny @ rewizja (z sekcji „Model kontrolny etapu B”) albo „bez kontroli” | |
| bez kontroli: miejsca, w których szukano opublikowanego wyniku | |
| bez kontroli: model @ rewizja liczony kodem autorów i kodem z repo | |
| bez kontroli: zgodność według kolumny „test zgodności” typu (np. co najmniej 99% zgodnych decyzji; przy `ppl` różnica per dokument poniżej 0,1%) | |
| bez kontroli: powód, gdy kodu autorów nie da się uruchomić (zgodność sprawdza wtedy recenzent PR) | |
| dlaczego ten model (które modele z listy nie mają opublikowanego wyniku) | |
| zbiór @ rewizja, split, n | |
| wynik (SE) | |
| wartość referencyjna i źródło | |
| różnica | |
| kontrola odróżnia działający kod od zepsutego (kolumna „kontrola” typu): b, wynik − b w SE, dodatkowy przebieg, jeśli typ go wymaga | |
| warunek odtworzenia | ±2 pkt w skali metryki; gdy 2 SE > 2 pkt, w granicach 2 SE; dla `ppl` próg zapisany tu przed pomiarem |
| werdykt | spełniony / niespełniony / bez kontroli: kod zgodny / bez kontroli: kod niezgodny / bez kontroli: nierozstrzygnięte / nierozstrzygalny (`ppl` bez progu zapisanego przed pomiarem) |

Komendę i środowisko zapisujesz w [`RECIPE.md`](RECIPE.md).
