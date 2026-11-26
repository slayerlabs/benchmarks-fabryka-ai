# CzyWiesz (DYK) (T25): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `allegro/klej-dyk@dd7c3c3bb336738c853ea17c64b85d876e6714a9` (wpis `T25` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie modele z `MODELE` i wszystkie zadania (lista etykiet wymaga `POMIN` z pominiętymi modelami); dla tego zadania woła `common/ewaluuj.py --zadania T25 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T25 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/dyk/<model>/results.json`

## Kontrola etapu B (`+pl`)

Wpis przed przebiegiem; po przebiegu dostaje commit, precyzję, sprzęt, datę i wynik. Reguła, próg i wpływ #157:
[`REPRODUCTION.md`](REPRODUCTION.md).

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `lock` (`common/requirements.lock.txt`, lm-eval 0.4.9.1)
- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3`). Gdy przebieg go pominie (brak zgody na HF), werdykt brzmi „bez kontroli: nierozstrzygnięte”; `utter-project/EuroLLM-1.7B` nie jest zapasem, bo w eksporcie z 2026-11-18 ma `dyk_mc` 16,89% < b = 28,93% (0,289277). <!-- liczba-spoza-wynikow: eksport all_data.json z 2026-11-18, SHA-256 68cc602c56518b6127d463da5b2af3847ffaad203855b74d6ded050e80fb96ec -->
- Zbiór: `allegro/klej-dyk@dd7c3c3bb336738c853ea17c64b85d876e6714a9`, split `test`, n = 1029 (wpis `T25` w `common/zadania.py`), demonstracje z banku splitu `train`
- Komenda przebiegu (w `research/`): `common/ewaluuj.py --zadania T25 --probka pelna --device cuda` z modelem z wiersza wyżej (pełna linia: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T25 ' | grep bielik-1.5b-v3`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234; bootstrap kontroli: `metryki.SEED`, 10 000 powtórzeń
- Precyzja: float32 (domyślna w `MODELE`); niezapisane, dopóki przebieg nie zapisze pola `dtype`
- Sprzęt i data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/dyk/bielik-1.5b-v3/results.json`, próbki `probki/T25_space.jsonl.gz`
- Kontrola z próbek (różnica F1 modelu i F1 stałej „Tak”, SE B parowane po klastrach `question`, obok udział predykcji „Tak” i `acc`), w `research/`:

```bash
python - studies/2026-10-lm-eval-benchmarks/results/central-run/dyk/bielik-1.5b-v3/probki/T25_space.jsonl.gz <<'PY'
import gzip, json, sys
sys.path[:0] = ["common", "tools"]
import metryki as M, statystyka as S, zadania as Z, ewaluuj as E
cfg = Z.konfiguracje("T25")[0][1]
f, pmi = E.funkcja_korpusowa(cfg, "f1"), E.z_pmi(cfg)
p = [json.loads(l) for l in gzip.open(sys.argv[1], "rt", encoding="utf-8")]
o = [M.oceny_mc(s, pmi) for s in p]
z, q, k = [x["gold"] for x in o], [x["pred"] for x in o], [s["doc"]["question"] for s in p]
r = M.korpusowa_z_niepewnoscia(z, q, lambda z, q: f(z, q) - f(z, [1] * len(z)), klastry=k)
print({"f1": f(z, q), "b": f(z, [1] * len(z)), **r, "z": r["value"] / r["se"] if r["se"] else None,
       "werdykt": S.werdykt(r["value"] / r["se"]) if r["se"] else S.NIEROZSTRZYGALNE,
       "spelniona": bool(r["se"]) and r["value"] / r["se"] >= 2,
       "udzial_tak": sum(q) / len(q), "acc": sum(x["acc"] for x in o) / len(o)})
PY
```

## Smoke test przed przebiegiem

Osiem pytań `test` (indeks od 0 w `test.csv` @ `dd7c3c3`): pierwsze, ostatnie, pięć losowych spośród pozostałych
(`random.Random(1234).sample`) i pierwsze z odpowiedzią „Tak”. Prompt wyrenderowało zadanie lm-eval `T25` w
środowisku `lock` (lm-eval 0.4.9.1) z bankiem ustawionym przez `ewaluuj.ustaw_bank`, czyli tak jak w przebiegu:
5 demonstracji z `train` (złote Tak, Nie, Nie, Nie, Nie) rozdzielonych pustą linią, każda zakończona
`Prawidłowa odpowiedź: <Tak|Nie>`, potem pytanie bez odpowiedzi. Oceniane kontynuacje to zawsze `" Nie"` i `" Tak"`;
złoto to `target` (0 = Nie, 1 = Tak). Logprobu modelu nie ma: wag nie ładowano. <!-- liczba-spoza-wynikow: zadanie lm-eval T25 @ dd7c3c3, ewaluuj.ustaw_bank, odczyt 2026-11-17 -->

- indeks 0, `czywiesz4267`, złoto Nie: pytanie o rok powstania „Silikonów Polskich”, odpowiedź opisuje Synthos i jego historię bez tej firmy; pytanie i odpowiedź mają w prompcie podwojone cudzysłowy (niżej). <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 0 -->
- indeks 1028, `czywiesz353`, złoto Nie: „kto utworzył Sojusz 8 Marca?”, odpowiedź mówi o wyjściu ministrów z rządu w 2011 r., nie o założycielach. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 1028 -->
- indeks 16, `czywiesz3890`, złoto Nie: pytanie o zadania wezyra, odpowiedź to biogram jednego wezyra. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 16 -->
- indeks 72, `czywiesz3971`, złoto Nie: pytanie o Muzeum Narodowe w Pekinie, odpowiedź o Muzeum Narodowym w Warszawie. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 72 -->
- indeks 186, `czywiesz1321`, złoto Nie: pytanie o deklarację dedykowaną Marii Antoninie, odpowiedź o deklaracjach procedur w Pascalu. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 186 -->
- indeks 240, `czywiesz4551`, złoto Nie: pytanie o misje z pojazdami Wiesel, odpowiedź o źródle zasilania. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 240 -->
- indeks 903, `czywiesz1321`, złoto Nie: to samo pytanie co indeks 186 (jeden klaster `question`), odpowiedź o Powszechnej Deklaracji Praw Człowieka. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 903 -->
- indeks 6, `czywiesz1319`, złoto Tak: „jakie utwory komponowała May Aufderheide?”, odpowiedź wymienia „The Thriller Rag”. <!-- liczba-spoza-wynikow: test.csv @ dd7c3c3, wiersz o indeksie 6 -->

Złoto pasuje do pytania w każdym z ośmiu wierszy; każdy prompt ma dokładnie 5 demonstracji i pytanie (długość
kontekstu w całym teście od 2 257 do 3 703 znaków). Na całym teście: 0 pustych pól, `target` zawsze liczba 0 albo 1,
264 unikalne `q_id` = 264 klastry `question`. Dziwna rzecz z danych: 91 z 1029 wierszy ma pole zaczynające się od
cudzysłowu z podwojonymi cudzysłowami w środku (28 wierszy z takim `question`, 7 różnych pytań; 74 z takim `answer`),
np. `Pytanie: ""kiedy powstało … ""Silikony Polskie""?""`. To ślad podwójnego cytowania CSV w zbiorze HF, ten sam w
leaderboardzie (ten sam plik i YAML), więc nie odróżnia kodu repo od kodu forka; demonstracje banku go nie mają. <!-- liczba-spoza-wynikow: test.csv i train.csv allegro/klej-dyk @ dd7c3c3, wyliczenie 2026-11-17 -->
