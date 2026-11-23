#!/usr/bin/env bash
# LiveCodeBench Pro 25Q2 (quater_2025_4_6, 167 problems) for one model. Settings are fixed in PROTOCOL.md.
#
#   bash run.sh <model-id> [--limit N]           generate the answers (resumes where it stopped)
#   bash run.sh <model-id> --score [--limit N]   judge them and write results/<model-id>.json (Linux x86_64, Docker)
#   bash run.sh --prepare-scoring                clone the harness, build the venv and the judge image (setup VM)
#
#   lfm3-1.7b              LiquidAI/LFM3-1.7B on vLLM 0.34.0, bf16, context 262144, thinking on (template default).
#                          Linux with one NVIDIA GPU. BASE_URL: a vLLM server already running (shared) that serves
#                          the pinned revision as SERVED_MODEL (default lfm3-1.7b) with max_model_len >= 262144;
#                          without BASE_URL run.sh starts `vllm serve` itself.
#   lfm3-1.7b-nothink      the same server, chat_template_kwargs {"enable_thinking": false}.
#   bielik-11b-v3.1        the Fabryka AI API (macOS or Linux, no GPU). Needs FABRYKA_API_KEY and a Hugging Face
#                          login with access to speakleash/Bielik-11B-v3.1-Instruct (tokenizer and template count
#                          the prompt).
#   slayer1b-1.09-k70000   not run: writes results/slayer1b-1.09-k70000.json with score null and the reason.
#
# Generation needs a Hugging Face login that accepted the terms of the gated QAQAQAQAQ/LiveCodeBench-Pro; it writes
# out/<model-id>/{generations.jsonl,problems.json,api-events.jsonl,run.json,manifest.json}. Copy that directory to
# the scoring machine (same path under this benchmark) before --score. Scoring needs no login: it downloads the
# public test zips at the pinned revision into .cache/hf (HF_HOME of its own), then judges offline, so the harness's
# revision-less download reads the pinned files (lcbpro.py, docstring). All models are judged on the same machine
# with the same judge image and JUDGE_WORKERS (lcbpro.py), after all generation has finished (PROTOCOL.md).
# Env: CONCURRENCY (requests in flight; default 64 on vLLM, 2 on the API), REQUEST_TIMEOUT (seconds per request,
# default 21600), PORT (vLLM, default 8000), OUT_DIR, RESULTS_DIR.
set -euo pipefail
export PYTHONUTF8=1

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$HERE/.venv}"
VENV_VLLM="${VENV_VLLM:-$HERE/.venv-vllm}"
HARNESS_REPO="https://github.com/GavinZhengOI/LiveCodeBench-Pro"
HARNESS_COMMIT="d614eef4f95b3654bf0758c64e1194b2575850b8"
VERIFIER_COMMIT="021d121c882e70856b66113142495e31b9fe1d80"
HARNESS_DIR="$HERE/.cache/LiveCodeBench-Pro"
VLLM_VERSION="0.34.0"  # the first release with Lfm3ForCausalLM
LFM3_REPO="LiquidAI/LFM3-1.7B"; LFM3_REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; LFM3_CONTEXT=262144

prepare() {
  command -v uv >/dev/null || python3 -m pip install -q uv
  mkdir -p "$HERE/.cache"
  [[ -d "$HARNESS_DIR/.git" ]] || git clone -q "$HARNESS_REPO" "$HARNESS_DIR"
  git -C "$HARNESS_DIR" checkout -q "$HARNESS_COMMIT"
  git -C "$HARNESS_DIR" submodule update --init -q
  [[ "$(git -C "$HARNESS_DIR/LightCPVerifier" rev-parse HEAD)" == "$VERIFIER_COMMIT" ]] \
    || { echo "LightCPVerifier is not at $VERIFIER_COMMIT" >&2; exit 1; }
  # The harness's own dependencies at the versions of its uv.lock (Python >= 3.12: judge.py needs it).
  [[ -d "$VENV" ]] || uv venv -q --python 3.12 "$VENV"
  uv export --frozen --no-hashes --no-dev --no-emit-project --project "$HARNESS_DIR" -q \
    -o "$HERE/.cache/harness-constraints.txt"
  uv pip install -q --python "$VENV/bin/python" -c "$HERE/.cache/harness-constraints.txt" \
    datasets docker huggingface-hub openai requests certifi
}

score_env() {
  export HF_HOME="$HERE/.cache/hf"  # the test zips and the refs/main lcbpro.py tests points at the pin
  unset HF_TOKEN HUGGING_FACE_HUB_TOKEN
}

if [[ "${1:-}" == "--prepare-scoring" ]]; then
  [[ "$(uname -s)-$(uname -m)" == "Linux-x86_64" ]] || { echo "the judge needs Linux x86_64" >&2; exit 1; }
  prepare
  # The image the harness's judge builds (LightCPVerifierJudge._build_image: a build of ./LightCPVerifier tagged
  # lightcpverifier; the judge uses an existing image of that name and never rebuilds it), built once here with the
  # same docker client call. Two steps of the pinned Dockerfile take "latest" and no longer build (2026-11-22):
  # `npm install -g npm@latest` fetches an npm that refuses the image's Node 20 (EBADENGINE), and go-judge's latest
  # release lists an init-binary tarball first, which has no `go-judge` in it. The build uses a copy of the
  # Dockerfile with both at their "latest" on the day of the pinned LightCPVerifier commit (2025-09-07): npm 11.6.0
  # and go-judge v1.9.6 (same asset selection). Everything else, the checkout and the judge code are unchanged
  # (README, Deviations). The image id is recorded and the image is not rebuilt between models.
  python3 - "$HARNESS_DIR/LightCPVerifier/Dockerfile" "$HERE/.cache/Dockerfile.judge" <<'EOF'
import sys
text = open(sys.argv[1], encoding="utf-8").read()
for old, new in (("RUN npm install -g npm@latest\n", "RUN npm install -g npm@11.6.0\n"),
                 ("/repos/criyle/go-judge/releases/latest", "/repos/criyle/go-judge/releases/tags/v1.9.6")):
    if text.count(old) != 1:
        sys.exit(f"the pinned Dockerfile does not have exactly one {old!r}")
    text = text.replace(old, new)
open(sys.argv[2], "w", encoding="utf-8").write(text)
EOF
  (cd "$HARNESS_DIR" && "$VENV/bin/python" - "$HERE/.cache/Dockerfile.judge" <<'EOF'
import json, sys
import docker
import judge
client = docker.from_env()
try:
    image = client.images.get(judge.LightCPVerifierJudge.IMAGE_NAME)
except docker.errors.ImageNotFound:
    image, _ = client.images.build(path=judge.LightCPVerifierJudge.REPO_DIR, dockerfile=sys.argv[1],
                                   tag=judge.LightCPVerifierJudge.IMAGE_NAME)
print(json.dumps({"image": judge.LightCPVerifierJudge.IMAGE_NAME, "id": image.id,
                  "created": image.attrs.get("Created")}))
EOF
) | tee "$HERE/.cache/judge-image.json"
  { docker run --rm --entrypoint /usr/local/bin/go-judge lightcpverifier -version 2>&1 || true; } \
    | tee "$HERE/.cache/go-judge-version.txt"
  exit 0
fi

MODEL="${1:?usage: bash run.sh <model-id> [--score] [--limit N]}"
shift
SCORE=0
LIMIT=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --score) SCORE=1; shift ;;
    --limit) LIMIT=(--limit "${2:?--limit needs N}"); shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
# ${LIMIT[@]+...} below: macOS ships bash 3.2, where "${LIMIT[@]}" of an empty array fails under set -u.
OUT="${OUT_DIR:-$HERE/out}/$MODEL"

case "$MODEL" in
  lfm3-1.7b) SERVING=vllm; SERVED="${SERVED_MODEL:-lfm3-1.7b}"; KWARGS="" ;;
  lfm3-1.7b-nothink) SERVING=vllm; SERVED="${SERVED_MODEL:-lfm3-1.7b}"; KWARGS='{"enable_thinking": false}' ;;
  bielik-11b-v3.1)
    SERVING=api
    API_URL="https://fabryka.ai/v1/chat/completions"
    TOKENIZER="speakleash/Bielik-11B-v3.1-Instruct@d6e755d356ad418d0f0e30b8c428db267415ddb9"
    CONTEXT=32768
    # The API renders the template itself, with a live date in its provider system prompt; 64 tokens cover the
    # difference from our local count (livecodebench-v6 @ 7d931ba2, README "Deviations").
    MARGIN=64 ;;
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
  *) echo "unknown model-id: $MODEL (lfm3-1.7b | lfm3-1.7b-nothink | bielik-11b-v3.1 | slayer1b-1.09-k70000)" >&2
     exit 2 ;;
esac

if [[ "$SCORE" == 1 ]]; then
  [[ "$(uname -s)-$(uname -m)" == "Linux-x86_64" ]] || { echo "the judge needs Linux x86_64 (setup_scoring_vm.sh)" >&2; exit 1; }
  prepare
  score_env
  "$VENV/bin/python" "$HERE/lcbpro.py" tests "$OUT" ${LIMIT[@]+"${LIMIT[@]}"}
  HF_HUB_OFFLINE=1 "$VENV/bin/python" "$HERE/lcbpro.py" score "$OUT" ${LIMIT[@]+"${LIMIT[@]}"}
  "$VENV/bin/python" "$HERE/summarize.py" "$OUT" "${RESULTS_DIR:-$HERE/results}/$MODEL" ${LIMIT[@]+"${LIMIT[@]}"}
  exit 0
fi

prepare
mkdir -p "$OUT"

prepare_slayer() {
  local SLAYER_PY="${SLAYER_PYTHON:-$VENV/bin/python}"
  if [[ ! -f "$SLAYER_DIR/config.json" || ! -f "$SLAYER_DIR/model.safetensors" || ! -f "$SLAYER_DIR/tokenizer.json" ]]; then
    echo "preparing Slayer model at $SLAYER_DIR"
    "$SLAYER_PY" -c "import torch, safetensors, tokenizers, transformers" >/dev/null 2>&1 || \
      uv pip install -q --python "$SLAYER_PY" torch safetensors tokenizers transformers huggingface_hub
    "$SLAYER_PY" - "$SLAYER_REPO" "$SLAYER_REVISION" "$SLAYER_FILE" "$SLAYER_TEMPLATE_REPO" "$SLAYER_TEMPLATE_REVISION" "$SLAYER_DIR" "$HERE/../../tools/konwertuj.py" <<'PY'
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
}

if [[ "$SERVING" == slayer ]]; then
  prepare_slayer
  SLAYER_PY="${SLAYER_PYTHON:-$VENV/bin/python}"
  "$SLAYER_PY" -c "import torch, safetensors, tokenizers" >/dev/null 2>&1 || \
    uv pip install -q --python "$SLAYER_PY" torch safetensors tokenizers transformers huggingface_hub
  "$SLAYER_PY" "$HERE/lcbpro.py" generate "$OUT" --model "$MODEL" \
    --slayer-pretrained "$SLAYER_DIR" --slayer-device "$SLAYER_DEVICE" --slayer-dtype "$SLAYER_DTYPE" \
    --concurrency 1 ${LIMIT[@]+"${LIMIT[@]}"}
  exit 0
fi

if [[ "$SERVING" == api ]]; then
  : "${FABRYKA_API_KEY:?set FABRYKA_API_KEY (Fabryka AI API key)}"
  # Bielik's tokenizer and template need a newer transformers than the harness has; the versions of
  # livecodebench-v6 (and ifeval/vllm.sh for Bielik).
  uv pip install -q --python "$VENV/bin/python" "transformers==4.57.6" "jinja2==3.1.6" "sentencepiece==0.2.3" \
    "protobuf==7.36.2"
  "$VENV/bin/python" "$HERE/lcbpro.py" generate "$OUT" --chat-url "$API_URL" --model "$MODEL" \
    --api-key-env FABRYKA_API_KEY --tokenizer "$TOKENIZER" --context "$CONTEXT" --margin "$MARGIN" \
    --retries 30 --concurrency "${CONCURRENCY:-2}" ${LIMIT[@]+"${LIMIT[@]}"}
  exit 0
fi

GEN=(--model "$SERVED" --model-repo "$LFM3_REPO@$LFM3_REVISION" --context "$LFM3_CONTEXT"
     --concurrency "${CONCURRENCY:-64}")
[[ -n "$KWARGS" ]] && GEN+=(--chat-template-kwargs "$KWARGS")
if [[ -n "${BASE_URL:-}" ]]; then
  curl -sf "$BASE_URL/health" >/dev/null || { echo "no vLLM server answering at $BASE_URL/health" >&2; exit 1; }
  MODELS="$(curl -sf "$BASE_URL/v1/models")" || { echo "no answer from $BASE_URL/v1/models" >&2; exit 1; }
  grep -Eq "\"id\": ?\"$SERVED\"" <<< "$MODELS" \
    || { echo "$BASE_URL does not serve a model named $SERVED (set SERVED_MODEL): $MODELS" >&2; exit 1; }
  "$VENV/bin/python" "$HERE/lcbpro.py" generate "$OUT" --base-url "$BASE_URL" "${GEN[@]}" ${LIMIT[@]+"${LIMIT[@]}"}
else
  PORT="${PORT:-8000}"
  [[ -d "$VENV_VLLM" ]] || uv venv -q --python 3.12 "$VENV_VLLM"
  uv pip install -q --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION"
  # No --reasoning-parser: the content keeps the thinking, and lcbpro.py scores the text after </think>.
  "$VENV_VLLM/bin/vllm" serve "$LFM3_REPO" --revision "$LFM3_REVISION" --served-model-name "$SERVED" \
    --dtype bfloat16 --max-model-len "$LFM3_CONTEXT" --port "$PORT" > "$OUT/vllm.log" 2>&1 &
  VLLM_PID=$!
  trap 'kill $VLLM_PID 2>/dev/null || true' EXIT
  echo "waiting for vLLM (log: $OUT/vllm.log)"
  for _ in $(seq 1 180); do
    curl -sf "http://localhost:$PORT/health" >/dev/null && break
    kill -0 $VLLM_PID 2>/dev/null || { tail -30 "$OUT/vllm.log"; exit 1; }
    sleep 10
  done
  curl -sf "http://localhost:$PORT/health" >/dev/null || { echo "vLLM did not start in 30 min" >&2; exit 1; }
  "$VENV/bin/python" "$HERE/lcbpro.py" generate "$OUT" --base-url "http://localhost:$PORT" "${GEN[@]}" \
    ${LIMIT[@]+"${LIMIT[@]}"}
  kill $VLLM_PID; wait $VLLM_PID 2>/dev/null || true
fi
