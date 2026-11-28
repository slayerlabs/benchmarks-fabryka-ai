#!/usr/bin/env bash
# IFEval for Bielik 11B v3.1 on a rented GPU, served by vLLM with the model's own chat template.
# Modal: `modal run modal_ifeval.py` runs this script in a container (see modal_ifeval.py).
# Any other machine (vast.ai, RunPod), from a copy of this directory: HF_TOKEN=... bash vllm.sh [--limit N]
# `bash vllm.sh --setup-only` only installs the two venvs (Modal does this when it builds the image).
#
# Runs against one server (RUNS="id ..." picks some; default all three):
#   bielik-11b-v3.1-vllm             settings of the Fabryka run (run.sh, LFM3-1.7B card sampling), template defaults:
#                                    the provider system prompt is on, as on the Fabryka API. A check that this setup
#                                    reproduces the API score.
#   bielik-11b-v3.1-vllm-no-provider the same with provider_system_prompt=false: no system prompt at all.
#   bielik-11b-v3.1-vllm-t0.3        template defaults, Bielik's own sampling: its generation_config.json sets only
#                                    temperature 0.3, so top_p stays at 1.0.
# The template puts the date into the provider prompt; it is pinned to the day of the Fabryka run.
#
# Needs: an NVIDIA GPU with >= 40 GB (bf16 weights are 22 GB, plus KV cache for 32k context), CUDA drivers,
# python3, curl, and access to the gated repo (accept it on Hugging Face, then pass HF_TOKEN).
set -euo pipefail
export PYTHONUTF8=1

LIMIT=()
SETUP_ONLY=0
case "${1:-}" in
  --limit) LIMIT=(--limit "${2:?--limit needs N}") ;;
  --setup-only) SETUP_ONLY=1 ;;
esac

HERE="$(cd "$(dirname "$0")" && pwd)"
# Separate venvs: vLLM and lm-eval pin different transformers versions.
VENV_VLLM="${VENV_VLLM:-$HERE/.venv-vllm}"
VENV="${VENV:-$HERE/.venv}"
OUT_DIR="${OUT_DIR:-$HERE/out}"

MODEL_REPO="speakleash/Bielik-11B-v3.1-Instruct"
MODEL_REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"
SERVED_NAME="bielik-11b-v3.1"
VLLM_VERSION="0.11.0"
LM_EVAL_VERSION="0.4.9.1"
PORT=8000
DATE_KWARGS='"current_date": "2026-11-18", "current_day_of_week": "Wednesday", "current_time_of_day": "night"'

command -v uv >/dev/null || python3 -m pip install -q uv
[[ -d "$VENV_VLLM" ]] || uv venv --python 3.12 "$VENV_VLLM"
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
# vLLM 0.11.0 breaks on transformers 5.x (LlamaTokenizer.all_special_tokens_extended is gone).
uv pip install --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION" "transformers==4.57.6"
uv pip install --python "$VENV/bin/python" "lm-eval[ifeval,api]==$LM_EVAL_VERSION" "transformers==4.57.6"
"$VENV/bin/python" -c "import nltk; nltk.download('punkt_tab', quiet=True)"
[[ "$SETUP_ONLY" == 1 ]] && exit 0

: "${HF_TOKEN:?set HF_TOKEN (Hugging Face token with access to $MODEL_REPO)}"

mkdir -p "$OUT_DIR"
"$VENV_VLLM/bin/vllm" serve "$MODEL_REPO" --revision "$MODEL_REVISION" \
  --served-model-name "$SERVED_NAME" --dtype bfloat16 --max-model-len "${MAX_MODEL_LEN:-32768}" \
  --port "$PORT" > "$OUT_DIR/vllm.log" 2>&1 &
VLLM_PID=$!
trap 'kill $VLLM_PID 2>/dev/null || true' EXIT

echo "waiting for vLLM (log: $OUT_DIR/vllm.log)"
for _ in $(seq 1 180); do
  curl -sf "http://localhost:$PORT/health" >/dev/null && break
  kill -0 $VLLM_PID 2>/dev/null || { tail -30 "$OUT_DIR/vllm.log"; exit 1; }
  sleep 10
done
curl -sf "http://localhost:$PORT/health" >/dev/null || { echo "vLLM did not start in 30 min" >&2; exit 1; }

run() {  # run <model-id> <chat_template_kwargs JSON> <gen_kwargs>
  local id="$1" out="$OUT_DIR/$1"
  EXTRA_BODY="{\"chat_template_kwargs\": $2}" OPENAI_API_KEY=none \
  "$VENV/bin/python" "$HERE/lm_eval_fabryka.py" \
    --model local-chat-completions \
    --model_args "model=$SERVED_NAME,base_url=http://localhost:$PORT/v1/chat/completions,num_concurrent=${CONCURRENCY:-32},tokenized_requests=False" \
    --apply_chat_template \
    --gen_kwargs "$3" \
    --include_path "$HERE/task" --tasks ifeval_pinned \
    --log_samples --output_path "$out" --seed 1234 "${LIMIT[@]}"
  "$VENV/bin/python" "$HERE/summarize.py" "$out" "${RESULTS_DIR:-$HERE/results}/$id"
}

CARD="do_sample=true,temperature=0.6,top_p=0.95,max_gen_toks=30720"
OWN="do_sample=true,temperature=0.3,top_p=1.0,max_gen_toks=30720"
for id in ${RUNS:-bielik-11b-v3.1-vllm bielik-11b-v3.1-vllm-no-provider bielik-11b-v3.1-vllm-t0.3}; do
  case "$id" in
    bielik-11b-v3.1-vllm) run "$id" "{$DATE_KWARGS}" "$CARD" ;;
    bielik-11b-v3.1-vllm-no-provider) run "$id" "{$DATE_KWARGS, \"provider_system_prompt\": false}" "$CARD" ;;
    bielik-11b-v3.1-vllm-t0.3) run "$id" "{$DATE_KWARGS}" "$OWN" ;;
    *) echo "unknown run: $id" >&2; exit 2 ;;
  esac
done
