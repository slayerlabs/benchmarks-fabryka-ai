# Polish Cyberbullying Dataset (T28): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `ptaszynski/PolishCyberbullyingDataset@be3b1236598a02eff6db05ea7ac386afaabc33e8` (wpis `T28` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie modele z `MODELE` i wszystkie zadania (lista etykiet wymaga `POMIN` z pominiętymi modelami); dla tego zadania woła `common/ewaluuj.py --zadania T28 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T28 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/cbd/<model>/results.json`

## Kontrola etapu B (`+pl`)

Wpis przed przebiegiem; po przebiegu dostaje commit, precyzję, sprzęt, datę i wynik. Reguła i próg:
[`REPRODUCTION.md`](REPRODUCTION.md).

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `lock` (`common/requirements.lock.txt`, lm-eval 0.4.9.1)
- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3`), liczony zwykłym przebiegiem z listy `MODELE`, bez osobnego wpisu w `TESTY_MODELU`. Bez zapasu: gdy przebieg go pominie (brak zgody na HF albo `POMIN`), werdykt to „bez kontroli: nierozstrzygnięte”, bo wiersz leaderboardu EuroLLM-1.7B jest pod b ([`REPRODUCTION.md`](REPRODUCTION.md)).
- Zbiór: `ptaszynski/PolishCyberbullyingDataset@be3b1236598a02eff6db05ea7ac386afaabc33e8`, split `test`, n = 1000 (wpis `T28` w `common/zadania.py`), demonstracje z banku splitu `train`
- Komenda przebiegu (w `research/`): linia `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T28 ' | grep bielik-1.5b-v3`, czyli `common/ewaluuj.py --model hf --repo speakleash/Bielik-1.5B-v3 --revision 4b25049621bf3952a1fc9314c89773102eda0333 --model_path /workspace/modele/bielik-1.5b-v3 --zadania T28 --probka pelna --device cuda --batch 1 --eval_gpu <GPU> --etykieta bielik-1.5b-v3 --wyjscie /workspace/wyniki/cbd/bielik-1.5b-v3` (nazwę GPU i katalog wag, przy kilku GPU z sufiksem `.gpu<N>`, ustawia przebieg)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234; bootstrap kontroli: `metryki.SEED`, 10 000 powtórzeń
- Precyzja: float32 (domyślna w `MODELE`); niezapisane, dopóki przebieg nie zapisze pola `dtype`
- Sprzęt i data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/cbd/bielik-1.5b-v3/results.json`, próbki `probki/T28_space.jsonl.gz`
- Kontrola z próbek (różnica makro-F1 modelu i makro-F1 stałej klasy 0 „nieszkodliwa”, SE B parowane po klastrach `TEXT`, spełniona przy dodatniej różnicy i z ≥ 2, obok udział predykcji klasy 0 i `acc`), w `research/`:

```bash
python - results/central-run/cbd/bielik-1.5b-v3/probki/T28_space.jsonl.gz <<'PY'
import gzip, json, sys
sys.path[:0] = ["common", "tools"]
import metryki as M, statystyka as S, zadania as Z, ewaluuj as E
cfg = Z.konfiguracje("T28")[0][1]
f, pmi = E.funkcja_korpusowa(cfg, "f1"), E.z_pmi(cfg)
p = [json.loads(l) for l in gzip.open(sys.argv[1], "rt", encoding="utf-8")]
o = [M.oceny_mc(s, pmi) for s in p]
z, q, k = [x["gold"] for x in o], [x["pred"] for x in o], [s["doc"]["TEXT"] for s in p]
r = M.korpusowa_z_niepewnoscia(z, q, lambda z, q: f(z, q) - f(z, [0] * len(z)), klastry=k)
print({"f1": f(z, q), "b": f(z, [0] * len(z)), **r, "z": r["value"] / r["se"] if r["se"] else None,
       "werdykt": S.werdykt(r["value"] / r["se"]) if r["se"] else S.NIEROZSTRZYGALNE,
       "spelniona": bool(r["se"]) and r["value"] / r["se"] >= 2,
       "udzial_klasy0": sum(1 for x in q if x == 0) / len(q), "acc": sum(x["acc"] for x in o) / len(o)})
PY
```

## Smoke test przed przebiegiem

Wyrenderowane 2026-11-18 funkcjami repo, bez wag: `zadania.konfiguracje("T28", "hf")`, `ewaluuj.zbuduj_zadania`, `ewaluuj.ustaw_bank` dla pełnego splitu (członek `None`, więc klucz banku to `meta["task"]`, jak w linii 560 `common/ewaluuj.py`), potem `fewshot_context` lm-eval 0.4.9.1. Logprobu modelu nie ma: wag nie ładowano. Indeksy są od 0; pytania testu to pierwsze, ostatnie i trzy wylosowane `random.Random(0)` z pozostałych. Plik testu jest anonimizowany (`v2_test_anonymized.tsv`), więc poniżej nie ma cytatów wypowiedzi — tylko kategoria i jedno zdanie opisu.

Bank (`train`, 10 038 wierszy): indeksy 9474, 5594, 2140, 7928, 7929, złote kolejno 1 (szyderstwo), 0, 0, 0, 0 (puste `CATEGORIES` mapuje `.get(..., 0)` na „nieszkodliwa”); dwa ostatnie wiersze to identyczny tekst, więc jedna demonstracja powtarza się dwa razy, a 4 z 5 demonstracji to „nieszkodliwa”. Każde pytanie dostaje te same demonstracje w tej samej kolejności; prompt pytania kończy się `Kategoria:` bez spacji, a sześć kontynuacji to spacja i kategoria (`target_delimiter` spacja): ` nieszkodliwa`, ` szyderstwo`, ` obelga`, ` insynuacja`, ` groźba`, ` molestowanie`. Długości opcji w znakach (do `acc_norm`): 12, 10, 6, 10, 6, 12. <!-- liczba-spoza-wynikow: ewaluuj.ustaw_bank i fewshot_context na v2 @ be3b1236, 2026-11-18 -->

- indeks 0, złoto 1 „szyderstwo”: ironiczna wypowiedź o politykach i piwie; etykieta pasuje. <!-- liczba-spoza-wynikow: v2_test_anonymized.tsv @ be3b1236, wiersz o indeksie 0 -->
- indeks 999, złoto 0: krótka, spokojna uwaga o grupie osób; puste `CATEGORIES` → 0, etykieta pasuje. <!-- liczba-spoza-wynikow: v2_test_anonymized.tsv @ be3b1236, wiersz o indeksie 999 -->
- indeks 395, złoto 0: żartobliwa uwaga o „rekinach”; puste `CATEGORIES` → 0, etykieta pasuje. <!-- liczba-spoza-wynikow: v2_test_anonymized.tsv @ be3b1236, wiersz o indeksie 395 -->
- indeks 777, złoto 0: rzeczowe pytanie o zakres zaproszeń; puste `CATEGORIES` → 0, etykieta pasuje. <!-- liczba-spoza-wynikow: v2_test_anonymized.tsv @ be3b1236, wiersz o indeksie 777 -->
- indeks 865, złoto 0: przyjacielska odpowiedź z żartem, ze śladami anonimizacji w treści; puste `CATEGORIES` → 0, etykieta pasuje. <!-- liczba-spoza-wynikow: v2_test_anonymized.tsv @ be3b1236, wiersz o indeksie 865 -->

Na całym splicie `test`: 1 000 pytań, rozkład złotych 811/75/64/41/6/3 po indeksach 0–5, 0 pustych pól `TEXT`; 961 unikalnych tekstów i 39 grup identycznych (78 wierszy, wszystkie pary), w tym jedna grupa z różnymi etykietami (wiersze 64 i 65, indeksy od 0); 4 wiersze testu mają tekst występujący też w `train` (karta, „Kontaminacja”). 26 wierszy zawiera `"` i 27 zawiera `\`, a prompt opakowuje wypowiedź w `"..."` bez escapowania (karta, „Znane rozbieżności”) — obserwacja, dane niepoprawione. Najdłuższe wejście (BOS, prompt z 5 demonstracjami, najdłuższa opcja) ma 1 004 tokeny Pythii (`EleutherAI/pythia-1b-v0` @ `f3f1b6d5`, pytanie 912), mediana 771, najkrótsze 750, więc żadne nie przekracza 4096 i `ewaluuj.ogranicz_kontekst` nie zdejmie demonstracji. Tokenizatora Bielika (repo z bramką) nie liczono. <!-- liczba-spoza-wynikow: v2_test_anonymized.tsv @ be3b1236 i tokenizator Pythii @ f3f1b6d5, wyliczenie 2026-11-18 -->
