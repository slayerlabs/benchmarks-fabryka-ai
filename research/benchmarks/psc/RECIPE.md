# Polish Summaries Corpus (T27): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `allegro/klej-psc@9585582aef37e7747ef174b0ec3b74855da8bad2` (wpis `T27` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie modele z `MODELE` i wszystkie zadania (lista etykiet wymaga `POMIN` z pominiętymi modelami); dla tego zadania woła `common/ewaluuj.py --zadania T27 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T27 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/psc/<model>/results.json`

## Kontrola etapu B (`+pl`)

Wpis przed przebiegiem; po przebiegu dostaje commit, precyzję, sprzęt, datę i wynik. Reguła, próg i wpływ #157:
[`REPRODUCTION.md`](REPRODUCTION.md).

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `lock` (`common/requirements.lock.txt`, lm-eval 0.4.9.1)
- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3`); gdy przebieg go pominie (brak zgody na HF), `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` (etykieta `eurollm-1.7b`). Oba liczy zwykły przebieg z listy `MODELE`, bez osobnego wpisu w `TESTY_MODELU`.
- Zbiór: `allegro/klej-psc@9585582aef37e7747ef174b0ec3b74855da8bad2`, split `test`, n = 1078 (wpis `T27` w `common/zadania.py`), klastry `extract_text` (507), demonstracje z banku splitu `train`
- Komenda przebiegu (w `research/`): `common/ewaluuj.py --zadania T27 --probka pelna --device cuda` z modelem z wiersza wyżej (pełna linia: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T27 ' | grep bielik-1.5b-v3`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234; bootstrap kontroli: `metryki.SEED`, 10 000 powtórzeń
- Precyzja: float32 (domyślna w `MODELE`); niezapisane, dopóki przebieg nie zapisze pola `dtype`
- Sprzęt i data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/psc/bielik-1.5b-v3/results.json`, próbki `probki/T27_space.jsonl.gz`
- Kontrola z próbek (różnica F1 modelu i F1 stałej „Tak”, SE B parowane po klastrach `extract_text`, obok udział predykcji „Tak” i `acc`), w `research/`:

```bash
python - results/central-run/psc/bielik-1.5b-v3/probki/T27_space.jsonl.gz <<'PY'
import gzip, json, sys
sys.path[:0] = ["common", "tools"]
import metryki as M, statystyka as S, zadania as Z, ewaluuj as E
cfg = Z.konfiguracje("T27")[0][1]
f, pmi = E.funkcja_korpusowa(cfg, "f1"), E.z_pmi(cfg)
p = [json.loads(l) for l in gzip.open(sys.argv[1], "rt", encoding="utf-8")]
o = [M.oceny_mc(s, pmi) for s in p]
z, q, k = [x["gold"] for x in o], [x["pred"] for x in o], [s["doc"]["extract_text"] for s in p]
r = M.korpusowa_z_niepewnoscia(z, q, lambda z, q: f(z, q) - f(z, [1] * len(z)), klastry=k)
print({"f1": f(z, q), "b": f(z, [1] * len(z)), **r, "z": r["value"] / r["se"] if r["se"] else None,
       "werdykt": S.werdykt(r["value"] / r["se"]) if r["se"] else S.NIEROZSTRZYGALNE,
       "udzial_tak": sum(q) / len(q), "acc": sum(x["acc"] for x in o) / len(o)})
PY
```

## Smoke test przed przebiegiem

Wyrenderowane 2026-11-18 funkcjami repo, bez wag: `zadania.konfiguracje("T27", "hf")`, `ewaluuj.zbuduj_zadania`, `ewaluuj.ustaw_bank` dla pełnego splitu (członek `None`, więc klucz banku to `meta["task"]`, jak w linii 560 `common/ewaluuj.py`), potem `fewshot_context` lm-eval 0.4.9.1. Logprobu modelu nie ma: wag nie ładowano. Indeksy są od 0; pytania testu to pierwsze, ostatnie i trzy wylosowane `random.Random(0)` z pozostałych.

Bank (`train`, 4 302 wiersze): indeksy 3743, 2846, 2589, 3187, 844, złote kolejno Tak, Tak, Nie, Tak, Nie. Każde pytanie dostaje te same demonstracje w tej samej kolejności; demonstracja to prompt, spacja i „Nie”/„Tak”, demonstracje rozdziela `\n\n`; prompt pytania kończy się `Prawidłowa odpowiedź:` bez spacji, a oceniane kontynuacje to zawsze `" Nie"` i `" Tak"` (opcje po 3 znakach, więc `acc_norm` równa `acc`). <!-- liczba-spoza-wynikow: ewaluuj.ustaw_bank i fewshot_context na test.csv i train.csv @ 9585582a, 2026-11-18 -->

- indeks 0, złoto Nie: fragment recenzji ponad 400-stronicowej pracy o stereotypach polsko-niemieckich, streszczenie o wyborach parlamentarnych w Anglii; para z różnych artykułów, złoto pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9585582a, wiersz o indeksie 0 -->
- indeks 1077, złoto Tak: tekst o braku środków na pomoc materialną i miejsc w akademikach na początku roku akademickiego, streszczenie o kosztach utrzymania studenta, stypendiach i kwaterunku; ten sam temat, złoto pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9585582a, wiersz o indeksie 1077 -->
- indeks 83, złoto Nie: tekst o staroście powiatu Ostrołęka i kandydatach na stanowiska, streszczenie o opodatkowaniu dochodów ze sprzedaży akcji; różne tematy, złoto pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9585582a, wiersz o indeksie 83 -->
- indeks 789, złoto Nie: tekst o potknięciach rządu i koalicji, streszczenie o krytyce Międzynarodowego Funduszu Walutowego; różne tematy, złoto pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9585582a, wiersz o indeksie 789 -->
- indeks 862, złoto Nie: tekst o magazynie „City Magazine”, streszczenie o startujących w wyborach ugrupowaniach; różne tematy, złoto pasuje. <!-- liczba-spoza-wynikow: test.csv @ 9585582a, wiersz o indeksie 862 -->

Na całym splicie `test`: 1078 pytań, rozkład złotych 328 „Tak” i 750 „Nie”, 0 pustych pól, 507 unikalnych `extract_text` (106 tekstów z obiema etykietami), 406 unikalnych streszczeń; 997 z 1078 wierszy ma streszczenie występujące też w `train`, ale `extract_text` są rozłączne między splitami (0 wspólnych) i żadna para nie występuje w obu splitach (karta, „Znane rozbieżności”). Najdłuższe wejście (BOS, prompt z 5 demonstracjami, kontynuacja) ma 3 593 tokeny Pythii (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5`, pytanie 214), mediana 2 798, najkrótsze 2 638, więc żadne nie przekracza 4096 i `ewaluuj.ogranicz_kontekst` nie zdejmie demonstracji. Tokenizatora Bielika (repo z bramką) nie liczono. <!-- liczba-spoza-wynikow: test.csv i train.csv @ 9585582a oraz tokenizator Pythii @ f3f1b6d5, wyliczenie 2026-11-18 -->
