# benchmarks-fabryka-ai

Mierzymy otwarte modele językowe, dziś polsko-angielskiego **Slayer 1B**, na benchmarkach odtworzonych zgodnie z
oryginałem, i budujemy polskie benchmarki.

## Pierwsze kroki

1. **Dołącz.** Napisz na Discordzie na kanale #bench-team i podaj swój login GitHub. Zasady pracy są w „Jak dołączyć”.

   <a href="https://discord.gg/HnTkVR4c5T"><img src="docs/img/discord.svg" alt="Discord" height="36"></a>
   <a href="CONTRIBUTING.md"><img src="docs/img/jak-dolaczyc.svg" alt="Jak dołączyć" height="36"></a>

2. **Weź zadanie** z kolumny Ready na tablicy albo z etykietą `good first issue`. Przypisz się i przestaw je na In
   Progress.

   <a href="https://github.com/orgs/slayerlabs/projects/10"><img src="docs/img/tablica.svg" alt="Tablica" height="36"></a>
   <a href="https://github.com/slayerlabs/benchmarks-fabryka-ai/issues?q=is%3Aopen+label%3A%22good+first+issue%22"><img src="docs/img/zadania-na-start.svg" alt="Zadania na start" height="36"></a>

3. **Przygotuj środowisko.**

   <a href="research/README.md#przygotowanie-raz"><img src="docs/img/przygotowanie.svg" alt="Przygotowanie" height="36"></a>

4. **Uruchom jeden test** w katalogu `research/`. Kod 0 znaczy, że środowisko działa:

   ```bash
   .venv-eval/bin/python tests/test_statystyka.py
   ```

5. **Otwórz PR do `main`** z `Refs #N` w opisie, według [`CONTRIBUTING.md`, „PR”](CONTRIBUTING.md#pr).

Jak powstaje test: [METODOLOGIA, „Etapy pracy”](research/METODOLOGIA.md#etapy-pracy).

<a name="definicja-zrobione"></a>Kiedy test jest skończony: [METODOLOGIA, „Definicja „zrobione””](research/METODOLOGIA.md#definicja-zrobione).

<a name="przed-pr"></a>Przed PR: [CONTRIBUTING, „Przed PR”](CONTRIBUTING.md#przed-pr).

## Gdzie co jest

| gdzie | co tam jest |
|---|---|
| <a href="research/METODOLOGIA.md"><img src="docs/img/metodologia.svg" alt="Metodologia" height="36"></a> | jak powstaje benchmark: etapy A–D, typy testów, SE i werdykt |
| <a href="research/benchmarks/_template"><img src="docs/img/nowy-test.svg" alt="Nowy test" height="36"></a> | wzór nowego benchmarku; każdy benchmark ma katalog w `research/benchmarks/` |
| <a href="https://huggingface.co/spaces/SlayerLab/Slayer1B-Benchmarks"><img src="docs/img/wyniki-na-hf.svg" alt="Wyniki na HF" height="36"></a> | wyniki Slayera 1B w Space |
| `research/common/`, `research/tools/`, `research/tests/` | kod wspólny, bramka liczb i przebieg centralny, testy bez sieci i bez wag |
| `research/slayer-1b/` | praca nad samym Slayerem 1B poza benchmarkami |

Pełny układ: [`research/README.md`, „Układ”](research/README.md#układ).
