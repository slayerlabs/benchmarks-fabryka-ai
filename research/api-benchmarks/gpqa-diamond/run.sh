#!/usr/bin/env bash
# GPQA Diamond, EXPLORATORY LOCAL RUN: bash run.sh <model-id> [--limit N]
#   env: MAX_GEN_TOKS (default 8192), BATCH_SIZE, OUT_DIR, VENV,
#        SAMPLES_JSON=<file>  run only the doc_ids in it (lm-eval --samples; scripts/select_rerun_subset.py writes one)
#   bielik-11b-v3.1  speakleash/Bielik-11B-v3.1-Instruct @ d6e755d356ad418d0f0e30b8c428db267415ddb9
#   lfm3-1.7b        LiquidAI/LFM3-1.7B @ 1da06bec6a819da10b54c67e5c90972b46d81871 (trust_remote_code)
# NOTE: the official path should be the Fabryka API at the LFM3-1.7B card settings (temperature 0.6, top_p 0.95,
# reasoning on, no output limit). This script reproduces the exploratory local run only (greedy, local GPU).
# Syntax-checked only (bash -n); not run on a GPU here.
# Needs a Hugging Face token with access to the gated dataset Idavidrein/gpqa (HF_TOKEN) and a CUDA GPU.
set -euo pipefail

MODEL="${1:?usage: bash run.sh <model-id> [--limit N]}"
shift
LIMIT=()
if [[ "${1:-}" == "--limit" ]]; then LIMIT=(--limit "${2:?--limit needs N}"); fi
SUBSET=()
if [[ -n "${SAMPLES_JSON:-}" ]]; then
  [[ ${#LIMIT[@]} -eq 0 ]] || { echo "SAMPLES_JSON and --limit are mutually exclusive" >&2; exit 2; }
  SUBSET=(--samples "$SAMPLES_JSON")
fi
: "${HF_TOKEN:?set HF_TOKEN (GPQA is gated)}"

HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${VENV:-$HERE/.venv}"
LM_EVAL_VERSION="0.4.13"       # used for the published run; the repo pin elsewhere is 0.4.9.1 (see README, Deviations)
MAX_GEN_TOKS="${MAX_GEN_TOKS:-8192}"
OUT="${OUT_DIR:-$HERE/out}/$MODEL-$MAX_GEN_TOKS"   # budget in the path: a 16384 run does not overwrite the 8192 one
DATASET_REV="83022cefff930aea54f654c0b282e74b9eeda5c6"   # Idavidrein/gpqa, config gpqa_diamond (198 questions)
TORCH_INDEX="https://download.pytorch.org/whl/cu128"

case "$MODEL" in
  bielik-11b-v3.1)
    REPO="speakleash/Bielik-11B-v3.1-Instruct"; REVISION="d6e755d356ad418d0f0e30b8c428db267415ddb9"
    TRUST="" ; BATCH="${BATCH_SIZE:-1}" ;;
  lfm3-1.7b)
    REPO="LiquidAI/LFM3-1.7B"; REVISION="1da06bec6a819da10b54c67e5c90972b46d81871"
    TRUST=",trust_remote_code=True"; BATCH="${BATCH_SIZE:-22}" ;;
  *) echo "unknown model-id: $MODEL (bielik-11b-v3.1 | lfm3-1.7b)" >&2; exit 2 ;;
esac

[[ -d "$VENV" ]] || uv venv --python 3.12 "$VENV"
BIN="$VENV/bin"
PY="$BIN/python"
uv pip install --python "$PY" --index-url "$TORCH_INDEX" "torch==2.8.0"
uv pip install --python "$PY" "lm-eval==$LM_EVAL_VERSION" "transformers==5.22.1" huggingface_hub
WEIGHTS="$("$PY" -c "from huggingface_hub import snapshot_download as s; print(s('$REPO', revision='$REVISION'))")"

# Pin the dataset revision at run time. The stock task has no `revision`, so lm-eval would load whatever "main" is
# today. This task includes the stock one and adds dataset_kwargs.revision; the task name gets a _pinned suffix.
TASK="gpqa_diamond_cot_zeroshot_pinned"
TASKDIR="$OUT/tasks"
mkdir -p "$TASKDIR"
STOCK="$("$PY" -c 'import os, lm_eval; print(os.path.join(os.path.dirname(lm_eval.__file__), "tasks/gpqa/cot_zeroshot/gpqa_diamond_cot_zeroshot.yaml"))')"
cat > "$TASKDIR/$TASK.yaml" <<YAML
include: $STOCK
task: $TASK
dataset_kwargs:
  revision: $DATASET_REV
YAML

"$BIN/lm_eval" \
  --model hf \
  --model_args "pretrained=$WEIGHTS,dtype=bfloat16$TRUST" \
  --include_path "$TASKDIR" \
  --tasks "$TASK" \
  --apply_chat_template \
  --gen_kwargs "max_gen_toks=$MAX_GEN_TOKS,do_sample=false,temperature=0.0" \
  --batch_size "$BATCH" \
  --log_samples --output_path "$OUT" "${LIMIT[@]}" "${SUBSET[@]}"

# Fail fast if the pin did not reach the dataset loader (results JSON records the task's dataset_kwargs).
"$PY" - "$OUT" "$DATASET_REV" <<'PYEOF'
import glob, json, sys
out, rev = sys.argv[1], sys.argv[2]
files = sorted(glob.glob(out + "/**/results_*.json", recursive=True))
if not files:
    sys.exit("no results_*.json under " + out)
cfg = json.load(open(files[-1]))["configs"]
got = [c.get("dataset_kwargs", {}).get("revision") for c in cfg.values() if isinstance(c.get("dataset_kwargs"), dict)]
if got != [rev]:
    sys.exit(f"dataset revision not pinned: expected {rev}, results record {got}")
print("dataset revision pinned:", rev)
PYEOF

echo "Raw lm-eval output in $OUT (it holds gated question text and model output: do not publish it)." \
     "Per-item flags for results/: python scripts/samples_to_flags.py <samples_*.jsonl> results/<id>.jsonl.gz," \
     "then scripts/truncation_flags.py for the truncated_<budget> flag (see README, Reproduce)."
