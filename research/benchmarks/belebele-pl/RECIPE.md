# Belebele-PL (T24): przepis

Jeden wpis na każdy wynik. Wyników jeszcze nie ma: liczy je przebieg centralny, a wpis dostaje wtedy commit, sprzęt i datę.

## Przebieg centralny (Slayer i modele odniesienia)

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `common/requirements.lock.txt` + piny `LOCK_ENV_PINS` / `NEW_ENV_PINS` z `tools/przebieg_centralny.sh` (env `lock`: lm-eval 0.4.9.1, env `new`: lm-eval 0.4.13)
- Modele: lista `MODELE` w `tools/przebieg_centralny.sh` (rewizje z METODOLOGII)
- Zbiór: `facebook/belebele@7899cdfa4e1e0d733fd77c848e2c273cb1d32be2` (wpis `T24` w `common/zadania.py`)
- Komenda (w `research/`): `bash tools/przebieg_centralny.sh licz` liczy wszystkie zadania; dla tego zadania woła `common/ewaluuj.py --zadania T24 --probka pelna --device cuda` (pełne linie: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T24 '`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: niezapisane (przed przebiegiem)
- Sprzęt: niezapisane (przed przebiegiem)
- Data: niezapisane (przed przebiegiem)
- Smoke test: `bash tools/przebieg_centralny.sh proba_cpu` (2 pytania na parę model × zadanie)
- Wynik: `results/central-run/belebele-pl/<model>/results.json`

## Kontrola etapu B (`+pl`)

Wpis przed przebiegiem; po przebiegu dostaje commit, precyzję, sprzęt, datę i wynik. Reguła i próg:
[`REPRODUCTION.md`](REPRODUCTION.md).

- Commit kodu: niezapisane (przed przebiegiem)
- Środowisko: `lock` (`common/requirements.lock.txt`, lm-eval 0.4.9.1)
- Model: `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` (etykieta `bielik-1.5b-v3`). Gdy przebieg go pominie (brak zgody na HF), werdykt brzmi „bez kontroli: nierozstrzygnięte”; `utter-project/EuroLLM-1.7B` nie jest zapasem, bo w eksporcie z 2026-11-18 ma `belebele_mc` 23,11 < b = 27,7095. <!-- liczba-spoza-wynikow: eksport all_data.json z 2026-11-18, SHA-256 68cc602c56518b6127d463da5b2af3847ffaad203855b74d6ded050e80fb96ec -->
- Zbiór: `facebook/belebele@7899cdfa4e1e0d733fd77c848e2c273cb1d32be2`, `pol_Latn`, split `test` (wpis `T24` w `common/zadania.py`), 895 liczonych
- Komenda przebiegu (w `research/`): `common/ewaluuj.py --zadania T24 --probka pelna --device cuda` z modelem z wiersza wyżej (pełna linia: `bash tools/przebieg_centralny.sh plan | grep -- '--zadania T24 ' | grep bielik-1.5b-v3`)
- Seed: python 0, numpy 1234, torch 1234, fewshot 1234
- Precyzja: float32 (domyślna w `MODELE`); niezapisane, dopóki przebieg nie zapisze pola `dtype`
- Sprzęt i data: niezapisane (przed przebiegiem)
- Wynik: `results/central-run/belebele-pl/bielik-1.5b-v3/results.json`, próbki `probki/T24_space.jsonl.gz`
- Kontrola z próbek (parowanie ze stałą `B`, SE K po `link`), w `research/`:

```bash
python - results/central-run/belebele-pl/bielik-1.5b-v3/probki/T24_space.jsonl.gz <<'PY'
import gzip, json, sys
sys.path[:0] = ["common", "tools"]
import metryki as M, statystyka as S, zadania as Z, ewaluuj as E
pmi = E.z_pmi(Z.konfiguracje("T24")[0][1])
p = [json.loads(l) for l in gzip.open(sys.argv[1], "rt", encoding="utf-8")]
o = [M.oceny_mc(s, pmi) for s in p]
print(S.wobec_stalej([x["acc"] for x in o], [x["gold"] for x in o], [s["doc"]["link"] for s in p]))
PY
```

## Smoke test przed przebiegiem

Siedem pytań liczonych w pełnym przebiegu: pierwsze i ostatnie (indeks od 0 w `data/pol_Latn.jsonl` @ `7899cdfa`) i pięć
losowych spośród pozostałych (`random.Random(1234).sample`). Prompt wyrenderowało zadanie lm-eval `T24` w środowisku
`lock` (lm-eval 0.4.9.1) z bankiem ustawionym przez `ewaluuj.ustaw_bank`, czyli tak jak w przebiegu: 5 demonstracji
(indeksy 776, 394, 167, 830, 222, złote B, C, B, C, B) rozdzielonych pustą linią, każda zakończona
`Prawidłowa odpowiedź: <litera>`, potem pytanie bez odpowiedzi. Oceniane kontynuacje to zawsze `" A"`, `" B"`, `" C"`,
`" D"`; złoto to litera z `correct_answer_num`. Logprobu modelu nie ma: wag nie ładowano. <!-- liczba-spoza-wynikow: zadanie lm-eval T24 @ 7899cdfa, ewaluuj.ustaw_bank, odczyt 2026-11-17 -->

- indeks 0, `Accordion/Right_hand` pytanie 1, złoto A: „Czego zgodnie z fragmentem nie można uważać za dokładną wskazówkę…”; A „Aby zwiększyć głośność, naciskaj klawisze z większą siłą” przeczy zdaniu fragmentu o miechach, więc złoto pasuje. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 0 -->
- indeks 899, `Yellowstone_National_Park` pytanie 2, złoto D: „Zwierzęta nieznające ludzi” — fragment mówi, że zwierzęta przyzwyczaiły się do ludzi, a zapachy, odległość i karmienie są wymienione. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 899 -->
- indeks 8, `Ticonderoga_and_Bunker_Hill` pytanie 2, złoto C: „Podczas odpływu” — fragment: „Gdy odpływ otworzył wolne przejście…”. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 8 -->
- indeks 93, `Introduction_to_Paleoanthropology/Genetics/Introduction` pytanie 1, złoto D: „Wyrażona” — fragment: selekcja usuwa wariację z puli wyrażonych genów. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 93 -->
- indeks 120, `Modern_Photography/Lenses` pytanie 2, złoto D: „Gdy szukasz bardziej zaawansowanych ustawień ogniskowej”; A–C to wady obiektywu zmiennoogniskowego z fragmentu. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 120 -->
- indeks 455, `La_La_Land…` pytanie 1, złoto C: „Najlepsza aktorka” — fragment: nominacje dla najlepszego aktora i najlepszej aktorki otrzymali Gosling i Stone. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 455 -->
- indeks 801, `Pests` pytanie 1, złoto D: „Przyczynianie się do poważnych obrażeń” — fragment wyłącza z szkodników zwierzęta, które mogą zranić. <!-- liczba-spoza-wynikow: data/pol_Latn.jsonl @ 7899cdfa, wiersz o indeksie 801 -->

W każdym z siedmiu promptów są dokładnie 5 demonstracji i pytanie, opcje A–D stoją w kolejności `mc_answer1`–`mc_answer4`,
a cudzysłów wokół fragmentu i pytania pochodzi z szablonu. Na wszystkich 895 liczonych: 0 pustych opcji, 3 pytania z dwiema
identycznymi opcjami (indeksy 401, 431, 779, opisane w karcie), żaden dokument banku nie jest wśród nich; cudzysłów `"`
stoi w 2 fragmentach i w 0 pytaniach, więc szablon `"…"` rzadko się z nim miesza. Druga demonstracja banku kończy się
opcją z białym znakiem na końcu (karta: 105 takich opcji w 98 pytaniach, a 1 opcja ma biały znak na początku), który zostaje w prompcie przed `\n`. <!-- liczba-spoza-wynikow: zadanie lm-eval T24 @ 7899cdfa, liczone 895, odczyt 2026-11-17 -->
