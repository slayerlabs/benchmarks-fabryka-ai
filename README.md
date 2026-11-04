# benchmarks-fabryka-ai

Mierzymy otwarte modele językowe, dziś polsko-angielskiego **Slayer 1B**, na benchmarkach odtworzonych zgodnie z
oryginałem, i budujemy polskie benchmarki.

<p align="center">
  <a href="https://discord.gg/HnTkVR4c5T"><img src="docs/img/discord.svg" alt="Discord" height="36"></a>
  <a href="https://github.com/orgs/slayerlabs/projects/10"><img src="docs/img/tablica.svg" alt="Tablica" height="36"></a>
  <a href="https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22"><img src="docs/img/zadania-na-start.svg" alt="Zadania na start" height="36"></a>
  <a href="CONTRIBUTING.md"><img src="docs/img/jak-dolaczyc.svg" alt="Jak dołączyć" height="36"></a>
  <a href="research/README.md#przygotowanie-raz"><img src="docs/img/przygotowanie.svg" alt="Przygotowanie" height="36"></a>
  <a href="research/METODOLOGIA.md"><img src="docs/img/metodologia.svg" alt="Metodologia" height="36"></a>
  <a href="research/benchmarks/_template"><img src="docs/img/nowy-test.svg" alt="Nowy test" height="36"></a>
  <a href="https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks"><img src="docs/img/wyniki-na-hf.svg" alt="Wyniki na HF" height="36"></a>
</p>

[Discord](https://discord.gg/HnTkVR4c5T) · [Tablica](https://github.com/orgs/slayerlabs/projects/10) ·
[Zadania na start](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22) ·
[Jak dołączyć](CONTRIBUTING.md) · [Przygotowanie](research/README.md#przygotowanie-raz) ·
[Metodologia](research/METODOLOGIA.md) · [Nowy test](research/benchmarks/_template) ·
[Wyniki na HF](https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks)

## Gdzie co jest

| katalog albo plik | co tam jest |
|---|---|
| `research/benchmarks/` | jeden katalog na benchmark; wzór nowego w `_template/` |
| `research/METODOLOGIA.md` | jak powstaje benchmark: etapy A–D, typy testów, SE i werdykt |
| `research/common/` | kod wspólny: ładowanie modeli, ewaluacja przez lm-eval |
| `research/tools/` | bramka liczb i przebieg centralny |
| `research/tests/` | testy kodu, bez sieci i bez wag |
| `research/results/` | `LICZBY.json`: wszystkie liczby raportów |
| `research/slayer-1b/` | praca nad samym Slayerem 1B poza benchmarkami |
| `CONTRIBUTING.md`, `AGENTS.md` | zasady pracy w repo; krótki opis dla piszących kod |

Pełny układ: [`research/README.md`, „Układ”](research/README.md#układ).

## Pierwsze kroki

1. **Dołącz.** Napisz na Discordzie według [`CONTRIBUTING.md`, „Kontakt”](CONTRIBUTING.md#kontakt).
2. **Weź zadanie** z kolumny Ready na [tablicy](https://github.com/orgs/slayerlabs/projects/10) albo z etykietą
   [`good first issue`](https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22).
   Przypisz się i przestaw je na In Progress ([„Pierwsze zadanie”](CONTRIBUTING.md#pierwsze-zadanie)).
3. **Przygotuj środowisko** według [„Przygotowanie (raz)”](research/README.md#przygotowanie-raz).
4. **Uruchom jeden test** w katalogu `research/`. Kod 0 znaczy, że środowisko działa:

   ```bash
   .venv-eval/bin/python tests/test_statystyka.py
   ```

5. **Otwórz PR do `main`** z `Refs #N` w opisie, według [`CONTRIBUTING.md`, „PR”](CONTRIBUTING.md#pr).

## Definicja „zrobione”

Benchmark jest zrobiony, gdy PR do `main` zawiera katalog `research/benchmarks/<name>/` założony z
[`research/benchmarks/_template/`](research/benchmarks/_template/README.md). Zamiast jednego PR może być kilka, po
jednym na etap. W katalogu musi być:

1. `ORIGINAL.md` (etap A) i `REPRODUCTION.md` (etap B) ze spełnionym warunkiem odtworzenia. Benchmark bez oryginału
   ma zamiast nich `DATASET.md` i kontrolę na modelu, który zna polski. Wersja polska leży w osobnym katalogu
   `research/benchmarks/<name>-pl/` i ma `POLISH.md` (etap D).
2. Kod liczący wynik (etap C). To wywołanie kodu z etapu B albo własna implementacja z testem zgodności
   `research/tests/test_<name>_zgodnosc.py`.
3. Test kodu `research/tests/test_<name>.py` z próbką danych. Test przechodzi bez sieci i bez wag.
4. Wynik mierzonego modelu z n i SE, a obok wynik modelu kontrolnego
   ([„Model kontrolny etapu B”](research/METODOLOGIA.md#model-kontrolny-etapu-b)) liczony tym samym kodem. Oba liczy
   autor PR.
5. Wiersz testu w [`research/README.md`, „Benchmarki i typy”](research/README.md#benchmarki-i-typy) (karta do niego linkuje), bazy i b według tabeli typów, porównanie z modelem kontrolnym jako różnica w SE z werdyktem
   ([METODOLOGIA, „Typy testów”](research/METODOLOGIA.md#typy-testów)).
6. `RECIPE.md` z wpisem dla każdego wyniku.
7. Benchmark liczony przez `research/common/ewaluuj.py`: wpis w `ZADANIA` (`research/common/zadania.py`) i w
   `KATALOGI` przebiegu centralnego. Benchmark z własnym kodem: komenda w `RECIPE.md`, którą liczy się go ręcznie,
   bo przebieg centralny woła tylko `ewaluuj.py`.
8. Komendy z sekcji [„Przed PR”](#przed-pr) zakończone kodem 0.
9. `Refs #N` zadania w opisie PR.

Autor PR nie liczy modeli odniesienia. Liczy je przebieg centralny `research/tools/przebieg_centralny.sh`, opisany w
[METODOLOGII, „Następna wersja Slayera”](research/METODOLOGIA.md#następna-wersja-slayera).

## Przed PR

Przed otwarciem PR uruchom w katalogu `research/` komendy niżej. To testy zmienionego benchmarku,
`tests/test_liczby_raportow.py` i bramka liczb. Każda komenda musi zakończyć się kodem 0. Katalog `research/` nie ma
CI, więc uruchamiasz je sam.

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
.venv-eval/bin/python tests/test_<name>.py
.venv-eval/bin/python tests/test_<name>_zgodnosc.py   # tylko gdy benchmark ma własną implementację
.venv-eval/bin/python tests/test_liczby_raportow.py
```

**Sama karta.** PR z samą kartą oryginału (etap A) wymaga tylko bramki liczb z kodem 0, bez testów benchmarku:

```bash
.venv-eval/bin/python tools/liczby.py && .venv-eval/bin/python tools/sprawdz_raporty.py
```

Recenzent takiego PR nie odtwarza `RECIPE.md`. Sprawdza u źródła prompt, ocenę, wynik referencyjny i bazy, a przy
„brak” albo „nieustalone” listę przeszukanych miejsc.
