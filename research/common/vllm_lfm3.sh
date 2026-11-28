#!/usr/bin/env bash
# Serves LiquidAI/LFM3-1.7B with vLLM for the run.sh of ifbench, ifstruct and multi-if (model-id lfm3-1.7b):
# bash vllm_lfm3.sh. One GPU is enough (bf16 weights are 3.4 GB); DATA_PARALLEL=N serves one copy on each of N GPUs
# behind the same address. Listens on 127.0.0.1:8000 only, served model name "lfm3". No token needed.
#
# LFM3-1.7B card, "Evaluation details": vLLM, bf16, temperature 0.6 and top_p 0.95, reasoning on (the template's
# default). IFBench and IFStruct send only temperature, so top_p is set here; everything else stays at vLLM's neutral
# values (--generation-config vllm), as benchmarks/docs/methodology.md, section 3, asks.
# The template opens <think> in the prompt; --reasoning-parser deepseek_r1 puts the text up to </think> into
# `reasoning`, so the harnesses score, and carry into the next turn, only the answer in `content`.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VLLM_LFM3_VENV:-$HERE/.venv-vllm-lfm3}"

MODEL_REPO="LiquidAI/LFM3-1.7B"
MODEL_REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"  # as in research/benchmarks/ifeval/lfm3.sh
VLLM_VERSION="0.34.0"  # the first release with Lfm3ForCausalLM

command -v uv >/dev/null || python3 -m pip install -q uv
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
uv pip install --python "$VENV/bin/python" "vllm==$VLLM_VERSION"

# 65,536 tokens: a Multi-IF third turn (two earlier turns, without their thinking) plus 32,768 output tokens.
exec "$VENV/bin/vllm" serve "$MODEL_REPO" --revision "$MODEL_REVISION" --served-model-name lfm3 \
  --host 127.0.0.1 --port 8000 --dtype bfloat16 --max-model-len 65536 --reasoning-parser deepseek_r1 \
  --generation-config vllm --override-generation-config '{"top_p": 0.95}' \
  --data-parallel-size "${DATA_PARALLEL:-1}" --seed 0
