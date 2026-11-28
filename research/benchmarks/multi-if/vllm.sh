#!/usr/bin/env bash
# Serves Bielik 11B v3.1 Instruct with vLLM for run.sh: bash vllm.sh [model-id]
#   bielik-11b-v3.1-vllm (default)  LFM3-1.7B card sampling, served model name "bielik"
#   bielik-11b-v3.1-vllm-t0.3       Bielik's own sampling, served model name "bielik-t0.3"
# Needs one GPU with at least 48 GB and a Hugging Face token with access to the gated model (HF_TOKEN).
# DATA_PARALLEL=N serves one copy on each of N GPUs behind the same address.
# Listens on 127.0.0.1:8000 only; run.sh reads BASE_URL (default http://127.0.0.1:8000/v1).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VLLM_VENV:-$HERE/.venv-vllm}"
WORK="${WORK_DIR:-$HERE/out}"

BIELIK_REPO="speakleash/Bielik-11B-v3.1-Instruct"
BIELIK_REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"
VLLM_VERSION="0.34.0"
BIELIK_TOOLS_COMMIT="2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09"  # tool-call and reasoning parsers for vLLM
# The chat template's own defaults: the provider system prompt on, date pinned to the run (see README, Deviations).
TEMPLATE_KWARGS='{"provider_system_prompt": true, "current_date": "2026-11-18", "current_day_of_week": "Wednesday"}'

# --generation-config vllm: no sampling defaults from the model's generation_config.json. The Multi-IF harness sends
# top_p itself (run.sh); the server default matches it, as in the runs.
case "${1:-bielik-11b-v3.1-vllm}" in
  bielik-11b-v3.1-vllm) SERVED=bielik; SAMPLING=(--override-generation-config '{"top_p": 0.95}') ;;  # LFM3-1.7B card
  bielik-11b-v3.1-vllm-t0.3) SERVED=bielik-t0.3; SAMPLING=() ;;  # generation_config.json: temperature only, top_p 1.0
  *) echo "unknown model-id: $1 (bielik-11b-v3.1-vllm | bielik-11b-v3.1-vllm-t0.3)" >&2; exit 2 ;;
esac

: "${HF_TOKEN:?set HF_TOKEN (the model is gated)}"
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
uv pip install --python "$VENV/bin/python" "vllm==$VLLM_VERSION" huggingface_hub

mkdir -p "$WORK"
if [[ ! -d "$WORK/bielik-tools/.git" ]]; then
  git init -q "$WORK/bielik-tools"
  git -C "$WORK/bielik-tools" fetch -q --depth 1 https://github.com/speakleash/bielik-tools.git "$BIELIK_TOOLS_COMMIT"
  git -C "$WORK/bielik-tools" checkout -q FETCH_HEAD
fi
TOOLS="$WORK/bielik-tools/tools"
WEIGHTS="$("$VENV/bin/python" -c "from huggingface_hub import snapshot_download as s; print(s('$BIELIK_REPO', revision='$BIELIK_REVISION'))")"

exec "$VENV/bin/vllm" serve "$WEIGHTS" --served-model-name "$SERVED" --host 127.0.0.1 --port 8000 --dtype bfloat16 \
  --max-model-len 32768 --enable-auto-tool-choice \
  --tool-parser-plugin "$TOOLS/bielik_vllm_tool_parser.py" --tool-call-parser bielik \
  --reasoning-parser-plugin "$TOOLS/bielik_vllm_reasoning_parser.py" --reasoning-parser bielik \
  --exclude-tools-when-tool-choice-none --default-chat-template-kwargs "$TEMPLATE_KWARGS" \
  --generation-config vllm "${SAMPLING[@]}" --data-parallel-size "${DATA_PARALLEL:-1}" --seed 0
