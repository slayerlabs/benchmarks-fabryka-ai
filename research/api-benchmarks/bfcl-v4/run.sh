#!/usr/bin/env bash
# BFCL V4 for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1-vllm  Bielik 11B v3.1 Instruct served by vLLM (start it with vllm.sh) at BASE_URL
#                         (default http://127.0.0.1:8000/v1, served model name "bielik")
#   slayer1b-60000        cannot run the benchmark: writes results/slayer1b-60000.json with score null
# Installs the BFCL harness at the pinned commit in its own venv, generates and scores the 20 named test categories
# (all of BFCL V4 except web_search) and writes results/<model-id>.json and results/<model-id>.jsonl.gz.
# --limit N runs the first N tasks of each category (plus the memory prerequisite conversations) and writes to out/.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=""
if [[ "${1:-}" == "--limit" ]]; then LIMIT="${2:?--limit needs N}"; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$HERE/.venv}"
OUT="${OUT_DIR:-$HERE/out}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"

GORILLA_COMMIT="6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
SOUNDFILE_VERSION="0.13.1"  # imported by qwen-agent (a bfcl_eval dependency) but not declared by it
CATS="simple_python,simple_java,simple_javascript,multiple,parallel,parallel_multiple,irrelevance,live_simple,live_multiple,live_parallel,live_parallel_multiple,live_irrelevance,live_relevance,multi_turn_base,multi_turn_miss_func,multi_turn_miss_param,multi_turn_long_context,memory_kv,memory_vector,memory_rec_sum"

case "$MODEL" in
  bielik-11b-v3.1-vllm) BFCL_MODEL="bielik-FC" ;;
  slayer1b-60000)
    python3 "$HERE/summarize.py" --cannot-run "Slayer 1B is a base model without a chat template or tool-calling format; the serving endpoint rejects requests with tools (HTTP 400), so no syntactically valid call is possible." "$HERE/results/$MODEL"
    exit 0 ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1-vllm | slayer1b-60000)" >&2; exit 2 ;;
esac

curl -sf "$BASE_URL/models" | grep -q '"bielik"' || { echo "no model \"bielik\" at $BASE_URL (start vllm.sh first)" >&2; exit 1; }

mkdir -p "$OUT"
REPO="$OUT/gorilla"
if [[ ! -d "$REPO/.git" ]]; then
  git init -q "$REPO"
  git -C "$REPO" fetch -q --depth 1 https://github.com/ShishirPatil/gorilla.git "$GORILLA_COMMIT"
  git -C "$REPO" checkout -q FETCH_HEAD
fi
[[ "$(git -C "$REPO" rev-parse HEAD)" == "$GORILLA_COMMIT" ]] || { echo "gorilla checkout is not $GORILLA_COMMIT" >&2; exit 1; }
BC="$REPO/berkeley-function-call-leaderboard"

[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
PY="$VENV/bin/python"
uv pip install --python "$PY" torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python "$PY" -e "$BC" "soundfile==$SOUNDFILE_VERSION"

# Register the served model: one entry appended to the harness's model table (model_config_bielik.py).
CONFIG="$BC/bfcl_eval/constants/model_config.py"
grep -q 'MODEL_CONFIG_MAPPING\["bielik-FC"\]' "$CONFIG" || cat "$HERE/model_config_bielik.py" >> "$CONFIG"
# OpenAICompletionsHandler reads the endpoint from .env; the local vLLM needs no key.
printf 'OPENAI_BASE_URL=%s\nOPENAI_API_KEY=EMPTY\n' "$BASE_URL" > "$BC/.env"

GEN_ARGS=()
TARGET="$HERE/results/$MODEL"
if [[ -n "$LIMIT" ]]; then
  # The first N tasks of each category; memory categories also need all their prerequisite conversations.
  (cd "$BC" && "$PY" - "$CATS" "$LIMIT" > test_case_ids_to_generate.json) <<'EOF'
import json, sys
from bfcl_eval.utils import load_dataset_entry
cats, n = sys.argv[1].split(","), int(sys.argv[2])
ids = {}
for c in cats:
    entries = load_dataset_entry(c)
    ids[c] = [e["id"] for e in entries if "prereq" in e["id"]] + [e["id"] for e in entries if "prereq" not in e["id"]][:n]
print(json.dumps(ids))
EOF
  GEN_ARGS=(--run-ids)
  TARGET="$OUT/limit/$MODEL"
fi

# BFCL's own sampling: temperature 0.001, which vLLM raises to its minimum of 0.01 (see README, Deviations).
(cd "$BC" && "$VENV/bin/bfcl" generate --model "$BFCL_MODEL" --test-category "$CATS" --temperature 0.001 \
   --num-threads "${THREADS:-16}" "${GEN_ARGS[@]}")
EVAL_ARGS=(); [[ -n "$LIMIT" ]] && EVAL_ARGS=(--partial-eval)
(cd "$BC" && "$VENV/bin/bfcl" evaluate --model "$BFCL_MODEL" --test-category "$CATS" "${EVAL_ARGS[@]}")

SUM_ARGS=(--bfcl-model "$BFCL_MODEL"); [[ -n "$LIMIT" ]] && SUM_ARGS+=(--limit)
"$PY" "$HERE/summarize.py" "$BC" "$TARGET" "${SUM_ARGS[@]}"
