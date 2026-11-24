#!/usr/bin/env bash
# IFBench for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1-vllm  Bielik 11B v3.1 Instruct served by vLLM (start it with vllm.sh) at BASE_URL
#                         (default http://127.0.0.1:8000/v1, served model name "bielik")
#   slayer1b-60000        Slayer 1B, training step 60000, on a local CUDA GPU (slayer_package.py + slayer_kv_lm.py
#                         from research/common/slayer_serving)
# Installs IFBench at the pinned commit (uv sync --frozen), takes the test set from Hugging Face at the pinned
# revision, generates (Bielik: IFBench's generate_responses.py; Slayer: slayer_kv_lm.py, raw prompt, greedy), scores
# with IFBench's run_eval and writes results/<model-id>.json and results/<model-id>.jsonl.gz.
# --limit N scores only the first N prompts, in out/.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=""
if [[ "${1:-}" == "--limit" ]]; then LIMIT="${2:?--limit needs N}"; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
COMMON="$HERE/../../common/slayer_serving"
OUT="${OUT_DIR:-$HERE/out}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"

IFBENCH_COMMIT="488918665d53f867fa908a293769ec6e71e74aec"
DATA_REVISION="ed7c12452594b7028b15807b86d3938150b663ae"
DATA_URL="https://huggingface.co/datasets/allenai/IFBench_test/resolve/$DATA_REVISION/data/train-00000-of-00001.parquet"

case "$MODEL" in
  bielik-11b-v3.1-vllm)
    # LFM3-1.7B card: temperature 0.6, top_p 0.95 (set on the server, vllm.sh), no output limit other than the
    # context: 32,768 minus the longest prompt of the set with the chat template (1,530 tokens) = 31,238.
    GEN=(--model bielik --temperature 0.6 --max-tokens 31238 --seed 20261119 --workers "${WORKERS:-32}")
    SETTINGS='{"temperature": 0.6, "top_p": 0.95, "seed": 20261119, "max_tokens_per_turn": 31238, "max_turns": 1, "trials": 1}'
    curl -sf "$BASE_URL/models" | grep -q '"bielik"' || { echo "no model \"bielik\" at $BASE_URL (start vllm.sh first)" >&2; exit 1; } ;;
  slayer1b-60000)
    # Base model, no chat template: the raw prompt, greedy decoding up to 1280 tokens (as in the IFEval benchmark).
    SETTINGS='{"temperature": 0, "max_tokens_per_turn": 1280, "max_turns": 1, "trials": 1, "chat_template": false}' ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1-vllm | slayer1b-60000)" >&2; exit 2 ;;
esac

mkdir -p "$OUT"
REPO="$OUT/IFBench"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/allenai/IFBench.git "$IFBENCH_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$IFBENCH_COMMIT" ]] || { echo "IFBench checkout is not $IFBENCH_COMMIT" >&2; exit 1; }

cd "$REPO"
uv sync -q --frozen --python 3.12
curl -sfL -o data/IFBench_test-hf.parquet "$DATA_URL"
uv run -q --with pyarrow python "$HERE/convert_hf.py" data/IFBench_test-hf.parquet data/IFBench_test.hf.jsonl
INPUT=data/IFBench_test.hf.jsonl
TARGET="$HERE/results/$MODEL"
if [[ -n "$LIMIT" ]]; then
  head -n "$LIMIT" data/IFBench_test.hf.jsonl > data/IFBench_test.limit.jsonl
  INPUT=data/IFBench_test.limit.jsonl
  TARGET="$OUT/limit/$MODEL"
fi

if [[ "$MODEL" == slayer1b-60000 ]]; then
  VENV="${SLAYER_VENV:-$HERE/.venv-slayer}"
  LM_EVAL_COMMIT="ddd67220430a2470529f25fd5c05a576ca1057a0"  # lm-evaluation-harness; slayer_kv_lm.py subclasses its LM
  [[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
  uv pip install --python "$VENV/bin/python" "torch==2.8.0" --index-url https://download.pytorch.org/whl/cu128
  uv pip install --python "$VENV/bin/python" "lm-eval @ git+https://github.com/EleutherAI/lm-evaluation-harness@$LM_EVAL_COMMIT" \
    tokenizers safetensors numpy huggingface_hub
  PKG="$OUT/slayer1b-60000-package"
  [[ -d "$PKG" ]] || "$VENV/bin/python" "$COMMON/slayer_package.py" --out "$PKG"
  "$VENV/bin/python" "$COMMON/slayer_kv_lm.py" --pkg "$PKG" --prompts "$INPUT" --responses "data/$MODEL-responses.jsonl" \
    --max-gen-toks 1280 --out "$OUT/$MODEL-generation.json"
else
  uv run -q python generate_responses.py --api-base "$BASE_URL" --input-file "$INPUT" \
    --output-file "data/$MODEL-responses.jsonl" "${GEN[@]}"
fi
# run_eval names its output after the responses file: eval/<model-id>-eval_results_{strict,loose}.jsonl.
# The repo also ships sample files eval/eval_results_*.jsonl; summarize.py reads only the prefixed ones.
uv run -q python -m run_eval --input_data="$INPUT" --input_response_data="data/$MODEL-responses.jsonl" --output_dir=eval

python3 "$HERE/summarize.py" "$INPUT" eval "$MODEL" "$TARGET" "$SETTINGS"
