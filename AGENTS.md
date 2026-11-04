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

Komendy z sekcji [„Przed PR”](README.md#przed-pr) README kończą się kodem 0; katalog `research/` nie ma CI. Reguły,
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
