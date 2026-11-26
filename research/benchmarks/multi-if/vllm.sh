#!/usr/bin/env bash
# Serves Bielik 11B v3.1 Instruct with vLLM for run.sh (model-id bielik-11b-v3.1-vllm): bash vllm.sh
# Needs one GPU with at least 48 GB and a Hugging Face token with access to the gated model (HF_TOKEN).
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

# --generation-config vllm: no sampling defaults from the model's generation_config.json. top_p 0.95 (the LFM3-1.7B
# card setting) is also the server default here, as in the run; the Multi-IF harness sends top_p 0.95 itself as well.
exec "$VENV/bin/vllm" serve "$WEIGHTS" --served-model-name bielik --host 127.0.0.1 --port 8000 --dtype bfloat16 \
  --max-model-len 32768 --enable-auto-tool-choice \
  --tool-parser-plugin "$TOOLS/bielik_vllm_tool_parser.py" --tool-call-parser bielik \
  --reasoning-parser-plugin "$TOOLS/bielik_vllm_reasoning_parser.py" --reasoning-parser bielik \
  --exclude-tools-when-tool-choice-none --default-chat-template-kwargs "$TEMPLATE_KWARGS" \
  --generation-config vllm --override-generation-config '{"top_p": 0.95}' --seed 0
