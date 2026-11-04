# WinoGrande: przepis

Jak odtworzyć każdy wynik. Komendy uruchamiasz w `research/`. Czego nie zapisano w czasie pomiaru: „niezapisane”.

Ten plik powstał przed przebiegiem Pythii. Wyniku tu nie ma.

## Wspólne

- Commit kodu: `09e597c` z `main`, plus ten protokół. Hash gałęzi roboczej znika po spłaszczeniu historii.
- Środowisko: Python 3.9.25, `torch 2.8.0+cu128`, `transformers 4.57.6`, `datasets 3.6.0`, `lm_eval 0.4.9.1`. Wersje odczytane 2026-11-04 z `C:/Users/taki1/bench/.venv-eval`. Transformers to wydanie z PyPI; commit gita nie jest przypięty.
- Model kontroli: `EleutherAI/pythia-1b-v0` @ `step143000`, lokalnie `D:/models/pythia-1b-v0`.
- Zbiór: `allenai/winogrande`, konfiguracja `winogrande_xl`, rewizja `01e74176c63542e6b0bcb004dcdea22d94fb67b5`, split `validation`, n = 1267. Przypięcie rewizji jest w `lm_eval_tasks/winogrande/default.yaml`. Katalog zadania lm-eval `0.4.9.1` skopiowany bez zmiany promptu; dodane jest tylko `dataset_kwargs.revision`.
- Zadanie: `winogrande`, 0-shot, bez instrukcji, bez szablonu czatu, metryka `acc`.
- BOS: `HFLM` ma domyślnie `add_bos_token=False`. Kontekst nie jest pusty, więc przebieg nie dokleja BOS. Tokenizer: `bos_token_id` 0, `add_bos_token` False. `config.json` ma `bos_token_id` 1. Żadnego z nich nie wstawiamy ręcznie. Ustalone przed pomiarem, ze smoke testu tokenów i z kodu `lm_eval/models/huggingface.py` oraz `lm_eval/api/model.py` (`_encode_pair`).
- Seed: `0,1234,1234,1234` (domyślne lm-eval: python, numpy, torch, fewshot).
- Precyzja: float32. Batch: 1.
- Sprzęt: NVIDIA GeForce RTX 5060 Ti, 16311 MiB, Windows 11. Sterownik i liczba wątków: niezapisane.
- Data protokołu: 2026-11-04.
- Próg etapu B, zapisany przed pomiarem: opublikowane `acc` 0,5375. Warunek z issue #27: ±2 pkt, a gdy 2 SE > 2 pkt, ±2 SE. SE z karty to 0,0140, więc 2 SE = 0,0280 > 0,02. Obowiązuje pasmo 0,5095–0,5655. Przewidywanie przed przebiegiem dotyczyło węższego pasma ±2 pkt, czyli 0,5175–0,5575, i brzmiało „tak”.

## Smoke test przed przebiegiem

Pięć pierwszych wierszy `validation`, bez wag w scoringu, sam tokenizer Pythii. Id to indeks w splicie, bo HF nie ma `qID`.

- 0: `Sarah was a much better surgeon than Maria so _ always got the easier cases.` złoto 2. Kontynuacja ` always got the easier cases.`, tokeny `Ġalways Ġgot Ġthe Ġeasier Ġcases .`
- 1: ta sama para, zakończenie `harder cases`, złoto 1.
- 2: `was't ruined`, złoto 2. Literówka zbioru.
- 3: eggplant / toaster, złoto 1.
- 4: ` wakes up late.` tokenizuje się jako `Ġw akes Ġup Ġlate .`, złoto 1.

## Wynik 1: Pythia-1B v0, pełny validation

- Komenda, w `research/`:

```bash
lm_eval --model hf \
  --model_args pretrained=D:/models/pythia-1b-v0,dtype=float32 \
  --tasks winogrande \
  --include_path benchmarks/winogrande/lm_eval_tasks \
  --num_fewshot 0 \
  --batch_size 1 \
  --device cuda \
  --seed 0,1234,1234,1234 \
  --log_samples \
  --output_path benchmarks/winogrande/results/pythia-1b-v0
```

- Data przebiegu: 2026-11-04, około 01:02 czasu lokalnego. Czas liczenia żądań: 57 s po załadowaniu modelu.
- Rewizja wag: lokalny katalog nie ma pola `model_sha` w wyjściu lm-eval (wpisane `main` i pusty sha, bo ścieżka jest lokalna). Commit pliku wag z metadanych pobrania: `f3f1b6d5a78e32208be0866398d0b2d32c0e1ce0`. To jest `step143000` według API HF.
- Wynik: `acc` 0,5445935280189423 (690 z 1267), SE 0,013996485037729782. Plik: `benchmarks/winogrande/results/pythia-1b-v0/D__models__pythia-1b-v0/results_2026-11-04T01-02-51.185008.json`, klucz `results.winogrande.acc,none`. Per pytanie: `samples_winogrande_2026-11-04T01-02-51.185008.jsonl`, pole `doc_id`.
- Różnica wobec 0,5375: +0,007094 (0,71 pkt). W paśmie ±2 pkt (0,5175–0,5575) i w paśmie ±2 SE (0,5095–0,5655). Werdykt słowny: w `REPRODUCTION.md`.

## Wynik 2: Slayer 1.06, pełny validation

Protokół zapisany przed przebiegiem. Wyniku tu jeszcze nie ma.

- Przewidywanie Grzegorza, przed przebiegiem: acc wyjdzie ponad pasmo 0,505–0,584 (Pythia 0,5446 ± 2 SE różnicy, SE różnicy 0,0198).
- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, lokalnie `D:/models/slayer-1.06`. `config.json` ma ten sam sha256 co plik z tej rewizji (`ca38e559…`). `model.safetensors` ma sha256 `e10df6d50101d8424ff7338c97373ab9e151e359a6fcb23108023ac4a6400214`, równy LFS oid tej rewizji. Rozmiar 4 295 670 676 bajtów.
- Ładowanie: nakładka `slayer` z `common/slayer_lm.py` tego worktree. `.pth` w venv wskazuje `C:/Users/taki1/bench/wt-winogrande/research/common`. Przed instalacją wskazywał `D:/projects/benchmarks-fabryka-ai/research/common`.
- BOS: nakładka dokleja jeden token `prefix_token_id` (`<|endoftext|>`, id 0) przed kontekstem w `_encode_pair`. Pythia w wyniku 1 szła bez BOS (`add_bos_token=False`, kontekst niepusty). To nie jest ten sam ciąg tokenów. Zapisane przed pomiarem, z kodu nakładki.
- Reszta jak w wyniku 1: zadanie `winogrande` z przypiętą rewizją zbioru, 0-shot, float32, batch 1, seed `0,1234,1234,1234`, CUDA, RTX 5060 Ti.
- Komenda, w `research/`:

```bash
lm_eval --model slayer \
  --model_args pretrained=D:/models/slayer-1.06,dtype=float32 \
  --tasks winogrande \
  --include_path benchmarks/winogrande/lm_eval_tasks \
  --num_fewshot 0 \
  --batch_size 1 \
  --device cuda \
  --seed 0,1234,1234,1234 \
  --log_samples \
  --output_path benchmarks/winogrande/results/slayer-1.06
```

- Wynik: `acc` 0,5217048145224941 (661 z 1267), SE 0,01403923921648463. Plik: `benchmarks/winogrande/results/slayer-1.06/D__models__slayer-1.06/results_2026-11-04T01-35-01.855277.json`, klucz `results.winogrande.acc,none`. Per pytanie: `samples_winogrande_2026-11-04T01-35-01.855277.jsonl`.
- Data przebiegu: 2026-11-04, około 01:35. Czas liczenia żądań: 80 s po załadowaniu modelu. Wyjście lm-eval: `tokenizer_bos_token` `<|endoftext|>`, id 0.
- Wobec Pythii, te same 1267 zdań: różnica acc Slayer minus Pythia = −0,022889, SE sparowane 0,017767, z = −1,288. Werdykt słowny: niezapisane, pisze go Grzegorz.

## Wynik 3: Pythia z tym samym BOS co nakładka Slayera

Protokół zapisany przed przebiegiem. Nie zastępuje wyniku 1. Wyniku tu jeszcze nie ma.

- Po co: wynik 1 i wynik 2 nie mają tego samego ciągu tokenów. Nakładka dokleja `<|endoftext|>` (id 0) przed kontekstem. `add_bos_token=True` u Pythii tego nie robi, bo tokenizer i tak nie emituje BOS. Skrypt wstawia token w `_encode_pair`, w tym samym miejscu co `common/slayer_lm.py`.
- Model, zbiór, seed, precyzja, batch, sprzęt: jak w wyniku 1.
- Komenda, w `research/`:

```bash
python benchmarks/winogrande/pythia_bos.py --check
python benchmarks/winogrande/pythia_bos.py
```

- Wynik: `acc` 0,5438042620363063 (689 z 1267), SE 0,013998453610924324. Plik: `benchmarks/winogrande/results/pythia-1b-v0-bos/results.json`, klucz `results.winogrande.acc,none`. Per pytanie: `samples_winogrande.jsonl`.
- Wobec Pythii bez BOS, te same 1267: różnica −0,000789, SE sparowane 0,011194, z = −0,071, flipów decyzji 201. Wobec Slayera: różnica Slayer minus ta Pythia = −0,022099, SE sparowane 0,017179, z = −1,286.


