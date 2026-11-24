#!/usr/bin/env bash
# One-time setup of the scoring machine for SciCode: a fresh Ubuntu 22.04 x86_64 VM with Docker, run as root from a
# checkout of this repo:
#
#   bash research/api-benchmarks/scicode/setup_scoring_vm.sh
#
# Installs nothing on the host beyond git and curl (apt), then, all under this directory's .cache/ (not committed):
#   - clones SciCode at the pinned commit (.cache/SciCode);
#   - downloads test_data.h5 (1,049,345,865 bytes) from the byte-identical mirror and checks its sha256
#     (.cache/test_data.h5); an existing file with the right sha256 is kept;
#   - builds the scoring image `scicode-scoring` from Dockerfile.scoring (python 3.11.9 pinned by digest, packages
#     from requirements-scoring.lock with hashes);
#   - loads the dataset at the pinned revision into the scoring cache (.cache/hf-scoring), the only revision the
#     offline scorer may find there.
# Afterwards `bash run.sh <model-id> --score` scores an out/<model-id>/ directory copied from the generating machine.
# Scoring needs no GPU; the scorer is sequential (one step at a time), so a few cores and 16 GB RAM are enough.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SCICODE_REPO="https://github.com/scicode-bench/SciCode"
SCICODE_COMMIT="e3158ea011d4235245a547460d3688d7ccbf9900"
H5_URL="https://huggingface.co/datasets/xantheocracy/scicode-mirror/resolve/2f903a64a1c4eb62c7c649b0caf7ecb2c0217590/test_data.h5"
H5_SHA256="48b0272a88b17dbd29777c217e1b4fb2b019b92e11cc2add847409db9541b890"
IMAGE="scicode-scoring"

command -v docker >/dev/null || { echo "docker is required (the VM image ships it)" >&2; exit 1; }
if ! command -v git >/dev/null || ! command -v curl >/dev/null; then
  apt-get update -q && apt-get install -y -q git curl ca-certificates
fi

mkdir -p "$HERE/.cache"
[[ -d "$HERE/.cache/SciCode/.git" ]] || git clone -q "$SCICODE_REPO" "$HERE/.cache/SciCode"
git -C "$HERE/.cache/SciCode" checkout -q "$SCICODE_COMMIT"

H5="$HERE/.cache/test_data.h5"
if [[ ! -f "$H5" ]] || [[ "$(sha256sum "$H5" | cut -d' ' -f1)" != "$H5_SHA256" ]]; then
  curl -fL --retry 5 -o "$H5.part" "$H5_URL"
  mv "$H5.part" "$H5"
fi
echo "$H5_SHA256  $H5" | sha256sum -c -

docker build -q -t "$IMAGE" -f "$HERE/Dockerfile.scoring" "$HERE"
docker run --rm "$IMAGE" python -c "import numpy, scipy, sympy, h5py, matplotlib, datasets; print('scoring image:', \
numpy.__version__, scipy.__version__, sympy.__version__, h5py.__version__, matplotlib.__version__, datasets.__version__)"

# The scorer loads the dataset without a revision; offline it takes the latest cached one, so the cache holds only
# the pinned revision (scicode_runner.py prefetch checks it and records what `main` points to today).
docker run --rm -v "$HERE:$HERE" -w "$HERE" -e HF_HOME="$HERE/.cache/hf-scoring" "$IMAGE" \
  python scicode_runner.py prefetch
echo "setup_scoring_vm.sh: done"
