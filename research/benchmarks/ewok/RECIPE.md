# EWoK: przepis

Każdy wynik z [`README.md`](README.md) i [`REPRODUCTION.md`](REPRODUCTION.md) ma tu wpis. Komendy uruchamiasz w
`research/`, chyba że napisano inaczej. Czego nie zapisano w czasie pomiaru, ma dopisek „niezapisane”.

## Wspólne

- Commit kodu: `main` @ `0e787f6001ac70431ef378dd3f2324b2e1cf7270` plus kod z gałęzi `research/ewok` (PR #93). Hash z
  gałęzi roboczej znika po spłaszczeniu historii.
  - Wyniki w `results/ewok.json` liczy reguła `authors` (domyślna w `ewok.py score`), przebiegi z 2026-11-03 wieczorem.
  - Poprzednia reguła `plain` (`results/ewok_plain.json`, `results/gpt2-xl-plain/`): pliki per rekord policzył kod
    `benchmarks/ewok-pl/ewok.py licz --dane en --bez-bos` z gałęzi `research/ewok-pl` @
    `7c63dfe2977e2d8f52066f85531423c5185adda1`. To ta sama reguła co `ewok.py score --rule plain`. Pliki per rekord
    pozostałych modeli w tej regule leżą w historii gałęzi, commit `aa45f59`, `results/<model>/ewok.jsonl.gz`.
- Środowisko naszego kodu: lokalne `.venv-gpu` (Python 3.12.2, `torch 2.10.0+cu130`, `transformers 5.19.0` z PyPI,
  `tokenizers 0.23.3`). Przebieg w środowisku z `common/requirements.lock.txt`: niezapisane.
- Zbiór: [`ewok-core/ewok-core-1.0` @ `34d912a608066c92e2990a0328ffc3bd9a716042`](https://huggingface.co/datasets/ewok-core/ewok-core-1.0/tree/34d912a608066c92e2990a0328ffc3bd9a716042),
  `data/test/ewok-core-1.0.parquet`, 4374 rekordy (repo z bramką zgody). sha256 pliku: niezapisane.
- Seed: forward deterministyczny, bez próbkowania. Bootstrap po szablonach i test permutacyjny: seed i liczba
  powtórzeń z `common/metryki.py` (`SEED`, `POWTORZENIA`, zapisane w `results/ewok.json`, `protocol.bootstrap`).
- Precyzja: float32, chyba że wpis mówi inaczej.
- Sprzęt: 1× NVIDIA GeForce RTX 5060 Ti 16 GB, Windows 11. Modele liczone po kolei, jeden proces naraz.
- Data: 2026-11-03.

## Model kontrolny: gpt2-xl naszym kodem (`results/gpt2-xl/`)

- Model: [`openai-community/gpt2-xl` @ `15ea56dee5df4983c59b2538573817e1667135e2`](https://huggingface.co/openai-community/gpt2-xl/tree/15ea56dee5df4983c59b2538573817e1667135e2)
  (pliki `*.json`, `*.safetensors`, `*.txt` przez `snapshot_download`).
- Komenda: `python benchmarks/ewok/ewok.py score --model <katalog gpt2-xl> --out benchmarks/ewok/results/gpt2-xl`
  (przebieg: batch 32, czas 137 s).
- Wynik: `results/ewok.json`, klucz `models/gpt2-xl`. Per rekord: `results/gpt2-xl/ewok.jsonl.gz`.

## Slayer 1.06 i pięć modeli odniesienia

Wszystkie z tą samą komendą, reguła `authors`, z batchem 8 (przebieg lokalny, nie przebieg centralny, jeden model
naraz):

```bash
python benchmarks/ewok/reference/check_loading.py --model <katalog modelu>   # tylko modele HF
python benchmarks/ewok/ewok.py score --model <katalog modelu> --batch 8 --out benchmarks/ewok/results/<model>
```

| `<model>` (katalog wyników) | repo HF @ rewizja | tokeny specjalne tokenizera, token wyłączany przed softmaxem |
|---|---|---|
| `Slayer1B-1.06` | `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609` | brak; `<\|endoftext\|>` (EOS, brak pad). Forward z `common/slayer_model.py` |
| `Qwen3.5-0.8B-Base` | `Qwen/Qwen3.5-0.8B-Base` @ `dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68` | brak; pad `<\|endoftext\|>`. `Qwen3_5ForCausalLM` z `transformers 5.19.0` (PyPI), nie z gałęzi main |
| `LFM2.5-1.2B-Base` | `LiquidAI/LFM2.5-1.2B-Base` @ `7453bca97ca1e67754c4035a4b4c584e1c9dd725` | BOS (id 1); pad `<\|pad\|>` |
| `Bielik-1.5B-v3` | `speakleash/Bielik-1.5B-v3` @ `4b25049621bf3952a1fc9314c89773102eda0333` | BOS `<s>`; pad `</s>` |
| `LFM3-1.7B-Base` | `LiquidAI/LFM3-1.7B-Base` @ `545fc8f4c7b5fa9f405105274cd29c4f8f44b526` | brak; pad `<\|pad\|>`. `trust_remote_code`, kod modelu z tej rewizji |
| `EuroLLM-1.7B` | `utter-project/EuroLLM-1.7B` @ `c730cd9b616799ace3c65e927d63191446f59374` | BOS `<s>`; EOS `</s>` (brak pad) |

- Wynik: `results/ewok.json`, klucze `models/<model>` i `contrasts` (Slayer 1.06 minus każdy model, z `domains` i
  `diff_by_domain_clusters`). Per rekord:
  `results/<model>/ewok.jsonl.gz`.

## Raport z plików per rekord

```bash
python benchmarks/ewok/ewok.py report --models Slayer1B-1.06,gpt2-xl,Qwen3.5-0.8B-Base,LFM2.5-1.2B-Base,Bielik-1.5B-v3,LFM3-1.7B-Base,EuroLLM-1.7B \
  --measured Slayer1B-1.06
python tools/liczby.py && python tools/sprawdz_raporty.py
```

Bez wag: `report` czyta `results/<model>/ewok.jsonl.gz`, gdy nie ma surowego `ewok.jsonl`. Potrzebny jest tylko
zbiór z HF. `--rule` (domyślnie `authors`) wpisuje do `protocol` regułę, którą policzono pliki per rekord. Dla
`results/ewok_plain.json` to `--rule plain`.

## Etap B: kod autorów (`authors_bf16` i `authors_fp32`)

- Środowisko: osobny venv z [`reference/requirements-ref.txt`](reference/requirements-ref.txt) (Python 3.12.2,
  `transformers 4.40.0`, `surprisal` @ `366b074`, instalacja `--no-deps`) plus torch 2.10.0+cu130 z `.venv-gpu`
  przez plik `.pth`.
- Zbiór i wyniki autorów: `analyses/data.zip` z `ewok-core/ewok-paper` @ `9e40d30e242925866ee50448f80a13bcdf971318`.
  Zip jest szyfrowany AES (hasło z TERMS_OF_USE), więc `zipfile` z Pythona go nie czyta. Rozpakowanie:
  `7z x -p<hasło> -o<katalog poza repo> analyses/data.zip`. Ścieżki w zipie są długie, na Windows rozpakuj do krótkiego
  katalogu (my: `D:\ewd`).
- Komenda (w katalogu z klonem `ewok-paper`):

```bash
python <research>/benchmarks/ewok/reference/run_authors.py --ewok-paper ewok-paper --model <katalog gpt2-xl> \
  --data <rozpakowany data.zip> --out <katalog poza repo> --precision bf16   # albo fp32
```

- `authors_bf16`: przebieg wykonano wcześniejszą wersją tego skryptu ze ścieżkami wpisanymi na stałe, z tymi samymi
  wywołaniami kodu autorów. Drugi przebieg bf16 dał identyczne log P.
- `authors_fp32`: `run_authors.py --precision fp32`, przed zmianą nazw argumentów na angielskie (wcześniej
  `--precyzja`, `--wyjscie`).

## Etap C: dodatkowe przebiegi naszego kodu na gpt2-xl

- `ours_plain` (`results/gpt2-xl-plain/`): `python benchmarks/ewok/ewok.py score --model <katalog gpt2-xl> --rule plain
  --out benchmarks/ewok/results/gpt2-xl-plain` (przebieg: stary kod z `--bez-bos`, batch 32).
- `ours_bos` (`results/gpt2-xl-bos/`): `python benchmarks/ewok/ewok.py score --model <katalog gpt2-xl> --rule bos --out
  benchmarks/ewok/results/gpt2-xl-bos` (przebieg: stary kod bez `--bez-bos`, batch 32).
- `ours_bf16` (`results/gpt2-xl-bf16/`): reguła `plain`, wagi w bf16, batch 1, czyli jak `Evaluator` autorów.
  `python benchmarks/ewok/reference/ours_bf16.py --model <katalog gpt2-xl> --rule plain --out
  benchmarks/ewok/results/gpt2-xl-bf16` (przebieg: stary kod).

## Porównanie i próbka testu zgodności

```bash
python benchmarks/ewok/reference/compare.py --data <rozpakowany data.zip> \
  --authors bf16=<wyjście bf16> fp32=<wyjście fp32> \
  --ours ours=benchmarks/ewok/results/gpt2-xl/ewok.jsonl ours_bos=benchmarks/ewok/results/gpt2-xl-bos/ewok.jsonl \
    ours_bf16=benchmarks/ewok/results/gpt2-xl-bf16/ewok.jsonl \
  --out benchmarks/ewok/results/gpt2xl_comparison.json --sample common/tests/data/ewok_zgodnosc.json
python tests/test_ewok_zgodnosc.py
```

Klucze:
- `accuracy/<przebieg>`: trafność po rekordach z SE, z remisem 0,5 i z remisem 0, średnia i wartości 5 wersji;
- `pairs/<A> vs <B>`: zgodność decyzji, różnica trafności A − B z SE, |Δ log P|.

`authors_data_zip` to wyniki autorów z `data.zip`. `compare.py` czyta surowe `ewok.jsonl`, więc pliki `.gz` trzeba
najpierw rozpakować.
