# IFEval: przepis

Komendy i środowisko obu przebiegów kontrolnych Pythii-1b (etap B) oraz przebiegu Bielika. Czego nie zapisano w chwili pomiaru, oznaczono „niezapisane”. Przebieg centralny dla pozostałych modeli: `bash tools/przebieg_centralny.sh licz` (w `research/`); jedno zadanie: `python common/ewaluuj.py --model hf --repo <repo> --revision <rewizja> --zadania T36 --probka pelna --device cuda --wyjscie results/central-run/ifeval/<etykieta>`.

## Wspólne środowisko

| pozycja | wartość |
|---|---|
| harness | lm_eval `0.4.9.1` |
| transformers / torch | `4.57.6` / `2.8.0+cu128` |
| sprzęt | RTX 5090 (32 GB); wersja sterownika i liczba wątków: niezapisane |
| model kontrolny | `EleutherAI/pythia-1b` @ `f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2` |
| dtype | float32 (Pythia), bf16 (Bielik) |
| rozmiar batcha | 1 |
| dekodowanie | zachłanne, 0-shot, bez szablonu czatu |
| zbiór | `google/IFEval@966cd89545d6b6acfd7638bc708b98261ca58e84`, split `train`, n = 541 |
| seed | harness (python, numpy, torch, fewshot) = (0, 1234, 1234, 1234); bootstrap 20261028 |

## Przebieg 1: 1 BOS (protokół repo, `bench50-v0.3.1-fullB`)

Przebieg przez opakowanie repo (`slayer_eval`), zadanie `ifeval` (wpis `T36`). Dokładna komenda opakowania leży w repo `benchmarks-fabryka-ai` (protokół `bench50-v0.3.1-fullB`) i nie jest tu powielana. Kluczowe parametry:

- `max_gen_toks` 1280, `max_length` 2048
- dokładnie jeden wiodący BOS `<|endoftext|>` (id 0) dla Pythii, wymuszony przez opakowanie
- wynik: `prompt_level_strict_acc` 0,2033 (110/541)

Ten sam protokół dał dla Bielika-11B-v3.1-Instruct @ `d6e755d356ad418d0f0e30b8c428db267415ddb9` (bf16, jeden wiodący BOS `<s>`, id 1, wariant A): `prompt_level_strict_acc` 0,3715 (201/541), `prompt_level_loose_acc` 0,3919 (212/541).

## Przebieg 0: 0 BOS (kontrola, surowy lm-eval CLI)

`add_bos_token=False`, bez opakowania:

```
python -m lm_eval --model hf \
  --model_args pretrained=EleutherAI/pythia-1b,revision=f73d7dcc545c8bd326d8559c8ef84ffe92fea6b2,dtype=float32,add_bos_token=False \
  --tasks ifeval_pin --batch_size 1 --output_path <out> --log_samples
```

`ifeval_pin` to mały YAML w katalogu zadania `ifeval`:

```
include: ifeval.yaml
dataset_kwargs:
  revision: 966cd89545d6b6acfd7638bc708b98261ca58e84
```

Przypina zbiór, żeby użyto tych samych 541 promptów co w przebiegu 1.

Wynik: `prompt_level_strict_acc` 0,1701 (92/541), eksploracyjny/kontrolny (przebieg na vast, 2026-11-19). `max_gen_toks` i `max_length` tego przebiegu nie są podane w komendzie powyżej (domyślne zadania lm-eval, chyba że raport z przebiegu mówi inaczej): tu niezapisane.

## Luka odtwarzalności

- `ifeval_pin.yaml` NIE został zarchiwizowany w dostarczonym `cot_and_0bos.tgz` (archiwum zawiera tylko dwa pliki `samples_*.jsonl`). Treść YAML powyżej jest zrekonstruowana z raportu z przebiegu, nie z archiwum.
- Skrypt `mcnemar.py` wspomniany w raporcie z przebiegu NIE został dostarczony. Liczby McNemara w `REPRODUCTION.md` pochodzą z raportu z przebiegu (liczby CUDA 43 / 25, chi2 4,250 dają się odtworzyć z plików per prompt w `results/`); skrypt, który je wyprodukował, jest niedostępny do ponownego uruchomienia.
- Dla pełnej odtwarzalności przebiegu 0-BOS `ifeval_pin.yaml` (i skrypt McNemara) trzeba dodać do repo.
