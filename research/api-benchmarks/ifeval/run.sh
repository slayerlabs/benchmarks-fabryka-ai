#!/usr/bin/env bash
# IFEval for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1  through the Fabryka AI API (needs FABRYKA_API_KEY)
#   slayer1b-1.08    local GPU, SlayerLab/Slayer1B-1.08 through lm_eval_slayer.py (research/common/slayer_lm.py, batched)
# Installs lm-eval at the pinned version in its own venv, runs the `ifeval` task and writes
# results/<model-id>.json and results/<model-id>.jsonl.gz.
set -euo pipefail
export PYTHONUTF8=1  # Windows: lm-eval prints "↑" in its results table, which cp1252 cannot encode

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--limit "${2:?--limit needs N}"); fi

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$HERE/.venv}"
# RESULT_ID names the output (default: the model id); OUT_DIR and RESULTS_DIR move it (modal_ifeval.py sets them).
RESULT_ID="${RESULT_ID:-$MODEL}"
OUT="${OUT_DIR:-$HERE/out}/$RESULT_ID"

LM_EVAL_VERSION="0.4.9.1"
SLAYER_REPO="SlayerLab/Slayer1B-1.08"
SLAYER_REVISION="ea0945b11153e67517b70d21192e6076d161f658"
TORCH_INDEX="https://download.pytorch.org/whl/cu128"           # RTX 50xx (sm_120) needs CUDA 12.8+

if [[ ! -d "$VENV" ]]; then
  uv venv --python 3.12 "$VENV"
fi
BIN="$VENV/bin"; [[ -d "$BIN" ]] || BIN="$VENV/Scripts"
EXE=""; [[ -f "$BIN/python.exe" ]] && EXE=".exe"  # Windows venv
PY="$BIN/python$EXE"
# transformers as in research/common/requirements.lock.txt: lm-eval 0.4.9.1 breaks on transformers 5.x
uv pip install --python "$PY" "lm-eval[ifeval,api]==$LM_EVAL_VERSION" "transformers==4.57.6"
"$PY" -c "import nltk; nltk.download('punkt_tab', quiet=True)"

TASK_ARGS=(--include_path "$HERE/task" --tasks ifeval_pinned
           --log_samples --output_path "$OUT" --seed 1234 "${LIMIT[@]}")

case "$MODEL" in
  bielik-11b-v3.1)
    : "${FABRYKA_API_KEY:?set FABRYKA_API_KEY}"
    # The API runs on Fabryka's own GPUs: 2 requests at a time, and after a failure lm_eval_fabryka.py pauses all
    # requests (10 s up to 5 min). 30 retries per prompt, because a 503 burst used up lm-eval's default 5.
    # LFM3-1.7B card, "Evaluation details": temperature 0.6, top_p 0.95, no output limit other than the context
    # (32,768 tokens on the API; 30,720 leaves room for the prompt).
    OPENAI_API_KEY="$FABRYKA_API_KEY" "$PY" "$HERE/lm_eval_fabryka.py" \
      --model local-chat-completions \
      --model_args "model=$MODEL,base_url=https://fabryka.ai/v1/chat/completions,num_concurrent=${CONCURRENCY:-2},max_retries=${MAX_RETRIES:-30},tokenized_requests=False" \
      --apply_chat_template \
      --gen_kwargs "do_sample=true,temperature=0.6,top_p=0.95,max_gen_toks=30720" \
      "${TASK_ARGS[@]}" ;;
  slayer1b-1.08)
    uv pip install --python "$PY" --index-url "$TORCH_INDEX" --reinstall-package torch torch
    uv pip install --python "$PY" safetensors tokenizers huggingface_hub
    WEIGHTS="$("$PY" -c "from huggingface_hub import snapshot_download as s; print(s('$SLAYER_REPO', revision='$SLAYER_REVISION'))")"
    # Base model: no chat template, the raw IFEval prompt. Greedy only, and the context is 4,096.
    # lm_eval_slayer.py = research/common/slayer_lm.py with the whole batch in one forward per step
    # (check_batched.py: the same tokens as slayer_lm, about 15x faster).
    "$PY" "$HERE/lm_eval_slayer.py" \
      --model slayer \
      --model_args "pretrained=$WEIGHTS,dtype=bfloat16,device=cuda" \
      --batch_size "${BATCH_SIZE:-32}" \
      --gen_kwargs "max_gen_toks=${MAX_GEN_TOKS:-1280}" \
      "${TASK_ARGS[@]}"
    ;;
  *)
    echo "unknown model-id: $MODEL (bielik-11b-v3.1 | slayer1b-1.08)" >&2; exit 2 ;;
esac

"$PY" "$HERE/summarize.py" "$OUT" "${RESULTS_DIR:-$HERE/results}/$RESULT_ID"
