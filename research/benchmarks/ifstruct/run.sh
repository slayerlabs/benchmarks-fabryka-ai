#!/usr/bin/env bash
# IFStruct for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1-vllm       Bielik 11B v3.1 Instruct served by vLLM at BASE_URL (default http://127.0.0.1:8000/v1):
#                              LFM3-1.7B card sampling, start it with `bash vllm.sh` (served model name "bielik")
#   bielik-11b-v3.1-vllm-t0.3  the same, Bielik's own sampling: `bash vllm.sh bielik-11b-v3.1-vllm-t0.3`
#   lfm3-1.7b                  LFM3-1.7B served by vLLM at BASE_URL: `bash ../../common/vllm_lfm3.sh`
#   slayer1b-60000             Slayer 1B, training step 60000, served locally by slayer_server.py
#                              (research/common/slayer_serving) on a CUDA GPU
# Installs IFStruct at the pinned commit (uv sync --frozen), takes the test set from Hugging Face at the pinned
# revision, runs the harness's ifstruct-eval and writes results/<model-id>.json and results/<model-id>.jsonl.gz.
# --limit N runs only the first N samples and writes to out/.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--limit "${2:?--limit needs N}"); fi

HERE="$(cd "$(dirname "$0")" && pwd)"
COMMON="$HERE/../../common/slayer_serving"
OUT="${OUT_DIR:-$HERE/out}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"
TIMEOUT=120  # seconds per request, the harness's own (ifstruct/client.py)

IFSTRUCT_COMMIT="73e03a6d3a8508357ba430675a106d4887abedf3"
DATA_REVISION="2e342ca5f2673fb1287411fdbadcdfde82b35682"
DATA_URL="https://huggingface.co/datasets/LiquidAI/ifstruct-v1.0/resolve/$DATA_REVISION/test.parquet"

case "$MODEL" in
  bielik-11b-v3.1-vllm)
    # LFM3-1.7B card: temperature 0.6, top_p 0.95 (set on the server, vllm.sh), no output limit other than the
    # context: 32,768 minus the longest prompt of the set with the chat template (3,165 tokens) = 29,603.
    GEN=(--model bielik --temperature 0.6 --max-tokens 29603 --n-threads "${THREADS:-32}" --max-retries 2)
    SETTINGS='{"temperature": 0.6, "top_p": 0.95, "max_tokens_per_turn": 29603, "max_turns": 1, "trials": 1}'
    curl -sf "$BASE_URL/models" | grep -q '"bielik"' || { echo "no model \"bielik\" at $BASE_URL (start vllm.sh first)" >&2; exit 1; } ;;
  bielik-11b-v3.1-vllm-t0.3)
    # Bielik's own generation_config.json sets only temperature 0.3; top_p stays at 1.0 (vllm.sh). Output limit as above.
    GEN=(--model bielik-t0.3 --temperature 0.3 --max-tokens 29603 --n-threads "${THREADS:-32}" --max-retries 2)
    SETTINGS='{"temperature": 0.3, "top_p": 1.0, "max_tokens_per_turn": 29603, "max_turns": 1, "trials": 1}'
    curl -sf "$BASE_URL/models" | grep -q '"bielik-t0.3"' || { echo "no model \"bielik-t0.3\" at $BASE_URL (start vllm.sh bielik-11b-v3.1-vllm-t0.3 first)" >&2; exit 1; } ;;
  lfm3-1.7b)
    # LFM3-1.7B card: temperature 0.6, top_p 0.95 (set on the server), reasoning on; up to 32,768 output tokens, as in
    # the IFEval benchmark. The server's reasoning parser keeps the thinking out of the validated answer. A long
    # reasoning answer takes more than the harness's 120 s, and a timed-out request would be retried as a new sample.
    GEN=(--model lfm3 --temperature 0.6 --max-tokens 32768 --n-threads "${THREADS:-32}" --max-retries 2)
    SETTINGS='{"temperature": 0.6, "top_p": 0.95, "max_tokens_per_turn": 32768, "max_turns": 1, "trials": 1, "reasoning": true}'
    TIMEOUT=3600
    curl -sf "$BASE_URL/models" | grep -q '"lfm3"' || { echo "no model \"lfm3\" at $BASE_URL (start vllm_lfm3.sh first)" >&2; exit 1; } ;;
  slayer1b-60000)
    BASE_URL="http://127.0.0.1:8001/v1"
    SVENV="${SLAYER_VENV:-$HERE/.venv-slayer}"
    [[ -d "$SVENV" ]] || uv venv --python 3.12 "$SVENV"
    uv pip install --python "$SVENV/bin/python" "torch==2.8.0" --index-url https://download.pytorch.org/whl/cu128
    uv pip install --python "$SVENV/bin/python" \
      "lm-eval @ git+https://github.com/EleutherAI/lm-evaluation-harness@ddd67220430a2470529f25fd5c05a576ca1057a0" \
      tokenizers safetensors numpy huggingface_hub
    mkdir -p "$OUT"
    OUT="$(cd "$OUT" && pwd)"  # absolute: the server runs from $COMMON
    PKG="$OUT/slayer1b-60000-package"
    [[ -d "$PKG" ]] || "$SVENV/bin/python" "$COMMON/slayer_package.py" --out "$PKG"
    # Base model: the prompt as raw text, greedy, up to 1280 tokens whatever max_tokens asks (limit mode fixed).
    (cd "$COMMON" && "$SVENV/bin/python" slayer_server.py --pkg "$PKG" --port 8001 --log "$OUT/server-log" \
       --limit-mode fixed --batch 32 > "$OUT/server.log" 2>&1) &
    SERVER_PID=$!
    trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
    for _ in $(seq 1 120); do curl -sf "$BASE_URL/models" > /dev/null && break; sleep 5; done
    curl -sf "$BASE_URL/models" | grep -q '"slayer"' || { echo "slayer_server.py did not start (out/server.log)" >&2; exit 1; }
    GEN=(--model slayer --temperature 0 --max-tokens 4096 --n-threads "${THREADS:-32}" --max-retries 2)
    SETTINGS='{"temperature": 0, "max_tokens_per_turn": 1280, "max_turns": 1, "trials": 1, "chat_template": false}' ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1-vllm | bielik-11b-v3.1-vllm-t0.3 | lfm3-1.7b | slayer1b-60000)" >&2; exit 2 ;;
esac

mkdir -p "$OUT"
REPO="$OUT/ifstruct"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/Liquid4All/ifstruct.git "$IFSTRUCT_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$IFSTRUCT_COMMIT" ]] || { echo "ifstruct checkout is not $IFSTRUCT_COMMIT" >&2; exit 1; }

cd "$REPO"
uv sync -q --frozen --python 3.12
curl -sfL -o data/test-hf.parquet "$DATA_URL"
uv run -q --with pyarrow python "$HERE/convert_hf.py" data/test-hf.parquet data/test.hf.jsonl
TARGET="$HERE/results/$MODEL"; SUM_ARGS=()
if [[ ${#LIMIT[@]} -gt 0 ]]; then TARGET="$OUT/limit/$MODEL"; SUM_ARGS=(--limit); fi

mkdir -p results
uv run -q python "$HERE/eval_timeout.py" "$TIMEOUT" --base-url "$BASE_URL" --api-key EMPTY --dataset data/test.hf.jsonl \
  "${GEN[@]}" "${LIMIT[@]}" --results-file "results/$MODEL.json" --log-failures "results/$MODEL-failures.jsonl" -v

python3 "$HERE/summarize.py" "results/$MODEL.json" data/test.hf.jsonl "$TARGET" "$SETTINGS" "${SUM_ARGS[@]}"
