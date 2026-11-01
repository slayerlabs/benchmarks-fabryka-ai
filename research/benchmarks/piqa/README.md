# PIQA (Space T06)

Slayer 1.06 on PIQA by the Space protocol, with the Pythia-1B v0 control (issue #16). The original card (stage A)
and stages B–C follow in #57.

- [`PROTOCOL.md`](PROTOCOL.md): variant, panel, baselines, control threshold and claims, committed before the first
  raw result.
- [`results/PIQA.md`](results/PIQA.md): report generated from `results/piqa.json`.
- [`RECIPE.md`](RECIPE.md): one entry per result.
- `piqa.py`: `fetch`, `score`, `report`; `instance.sh`: the same on a vast.ai GPU.
- `results/raw/`: one line per question (log-probability of each option, picks, gold, source id), sha256 in
  `SHA256SUMS`.
- Test: `tests/test_piqa.py` (logic on dummies, independent recompute from the raw files).
