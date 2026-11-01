# PIQA (T06): recipe

One entry per result. Protocol: [`PROTOCOL.md`](PROTOCOL.md). Report: [`results/PIQA.md`](results/PIQA.md).

Common to every entry:

- Code: branch `research/piqa-slayer106` off `main` @ `53502fe`; scored at commit `f932e5e` (`benchmarks/piqa/piqa.py`,
  `benchmarks/piqa/instance.sh`, `common/slayer_lm.py`, `common/slayer_model.py`). The squash commit on `main`: not
  yet known, filled after merge.
- Environment: `common/requirements.lock.txt` in a venv with `--system-site-packages` over the image
  `pytorch/pytorch:2.8.0-cuda12.8-cudnn9-runtime` (torch 2.8.0+cu128, CUDA 12.8); transformers 4.57.6 (PyPI);
  lm-eval 0.4.9.1 (PyPI).
- Data: `ybisk/piqa` @ `2e8ac2dffd59bac8c3c6714948f4c551a0848bb0` (tasks_50.json); read from
  `refs/convert/parquet` @ `142c51238b3ca2bc61e9a075913871b8b600e8e1`, `plain_text/validation/0000.parquet`, sha256
  `40e1677bba609c8801deacc171d76f3e24c083f365c95a1cbda7520c923dfea2`, 1838 rows. Space files read at
  `SlayerLab/Slayer1B-Benchmarks` @ `2d3d73f5c0ee431df9d38bd9619ccb05a26bf9a9`.
- Seeds: python 0, numpy 1234, torch 1234, fewshot 1234 (0-shot); bootstrap seed 20261028, 10 000 replicates.
- Precision: float32, batch 1, `NVIDIA_TF32_OVERRIDE=0`.
- Date: 2026-11-01.
- Setup on the instance (in `/workspace`, repo cloned to `/workspace/repo`):
  `bash repo/research/benchmarks/piqa/instance.sh setup 5400` (lockfile, data, weights; destroys the instance after
  5400 s).
- Report (in `research/`): `python benchmarks/piqa/piqa.py report`, then `python tools/liczby.py`.

## SlayerLab/Slayer1B-1.06

- Model: `SlayerLab/Slayer1B-1.06` @ `ef81be58742544ad32e1afab38db011fec209609`, wrapper `slayer` (`common/slayer_lm.py`,
  one BOS per request).
- Command: `bash repo/research/benchmarks/piqa/instance.sh slayer`, that is
  `python benchmarks/piqa/piqa.py score --model slayer --pretrained /workspace/slayer-1.06 --repo SlayerLab/Slayer1B-1.06 --revision ef81be58742544ad32e1afab38db011fec209609 --data /workspace/data --out /workspace/out/slayer-1.06.jsonl.gz --device cuda --batch 1`
- Hardware: NVIDIA GeForce RTX 4090 (vast.ai, Virginia, US).
- Result: `results/raw/slayer-1.06.jsonl.gz` (sha256 in `results/raw/SHA256SUMS`); values in `results/piqa.json`,
  keys `models.slayer-1.06.full` and `models.slayer-1.06.panel`.

## EleutherAI/pythia-1b-v0 (control)

- Model: `EleutherAI/pythia-1b-v0` @ `step143000`, `HFLM` (no BOS added, tokenizer default).
- Command: `bash repo/research/benchmarks/piqa/instance.sh pythia pythia-1b-v0`, that is
  `python benchmarks/piqa/piqa.py score --model hf --pretrained EleutherAI/pythia-1b-v0 --repo EleutherAI/pythia-1b-v0 --revision step143000 --data /workspace/data --out /workspace/out/pythia-1b-v0.jsonl.gz --device cuda --batch 1`
- Hardware: NVIDIA GeForce RTX 4090 (vast.ai, Virginia, US).
- Result: `results/raw/pythia-1b-v0.jsonl.gz`; values in `results/piqa.json`, keys `models.pythia-1b-v0.*` and
  `control`.

## EleutherAI/pythia-1b-v0, repeats on other GPUs

- Same command with label `pythia-1b-v0_<gpu>`; hardware in the file name and in `<label>.meta.json`.
- Result: `results/raw/pythia-1b-v0_<gpu>.jsonl.gz`; values in `results/piqa.json`, key `gpu_repeats`.
