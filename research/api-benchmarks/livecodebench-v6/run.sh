#!/usr/bin/env bash
# LiveCodeBench v6 (code generation, release_v6) for one model: bash run.sh <model-id> [--limit N]
# Settings are fixed in PROTOCOL.md (with Amendments 1 to 5).
#
#   lfm3-1.7b              vLLM 0.34.0, bf16, context 262144. Linux with one NVIDIA GPU (written for an H100 80 GB),
#                          CUDA drivers, python3, git, curl.
#   lfm3-1.7b-cardsampling the same, with repetition_penalty 1.0 and top_k 0 (no limit) sent in every request
#                          instead of vLLM's defaults from generation_config.json (PROTOCOL.md, Amendment 4).
#   bielik-11b-v3.1        the Fabryka AI API; no GPU (macOS or Linux, python3, git). Needs FABRYKA_API_KEY and a
#                          Hugging Face login (`hf auth login`) with access to the gated speakleash/Bielik-11B-v3.1-Instruct,
#                          whose tokenizer and chat template count the prompt.
#   slayer1b-1.09-k70000   not run (README, "Deviations")
#
# Steps: clone LiveCodeBench at the pinned commit, send one chat request per problem (lcb.py generate; resumes
# where it stopped), score with LiveCodeBench's evaluator on the CPU (lcb.py score) and write
# results/<model-id>.json and .jsonl.gz (summarize.py). For LFM3-1.7B, `vllm serve` runs at the pinned revision
# during generation. Each step records our code commit, runner checksums and machine in out/<model-id>/run.json and
# the sha256 of what it wrote in manifest.json; the next step stops if its input no longer matches.
# Env: CONCURRENCY (requests in flight; default 64 on vLLM, 2 on the API), REQUEST_TIMEOUT (seconds per request,
# default 21600), PORT (vLLM, default 8000), OUT_DIR, RESULTS_DIR. BASE_URL (vLLM models): use a vLLM server that
# is already running (e.g. http://localhost:8000) instead of starting one; it must serve the pinned revision under
# SERVED_MODEL (default lfm3-1.7b) with a max_model_len of at least the context, and lcb.py records what its
# /version and /v1/models report.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--limit "${2:?--limit needs N}"); fi
# ${LIMIT[@]+...} below: macOS ships bash 3.2, where "${LIMIT[@]}" of an empty array fails under set -u.

HERE="$(cd "$(dirname "$0")" && pwd)"
# Separate venvs: vLLM pins its own transformers and torch; LiveCodeBench's evaluator needs neither.
VENV_VLLM="${VENV_VLLM:-$HERE/.venv-vllm}"
VENV_LCB="${VENV_LCB:-$HERE/.venv-lcb}"
OUT="${OUT_DIR:-$HERE/out}/$MODEL"
PORT="${PORT:-8000}"

LCB_REPO="https://github.com/LiveCodeBench/LiveCodeBench"
LCB_COMMIT="28fef95ea8c9f7a547c8329f2cd3d32b92c1fa24"
LCB_DIR="$HERE/.cache/LiveCodeBench"
VLLM_VERSION="0.34.0"  # the first release with Lfm3ForCausalLM

case "$MODEL" in
  lfm3-1.7b)
    SERVING=vllm; REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144
    SERVED="${SERVED_MODEL:-$MODEL}"; GEN_EXTRA=() ;;
  lfm3-1.7b-cardsampling)
    SERVING=vllm; REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144
    # The same served model as lfm3-1.7b; max_tokens from the protocol's context, checked against the server's.
    SERVED="${SERVED_MODEL:-lfm3-1.7b}"; GEN_EXTRA=(--card-sampling --context "$CONTEXT") ;;
  bielik-11b-v3.1)
    SERVING=api
    : "${FABRYKA_API_KEY:?set FABRYKA_API_KEY (Fabryka AI API key)}"
    API_URL="https://fabryka.ai/v1/chat/completions"
    TOKENIZER="speakleash/Bielik-11B-v3.1-Instruct@d6e755d356ad418d0f0e30b8c428db267415ddb9"
    CONTEXT=32768
    # The API renders the template itself, with a live date in its provider system prompt; 64 tokens cover the
    # difference from our local count (README, "Deviations").
    MARGIN=64 ;;
  slayer1b-1.09-k70000)
    echo "slayer1b-1.09-k70000 is not run, a cost decision (PROTOCOL.md, Amendment 5): Slayer 1B passed 0 of 30 Python" \
         "tasks in research/slayer-1b/rozmowy-1.08 (PAPER.md, H5.1), and research/common/slayer_lm.py would need" \
         "about 27 h on one GPU for the 1055 problems (README, \"Deviations\")." >&2
    exit 2 ;;
  *)
    echo "unknown model-id: $MODEL (lfm3-1.7b | lfm3-1.7b-cardsampling | bielik-11b-v3.1)" >&2; exit 2 ;;
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

if [[ "$SERVING" == api ]]; then
  # Bielik's tokenizer and template need a newer transformers than LiveCodeBench's lock (4.51.3 cannot load
  # them); 4.57.6 as for Bielik in ifeval/vllm.sh. sentencepiece and protobuf convert its tokenizer.
  uv pip install --python "$VENV_LCB/bin/python" "transformers==4.57.6" "jinja2==3.1.6" "sentencepiece==0.2.3" \
    "protobuf==7.36.2"
  "$VENV_LCB/bin/python" "$HERE/lcb.py" generate "$OUT" --chat-url "$API_URL" --model "$MODEL" \
    --api-key-env FABRYKA_API_KEY --tokenizer "$TOKENIZER" --context "$CONTEXT" --margin "$MARGIN" \
    --retries 30 --concurrency "${CONCURRENCY:-2}" ${LIMIT[@]+"${LIMIT[@]}"}
elif [[ -n "${BASE_URL:-}" ]]; then
  # A vLLM server that is already up (possibly shared with another job: PROTOCOL.md, Amendment 4).
  curl -sf "$BASE_URL/health" >/dev/null || { echo "no vLLM server answering at $BASE_URL/health" >&2; exit 1; }
  MODELS="$(curl -sf "$BASE_URL/v1/models")" || { echo "no answer from $BASE_URL/v1/models" >&2; exit 1; }
  grep -Eq "\"id\": ?\"$SERVED\"" <<< "$MODELS" \
    || { echo "$BASE_URL does not serve a model named $SERVED (set SERVED_MODEL): $MODELS" >&2; exit 1; }
  "$VENV_LCB/bin/python" "$HERE/lcb.py" generate "$OUT" --base-url "$BASE_URL" --model "$SERVED" \
    --model-repo "$REPO@$REVISION" --concurrency "${CONCURRENCY:-64}" ${GEN_EXTRA[@]+"${GEN_EXTRA[@]}"} \
    ${LIMIT[@]+"${LIMIT[@]}"}
else
  [[ -d "$VENV_VLLM" ]] || uv venv --python 3.12 "$VENV_VLLM"
  uv pip install --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION"

  # No --reasoning-parser: the response content keeps the thinking, and lcb.py scores the text after </think>.
  # vLLM applies the model's generation_config.json as default sampling (README, "Deviations").
  "$VENV_VLLM/bin/vllm" serve "$REPO" --revision "$REVISION" --served-model-name "$SERVED" --dtype bfloat16 \
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

  "$VENV_LCB/bin/python" "$HERE/lcb.py" generate "$OUT" --base-url "http://localhost:$PORT" --model "$SERVED" \
    --model-repo "$REPO@$REVISION" --concurrency "${CONCURRENCY:-64}" ${GEN_EXTRA[@]+"${GEN_EXTRA[@]}"} \
    ${LIMIT[@]+"${LIMIT[@]}"}
  kill $VLLM_PID; wait $VLLM_PID 2>/dev/null || true
fi

"$VENV_LCB/bin/python" "$HERE/lcb.py" score "$OUT" ${LIMIT[@]+"${LIMIT[@]}"}
"$VENV_LCB/bin/python" "$HERE/summarize.py" "$OUT" "${RESULTS_DIR:-$HERE/results}/$MODEL" ${LIMIT[@]+"${LIMIT[@]}"}
