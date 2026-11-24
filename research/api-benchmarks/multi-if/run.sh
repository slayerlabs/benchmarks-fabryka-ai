#!/usr/bin/env bash
# Multi-IF for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1-vllm  Bielik 11B v3.1 Instruct served by vLLM (start it with vllm.sh) at BASE_URL
#                         (default http://127.0.0.1:8000/v1, served model name "bielik")
#   slayer1b-60000        Slayer 1B, training step 60000, served locally by slayer_server.py
#                         (research/common/slayer_serving) on a CUDA GPU
# Installs Multi-IF at the pinned commit, applies patch_api_client.py, takes the data from Hugging Face at the pinned
# revision, runs the harness's three turns and writes results/<model-id>.json and results/<model-id>.jsonl.gz.
# --limit N keeps only the first N conversations (all their turns) and writes to out/limit/.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=""
if [[ "${1:-}" == "--limit" ]]; then LIMIT="${2:?--limit needs N}"; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
COMMON="$HERE/../../common/slayer_serving"
OUT="${OUT_DIR:-$HERE/out}"
VENV="${VENV:-$HERE/.venv}"
MULTIIF_COMMIT="1cdb53ed18499ad729e0766e5d3099dd5344406f"
DATA_URL="https://huggingface.co/datasets/facebook/Multi-IF/resolve/0ab97ce0b45c7f57772e8ba2ac1616f4b00bd3aa/multiIF_20241018.csv"
DATA_SHA256="6c588af031fe67b17c535b9ba0ccc14a1b9d77b4faf88c294f83aaa5a3000018"

mkdir -p "$OUT"
OUT="$(cd "$OUT" && pwd)"  # absolute: the Slayer server runs from $COMMON
REPO="$OUT/Multi-IF"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/facebookresearch/Multi-IF.git "$MULTIIF_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$MULTIIF_COMMIT" ]] || { echo "Multi-IF checkout is not $MULTIIF_COMMIT" >&2; exit 1; }
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
PY="$VENV/bin/python"
uv pip install --python "$PY" -r "$HERE/requirements.txt"
"$PY" -m nltk.downloader -q punkt
"$PY" "$HERE/patch_api_client.py" "$REPO/api_client.py"
mkdir -p "$REPO/data/Multi-IF"
CSV="$REPO/data/Multi-IF/multiIF_20241018.csv"
curl -sfL -o "$CSV" "$DATA_URL"
echo "$DATA_SHA256  $CSV" | sha256sum -c --quiet -
TARGET="$HERE/results/$MODEL"; SUM_ARGS=()
if [[ -n "$LIMIT" ]]; then
  "$PY" -c "import pandas as pd, sys; d = pd.read_csv(sys.argv[1], keep_default_na=False); d.head(int(sys.argv[2])).to_csv(sys.argv[3], index=False)" \
    "$CSV" "$LIMIT" "$REPO/data/Multi-IF/limit.csv"
  CSV="$REPO/data/Multi-IF/limit.csv"; TARGET="$OUT/limit/$MODEL"; SUM_ARGS=(--limit)
fi

case "$MODEL" in
  bielik-11b-v3.1-vllm)
    BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"; SERVED=bielik
    curl -sf "$BASE_URL/models" | grep -q '"bielik"' || { echo "no model \"bielik\" at $BASE_URL (start vllm.sh first)" >&2; exit 1; }
    # LFM3-1.7B card: temperature 0.6, top_p 0.95; up to 8192 new tokens per turn (see README, Deviations).
    GEN=(--max_new_tokens 8192 --temperature 0.6 --top_p 0.95 --seed 20261119)
    SETTINGS='{"temperature": 0.6, "top_p": 0.95, "seed": 20261119, "max_tokens_per_turn": 8192, "max_turns": 3, "trials": 1}' ;;
  slayer1b-60000)
    BASE_URL="http://127.0.0.1:8001/v1"; SERVED=slayer
    SVENV="${SLAYER_VENV:-$HERE/.venv-slayer}"
    [[ -d "$SVENV" ]] || uv venv --python 3.12 "$SVENV"
    uv pip install --python "$SVENV/bin/python" "torch==2.8.0" --index-url https://download.pytorch.org/whl/cu128
    uv pip install --python "$SVENV/bin/python" \
      "lm-eval @ git+https://github.com/EleutherAI/lm-evaluation-harness@ddd67220430a2470529f25fd5c05a576ca1057a0" \
      tokenizers safetensors numpy huggingface_hub
    PKG="$OUT/slayer1b-60000-package"
    [[ -d "$PKG" ]] || "$SVENV/bin/python" "$COMMON/slayer_package.py" --out "$PKG"
    # Base model: earlier turns joined as "User: ... Assistant: ..." text, greedy, up to 1280 tokens (limit mode fixed);
    # a turn whose input + 1280 does not fit in 4096 tokens is answered with 400 (context exceeded, see README).
    (cd "$COMMON" && "$SVENV/bin/python" slayer_server.py --pkg "$PKG" --port 8001 --log "$OUT/server-log" \
       --limit-mode fixed --batch 32 > "$OUT/server.log" 2>&1) &
    SERVER_PID=$!
    trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
    for _ in $(seq 1 120); do curl -sf "$BASE_URL/models" > /dev/null && break; sleep 5; done
    curl -sf "$BASE_URL/models" | grep -q '"slayer"' || { echo "slayer_server.py did not start (out/server.log)" >&2; exit 1; }
    GEN=(--max_new_tokens 1280 --temperature 0 --top_p 1.0 --seed 20261119)
    SETTINGS='{"temperature": 0, "max_tokens_per_turn": 1280, "max_turns": 3, "trials": 1, "chat_template": false}' ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1-vllm | slayer1b-60000)" >&2; exit 2 ;;
esac

# The harness's OpenAI-compatible backend reads its endpoint and key from the environment: point both at the local
# server explicitly, so that no other key or the default api.openai.com is used.
(cd "$REPO" && OPENAI_BASE_URL="$BASE_URL" OPENAI_API_KEY=EMPTY "$PY" multi_turn_instruct_following_eval_api.py \
   --api_model_name "$SERVED" --input_data_csv "$CSV" "${GEN[@]}" --max_workers "${WORKERS:-32}" --steps 1 2 3)
# summarize.py imports the harness's metrics.py: put the checkout on PYTHONPATH (the script's own directory, not the
# working directory, is first on sys.path).
(cd "$REPO" && PYTHONPATH="$REPO" "$PY" "$HERE/summarize.py" "results/$SERVED" "$TARGET" "$SETTINGS" "${SUM_ARGS[@]}")
