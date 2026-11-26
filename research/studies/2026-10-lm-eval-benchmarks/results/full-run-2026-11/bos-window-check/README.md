# Pomiar BOS i okna na Pythii-1B v0 (pełny przebieg 2026-11)

Protokół: [`PROTOKOL.md`](PROTOKOL.md), spisany przed pierwszym wynikiem. Raport z liczbami: [`RAPORT.md`](RAPORT.md),
te same liczby jako dane: [`LICZBY.json`](LICZBY.json). Wnioski i ich miejsce w tabelach: [raport przebiegu](../README.md#bos-okno-wikitext-i-kontrola-arc-challenge).

Sprawdzono wyłącznie Pythię-1B v0 (BOS, okno) i EuroLLM-1.7B (25-shot ARC-Challenge); o innych modelach pomiar nic nie mówi.

| ścieżka | zawartość |
|---|---|
| `PROTOKOL.md`, `RAPORT.md`, `LICZBY.json` | protokół, raport i liczby pomiaru |
| `code/` | skrypt uruchamiający (`bos_start.py`, `kolejka.sh`), zbieranie i raport (`zbierz.py`, `raport.py`), testy, mutacje i niezależne przeliczenie |
| `results/<wariant>/<test>/<model>/` | `results.json`, `results_rozszerzone.json`, `scores-history-wiersz.csv`, `podsumowanie.md`: bez próbek, jak w katalogu przebiegu |
| `results/logi/` | `pip freeze` środowisk tego pomiaru |

Pomiar nie zapisał własnego `pip freeze` wyników pełnego przebiegu; freeze w `results/logi/` dotyczy tej instancji. Pełna paczka z próbkami
per pytanie i dziennikami BOS jest poza repo, bo tak repo trzyma próbki dużych przebiegów; sumy sha256 każdego pliku są w `LICZBY.json`
(`sha_wszystkich_plikow`). `RAPORT.md` jest wygenerowany przez `code/raport.py` i zachowany bez zmian, razem z pisownią ASCII.
