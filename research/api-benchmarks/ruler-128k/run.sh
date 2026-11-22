#!/usr/bin/env bash
# RULER 128K for one model on a Linux CUDA machine (vast.ai H100 80 GB): bash run.sh <model-id> [--limit N]
#   lfm3-1.7b | qwen3.5-4b | qwen3.5-9b | bielik-11b-v3.1-vllm   vLLM, chat template, sampling (PROTOCOL.md)
#   slayer1b-1.08                                               research/common/slayer_lm.py, raw prompt, greedy
# The protocol (models, revisions, tasks, lengths, samples, seeds, settings) is PROTOCOL.md; this script only
# carries it out. Steps for each length the model can hold: RULER data generation with the model's tokenizer
# (scripts/data/prepare.py), generation (predict.py or slayer_predict.py), RULER scoring (scripts/eval/evaluate.py),
# then summarize.py writes results/<model-id>.json and .jsonl.gz.
# Resumable: data files with all samples, outputs that exist and scored lengths are kept; samples whose last
# attempt is an error are sent again. --limit N: N samples per task at 4096 only, written under out/ (smoke test).
# Needs: NVIDIA GPU, CUDA drivers, python3, curl, wget, git. Bielik: HF_TOKEN with access to the gated repo.
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
CONCURRENCY="${CONCURRENCY:-32}"

SEED=20261122
NUM_SAMPLES=50
TEMPERATURE=0.6
TOP_P=0.95
TASKS=(niah_single_1 niah_single_2 niah_single_3 niah_multikey_1 niah_multikey_2 niah_multikey_3
       niah_multivalue niah_multiquery vt cwe fwe qa_1 qa_2)
LENGTHS=(4096 8192 16384 32768 65536 131072)

TEMPLATE_KWARGS=""
case "$MODEL" in
  lfm3-1.7b)  REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"; CONTEXT=262144 ;;
  # Qwen3.5 is served as the full checkpoint without extra flags (a GPU smoke test started it that way); its
  # thinking comes back inside message.content and ends with </think>. No reasoning parser on purpose.
  qwen3.5-4b) REPO="Qwen/Qwen3.5-4B"; REVISION="851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"; CONTEXT=262144 ;;
  qwen3.5-9b) REPO="Qwen/Qwen3.5-9B"; REVISION="c202236235762e1c871ad0ccb60c8ee5ba337b9a"; CONTEXT=262144 ;;
  bielik-11b-v3.1-vllm)
    REPO="speakleash/Bielik-11B-v3.1-Instruct"; REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"; CONTEXT=32768
    : "${HF_TOKEN:?set HF_TOKEN (Hugging Face token with access to $REPO)}"
    # The template's provider system prompt stays on (template default); its date is pinned to the protocol day so
    # that the prompt does not change between runs (as ../ifeval/vllm.sh does).
    TEMPLATE_KWARGS='{"current_date": "2026-11-22", "current_day_of_week": "Sunday", "current_time_of_day": "morning"}' ;;
  slayer1b-1.08)
    REPO="SlayerLab/Slayer1B-1.08"; REVISION="ea0945b11153e67517b70d21192e6076d161f658"; CONTEXT=4096 ;;
  *) echo "unknown model-id: $MODEL (lfm3-1.7b | qwen3.5-4b | qwen3.5-9b | bielik-11b-v3.1-vllm | slayer1b-1.08)" >&2
     exit 2 ;;
esac

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
# RULER's essay haystacks are split with nltk's sent_tokenize (punkt_tab); nltk.download only prints a failure.
export NLTK_DATA="$CACHE/nltk_data"
"$VENV/bin/python" -c "import nltk, sys; sys.exit(not all(nltk.download(p, download_dir='$NLTK_DATA', quiet=True) for p in ('punkt', 'punkt_tab')))" \
  || { echo "nltk punkt / punkt_tab download failed" >&2; exit 1; }

JSON_DIR="$RULER_DIR/scripts/data/synthetic/json"
if ! echo "$ENGLISH_WORDS_SHA256  $JSON_DIR/english_words.json" | sha256sum -c --status 2>/dev/null; then
  curl -sfL "https://media.githubusercontent.com/media/NVIDIA/RULER/$RULER_COMMIT/scripts/data/synthetic/json/english_words.json" \
    -o "$JSON_DIR/english_words.json"
  echo "$ENGLISH_WORDS_SHA256  $JSON_DIR/english_words.json" | sha256sum -c --status \
    || { echo "english_words.json does not match its git-lfs oid" >&2; exit 1; }
fi
# RULER's own download scripts. Essays come from paulgraham.com and GitHub as they are today, QA from SQuAD v2.0
# dev and HotpotQA dev: the sha256 of each file goes into the result, and all models must share the same files.
if [[ ! -s "$JSON_DIR/PaulGrahamEssays.json" ]]; then
  (cd "$JSON_DIR" && "$VENV/bin/python" download_paulgraham_essay.py)
fi
if [[ ! -s "$JSON_DIR/squad.json" || ! -s "$JSON_DIR/hotpotqa.json" ]]; then
  (cd "$JSON_DIR" && bash download_qa_dataset.sh)
fi

# --- run.json: what summarize.py needs to describe the run (written once, kept on resume) -------------------
if [[ ! -f "$OUT/run.json" ]]; then
  "$VENV/bin/python" - "$OUT/run.json" "$JSON_DIR" <<PY
import datetime, hashlib, json, sys
from pathlib import Path
json_dir = Path(sys.argv[2])
sources = {f: hashlib.sha256((json_dir / f).read_bytes()).hexdigest()
           for f in ["PaulGrahamEssays.json", "squad.json", "hotpotqa.json", "english_words.json"]}
slayer = "$MODEL" == "slayer1b-1.08"
settings = {"weights": "$REPO @ $REVISION", "context_window": $CONTEXT, "seed": $SEED}
if slayer:
    settings.update(serving="research/common/slayer_lm.py, bfloat16", prompt="RULER raw prompt (base template), BOS",
                    temperature=0.0, max_tokens="RULER per-task answer budget")
else:
    settings.update(serving="vLLM $VLLM_VERSION, bfloat16", prompt="RULER input + answer prefix as one user message, "
                    "model chat template with its defaults", chat_template_kwargs=json.loads('${TEMPLATE_KWARGS:-null}'),
                    temperature=$TEMPERATURE, top_p=$TOP_P, max_tokens="context window minus templated input",
                    scored="text after the last </think>")
run = {"model": "$MODEL", "date": datetime.date.today().isoformat(), "ruler_commit": "$RULER_COMMIT",
       "seed": $SEED, "num_samples": $NUM, "limit": ${LIMIT:-None}, "tasks": "${TASKS[*]}".split(),
       "lengths": [int(x) for x in "${LENGTHS[*]}".split()], "data_sources": sources, "settings": settings}
Path(sys.argv[1]).write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
PY
fi

# --- the model's tokenizer for RULER's data generation (no weights) ----------------------------------------
TOKENIZER="$("$VENV/bin/python" -c "
from huggingface_hub import snapshot_download as s
print(s('$REPO', revision='$REVISION', allow_patterns=['*.json', '*.jinja', '*.txt', '*.model', '*.tiktoken']))")"
if [[ "$MODEL" == "slayer1b-1.08" ]]; then
  # Slayer's config.json has no model_type, so AutoTokenizer cannot load its snapshot; this directory holds only
  # its tokenizer.json, loaded as PreTrainedTokenizerFast (the same class research/common/slayer_lm.py uses).
  mkdir -p "$CACHE/slayer-tokenizer"
  cp "$TOKENIZER/tokenizer.json" "$CACHE/slayer-tokenizer/tokenizer.json"
  echo '{"tokenizer_class": "PreTrainedTokenizerFast"}' > "$CACHE/slayer-tokenizer/tokenizer_config.json"
  TOKENIZER="$CACHE/slayer-tokenizer"
fi

# --- data: RULER prepare.py per length and task --------------------------------------------------------------
RUN_LENGTHS=()
for L in "${LENGTHS[@]}"; do
  if (( L > CONTEXT )) || [[ "$MODEL" == "slayer1b-1.08" && "$L" != 4096 ]]; then
    mkdir -p "$OUT/$L"
    printf '{"reason": "the %s-token context window does not hold a %s-token RULER sample"}\n' "$CONTEXT" "$L" \
      > "$OUT/$L/skip.json"
    continue
  fi
  [[ -f "$OUT/$L/skip.json" ]] && continue   # an earlier run found that the templated prompts do not fit
  RUN_LENGTHS+=("$L")
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
if [[ "$MODEL" == "slayer1b-1.08" ]]; then
  [[ -d "$VENV_SLAYER" ]] || uv venv -q --python 3.12 "$VENV_SLAYER"
  # transformers as in research/common/requirements.lock.txt: lm-eval 0.4.9.1 breaks on transformers 5.x
  uv pip install -q --python "$VENV_SLAYER/bin/python" "lm-eval==$LM_EVAL_VERSION" "transformers==4.57.6" \
    safetensors tokenizers huggingface_hub pyyaml
  if ! "$VENV_SLAYER/bin/python" -c "import torch, sys; c = torch.version.cuda; sys.exit(not c or tuple(map(int, c.split('.')[:2])) < (12, 8))" 2>/dev/null; then
    uv pip install -q --python "$VENV_SLAYER/bin/python" --index-url "$TORCH_INDEX" --reinstall-package torch torch
  fi
  WEIGHTS="$("$VENV_SLAYER/bin/python" -c "from huggingface_hub import snapshot_download as s; print(s('$REPO', revision='$REVISION'))")"
  for L in "${RUN_LENGTHS[@]}"; do
    "$VENV_SLAYER/bin/python" "$HERE/slayer_predict.py" --weights "$WEIGHTS" --length-dir "$OUT/$L" \
      --tasks "${TASKS[@]}" --ruler-dir "$RULER_DIR"
  done
elif (( ${#RUN_LENGTHS[@]} )); then
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
  KWARGS=()
  [[ -n "$TEMPLATE_KWARGS" ]] && KWARGS=(--chat-template-kwargs "$TEMPLATE_KWARGS")
  for L in "${RUN_LENGTHS[@]}"; do
    "$VENV/bin/python" "$HERE/predict.py" --base-url "http://localhost:$PORT" --model "$MODEL" \
      --length-dir "$OUT/$L" --tasks "${TASKS[@]}" --seed "$SEED" --temperature "$TEMPERATURE" --top-p "$TOP_P" \
      --concurrency "$CONCURRENCY" --ruler-dir "$RULER_DIR" "${KWARGS[@]}"
  done
  kill $VLLM_PID 2>/dev/null || true
fi

# --- scoring: RULER's evaluate.py on the text after the last </think> -------------------------------------
for L in "${RUN_LENGTHS[@]}"; do
  [[ -f "$OUT/$L/skip.json" ]] && continue
  "$VENV/bin/python" "$HERE/summarize.py" preds "$OUT/$L"
  (cd "$RULER_DIR/scripts/eval" && PYTHONPATH="$HERE/nemo_shim" "$VENV/bin/python" evaluate.py \
    --data_dir "$OUT/$L/pred" --benchmark synthetic)
done

"$VENV/bin/python" "$HERE/summarize.py" results "$OUT" "${RESULTS_DIR:-$HERE/results}/$MODEL" --ruler-dir "$RULER_DIR"
