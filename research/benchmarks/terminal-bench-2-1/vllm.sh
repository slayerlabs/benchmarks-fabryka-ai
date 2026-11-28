#!/usr/bin/env bash
# Serves one model with vLLM for run.sh: bash vllm.sh <model-id>
#   lfm3-1.7b        LiquidAI/LFM3-1.7B in bf16, parsers from Liquid AI's vLLM guide; one GPU with >= 24 GB for the
#                    full 262144-token context (MAX_MODEL_LEN lowers it, see README)
#   bielik-11b-v3.1  speakleash/Bielik-11B-v3.1-Instruct in bf16 with the parsers from speakleash/bielik-tools;
#                    one GPU with >= 48 GB; needs HF_TOKEN (gated model)
# Listens on HOST:PORT (default 127.0.0.1:8000). To serve from a rented GPU, keep the default and forward the port
# over SSH (ssh -L 8000:127.0.0.1:8000 ...), so the server is never public.
set -euo pipefail

MODEL="${1:?usage: bash vllm.sh <model-id>}"
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VLLM_VENV:-$HERE/.venv-vllm}"
WORK="${OUT_DIR:-$HERE/out}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
VLLM_VERSION="0.34.0"

command -v uv >/dev/null || python3 -m pip install -q uv
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
uv pip install --python "$VENV/bin/python" "vllm==$VLLM_VERSION" huggingface_hub
fetch() { "$VENV/bin/python" -c "from huggingface_hub import snapshot_download as s; print(s('$1', revision='$2'))"; }

# --generation-config vllm: no sampling defaults from the model's generation_config.json; OpenCode sends
# temperature and top_p (run.sh) in every request.
COMMON=(--host "$HOST" --port "$PORT" --dtype bfloat16 --enable-auto-tool-choice --generation-config vllm --seed 0)

case "$MODEL" in
  lfm3-1.7b)
    WEIGHTS="$(fetch LiquidAI/LFM3-1.7B 1da06bec6a819da10b54c67e5c90972b46d81871)"
    # https://docs.liquid.ai/deployment/gpu-inference/vllm (vLLM 0.34.0 has the native LFM3 implementation)
    exec "$VENV/bin/vllm" serve "$WEIGHTS" --served-model-name lfm3 "${COMMON[@]}" --trust-remote-code \
      --reasoning-parser qwen3 --tool-call-parser qwen3_coder --max-model-len "${MAX_MODEL_LEN:-262144}" ;;
  bielik-11b-v3.1)
    : "${HF_TOKEN:?set HF_TOKEN (the model is gated)}"
    TOOLS_COMMIT="2bcd696d5f1d8bee0c4821e3b8c9c666c075ae09"
    if [[ ! -d "$WORK/bielik-tools/.git" ]]; then
      mkdir -p "$WORK"
      git init -q "$WORK/bielik-tools"
      git -C "$WORK/bielik-tools" fetch -q --depth 1 https://github.com/speakleash/bielik-tools.git "$TOOLS_COMMIT"
      git -C "$WORK/bielik-tools" checkout -q FETCH_HEAD
    fi
    TOOLS="$WORK/bielik-tools/tools"
    WEIGHTS="$(fetch speakleash/Bielik-11B-v3.1-Instruct d6e755d356ad418d0f0e30b8c428db267415ddb9)"
    # The chat template's own defaults (provider system prompt on), with the date pinned to the run day.
    RUN_DATE="${RUN_DATE:?set RUN_DATE=YYYY-MM-DD, the day of the run (README, Deviations)}"
    DOW="$(date -d "$RUN_DATE" +%A)"
    KWARGS="{\"provider_system_prompt\": true, \"current_date\": \"$RUN_DATE\", \"current_day_of_week\": \"$DOW\"}"
    exec "$VENV/bin/vllm" serve "$WEIGHTS" --served-model-name bielik "${COMMON[@]}" \
      --max-model-len "${MAX_MODEL_LEN:-32768}" \
      --tool-parser-plugin "$TOOLS/bielik_vllm_tool_parser.py" --tool-call-parser bielik \
      --reasoning-parser-plugin "$TOOLS/bielik_vllm_reasoning_parser.py" --reasoning-parser bielik \
      --default-chat-template-kwargs "$KWARGS" ;;
  *) echo "unknown model-id: $MODEL (lfm3-1.7b | bielik-11b-v3.1)" >&2; exit 2 ;;
esac
