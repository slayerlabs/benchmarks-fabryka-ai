# Protocol: Slayer 1B 1.09, step 70 000, on the 15 tests of the full run 2026-11

Fixed before the first result. Settings and the reading of the results do not change after the results.
Result label: **"1.09, step 70 000, training in progress, preliminary result"**. It is a checkpoint during training,
not a released version. This protocol follows [`../slayer-1.09-k40000/PROTOKOL.md`](../slayer-1.09-k40000/PROTOKOL.md)
and changes only what is named here.

## Question

The values of the 1.09 checkpoint at step 70 000 on the 15 tests of the full run 2026-11, with the same code and
settings as the full run (`research/results/full-run-2026-11/`).

This measurement computes **only step 70 000**. Step 40 000 and 1.08 are not recomputed on the same hardware, so it
makes no paired comparison and gives no verdict "better" or "worse" (see "Reading").

## Model

| label | source | weights |
|---|---|---|
| `slayer1b-1.09-k70000` | `SlayerLab/Slayer1B-1.09-checkpoints` @ `adfaf3fd5402bc7f3adbfe077798f20262979433`, file `wagi_70000.pt` | sha256 `9ed73494fc139422f5314f72b4f970242454a7ab9d8caceee6b52fe5bdfc40c0` (LFS sha256 on the Hub) |

- The checkpoint takes the path of the k40000 measurement: `konwertuj.py` with the 1.08 template
  (`SlayerLab/Slayer1B-1.08` @ `5f854a0cc7160594d54d1788d37a44e8ebabe16c`), `.pt` →
  `tools/ewaluacja/modele/slayer1b-1.09-k70000/model.safetensors`, loader `slayer-ckpt`. The sha256 of the converted
  file, computed locally before the instance, is in `SUMY_WAG_CKPT` (`tools/ewaluacja/ewaluacja.py`); the runner
  refuses a different file.
- **Start condition:** architecture and tokenizer of `wagi_70000.pt` equal to 1.08
  (`../slayer-1.09-k40000/code/sprawdz_architekture.py`), checked locally and again on the instance. Any difference
  stops the measurement.

## Code and environment

- Branch `research/full-run-109-k70000` from `origin/main`, cloned on the instance (the commit is recorded in
  `logi/commit.txt`). `research/common/` unchanged (same `runner_sha256` as the full run). The runner
  `tools/ewaluacja/ewaluacja.py` gets the model entry, the weight sum, and `nvidia-smi -i` for one runner per GPU;
  none of these changes a number.
- Environment `lock`: a fresh venv with `research/common/requirements.lock.txt` (lm_eval 0.4.9.1, torch 2.8.0 from
  PyPI, CUDA 12.8 build). The image has no torch; the full run used the torch 2.8.0 of a CUDA 12.9 image. EWoK with its
  own code (`ewok.py`).
- float32, TF32 off, batch 1, full splits, the run's shots, the runner's default seed.
- **One vast.ai instance with 8 × RTX 4090** (32 GB disk), one runner per GPU with the tests of
  [`code/plan_gpu.txt`](code/plan_gpu.txt), at most 2 processes per GPU. The queue is
  [`code/kolejka.sh`](code/kolejka.sh), started by [`code/start_zdalny.sh`](code/start_zdalny.sh).

## Tests

The 15 tests of `../slayer-1.09-k40000/PROTOKOL.md`, with the same metrics.

## Reading

- Each test: value, SE and n, in the format of the rest of the run.
- The report may show the published values of step 40 000 and of 1.08 next to them, marked as measured on another
  GPU (RTX 5090) and environment, as context only: no difference between them gets a verdict, and none is reported
  as an improvement or a regression.
- A value of 1.000, or more than 5 points below the random baseline, is a code error, not a result.
- Paired comparisons with step 40 000 and 1.08 need those models recomputed on the same hardware, under a protocol
  of their own.

## Results

- Results in `research/results/full-run-2026-11/<test>/slayer1b-1.09-k70000/`, in the format of the rest of the run,
  with rows in `manifest.jsonl`. The published values of the run do not change.
- This directory: protocol, code, logs, and a sha256 manifest of the raw samples.

## Budget

One 8 × RTX 4090 instance (about 3 USD/h), rented and destroyed by the maintainer. About 1.5 h of computation is
expected from the k40000 times; BLiMP on one GPU is the longest part. Hard limit 4 h (`timeout` in
`start_zdalny.sh`).
