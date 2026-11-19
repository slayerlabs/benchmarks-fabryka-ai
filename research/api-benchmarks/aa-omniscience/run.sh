#!/usr/bin/env bash
# AA-Omniscience (public) for one model: bash run.sh <model-id> [--limit N]
#   bielik-11b-v3.1-vllm  Bielik 11B v3.1 Instruct served by vLLM (start it with vllm.sh) at BASE_URL
#                         (default http://127.0.0.1:8000/v1, served model name "bielik")
#   slayer1b-60000        Slayer 1B, training step 60000, served locally by slayer_server.py on a CUDA GPU
# Needs a judge on an OpenAI-compatible endpoint: JUDGE_BASE_URL, JUDGE_MODEL, JUDGE_API_KEY (see README, Deviations).
# prepare.py -> generate.py -> judge.py -> summarize.py; writes results/<model-id>.json and .jsonl.gz (ids and grades
# only: the question set is closed). --limit N asks only the first N questions and writes to out/limit/ (the 12 judge
# controls always run, they use the answer key only).
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=""
if [[ "${1:-}" == "--limit" ]]; then LIMIT="${2:?--limit needs N}"; fi
: "${JUDGE_BASE_URL:?set JUDGE_BASE_URL, JUDGE_MODEL and JUDGE_API_KEY}" "${JUDGE_MODEL:?}"

HERE="$(cd "$(dirname "$0")" && pwd)"
OUT="${OUT_DIR:-$HERE/out}"
VENV="${VENV:-$HERE/.venv}"
mkdir -p "$OUT"
[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
PY="$VENV/bin/python"
uv pip install --python "$PY" httpx huggingface_hub
"$PY" "$HERE/prepare.py" "$OUT/prep"

TEMPLATE_KWARGS='{"provider_system_prompt": true, "current_date": "2026-11-18", "current_day_of_week": "Wednesday"}'
case "$MODEL" in
  bielik-11b-v3.1-vllm)
    BASE_URL="${BASE_URL:-http://127.0.0.1:8000/v1}"; SERVED=bielik
    curl -sf "$BASE_URL/models" | grep -q '"bielik"' || { echo "no model \"bielik\" at $BASE_URL (start vllm.sh first)" >&2; exit 1; }
    # LFM3-1.7B card: temperature 0.6, top_p 0.95, no output limit other than the context.
    GEN=(--temperature 0.6 --top-p 0.95 --seed-base 20261119 --max-tokens 0)
    SETTINGS='{"temperature": 0.6, "top_p": 0.95, "seed": "20261119 + question index", "max_tokens_per_turn": null, "max_turns": 1, "trials": 1}' ;;
  slayer1b-60000)
    BASE_URL="http://127.0.0.1:8001/v1"; SERVED=slayer
    SVENV="${SLAYER_VENV:-$HERE/.venv-slayer}"
    [[ -d "$SVENV" ]] || uv venv --python 3.12 "$SVENV"
    uv pip install --python "$SVENV/bin/python" "torch==2.8.0" --index-url https://download.pytorch.org/whl/cu128
    uv pip install --python "$SVENV/bin/python" \
      "lm-eval @ git+https://github.com/EleutherAI/lm-evaluation-harness@ddd67220430a2470529f25fd5c05a576ca1057a0" \
      tokenizers safetensors numpy huggingface_hub
    PKG="$OUT/slayer1b-60000-package"
    [[ -d "$PKG" ]] || "$SVENV/bin/python" "$HERE/slayer_package.py" --out "$PKG"
    # Base model: the system prompt and the question as raw text, greedy, up to 1280 tokens (limit mode fixed).
    (cd "$HERE" && "$SVENV/bin/python" slayer_server.py --pkg "$PKG" --port 8001 --log "$OUT/server-log" \
       --limit-mode fixed --batch 32 > "$OUT/server.log" 2>&1) &
    SERVER_PID=$!
    trap 'kill $SERVER_PID 2>/dev/null || true' EXIT
    for _ in $(seq 1 120); do curl -sf "$BASE_URL/models" > /dev/null && break; sleep 5; done
    curl -sf "$BASE_URL/models" | grep -q '"slayer"' || { echo "slayer_server.py did not start (out/server.log)" >&2; exit 1; }
    GEN=(--temperature 0 --max-tokens 0)
    SETTINGS='{"temperature": 0, "max_tokens_per_turn": 1280, "max_turns": 1, "trials": 1, "chat_template": false}' ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1-vllm | slayer1b-60000)" >&2; exit 2 ;;
esac

QUESTIONS="$OUT/prep/questions.jsonl"; N=600; TARGET="$HERE/results/$MODEL"; SUM_ARGS=()
if [[ -n "$LIMIT" ]]; then
  head -n "$LIMIT" "$QUESTIONS" > "$OUT/prep/questions.limit.jsonl"
  QUESTIONS="$OUT/prep/questions.limit.jsonl"; N="$LIMIT"; TARGET="$OUT/limit/$MODEL"; SUM_ARGS=(--limit)
fi
"$PY" "$HERE/generate.py" --api "$BASE_URL" --model "$SERVED" --input "$QUESTIONS" --n "$N" \
  --kwargs "$TEMPLATE_KWARGS" "${GEN[@]}" --output "$OUT/$MODEL-answers.json"
"$PY" "$HERE/judge.py" "$OUT/prep" "$OUT/$MODEL-answers.json" "$OUT/$MODEL-grades.json"
"$PY" "$HERE/summarize.py" "$OUT/prep" "$OUT/$MODEL-grades.json" "$OUT/$MODEL-answers.json" "$TARGET" \
  "$SETTINGS" "$JUDGE_MODEL" "${SUM_ARGS[@]}"
