#!/usr/bin/env bash
# RULER 128K for one model: bash run.sh <model-id> [--limit N]
#   lfm3-1.7b         Linux + NVIDIA GPU (H100 80 GB): vLLM, chat template, sampling (PROTOCOL.md)
#   bielik-11b-v3.1   any Mac or Linux machine, no GPU: the Fabryka AI API (PROTOCOL.md, Amendment 1).
#                     Needs FABRYKA_API_KEY and a Hugging Face login with access to the gated Bielik repo
#                     (`hf auth login`), for its tokenizer and chat template.
#   slayer1b-1.09-k70000  Linux + NVIDIA GPU: Slayer 1.09 at update 70 000 (PROTOCOL.md, Amendment 2) through
#                     research/common/slayer_lm.py, raw prompt, greedy
# The protocol (models, revisions, tasks, lengths, samples, seeds, settings) is PROTOCOL.md; this script only
# carries it out. Steps for each length the model can hold: RULER data generation with the model's tokenizer
# (scripts/data/prepare.py), generation (predict.py or slayer_predict.py), RULER scoring (scripts/eval/evaluate.py),
# then summarize.py writes results/<model-id>.json and .jsonl.gz.
# Resumable: data files with all samples, outputs that exist and scored lengths are kept; samples whose last
# attempt is an error are sent again. --limit N: N samples per task at 4096 only, written under out/ (smoke test).
# Needs: python3 (or uv), curl, git. Written for bash 3.2 (macOS) as well.
set -euo pipefail
export PYTHONUTF8=1

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=""
if [[ "${1:-}" == "--limit" ]]; then LIMIT="${2:?--limit needs N}"; fi

HERE="$(cd "$(dirname "$0")" && pwd)"
CACHE="$HERE/.cache"
RULER_DIR="$CACHE/RULER"
RULER_COMMIT="db43f92ff634bbce1c33d1fb15858aec4bba509a"
ENGLISH_WORDS_SHA256="affcd6d45fdf3cc843d585c99c97ad615094e760e6c4756b654bab6c73bc2eca"  # its git-lfs oid
VENV="${VENV:-$HERE/.venv}"                    # RULER data generation and scoring (requirements.lock.txt)
VENV_VLLM="${VENV_VLLM:-$HERE/.venv-vllm}"
VENV_SLAYER="${VENV_SLAYER:-$HERE/.venv-slayer}"
VLLM_VERSION="0.34.0"
VLLM_TRANSFORMERS="5.22.2"                     # what vllm==0.34.0 resolved to on 2026-11-22; pinned here
LM_EVAL_VERSION="0.4.9.1"                      # Slayer, as in ../ifeval/run.sh
TORCH_INDEX="https://download.pytorch.org/whl/cu128"
PORT="${PORT:-8000}"
FABRYKA_BASE_URL="${FABRYKA_BASE_URL:-https://fabryka.ai}"
# Tokens kept free on the API beyond the locally counted templated prompt (README, Deviations): the local count of a
# one-sentence message with Bielik's template is 1057 tokens, the API billed about 1065 in ../ifeval.
API_MARGIN=256

SEED=20261122
NUM_SAMPLES=50
TEMPERATURE=0.6
TOP_P=0.95
TASKS=(niah_single_1 niah_single_2 niah_single_3 niah_multikey_1 niah_multikey_2 niah_multikey_3
       niah_multivalue niah_multiquery vt cwe fwe qa_1 qa_2)
LENGTHS=(4096 8192 16384 32768 65536 131072)

case "$MODEL" in
  lfm3-1.7b)
    MODE=vllm; REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144 ;;
  bielik-11b-v3.1)
    MODE=api; REPO="speakleash/Bielik-11B-v3.1-Instruct"; REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"
    CONTEXT=32768
    [[ -n "${FABRYKA_API_KEY:-}" ]] || { echo "set FABRYKA_API_KEY (the Fabryka AI API key)" >&2; exit 2; } ;;
  slayer1b-1.09-k70000)
    # PROTOCOL.md, Amendment 2: the training checkpoint, converted with research/tools/konwertuj.py against the
    # 1.08 template, as research/tools/przebieg_centralny.sh does for `slayer-ckpt` rows.
    MODE=slayer; REPO="SlayerLab/Slayer1B-1.09-checkpoints"; REVISION="adfaf3fd5402bc7f3adbfe077798f20262979433"
    CKPT="wagi_70000.pt"; CKPT_SHA256="9ed73494fc139422f5314f72b4f970242454a7ab9d8caceee6b52fe5bdfc40c0"
    TEMPLATE_REPO="SlayerLab/Slayer1B-1.08"; TEMPLATE_REVISION="5f854a0cc7160594d54d1788d37a44e8ebabe16c"
    MODEL_SHA256="b9e31fc953af44638fd64ca163dd8d5658cfe02928445fa9a412f11a618bb24e"  # converted model.safetensors
    CONTEXT=4096 ;;
  *) echo "unknown model-id: $MODEL (lfm3-1.7b | bielik-11b-v3.1 | slayer1b-1.09-k70000)" >&2
     exit 2 ;;
esac
# The API runs on Fabryka's own GPUs: 2 requests at a time, as in ../ifeval/run.sh.
if [[ "$MODE" == api ]]; then CONCURRENCY="${CONCURRENCY:-2}"; else CONCURRENCY="${CONCURRENCY:-32}"; fi

RUN_ID="$MODEL"
NUM="$NUM_SAMPLES"
if [[ -n "$LIMIT" ]]; then RUN_ID="$MODEL-limit$LIMIT"; NUM="$LIMIT"; LENGTHS=(4096); fi
OUT="${OUT_DIR:-$HERE/out}/$RUN_ID"
mkdir -p "$OUT" "$CACHE"

# --- RULER at the pinned commit, its data sources, and the data/scoring venv ---------------------------------
command -v uv >/dev/null || python3 -m pip install -q uv
if [[ ! -d "$RULER_DIR/.git" ]]; then
  # The repo keeps its *.json files in git-lfs; only english_words.json is needed, fetched below and checked.
  GIT_LFS_SKIP_SMUDGE=1 git -c filter.lfs.smudge= -c filter.lfs.process= -c filter.lfs.required=false \
    clone -q --no-checkout https://github.com/NVIDIA/RULER.git "$RULER_DIR"
  git -C "$RULER_DIR" -c filter.lfs.smudge= -c filter.lfs.process= -c filter.lfs.required=false \
    checkout -q "$RULER_COMMIT"
fi
[[ "$(git -C "$RULER_DIR" rev-parse HEAD)" == "$RULER_COMMIT" ]] || { echo "RULER is not at $RULER_COMMIT" >&2; exit 1; }
[[ -d "$VENV" ]] || uv venv -q --python 3.12 "$VENV"
uv pip install -q --python "$VENV/bin/python" -r "$HERE/requirements.lock.txt"
PY="$VENV/bin/python"
# python.org builds on macOS have no CA certificates for urllib (nltk, the essay download, predict.py): use certifi's.
export SSL_CERT_FILE="${SSL_CERT_FILE:-$("$PY" -m certifi)}"
if [[ "$MODE" == api ]]; then
  "$PY" -c "import sys; from huggingface_hub import get_token; sys.exit(get_token() is None)" || {
    echo "no Hugging Face login: run \`$VENV/bin/hf auth login\` with a token that has access to $REPO" >&2; exit 2; }
fi
# RULER's essay haystacks are split with nltk's sent_tokenize (punkt_tab); nltk.download only prints a failure.
export NLTK_DATA="$CACHE/nltk_data"
"$PY" -c "import nltk, sys; sys.exit(not all(nltk.download(p, download_dir='$NLTK_DATA', quiet=True) for p in ('punkt', 'punkt_tab')))" \
  || { echo "nltk punkt / punkt_tab download failed" >&2; exit 1; }

sha256_is() {  # sha256_is <hex> <file>: portable (macOS has no sha256sum)
  [[ -f "$2" ]] && [[ "$("$PY" -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$2")" == "$1" ]]
}
JSON_DIR="$RULER_DIR/scripts/data/synthetic/json"
if ! sha256_is "$ENGLISH_WORDS_SHA256" "$JSON_DIR/english_words.json"; then
  curl -sfL "https://media.githubusercontent.com/media/NVIDIA/RULER/$RULER_COMMIT/scripts/data/synthetic/json/english_words.json" \
    -o "$JSON_DIR/english_words.json"
  sha256_is "$ENGLISH_WORDS_SHA256" "$JSON_DIR/english_words.json" \
    || { echo "english_words.json does not match its git-lfs oid" >&2; exit 1; }
fi
# RULER's own download scripts. Essays come from paulgraham.com and GitHub as they are today, QA from SQuAD v2.0
# dev and HotpotQA dev: the sha256 of each file goes into the result, and all models must share the same files.
if [[ ! -s "$JSON_DIR/PaulGrahamEssays.json" ]]; then
  (cd "$JSON_DIR" && "$PY" download_paulgraham_essay.py)
fi
if [[ ! -s "$JSON_DIR/squad.json" || ! -s "$JSON_DIR/hotpotqa.json" ]]; then
  QA_PATH="$PATH"
  if ! command -v wget >/dev/null; then
    # macOS has no wget: a curl stand-in for the two `wget [--tries=N] URL -O FILE` calls of download_qa_dataset.sh
    mkdir -p "$CACHE/bin"
    cat > "$CACHE/bin/wget" <<'SH'
#!/usr/bin/env bash
tries=1; url=""; out=""
while (($#)); do
  case "$1" in --tries=*) tries="${1#--tries=}" ;; -O) out="$2"; shift ;; *) url="$1" ;; esac
  shift
done
exec curl -fL --retry "$tries" "$url" -o "$out"
SH
    chmod +x "$CACHE/bin/wget"
    QA_PATH="$CACHE/bin:$PATH"
  fi
  (cd "$JSON_DIR" && PATH="$QA_PATH" bash download_qa_dataset.sh)
fi

# --- run.json: what summarize.py needs to describe the run (written once, kept on resume) -------------------
if [[ ! -f "$OUT/run.json" ]]; then
  "$PY" - "$OUT/run.json" "$JSON_DIR" <<PY
import datetime, hashlib, json, sys
from pathlib import Path
json_dir = Path(sys.argv[2])
sources = {f: hashlib.sha256((json_dir / f).read_bytes()).hexdigest()
           for f in ["PaulGrahamEssays.json", "squad.json", "hotpotqa.json", "english_words.json"]}
mode = "$MODE"
settings = {"weights": "$REPO @ $REVISION${CKPT:+ $CKPT (sha256 $CKPT_SHA256), converted with research/tools/konwertuj.py against $TEMPLATE_REPO @ $TEMPLATE_REVISION to model.safetensors sha256 $MODEL_SHA256}",
            "context_window": $CONTEXT, "seed": $SEED}
chat = dict(prompt="RULER input + answer prefix as one user message, model chat template with its defaults",
            temperature=$TEMPERATURE, top_p=$TOP_P, scored="text after the last </think>")
if mode == "slayer":
    settings.update(serving="research/common/slayer_lm.py, bfloat16", prompt="RULER raw prompt (base template), BOS",
                    temperature=0.0, max_tokens="RULER per-task answer budget")
elif mode == "vllm":
    settings.update(serving="vLLM $VLLM_VERSION, bfloat16", max_tokens="context window minus templated input", **chat)
else:
    settings.update(serving="Fabryka AI API, $FABRYKA_BASE_URL/v1/chat/completions, model $MODEL, concurrency $CONCURRENCY",
                    max_tokens="context window minus the templated input counted locally minus a $API_MARGIN-token margin",
                    prompt_count="the model's tokenizer and chat template at the pinned revision, template defaults "
                                 "(provider system prompt on, live date)", margin=$API_MARGIN, **chat)
run = {"model": "$MODEL", "date": datetime.date.today().isoformat(), "ruler_commit": "$RULER_COMMIT",
       "seed": $SEED, "num_samples": $NUM, "limit": ${LIMIT:-None}, "tasks": "${TASKS[*]}".split(),
       "lengths": [int(x) for x in "${LENGTHS[*]}".split()], "data_sources": sources, "settings": settings}
Path(sys.argv[1]).write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
PY
fi

# --- the model's tokenizer (and chat template) for RULER's data generation ---------------------------------
if [[ "$MODE" == slayer ]]; then
  # torch for konwertuj.py now, lm-eval for slayer_lm.py at generation
  [[ -d "$VENV_SLAYER" ]] || uv venv -q --python 3.12 "$VENV_SLAYER"
  # transformers as in research/common/requirements.lock.txt: lm-eval 0.4.9.1 breaks on transformers 5.x
  uv pip install -q --python "$VENV_SLAYER/bin/python" "lm-eval==$LM_EVAL_VERSION" "transformers==4.57.6" \
    safetensors tokenizers huggingface_hub pyyaml
  if ! "$VENV_SLAYER/bin/python" -c "import torch, sys; c = torch.version.cuda; sys.exit(not c or tuple(map(int, c.split('.')[:2])) < (12, 8))" 2>/dev/null; then
    uv pip install -q --python "$VENV_SLAYER/bin/python" --index-url "$TORCH_INDEX" --reinstall-package torch torch
  fi
  WEIGHTS="$CACHE/$MODEL"
  if ! sha256_is "$MODEL_SHA256" "$WEIGHTS/model.safetensors"; then
    rm -rf "$WEIGHTS" "$WEIGHTS.ckpt" "$WEIGHTS.wzorzec"
    "$VENV_SLAYER/bin/python" -c "from huggingface_hub import hf_hub_download as h; h('$REPO', '$CKPT', revision='$REVISION', local_dir='$WEIGHTS.ckpt')"
    "$VENV_SLAYER/bin/python" -c "from huggingface_hub import snapshot_download as s; s('$TEMPLATE_REPO', revision='$TEMPLATE_REVISION', local_dir='$WEIGHTS.wzorzec', allow_patterns=['model.safetensors', 'config.json', 'tokenizer.json'])"
    # --sha256: konwertuj.py stops before converting when the checkpoint is not the one in SHA256SUMS
    "$VENV_SLAYER/bin/python" "$HERE/../../tools/konwertuj.py" "$WEIGHTS.ckpt/$CKPT" "$WEIGHTS.wzorzec" "$WEIGHTS" \
      --sha256 "$CKPT_SHA256"
    rm -rf "$WEIGHTS.ckpt" "$WEIGHTS.wzorzec"
    sha256_is "$MODEL_SHA256" "$WEIGHTS/model.safetensors" || {
      echo "STOP: converted $WEIGHTS/model.safetensors is not $MODEL_SHA256 (PROTOCOL.md, Amendment 2)" >&2; exit 1; }
  fi
  # Slayer's config.json has no model_type, so AutoTokenizer cannot load the converted directory; this one holds
  # only its tokenizer.json, loaded as PreTrainedTokenizerFast (the same class research/common/slayer_lm.py uses).
  mkdir -p "$CACHE/slayer-tokenizer"
  cp "$WEIGHTS/tokenizer.json" "$CACHE/slayer-tokenizer/tokenizer.json"
  echo '{"tokenizer_class": "PreTrainedTokenizerFast"}' > "$CACHE/slayer-tokenizer/tokenizer_config.json"
  TOKENIZER="$CACHE/slayer-tokenizer"
else
  TOKENIZER="$("$PY" -c "
from huggingface_hub import snapshot_download as s
print(s('$REPO', revision='$REVISION', allow_patterns=['*.json', '*.jinja', '*.txt', '*.model', '*.tiktoken']))")"
fi

# --- data: RULER prepare.py per length and task --------------------------------------------------------------
RUN_LENGTHS=""
for L in "${LENGTHS[@]}"; do
  if (( L > CONTEXT )) || [[ "$MODE" == slayer && "$L" != 4096 ]]; then
    mkdir -p "$OUT/$L"
    printf '{"reason": "the %s-token context window does not hold a %s-token RULER sample"}\n' "$CONTEXT" "$L" \
      > "$OUT/$L/skip.json"
    continue
  fi
  [[ -f "$OUT/$L/skip.json" ]] && continue   # an earlier run found that the templated prompts do not fit
  RUN_LENGTHS="$RUN_LENGTHS $L"
  for T in "${TASKS[@]}"; do
    # prepare.py swallows a failing generator script (it only prints the error), so the line count is checked.
    (cd "$RULER_DIR/scripts/data" && PATH="$VENV/bin:$PATH" python prepare.py \
      --save_dir "$OUT/$L/data" --benchmark synthetic --task "$T" \
      --tokenizer_path "$TOKENIZER" --tokenizer_type hf --max_seq_length "$L" \
      --model_template_type base --num_samples "$NUM" --random_seed "$SEED")
    n="$(wc -l < "$OUT/$L/data/$T/validation.jsonl" 2>/dev/null || echo 0)"
    (( n == NUM )) || { echo "RULER data for $T @ $L has $n of $NUM samples" >&2; exit 1; }
  done
done

# --- generation ----------------------------------------------------------------------------------------------
PREDICT=("$PY" "$HERE/predict.py" --model "$MODEL" --tasks "${TASKS[@]}" --seed "$SEED" --temperature "$TEMPERATURE"
         --top-p "$TOP_P" --concurrency "$CONCURRENCY" --ruler-dir "$RULER_DIR")
if [[ -z "$RUN_LENGTHS" ]]; then
  :
elif [[ "$MODE" == slayer ]]; then
  for L in $RUN_LENGTHS; do
    "$VENV_SLAYER/bin/python" "$HERE/slayer_predict.py" --weights "$WEIGHTS" --length-dir "$OUT/$L" \
      --tasks "${TASKS[@]}" --ruler-dir "$RULER_DIR"
  done
elif [[ "$MODE" == api ]]; then
  # The API has no /tokenize: predict.py counts each templated prompt with Bielik's own tokenizer and template.
  # 30 retries behind a shared pause (10 s doubling to 5 min), as ../ifeval learned for this API.
  for L in $RUN_LENGTHS; do
    "${PREDICT[@]}" --base-url "$FABRYKA_BASE_URL" --api-key-env FABRYKA_API_KEY --length-dir "$OUT/$L" \
      --tokenizer "$TOKENIZER" --context "$CONTEXT" --margin "$API_MARGIN" --max-retries 30 \
      ${PAUSE_MIN:+--pause-min "$PAUSE_MIN"}
  done
else
  [[ -d "$VENV_VLLM" ]] || uv venv -q --python 3.12 "$VENV_VLLM"
  uv pip install -q --python "$VENV_VLLM/bin/python" "vllm==$VLLM_VERSION" "transformers==$VLLM_TRANSFORMERS"
  "$VENV_VLLM/bin/vllm" serve "$REPO" --revision "$REVISION" --served-model-name "$MODEL" --dtype bfloat16 \
    --max-model-len "$CONTEXT" --seed "$SEED" --port "$PORT" > "$OUT/vllm.log" 2>&1 &
  VLLM_PID=$!
  trap 'kill $VLLM_PID 2>/dev/null || true' EXIT
  echo "waiting for vLLM (log: $OUT/vllm.log)"
  for _ in $(seq 1 180); do
    curl -sf "http://localhost:$PORT/health" >/dev/null && break
    kill -0 $VLLM_PID 2>/dev/null || { tail -30 "$OUT/vllm.log"; exit 1; }
    sleep 10
  done
  curl -sf "http://localhost:$PORT/health" >/dev/null || { echo "vLLM did not start in 30 min" >&2; exit 1; }
  for L in $RUN_LENGTHS; do
    "${PREDICT[@]}" --base-url "http://localhost:$PORT" --length-dir "$OUT/$L"
  done
  kill $VLLM_PID 2>/dev/null || true
fi

# --- scoring: RULER's evaluate.py on the text after the last </think> -------------------------------------
for L in $RUN_LENGTHS; do
  [[ -f "$OUT/$L/skip.json" ]] && continue
  "$PY" "$HERE/summarize.py" preds "$OUT/$L"
  (cd "$RULER_DIR/scripts/eval" && PYTHONPATH="$HERE/nemo_shim" "$PY" evaluate.py \
    --data_dir "$OUT/$L/pred" --benchmark synthetic)
done

"$PY" "$HERE/summarize.py" results "$OUT" "${RESULTS_DIR:-$HERE/results}/$MODEL" --ruler-dir "$RULER_DIR"
