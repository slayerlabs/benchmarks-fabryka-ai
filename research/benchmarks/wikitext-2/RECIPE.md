# WikiText-2: przepisy

Wszystkie komendy uruchamiasz w `research/`. Wszystko niżej pochodzi z raportów, kodu i historii gita tego
repo; czego nigdzie nie zapisano, ma dopisek „nie zapisano”.

Wspólne dla wszystkich wyników:

- Zbiór: `EleutherAI/wikitext_document_level` @ `647234772b9554e208af6c826f23b99e3cac88c8`, konfiguracja
  `wikitext-2-raw-v1`, split `test`, wszystkie 62 dokumenty (`WIKI_REW` w `common/hipoteza_formatu.py`, T03
  w `common/zadania.py`).
- Elementy lm-eval: detokenizer z `lm_eval/tasks/wikitext/preprocess_wikitext.py` zainstalowanego
  `lm-eval 0.4.9.1` (identyczny z commitem `6d2abda4fd171e68a8789330c4149e37c1ca0bda`, kopia w `lm_eval_src/`),
  okna rolling z `lm_eval.utils`.
- Seed: niepotrzebny (deterministyczny forward, bez próbkowania, bez przykładów w prompcie).
- Precyzja: `float32` (domyślny `dtype` klasy `ModelSlayer` w `common/slayer_model.py`; tablice RoPE liczone
  w `float64` i rzutowane na `float32`).
- Korekta mianownika: commit `3ed788ca418e4375757d28581f1bd81c830173f5` (2026-10-31), przeliczenie bez
  modelu przez `python benchmarks/wikitext-2/przelicz_mianownik.py` (skaluje ln(ppl) przez stary / nowy
  mianownik; plik, który ma już pole `metoda`, zostaje bez zmian, więc ponowne uruchomienie niczego nie
  zmienia). Stare wartości zostają w polu `przed_korekta` każdego pliku.

## Slayer 1.06, przebieg kontrolny (`analyses/answer-format/results/raport_formatu.json`, `slayer_wikitext_kontrola`)

- Commit kodu przebiegu forwardu: nie zapisano; wynik pierwszy raz trafił do commitu
  `626449db17b9f501ceaaddcdc3cca7eba2d31b81` (2026-10-30), ze starym mianownikiem.
- Środowisko: `common/requirements.lock.txt` (`transformers 4.57.6`, `torch 2.8.0`, `lm-eval 0.4.9.1`); czy
  przy przebiegu był zainstalowany dokładnie ten lockfile: nie zapisano.
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, pobrany do
  `models/slayer-1.06` (komenda w `research/README.md`).
- Komenda (obecny kod, od razu z poprawnym mianownikiem):
  `python common/hipoteza_formatu.py wikitext --model models/slayer-1.06 --wyjscie <katalog>`; plik
  `<katalog>/wikitext.json` czyta potem `analyses/answer-format/analiza_formatu.py`. Dokładny katalog
  wyjścia i urządzenie: nie zapisano.
- Sprzęt: nie zapisano.
- Data: 2026-10-30 (forward), 2026-10-31 (przeliczenie mianownika).

## Slayer 1.06, A i B (`slayer-1b/wygaszanie/wyniki/{1.06,A,B}/wikitext.json`, `porownanie.json`)

- Commit kodu: wyniki pierwszy raz w `626449db17b9f501ceaaddcdc3cca7eba2d31b81`; commit kodu skopiowanego
  na instancję GPU: nie zapisano.
- Środowisko: obraz Dockera `pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel` (`torch 2.6.0+cu124`) na
  wynajętej instancji (`slayer-1b/wygaszanie/README.md`); wersje transformers i lm-eval na instancji: nie
  zapisano.
- Modele:
  - `1.06`: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` (`wyniki/pobrane.json`).
  - `A` (liniowe wygaszanie LR do 0) i `B` (stały LR): 150 kroków od `ckpt_13848.pt` z
    `SlayerLab/Slayer1B-1.06-checkpoints` @ `1113e3e657c1e82d0da09c1fb6d08a356edb8aa3` (sha256 w
    `wyniki/pobrane.json`), checkpoint `ckpt @ 13998` przekonwertowany przez `konwertuj.py`. Wagi A i B nie
    są opublikowane; gdzie leżą: nie zapisano.
- Komenda: `python wygaszanie/ewal.py --model <katalog modelu> --wyjscie wyniki/<etykieta> --device cuda`
  (uruchamiane z `slayer-1b/`); woła `cmd_wikitext` po zadaniach wyboru.
- Sprzęt: vast.ai, NVIDIA GeForce RTX 4090 (instancja z dwiema kartami, `slayer-1b/wygaszanie/README.md`).
- Data: 2026-10-30 (forward), 2026-10-31 (przeliczenie mianownika).

## Diagnoza mianownika (`results/bajty.json`, `results/mianownik.json`)

- Commit kodu: `3ed788ca418e4375757d28581f1bd81c830173f5`.
- Środowisko: dowolny Python z `datasets`; użyte wersje: nie zapisano.
- Model: brak (tylko bajty i słowa; sumę NLL odtwarza się z zapisanej perpleksji).
- Komendy:
  - `python benchmarks/wikitext-2/bajty.py` zapisuje `benchmarks/wikitext-2/results/bajty.json`
    (obie konfiguracje `wikitext-2-raw-v1` i `wikitext-2-v1`, bajty per dokument).
  - `python benchmarks/wikitext-2/mianownik.py benchmarks/wikitext-2/lm_eval_src/6d2abda4fd171e68a8789330c4149e37c1ca0bda_preprocess_wikitext.py benchmarks/wikitext-2/results`
    zapisuje `results/mianownik.json`. Uwaga: ten skrypt porównuje z wartością Space zaokrągloną do trzech
    miejsc po przecinku, więc jego `roznica_po_proc` nie jest końcową różnicą; tę podaje `bajty.json`.
- Sprzęt: CPU (bez modelu); maszyna: nie zapisano.
- Data: 2026-10-31.

## Test regresyjny

`python -m pytest -q tests/test_wikitext_mianownik.py` (bez modelu, bez sieci).
