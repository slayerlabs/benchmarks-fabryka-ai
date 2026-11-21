#!/usr/bin/env bash
# GPQA Diamond, EXPLORATORY LOCAL RUN: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1  speakleash/Bielik-11B-v3.1-Instruct @ d6e755d356ad418d0f0e30b8c428db267415ddb9
#   lfm3-1.7b        LiquidAI/LFM3-1.7B @ 1da06bec6a819da10b54c67e5c90972b46d81871 (trust_remote_code)
# NOTE: the official path should be the Fabryka API at the LFM3-1.7B card settings (temperature 0.6, top_p 0.95,
# reasoning on, no output limit). This script reproduces the exploratory local run only (greedy, local GPU).
# Syntax-checked only (bash -n); not run on a GPU here.
# Needs a Hugging Face token with access to the gated dataset Idavidrein/gpqa (HF_TOKEN) and a CUDA GPU.
set -euo pipefail

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--limit "${2:?--limit needs N}"); fi
: "${HF_TOKEN:?set HF_TOKEN (GPQA is gated)}"

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$HERE/.venv}"
OUT="${OUT_DIR:-$HERE/out}/$MODEL"
LM_EVAL_VERSION="0.4.13"       # used for the published run; the repo pin elsewhere is 0.4.9.1 (see README, Deviations)
MAX_GEN_TOKS="${MAX_GEN_TOKS:-8192}"
TORCH_INDEX="https://download.pytorch.org/whl/cu128"

case "$MODEL" in
  bielik-11b-v3.1)
    REPO="speakleash/Bielik-11B-v3.1-Instruct"; REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"
    TRUST="" ; BATCH="${BATCH_SIZE:-1}" ;;
  lfm3-1.7b)
    REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"
    TRUST=",trust_remote_code=True"; BATCH="${BATCH_SIZE:-22}" ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1 | lfm3-1.7b)" >&2; exit 2 ;;
esac

[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
BIN="$VENV/bin"
PY="$BIN/python"
uv pip install --python "$PY" --index-url "$TORCH_INDEX" "torch==2.8.0"
uv pip install --python "$PY" "lm-eval==$LM_EVAL_VERSION" "transformers==5.22.1" huggingface_hub
WEIGHTS="$("$PY" -c "from huggingface_hub import snapshot_download as s; print(s('$REPO', revision='$REVISION'))")"

# Dataset revision Idavidrein/gpqa @ 83022cefff930aea54f654c0b282e74b9eeda5c6 (gpqa_diamond, 198 questions)
"$BIN/lm_eval" \
  --model hf \
  --model_args "pretrained=$WEIGHTS,dtype=bfloat16$TRUST" \
  --tasks gpqa_diamond_cot_zeroshot \
  --apply_chat_template \
  --gen_kwargs "max_gen_toks=$MAX_GEN_TOKS,do_sample=false,temperature=0.0" \
  --batch_size "$BATCH" \
  --log_samples --output_path "$OUT" "${LIMIT[@]}"

echo "Raw lm-eval output in $OUT. Per-item flags for results/$MODEL.jsonl.gz are doc_id, exact_match" \
     "(flexible-extract) and answer_is_present ('answer is' in the response); no question or answer text is kept."
