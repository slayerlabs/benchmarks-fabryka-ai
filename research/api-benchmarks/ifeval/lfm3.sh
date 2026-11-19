#!/usr/bin/env bash
# IFEval for LiquidAI/LFM3-1.7B on a rented GPU, served by vLLM: a reference point against the LFM3-1.7B card
# (IFEval 96.66), to see which of the four IFEval metrics the card reports.
# Modal: `modal run modal_ifeval.py --model lfm3-1.7b`. Any other GPU machine: bash lfm3.sh [--limit N]
# `bash lfm3.sh --setup-only` only installs the vLLM venv (Modal does this when it builds the image).
#
# Settings from the card's "Evaluation details": vLLM, bf16, temperature 0.6, top_p 0.95, reasoning on (template
# default), template default system prompt. The card sets no output limit other than the 262,144-token context;
# here the limit is 32768 output tokens (see README). task/utils.py scores the text after the last </think>.
set -euo pipefail
export PYTHONUTF8=1

LIMIT=()
SETUP_ONLY=0
case "${1:-}" in
  --limit) LIMIT=(--limit "${2:?--limit needs N}") ;;
  --setup-only) SETUP_ONLY=1 ;;
esac

HERE="$(cd "$(dirname "$0")" && pwd)"
# vLLM 0.34.0 is the first release with Lfm3ForCausalLM; it needs transformers 5.x, so its own venv.
VENV_VLLM="${VENV_VLLM_LFM3:-$HERE/.venv-vllm-lfm3}"
VENV="${VENV:-$HERE/.venv}"  # lm-eval, as in vllm.sh
OUT_DIR="${OUT_DIR:-$HERE/out}"

MODEL_REPO="LiquidAI/LFM3-1.7B"
MODEL_REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"
SERVED_NAME="lfm3-1.7b"
VLLM_VERSION="0.34.0"
LM_EVAL_VERSION="0.4.9.1"
PORT=8001
MAX_GEN_TOKS="${MAX_GEN_TOKS:-32768}"

command -v uv >/dev/null || python3 -m pip install -q uv
[[ -d "$VENV_VLLM" ]] || uv venv --python 3.12 "$VENV_VLLM"
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
uv pip install --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION"
uv pip install --python "$VENV/bin/python" "lm-eval[ifeval,api]==$LM_EVAL_VERSION" "transformers==4.57.6"
"$VENV/bin/python" -c "import nltk; nltk.download('punkt_tab', quiet=True)"
[[ "$SETUP_ONLY" == 1 ]] && exit 0

mkdir -p "$OUT_DIR"
"$VENV_VLLM/bin/vllm" serve "$MODEL_REPO" --revision "$MODEL_REVISION" \
  --served-model-name "$SERVED_NAME" --dtype bfloat16 --max-model-len $((MAX_GEN_TOKS + 4096)) \
  --port "$PORT" > "$OUT_DIR/vllm-lfm3.log" 2>&1 &
VLLM_PID=$!
trap 'kill $VLLM_PID 2>/dev/null || true' EXIT

echo "waiting for vLLM (log: $OUT_DIR/vllm-lfm3.log)"
for _ in $(seq 1 180); do
  curl -sf "http://localhost:$PORT/health" >/dev/null && break
  kill -0 $VLLM_PID 2>/dev/null || { tail -30 "$OUT_DIR/vllm-lfm3.log"; exit 1; }
  sleep 10
done
curl -sf "http://localhost:$PORT/health" >/dev/null || { echo "vLLM did not start in 30 min" >&2; exit 1; }

ID=lfm3-1.7b
OPENAI_API_KEY=none "$VENV/bin/python" "$HERE/lm_eval_fabryka.py" \
  --model local-chat-completions \
  --model_args "model=$SERVED_NAME,base_url=http://localhost:$PORT/v1/chat/completions,num_concurrent=${CONCURRENCY:-64},tokenized_requests=False" \
  --apply_chat_template \
  --gen_kwargs "do_sample=true,temperature=0.6,top_p=0.95,max_gen_toks=$MAX_GEN_TOKS" \
  --include_path "$HERE/task" --tasks ifeval_pinned \
  --log_samples --output_path "$OUT_DIR/$ID" --seed 1234 "${LIMIT[@]}"
"$VENV/bin/python" "$HERE/summarize.py" "$OUT_DIR/$ID" "${RESULTS_DIR:-$HERE/results}/$ID"
