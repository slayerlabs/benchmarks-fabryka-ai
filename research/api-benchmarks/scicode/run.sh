#!/usr/bin/env bash
# SciCode for one model, in two separate steps (PROTOCOL.md):
#
#   bash run.sh <model-id> [--limit N]           generate: both prompt settings, every subproblem (resumes)
#   bash run.sh <model-id> --score [--limit N]   score on the scoring VM, then write results/<model-id>.json
#
# Model ids:
#   lfm3-1.7b            LiquidAI/LFM3-1.7B on vLLM 0.34.0 (bf16, context 262144), thinking on. A Linux box with one
#                        NVIDIA GPU, python3, git, curl. BASE_URL: a vLLM server that is already up and serves the
#                        pinned revision as SERVED_MODEL (default lfm3-1.7b) with max_model_len >= 262144; without
#                        BASE_URL this script starts one.
#   lfm3-1.7b-nothink    the same server, chat_template_kwargs {"enable_thinking": false}.
#   bielik-11b-v3.1      the Fabryka AI API; no GPU (macOS or Linux, python3, git). Needs FABRYKA_API_KEY and a Hugging
#                        Face login with access to the gated speakleash/Bielik-11B-v3.1-Instruct (prompt counting).
#   dev-ground-truth     not a model: the dev split's ground_truth_code fed through the same Gencode files and scorer
#                        (`--split validation`), to show that passing is reachable. No network for the answers.
#   slayer1b-1.09-k70000 Slayer 1B 1.09 at update 70000, local GPU (CUDA, bf16, greedy), Amendment 3; measured 0.00.
#
# --limit N takes the first N problems of the split in dataset order; its results go to out/<model-id>/, never to
# results/. Generation writes out/<model-id>/ (generations.jsonl, generated_code/, prompts/, run.json,
# api-events.jsonl, manifest.json); copy that directory to the scoring VM's out/ before --score.
#
# --score runs only on the scoring VM prepared by setup_scoring_vm.sh: SciCode's scorer executes the models' code,
# so it runs in the `scicode-scoring` container (Dockerfile.scoring) without network, BLAS threads 1, with this
# directory mounted read-only and only out/<model-id>/ writable.
#
# Env: CONCURRENCY (chains in flight, so requests in flight; default 64 on vLLM, 2 on the API), REQUEST_TIMEOUT
# (seconds per request, default 21600), PORT (vLLM started here, default 8000), OUT_DIR, RESULTS_DIR, BASE_URL,
# SERVED_MODEL, SCORE_MEMORY (container memory limit, default 48g).
#
# Windows in Git Bash works for the API and the oracle paths: where `python3` is only the Microsoft Store stub the
# script uses `python`, and it reads the venv from `Scripts/` when there is no `bin/`. `--score` needs Linux and
# Docker, and starting vLLM needs a Linux box with one NVIDIA GPU.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--score] [--limit N]}"
shift
LIMIT=()
SCORE=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT=(--limit "${2:?--limit needs N}"); shift 2 ;;
    --score) SCORE=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
# ${LIMIT[@]+...} below: macOS ships bash 3.2, where "${LIMIT[@]}" of an empty array fails under set -u.

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV_GEN="${VENV_GEN:-$HERE/.venv-gen}"
VENV_VLLM="${VENV_VLLM:-$HERE/.venv-vllm}"
# Windows in Git Bash: `python3` is often only the Microsoft Store stub, and a venv there has Scripts/, not bin/
if python3 -c 'pass' >/dev/null 2>&1; then PY=python3; else PY=python; fi
VENV_PY="$VENV_GEN/bin/python"
[[ -x "$VENV_PY" ]] || VENV_PY="$VENV_GEN/Scripts/python.exe"
OUT="${OUT_DIR:-$HERE/out}/$MODEL"
RESULTS="${RESULTS_DIR:-$HERE/results}"
PORT="${PORT:-8000}"
SCICODE_REPO="https://github.com/scicode-bench/SciCode"
SCICODE_COMMIT="e3158ea011d4235245a547460d3688d7ccbf9900"
SCICODE_DIR="$HERE/.cache/SciCode"
VLLM_VERSION="0.34.0"
IMAGE="scicode-scoring"
SPLIT=test

case "$MODEL" in
  lfm3-1.7b)
    SERVING=vllm; REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144
    SERVED="${SERVED_MODEL:-lfm3-1.7b}"; GEN_EXTRA=(--thinking) ;;
  lfm3-1.7b-nothink)
    SERVING=vllm; REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144
    SERVED="${SERVED_MODEL:-lfm3-1.7b}"; GEN_EXTRA=(--chat-template-kwargs '{"enable_thinking": false}') ;;
  bielik-11b-v3.1)
    SERVING=api; API_URL="https://fabryka.ai/v1/chat/completions"
    TOKENIZER="speakleash/Bielik-11B-v3.1-Instruct@d6e755d356ad418d0f0e30b8c428db267415ddb9"
    # The API renders the template itself, with a live date in its provider system prompt; 64 tokens cover the
    # difference from our local count (README, "Deviations").
    CONTEXT=32768; MARGIN=64 ;;
  dev-ground-truth)
    SERVING=oracle; SPLIT=validation ;;
  slayer1b-1.09-k70000)
    SERVING=slayer
    SLAYER_REPO="SlayerLab/Slayer1B-1.09-checkpoints"
    SLAYER_REVISION="adfaf3fd5402bc7f3adbfe077798f20262979433"
    SLAYER_FILE="wagi_70000.pt"
    SLAYER_TEMPLATE_REPO="SlayerLab/Slayer1B-1.08"
    SLAYER_TEMPLATE_REVISION="5f854a0cc7160594d54d1788d37a44e8ebabe16c"
    SLAYER_DIR="${SLAYER_DIR:-$HERE/.cache/slayer1b-1.09-k70000}"
    SLAYER_DEVICE="${SLAYER_DEVICE:-cuda}"
    SLAYER_DTYPE="${SLAYER_DTYPE:-bfloat16}" ;;
  *)
    echo "unknown model-id: $MODEL (lfm3-1.7b | lfm3-1.7b-nothink | bielik-11b-v3.1 | dev-ground-truth | slayer1b-1.09-k70000)" >&2
    exit 2 ;;
esac

mkdir -p "$HERE/.cache" "$OUT"
[[ -d "$SCICODE_DIR/.git" ]] || git clone -q "$SCICODE_REPO" "$SCICODE_DIR"
git -C "$SCICODE_DIR" checkout -q "$SCICODE_COMMIT"

if [[ "$SCORE" == 1 ]]; then
  [[ "$(uname -s)" == Linux ]] || { echo "--score runs on the scoring VM (setup_scoring_vm.sh), not here" >&2; exit 1; }
  docker image inspect "$IMAGE" >/dev/null 2>&1 \
    || { echo "no $IMAGE image: run setup_scoring_vm.sh first" >&2; exit 1; }
  docker build -q -t "$IMAGE" -f "$HERE/Dockerfile.scoring" "$HERE" >/dev/null  # cached; rebuilds if the lock changed
  COMMIT="$(git -C "$HERE" rev-parse HEAD 2>/dev/null || true)"
  DIRTY=0; [[ -n "$(git -C "$HERE" status --porcelain --untracked-files=no -- . 2>/dev/null)" ]] && DIRTY=1
  docker run --rm --network none --memory "${SCORE_MEMORY:-48g}" --pids-limit 4096 \
    -v "$HERE:$HERE:ro" -v "$OUT:$OUT" -v "$HERE/.cache/hf-scoring:$HERE/.cache/hf-scoring" -w "$HERE" \
    -e HF_HOME="$HERE/.cache/hf-scoring" -e SCICODE_CODE_COMMIT="$COMMIT" -e SCICODE_CODE_DIRTY="$DIRTY" \
    -e SCICODE_IMAGE_ID="$(docker image inspect -f '{{.Id}}' "$IMAGE")" -e SCICODE_NETWORK=none \
    "$IMAGE" python scicode_runner.py score "$OUT" --model-id "$MODEL" --split "$SPLIT" ${LIMIT[@]+"${LIMIT[@]}"}
  TARGET="$RESULTS/$MODEL"
  [[ "$MODEL" == dev-ground-truth ]] && TARGET="$RESULTS/checks/$MODEL"
  "$PY" "$HERE/summarize.py" "$OUT" "$TARGET" ${LIMIT[@]+"${LIMIT[@]}"}
  exit 0
fi

command -v uv >/dev/null || "$PY" -m pip install -q uv
[[ -d "$VENV_GEN" ]] || uv venv -q --python 3.11 "$VENV_GEN"
uv pip sync -q --python "$VENV_PY" "$HERE/requirements-generate.lock"
GEN=("$VENV_PY" "$HERE/scicode_runner.py" generate "$OUT" --model-id "$MODEL" --split "$SPLIT")

prepare_slayer() {
  local SLAYER_PY="${SLAYER_PYTHON:-$VENV_PY}"
  if [[ ! -f "$SLAYER_DIR/config.json" || ! -f "$SLAYER_DIR/model.safetensors" || ! -f "$SLAYER_DIR/tokenizer.json" ]]; then
    echo "preparing Slayer model at $SLAYER_DIR"
    "$SLAYER_PY" -c "import torch, safetensors, tokenizers, transformers" >/dev/null 2>&1 || \
      uv pip install -q --python "$SLAYER_PY" torch safetensors tokenizers transformers
    "$SLAYER_PY" - "$SLAYER_REPO" "$SLAYER_REVISION" "$SLAYER_FILE" "$SLAYER_TEMPLATE_REPO" "$SLAYER_TEMPLATE_REVISION" "$SLAYER_DIR" "$HERE/../../tools/konwertuj.py" <<'PY'
import os, sys
from huggingface_hub import hf_hub_download, snapshot_download
repo, rev, fname, tpl_repo, tpl_rev, out, konvertuj = sys.argv[1:8]
ckpt = hf_hub_download(repo, fname, revision=rev)
tpl = snapshot_download(tpl_repo, revision=tpl_rev, allow_patterns=["config.json", "tokenizer.json", "model.safetensors"])
os.makedirs(out, exist_ok=True)
# konwertuj.py is a script; run it in-process with argv
sys.argv = ["konwertuj.py", ckpt, tpl, out]
with open(konvertuj, encoding="utf-8") as f:
    code = compile(f.read(), konvertuj, "exec")
exec(code, {"__name__": "__main__", "__file__": konvertuj})
PY
  fi
}

if [[ "$SERVING" == slayer ]]; then
  prepare_slayer
  SLAYER_PY="${SLAYER_PYTHON:-$VENV_PY}"
  "$SLAYER_PY" -c "import torch, safetensors, tokenizers" >/dev/null 2>&1 || \
    uv pip install -q --python "$SLAYER_PY" torch safetensors tokenizers transformers
  "$SLAYER_PY" "$HERE/scicode_runner.py" generate "$OUT" --model-id "$MODEL" --split "$SPLIT" \
    --slayer-pretrained "$SLAYER_DIR" --slayer-device "$SLAYER_DEVICE" --slayer-dtype "$SLAYER_DTYPE" \
    --concurrency 1 ${LIMIT[@]+"${LIMIT[@]}"}
elif [[ "$SERVING" == oracle ]]; then
  "${GEN[@]}" --oracle --concurrency 4 ${LIMIT[@]+"${LIMIT[@]}"}
elif [[ "$SERVING" == api ]]; then
  : "${FABRYKA_API_KEY:?set FABRYKA_API_KEY (Fabryka AI API key)}"
  "${GEN[@]}" --chat-url "$API_URL" --model "$MODEL" --api-key-env FABRYKA_API_KEY --tokenizer "$TOKENIZER" \
    --context "$CONTEXT" --margin "$MARGIN" --retries 30 --concurrency "${CONCURRENCY:-2}" ${LIMIT[@]+"${LIMIT[@]}"}
elif [[ -n "${BASE_URL:-}" ]]; then
  curl -sf "$BASE_URL/health" >/dev/null || { echo "no vLLM server answering at $BASE_URL/health" >&2; exit 1; }
  MODELS="$(curl -sf "$BASE_URL/v1/models")" || { echo "no answer from $BASE_URL/v1/models" >&2; exit 1; }
  grep -Eq "\"id\": ?\"$SERVED\"" <<< "$MODELS" \
    || { echo "$BASE_URL does not serve a model named $SERVED (set SERVED_MODEL): $MODELS" >&2; exit 1; }
  "${GEN[@]}" --base-url "$BASE_URL" --model "$SERVED" --model-repo "$REPO@$REVISION" --context "$CONTEXT" \
    --concurrency "${CONCURRENCY:-64}" "${GEN_EXTRA[@]}" ${LIMIT[@]+"${LIMIT[@]}"}
else
  [[ -d "$VENV_VLLM" ]] || uv venv -q --python 3.12 "$VENV_VLLM"
  uv pip install -q --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION"
  # No --reasoning-parser: the content keeps the thinking, and scicode_runner.py takes the text after </think>.
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
  "${GEN[@]}" --base-url "http://localhost:$PORT" --model "$SERVED" --model-repo "$REPO@$REVISION" \
    --context "$CONTEXT" --concurrency "${CONCURRENCY:-64}" "${GEN_EXTRA[@]}" ${LIMIT[@]+"${LIMIT[@]}"}
  kill $VLLM_PID; wait $VLLM_PID 2>/dev/null || true
fi
echo "run.sh: generation done; copy $OUT to the scoring VM and run: bash run.sh $MODEL --score ${LIMIT[*]+${LIMIT[*]}}"
