# Przepis: nakładka lm-eval `slayer`, kontrola T02

Jeden wynik: ARC-Challenge, próbka Space (200), Slayer 1.06. Komenda w `research/`.

## Slayer 1.06, T02 ARC-Challenge

- Commit kodu: commit, który dodał ten plik, na `3c8ca13`. Przebiegi zapisały `git_hash` `b129f6c`, czyli hash tego samego kodu sprzed spłaszczenia historii.
- Środowisko przebiegu: Python 3.12.10, lm-eval 0.4.9.1, transformers 4.57.6, torch 2.8.0+cpu, pakiety z `common/requirements.lock.txt`.
- Drugi przebieg na CPU, na wcześniejszej wersji kodu z tym samym forwardem: Python 3.9.25, torch 2.8.0+cu128, pakiety zgodne z lockiem (77 z 77), poza lokalnym znacznikiem `+cu128` przy torch; venv miał dodatkowo `pywin32` i `setuptools`. Wynik ten sam, per pytanie nie porównany, bo ten przebieg nie zapisał próbek.
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` (tokenizer sha256 `0640d3bd3674d7a6e59c540d945a2ad275a12e1bcaeb6007c37a90751f9815dd`, jak w `config.json`)
- Zbiór: `allenai/ai2_arc` @ `210d026faf9955653af8916fad021475a3f00453`, split `test`, konfiguracja `ARC-Challenge`
- Próbka: `common/tests/data/arc_panel200.json` — 200 indeksów z `metryki.ranking_panel("arc", "arc_challenge", id, 200)`, seed `20261028`. Harness wypisał „Evaluating on 200 examples”; SE wyniku zgadza się z n=200.
- Komenda (w `research/`, po `python common/slayer_lm.py --install`). W tym przebiegu `pretrained` wskazywał lokalną kopię, nie `models/slayer-1.06`:

```bash
.venv-eval/bin/lm_eval --model slayer --model_args pretrained=models/slayer-1.06,dtype=float32 --include_path common/lm_eval_tasks --tasks arc_challenge --samples common/tests/data/arc_panel200.json --num_fewshot 0 --batch_size 1 --device cpu --seed 0,1234,1234,1234
```

- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32
- Sprzęt: CPU, AMD Ryzen 7 5800X3D, Windows 11, `--device cpu`
- Data: 2026-11-01
- Wynik: acc_norm 0,245 (SE 0,0305), acc 0,21 (SE 0,0289), n=200 <!-- liczba-spoza-wynikow: pomiar tej nakładki, nie ma go w results/LICZBY.json -->
- Odniesienie Space (T02, acc_norm, n=200, CI95 0,19–0,31): 0,25 <!-- liczba-spoza-wynikow: wartość ze Space results.json, nie z results/LICZBY.json -->
- Zgodność: różnica acc_norm 0,005, w granicach SE (SE Space przy n=200 i p=0,25 to około 0,031). <!-- liczba-spoza-wynikow: różnica i SE nie są w LICZBY.json -->

## Znane rozbieżności

- Plik zadania lm-eval: `lm_eval/tasks/arc/arc_easy.yaml` i `arc_challenge.yaml` są identyczne w `6d2abda4` (Space) i w 0.4.9.1 (lock); porównane plik po pliku, katalog `arc` ma w obu ten sam zestaw plików.
- Lokalne `common/lm_eval_tasks/arc_challenge.yaml` scala te dwa pliki w jeden (bez `include`) i różni się od nich tylko w tym, co nie zmienia promptu ani metryki:
  - przypina rewizję zbioru (`dataset_kwargs.revision`), której upstream nie ma, wartość z `tasks_50.json` Space;
  - jawnie ustawia `target_delimiter: " "`, wartość domyślną w lm-eval;
  - nie ma `tag`, `should_decontaminate` ani `doc_to_decontamination_query`; przebieg nie liczy dekontaminacji.
- Model w harnessie: kodu, który policzył wartość Space, nie ma w tym repo, więc adaptera Space nie porównano. Ten przebieg ładuje Slayera przez `SlayerLM` i `slayer_model.py`. Forward jest odtworzony z `config.json` i wag.
- Długość kontekstu: `SlayerLM` ustawia `max_length` na `block` (4096), a lm-eval tnie dłuższy kontekst od lewej. W tej próbce nie ma to znaczenia, najdłuższy prompt ma 120 tokenów. Testy offline nie sprawdzają cięcia. <!-- liczba-spoza-wynikow: config.json Slayera i pomiar promptów tej próbki -->
- Moc kontroli: T02 nie odróżnia poprawnego forwardu od zepsutego. Poziom losowy tej próbki (średnia z 1/liczba odpowiedzi) to 0,24975, czyli zgodność ze Space to też zgodność z losowaniem. Pokazuje tylko, że komenda przechodzi cały harness. Poprawność forwardu opiera się na `tests/test_lm_eval_slayer.py`. <!-- liczba-spoza-wynikow: policzone z pliku samples tego przebiegu -->
- GPU: ta sama komenda z `--device cuda` (Python 3.12.10, torch 2.8.0+cu128, RTX 5060 Ti) daje ten sam wynik co CPU: acc i acc_norm zgodne w 200 z 200 pytań, loglikelihood różni się najwyżej o 0,00062. <!-- liczba-spoza-wynikow: porównanie plików samples przebiegów CPU i GPU tej nakładki -->
- Próbka: `arc_panel200.json` to wynik `metryki.ranking_panel`, nie plik z przebiegu Space.
