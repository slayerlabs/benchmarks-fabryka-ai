# CLAUDE.md

Reguły dla Claude Code w tym repo. Claude Code nie wczytuje `AGENTS.md`, dlatego najważniejsze zasady stoją tu.
Pełny opis układu repo jest w [`AGENTS.md`](AGENTS.md), procedura pracy w
[`research/METODOLOGIA.md`](research/METODOLOGIA.md), zasady PR i tablicy w [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Układ i granice

- Jeden benchmark to `research/benchmarks/<name>/`. Wersja polska ma osobny katalog `<name>-pl/` z `POLISH.md`.
  Nowy benchmark kopiujesz z `research/benchmarks/_template/`.
- Kod trafia do `research/common/` tylko wtedy, gdy używa go więcej niż jeden benchmark.
- `research/slayer-1b/` i `frontend-beta/` zostają nieruszone przy pracy nad benchmarkami.
- Nazwy katalogów, plików i kod piszesz po angielsku. Dokumenty, opisy PR i komentarze po polsku.

## Liczby

- Każda liczba w raporcie `.md` pod `research/` musi być w `results/LICZBY.json`. Liczbę spoza wyników, np. z pracy,
  oznaczasz na końcu linii: `<!-- liczba-spoza-wynikow: skąd jest liczba -->`.
- Każdy wynik ma n i SE. Każde porównanie ma różnicę wyrażoną w SE i werdykt.
- Pytania benchmarku nie trafiają do danych treningowych (`research/METODOLOGIA.md`, sekcja „Czystość benchmarku”).

## Przed PR

W `research/` uruchamiasz poniższe komendy. Każda musi skończyć się kodem 0, bo katalog nie ma CI:

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
.venv-eval/bin/python tests/test_<name>.py
.venv-eval/bin/python tests/test_<name>_zgodnosc.py   # tylko gdy benchmark ma własną implementację
.venv-eval/bin/python tests/test_liczby_raportow.py
```

Gałąź zakładasz od `main`: `research/<name>` albo `docs/<temat>`. PR idzie do `main` z `Refs #N` zadania z tego
repo. Piszesz `Refs`, nie `Closes`, bo zadanie zamyka recenzent. Nie scalasz własnego PR.

## Czego nie commitujesz

Wag modeli (`*.safetensors`, `*.bin`, `*.pt`, katalog `models/`), zbiorów danych (`*.parquet`, `*.arrow`), archiwów
`*.zip` ani żadnego pliku powyżej 10 MB. Wyniki per pytanie wolno commitować skompresowane, jako
`results/<model>/<zadanie>.jsonl.gz`, do około 10 MB na plik. Surowe `*.jsonl` zostają lokalnie.

## Trening przechodzi bramkę, zanim pójdzie pełny przebieg

Przebieg, który żyje i zapisuje pliki, z zewnątrz wygląda na działający trening, nawet gdy niczego się nie uczy.
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
- Bez łańcuchów „poczekaj i odpal” (`while … sleep; done; python train.py`, kolejki nocne). Następny ciężki
  proces startuje ręcznie, po sprawdzeniu punktu wyżej.

## Wczytywanie checkpointów

`torch.load(..., weights_only=True)`. Inne formy deserializują pickle i mogą wykonać obcy kod.
