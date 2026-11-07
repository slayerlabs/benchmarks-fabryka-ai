# AGENTS.md

Krótki opis repo dla każdego, kto pisze tu kod. Szczegóły są w [`README.md`](README.md),
[`research/README.md`](research/README.md) i [`research/METODOLOGIA.md`](research/METODOLOGIA.md).

## Układ

Układ katalogów opisuje [`research/README.md`, „Układ”](research/README.md#układ). `research/slayer-1b/` i
`frontend-beta/` nie ruszasz przy pracy nad benchmarkami.

## Gdzie co dodać

- Nowy benchmark: skopiuj `research/benchmarks/_template/` do `research/benchmarks/<name>/` (małe litery, myślnik).
  Potem idź etapami z `research/METODOLOGIA.md`.
- Analiza na wielu benchmarkach: `research/analyses/<name>/`.
- Kod trafia do `research/common/` tylko wtedy, gdy używa go więcej niż jeden benchmark. Inaczej zostaje w katalogu
  benchmarku.
- Test: `research/tests/test_<name>.py`. Dane próbki: `research/common/tests/data/<name>.jsonl`.

## Przed PR

Komendy z sekcji [„Przed PR”](CONTRIBUTING.md#przed-pr) w CONTRIBUTING kończą się kodem 0; katalog `research/` nie ma CI. Reguły,
które sprawdzają (bramka liczb, SE i werdykt przy każdym porównaniu), opisuje
[`research/METODOLOGIA.md`](research/METODOLOGIA.md), „Wspólny rdzeń”.

## Zasady

- Język: nazwy katalogów, plików i kod po angielsku. Dokumenty po polsku.
- Czego nie commitujesz (wagi, zbiory, pliki powyżej 10 MB) i kiedy wolno `.jsonl.gz`:
  [`CONTRIBUTING.md`, „Pliki w repo”](CONTRIBUTING.md#pliki-w-repo).
- Pytania benchmarku nie trafiają do danych treningowych (`research/METODOLOGIA.md`, sekcja „Czystość benchmarku”).
- Siła dowodu rośnie z kosztem błędnej decyzji i jej odwrócenia, ponad minimum z bramki liczb (liczba w
  `LICZBY.json`, SE i werdykt). Sekcja „Siła dowodu” w `research/METODOLOGIA.md`.
- PR otwierasz do `main`, z `Refs #N` zadania z tego repo w opisie.
- Checkpoint wczytujesz przez `torch.load(..., weights_only=True)`. Inne formy deserializują pickle i mogą wykonać
  obcy kod.

## Trening przechodzi bramkę, zanim pójdzie pełny przebieg

Przebieg, który żyje i zapisuje pliki, wygląda z zewnątrz na działający trening, nawet gdy niczego się nie uczy.
Dlatego przed pełnym przebiegiem:

1. **Tokenizacja:** wypisz tokeny 2 przykładów i sprawdź, że polskie słowa dzielą się sensownie.
2. **Test przeuczenia:** 64 przykłady, 100 kroków. Strata ma spaść blisko 0. Jeśli nie spada, w kodzie jest błąd
   i pełnego treningu nie odpalasz.
3. **Przerwanie:** pełny trening sam się zatrzymuje, gdy strata po 20% kroków nie spadła o co najmniej 10% od
   startu.

Na pytanie „czy trening działa” podajesz ostatnie wartości straty (train i val) i to, czy spada. „Proces żyje”
nie jest odpowiedzią.

## Ciężkie procesy na własnym komputerze

- Trening dłuższy niż godzina idzie na wynajętą kartę, nie na laptopa.
- Lokalnie najwyżej jeden ciężki proces naraz (trening, ewaluacja modelu, pobieranie wag). Przed startem sprawdź
  `pgrep -fl python` i wolną pamięć.
- Bez łańcuchów „poczekaj i odpal” (`while … sleep; done; python train.py`, kolejki nocne). Następny ciężki proces
  startuje ręcznie, po sprawdzeniu punktu wyżej.
