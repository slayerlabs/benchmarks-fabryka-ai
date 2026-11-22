#!/usr/bin/env bash
# LiveCodeBench v6 (code generation, release_v6) for one model: bash run.sh <model-id> [--limit N]
# Settings are fixed in PROTOCOL.md. Needs Linux with one NVIDIA GPU (written for an H100 80 GB), CUDA drivers,
# python3, git and curl; Bielik also needs HF_TOKEN with access to the gated repo.
#
#   lfm3-1.7b, qwen3.5-4b, qwen3.5-9b, bielik-11b-v3.1-vllm   vLLM 0.34.0, bf16, the model's full context
#   slayer1b-1.08                                              not run (README, "Deviations")
#
# Steps: clone LiveCodeBench at the pinned commit, start `vllm serve` at the pinned model revision, send one chat
# request per problem (lcb.py generate; resumes where it stopped), stop vLLM, score with LiveCodeBench's evaluator
# (lcb.py score) and write results/<model-id>.json and .jsonl.gz (summarize.py).
# Env: CONCURRENCY (requests in flight, default 64), REQUEST_TIMEOUT (seconds per request, default 21600),
# PORT (default 8000), OUT_DIR, RESULTS_DIR.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--limit "${2:?--limit needs N}"); fi

HERE="$(cd "$(dirname "$0")" && pwd)"
# Separate venvs: vLLM pins its own transformers and torch; LiveCodeBench's evaluator needs neither.
VENV_VLLM="${VENV_VLLM:-$HERE/.venv-vllm}"
VENV_LCB="${VENV_LCB:-$HERE/.venv-lcb}"
OUT="${OUT_DIR:-$HERE/out}/$MODEL"
PORT="${PORT:-8000}"

LCB_REPO="https://github.com/LiveCodeBench/LiveCodeBench"
LCB_COMMIT="28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24"
LCB_DIR="$HERE/.cache/LiveCodeBench"
VLLM_VERSION="0.34.0"  # the first release with Lfm3ForCausalLM; one version for all four models
TEMPLATE_KWARGS=""

case "$MODEL" in
  lfm3-1.7b)  REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144 ;;
  qwen3.5-4b) REPO="Qwen/Qwen3.5-4B";    REVISION="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"; CONTEXT=262144 ;;
  qwen3.5-9b) REPO="Qwen/Qwen3.5-9B";    REVISION="c202236235762e1c871ad0ccb60c8ee5ba337b9a"; CONTEXT=262144 ;;
  bielik-11b-v3.1-vllm)
    REPO="speakleash/Bielik-11B-v3.1-Instruct"; REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"; CONTEXT=32768
    : "${HF_TOKEN:?set HF_TOKEN (Hugging Face token with access to $REPO)}"
    # The template's default provider system prompt carries the current date; pinned to the day of PROTOCOL.md so
    # a rerun sends the same prompt (as ifeval/vllm.sh pins it to its run day).
    TEMPLATE_KWARGS='{"current_date": "2026-11-22", "current_day_of_week": "Sunday", "current_time_of_day": "night"}' ;;
  slayer1b-1.08)
    echo "slayer1b-1.08 is not run: research/common/slayer_lm.py decodes about 29 tokens/s whatever the batch," \
         "and the 1055 prompts leave 2.87M output tokens under the 4096 context, about 27 h on one GPU" \
         "(README, \"Deviations\")." >&2
    exit 2 ;;
  *)
    echo "unknown model-id: $MODEL (lfm3-1.7b | qwen3.5-4b | qwen3.5-9b | bielik-11b-v3.1-vllm)" >&2; exit 2 ;;
esac

command -v uv >/dev/null || python3 -m pip install -q uv
mkdir -p "$HERE/.cache" "$OUT"
[[ -d "$LCB_DIR/.git" ]] || git clone -q "$LCB_REPO" "$LCB_DIR"
git -C "$LCB_DIR" checkout -q "$LCB_COMMIT"

# LiveCodeBench's own dependencies at the versions of its uv.lock, but only the packages its prompt builder,
# dataset class and evaluator import (the lock also pins torch, vllm and API clients for its own runners).
[[ -d "$VENV_LCB" ]] || uv venv --python 3.12 "$VENV_LCB"
uv export --frozen --no-hashes --no-dev --no-emit-project --project "$LCB_DIR" -q -o "$HERE/.cache/lcb-constraints.txt"
uv pip install --python "$VENV_LCB/bin/python" -c "$HERE/.cache/lcb-constraints.txt" datasets numpy tqdm pebble anthropic

[[ -d "$VENV_VLLM" ]] || uv venv --python 3.12 "$VENV_VLLM"
uv pip install --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION"

# No --reasoning-parser: the response content keeps the thinking, and lcb.py scores the text after </think>.
# vLLM applies the model's generation_config.json as default sampling (README, "Deviations").
"$VENV_VLLM/bin/vllm" serve "$REPO" --revision "$REVISION" --served-model-name "$MODEL" --dtype bfloat16 \
  --max-model-len "$CONTEXT" --port "$PORT" > "$OUT/vllm.log" 2>&1 &
VLLM_PID=$!
trap 'kill $VLLM_PID 2>/dev/null || true' EXIT

echo "waiting for vLLM (log: $OUT/vllm.log)"
for _ in $(seq 1 180); do
  curl -sf "http://localhost:$PORT/health" >/dev/null && break
  kill -0 $VLLM_PID 2>/dev/null || { tail -30 "$OUT/vllm.log"; exit 1; }
  sleep 10
done
curl -sf "http://localhost:$PORT/health" >/dev/null || { echo "vLLM did not start in 30 min" >&2; exit 1; }
grep -i "generation config" "$OUT/vllm.log" || true  # the sampling defaults vLLM took from the model

"$VENV_LCB/bin/python" "$HERE/lcb.py" generate "$OUT" --base-url "http://localhost:$PORT" --model "$MODEL" \
  --chat-template-kwargs "$TEMPLATE_KWARGS" "${LIMIT[@]}"
kill $VLLM_PID; wait $VLLM_PID 2>/dev/null || true

"$VENV_LCB/bin/python" "$HERE/lcb.py" score "$OUT" "${LIMIT[@]}"
"$VENV_LCB/bin/python" "$HERE/summarize.py" "$OUT" "${RESULTS_DIR:-$HERE/results}/$MODEL" "${LIMIT[@]}"
