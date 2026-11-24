#!/usr/bin/env bash
# Prepares a fresh Ubuntu 22.04 x86_64 machine (VM or bare metal, not a container: the judge runs privileged
# Docker with cgroups) with Docker installed, as root, for `bash run.sh <model-id> --score`.
#
#   bash setup_scoring_vm.sh
#
# Installs git, curl and uv 0.13.7 (which brings Python 3.12), then runs `run.sh --prepare-scoring`: the harness
# clone at its pinned commit with LightCPVerifier at its gitlink, the venv at the harness's uv.lock versions, and the
# judge image `lightcpverifier` built once through the harness's own code. The image id goes to
# .cache/judge-image.json and go-judge's version to .cache/go-judge-version.txt (the Dockerfile pulls go-judge
# "latest" and npm "latest", so a rebuild on another day can differ; do not rebuild between models). The test zips
# (about 3 GB for the 167 problems) are downloaded by the first `run.sh <model-id> --score`.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
UV_VERSION="0.13.7"

[[ "$(id -u)" == 0 ]] || { echo "run as root" >&2; exit 1; }
[[ "$(uname -s)-$(uname -m)" == "Linux-x86_64" ]] || { echo "needs Linux x86_64" >&2; exit 1; }
grep -q 'VERSION_ID="22.04"' /etc/os-release || echo "warning: written for Ubuntu 22.04" >&2
command -v docker >/dev/null || { echo "Docker is not installed" >&2; exit 1; }
docker info >/dev/null || { echo "the Docker daemon is not running" >&2; exit 1; }
# go-judge needs a privileged container with cgroups
docker run --rm --privileged ubuntu:22.04 sh -c 'test -d /sys/fs/cgroup && ls /sys/fs/cgroup >/dev/null' \
  || { echo "cannot run a privileged container with cgroups" >&2; exit 1; }

export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q --no-install-recommends git curl ca-certificates
if ! command -v uv >/dev/null || [[ "$(uv --version | cut -d' ' -f2)" != "$UV_VERSION" ]]; then
  curl -LsSf "https://astral.sh/uv/$UV_VERSION/install.sh" | env UV_INSTALL_DIR=/usr/local/bin sh
fi

bash "$HERE/run.sh" --prepare-scoring
echo "CPU: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2-), $(nproc) logical CPUs," \
     "$(lscpu | awk -F: '/^Core\(s\) per socket/ {c=$2} /^Socket\(s\)/ {s=$2} END {print c*s}') physical cores"
