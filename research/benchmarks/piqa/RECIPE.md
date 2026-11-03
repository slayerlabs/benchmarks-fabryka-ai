# PIQA (T06): przepis

Jeden wpis na każdy wynik. Protokół: [`PROTOCOL.md`](PROTOCOL.md). Raport: [`results/PIQA.md`](results/PIQA.md).

Wspólne dla wszystkich wpisów:

- Kod: gałąź `research/piqa-slayer106` od `main` @ `53502fe`; liczone w commicie `f932e5e` (`benchmarks/piqa/piqa.py`,
  `benchmarks/piqa/instance.sh`, `common/slayer_lm.py`, `common/slayer_model.py`). Commit squash na `main`: jeszcze
  nieznany, uzupełniany po merge'u.
- Środowisko: `common/requirements.lock.txt` w venv z `--system-site-packages` na obrazie
  `pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime` (torch 2.8.0+cu128, CUDA 12.8); transformers 4.57.6 (PyPI);
  lm-eval 0.4.9.1 (PyPI).
- Dane: `ybisk/piqa` @ `2e8ac2dffd59bac8c3c6714948f4c551a0848bb0` (tasks_50.json); czytane z
  `refs/convert/parquet` @ `142c51238b3ca2bc61e9a075913871b8b600e8e1`, `plain_text/validation/0000.parquet`, sha256
  `40e1677bba609c8801deacc171d76f3e24c083f365c95a1cbda7520c923dfea2`, 1838 wierszy. Pliki Space czytane w
  `SlayerLab/Slayer1B-Benchmarks` @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9`.
- Seedy: python 0, numpy 1234, torch 1234, fewshot 1234 (0-shot); seed bootstrapu 20261028, 10 000 powtórzeń.
- Precyzja: float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`.
- Data: 2026-11-01. Godzina liczenia nie jest zapisana (`meta.json` ma tylko datę); push PROTOCOL.md
  (16:10:03Z) poprzedza push surowych wyników (16:13:49Z), co pokazuje kolejność commitów, nie liczenia.
- Porównanie GPU: zapisane jest tylko `seconds_score`; cena za godzinę, czasy przygotowania i pobierania obiecane w
  PROTOCOL.md nie zostały zapisane.
- Przygotowanie na instancji (w `/workspace`, repo sklonowane do `/workspace/repo`):
  `bash repo/research/benchmarks/piqa/instance.sh setup 5400` (lockfile, dane, wagi; niszczy instancję po
  5400 s).
- Raport (w `research/`): `python benchmarks/piqa/piqa.py report`, potem `python tools/liczby.py`.

## SlayerLab/Slayer1B-1.06

- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, wrapper `slayer` (`common/slayer_lm.py`,
  jeden BOS na żądanie).
- Komenda: `bash repo/research/benchmarks/piqa/instance.sh slayer`, czyli
  `python benchmarks/piqa/piqa.py score --model slayer --pretrained /workspace/slayer-1.06 --repo SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --data /workspace/data --out /workspace/out/slayer-1.06.jsonl.gz --device cuda --batch 1`
- Sprzęt: NVIDIA GeForce RTX 4090 (vast.ai, Wirginia, USA).
- Wynik: `results/raw/slayer-1.06.jsonl.gz` (sha256 w `results/raw/SHA256SUMS`); wartości w `results/piqa.json`,
  klucze `models.slayer-1.06.full` i `models.slayer-1.06.panel`.

## EleutherAI/pythia-1b-v0 (kontrola)

- Model: `EleutherAI/pythia-1b-v0` @ `step143000`, `HFLM` (BOS nie jest dodawany, domyślne ustawienia tokenizera).
- Komenda: `bash repo/research/benchmarks/piqa/instance.sh pythia pythia-1b-v0`, czyli
  `python benchmarks/piqa/piqa.py score --model hf --pretrained EleutherAI/pythia-1b-v0 --repo EleutherAI/pythia-1b-v0 --revision step143000 --data /workspace/data --out /workspace/out/pythia-1b-v0.jsonl.gz --device cuda --batch 1`
- Sprzęt: NVIDIA GeForce RTX 4090 (vast.ai, Wirginia, USA).
- Wynik: `results/raw/pythia-1b-v0.jsonl.gz`; wartości w `results/piqa.json`, klucze `models.pythia-1b-v0.*` i
  `control`.

## EleutherAI/pythia-1b-v0, powtórzenia na innych GPU

- Ta sama komenda z etykietą `pythia-1b-v0_<gpu>`; sprzęt w nazwie pliku i w `<label>.meta.json`.
- Wynik: `results/raw/pythia-1b-v0_<gpu>.jsonl.gz`; wartości w `results/piqa.json`, klucz `gpu_repeats`.
