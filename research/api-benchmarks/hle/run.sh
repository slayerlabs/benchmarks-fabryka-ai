#!/usr/bin/env bash
# Humanity's Last Exam (no tools) for one model:
#   bash run.sh <model-id> [--limit N] [--judge-model MODEL]
#
# Generation uses the official centerforaisafety/hle harness at a pinned commit.
# Scoring uses the official LLM judge (default o3-mini-2025-01-31) and requires
# OPENAI_API_KEY with access to the judge model. Do not substitute a judge.
#
# Environment:
#   FABRYKA_API_KEY   required for API models (fabryka.ai)
#   HF_TOKEN          required to download gated cais/hle dataset
#   OPENAI_API_KEY    required for judge step (can differ from FABRYKA_API_KEY)
#   JUDGE_BASE_URL    optional, OpenAI-compatible base URL for judge (default: OpenAI)
#
# Output:
#   results/<model-id>.json and results/<model-id>.jsonl.gz  (full run)
#   out/<model-id>/<model-id>-limitN.*                       (smoke test)
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N] [--judge-model MODEL]}"
shift || true

LIMIT=""
JUDGE_MODEL="${JUDGE_MODEL:-o3-mini-2025-01-31}"
MAX_COMPLETION_TOKENS="${MAX_COMPLETION_TOKENS:-8192}"
TEMPERATURE="${TEMPERATURE:-0.6}"
TOP_P="${TOP_P:-0.95}"
NUM_WORKERS="${NUM_WORKERS:-10}"
JUDGE_WORKERS="${JUDGE_WORKERS:-100}"
SUBSET="${SUBSET:-text-only}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="${2:?--limit needs N}"; shift 2 ;;
    --judge-model) JUDGE_MODEL="${2:?--judge-model needs MODEL}"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
VENV="${VENV:-$HERE/.venv}"
OUT="$HERE/out/$MODEL"
RESULT_ID="$MODEL"
RESULTS_DIR="$HERE/results"
HLE_COMMIT="22ed3074b1e7b134bcbc09028d0ba320839b0655"
HLE_SRC="$OUT/hle-src"

mkdir -p "$OUT"

# Make uv discoverable in Git Bash on Windows; fall back to python -m venv/pip if unavailable.
for _uv_dir in "/c/Users/${USER:-}/.local/bin" "/c/Users/${USERNAME:-}/.local/bin" "${HOME:-}/.local/bin"; do
  [[ -n "$_uv_dir" && -d "$_uv_dir" ]] && export PATH="$_uv_dir:$PATH"
done
if command -v uv >/dev/null 2>&1; then
  [[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
  BIN="$VENV/bin"; [[ -d "$BIN" ]] || BIN="$VENV/Scripts"
  EXE=""; [[ -f "$BIN/python.exe" ]] && EXE=".exe"
  PY="$BIN/python$EXE"
  uv pip install --python "$PY" -r "$HERE/requirements.txt"
else
  PYTHON_BIN="${PYTHON_BIN:-python3}"
  command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN=python
  [[ -d "$VENV" ]] || "$PYTHON_BIN" -m venv "$VENV"
  BIN="$VENV/bin"; [[ -d "$BIN" ]] || BIN="$VENV/Scripts"
  EXE=""; [[ -f "$BIN/python.exe" ]] && EXE=".exe"
  PY="$BIN/python$EXE"
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r "$HERE/requirements.txt"
fi

if [[ ! -d "$HLE_SRC/.git" ]]; then
  rm -rf "$HLE_SRC"
  git clone https://github.com/centerforaisafety/hle.git "$HLE_SRC"
fi
git -C "$HLE_SRC" fetch --depth 1 origin "$HLE_COMMIT"
git -C "$HLE_SRC" checkout "$HLE_COMMIT"

PREDICTIONS="$OUT/hle_${MODEL}.json"
JUDGED="$OUT/judged_hle_${MODEL}.json"

generate_api() {
  : "${FABRYKA_API_KEY:?set FABRYKA_API_KEY for API models}"
  : "${HF_TOKEN:?set HF_TOKEN for gated cais/hle dataset}"
  local limit_args=()
  [[ -n "$LIMIT" ]] && limit_args=(--max_samples "$LIMIT")
  # Official harness uses AsyncOpenAI; OPENAI_BASE_URL points it at fabryka.
  # We pass temperature/top_p through env vars consumed by our patched wrapper if needed;
  # the upstream script currently comments out temperature in API call. We use a thin wrapper.
  OPENAI_API_KEY="$FABRYKA_API_KEY" OPENAI_BASE_URL="https://fabryka.ai/v1" \
    HLE_TEMPERATURE="$TEMPERATURE" HLE_TOP_P="$TOP_P" \
    "$PY" "$HERE/predict_api.py" \
      --dataset cais/hle \
      --model "$MODEL" \
      --max_completion_tokens "$MAX_COMPLETION_TOKENS" \
      --temperature "$TEMPERATURE" \
      --top_p "$TOP_P" \
      --num_workers "$NUM_WORKERS" \
      --subset "$SUBSET" \
      --output "$PREDICTIONS" \
      "${limit_args[@]}"
}

case "$MODEL" in
  slayer1b-1.08|slayer1b-*|slayer*)
    : "${HF_TOKEN:?set HF_TOKEN for gated cais/hle dataset}"
    SLAYER_REPO="SlayerLab/Slayer1B-1.09-checkpoints"
    SLAYER_REVISION="adfaf3fd5402bc7f3adbfe077798f20262979433"
    SLAYER_FILE="wagi_70000.pt"
    SLAYER_TEMPLATE_REPO="SlayerLab/Slayer1B-1.08"
    SLAYER_TEMPLATE_REVISION="5f854a0cc7160594d54d1788d37a44e8ebabe16c"
    SLAYER_DIR="${SLAYER_DIR:-$HERE/.cache/slayer1b-1.09-k70000}"
    SLAYER_DEVICE="${SLAYER_DEVICE:-cuda}"
    SLAYER_DTYPE="${SLAYER_DTYPE:-bfloat16}"
    if [[ ! -f "$SLAYER_DIR/config.json" || ! -f "$SLAYER_DIR/model.safetensors" || ! -f "$SLAYER_DIR/tokenizer.json" ]]; then
      echo "preparing Slayer model at $SLAYER_DIR"
      "$PY" -c "import torch, safetensors, tokenizers, transformers, huggingface_hub" >/dev/null 2>&1 || \
        "$PY" -m pip install torch safetensors tokenizers transformers huggingface_hub
      "$PY" - "$SLAYER_REPO" "$SLAYER_REVISION" "$SLAYER_FILE" "$SLAYER_TEMPLATE_REPO" "$SLAYER_TEMPLATE_REVISION" "$SLAYER_DIR" "$REPO_ROOT/tools/konwertuj.py" <<'PY'
import os, sys
from huggingface_hub import hf_hub_download, snapshot_download
repo, rev, fname, tpl_repo, tpl_rev, out, konvertuj = sys.argv[1:8]
ckpt = hf_hub_download(repo, fname, revision=rev)
tpl = snapshot_download(tpl_repo, revision=tpl_rev, allow_patterns=["config.json", "tokenizer.json", "model.safetensors"])
os.makedirs(out, exist_ok=True)
sys.argv = ["konvertuj.py", ckpt, tpl, out]
with open(konvertuj, encoding="utf-8") as f:
    code = compile(f.read(), konvertuj, "exec")
exec(code, {"__name__": "__main__", "__file__": konvertuj})
PY
    fi
    limit_args=()
    [[ -n "$LIMIT" ]] && limit_args=(--max_samples "$LIMIT")
    "$PY" "$HERE/predict_slayer.py" \
      --dataset cais/hle \
      --model "$MODEL" \
      --slayer-pretrained "$SLAYER_DIR" \
      --slayer-device "$SLAYER_DEVICE" \
      --slayer-dtype "$SLAYER_DTYPE" \
      --subset "$SUBSET" \
      --output "$PREDICTIONS" \
      "${limit_args[@]}"
    ;;
  *)
    generate_api
    ;;
esac

if [[ -z "${OPENAI_API_KEY:-}" && -z "${JUDGE_OPENAI_API_KEY:-}" ]]; then
  echo "Judge step skipped: no OPENAI_API_KEY/JUDGE_OPENAI_API_KEY set." >&2
  echo "Generation output: $PREDICTIONS" >&2
  echo "Run judge after owner provides judge access, then summarize.py." >&2
  exit 0
fi

JUDGE_KEY="${JUDGE_OPENAI_API_KEY:-$OPENAI_API_KEY}"
JUDGE_BASE_ARGS=()
[[ -n "${JUDGE_BASE_URL:-}" ]] && JUDGE_BASE_ARGS=(--base_url "$JUDGE_BASE_URL")

OPENAI_API_KEY="$JUDGE_KEY" "$PY" "$HERE/judge.py" \
  --dataset cais/hle \
  --predictions "$PREDICTIONS" \
  --num_workers "$JUDGE_WORKERS" \
  --judge "$JUDGE_MODEL" \
  --output "$JUDGED"

"$PY" "$HERE/summarize.py" \
  --predictions "$PREDICTIONS" \
  --judged "$JUDGED" \
  --target "$RESULTS_DIR/$RESULT_ID" \
  --model "$MODEL" \
  --limit "${LIMIT:-0}" \
  --harness "https://github.com/centerforaisafety/hle @ $HLE_COMMIT" \
  --data "https://huggingface.co/datasets/cais/hle (test, gated; revision recorded at run time)" \
  --temperature "$TEMPERATURE" \
  --top_p "$TOP_P" \
  --max_completion_tokens "$MAX_COMPLETION_TOKENS" \
  --judge "$JUDGE_MODEL"
